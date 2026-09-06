import os
import html
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

# 対象地域：広島県竹原市
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
    
    all_temps, all_precip, all_wind, all_solar, all_rh = [], [], [], [], []
    max_t, min_t, max_rain, max_wind = -999.0, 999.0, 0.0, 0.0

    monthly_data = {
        y: {m: {'temps': [], 'tmax': [], 'tmin': [], 'precip': 0.0, 'solar': [], 'wind': []} for m in range(1, 13)}
        for y in years
    }
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
        if tmax_val is not None:
            monthly_data[year][month]['tmax'].append(tmax_val)
            if tmax_val > max_t: max_t = tmax_val
        if tmin_val is not None:
            monthly_data[year][month]['tmin'].append(tmin_val)
            if tmin_val < min_t: min_t = tmin_val
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
            monthly_data[year][month]['wind'].append(wind_val)
            if wind_val > max_wind: max_wind = wind_val
        if solar_val is not None:
            all_solar.append(solar_val)
            monthly_data[year][month]['solar'].append(solar_val)
        if rh_val is not None:
            all_rh.append(rh_val)

    avg_temp = round(sum(all_temps) / len(all_temps), 1) if all_temps else 0.0
    total_precip = round(sum(all_precip), 1)
    annual_precip = round(total_precip / len(years), 1)
    avg_solar = round(sum(all_solar) / len(all_solar), 2) if all_solar else 0.0
    avg_wind = round(sum(all_wind) / len(all_wind), 1) if all_wind else 0.0
    avg_rh = round(sum(all_rh) / len(all_rh), 1) if all_rh else 0.0
    annual_rainy_days = round(sum(s['rainy_days'] for s in yearly_stats.values()) / len(years))

    chart_datasets = {
        'temp_avg': {},
        'temp_max': {},
        'temp_min': {},
        'precip': {},
        'solar': {},
        'wind': {}
    }

    for y in years:
        chart_datasets['temp_avg'][y] = [round(sum(monthly_data[y][m]['temps']) / len(monthly_data[y][m]['temps']), 1) if monthly_data[y][m]['temps'] else 0.0 for m in range(1, 13)]
        chart_datasets['temp_max'][y] = [round(max(monthly_data[y][m]['tmax']), 1) if monthly_data[y][m]['tmax'] else 0.0 for m in range(1, 13)]
        chart_datasets['temp_min'][y] = [round(min(monthly_data[y][m]['tmin']), 1) if monthly_data[y][m]['tmin'] else 0.0 for m in range(1, 13)]
        chart_datasets['precip'][y] = [round(monthly_data[y][m]['precip'], 1) for m in range(1, 13)]
        chart_datasets['solar'][y] = [round(sum(monthly_data[y][m]['solar']) / len(monthly_data[y][m]['solar']), 2) if monthly_data[y][m]['solar'] else 0.0 for m in range(1, 13)]
        chart_datasets['wind'][y] = [round(sum(monthly_data[y][m]['wind']) / len(monthly_data[y][m]['wind']), 1) if monthly_data[y][m]['wind'] else 0.0 for m in range(1, 13)]
        yearly_stats[y]['precip_total'] = round(yearly_stats[y]['precip_total'], 1)

    return {
        "years": years,
        "elevation": elevation,
        "avg_temp": avg_temp,
        "max_temp": round(max_t, 1),
        "min_temp": round(min_t, 1),
        "annual_precip": annual_precip,
        "total_precip": total_precip,
        "max_rain": round(max_rain, 1),
        "avg_solar": avg_solar,
        "solar_kwh": round(avg_solar / 3.6, 2),
        "avg_wind": avg_wind,
        "avg_wind_kmh": round(avg_wind * 3.6, 1),
        "max_wind": round(max_wind, 1),
        "avg_rh": avg_rh,
        "annual_rainy_days": annual_rainy_days,
        "chart_datasets": chart_datasets,
        "yearly_stats": yearly_stats
    }

def build_interactive_dashboard_html(data):
    years = data["years"]
    y1, y2, y3 = years[0], years[1], years[2]
    years_str = f"{y1}〜{y3}年"

    avg_p = data["annual_precip"]
    diff_y1 = round(data["yearly_stats"][y1]["precip_total"] - avg_p, 1)
    diff_y2 = round(data["yearly_stats"][y2]["precip_total"] - avg_p, 1)
    diff_y3 = round(data["yearly_stats"][y3]["precip_total"] - avg_p, 1)

    chart_data_json = json.dumps(data["chart_datasets"])

    raw_inner_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {{
      --bg-main: #f1f5f9;
      --card-bg: #ffffff;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --primary: #2563eb;
      --border-color: #e2e8f0;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg-main);
      color: var(--text-main);
      padding: 16px;
    }}
    .dashboard-container {{
      max-width: 1040px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}
    .header-bar {{
      background: #ffffff;
      padding: 14px 20px;
      border-radius: 14px;
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      border: 1px solid var(--border-color);
      box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }}
    .header-left {{ display: flex; align-items: center; gap: 10px; }}
    .badge-dot {{ width: 10px; height: 10px; background: #10b981; border-radius: 50%; display: inline-block; }}
    .header-title {{ font-size: 1.15em; font-weight: 800; color: #0f172a; }}
    .header-sub {{ font-size: 0.85em; color: var(--text-muted); }}
    .header-badge {{
      background: #eff6ff;
      color: var(--primary);
      font-size: 0.8em;
      font-weight: 700;
      padding: 6px 12px;
      border-radius: 9999px;
    }}
    .metrics-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 12px;
    }}
    .metric-card {{
      background: #ffffff;
      border-radius: 14px;
      padding: 16px;
      border: 1px solid var(--border-color);
      box-shadow: 0 1px 3px rgba(0,0,0,0.03);
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .metric-card:hover {{
      transform: translateY(-2px);
      box-shadow: 0 6px 12px rgba(0,0,0,0.05);
    }}
    .metric-head {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }}
    .metric-title {{ font-size: 0.78em; color: var(--text-muted); font-weight: 700; }}
    .metric-icon {{
      width: 28px;
      height: 28px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 8px;
      font-size: 0.9em;
    }}
    .metric-value {{ font-size: 1.85em; font-weight: 900; color: #0f172a; margin-bottom: 8px; }}
    .metric-value span {{ font-size: 0.5em; font-weight: 600; color: var(--text-muted); }}
    .metric-foot {{
      font-size: 0.74em;
      color: var(--text-muted);
      border-top: 1px solid #f1f5f9;
      padding-top: 6px;
      display: flex;
      justify-content: space-between;
    }}
    .chart-panel {{
      background: #ffffff;
      border-radius: 16px;
      padding: 20px;
      border: 1px solid var(--border-color);
      box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }}
    .chart-header {{
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
    }}
    .chart-title-group h3 {{ font-size: 1.1em; font-weight: 800; color: #0f172a; }}
    .chart-title-group p {{ font-size: 0.8em; color: var(--text-muted); margin-top: 2px; }}
    .tab-group {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      background: #f1f5f9;
      padding: 4px;
      border-radius: 10px;
    }}
    .tab-btn {{
      border: none;
      background: transparent;
      padding: 6px 12px;
      font-size: 0.8em;
      font-weight: 700;
      color: #64748b;
      cursor: pointer;
      border-radius: 7px;
      transition: all 0.2s ease;
    }}
    .tab-btn.active {{
      background: #ffffff;
      color: var(--primary);
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }}
    .chart-wrapper {{
      position: relative;
      height: 310px;
      width: 100%;
    }}
    .precip-summary-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      margin-top: 16px;
    }}
    .summary-box {{
      padding: 12px;
      border-radius: 10px;
      text-align: center;
    }}
    .footer-note {{
      text-align: right;
      font-size: 0.75em;
      color: #94a3b8;
    }}
  </style>
</head>
<body>

<div class="dashboard-container">
  
  <div class="header-bar">
    <div class="header-left">
      <span class="badge-dot"></span>
      <div>
        <span class="header-title">{LOCATION_NAME}</span>
        <span class="header-sub">| 緯度 {LATITUDE}° / 経度 {LONGITUDE}° / 標高 {data['elevation']}m</span>
      </div>
    </div>
    <div class="header-badge">NASA POWER 観測期間: {years_str}</div>
  </div>

  <div class="metrics-grid">
    <div class="metric-card">
      <div class="metric-head">
        <span class="metric-title">3年間 平均気温</span>
        <span class="metric-icon" style="background: #fff7ed; color: #ea580c;">🌡️</span>
      </div>
      <div class="metric-value">+{data['avg_temp']}<span> ℃</span></div>
      <div class="metric-foot">
        <span>最高 <strong>{data['max_temp']}℃</strong></span>
        <span>最低 <strong>{data['min_temp']}℃</strong></span>
      </div>
    </div>

    <div class="metric-card">
      <div class="metric-head">
        <span class="metric-title">年平均 降水量</span>
        <span class="metric-icon" style="background: #eff6ff; color: #2563eb;">🌧️</span>
      </div>
      <div class="metric-value">{int(data['annual_precip'])}<span> mm/年</span></div>
      <div class="metric-foot">
        <span>3年累計 <strong>{data['total_precip']}mm</strong></span>
        <span>1日最大 <strong>{data['max_rain']}mm</strong></span>
      </div>
    </div>

    <div class="metric-card">
      <div class="metric-head">
        <span class="metric-title">全天日射量 (平均)</span>
        <span class="metric-icon" style="background: #fefce8; color: #ca8a04;">☀️</span>
      </div>
      <div class="metric-value">{data['avg_solar']}<span> MJ/m²</span></div>
      <div class="metric-foot">
        <span>発電換算: <strong>{data['solar_kwh']} kWh/m²</strong></span>
        <span style="color:#10b981; font-weight:bold;">平年並み</span>
      </div>
    </div>

    <div class="metric-card">
      <div class="metric-head">
        <span class="metric-title">地上2M 平均風速</span>
        <span class="metric-icon" style="background: #ecfdf5; color: #059669;">💨</span>
      </div>
      <div class="metric-value">{data['avg_wind']}<span> m/s</span></div>
      <div class="metric-foot">
        <span>時速 <strong>{data['avg_wind_kmh']} km/h</strong></span>
        <span>最大 <strong>{data['max_wind']} m/s</strong></span>
      </div>
    </div>

    <div class="metric-card">
      <div class="metric-head">
        <span class="metric-title">平均相対湿度</span>
        <span class="metric-icon" style="background: #faf5ff; color: #9333ea;">💧</span>
      </div>
      <div class="metric-value">{data['avg_rh']}<span> %</span></div>
      <div class="metric-foot">
        <span>年間降雨日数 <strong>約 {data['annual_rainy_days']} 日</strong></span>
        <span style="color:#6366f1; font-weight:bold;">湿潤</span>
      </div>
    </div>
  </div>

  <div class="chart-panel">
    <div class="chart-header">
      <div class="chart-title-group">
        <h3 id="currentChartTitle">3年間の月別 気象比較 (月平均気温)</h3>
        <p id="currentChartSub">各月における推移と年次比較</p>
      </div>
      <div class="tab-group">
        <button class="tab-btn active" onclick="switchMetric('temp_avg', '月平均気温', '℃', 'line')">平均気温</button>
        <button class="tab-btn" onclick="switchMetric('temp_max', '最高気温(極値)', '℃', 'line')">最高気温</button>
        <button class="tab-btn" onclick="switchMetric('temp_min', '最低気温(極値)', '℃', 'line')">最低気温</button>
        <button class="tab-btn" onclick="switchMetric('precip', '月間降水量', 'mm', 'bar')">降水量</button>
        <button class="tab-btn" onclick="switchMetric('solar', '日射量', 'MJ/m²', 'line')">日射量</button>
        <button class="tab-btn" onclick="switchMetric('wind', '風速', 'm/s', 'line')">風速</button>
      </div>
    </div>
    
    <div class="chart-wrapper">
      <canvas id="weatherMainChart"></canvas>
    </div>

    <div class="precip-summary-grid">
      <div class="summary-box" style="background: #fffbeb; border: 1px solid #fef3c7;">
        <div style="font-size: 0.75em; color: #b45309; font-weight: bold;">YEAR {y1}</div>
        <div style="font-size: 1.2em; font-weight: 900; color: #78350f; margin: 2px 0;">{data['yearly_stats'][y1]['precip_total']} <span style="font-size: 0.65em;">mm</span></div>
        <div style="font-size: 0.72em; color: #92400e;">雨天: {data['yearly_stats'][y1]['rainy_days']}日 ({'+' if diff_y1 >= 0 else ''}{diff_y1}mm)</div>
      </div>
      <div class="summary-box" style="background: #eff6ff; border: 1px solid #dbeafe;">
        <div style="font-size: 0.75em; color: #1d4ed8; font-weight: bold;">YEAR {y2}</div>
        <div style="font-size: 1.2em; font-weight: 900; color: #1e40af; margin: 2px 0;">{data['yearly_stats'][y2]['precip_total']} <span style="font-size: 0.65em;">mm</span></div>
        <div style="font-size: 0.72em; color: #1e3a8a;">雨天: {data['yearly_stats'][y2]['rainy_days']}日 ({'+' if diff_y2 >= 0 else ''}{diff_y2}mm)</div>
      </div>
      <div class="summary-box" style="background: #ecfdf5; border: 1px solid #a7f3d0;">
        <div style="font-size: 0.75em; color: #047857; font-weight: bold;">YEAR {y3}</div>
        <div style="font-size: 1.2em; font-weight: 900; color: #065f46; margin: 2px 0;">{data['yearly_stats'][y3]['precip_total']} <span style="font-size: 0.65em;">mm</span></div>
        <div style="font-size: 0.72em; color: #064e3b;">雨天: {data['yearly_stats'][y3]['rainy_days']}日 ({'+' if diff_y3 >= 0 else ''}{diff_y3}mm)</div>
      </div>
    </div>
  </div>

  <div class="footer-note">データソース: NASA POWER (MERRA-2 &amp; GEOS-FP) / 自動同期ダッシュボード</div>

</div>

<script>
  const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
  const rawDatasets = {chart_data_json};
  const years = [{y1}, {y2}, {y3}];
  const colorMap = [
    {{ border: '#f97316', bg: 'rgba(249, 115, 22, 0.15)', bar: '#f97316' }},
    {{ border: '#2563eb', bg: 'rgba(37, 99, 235, 0.15)', bar: '#2563eb' }},
    {{ border: '#10b981', bg: 'rgba(16, 185, 129, 0.15)', bar: '#10b981' }}
  ];

  let chartInstance = null;

  function renderChart(metricKey, unit, type) {{
    const ctx = document.getElementById('weatherMainChart').getContext('2d');
    if (chartInstance) chartInstance.destroy();

    const datasets = years.map((y, idx) => {{
      const base = {{
        label: y + '年',
        data: rawDatasets[metricKey][y]
      }};
      if (type === 'line') {{
        return {{
          ...base,
          borderColor: colorMap[idx].border,
          backgroundColor: colorMap[idx].bg,
          tension: 0.35,
          pointRadius: 4,
          pointHoverRadius: 6,
          fill: false
        }};
      }} else {{
        return {{
          ...base,
          backgroundColor: colorMap[idx].bar,
          borderRadius: 4
        }};
      }}
    }});

    chartInstance = new Chart(ctx, {{
      type: type,
      data: {{ labels: months, datasets: datasets }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        interaction: {{ mode: 'index', intersect: false }},
        plugins: {{
          legend: {{ position: 'top', labels: {{ boxWidth: 12, font: {{ weight: 'bold' }} }} }},
          tooltip: {{
            callbacks: {{
              label: (context) => `${{context.dataset.label}}: ${{context.parsed.y}} ${{unit}}`
            }}
          }}
        }},
        scales: {{
          y: {{
            grid: {{ color: '#f1f5f9' }},
            ticks: {{ callback: (v) => v + ' ' + unit }}
          }},
          x: {{ grid: {{ display: false }} }}
        }}
      }}
    }});
  }}

  function switchMetric(key, label, unit, type) {{
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    document.getElementById('currentChartTitle').textContent = `3年間の月別 気象比較 (${{label}})`;
    renderChart(key, unit, type);
  }}

  window.addEventListener('DOMContentLoaded', () => {{
    renderChart('temp_avg', '℃', 'line');
  }});
</script>
</body>
</html>"""

    escaped_srcdoc = html.escape(raw_inner_html, quote=True)
    embed_iframe = f'<iframe srcdoc="{escaped_srcdoc}" style="width: 100%; min-height: 840px; border: none; border-radius: 16px; overflow: hidden;" loading="lazy"></iframe>'
    return embed_iframe

def main():
    current_year = datetime.now().year
    start_year = current_year - 3
    end_year = current_year - 1

    print(f"NASA POWERから {LOCATION_NAME} の気象データを取得中 ({start_year}〜{end_year})...")
    data = fetch_weather_dashboard_data(LATITUDE, LONGITUDE, start_year, end_year)

    today_str = datetime.now().strftime("%Y-%m-%d")
    title = f"【気象ダッシュボード】{LOCATION_NAME} ({today_str} 更新)"
    content_html = build_interactive_dashboard_html(data)

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
