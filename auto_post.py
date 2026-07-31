import json
import os
import random
import requests
from google import genai
from google.genai import types

# --- 環境変数 ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WP_URL = os.environ.get("WP_URL", "").rstrip("/")
WP_USER = os.environ.get("WP_USER")
WP_PASS = os.environ.get("WP_PASS")
AUTH = (WP_USER, WP_PASS)

# 記事クオリティを高める高度なテーマ定義
THEMES = [
    {
        "title": "小学5年生の算数でつまずく「割合と平均」：思考力を伸ばす海外のバーモデル学習法",
        "detail": "日本とシンガポールの算数教育比較、認知心理学に基づく理解の深め方、具体的な解法ステップと保護者の声かけパターン"
    },
    {
        "title": "小学6年生の「速さと比」完全攻略：公式丸暗記から脱却する概念理解のアプローチ",
        "detail": "速さの概念理解、図解を用いたビジュアル解法、アメリカのSTEM教育で用いられる実生活応用問題の事例"
    },
    {
        "title": "中学生が陥る「関係代名詞・不定詞」の壁を打ち破る：第二言語習得論（SLA）に基づく文法講座",
        "detail": "なぜ日本の英語学習者はここでつまずくのか、チャンクリーディングの導入、脳科学に基づいた記憶の定着メカニズム"
    },
    {
        "title": "家にあるものでできる！小学生向け本格科学実験：仮説検証能力を育む家庭学習ガイド",
        "detail": "探究学習（Inquiry-based Learning）のフレームワーク、具体的な実験手順、観察シートの作り方と科学的思考を深める問答集"
    },
    {
        "title": "科学的に正しい家庭学習の習慣化：行動経済学とWOOP法則でつくる自律学習環境",
        "detail": "ハビット・スタッキング、作業興奮を引き出す環境デザイン、親の関わり方とモチベーションを維持するフィードバック構造"
    }
]

selected_theme = random.choice(THEMES)

system_instruction = """あなたは教育科学・認知心理学・比較教育学に精通したプロフェッショナルWeb教育アナリスト兼ライターです。
読者に圧倒的な価値を提供する専門的かつ読みやすいブログ記事を作成してください。

【厳格な禁止・注意事項】
1. 挨拶、前置き、自己紹介、作成報告（例：「作成しました」「記事の本文です」等）、末尾の解説や注釈は一切禁止です。
2. 「〜でしょうか？」「〜してみましょう！」といった陳腐で大げさな表現（AIしぐさ）を排除し、信頼できる知的なトーンで記述してください。
3. 出力する本文（content）はHTML形式（<h2>, <h3>, <p>, <ul>, <li>, <strong>, <table>等）とし、マークダウン記号（**や#）は絶対に使わないでください。
4. contentの先頭は挨拶なしで、ダイレクトに導入文（<p>）または<h2>見出しから始めてください。
"""

prompt = f"""
テーマ: 「{selected_theme['title']}」
取り込む要素: {selected_theme['detail']}

上記テーマについて、専門的で非常に価値の高いブログ記事と、関連する検索用タグ（3〜5個）を作成してください。

【記事構成の指定】
1. 導入：従来の学習法の問題点と、科学的・論理的な解決アプローチの提示
2. 理論・海外事例：シンガポール教育、欧米のSTEM教育、認知科学の知見などを取り入れた深い解説
3. 具体例・実践ステップ：具体的な問題、解法、または具体的なステップバイステップの解説
4. まとめ：今日から実践できる具体的なアクションプラン

【タグの指定】
* 簡潔で一般的なキーワード（例：「小学生算数」「家庭学習」「認知科学」「勉強法」など）を3〜5個指定してください。
"""

client = genai.Client(api_key=GEMINI_API_KEY)

# 強固なレスポンス構造（JSON Schema）定義
response_schema = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "content": {"type": "STRING"},
        "tags": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        }
    },
    "required": ["title", "content", "tags"]
}

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=prompt,
    config=types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="application/json",
        response_schema=response_schema,
        temperature=0.7
    ),
)

data = json.loads(response.text)
title = data.get("title", selected_theme["title"])
content = data.get("content", "")
tag_names = data.get("tags", [])


def get_or_create_tag_ids(names):
    tag_ids = []
    for name in names:
        name = name.strip().replace("#", "")
        if not name:
            continue

        res = requests.get(
            f"{WP_URL}/wp-json/wp/v2/tags",
            auth=AUTH,
            params={"search": name},
            timeout=15
        )
        if res.status_code == 200:
            tags = res.json()
            matched = [t for t in tags if t["name"].lower() == name.lower()]
            if matched:
                tag_ids.append(matched[0]["id"])
                continue

        create_res = requests.post(
            f"{WP_URL}/wp-json/wp/v2/tags",
            auth=AUTH,
            json={"name": name},
            timeout=15
        )
        if create_res.status_code == 201:
            tag_ids.append(create_res.json()["id"])
        elif create_res.status_code == 400:
            err_data = create_res.json()
            existing_id = err_data.get("data", {}).get("term_id")
            if existing_id:
                tag_ids.append(existing_id)

    return tag_ids


tag_ids = get_or_create_tag_ids(tag_names)
print(f"作成・取得したタグID: {tag_ids}")

payload = {
    "title": title,
    "content": content,
    "status": "publish",
    "tags": tag_ids,
}

post_res = requests.post(
    f"{WP_URL}/wp-json/wp/v2/posts",
    auth=AUTH,
    json=payload,
    timeout=30,
)

if post_res.status_code == 201:
    post_data = post_res.json()
    post_id = post_data.get("id")
    current_status = post_data.get("status")
    print(f"投稿作成成功 ID: {post_id}, ステータス: {current_status}")

    # 下書き（draft）にとどまった場合の強制公開リクエスト
    if current_status != "publish":
        update_res = requests.post(
            f"{WP_URL}/wp-json/wp/v2/posts/{post_id}",
            auth=AUTH,
            json={"status": "publish"},
            timeout=30
        )
        if update_res.status_code == 200:
            print("ステータスを publish に強制変更しました。")
        else:
            print(f"公開ステータス変更エラー: {update_res.status_code} {update_res.text}")
else:
    print(f"投稿エラー: {post_res.status_code}\n{post_res.text}")
    raise Exception("WordPress投稿に失敗しました")
