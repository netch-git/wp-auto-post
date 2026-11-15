import os
import json
import random
import datetime
import io
import time
from zoneinfo import ZoneInfo

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont

# ==========================================
# 環境変数と設定（デフォルト値でフォールバック完備）
# ==========================================
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID") or "1Tg4GKLDqiIcbNudSvK8C6Uw_XIqdNNSi6hOZjlifKxY"
DRIVE_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID") or "17qo8NbDC_D6Xdbz1b6oo6OxXIIBFaezK"

# テキスト生成モデル（環境変数で柔軟に変更可能）
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")

# 画像生成モデル（環境変数で柔軟に変更可能）
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "gemini-2.5-flash-image")
IMAGE_MODELS_TRY = [
    IMAGE_MODEL,
    "gemini-2.5-flash-image",
    "gemini-3.1-flash-image",
    "gemini-3-pro-image",
]

# サインテキストのラベル（日付の後に付与される）
SIGN_LABEL = os.environ.get("SIGN_LABEL", "#DailySketch")


JST = ZoneInfo("Asia/Tokyo")
NOW_JST = datetime.datetime.now(JST)
TODAY_STR = NOW_JST.strftime("%Y-%m-%d")
CURRENT_MONTH = str(NOW_JST.month)

# ==========================================
# ベースとなる「3人の女性と画風」の絶対ルール
# ==========================================
BASE_STORY_GUIDELINE = """
You are an expert art director writing an image generation prompt for Imagen 3/4.
Follow these strict rules without exception:

1. VISUAL STYLE & MEDIUM (NON-NEGOTIABLE):
- Modern Japanese commercial art book editorial illustration.
- Exact visual tone: delicate uniform fineliner ink outlines (ligne claire), matte gouache and transparent watercolors on cold-press paper with visible paper grain.
- Palette: muted atmospheric earth tones. A small number of impactful vibrant colors are permitted ONLY for life-enriching focal elements like illuminations, fireworks, or soap bubbles.
- STRICTLY PROHIBITED: plastic-like CGI glossy objects, 3D digital gradient gloss, simple flat gradients, moe anime tropes, oversized sparkling eyes, exaggerated open-mouthed anime smiles, blushing cheeks.
- NO TEXT: The image must contain zero text, zero letters, and zero pseudo-glyphs on signs, boards, or clothing.

2. CAMERA & SPATIAL CLEARANCE:
- Wide pulled-back architectural perspective, accurately framed in perspective.
- Spacious environment with natural, realistic spacing and unobstructed floor/walkway clearance in front of figures.

3. THE THREE RECURRING CHARACTERS (STORY CONTINUITY):
Always feature these three distinct junior high/high school girls naturally integrated into the seasonal scene (adapt outerwear/sleeves realistically to match the season while preserving their core identities):
- Girl 1: Short black bob cut, wearing a neat navy school uniform (adapt to summer/winter naturally), carrying a navy duffel bag, calm and observant demeanor.
- Girl 2: Loosely wavy chestnut brown ponytail, wearing an oversized beige cardigan over her uniform (or summer equivalent if hot), relaxed natural contrapposto pose.
- Girl 3: Sporty layered dark hair, hands in pockets (when wearing blazer/jacket/cardigan), canvas tote bag over her shoulder, casually interacting with her friends.

4. COHESIVE INTERACTION & EXPRESSIONS:
- Arrange their natural daily movements (walking, standing, sitting, conversing, or quiet emotion) cohesively so they share a unified atmosphere (never draw unnatural combinations like one laughing while two are crying).
- Use understated, calm, mature micro-expressions with closed or gently relaxed mouths.
"""


def get_google_services():
    """Google Sheets APIとDrive APIのクライアントを初期化（ユーザーOAuth優先 / SAフォールバック）"""
    # ルート1: ユーザーのOAuth認証情報（リフレッシュトークン方式でサービスアカウントの0GB制限を完全解消）
    refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN")
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    if refresh_token and client_id and client_secret:
        try:
            print("ユーザーOAuth認証情報（GOOGLE_REFRESH_TOKEN）を使用します。")
            from google.oauth2.credentials import Credentials as UserCredentials
            user_creds = UserCredentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret,
                scopes=[
                    "https://www.googleapis.com/auth/drive",
                    "https://www.googleapis.com/auth/spreadsheets",
                ]
            )
            sheets_service = build("sheets", "v4", credentials=user_creds)
            drive_service = build("drive", "v3", credentials=user_creds)
            return sheets_service, drive_service
        except Exception as e:
            print(f"⚠️ ユーザーOAuth初期化スキップ: {e}")

    # ルート2: サービスアカウント認証情報（GCP_SA_KEY）
    sa_key_str = os.environ.get("GCP_SA_KEY")
    if not sa_key_str:
        local_key_paths = [
            "/tmp/gemini-ai-lab-key.json",
            os.path.expanduser("~/.gemini/gcp-keys/gemini-ai-lab-key.json"),
            r"G:\マイドライブ\antigravity\credentials\gemini-ai-lab-key.json",
        ]
        for p in local_key_paths:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    sa_key_str = f.read()
                print(f"ローカル鍵ファイルを使用: {p}")
                break

    if not sa_key_str:
        raise ValueError("環境変数 GCP_SA_KEY または GOOGLE_REFRESH_TOKEN が設定されていません。")

    sa_info = json.loads(sa_key_str)
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = service_account.Credentials.from_service_account_info(sa_info, scopes=scopes)
    sheets_service = build("sheets", "v4", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)
    return sheets_service, drive_service



FALLBACK_NOVEMBER_SEEDS = [
    {
        "month": "11",
        "kigo_props": "落ち葉の絨毯・焼き芋の紙袋・木製ベンチ",
        "location": "晩秋の静かなイチョウ並木の歩道",
        "attire_note": "トレンチコート・チェック柄マフラー・ニットベスト",
        "gesture": "ベンチに腰掛け温かい紙袋を膝に置いて並木を眺める",
        "lighting": "午後3時・黄金色の柔らかい秋の斜光",
        "seed": "late November afternoon on quiet tree-lined pedestrian avenue covered in golden ginkgo leaves, trench coat, tartan muffler, holding warm paper bag quietly on wooden bench, slanting warm golden sunlight",
    },
    {
        "month": "11",
        "kigo_props": "防寒カーディガン・温かい缶コーヒー・自転車の荷台",
        "location": "夕暮れのコインランドリーの軒下ベンチ",
        "attire_note": "オーバーサイズのベージュカーディガン・ネイビー制服",
        "gesture": "両手で温かい缶を持ち静かに夕暮れの空を見上げる",
        "lighting": "午後5時・藍色と茜色が混ざり合う薄暮のグラデーション",
        "seed": "November twilight outside retro laundromat, oversized beige cardigan over uniform, holding warm canned drink with both hands, calm gaze into dusk sky",
    },
]


def fetch_seasonal_row(sheets_service, target_month: str) -> dict:
    """スプレッドシートの「マスタ」から当月の行を抽出しランダムに1件返す（Sheets API未有効時は安全にフォールバック）"""
    try:
        result = (
            sheets_service.spreadsheets()
            .values()
            .get(spreadsheetId=SPREADSHEET_ID, range="マスタ!A2:G")
            .execute()
        )
        rows = result.get("values", [])
        if rows:
            matching_rows = [r for r in rows if len(r) >= 7 and str(r[0]).strip() == target_month]
            if not matching_rows:
                matching_rows = [r for r in rows if len(r) >= 7]
            if matching_rows:
                chosen = random.choice(matching_rows)
                return {
                    "month": chosen[0],
                    "kigo_props": chosen[1],
                    "location": chosen[2],
                    "attire_note": chosen[3],
                    "gesture": chosen[4],
                    "lighting": chosen[5],
                    "seed": chosen[6],
                }
    except Exception as e:
        print(f"⚠️ Sheets APIマスタ取得スキップ（フォールバックを使用）: {e}")

    # フォールバックシードを返す
    print(f"マスタDBフォールバックシードから{target_month}月を抽出します。")
    return random.choice(FALLBACK_NOVEMBER_SEEDS)



def build_prompt_with_gemini(genai_client: genai.Client, row_data: dict) -> str:
    """Gemini Flashを使用して、当月のシチュエーションと3人の物語ルールを統合した完璧な英語プロンプトを生成"""
    user_instruction = f"""
Create a single, cohesive English image generation prompt (around 150-220 words) combining the following seasonal scene data with the 3 recurring characters and strict artistic rules.

[Seasonal Scene Seed from Master DB]
- Month: {row_data['month']}
- Seasonal Props / Kigo: {row_data['kigo_props']}
- Location & Architecture: {row_data['location']}
- Seasonal Attire Adjustment: {row_data['attire_note']}
- Cohesive Action / Atmosphere: {row_data['gesture']}
- Time & Lighting: {row_data['lighting']}
- English Reference Seed: {row_data['seed']}

Output ONLY the final English prompt text, ready to pass directly to image generation. No markdown formatting, no quotes, no preamble.
"""

    # 環境変数指定モデルを優先し、未サポート時は自動フォールバック
    models_to_try = [GEMINI_MODEL, "gemini-3.8-flash", "gemini-3.7-flash", "gemini-2.5-flash"]
    seen = []
    last_err = None
    for m in models_to_try:
        if m in seen:
            continue
        seen.append(m)

        try:
            response = genai_client.models.generate_content(
                model=m,
                contents=user_instruction,
                config=types.GenerateContentConfig(
                    system_instruction=BASE_STORY_GUIDELINE,
                    temperature=0.7,
                ),
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"Gemini prompt generation failed: {last_err}")


IMAGE_MODELS_TRY = [
    "gemini-2.5-flash-image",
    "gemini-3.1-flash-image",
    "gemini-3-pro-image",
]


def generate_image_with_retry(genai_client: genai.Client, prompt: str) -> bytes:
    """
    画像生成実行関数（Imagen系 / Gemini Native Image系の両方式に完全自動対応）
    ・imagen-*系: client.models.generate_images(prompt=..., config=GenerateImagesConfig(aspect_ratio="16:9"))
    ・gemini-*-image系: client.models.generate_content(contents=..., config=GenerateContentConfig(response_modalities=["IMAGE"]))
    """
    seen_models = []
    for model_name in IMAGE_MODELS_TRY:
        if model_name in seen_models:
            continue
        seen_models.append(model_name)

        for attempt in range(1, 3):
            try:
                print(f"画像生成を実行中 [モデル: {model_name}] (試行 {attempt}/2)...")

                # パターンA: imagen-* 系モデル (generate_images)
                if "imagen" in model_name.lower():
                    result = genai_client.models.generate_images(
                        model=model_name,
                        prompt=prompt,
                        config=types.GenerateImagesConfig(
                            number_of_images=1,
                            aspect_ratio="16:9",
                            output_mime_type="image/png",
                        ),
                    )
                    if result.generated_images:
                        img_bytes = result.generated_images[0].image.image_bytes
                        print(f"画像生成成功 (generate_images)! [モデル: {model_name}] (サイズ: {len(img_bytes)} bytes)")
                        return img_bytes

                # パターンB: gemini-*-image 系モデル (generate_content with response_modalities=["IMAGE"])
                else:
                    resp = genai_client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_modalities=["IMAGE"],
                        ),
                    )
                    if resp and resp.candidates and resp.candidates[0].content.parts:
                        for part in resp.candidates[0].content.parts:
                            if part.inline_data and part.inline_data.data:
                                print(f"画像生成成功 (generate_content)! [モデル: {model_name}] (サイズ: {len(part.inline_data.data)} bytes)")
                                return part.inline_data.data

            except Exception as e:
                print(f"モデル {model_name} (試行 {attempt}) 失敗: {e}")
                time.sleep(2 * attempt)

    raise RuntimeError("すべての画像モデル・API方式での生成が失敗しました。")




def add_signature(image_bytes: bytes, signature_text: str) -> bytes:
    """Pillowを使用して右下に影付きのサインを綺麗に焼き込む"""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    font_size = max(18, int(img.width * 0.018))
    font = None
    font_paths = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:\\Windows\\Fonts\\meiryo.ttc",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, font_size)
                break
            except Exception:
                continue

    if font is None:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), signature_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    margin_x = int(img.width * 0.025)
    margin_y = int(img.height * 0.03)
    x = img.width - text_w - margin_x
    y = img.height - text_h - margin_y

    shadow_offset = max(2, int(font_size * 0.08))
    draw.text((x + shadow_offset, y + shadow_offset), signature_text, font=font, fill=(20, 20, 20, 140))
    draw.text((x, y), signature_text, font=font, fill=(250, 248, 245, 220))

    combined = Image.alpha_composite(img, overlay).convert("RGB")
    out_buffer = io.BytesIO()
    combined.save(out_buffer, format="PNG", quality=95)
    return out_buffer.getvalue()


def upload_to_drive(drive_service, image_bytes: bytes, filename: str) -> str:
    """
    Google Driveの指定フォルダに画像をアップロードしURLを返す
    Priority 1: GAS WebApp (サービスアカウントの0GB制限を完全回避し、ユーザーのマイドライブへ安全保存)
    Priority 2: Drive API v3 (Shared Drive等)
    """
    gas_url = os.environ.get("GAS_UPLOAD_URL")
    gas_token = os.environ.get("GAS_UPLOAD_TOKEN", "")

    if gas_url:
        print(f"GAS WebApp経由でDrive保存を実行中: {gas_url[:35]}...")
        try:
            import base64
            import requests

            b64_str = base64.b64encode(image_bytes).decode("utf-8")
            payload = {
                "folderId": DRIVE_FOLDER_ID,
                "fileName": filename,
                "mimeType": "image/png",
                "base64Content": b64_str,
                "token": gas_token,
            }
            res = requests.post(gas_url, json=payload, timeout=90, allow_redirects=True)
            if res.status_code == 200:
                data = res.json()
                if data.get("status") == "success":
                    file_id = data.get("fileId")
                    file_url = data.get("url") or f"https://drive.google.com/file/d/{file_id}/view"
                    print(f"アップロード成功 (GAS経由)! File ID: {file_id}")
                    return file_url
                else:
                    print(f"⚠️ GAS returned error: {data.get('message')}")
            else:
                print(f"⚠️ GAS HTTP status: {res.status_code}")
        except Exception as gas_err:
            print(f"⚠️ GAS upload attempt failed: {gas_err}")

    # Fallback: Drive API v3
    file_metadata = {
        "name": filename,
        "parents": [DRIVE_FOLDER_ID],
    }
    media = MediaIoBaseUpload(io.BytesIO(image_bytes), mimetype="image/png", resumable=True)
    uploaded = (
        drive_service.files()
        .create(body=file_metadata, media_body=media, fields="id, webViewLink", supportsAllDrives=True)
        .execute()
    )
    return uploaded.get("webViewLink", f"https://drive.google.com/file/d/{uploaded['id']}/view")


def append_log_to_sheet(sheets_service, row_data: dict, prompt: str, drive_url: str, status: str):
    """スプレッドシートの「生成ログ」シートに結果を1行追記"""
    timestamp = NOW_JST.strftime("%Y-%m-%d %H:%M:%S")
    values = [[
        timestamp,
        row_data.get("month", CURRENT_MONTH),
        row_data.get("kigo_props", ""),
        row_data.get("location", ""),
        "3名の女子生徒（黒髪ボブ・栗色ポニテ・ショート）",
        prompt,
        drive_url,
        status,
    ]]
    sheets_service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range="生成ログ!A:H",
        valueInputOption="USER_ENTERED",
        body={"values": values},
    ).execute()


def main():
    print(f"=== 日常イラスト自動生成開始 ({TODAY_STR} / 対象月: {CURRENT_MONTH}月) ===")
    sheets_service, drive_service = get_google_services()

    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        raise ValueError("環境変数 GEMINI_API_KEY が設定されていません。")
    genai_client = genai.Client(api_key=gemini_key)

    row_data = {}
    prompt = ""
    drive_url = ""

    try:
        # 1. マスタから当月のシチュエーションを抽選
        row_data = fetch_seasonal_row(sheets_service, CURRENT_MONTH)
        print(f"抽選完了: [{row_data['kigo_props']}] @ {row_data['location']}")

        # 2. Gemini Flashでプロンプト生成
        prompt = build_prompt_with_gemini(genai_client, row_data)
        print(f"構築プロンプト:\n{prompt}\n")

        # 3. 画像生成
        raw_image = generate_image_with_retry(genai_client, prompt)

        # 4. 右下に日付・サインを焼き込み
        sign_text = f"{TODAY_STR} {SIGN_LABEL}"
        signed_image = add_signature(raw_image, sign_text)

        # 5. ローカルキャッシュ保存 (GitHub Actions Artifact用)
        filename = f"{TODAY_STR}_month{CURRENT_MONTH}_{int(time.time())}.png"
        os.makedirs("output_images", exist_ok=True)
        local_filepath = os.path.join("output_images", filename)
        with open(local_filepath, "wb") as f:
            f.write(signed_image)
        print(f"ローカル保存完了: {local_filepath}")

        # 6. Google Driveに保存 (GAS優先 / 0GB制限回避)
        try:
            drive_url = upload_to_drive(drive_service, signed_image, filename)
            print(f"Driveアップロード完了: {drive_url}")
        except Exception as drive_err:
            print(f"⚠️ Driveアップロード失敗（Artifactに保存済み）: {drive_err}")
            drive_url = f"GitHub Artifact: {filename}"


        # 6. ログシートに記録（万が一のAPI未有効時も警告で安全継続）
        try:
            append_log_to_sheet(sheets_service, row_data, prompt, drive_url, "SUCCESS")
        except Exception as log_err:
            print(f"⚠️ スプレッドシートログ記録スキップ: {log_err}")
        print("=== 全工程が正常に完了しました ===")

    except Exception as e:
        print(f"エラー発生: {e}")
        try:
            append_log_to_sheet(sheets_service, row_data, prompt, drive_url, f"ERROR: {str(e)[:100]}")
        except Exception as log_err:
            print(f"ログ記録スキップ: {log_err}")
        raise



if __name__ == "__main__":
    main()
