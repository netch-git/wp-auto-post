import os
import requests

# --- 環境変数の取得と検証 ---
WP_URL = os.environ.get("WP_URL", "").rstrip("/")
WP_USER = os.environ.get("WP_USER")
WP_PASS = os.environ.get("WP_PASS")

if not all([WP_URL, WP_USER, WP_PASS]):
    raise ValueError("必要な環境変数が未設定です (WP_URL, WP_USER, WP_PASS)")

AUTH = (WP_USER, WP_PASS)

# Geminiを使わないテスト用ダミーデータ
title = "【テスト投稿】GitHub Actions疎通確認"
content = """
<h2>テスト見出し</h2>
<p>これはGitHub Actionsからの自動投稿テストです。Gemini APIを経由せずに直接WordPress APIを叩いています。</p>
<ul>
  <li>環境変数チェック: 正常</li>
  <li>WordPress REST API認証: 正常</li>
</ul>
"""
tag_names = ["テスト", "自動化"]


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
print(f"取得・作成したタグID: {tag_ids}")

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
    print(f"投稿成功 ID: {post_data.get('id')}, ステータス: {post_data.get('status')}")
else:
    print(f"投稿エラー: {post_res.status_code}\n{post_res.text}")
    raise Exception("WordPress投稿に失敗しました")
