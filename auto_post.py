import json
import os
import random
import re
import requests
from google import genai
from google.genai import types

# --- 環境変数の取得と検証 ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WP_URL = os.environ.get("WP_URL", "").rstrip("/")
WP_USER = os.environ.get("WP_USER")
WP_PASS = os.environ.get("WP_PASS")

if not all([GEMINI_API_KEY, WP_URL, WP_USER, WP_PASS]):
    raise ValueError(
        "必要な環境変数が未設定です (GEMINI_API_KEY, WP_URL, WP_USER, WP_PASS)"
    )

AUTH = (WP_USER, WP_PASS)

GENRES = [
    {
        "category": "生産性・タイムマネジメント",
        "angle": "科学的に効果のある時短・集中力ハック",
    },
    {
        "category": "心理学・人間関係",
        "angle": "行動経済学や心理学を用いた、日常のストレス緩和と人間関係の改善策",
    },
    {
        "category": "最新テクノロジー・AI活用",
        "angle": "最新AIツールの具体的な活用事例と未来の働き方",
    },
    {
        "category": "ビジネス・マーケティング",
        "angle": "企業のマーケティング事例や、話題のビジネスモデルの解説",
    },
    {
        "category": "ヘルスケア・睡眠科学",
        "angle": "効果的な疲労回復やパフォーマンス向上術",
    },
    {
        "category": "教育・認知心理学",
        "angle": "世界の教育アプローチや認知科学を取り入れた学習法",
    },
]

selected_genre = random.choice(GENRES)

system_instruction = """あなたは読者に具体的で正確な情報を提供するプロのWebライターです。
与えられたジャンルについて、信頼性の高いブログ記事を作成してください。

【執筆ルール】
1. 挨拶、前置き、自己紹介、作成報告（「〜作成しました」等）、末尾のメタ解説は一切禁止です。
2. 記事内には具体的なデータ、事例、または専門的な知見・数値を盛り込んでください。
3. 親しみやすく丁寧で説得力のあるトーンで記述してください。
4. 出力はすべてHTML形式（<h2>, <h3>, <p>, <ul>, <li>, <strong>, <table>等）とし、マークダウン記号（**や#）は絶対に使用しないでください。
5. 本文の先頭は挨拶なしで、ダイレクトに導入文（<p>）または<h2>見出しから始めてください。
"""

prompt = f"""
ジャンル: 「{selected_genre['category']}」
テーマの方向性: 「{selected_genre['angle']}」

【構成ルール】
1. タイトル: 読者の興味を引く具体的で魅力的なタイトル
2. 導入: 読者の悩みや疑問に寄り添う導入
3. 本論: 事実データや具体例・比較表（<table>や<ul>を活用）
4. アクションプラン: 今日から試せる具体的な1つのステップ

【出力フォーマット】
以下のJSON形式のみを出力してください。
{{
  "title": "記事タイトル",
  "content": "HTML形式の記事本文",
  "tags": ["タグ1", "タグ2", "タグ3"]
}}
"""

client = genai.Client(api_key=GEMINI_API_KEY)

# 検索ツールを外し、標準生成でAPIを呼び出し
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config=types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.7,
    ),
)

if not response or not response.text:
    raise RuntimeError("モデルからのテキスト取得に失敗しました。")

raw_text = response.text.strip()

json_match = re.search(r"\{[\s\S]*\}", raw_text)
json_str = json_match.group(0) if json_match else raw_text

try:
    data = json.loads(json_str)
except json.JSONDecodeError as e:
    print(f"JSONパースエラー。生レスポンス:\n{raw_text}")
    raise e

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
print(f"タグID: {tag_ids}")

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
                f"ステータス変更エラー: {update_res.status_code} {update_res.text}"
            )
else:
    print(f"投稿エラー: {post_res.status_code}\n{post_res.text}")
    raise Exception("WordPress投稿に失敗しました")
