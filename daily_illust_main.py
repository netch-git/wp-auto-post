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
# 設定
# ==========================================
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID") or "1Tg4GKLDqiIcbNudSvK8C6Uw_XIqdNNSi6hOZjlifKxY"
DRIVE_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID") or "17qo8NbDC_D6Xdbz1b6oo6OxXIIBFaezK"

# Imagen 3 最高精度モデルを最優先
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "imagen-3.0-generate-002")
IMAGE_MODELS_TRY = [
    IMAGE_MODEL,
    "imagen-3.0-generate-002",
    "imagen-3.0-generate-001",
    "gemini-3.1-flash-image",
]

JST = ZoneInfo("Asia/Tokyo")
NOW_JST = datetime.datetime.now(JST)
TODAY_STR = NOW_JST.strftime("%Y-%m-%d")
CURRENT_MONTH = str(NOW_JST.month)

# 毎日配信する3つのテーマ
DAILY_THEMES = [
    {
        "id": "monetize",
        "tag_full": f"{TODAY_STR}#本日のデジタル資産・スキルのマネタイズ",
        "lines": [TODAY_STR, "#本日のデジタル資産", "スキルのマネタイズ"],
    },
    {
        "id": "gas",
        "tag_full": f"{TODAY_STR}#本日の高度GAS事例",
        "lines": [TODAY_STR, "#本日の高度GAS事例"],
    },
    {
        "id": "ai",
        "tag_full": f"{TODAY_STR}#本日の生成AIニュース",
        "lines": [TODAY_STR, "#本日の生成AIニュース"],
    },
]

# ランダム蛍光カラーパレット（手書きネオンサイン用）
NEON_PALETTES = [
    {"name": "neon_magenta", "fill": (255, 0, 128), "glow": (255, 255, 255), "shadow": (20, 10, 15)},
    {"name": "neon_cyan", "fill": (0, 240, 255), "glow": (255, 255, 255), "shadow": (10, 15, 25)},
    {"name": "neon_green", "fill": (57, 255, 20), "glow": (255, 255, 255), "shadow": (10, 25, 10)},
    {"name": "neon_yellow", "fill": (255, 255, 0), "glow": (255, 255, 255), "shadow": (25, 25, 10)},
]


def get_google_services():
    refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN")
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    if refresh_token and client_id and client_secret:
        try:
            from google.oauth2.credentials import Credentials as UserCredentials
            user_creds = UserCredentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret,
                scopes=["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
            )
            return build("sheets", "v4", credentials=user_creds), build("drive", "v3", credentials=user_creds)
        except Exception as e:
            print(f"⚠️ OAuth初期化スキップ: {e}")

    sa_key_str = os.environ.get("GCP_SA_KEY")
    if not sa_key_str:
        for p in ["/tmp/gemini-ai-lab-key.json", os.path.expanduser("~/.gemini/gcp-keys/gemini-ai-lab-key.json"), r"G:\マイドライブ\antigravity\credentials\gemini-ai-lab-key.json"]:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    sa_key_str = f.read()
                break

    sa_info = json.loads(sa_key_str)
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = service_account.Credentials.from_service_account_info(sa_info, scopes=scopes)
    return build("sheets", "v4", credentials=creds), build("drive", "v3", credentials=creds)


FALLBACK_SEEDS = [
    {
        "month": "11",
        "kigo_props": "黄色いイチョウの並木・敷き詰められた落ち葉・通学鞄",
        "location": "11月中旬・広々とした秋晴れの学校前のイチョウ並木通り",
        "attire_note": "ネイビー冬制服・ブレザー",
        "gesture": "落ち葉の上を穏やかに歩き、自然に微笑み合う",
        "lighting": "午前8時・朝霧を透かして射し込む澄んだ黄金色の斜光",
        "seed": "crisp morning autumn sunlight filtering through vibrant golden ginkgo canopy, spacious pedestrian avenue",
    },
    {
        "month": "11",
        "kigo_props": "木枯らし・温かい缶コーヒー・自転車の荷台",
        "location": "11月末の肌寒い夕暮れ・田舎駅の改札前ベンチ",
        "attire_note": "ウールコート・チェック柄マフラー・革の手袋",
        "gesture": "ベンチに腰掛け、温かい缶を持ちながら次の電車を待つ",
        "lighting": "午後5時・藍色と茜色が混ざり合う薄暮のグラデーション",
        "seed": "late November twilight at quiet rural train station bench, holding warm canned drink, peaceful dusk sky",
    },
    {
        "month": "11",
        "kigo_props": "海風・白波・テトラポッド・潮の香り",
        "location": "初冬の穏やかな瀬戸内海沿いの防波堤遊歩道",
        "attire_note": "厚手の冬ブレザー・大きめカーディガン・キャンバストート",
        "gesture": "防波堤を背に歩き、海を眺めながら静かに会話する",
        "lighting": "午後3時・低い冬の太陽が海面にきらめく銀色の反射光",
        "seed": "coastal sea embankment walkway, gentle waves crashing on breakwater, shimmering winter sunlight on water surface",
    },
]


def fetch_seasonal_rows(sheets_service, target_month: str, count: int = 3) -> list:
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range="マスタ!A2:G").execute()
        rows = result.get("values", [])
        if rows:
            matching = [r for r in rows if len(r) >= 7 and str(r[0]).strip() == target_month] or [r for r in rows if len(r) >= 7]
            random.shuffle(matching)
            extracted = []
            for c in matching[:count]:
                extracted.append({"month": c[0], "kigo_props": c[1], "location": c[2], "attire_note": c[3], "gesture": c[4], "lighting": c[5], "seed": c[6]})
            return extracted
    except Exception as e:
        print(f"⚠️ Sheets APIマスタ取得スキップ: {e}")
    shuffled = FALLBACK_SEEDS.copy()
    random.shuffle(shuffled)
    return shuffled[:count]


def build_editorial_prompt(row_data: dict) -> str:
    location = row_data.get("location", "a spacious school commuting avenue")
    kigo = row_data.get("kigo_props", "seasonal autumn leaves and scarves")
    lighting = row_data.get("lighting", "crisp, transparent natural daylight")
    gesture = row_data.get("gesture", "natural daily movement, walking and conversing calmly")
    attire = row_data.get("attire_note", "seasonal tailored uniforms")
    seed_en = row_data.get("seed", "")

    return f"""Modern Japanese commercial art book editorial illustration, masterfully maintaining the exact visual tone, fine ink line weight, character proportions, and muted transparent watercolor palette of a high-end publication. Use a wide architectural perspective, accurately framed in perspective with authentic three-dimensional depth and vanishing points.

Setting & Atmosphere ({row_data.get('month', CURRENT_MONTH)}月):
- Location & Architecture: {location}
- Seasonal elements & props: {kigo}
- Time & Lighting: {lighting}
- Cohesive Movement: {gesture}. {seed_en}

Three distinct students are drawn in a spacious environment with natural, realistic spacing and generous open foreground clearance:
- Girl 1 (Left): Short black bob cut, wearing a neat navy blazer with {attire}, calmly looking at a commuter pass or observing the surroundings; a navy duffel bag rests nearby.
- Girl 2 (Center): Loosely wavy chestnut brown ponytail, wearing an oversized beige cardigan over her uniform, standing or walking in a relaxed, natural contrapposto pose.
- Girl 3 (Right): Sporty layered dark hair, hands in blazer pockets, canvas tote bag over her shoulder, casually looking towards her friends.
Their placement and actions depict natural daily movements, ensuring a cohesive, serene daily scene.

Strict Invariants & Prohibitions:
- Prohibit 'moe' elements and anime expressions such as exaggerated open-mouthed smiles or blushing cheeks; use understated, calm, mature micro-expressions (natural expressions with closed mouths).
- The illustration itself must not contain text.
- Utilize delicate fineliner ink outlines for uniforms, matte gouache and transparent watercolors on cold-press paper with visible fine grain, and muted earth tones.
- The use of a small number of impactful colors is permitted for generating life-enriching elements like illuminations, fireworks, or soap bubbles.
- Absolutely no plastic-like CGI glossy objects, simple gradients, or moe tropes.""".strip()


def generate_image_with_retry(genai_client: genai.Client, prompt: str) -> bytes:
    for model_name in IMAGE_MODELS_TRY:
        for attempt in range(1, 3):
            try:
                print(f"画像生成を実行中 [モデル: {model_name}] (試行 {attempt}/2)...")
                if "imagen" in model_name.lower():
                    result = genai_client.models.generate_images(
                        model=model_name,
                        prompt=prompt,
                        config=types.GenerateImagesConfig(
                            number_of_images=1,
                            aspect_ratio="16:9",
                            output_mime_type="image/png",
                            person_generation="ALLOW_ADULT",
                        ),
                    )
                    if result.generated_images:
                        img_bytes = result.generated_images[0].image.image_bytes
                        print(f"画像生成成功 (Imagen 3)! [モデル: {model_name}] ({len(img_bytes)} bytes)")
                        return img_bytes
                else:
                    resp = genai_client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
                    )
                    if resp and resp.candidates and resp.candidates[0].content.parts:
                        for part in resp.candidates[0].content.parts:
                            if part.inline_data and part.inline_data.data:
                                print(f"画像生成成功 (generate_content)! [モデル: {model_name}] ({len(part.inline_data.data)} bytes)")
                                return part.inline_data.data
            except Exception as e:
                print(f"モデル {model_name} (試行 {attempt}) 失敗: {e}")
                time.sleep(2 * attempt)
    raise RuntimeError("すべての画像モデルでの生成が失敗しました。")


def add_center_signature(image_bytes: bytes, lines: list, palette: dict) -> bytes:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    font_paths = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "C:\\Windows\\Fonts\\meiryob.ttc",
    ]
    font_size = max(40, int(img.height * 0.095))
    font = None
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, font_size)
                break
            except Exception:
                continue
    if font is None:
        font = ImageFont.load_default()

    line_metrics = []
    total_text_h = 0
    line_spacing = int(font_size * 0.25)
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        line_metrics.append((line, w, h))
        total_text_h += h
    total_text_h += line_spacing * (len(lines) - 1)

    current_y = int((img.height - total_text_h) / 2)
    stroke_w = max(5, int(font_size * 0.1))
    shadow_offset = max(4, int(font_size * 0.08))

    for line, w, h in line_metrics:
        x = int((img.width - w) / 2)
        # ドロップシャドウ
        for dx in range(-shadow_offset, shadow_offset + 1):
            for dy in range(-shadow_offset, shadow_offset + 1):
                draw.text((x + dx + shadow_offset, current_y + dy + shadow_offset), line, font=font, fill=(10, 15, 25, 180))
        # 白い太い縁取り（袋文字）
        draw.text((x, current_y), line, font=font, fill=palette["glow"], stroke_width=stroke_w + 3, stroke_fill=(15, 20, 30, 255))
        # ネオンカラー
        draw.text((x, current_y), line, font=font, fill=palette["fill"], stroke_width=stroke_w, stroke_fill=(20, 25, 35, 255))
        current_y += h + line_spacing

    combined = Image.alpha_composite(img, overlay).convert("RGB")
    out_buffer = io.BytesIO()
    combined.save(out_buffer, format="JPEG", quality=95)
    return out_buffer.getvalue()


def upload_to_drive(drive_service, image_bytes: bytes, filename: str) -> str:
    gas_url = os.environ.get("GAS_UPLOAD_URL")
    gas_token = os.environ.get("GAS_UPLOAD_TOKEN", "")
    if gas_url:
        try:
            import base64, requests
            b64_str = base64.b64encode(image_bytes).decode("utf-8")
            payload = {"folderId": DRIVE_FOLDER_ID, "fileName": filename, "mimeType": "image/jpeg", "base64Content": b64_str, "token": gas_token}
            res = requests.post(gas_url, json=payload, timeout=90, allow_redirects=True)
            if res.status_code == 200 and res.json().get("status") == "success":
                file_id = res.json().get("fileId")
                return res.json().get("url") or f"https://drive.google.com/file/d/{file_id}/view"
        except Exception as gas_err:
            print(f"⚠️ GAS upload attempt failed: {gas_err}")

    media = MediaIoBaseUpload(io.BytesIO(image_bytes), mimetype="image/jpeg", resumable=True)
    uploaded = drive_service.files().create(body={"name": filename, "parents": [DRIVE_FOLDER_ID]}, media_body=media, fields="id, webViewLink", supportsAllDrives=True).execute()
    return uploaded.get("webViewLink", f"https://drive.google.com/file/d/{uploaded['id']}/view")


def main():
    print(f"=== 日常イラスト自動生成開始 (Imagen 3 最高精度モデル / {TODAY_STR} / 3本配信) ===")
    sheets_service, drive_service = get_google_services()
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        raise ValueError("環境変数 GEMINI_API_KEY が設定されていません。")
    genai_client = genai.Client(api_key=gemini_key)

    seasonal_rows = fetch_seasonal_rows(sheets_service, CURRENT_MONTH, count=3)
    while len(seasonal_rows) < 3:
        seasonal_rows.append(random.choice(FALLBACK_SEEDS))

    os.makedirs("output_images", exist_ok=True)
    for idx, theme in enumerate(DAILY_THEMES):
        row_data = seasonal_rows[idx]
        print(f"\n--- [{idx + 1}/3] {theme['tag_full']} ---")
        prompt = build_editorial_prompt(row_data)
        raw_image = generate_image_with_retry(genai_client, prompt)
        palette = random.choice(NEON_PALETTES)
        signed_image = add_center_signature(raw_image, theme["lines"], palette)

        filename = f"{theme['tag_full']}.jpeg"
        local_filepath = os.path.join("output_images", filename)
        with open(local_filepath, "wb") as f:
            f.write(signed_image)
        print(f"ローカル保存完了: {local_filepath} (ネオン: {palette['name']})")

        drive_url = ""
        try:
            drive_url = upload_to_drive(drive_service, signed_image, filename)
            print(f"Driveアップロード完了: {drive_url}")
        except Exception as drive_err:
            print(f"⚠️ Driveアップロード失敗（Artifactに保存済み）: {drive_err}")
            drive_url = f"GitHub Artifact: {filename}"

        try:
            timestamp = NOW_JST.strftime("%Y-%m-%d %H:%M:%S")
            sheets_service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range="生成ログ!A:H",
                valueInputOption="USER_ENTERED",
                body={"values": [[timestamp, row_data.get("month", CURRENT_MONTH), row_data.get("kigo_props", ""), row_data.get("location", ""), theme["tag_full"], prompt, drive_url, "SUCCESS"]]},
            ).execute()
        except Exception as log_err:
            print(f"⚠️ ログ追記スキップ: {log_err}")

    print("\n=== 3本すべての生成・保存工程が完了しました ===")


if __name__ == "__main__":
    main()
