import os
import random
import requests
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WP_URL = os.environ.get("WP_URL")
WP_USER = os.environ.get("WP_USER")
WP_PASS = os.environ.get("WP_PASS")

THEMES = [
    "小学5年生の算数のよくある問題と回答",
    "小学6年生の算数のよくある問題と回答",
    "中学生でつまずきやすい英語の文法と解説",
    "小学生向けの理科の面白い実験と解説",
    "効果的な家庭学習の方法と習慣化のコツ",
]

theme = random.choice(THEMES)

prompt = f"""
「{theme}」についてのWordPressブログ記事本文を作成してください。

【出力ルール】
* 記事のタイトル（h1）から直接開始し、冒頭や末尾に「以下は〜」「〜作成しました」などの挨拶や説明文を一切含めないでください。
* 見出し（h2, h3）、箇条書き、表などを活用してわかりやすく解説してください。
* WordPressへ直接投稿できるクリーンなMarkdown形式のみを出力してください。
* どこにでもあるようなありきたりな内容は絶対に禁止でユニークな事例にしてください。
* 可能な限り学術的に裏付けされたコンテンツを参照して、引用もリストで末尾に記述してください。
"""

client = genai.Client(api_key=GEMINI_API_KEY)

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=prompt,
)
article_html = response.text

payload = {
    "title": theme,
    "content": article_html,
    "status": "publish",  # "draft"（下書き）から "publish"（公開）に変更
}

res = requests.post(
    f"{WP_URL.rstrip('/')}/wp-json/wp/v2/posts",
    auth=(WP_USER, WP_PASS),
    json=payload,
    timeout=30,
)

if res.status_code == 201:
    print(f"成功: {theme} (ID: {res.json().get('id')})")
else:
    print(f"エラー: {res.status_code}\n{res.text}")
    raise Exception("WordPress投稿に失敗しました")
