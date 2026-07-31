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

# 幅広いジャンルと、親しみやすく寄り添う方向性
GENRES = [
    {
        "category": "生産性・タイムマネジメント",
        "angle": "無理な頑張りに頼らず、毎日の生活や仕事を少しラクにする優しいヒント",
    },
    {
        "category": "心理学・人間関係",
        "angle": "日常のモヤモヤや人間関係の悩みに寄り添い、心が軽くなる視点の切り替え",
    },
    {
        "category": "最新テクノロジー・AI活用",
        "angle": "難しい技術論ではなく、『こんな風に使ってみたら毎日がちょっと楽しくなった』体験談的アプローチ",
    },
    {
        "category": "マーケティング・身近な疑問",
        "angle": "普段の生活で感じる『これってなんでだろう？』を楽しく読み解く雑学風ストーリー",
    },
    {
        "category": "ヘルスケア・睡眠",
        "angle": "厳しい健康管理ではなく、今日から心地よく取り入れられる小さなセルフケア",
    },
    {
        "category": "教育・学びの工夫",
        "angle": "『勉強しなさい』と言わずに、自然と知的好奇心が湧いてくる親子で試せるアイデア",
    },
]

selected_genre = random.choice(GENRES)

system_instruction = """あなたは親しみやすく、温かみのあるWebコラムニストです。
読者と同じ目線に立ち、寄り添いながら一緒に考えるような、説教くさくないブログ記事を作成してください。

【執筆ルール】
1. 挨拶、前置き、自己紹介、作成報告（「〜作成しました」等）、末尾のメタ解説は一切禁止です。
2. 上から目線の指導や断定（「〜すべき」「〜は間違いです」等）は避け、共感と優しさのある語り口（「〜ですよね」「〜という考え方もあります」「試してみませんか？」）で記述してください。
3. 専門知識は噛み砕き、読者が「それなら自分にもできそう」「読んで心が軽くなった」と感じられるトーンを意識してください。
4. 出力はすべてHTML形式（<h2>, <h3>, <p>, <ul>, <li>, <strong>, <table>等）とし、マークダウン記号（**や#）は絶対に使用しないでください。
5. 本文の先頭は挨拶なしで、ダイレクトに導入文（<p>）または<h2>見出しから始めてください。
"""

prompt = f"""
ジャンル: 「{selected_genre['category']}」
テーマの方向性: 「{selected_genre['angle']}」

上記ジャンルにおいて、読者の悩みに優しく共感し、読んだ後に少しホッとするようなブログ記事と、関連タグ（3〜5個）を生成してください。

【構成ルール】
1. タイトル: 共感しやすく、親しみやすいタイトル（例：「実は〇〇で大丈夫」「〜を少しラクにするヒント」など）
2. 導入: 読者が日常で感じる「あるある」や悩みに寄り添う共感文
3. 本論: 科学的な知見や海外の面白い工夫を、図表（<table>）やリスト（<ul>）を使って優しく解説
4. アクションプラン: 今日から無理なく試せる、小さな1ステップの提案
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

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=prompt,
    config=types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="application/json",
        response_schema=response_schema,
        temperature=0.7,
    ),
)

data = json.loads(response.text)
title = data.get("title", f"{selected_genre['category']}のヒント")
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
