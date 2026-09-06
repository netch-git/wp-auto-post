import os
import json
import requests
from datetime import datetime

# --- 環境設定 ---
WP_URL = os.environ.get("WP_URL", "").rstrip("/")
WP_USER = os.environ.get("WP_USER")
WP_PASS = os.environ.get("WP_PASS")

if not all([WP_URL, WP_USER, WP_PASS]):
    raise ValueError("必要な環境変数 (WP_URL, WP_USER, WP_PASS) が未設定です")

AUTH = (WP_USER, WP_PASS)

# 対象地域：広島県 竹原市
LOCATION_NAME = "広島県竹原市"
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
    
    # 日別データ集計
    all_temps, all_precip, all_wind, all_solar, all_rh = [], [], [], [], []
    max_t = -999.0
    min_t = 999.0
    max_rain = 0.0

    # 月別バケット: {year: {month: {'temp': [], 'precip': []}}}
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
        if solar_val is not None:
            all_solar.append(solar_val)
        if rh_val is not None:
            all_rh.append(rh_val)

    # 3年間全体指標
    avg_temp = round(sum(all_temps) / len(all_temps), 1) if all_temps else 0.0
    total_precip = round(sum(all_precip), 1)
    annual_precip = round(total_precip / len(years), 0)
    avg_solar = round(sum(all_solar) / len(all_solar), 2) if all_solar else 0.0
    avg_wind = round(sum(all_wind) / len(all_wind), 1) if all_wind else 0.0
    avg_rh = round(sum(all_rh) / len(all_rh), 1) if all_rh else 0.0
    annual_rainy_days = round(sum(s['rainy_days'] for s in yearly_stats.values()) / len(years))

    # 各年の月別配列生成
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

    return {
        "years": years,
        "elevation": elevation,
        "avg_temp": avg_temp,
        "max_temp": round(max_t, 1),
        "min_temp": round(min_t, 1),
        "annual_precip": int(annual_precip),
        "total_precip": total_precip,
        "max_rain": round(max_rain, 1),
        "avg_solar": avg_solar,
        "solar_kwh": round(avg_solar / 3.6, 2), # MJ/m2 -> kWh/m2
        "avg_wind": avg_wind,
        "avg_wind_kmh": round(avg_wind * 3.6, 1),
        "avg_rh": avg_rh,
        "annual_rainy_days": annual_rainy_days,
        "chart_temps": chart_temps,
        "chart_precips": chart_precips,
        "yearly_stats": yearly_stats
    }

def generate_dashboard_html(data):
    years = data["years"]
    years_str = ", ".join(map(str, years))
    y1, y2, y3 = years[0], years[1], years[2]

    # 年次差分計算
    avg_p = data["annual_precip"]
    diff_y1 = round(data["yearly_stats"][y1]["precip_total"] - avg_p, 1)
    diff_y2 = round(data["yearly_stats"][y2]["precip_total"] - avg_p, 1)
    diff_y3 = round(data["yearly_stats"][y3]["precip_total"] - avg_p, 1)

    chart_temps_json = json.dumps(data["chart_temps"])
    chart_precips_json = json.dumps(data["chart_precips"])

    html = f"""
    <!-- NASA POWER Climate Dashboard -->
    <div style="font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', Meiryo, sans-serif; background: #f8fafc; padding: 24px; border-radius: 16px; color: #1e293b; max-width: 1100px; margin: 0 auto; box-sizing: border-box;">
      
      <!-- ヘッダーメタ情報 -->
      <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px 20px; display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 24px;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="display: inline-block; width: 10px; height: 10px; background: #10b981; border-radius: 50%;"></span>
          <strong style="font-size: 1.15em; color: #0f172a;">{LOCATION_NAME}</strong>
          <span style="color: #64748b; font-size: 0.9em;">緯度: {LATITUDE}° / 経度: {LONGITUDE}° / 標高: {data['elevation']}m</span>
        </div>
        <span style="background: #eff6ff; color: #1d4ed8; font-size: 0.85em; font-weight: 600; padding: 6px 12px; border-radius: 9999px;">
          NASA POWER 観測期間: {years_str}年
        </span>
      </div>

      <!-- 5大メトリクスカード -->
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px;">
        
        <!-- 気温 -->
        <div style="background: #ffffff; border-radius: 14px; padding: 18px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 0.85em; color: #64748b; font-weight: 600;">3年間 平均気温</span>
            <span style="background: #fff7ed; color: #ea580c; border-radius: 8px; padding: 4px 6px; font-size: 0.9em;">🌡️</span>
          </div>
          <div style="font-size: 2em; font-weight: 800; color: #0f172a; margin-bottom: 12px;">+{data['avg_temp']}<span style="font-size: 0.5em; font-weight: 500;"> ℃</span></div>
          <div style="font-size: 0.78em; color: #64748b; display: flex; justify-content: space-between; border-top: 1px solid #f1f5f9; pt: 8px;">
            <span>最高: <strong style="color: #dc2626;">{data['max_temp']}℃</strong></span>
            <span>最低: <strong style="color: #2563eb;">{data['min_temp']}℃</strong></span>
          </div>
        </div>

        <!-- 降水量 -->
        <div style="background: #ffffff; border-radius: 14px; padding: 18px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 0.85em; color: #64748b; font-weight: 600;">年平均 降水量</span>
            <span style="background: #eff6ff; color: #2563eb; border-radius: 8px; padding: 4px 6px; font-size: 0.9em;">🌧️</span>
          </div>
          <div style="font-size: 2em; font-weight: 800; color: #0f172a; margin-bottom: 12px;">{data['annual_precip']}<span style="font-size: 0.5em; font-weight: 500;"> mm/年</span></div>
          <div style="font-size: 0.78em; color: #64748b; display: flex; justify-content: space-between; border-top: 1px solid #f1f5f9; pt: 8px;">
            <span>3年累計: {data['total_precip']}mm</span>
            <span>1日最大: <strong style="color: #2563eb;">{data['max_rain']}mm</strong></span>
          </div>
        </div>

        <!-- 全天日射量 -->
        <div style="background: #ffffff; border-radius: 14px; padding: 18px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 0.85em; color: #64748b; font-weight: 600;">全天日射量 (平均)</span>
            <span style="background: #fefce8; color: #ca8a04; border-radius: 8px; padding: 4px 6px; font-size: 0.9em;">☀️</span>
          </div>
          <div style="font-size: 2em; font-weight: 800; color: #0f172a; margin-bottom: 12px;">{data['avg_solar']}<span style="font-size: 0.45em; font-weight: 500;"> MJ/m²/日</span></div>
          <div style="font-size: 0.78em; color: #64748b; border-top: 1px solid #f1f5f9; pt: 8px;">
            発電換算: <strong>{data['solar_kwh']} kWh/m²</strong>
          </div>
        </div>

        <!-- 平均風速 -->
        <div style="background: #ffffff; border-radius: 14px; padding: 18px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 0.85em; color: #64748b; font-weight: 600;">地上2M 平均風速</span>
            <span style="background: #ecfdf5; color: #059669; border-radius: 8px; padding: 4px 6px; font-size: 0.9em;">💨</span>
          </div>
          <div style="font-size: 2em; font-weight: 800; color: #0f172a; margin-bottom: 12px;">{data['avg_wind']}<span style="font-size: 0.5em; font-weight: 500;"> m/s</span></div>
          <div style="font-size: 0.78em; color: #64748b; border-top: 1px solid #f1f5f9; pt: 8px;">
            時速換算: <strong>{data['avg_wind_kmh']} km/h</strong>
          </div>
        </div>

        <!-- 相対湿度 -->
        <div style="background: #ffffff; border-radius: 14px; padding: 18px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 0.85em; color: #64748b; font-weight: 600;">平均相対湿度</span>
            <span style="background: #faf5ff; color: #9333ea; border-radius: 8px; padding: 4px 6px; font-size: 0.9em;">💧</span>
          </div>
          <div style="font-size: 2em; font-weight: 800; color: #0f172a; margin-bottom: 12px;">{data['avg_rh']}<span style="font-size: 0.5em; font-weight: 500;"> %</span></div>
          <div style="font-size: 0.78em; color: #64748b; border-top: 1px solid #f1f5f9; pt: 8px;">
            年間降雨日数: <strong>約 {data['annual_rainy_days']} 日</strong>
          </div>
        </div>

      </div>

      <!-- グラフセクション (2カラム) -->
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 20px; margin-bottom: 20px;">
        
        <!-- 左: 月別 気象比較 (折れ線グラフ) -->
        <div style="background: #ffffff; border-radius: 14px; padding: 20px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
          <h3 style="margin: 0 0 4px 0; font-size: 1.1em; color: #0f172a;">3年間の月別 気象比較</h3>
          <p style="margin: 0 0 16px 0; font-size: 0.82em; color: #64748b;">各年（{years_str}年）の月平均気温推移</p>
          <div style="position: relative; height: 280px; width: 100%;">
            <canvas id="tempLineChart"></canvas>
          </div>
        </div>

        <!-- 右: 月別 降水量推移 (棒グラフ) -->
        <div style="background: #ffffff; border-radius: 14px; padding: 20px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
            <div>
              <h3 style="margin: 0 0 4px 0; font-size: 1.1em; color: #0f172a;">月別 降水量の年次推移</h3>
              <p style="margin: 0; font-size: 0.82em; color: #64748b;">雨季・乾季のパターンと降水量（単位: mm）</p>
            </div>
            <span style="background: #eff6ff; color: #2563eb; font-size: 0.8em; font-weight: 700; padding: 4px 10px; border-radius: 6px;">
              3年平均: {data['annual_precip']} mm
            </span>
          </div>
          <div style="position: relative; height: 200px; width: 100%; margin-bottom: 16px;">
            <canvas id="precipBarChart"></canvas>
          </div>

          <!-- 年別降水量サマリーカード -->
          <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
            <div style="background: #fffbeb; border: 1px solid #fef3c7; border-radius: 10px; padding: 10px; text-align: center;">
              <div style="font-size: 0.75em; color: #b45309; font-weight: bold;">YEAR {y1}</div>
              <div style="font-size: 1.15em; font-weight: 800; color: #78350f;">{data['yearly_stats'][y1]['precip_total']} <span style="font-size: 0.7em;">mm</span></div>
              <div style="font-size: 0.7em; color: #92400e;">雨天: {data['yearly_stats'][y1]['rainy_days']}日 ({'+' if diff_y1 >= 0 else ''}{diff_y1})</div>
            </div>
            <div style="background: #eff6ff; border: 1px solid #dbeafe; border-radius: 10px; padding: 10px; text-align: center;">
              <div style="font-size: 0.75em; color: #1d4ed8; font-weight: bold;">YEAR {y2}</div>
              <div style="font-size: 1.15em; font-weight: 800; color: #1e40af;">{data['yearly_stats'][y2]['precip_total']} <span style="font-size: 0.7em;">mm</span></div>
              <div style="font-size: 0.7em; color: #1e3a8a;">雨天: {data['yearly_stats'][y2]['rainy_days']}日 ({'+' if diff_y2 >= 0 else ''}{diff_y2})</div>
            </div>
            <div style="background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 10px; padding: 10px; text-align: center;">
              <div style="font-size: 0.75em; color: #047857; font-weight: bold;">YEAR {y3}</div>
              <div style="font-size: 1.15em; font-weight: 800; color: #065f46;">{data['yearly_stats'][y3]['precip_total']} <span style="font-size: 0.7em;">mm</span></div>
              <div style="font-size: 0.7em; color: #064e3b;">雨天: {data['yearly_stats'][y3]['rainy_days']}日 ({'+' if diff_y3 >= 0 else ''}{diff_y3})</div>
            </div>
          </div>

        </div>

      </div>

      <div style="text-align: right; font-size: 0.75em; color: #94a3b8;">
        データソース: NASA POWER (MERRA-2 & GEOS-FP) / 自動更新
      </div>

    </div>

    <!-- Chart.js 描画スクリプト -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
      (function() {{
        function initCharts() {{
          if (typeof Chart === 'undefined') {{
            setTimeout(initCharts, 100);
            return;
          }}

          const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
          const temps = {chart_temps_json};
          const precips = {chart_precips_json};

          // 折れ線グラフ（気温）
          const ctxLine = document.getElementById('tempLineChart').getContext('2d');
          new Chart(ctxLine, {{
            type: 'line',
            data: {{
              labels: months,
              datasets: [
                {{
                  label: '{y1}年',
                  data: temps[{y1}],
                  borderColor: '#f97316',
                  backgroundColor: '#f97316',
                  tension: 0.35,
                  pointRadius: 3
                }},
                {{
                  label: '{y2}年',
                  data: temps[{y2}],
                  borderColor: '#2563eb',
                  backgroundColor: '#2563eb',
                  tension: 0.35,
                  pointRadius: 3
                }},
                {{
                  label: '{y3}年',
                  data: temps[{y3}],
                  borderColor: '#10b981',
                  backgroundColor: '#10b981',
                  tension: 0.35,
                  pointRadius: 3
                }}
              ]
            }},
            options: {{
              responsive: true,
              maintainAspectRatio: false,
              scales: {{
                y: {{
                  ticks: {{ callback: (v) => v + '°' }}
                }}
              }}
            }}
          }});

          // 棒グラフ（降水量）
          const ctxBar = document.getElementById('precipBarChart').getContext('2d');
          new Chart(ctxBar, {{
            type: 'bar',
            data: {{
              labels: months,
              datasets: [
                {{ label: '{y1}年', data: precips[{y1}], backgroundColor: '#f97316' }},
                {{ label: '{y2}年', data: precips[{y2}], backgroundColor: '#2563eb' }},
                {{ label: '{y3}年', data: precips[{y3}], backgroundColor: '#10b981' }}
              ]
            }},
            options: {{
              responsive: true,
              maintainAspectRatio: false,
              scales: {{
                y: {{
                  ticks: {{ callback: (v) => v + 'mm' }}
                }}
              }}
            }}
          }});
        }}
        initCharts();
      }})();
    </script>
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
