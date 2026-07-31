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

# リサーチ対象となるジャンルと方向性
GENRES = [
    {
        "category": "生産性・タイムマネジメント",
        "angle": "最新の研究データや実証実験に基づいた、科学的に効果のある時短・集中力ハック",
    },
    {
        "category": "心理学・人間関係",
        "angle": "行動経済学や心理学の最新トピックを用いた、日常のストレス緩和と人間関係の改善策",
    },
    {
        "category": "最新テクノロジー・AI活用",
        "angle": "海外で話題になっている最新AIツールやテクノロジーの具体的な活用事例と未来の働き方",
    },
    {
        "category": "ビジネス・マーケティング",
        "angle": "海外の成功企業のマーケティング事例や、話題のビジネスモデルの裏側解説",
    },
    {
        "category": "ヘルスケア・睡眠科学",
        "angle": "海外論文や最新医学ニュースに基づく、効果的な疲労回復やパフォーマンス向上術",
    },
    {
        "category": "教育・認知心理学",
        "angle": "世界の最新教育アプローチや認知科学の研究結果を取り入れた家庭学習法",
    },
]

selected_genre = random.choice(GENRES)

system_instruction = """あなたは最新の情報を自らWeb検索して調査し、読者に具体的で正確な情報を提供するプロのWebライターです。
与えられたジャンルについてWeb検索（Google Search）を実行し、最新のファクト・具体例・統計データ・研究成果を収集した上で、信頼性の高いブログ記事を作成してください。

【執筆ルール】
1. 挨拶、前置き、自己紹介、作成報告（「〜作成しました」等）、末尾のメタ解説は一切禁止です。
2. 記事内には必ずGoogle検索等で得た具体的なデータ、最新の事例、または専門的な知見・数値を盛り込んでください。
3. 上から目線の指導や断定は避け、親しみやすく丁寧で説得力のあるトーンで記述してください。
4. 出力はすべてHTML形式（<h2>, <h3>, <p>, <ul>, <li>, <strong>, <table>等）とし、マークダウン記号（**や#）は絶対に使用しないでください。
5. 本文の先頭は挨拶なしで、ダイレクトに導入文（<p>）または<h2>見出しから始めてください。
"""

prompt = f"""
ジャンル: 「{selected_genre['category']}」
テーマの方向性: 「{selected_genre['angle']}」

【作業手順】
1. まずGoogle検索機能を用いて、このジャンルの最新トレンド、海外事例、研究論文、統計データ、または具体的なエピソードをリアルタイム検索・リサーチしてください。
2. 検索結果で得られた正確な情報をもとに、読者にとって非常に有益で興味深いブログ記事と関連タグ（3〜5個）を作成してください。

【構成ルール】
1. タイトル: 読者の興味を引く具体的で魅力的なタイトル
2. 導入: 読者の悩みや疑問に寄り添う導入
3. 本論: 検索で得た事実データや具体例・比較表（<table>や<ul>を活用）
4. アクションプラン: 今日から試せる具体的な1つのステップ
"""

client = genai.Client(api_key=GEMINI_API_KEY)

response_schema = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "content": {"type": "STRING"},
        "tags": {"type": "ARRAY", "items": {"type": "STRING"}},
    },
    "required": ["title", "content", "tags"],
}

# tools=[{"google_search": {}}] により、GeminiがリアルタイムでWeb検索（Google Search Grounding）を行ってから回答を生成します
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config=types.GenerateContentConfig(
        system_instruction=system_instruction,
        tools=[{"google_search": {}}],
        response_mime_type="application/json",
        response_schema=response_schema,
        temperature=0.7,
    ),
)

data = json.loads(response.text)
title = data.get("title", f"{selected_genre['category']}の最新知見")
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
            timeout=15,
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
            timeout=15,
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
print(f"ジャンル: {selected_genre['category']}")
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
    print(
        f"投稿成功 ID: {post_id}, タイトル: {title}, ステータス: {current_status}"
    )

    if current_status != "publish":
        update_res = requests.post(
            f"{WP_URL}/wp-json/wp/v2/posts/{post_id}",
            auth=AUTH,
            json={"status": "publish"},
            timeout=30,
        )
        if update_res.status_code == 200:
            print("ステータスを publish に強制変更しました。")
        else:
            print(
                f"公開ステータス変更エラー: {update_res.status_code} {update_res.text}"
            )
else:
    print(f"投稿エラー: {post_res.status_code}\n{post_res.text}")
    raise Exception("WordPress投稿に失敗しました")
