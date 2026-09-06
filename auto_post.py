import os
import requests
from datetime import datetime

# --- 環境変数の取得 ---
WP_URL = os.environ.get("WP_URL", "").rstrip("/")
WP_USER = os.environ.get("WP_USER")
WP_PASS = os.environ.get("WP_PASS")

if not all([WP_URL, WP_USER, WP_PASS]):
    raise ValueError("必要な環境変数 (WP_URL, WP_USER, WP_PASS) が未設定です")

AUTH = (WP_USER, WP_PASS)

# 対象地域の設定（例: 東京）
LOCATION_NAME = "東京都, 日本"
LATITUDE = 35.6762
LONGITUDE = 139.6503

def fetch_weather_data(lat, lon, start_year, end_year):
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters": "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,WS2M,RH2M,ALLSKY_SFC_SW_DWN",
        "community": "RE",
        "longitude": lon,
        "latitude": lat,
        "start": f"{start_year}0101",
        "end": f"{end_year}1231",
        "format": "JSON"
    }
    
    res = requests.get(url, params=params, timeout=30)
    res.raise_for_status()
    data = res.json()
    params_data = data.get("properties", {}).get("parameter", {})

    t2m = params_data.get("T2M", {})
    t2m_max = params_data.get("T2M_MAX", {})
    t2m_min = params_data.get("T2M_MIN", {})
    precip = params_data.get("PRECTOTCORR", {})
    ws2m = params_data.get("WS2M", {})
    rh2m = params_data.get("RH2M", {})
    solar = params_data.get("ALLSKY_SFC_SW_DWN", {})

    valid_temps = [v for v in t2m.values() if v not in (-999, -9999, None)]
    valid_precip = [v for v in precip.values() if v not in (-999, -9999, None)]
    valid_wind = [v for v in ws2m.values() if v not in (-999, -9999, None)]
    valid_solar = [v for v in solar.values() if v not in (-999, -9999, None)]
    valid_rh = [v for v in rh2m.values() if v not in (-999, -9999, None)]

    # 最高・最低気温とその日付
    max_temp_date = max((d for d, v in t2m_max.items() if v not in (-999, None)), key=lambda d: t2m_max[d], default="")
    min_temp_date = min((d for d, v in t2m_min.items() if v not in (-999, None)), key=lambda d: t2m_min[d], default="")
    max_rain_date = max((d for d, v in precip.items() if v not in (-999, None)), key=lambda d: precip[d], default="")

    years_count = max(1, end_year - start_year + 1)

    return {
        "start_year": start_year,
        "end_year": end_year,
        "avg_temp": round(sum(valid_temps) / len(valid_temps), 1) if valid_temps else 0,
        "max_temp": t2m_max.get(max_temp_date, 0),
        "max_temp_date": f"{max_temp_date[:4]}-{max_temp_date[4:6]}-{max_temp_date[6:]}" if max_temp_date else "",
        "min_temp": t2m_min.get(min_temp_date, 0),
        "min_temp_date": f"{min_temp_date[:4]}-{min_temp_date[4:6]}-{min_temp_date[6:]}" if min_temp_date else "",
        "annual_precip": round(sum(valid_precip) / years_count, 1) if valid_precip else 0,
        "max_rain": precip.get(max_rain_date, 0),
        "max_rain_date": f"{max_rain_date[:4]}-{max_rain_date[4:6]}-{max_rain_date[6:]}" if max_rain_date else "",
        "avg_wind": round(sum(valid_wind) / len(valid_wind), 1) if valid_wind else 0,
        "avg_solar": round(sum(valid_solar) / len(valid_solar), 2) if valid_solar else 0,
        "avg_rh": round(sum(valid_rh) / len(valid_rh), 1) if valid_rh else 0,
    }

def main():
    current_year = datetime.now().year
    start_year = current_year - 3
    end_year = current_year - 1

    print("NASA POWERから気象データを取得中...")
    stats = fetch_weather_data(LATITUDE, LONGITUDE, start_year, end_year)

    today_str = datetime.now().strftime("%Y-%m-%d")
    title = f"【気象データ】{LOCATION_NAME} ({today_str} 更新)"

    content = f"""
    <h2>気象統計サマリー ({stats['start_year']}年〜{stats['end_year']}年)</h2>
    <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd; text-align: left;">
      <tbody>
        <tr><th style="border: 1px solid #ddd; padding: 8px;">対象地域</th><td style="border: 1px solid #ddd; padding: 8px;">{LOCATION_NAME}</td></tr>
        <tr><th style="border: 1px solid #ddd; padding: 8px;">平均気温</th><td style="border: 1px solid #ddd; padding: 8px;">{stats['avg_temp']} ℃</td></tr>
        <tr><th style="border: 1px solid #ddd; padding: 8px;">最高気温</th><td style="border: 1px solid #ddd; padding: 8px;">{stats['max_temp']} ℃ ({stats['max_temp_date']})</td></tr>
        <tr><th style="border: 1px solid #ddd; padding: 8px;">最低気温</th><td style="border: 1px solid #ddd; padding: 8px;">{stats['min_temp']} ℃ ({stats['min_temp_date']})</td></tr>
        <tr><th style="border: 1px solid #ddd; padding: 8px;">年間平均降水量</th><td style="border: 1px solid #ddd; padding: 8px;">{stats['annual_precip']} mm</td></tr>
        <tr><th style="border: 1px solid #ddd; padding: 8px;">1日最大降水量</th><td style="border: 1px solid #ddd; padding: 8px;">{stats['max_rain']} mm ({stats['max_rain_date']})</td></tr>
        <tr><th style="border: 1px solid #ddd; padding: 8px;">平均風速</th><td style="border: 1px solid #ddd; padding: 8px;">{stats['avg_wind']} m/s</td></tr>
        <tr><th style="border: 1px solid #ddd; padding: 8px;">平均日射量</th><td style="border: 1px solid #ddd; padding: 8px;">{stats['avg_solar']} MJ/m²/日</td></tr>
        <tr><th style="border: 1px solid #ddd; padding: 8px;">平均湿度</th><td style="border: 1px solid #ddd; padding: 8px;">{stats['avg_rh']} %</td></tr>
      </tbody>
    </table>
    <p style="font-size: 0.8em; color: #777; margin-top: 10px;">データソース: NASA POWER</p>
    """

    endpoint = f"{WP_URL}/wp-json/wp/v2/posts"
    payload = {
        "title": title,
        "content": content,
        "status": "publish"
    }

    print("WordPressへ投稿中...")
    res = requests.post(endpoint, json=payload, auth=AUTH, timeout=20)
    if res.status_code not in (200, 201):
        raise RuntimeError(f"WordPress投稿失敗 ({res.status_code}): {res.text}")

    print("投稿成功:", res.json().get("link"))

if __name__ == "__main__":
    main()
