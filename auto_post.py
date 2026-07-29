import json
import os
import random
import requests
from google import genai

# --- 環境変数 ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WP_URL = os.environ.get("WP_URL").rstrip('/')
WP_USER = os.environ.get("WP_USER")
WP_PASS = os.environ.get("WP_PASS")
AUTH = (WP_USER, WP_PASS)

THEMES = [
    "小学5年生の算数のよくある問題と回答",
    "小学6年生の算数のよくある問題と回答",
    "中学生でつまずきやすい英語の文法と解説",
    "小学生向けの理科の面白い実験と解説",
    "効果的な家庭学習の方法と習慣化のコツ",
]

theme = random.choice(THEMES)

# 1. GeminiにJSON形式で「本文」と「タグリスト」を出力させるプロンプト
prompt = f"""
「{theme}」についてのWordPressブログ記事本文と、記事に最適なタグを3〜5個生成してください。
* 読者にわかりやすく丁寧な解説を含めてください。
* 誰にでも書けるようなありきたりな記事ではなくて、海外事例も含めて可能な限りユニークで科学的に裏付けされた記事を書いてください。
* いかにもAIが書いたと即時見破られるようなAIしぐさは禁止です。極端な比喩表現などはやめてください。
WordPressブログにそのまま貼り付けて使える、装飾用の見出し（h2, h3）や箇条書きを含めた記事本文を作成しました。　の様な挨拶は禁止です。自動投稿するので不要な挨拶や注射宇久は絶対に禁止


【出力フォーマット】
以下のJSON形式のみを出力してください（余計な解説文やコードブロック記号 ```json は含めないでください）。

{{
  "title": "{theme}",
  "content": "WordPress用のMarkdown本文（h2, h3, 箇条書きを活用）",
  "tags": ["タグ1", "タグ2", "タグ3"]
}}
"""

client = genai.Client(api_key=GEMINI_API_KEY)
response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=prompt,
)

# 返却されたJSON文字列をパース
raw_text = response.text.strip()
if raw_text.startswith("```"):
    raw_text = raw_text.split("\n", 1)[1].rsplit("\n", 1)[0]  # ```jsonの除去

data = json.loads(raw_text)
title = data.get("title", theme)
content = data.get("content", "")
tag_names = data.get("tags", [])


# 2. WordPressでタグ名からタグIDを取得（なければ新規作成）する関数
def get_or_create_tag_ids(names):
    tag_ids = []
    for name in names:
        name = name.strip()
        if not name:
            continue

        # 既存タグの検索
        res = requests.get(f"{WP_URL}/wp-json/wp/v2/tags", auth=AUTH, params={"search": name})
        if res.status_code == 200:
            tags = res.json()
            # 完全一致する既存タグを探す
            matched = [t for t in tags if t["name"].lower() == name.lower()]
            if matched:
                tag_ids.append(matched[0]["id"])
                continue

        # 既存タグがない場合は新規作成
        create_res = requests.post(f"{WP_URL}/wp-json/wp/v2/tags", auth=AUTH, json={"name": name})
        if create_res.status_code == 201:
            tag_ids.append(create_res.json()["id"])
        elif create_res.status_code == 400:
            # 既存エラー（スラッグ重複等）の場合は検索結果からIDを取得
            existing_id = create_res.json().get("data", {}).get("term_id")
            if existing_id:
                tag_ids.append(existing_id)

    return tag_ids


# タグIDの取得処理を実行
tag_ids = get_or_create_tag_ids(tag_names)
print(f"生成されたタグ: {tag_names} -> タグID: {tag_ids}")

# 3. 記事の投稿処理（タグIDを付与）
payload = {
    "title": title,
    "content": content,
    "status": "publish",  
    "tags": tag_ids,
}

res = requests.post(
    f"{WP_URL}/wp-json/wp/v2/posts",
    auth=AUTH,
    json=payload,
    timeout=30,
)

if res.status_code == 201:
    print(f"成功: {title} (ID: {res.json().get('id')})")
else:
    print(f"エラー: {res.status_code}\n{res.text}")
    raise Exception("WordPress投稿に失敗しました")
