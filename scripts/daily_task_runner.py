#!/usr/bin/env python3
"""
Daily Research & Eyecatch Automation Runner (note.com "やまねこ" Quality & Tone)
Part A (02:00 JST / 17:00 UTC): デジタル資産マネタイズ調査
Part B (03:30 JST / 18:30 UTC): 海外の高度GAS事例調査
Part C (04:00 JST / 19:00 UTC): Gemini 4 / Antigravity / AI Studio 活用調査

Strictly complies with Antigravity_Remote_Handover_Rules.md and user note articles:
- https://note.com/quirky_raven119/n/n918da28b96c8
- https://note.com/quirky_raven119/n/n72f5501a1cea
- https://note.com/quirky_raven119/n/n27856b8e3a0b
- https://note.com/quirky_raven119/n/n083a62f6df18
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
# Persona & Prompts matching note.com articles
# ==========================================

PERSONA_SYSTEM_HEADER = """
あなたは地方の海辺の町で日々の業務自動化やデータ分析・リスキリングに取り組んでいる個人開発者「やまねこ」（40代手前から海辺の町でリスキリング中、MOS Specialist/Expert 2016、Pythonエンジニア認定実践試験、G検定、統計検定2級、知的所有権管理技能士2級保有）です。

【最重要：身元特定防止ルール】
- 身元特定を防止するため、具体的な市町村名（竹原市、○○市など）やピンポイントな地名は絶対に記事内に登場させないでください。
- 地域文脈を表現する際は「海辺の町」「地方の拠点」「瀬戸内エリアの穏やかな地域資源」「ローカル線」といった一般的な表現のみを用いてください。

【文体および質・量（ボリューム）の厳格規定】
- noteアカウント（https://note.com/quirky_raven119）の過去記事と寸分違わぬ落ち着いたエンジニア・実務者トーンで執筆してください。
- 誇張表現や大げさなAI表現（「革命的な」「圧倒的」「魔法のような」「いかがでしたでしょうか」「言えるでしょう」「さあ、」等）は完全に排除してください。
- 1記事あたり3,500〜5,000文字程度の重厚な技術密度を確保し、表面的な概要だけでなく、具体的なクラス名・関数名・APIエンドポイント名・引数・計算量（O記法）・制限回避アーキテクチャの核心を深く掘り下げてください。
"""

PROMPT_PART_A = PERSONA_SYSTEM_HEADER + """
本日（{target_date}）付けの「デジタルスキル・資産マネタイズ調査」note記事を執筆してください。

【構成とタイトルフォーマット】
タイトル行：{target_date}#本日のデジタル資産・スキルのマネタイズ <本日フォーカスするテーマ1の具体的サービス・手法名>、<本日フォーカスするテーマ2の具体的サービス・手法名>

冒頭段落：
本日は、「<テーマ1>」と「<テーマ2>」に焦点を当ててお届けします。

1. **本日の注目マネタイズトレンド**
- 2つの注目テーマ（例：VoiceMap/izi.TRAVELによるGPS連動型多言語オーディオガイド販売、Premiere Pro用 .mogrt テンプレート販売、Polar.shでの開発者向けMoR決済直販、Wirestock一括配信、BOOTH/Gumroad等）を取り上げ、市場の仕組み、価格帯（$5〜$15、2,000円〜5,000円等）、収益化ロジック、AI（ElevenLabs等）や自動化ツールとの組み合わせ手法を詳細な長文で解説してください。

2. **カテゴリー別のおすすめマネタイズ手法と販売先**
以下の5カテゴリーすべてについて、具体的なプロダクト名・仕様・販売先を2点ずつ箇条書きで提示してください：
- ① GAS・Pythonコード
- ② 田舎の環境音（自然音・波音・雨音・虫の声）
- ③ 田舎の風景写真
- ④ 田舎の海の動画
- ⑤ 田舎の電車の動画

3. **個人が短時間で着手できる具体的なアクションプラン**
- 個人が今日・明日のスキマ時間（10〜15分程度）で即座に着手できる実践的な3ステップ（具体的な操作手順や確認先URLを含む）を提示してください。

4. **主な参照元・プラットフォームリンク**
- 記事内で言及した公式サービスやドキュメントの名称と正確なURL一覧。

【ハッシュタグ規程】
記事の末尾に、空行を1行空けて、直接プレーンテキストのコードブロック（```text ... ```）で、その日の記事に登場した具体的な専門用語・サービス名を反映した12個のハッシュタグを出力してください。見出し行（「3. note用ハッシュタグ」等）は絶対に設置しないでください。
"""

PROMPT_PART_B = PERSONA_SYSTEM_HEADER + """
本日（{target_date}）付けの海外の高度なGoogle Apps Script（GAS）活用事例調査note記事を執筆してください。

【構成とタイトルフォーマット】
タイトル行：{target_date}#本日の高度GAS事例 <事例1の技術概要>、<事例2の技術概要>、<事例3の技術概要>、<事例4の技術概要>

冒頭段落：
本日の海外における高度なGoogle Apps Script（GAS）活用事例レポートをお届けします。

<事例1概要>、<事例2概要>、<事例3概要>、<事例4概要>の4件を厳選しました。

1〜4. **厳選事例（全4件）**
各事例を以下のフォーマットで詳細に記述してください：
### <番号>. <事例のタイトル（英語原題または技術テーマ）>
- **概要**: <記事またはリポジトリのタイトル（URL）>（著者名 / 公開媒体・GitHub等）＋ 解決している現場の課題と全体像の要約。
- **技術構成・アーキテクチャのポイント**: 具体的な実装ロジック、データフロー、関数名・APIメソッド名（例：`documents.get`, `batchUpdate`, `HtmlService.createTemplateFromFile()`, `UrlFetchApp.fetchAll()`, `ScriptApp.getOAuthToken()`, `PropertiesService`, `LockService` 等）を交え、太字見出し付きで3点以上詳しく解説。
- **具体的な応用アイデア**: 業務自動化・データサイエンス教育・地域DX（オープンデータ可視化、施設マッピング、維持費ゼロのダッシュボード等）にどう転用できるかを実務目線で具体的に提示。

【ハッシュタグ規程】
記事の末尾に、空行を1行空けて、直接プレーンテキストのコードブロック（```text ... ```）で、`#GAS #GoogleAppsScript` を含む登場技術用語のハッシュタグ12個を出力してください。見出し行は絶対に設置しないでください。
"""

PROMPT_PART_C = PERSONA_SYSTEM_HEADER + """
本日（{target_date}）付けの「Gemini 4 / Antigravity / AI Studio」活用調査note記事を執筆してください。

【構成とタイトルフォーマット】
タイトル行：{target_date}#本日のAIニュース:<トピック1概要>の公開、<トピック2概要>、<トピック3概要>

冒頭段落：
<トピック1>の公開と、<トピック2>、さらに<トピック3>が明らかになりました。

**本日の注目トピック**
- 直近で発表・検証された重要トピック3件（例：40年前のFORTRANコードをPython/NumPyへ自動移植し40%高速化した事例、Gemini 4 Argon/Carbonの実測ベンチマーク、トークン効率評価等）について、ベンチマーク数値や移行アーキテクチャを詳細に解説。

**Google AI Pro プランでできる実践活用例**
- 地方の拠点や個人開発者が今日から手元の環境で試せる具体的な活用例2件（概要と効果を明記）。

**すぐに試せるワンポイントテクニック**
- コピペで使えるプロンプトテンプレート、設定ファイル、またはCLI/Pythonコード例2件（完全なコードブロック付き）。

**参考元リンク**
- 公式発表、ドキュメント、ベンチマーク記事の正確なタイトルとURL一覧。

【ハッシュタグ規程および末尾シグネチャー】
参考元リンクの直後に、空行を1行空けて、直接プレーンテキストのコードブロック（```text ... ```）で、`#Gemini4Argon #GoogleAntigravity #GoogleAIStudio #GoogleAIPro` を含む12個のハッシュタグを出力してください。
そして、記事全体の最終行は必ず以下の1行のみで終えてください：
早く2月にならないかな・・・
"""

PARTS_CONFIG = {
    "A": {
        "title": "デジタルスキル・資産マネタイズ調査",
        "tag_suffix": "本日のデジタル資産・スキルのマネタイズ",
        "prompt_template": PROMPT_PART_A,
        "filename_part": "part_a"
    },
    "B": {
        "title": "海外の高度GAS活用事例調査",
        "tag_suffix": "本日の高度GAS",
        "prompt_template": PROMPT_PART_B,
        "filename_part": "part_b"
    },
    "C": {
        "title": "Gemini 4 / Antigravity / AI Studio 活用調査",
        "tag_suffix": "本日の生成AIニュース",
        "prompt_template": PROMPT_PART_C,
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
    
    prompt = cfg["prompt_template"].format(target_date=target_date)
    print(f"[{part_key}] Generating report with Gemini (persona: やまねこ, date: {target_date})...")
    
    # Active Models: gemini-3.8-flash -> gemini-2.5-flash -> gemini-2.0-flash
    models_to_try = ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-2.0-flash"]
    if client:
        for m in models_to_try:
            try:
                resp = client.models.generate_content(model=m, contents=prompt)
                if resp and resp.text:
                    text = resp.text.strip()
                    # Clean any accidental city leakage just in case
                    text = text.replace("竹原市", "海辺の町").replace("竹原", "海辺の町")
                    if part_key == "C" and not text.endswith("早く2月にならないかな・・・"):
                        text += "\n\n早く2月にならないかな・・・"
                    print(f"[{part_key}] Successfully generated {len(text)} characters using model {m}!")
                    return text
            except Exception as err:
                print(f"[{part_key}] Model {m} failed: {err}")
                continue

    print(f"[{part_key}] All Gemini API attempts failed. Falling back to structured baseline report.")
    notice = f"> [!WARNING]\n> **GEMINI_API_KEY 更新推奨**: Google AI Studio（https://aistudio.google.com/app/apikey）から有効なAPIキーを取得し、GitHub Secretsの `GEMINI_API_KEY` を更新してください。\n\n"
    
    if part_key == "A":
        return notice + f"""# {target_date} 本日のデジタルスキル・資産マネタイズ調査レポート

1. **本日の注目マネタイズトレンド**
- **開発者向けMoR決済（Polar.sh）を活用したGAS/Pythonツール直販の加速**: 従来のGumroad等の手数料高騰（10%+決済手数料）に対し、販売手数料4%+決済手数料のみで利用できる開発者特化MoR「Polar.sh」が急速に台頭。GitHubログインと直結し、有料APIラッパーや自動化スクリプトのライセンスキー即時発行に対応。
- **地域環境音・ローカル鉄道ASMRのマルチストック＆睡眠・作業用BGM配信**: 地方の自然音（波音・虫の声・雨音）やローカル線の走行音を、Audiostock・Pond5・Wirestockへ一括配信しつつ、Spotify for Creatorsでポッドキャストとして収益化するハイブリッド展開が好調。

2. **カテゴリー別のおすすめマネタイズ手法と販売先**
- **① GAS・Pythonコード**: 業務自動化テンプレートやスプレッドシート連携ツールの「Polar.sh」または「BOOTH」での直販。
- **② 田舎の環境音**: ハイレゾ録音した瀬戸内の波音や雨音の「Audiostock」でのライセンス販売、および「Spotify」での作業用BGMポッドキャスト配信。
- **③ 田舎の風景写真**: 瀬戸内の海や古い町並みの高解像度写真を「Wirestock」を通じた海外ストックフォト一括配信、および「Etsy」でのPrintable Art販売。
- **④ 田舎の海の動画**: 4K定点撮影した穏やかな海景色の「Pond5」でのB-roll素材販売、およびYouTube長時間チル系作業用動画配信。
- **⑤ 田舎の電車の動画**: ローカル線の前面展望・車窓映像をCapCut/Premiere Pro用テンプレート素材化して販売。

3. **個人が短時間で着手できる具体的なアクションプラン**
- **Step 1（10分）**: 手持ちのGAS自動化スクリプトから機密情報を除外し、配布用テンプレートを作成。
- **Step 2（15分）**: Polar.sh または BOOTH にアカウントを開設し、デジタルプロダクトとして登録。
- **Step 3（5分）**: note および X（Twitter）に解説記事の概要を投稿し、販売導線を設置。

4. **主な参照元・プラットフォームリンク**
- [Polar.sh (Developer First MoR)](https://polar.sh/)
- [Audiostock](https://audiostock.jp/)
- [Wirestock Global Distribution](https://wirestock.io/)
- [Pond5 Stock Footage](https://www.pond5.com/)

```text
#Polar #Audiostock #Wirestock #Pond5 #GAS #Python #デジタル資産 #マネタイズ #環境音 #ストックフォト #ASMR #スモールビジネス
```
"""
    elif part_key == "B":
        return notice + f"""# {target_date} 海外の高度なGoogle Apps Script（GAS）活用事例レポート

1. **導入サマリー**
本日は、GASの6分実行時間制限・1000万セル上限・UI制約を外部のモダンエコシステム（Apache Iceberg、Cloud Run、OpenStreetMap、React）と連携して突破する高度なアーキテクチャ事例4選を厳選しました。

2. **厳選事例**
- **事例1: [IcebergApp: Serverless Lakehouse on BigQuery with GAS](https://dev.to/gde/unifying-google-workspace-and-apache-iceberg-serverless-lakehouse-management-ep3)**
  - **技術構成**: GASからBigQuery REST APIを呼び出し、Apache Icebergテーブルのメタデータ管理・タイムトラベルクエリを実行。
  - **応用アイデア**: スプレッドシートをBIフロントエンドとし、ペタバイト級のデータレイクハウスをサーバーレスで直接操作する社内ダッシュボード。
- **事例2: [Cloud Run Sandboxes (gVisor + FastAPI) with GAS](https://medium.com/google-cloud/taking-advantage-of-cloud-run-sandboxes-with-google-apps-script-for-google-workspace-560348c06f40)**
  - **技術構成**: GASの非同期`UrlFetchApp`からCloud Run上のFastAPIサイドカーを呼び出し、Pandasによる重い集計やSeabornグラフ描画をサブ秒で実行。
  - **応用アイデア**: GASの計算性能ボトルネックを完全解消し、科学計算・データ解析をスプレッドシート上で完結。
- **事例3: [Geocoding with OpenStreetMap & PostGIS in GAS](https://github.com/mazenelkadi/Geocode-Addresses-with-OpenStreetMap-in-Google-Sheets)**
  - **技術構成**: Nominatim APIとGAS JDBC経由のPostgreSQL/PostGIS連携による双方向ジオコーディング。
  - **応用アイデア**: 地域店舗や避難所データの自動マッピング、シビックテックにおけるオープンデータ可視化。
- **事例4: [React-Google-Apps-Script with Vite & Tailwind CSS](https://github.com/enuchi/React-Google-Apps-Script)**
  - **技術構成**: HtmlService上にViteでシングルファイルビルドされたReact 18 SPAを展開。
  - **応用アイデア**: 業務アプリとして申し分のないモダンUIとレスポンシブデザインをGoogle Workspace拡張機能内に構築。

```text
#GAS #GoogleAppsScript #BigQuery #ApacheIceberg #CloudRun #FastAPI #OpenStreetMap #PostGIS #React #Vite #TailwindCSS #RESTAPI
```
"""
    else: # Part C
        return notice + f"""# {target_date} Gemini 4 / Antigravity / AI Studio 実践活用レポート

1. **本日の注目トピック**
- **Gemini 4 Argon & Carbon の実測ベンチマーク**: 100万トークン統合コンテキストとThinking Level（`low`/`medium`/`high`）制御による長文コードリファクタリング性能が向上。
- **Google Antigravity 自律エージェントの仕様書駆動開発（Spec-Driven Development）**: Data Spec、Agent Spec、Client Spec、Implementation Plan を組み合わせたマルチエージェント統制の実践事例が拡大。

2. **Google AI Proプランでできる実践活用例**
- **大規模レガシーコードの夜間自動近代化**: Antigravity の Remote Agent 機能により、手元PCの電源が落ちていてもクラウドVM上でユニットテスト生成・型安全リファクタリングを完結。
- **Google AI Studio Build によるWebアプリ即時生成**: 自然言語仕様からCloud Runデプロイ対応のフルスタックアプリを数分でプロトタイピング。

3. **すぐに試せるワンポイントテクニック**
- **テクニック1: 暗黙的コンテキストキャッシュの活用**: 4,096トークン以上のプロンプトで自動適用されるキャッシュにより、反復推論コストを95%削減。
- **テクニック2: Spec-Driven なプロンプト構造化**: `Goal` / `Context` / `Rules` / `Task` / `Output` / `Verification` の6要素フレームワークによるハルシネーション抑制。

4. **参考元のリンク**
- [Google AI Studio Official](https://aistudio.google.com/)
- [Introducing Gemini 4 Models (Google Blog)](https://blog.google/)
- [Google Antigravity Documentation](https://antigravity.google/)

```text
#Gemini4Argon #GoogleAntigravity #GoogleAIStudio #GoogleAIPro #SpecDrivenDevelopment #RemoteAgents #PromptEngineering #ContextCaching #LLM #CloudRun #DeveloperTools #CodeModernization
```

早く2月にならないかな・・・"""

def generate_eyecatch_image(tag_text, target_date, output_path):
    client = get_gemini_client()
    prompt_res = generate_random_prompt(tag_text=tag_text, target_date=target_date)
    print(f"=== Eyecatch Prompt ({prompt_res['style_jp']} / {prompt_res['color_jp']}) ===")
    print(prompt_res["prompt"])

    if not client:
        print("GEMINI_API_KEY not found. Skipping image generation.")
        return False

    # Try generate_content with image generation models
    image_models = ["gemini-2.5-flash-image", "gemini-3.1-flash-image", "gemini-3-pro-image"]
    for m in image_models:
        try:
            print(f"Calling image model {m} via generate_content...")
            resp = client.models.generate_content(
                model=m,
                contents=prompt_res["prompt"]
            )
            if resp and resp.candidates and resp.candidates[0].content.parts:
                for p in resp.candidates[0].content.parts:
                    if p.inline_data and p.inline_data.data:
                        with open(output_path, "wb") as f:
                            f.write(p.inline_data.data)
                        print(f"SUCCESS! Generated eyecatch ({m}): {output_path} (size: {len(p.inline_data.data)} bytes)")
                        return True
        except Exception as e:
            print(f"Model {m} failed: {e}")
            continue

    # Fallback to Pillow canvas if all image models fail
    try:
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (1024, 1024), color=(20, 24, 33))
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, 974, 974], outline=(70, 80, 100), width=3)
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

    print(f"NOTE: Headless upload for {file_name} skipped or preserved locally.")
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
