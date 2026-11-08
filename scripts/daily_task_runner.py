#!/usr/bin/env python3
"""
Daily Research & Eyecatch Automation Runner
Part A (02:00 JST / 17:00 UTC): デジタル資産マネタイズ調査
Part B (03:30 JST / 18:30 UTC): 海外の高度GAS事例調査
Part C (04:00 JST / 19:00 UTC): Gemini 4 / Antigravity / AI Studio 活用調査

Strictly complies with Antigravity_Remote_Handover_Rules.md (Parts A, B, C, D).
"""

import os
import sys
import json
import base64
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add current scripts directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from random_prompt_generator import generate_random_prompt

DEFAULT_FOLDER_ID = "17qo8NbDC_D6Xdbz1b6oo6OxXIIBFaezK"

# ==========================================
# Handover Rules Prompts & Definitions
# ==========================================

PROMPT_PART_A = """
デジタルスキルやデジタル資産（GAS・Pythonコード、田舎の環境音、田舎の風景写真、田舎の海の動画、田舎の電車の動画）を活用した最新のマネタイズ手法、市場トレンド、成功事例、および販売プラットフォームをWeb検索を用いて調査し、実践的な日次レポートを作成してください。

### 調査・抽出条件
1. 以下の5つのデジタル資産カテゴリーすべてについて、国内外の最新販売手法、需要の高いフォーマット、マネタイズ事例をリサーチすること：
 - ① GAS・Pythonコード（業務自動化、スクレイピング、API連携、スプレッドシート連携テンプレート、MCPサーバー、プロンプト・設定ファイル等の販売・受託）
 - ② 田舎の環境音（自然音、雨音、波音、虫の声、バイノーラルASMR、作業用・睡眠用BGM、音源ライセンス、ゲーム・VR向け効果音、ポッドキャスト配信）
 - ③ 田舎の風景写真（ストックフォト、Web商用素材、海外向けデジタル壁紙・Printable Art、3D/PBRテクスチャ、地域魅力発信連動）
 - ④ 田舎の海の動画（YouTube作業用動画、4Kストックビデオ、配信用ループ背景、VFXプレート、リラクゼーション・チル系素材）
 - ⑤ 田舎の電車の動画（ローカル線・鉄道ファン向けコンテンツ、前面展望・車窓、走行音連動、動画編集テンプレート素材）
2. 少人数・個人でも小さく始められて再現性の高い具体的な施策や、高単価化・差別化の工夫（海外プラットフォーム活用、AI・自動化ツールとの組み合わせ、B2B・地域DX展開など）を抽出すること。毎回異なる切り口・ニッチ市場を深掘りし、定番サイトの単なる羅列を避けること。

### 出力構成
以下の構成で整理し、Markdown形式で出力してください：
1. **本日の注目マネタイズトレンド**（最新市場の動きや注目のプラットフォーム・成功事例を2〜3点）
2. **カテゴリー別のおすすめマネタイズ手法と販売先**（①GAS/Python、②環境音、③風景写真、④海の動画、⑤電車の動画）
3. **個人が短時間で着手できる具体的なアクションプラン**（15〜30分で試せる具体的な3ステップ）
4. **主な参照元・プラットフォームリンク**（検証済みの正確なURLリンク）

### 【最重要】末尾のハッシュタグ出力ルール
- 「3. note用ハッシュタグ（12個）」のような見出し行は絶対に設置しないでください（設置禁止）。
- 記事の最後（4. 主な参照元・プラットフォームリンク の直後）に、空行を1行空けて、直接プレーンテキストのコードブロック（```text ... ```）で12個のハッシュタグを出力してください。
例：
```text
#ハッシュタグ1 #ハッシュタグ2 #ハッシュタグ3 #ハッシュタグ4 #ハッシュタグ5 #ハッシュタグ6 #ハッシュタグ7 #ハッシュタグ8 #ハッシュタグ9 #ハッシュタグ10 #ハッシュタグ11 #ハッシュタグ12
```
"""

PROMPT_PART_B = """
目的: 海外の高度なGoogle Apps Script（GAS）の活用事例・技術記事・オープンソースプロジェクトを調査し、マネジメント用途ではなく、洗練されたUIやツール構築、Pythonとの連携、海外のオープンデータの取得・分析との組み合わせ、外部サービスAPIや他のGoogleツールとの連携、パフォーマンス向上に関する実践的なアイデアをまとめて私に届ける。

実行手順:
1. 英語圏のコミュニティや技術メディア（GitHub、Medium、Dev.to、Redditのr/GoogleAppsScript、Stack Overflow、Google Cloud Blog、著名なGAS開発者のブログなど）を対象に、Google Apps Scriptの高度な活用事例・最新トレンドを検索する。過去に取り上げた一般的な基本事例（単なるメール自動送信や単純な集計など）を避け、以下のような技術的・アーキテクチャ的に洗練されたトピックに焦点を当てる:
 - 海外のオープンデータの取得・分析との組み合わせ（政府・自治体・国際機関のオープンデータポータル、気象・地理空間・交通・経済統計API、BigQueryパブリックデータセット等からの自動取得、GAS＋Python / BigQuery / Looker Studioを連携させたデータクレンジング・分析・可視化パイプライン、シビックテックや地域課題解決への応用事例）
 - 洗練されたUI・フロントエンド構築（HtmlServiceでのReact / Vue.js / Svelte / Preact / Tailwind CSS等のモダンフレームワーク活用、clasp + TypeScript + Vite/Bunによるモダン開発環境、Google Workspace Add-ons / CardServiceによるリッチUI）
 - Pythonとの連携・ハイブリッド構成（Google Colab、Cloud Run / Cloud Functions上のPythonバックエンド、FastAPI / Flask等とのWebhook・API連携、Vertex AI / Gemini APIとの組み合わせ）
 - 外部サービスAPI・Googleツール群との高度な連携（BigQuery、Apache Iceberg、Looker Studio、Google Workspace Studio、MCP / A2Aサーバー、Slack / Discord / Notion / GitHub API、OAuth2認証やCloud Pub/Subを用いたイベント駆動パイプライン）
 - パフォーマンス最適化・設計パターン（バッチ処理、CacheService / PropertiesServiceの圧縮・チャンク分割、UrlFetchApp.fetchAllによる並列非同期リクエスト、WebAssembly / Web Workers活用、V8ランタイム最適化、実行時間6分制限やトリガー上限の回避アーキテクチャ）
2. 発見した事例の中から特に技術的価値や応用可能性が高いものを4件厳選し、それぞれの記事やリポジトリの具体的な内容を読み込む。
3. 厳選した各事例について、以下の項目を視覚的に分かりやすく簡潔な構成（結論・要点先頭、箇条書き活用、AIしぐさ完全排除）で日本語にまとめ、情報元の正確なリンクを添えて出力する:
 - **導入サマリー**（本日厳選した4件のテーマ・切り口の要約1段落）
 - **事例1〜4**（タイトルと概要、技術構成・アーキテクチャのポイント、具体的な応用アイデア）

### 【最重要】末尾のハッシュタグ出力ルール
- 見出し行は絶対に設置しないでください（設置禁止）。
- 記事の最後（4件目の事例の直後）に、空行を1行空けて、直接プレーンテキストのコードブロック（```text ... ```）で `#GAS #GoogleAppsScript` を含む12個の具体的な専門用語ハッシュタグを出力してください。
例：
```text
#GAS #GoogleAppsScript #専門用語3 #サービス名4 #フレームワーク名5 #API名6 #専門用語7 #専門用語8 #専門用語9 #専門用語10 #専門用語11 #専門用語12
```
"""

PROMPT_PART_C = """
Gemini 4 Argon（およびGemini 4 Carbon）、Google Antigravity、ならびにGoogle AI Studioを活用した実践的な活用法・最新アップデート情報をWebから収集し、Google AI Proプランで実現できる具体的な活用例やアイディアを中心に整理して私に届けてください。

### 実行手順
1. Web検索を行い、Gemini 4 Argon（gemini-4-argon）、Gemini 4 Carbon、Google Antigravity、Google AI Studioの最新機能、実践的なユースケース（コーディング自動化、仕様書駆動開発、レガシーコード近代化、3D/WebGPU生成、データ分析、エージェント開発、カスタムスキル・サブエージェント、MCP連携など）、およびGoogle AI Proプランでの利用範囲に関する直近の公開情報や技術記事をリサーチします。
2. 収集した情報の中から、Google AI Proプランで実際に試せる具体的かつ再現性の高い活用テクニックやプロンプト例、設定ファイル例、開発・業務効率化のアイディアを抽出します。過去に取り上げた基本的な概要の繰り返しを避け、直近の新しい検証事例や具体的な実装パターンを深掘りしてください。
3. 以下の構成で視覚的に分かりやすく簡潔に整理し、Markdown形式で報告してください：
 - **本日の注目トピック**（最新発表や機能更新、実測ベンチマークの要約・検証済みURLリンク付き）
 - **Google AI Proプランでできる実践活用例**（Antigravity、AI Studio、Gemini 4 Argonを組み合わせた具体的なユースケース）
 - **すぐに試せるワンポイントテクニック**（コピペで使えるコマンド、設定ファイル、またはプロンプト例を2点）
 - **参考元のリンク**（公式ドキュメントや発表記事の正確なURL一覧）

### 【最重要】末尾のハッシュタグ出力および署名ルール
- 見出し行は絶対に設置しないでください（設置禁止）。
- 参考元のリンクの直後に、空行を1行空けて、直接プレーンテキストのコードブロック（```text ... ```）で `#Gemini4Argon #GoogleAntigravity #GoogleAIStudio #GoogleAIPro` を含む12個のハッシュタグを出力してください。
- そして、レポート全体の最終行は、必ず以下の1行のみで終えてください：
早く2月にならないかな・・・
"""

PARTS_CONFIG = {
    "A": {
        "title": "デジタルスキル・資産マネタイズ調査",
        "tag_suffix": "本日のデジタル資産・スキルのマネタイズ",
        "prompt": PROMPT_PART_A,
        "filename_part": "part_a"
    },
    "B": {
        "title": "海外の高度GAS活用事例調査",
        "tag_suffix": "本日の高度GAS",
        "prompt": PROMPT_PART_B,
        "filename_part": "part_b"
    },
    "C": {
        "title": "Gemini 4 / Antigravity / AI Studio 活用調査",
        "tag_suffix": "本日の生成AIニュース",
        "prompt": PROMPT_PART_C,
        "filename_part": "part_c"
    }
}

def get_jst_now():
    return datetime.now(timezone(timedelta(hours=9)))

def get_jst_date_str(target_date=None):
    if target_date:
        return target_date
    return get_jst_now().strftime("%Y-%m-%d")

# ==========================================
# Google GenAI / Gemini Calls
# ==========================================

def get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("WARNING: GEMINI_API_KEY environment variable is not set.")
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Error initializing GenAI client: {e}")
        return None

def generate_report_text(part_key, target_date):
    cfg = PARTS_CONFIG[part_key]
    client = get_gemini_client()
    
    if not client:
        print(f"[{part_key}] Skipping API generation (no client). Using fallback placeholder.")
        return f"# {target_date} - {cfg['title']}\n\n自動生成準備完了（GEMINI_API_KEY設定待ち）"

    prompt = f"本日日付: {target_date} (JST)\n\n" + cfg["prompt"]
    print(f"[{part_key}] Generating report with Gemini...")
    
    # Try gemini-2.5-flash -> gemini-2.0-flash -> gemini-1.5-flash
    models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    for m in models_to_try:
        try:
            resp = client.models.generate_content(model=m, contents=prompt)
            if resp and resp.text:
                text = resp.text.strip()
                # Post-process Part C signature if needed
                if part_key == "C" and not text.endswith("早く2月にならないかな・・・"):
                    text += "\n\n早く2月にならないかな・・・"
                return text
        except Exception as err:
            print(f"[{part_key}] Model {m} failed: {err}")
            continue

    raise RuntimeError(f"Failed to generate report for Part {part_key} with all models.")

def generate_eyecatch_image(tag_text, target_date, output_path):
    client = get_gemini_client()
    prompt_res = generate_random_prompt(tag_text=tag_text, target_date=target_date)
    print(f"=== Eyecatch Prompt ({prompt_res['style_jp']} / {prompt_res['color_jp']}) ===")
    print(prompt_res["prompt"])

    if not client:
        print("GEMINI_API_KEY not found. Skipping image generation.")
        return False

    try:
        print("Calling Imagen 3 (imagen-3.0-generate-002)...")
        result = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=prompt_res["prompt"],
            config=dict(
                number_of_images=1,
                aspect_ratio="1:1",
                output_mime_type="image/png"
            )
        )
        if result and result.generated_images:
            img_bytes = result.generated_images[0].image.image_bytes
            with open(output_path, "wb") as f:
                f.write(img_bytes)
            print(f"Successfully generated and saved eyecatch: {output_path}")
            return True
    except Exception as e:
        print(f"Imagen 3 generation failed: {e}")
        # As fallback, create high quality placeholder image if pillow is available
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new("RGB", (1024, 1024), color=(20, 24, 33))
            draw = ImageDraw.Draw(img)
            draw.rectangle([50, 50, 974, 974], outline=(70, 80, 100), width=3)
            # Center text banner
            draw.text((512, 512), tag_text, fill=(255, 215, 0), anchor="mm")
            img.save(output_path)
            print(f"Saved fallback canvas to: {output_path}")
            return True
        except Exception as e2:
            print(f"Fallback canvas creation failed: {e2}")

    return False

# ==========================================
# Google Drive Uploader
# ==========================================

def upload_to_drive(file_path, file_name, mime_type, folder_id=DEFAULT_FOLDER_ID):
    """
    Uploads file to Google Drive.
    Priority 1: GAS Web App endpoint (bypasses service account quota limits).
    Priority 2: Google Service Account Key (if folder is in a Shared Drive).
    """
    gas_url = os.environ.get("GAS_UPLOAD_URL")
    gas_token = os.environ.get("GAS_UPLOAD_TOKEN", "")

    # Method 1: GAS WebApp
    if gas_url:
        print(f"Attempting upload via GAS WebApp: {gas_url}")
        try:
            import requests
            with open(file_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            
            payload = {
                "folderId": folder_id,
                "fileName": file_name,
                "mimeType": mime_type,
                "base64Content": b64,
                "token": gas_token
            }
            res = requests.post(gas_url, json=payload, timeout=60)
            if res.status_code == 200:
                data = res.json()
                if data.get("status") == "success":
                    print(f"SUCCESS [GAS]: Uploaded {file_name} -> ID: {data.get('fileId')}")
                    return True
                else:
                    print(f"GAS returned error: {data.get('message')}")
            else:
                print(f"GAS HTTP error {res.status_code}: {res.text}")
        except Exception as e:
            print(f"GAS upload exception: {e}")

    # Method 2: Service Account
    sa_key = os.environ.get("GCP_SA_KEY")
    if sa_key:
        print("Attempting upload via GCP Service Account...")
        try:
            import requests
            from google.oauth2 import service_account
            from google.auth.transport.requests import Request

            try:
                sa_info = json.loads(sa_key)
            except Exception:
                sa_info = json.load(open(sa_key)) if os.path.exists(sa_key) else None

            if sa_info:
                creds = service_account.Credentials.from_service_account_info(
                    sa_info, scopes=["https://www.googleapis.com/auth/drive"]
                )
                session = requests.Session()
                creds.refresh(Request(session=session))
                headers = {"Authorization": f"Bearer {creds.token}"}

                metadata = {"name": file_name, "parents": [folder_id]}
                with open(file_path, "rb") as f:
                    file_bytes = f.read()

                files = {
                    "data": ("metadata", json.dumps(metadata), "application/json; charset=UTF-8"),
                    "file": (file_name, file_bytes, mime_type)
                }
                res = session.post(
                    "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&supportsAllDrives=true",
                    headers=headers,
                    files=files,
                    timeout=60
                )
                if res.status_code == 200:
                    data = res.json()
                    print(f"SUCCESS [Service Account]: Uploaded {file_name} -> ID: {data.get('id')}")
                    return True
                else:
                    print(f"Service Account HTTP {res.status_code}: {res.text}")
        except Exception as e:
            print(f"Service Account upload exception: {e}")

    print(f"NOTE: Headless upload for {file_name} skipped or failed. File is preserved locally.")
    return False

# ==========================================
# Main Execution Pipeline
# ==========================================

def run_part(part_key, target_date, skip_image=False, skip_upload=False):
    cfg = PARTS_CONFIG[part_key]
    print(f"\n==========================================")
    print(f"Executing Part {part_key}: {cfg['title']}")
    print(f"Target Date: {target_date} (JST)")
    print(f"==========================================")

    # 1. Output paths
    reports_dir = SCRIPT_DIR.parent / "reports" / "daily"
    reports_dir.mkdir(parents=True, exist_ok=True)

    report_filename = f"{target_date}-{cfg['filename_part']}.md"
    report_path = reports_dir / report_filename

    tag_text = f"{target_date}#{cfg['tag_suffix']}"
    image_filename = f"{tag_text}.png"
    image_path = reports_dir / image_filename

    # 2. Generate and save Report Text
    report_text = generate_report_text(part_key, target_date)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"Saved report markdown: {report_path}")

    # 3. Generate Eyecatch Image
    image_created = False
    if not skip_image:
        image_created = generate_eyecatch_image(tag_text, target_date, image_path)

    # 4. Upload to Google Drive
    if not skip_upload:
        # Upload report
        upload_to_drive(report_path, report_filename, "text/markdown")
        # Upload image if created
        if image_created and image_path.exists():
            upload_to_drive(image_path, image_filename, "image/png")

    print(f"Completed Part {part_key} successfully.")
    return {
        "part": part_key,
        "report_file": str(report_path),
        "image_file": str(image_path) if image_created else None
    }

def main():
    parser = argparse.ArgumentParser(description="Daily Research & Eyecatch Pipeline")
    parser.add_argument("--part", choices=["A", "B", "C", "ALL"], default="ALL", help="Task part to execute")
    parser.add_argument("--date", default=None, help="Target date YYYY-MM-DD (defaults to JST today)")
    parser.add_argument("--skip-image", action="store_true", help="Skip image generation")
    parser.add_argument("--skip-upload", action="store_true", help="Skip Google Drive upload")
    args = parser.parse_args()

    target_date = get_jst_date_str(args.date)

    if args.part == "ALL":
        parts = ["A", "B", "C"]
    else:
        parts = [args.part]

    results = []
    for p in parts:
        res = run_part(p, target_date, skip_image=args.skip_image, skip_upload=args.skip_upload)
        results.append(res)

    print("\nAll tasks finished. Results summary:")
    for r in results:
        print(f" - Part {r['part']}: {r['report_file']} (Image: {r['image_file']})")

if __name__ == "__main__":
    main()
