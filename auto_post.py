import os
import requests
from datetime import datetime

# --- 環境設定 ---
WP_URL = os.environ.get("WP_URL", "").rstrip("/")
WP_USER = os.environ.get("WP_USER")
WP_PASS = os.environ.get("WP_PASS")

if not all([WP_URL, WP_USER, WP_PASS]):
    raise ValueError("必要な環境変数 (WP_URL, WP_USER, WP_PASS) が未設定です")

AUTH = (WP_USER, WP_PASS)

# 対象地点：広島県 竹原市
LOCATION_NAME = "竹原市, 広島県, 日本"
LATITUDE = 34.3428
LONGITUDE = 132.9092

def fetch_weather_dashboard_data(lat, lon, start_year, end_year):
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
    elevation = data.get("geometry", {}).get("coordinates", [lon, lat, 0])[2]

    t2m = params_data.get("T2M", {})
    t2m_max = params_data.get("T2M_MAX", {})
    t2m_min = params_data.get("T2M_MIN", {})
    precip = params_data.get("PRECTOTCORR", {})
    ws2m = params_data.get("WS2M", {})
    rh2m = params_data.get("RH2M", {})
    solar = params_data.get("ALLSKY_SFC_SW_DWN", {})

    def clean(v):
        return None if v is None or v in (-999, -9999) else float(v)

    years = list(range(start_year, end_year + 1))
    
    all_temps, all_precip, all_wind, all_solar, all_rh = [], [], [], [], []
    max_t, min_t, max_rain, max_wind = -999.0, 999.0, 0.0, 0.0

    monthly_data = {y: {m: {'temps': [], 'precip': 0.0} for m in range(1, 13)} for y in years}
    yearly_stats = {y: {'precip_total': 0.0, 'rainy_days': 0} for y in years}

    for d_str, v in t2m.items():
        year = int(d_str[:4])
        month = int(d_str[4:6])
        if year not in monthly_data:
            continue

        temp_val = clean(v)
        tmax_val = clean(t2m_max.get(d_str))
        tmin_val = clean(t2m_min.get(d_str))
        rain_val = clean(precip.get(d_str)) or 0.0
        wind_val = clean(ws2m.get(d_str))
        solar_val = clean(solar.get(d_str))
        rh_val = clean(rh2m.get(d_str))

        if temp_val is not None:
            all_temps.append(temp_val)
            monthly_data[year][month]['temps'].append(temp_val)
        if tmax_val is not None and tmax_val > max_t:
            max_t = tmax_val
        if tmin_val is not None and tmin_val < min_t:
            min_t = tmin_val
        if rain_val is not None:
            all_precip.append(rain_val)
            monthly_data[year][month]['precip'] += rain_val
            yearly_stats[year]['precip_total'] += rain_val
            if rain_val >= 1.0:
                yearly_stats[year]['rainy_days'] += 1
            if rain_val > max_rain:
                max_rain = rain_val
        if wind_val is not None:
            all_wind.append(wind_val)
            if wind_val > max_wind:
                max_wind = wind_val
        if solar_val is not None:
            all_solar.append(solar_val)
        if rh_val is not None:
            all_rh.append(rh_val)

    avg_temp = round(sum(all_temps) / len(all_temps), 1) if all_temps else 0.0
    total_precip = round(sum(all_precip), 1)
    annual_precip = round(total_precip / len(years), 1)
    avg_solar = round(sum(all_solar) / len(all_solar), 2) if all_solar else 0.0
    avg_wind = round(sum(all_wind) / len(all_wind), 1) if all_wind else 0.0
    avg_rh = round(sum(all_rh) / len(all_rh), 1) if all_rh else 0.0
    annual_rainy_days = round(sum(s['rainy_days'] for s in yearly_stats.values()) / len(years))

    chart_temps = {}
    chart_precips = {}
    for y in years:
        chart_temps[y] = [
            round(sum(monthly_data[y][m]['temps']) / len(monthly_data[y][m]['temps']), 1)
            if monthly_data[y][m]['temps'] else 0.0
            for m in range(1, 13)
        ]
        chart_precips[y] = [
            round(monthly_data[y][m]['precip'], 1)
            for m in range(1, 13)
        ]
        yearly_stats[y]['precip_total'] = round(yearly_stats[y]['precip_total'], 1)

    return {
        "years": years,
        "elevation": elevation,
        "avg_temp": avg_temp,
        "max_temp": round(max_t, 2),
        "min_temp": round(min_t, 2),
        "annual_precip": annual_precip,
        "total_precip": total_precip,
        "max_rain": round(max_rain, 2),
        "avg_solar": avg_solar,
        "solar_kwh": round(avg_solar / 3.6, 2),
        "avg_wind": avg_wind,
        "avg_wind_kmh": round(avg_wind * 3.6, 1),
        "max_wind": round(max_wind, 2),
        "avg_rh": avg_rh,
        "annual_rainy_days": annual_rainy_days,
        "chart_temps": chart_temps,
        "chart_precips": chart_precips,
        "yearly_stats": yearly_stats
    }

def generate_svg_line_chart(years, chart_temps):
    # 幅 500, 高さ 280, X余白 35〜475, Y余白 25〜235 (気温 0℃〜35℃)
    colors = ['#f97316', '#2563eb', '#10b981']
    y_min, y_max = 0, 35
    w, h = 500, 270
    pad_l, pad_r, pad_t, pad_b = 35, 20, 20, 35
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b

    svg = [f'<svg viewBox="0 0 {w} {h}" style="width: 100%; height: auto; display: block;" xmlns="http://www.w3.org/2000/svg">']
    
    # 背景グリッド線 & Y軸ラベル
    for temp in [0, 7, 14, 21, 28, 35]:
        y_pos = pad_t + plot_h - ((temp - y_min) / (y_max - y_min) * plot_h)
        svg.append(f'<line x1="{pad_l}" y1="{y_pos}" x2="{w - pad_r}" y2="{y_pos}" stroke="#f1f5f9" stroke-dasharray="3,3" stroke-width="1"/>')
        svg.append(f'<text x="{pad_l - 6}" y="{y_pos + 4}" font-size="10" fill="#94a3b8" text-anchor="end">{temp}°</text>')

    # X軸月ラベル
    months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
    x_coords = [pad_l + (i / 11) * plot_w for i in range(12)]
    for i, m in enumerate(months):
        svg.append(f'<text x="{x_coords[i]}" y="{h - 10}" font-size="10" fill="#94a3b8" text-anchor="middle">{m}</text>')

    # 各年の折れ線とプロット点
    for idx, y in enumerate(years):
        color = colors[idx]
        pts = []
        for i, t in enumerate(chart_temps[y]):
            clamped_t = max(y_min, min(y_max, t))
            y_pos = pad_t + plot_h - ((clamped_t - y_min) / (y_max - y_min) * plot_h)
            pts.append((x_coords[i], y_pos))

        # 折れ線
        d_str = " ".join([f"{'M' if i == 0 else 'L'} {p[0]:.1f},{p[1]:.1f}" for i, p in enumerate(pts)])
        svg.append(f'<path d="{d_str}" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>')
        
        # 点
        for p in pts:
            svg.append(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="3.5" fill="{color}" stroke="#ffffff" stroke-width="1.5"/>')

    svg.append('</svg>')
    return "".join(svg)

def generate_svg_bar_chart(years, chart_precips):
    # 幅 500, 高さ 230, Y軸 0〜360mm
    colors = ['#f97316', '#2563eb', '#10b981']
    y_max = 360
    w, h = 500, 230
    pad_l, pad_r, pad_t, pad_b = 40, 15, 15, 30
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b

    svg = [f'<svg viewBox="0 0 {w} {h}" style="width: 100%; height: auto; display: block;" xmlns="http://www.w3.org/2000/svg">']

    # グリッド線 & Y軸ラベル
    for rain in [0, 90, 180, 270, 360]:
        y_pos = pad_t + plot_h - (rain / y_max * plot_h)
        svg.append(f'<line x1="{pad_l}" y1="{y_pos}" x2="{w - pad_r}" y2="{y_pos}" stroke="#f1f5f9" stroke-width="1"/>')
        svg.append(f'<text x="{pad_l - 6}" y="{y_pos + 3}" font-size="9" fill="#94a3b8" text-anchor="end">{rain}mm</text>')

    months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
    month_w = plot_w / 12
    bar_w = 7.5

    for m_idx in range(12):
        m_center = pad_l + (m_idx + 0.5) * month_w
        svg.append(f'<text x="{m_center}" y="{h - 10}" font-size="10" fill="#94a3b8" text-anchor="middle">{months[m_idx]}</text>')

        # 3年分の棒グラフ
        for y_idx, y in enumerate(years):
            val = min(y_max, chart_precips[y][m_idx])
            bar_h = (val / y_max) * plot_h
            bx = m_center - (1.5 * bar_w) + (y_idx * bar_w)
            by = pad_t + plot_h - bar_h
            svg.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w - 1.5}" height="{bar_h:.1f}" fill="{colors[y_idx]}" rx="1.5"/>')

    svg.append('</svg>')
    return "".join(svg)

def generate_dashboard_html(data):
    years = data["years"]
    y1, y2, y3 = years[0], years[1], years[2]
    years_str = f"{y1}, {y2}, {y3}"

    avg_p = data["annual_precip"]
    diff_y1 = round(data["yearly_stats"][y1]["precip_total"] - avg_p, 1)
    diff_y2 = round(data["yearly_stats"][y2]["precip_total"] - avg_p, 1)
    diff_y3 = round(data["yearly_stats"][y3]["precip_total"] - avg_p, 1)

    line_chart_svg = generate_svg_line_chart(years, data["chart_temps"])
    bar_chart_svg = generate_svg_bar_chart(years, data["chart_precips"])

    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #f0f6ff; padding: 24px; border-radius: 20px; color: #1e293b; max-width: 980px; margin: 0 auto; box-sizing: border-box;">
      
      <!-- タイトルヘッダー -->
      <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px;">
        <span style="font-size: 24px; background: #2563eb; color: #ffffff; border-radius: 10px; width: 36px; height: 36px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold;">☀</span>
        <div>
          <h2 style="margin: 0; font-size: 1.35em; font-weight: 800; color: #0f172a; display: flex; align-items: center; gap: 8px;">
            NASA POWER <span style="background: #dbeafe; color: #1e40af; font-size: 0.55em; padding: 3px 8px; border-radius: 999px; font-weight: 700;">3-YEAR METRICS</span>
          </h2>
          <p style="margin: 2px 0 0 0; font-size: 0.8em; color: #64748b;">Prediction Of Worldwide Energy Resources 気象データダッシュボード</p>
        </div>
      </div>

      <!-- 地点メタバー -->
      <div style="background: #ffffff; border-radius: 12px; padding: 14px 18px; margin-bottom: 20px; display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="width: 9px; height: 9px; background: #10b981; border-radius: 50%; display: inline-block;"></span>
          <strong style="font-size: 1.05em; color: #0f172a;">{LOCATION_NAME}</strong>
          <span style="color: #64748b; font-size: 0.85em;">| 緯度: {LATITUDE}° / 経度: {LONGITUDE}° | 標高: {data['elevation']}m</span>
        </div>
        <span style="background: #eff6ff; color: #1d4ed8; font-size: 0.82em; font-weight: 700; padding: 5px 12px; border-radius: 9999px;">
          NASA POWER 観測期間: {years_str}年
        </span>
      </div>

      <!-- 5大メトリクスカード（完全横並びレスポンシブ） -->
      <div style="display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 20px;">
        
        <!-- 気温 -->
        <div style="flex: 1 1 170px; background: #ffffff; border-radius: 16px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); box-sizing: border-box;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-size: 0.8em; color: #64748b; font-weight: bold;">3年間 平均気温</span>
            <span style="background: #fff7ed; color: #ea580c; border-radius: 8px; padding: 3px 6px; font-size: 0.85em;">🌡</span>
          </div>
          <div style="font-size: 1.85em; font-weight: 900; color: #0f172a; margin-bottom: 8px;">+{data['avg_temp']}<span style="font-size: 0.5em; font-weight: 600;"> ℃</span></div>
          <div style="font-size: 0.72em; color: #64748b; display: flex; justify-content: space-between; border-top: 1px solid #f8fafc; padding-top: 6px;">
            <span>↗ 最高 <strong style="color: #0f172a;">{data['max_temp']}℃</strong></span>
            <span>↘ 最低 <strong style="color: #0f172a;">{data['min_temp']}℃</strong></span>
          </div>
        </div>

        <!-- 降水量 -->
        <div style="flex: 1 1 170px; background: #ffffff; border-radius: 16px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); box-sizing: border-box;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-size: 0.8em; color: #64748b; font-weight: bold;">年平均 降水量</span>
            <span style="background: #eff6ff; color: #2563eb; border-radius: 8px; padding: 3px 6px; font-size: 0.85em;">🌧</span>
          </div>
          <div style="font-size: 1.85em; font-weight: 900; color: #0f172a; margin-bottom: 8px;">{int(data['annual_precip'])}<span style="font-size: 0.5em; font-weight: 600;"> mm/年</span></div>
          <div style="font-size: 0.72em; color: #64748b; display: flex; justify-content: space-between; border-top: 1px solid #f8fafc; padding-top: 6px;">
            <span>3年累計 <strong style="color: #0f172a;">{data['total_precip']} mm</strong></span>
            <span>1日最大 <strong style="color: #2563eb;">{data['max_rain']} mm</strong></span>
          </div>
        </div>

        <!-- 全天日射量 -->
        <div style="flex: 1 1 170px; background: #ffffff; border-radius: 16px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); box-sizing: border-box;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-size: 0.8em; color: #64748b; font-weight: bold;">全天日射量 (平均)</span>
            <span style="background: #fefce8; color: #ca8a04; border-radius: 8px; padding: 3px 6px; font-size: 0.85em;">☀</span>
          </div>
          <div style="font-size: 1.85em; font-weight: 900; color: #0f172a; margin-bottom: 8px;">{data['avg_solar']}<span style="font-size: 0.45em; font-weight: 600;"> MJ/m²/日</span></div>
          <div style="font-size: 0.72em; color: #64748b; display: flex; justify-content: space-between; border-top: 1px solid #f8fafc; padding-top: 6px;">
            <span>発電換算: <strong>{data['solar_kwh']} kWh/m²</strong></span>
            <span style="color: #10b981; font-weight: bold;">平年並み</span>
          </div>
        </div>

        <!-- 平均風速 -->
        <div style="flex: 1 1 170px; background: #ffffff; border-radius: 16px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); box-sizing: border-box;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-size: 0.8em; color: #64748b; font-weight: bold;">地上2M 平均風速</span>
            <span style="background: #ecfdf5; color: #059669; border-radius: 8px; padding: 3px 6px; font-size: 0.85em;">💨</span>
          </div>
          <div style="font-size: 1.85em; font-weight: 900; color: #0f172a; margin-bottom: 8px;">{data['avg_wind']}<span style="font-size: 0.5em; font-weight: 600;"> m/s</span></div>
          <div style="font-size: 0.72em; color: #64748b; display: flex; justify-content: space-between; border-top: 1px solid #f8fafc; padding-top: 6px;">
            <span>時速換算: <strong>{data['avg_wind_kmh']} km/h</strong></span>
            <span>最大日平均: <strong>{data['max_wind']} m/s</strong></span>
          </div>
        </div>

        <!-- 相対湿度 -->
        <div style="flex: 1 1 170px; background: #ffffff; border-radius: 16px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); box-sizing: border-box;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-size: 0.8em; color: #64748b; font-weight: bold;">平均相対湿度</span>
            <span style="background: #faf5ff; color: #9333ea; border-radius: 8px; padding: 3px 6px; font-size: 0.85em;">💧</span>
          </div>
          <div style="font-size: 1.85em; font-weight: 900; color: #0f172a; margin-bottom: 8px;">{data['avg_rh']}<span style="font-size: 0.5em; font-weight: 600;"> %</span></div>
          <div style="font-size: 0.72em; color: #64748b; display: flex; justify-content: space-between; border-top: 1px solid #f8fafc; padding-top: 6px;">
            <span>年間雨天日数: <strong style="color: #2563eb;">約 {data['annual_rainy_days']} 日</strong></span>
            <span style="color: #6366f1; font-weight: bold;">湿潤</span>
          </div>
        </div>

      </div>

      <!-- グラフ2カラムエリア -->
      <div style="display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 16px;">
        
        <!-- 左: 気温折れ線グラフ -->
        <div style="flex: 1 1 440px; background: #ffffff; border-radius: 18px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); box-sizing: border-box;">
          <div style="margin-bottom: 14px;">
            <h3 style="margin: 0; font-size: 1.05em; color: #0f172a; font-weight: 800;">3年間の月別 気象比較</h3>
            <p style="margin: 3px 0 0 0; font-size: 0.78em; color: #64748b;">各年（{years_str}年）の月平均気温推移（単位: ℃）</p>
          </div>
          
          <!-- SVGグラフ -->
          <div style="width: 100%;">
            {line_chart_svg}
          </div>

          <!-- 凡例 -->
          <div style="display: flex; justify-content: center; gap: 16px; margin-top: 10px; font-size: 0.78em; font-weight: bold;">
            <span style="color: #f97316;">● {y1}年</span>
            <span style="color: #2563eb;">● {y2}年</span>
            <span style="color: #10b981;">● {y3}年</span>
          </div>
        </div>

        <!-- 右: 降水量棒グラフ + 年別カード -->
        <div style="flex: 1 1 440px; background: #ffffff; border-radius: 18px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); box-sizing: border-box;">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px;">
            <div>
              <h3 style="margin: 0; font-size: 1.05em; color: #0f172a; font-weight: 800;">月別 降水量の年次推移</h3>
              <p style="margin: 3px 0 0 0; font-size: 0.78em; color: #64748b;">雨季・乾季のパターンと年間降水量の違い（単位: mm）</p>
            </div>
            <span style="background: #eff6ff; color: #2563eb; font-size: 0.75em; font-weight: 700; padding: 4px 10px; border-radius: 6px; white-space: nowrap;">
              3年間年平均: {data['annual_precip']} mm
            </span>
          </div>

          <!-- SVG棒グラフ -->
          <div style="width: 100%; margin-bottom: 16px;">
            {bar_chart_svg}
          </div>

          <!-- 凡例 -->
          <div style="display: flex; justify-content: center; gap: 16px; margin-bottom: 16px; font-size: 0.78em; font-weight: bold;">
            <span style="color: #f97316;">■ {y1}年</span>
            <span style="color: #2563eb;">■ {y2}年</span>
            <span style="color: #10b981;">■ {y3}年</span>
          </div>

          <!-- 3年分サマリーカード（四捨五入済） -->
          <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;">
            <div style="background: #fffbeb; border: 1px solid #fef3c7; border-radius: 10px; padding: 10px 6px; text-align: center;">
              <div style="font-size: 0.72em; color: #b45309; font-weight: bold;">YEAR {y1}</div>
              <div style="font-size: 1.15em; font-weight: 900; color: #78350f; margin: 3px 0;">{data['yearly_stats'][y1]['precip_total']:.1f} <span style="font-size: 0.65em;">mm</span></div>
              <div style="font-size: 0.68em; color: #92400e;">雨天: {data['yearly_stats'][y1]['rainy_days']}日 ({'+' if diff_y1 >= 0 else ''}{diff_y1:.1f})</div>
            </div>
            <div style="background: #eff6ff; border: 1px solid #dbeafe; border-radius: 10px; padding: 10px 6px; text-align: center;">
              <div style="font-size: 0.72em; color: #1d4ed8; font-weight: bold;">YEAR {y2}</div>
              <div style="font-size: 1.15em; font-weight: 900; color: #1e40af; margin: 3px 0;">{data['yearly_stats'][y2]['precip_total']:.1f} <span style="font-size: 0.65em;">mm</span></div>
              <div style="font-size: 0.68em; color: #1e3a8a;">雨天: {data['yearly_stats'][y2]['rainy_days']}日 ({'+' if diff_y2 >= 0 else ''}{diff_y2:.1f})</div>
            </div>
            <div style="background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 10px; padding: 10px 6px; text-align: center;">
              <div style="font-size: 0.72em; color: #047857; font-weight: bold;">YEAR {y3}</div>
              <div style="font-size: 1.15em; font-weight: 900; color: #065f46; margin: 3px 0;">{data['yearly_stats'][y3]['precip_total']:.1f} <span style="font-size: 0.65em;">mm</span></div>
              <div style="font-size: 0.68em; color: #064e3b;">雨天: {data['yearly_stats'][y3]['rainy_days']}日 ({'+' if diff_y3 >= 0 else ''}{diff_y3:.1f})</div>
            </div>
          </div>

        </div>

      </div>

      <!-- フッタークレジット -->
      <div style="text-align: right; font-size: 0.72em; color: #94a3b8; padding-right: 4px;">
        データソース: NASA POWER (MERRA-2 &amp; GEOS-FP) / 毎日自動更新
      </div>

    </div>
    """
    return html

def main():
    current_year = datetime.now().year
    start_year = current_year - 3
    end_year = current_year - 1

    print(f"NASA POWERから {LOCATION_NAME} の気象データを取得中 ({start_year}〜{end_year})...")
    data = fetch_weather_dashboard_data(LATITUDE, LONGITUDE, start_year, end_year)

    today_str = datetime.now().strftime("%Y-%m-%d")
    title = f"【気象ダッシュボード】{LOCATION_NAME} ({today_str} 更新)"
    content_html = generate_dashboard_html(data)

    endpoint = f"{WP_URL}/wp-json/wp/v2/posts"
    payload = {
        "title": title,
        "content": content_html,
        "status": "publish"
    }

    print("WordPressへ投稿中...")
    res = requests.post(endpoint, json=payload, auth=AUTH, timeout=20)
    if res.status_code not in (200, 201):
        raise RuntimeError(f"WordPress投稿失敗 ({res.status_code}): {res.text}")

    print("投稿成功:", res.json().get("link"))

if __name__ == "__main__":
    main()
