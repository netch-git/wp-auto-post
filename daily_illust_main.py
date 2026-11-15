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

# 画像生成モデル（優先順位リスト）
PRIMARY_IMAGEN_MODEL = os.environ.get("IMAGEN_MODEL", "imagen-3.0-generate-002")
IMAGEN_MODELS_TRY = [
    PRIMARY_IMAGEN_MODEL,
    "imagen-3.0-generate-002",
    "imagen-3.0-fast-generate-001",
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
    """サービスアカウントでGoogle Sheets APIとDrive APIのクライアントを初期化"""
    sa_key_str = os.environ.get("GCP_SA_KEY")
    if not sa_key_str:
        # ローカル実行時のフォールバック探索
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
        raise ValueError("環境変数 GCP_SA_KEY が設定されていません。")

    sa_info = json.loads(sa_key_str)
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = service_account.Credentials.from_service_account_info(sa_info, scopes=scopes)
    sheets_service = build("sheets", "v4", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)
    return sheets_service, drive_service


def fetch_seasonal_row(sheets_service, target_month: str) -> dict:
    """スプレッドシートの「マスタ」から当月の行を抽出しランダムに1件返す"""
    result = (
        sheets_service.spreadsheets()
        .values()
        .get(spreadsheetId=SPREADSHEET_ID, range="マスタ!A2:G")
        .execute()
    )
    rows = result.get("values", [])
    if not rows:
        raise ValueError("「マスタ」シートにデータが見つかりません。")

    matching_rows = [r for r in rows if len(r) >= 7 and str(r[0]).strip() == target_month]
    if not matching_rows:
        print(f"警告: {target_month}月のデータが見つからないため全行から抽選します。")
        matching_rows = [r for r in rows if len(r) >= 7]

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

Output ONLY the final English prompt text, ready to pass directly to Imagen. No markdown formatting, no quotes, no preamble.
"""

    # gemini-2.5-flash -> gemini-2.0-flash
    models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash"]
    last_err = None
    for m in models_to_try:
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


def generate_image_with_retry(genai_client: genai.Client, prompt: str) -> bytes:
    """Imagen APIを呼び出して画像を生成（モデルフォールバック＆リトライ付き）"""
    seen_models = []
    for model_name in IMAGEN_MODELS_TRY:
        if model_name in seen_models:
            continue
        seen_models.append(model_name)

        for attempt in range(1, 3):
            try:
                print(f"画像生成を実行中 [モデル: {model_name}] (試行 {attempt}/2)...")
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
                    print(f"画像生成成功: {model_name}")
                    return result.generated_images[0].image.image_bytes
            except Exception as e:
                print(f"モデル {model_name} (試行 {attempt}) 失敗: {e}")
                time.sleep(3 * attempt)

    raise RuntimeError("すべてのImagenモデルでの生成が失敗しました。")


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
    """Google Driveの指定フォルダに画像をアップロードしURLを返す"""
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

        # 3. Imagenで画像生成
        raw_image = generate_image_with_retry(genai_client, prompt)

        # 4. 右下に日付・サインを焼き込み
        sign_text = f"{TODAY_STR} {SIGN_LABEL}"
        signed_image = add_signature(raw_image, sign_text)

        # 5. Google Driveに保存
        filename = f"{TODAY_STR}_month{CURRENT_MONTH}_{int(time.time())}.png"
        drive_url = upload_to_drive(drive_service, signed_image, filename)
        print(f"アップロード完了: {drive_url}")

        # 6. ログシートに記録
        append_log_to_sheet(sheets_service, row_data, prompt, drive_url, "SUCCESS")
        print("=== 全工程が正常に完了しました ===")

    except Exception as e:
        print(f"エラー発生: {e}")
        try:
            append_log_to_sheet(sheets_service, row_data, prompt, drive_url, f"ERROR: {str(e)[:100]}")
        except Exception as log_err:
            print(f"ログ記録失敗: {log_err}")
        raise


if __name__ == "__main__":
    main()
