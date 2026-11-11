import sqlite3
import json
import math
import os
import shutil

DB_PATH = 'data/hiroshima_analytics.db'
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 1. Fetch all corporations
cur.execute('''
    SELECT corporate_number, name, corporate_type, city, location, patent_count, subsidy_count, certification_count, procurement_count
    FROM corporations
    ORDER BY patent_count DESC, subsidy_count DESC, corporate_number ASC
''')
type_map = {'101':'国の機関', '201':'地方自治体', '301':'株式会社', '302':'有限会社', '305':'合同会社', '401':'その他'}
all_corps = []
for r in cur.fetchall():
    badges = []
    if r[5] > 0: badges.append(f'特許{r[5]:,}件')
    if r[6] > 0: badges.append(f'補助金{r[6]:,}件')
    if r[7] > 0: badges.append('認定取得')
    if r[8] > 0: badges.append('調達実績')
    all_corps.append({
        'n': r[0],
        'm': r[1],
        't': type_map.get(r[2], r[2]),
        'c': r[3] if r[3] else '県内',
        'l': r[4] if r[4] else '',
        'b': '・'.join(badges) if badges else '一般登記'
    })

print(f"Loaded {len(all_corps)} corporations.")

# 2. Municipal coordinates and aggregation
coords = {
    '広島市中区': [34.3892, 132.4552],
    '広島市西区': [34.3980, 132.4286],
    '広島市南区': [34.3812, 132.4770],
    '広島市安佐南区': [34.4526, 132.4497],
    '広島市安佐北区': [34.5186, 132.5097],
    '広島市東区': [34.4124, 132.4920],
    '広島市佐伯区': [34.3687, 132.3619],
    '福山市': [34.4858, 133.3626],
    '東広島市': [34.4270, 132.7432],
    '広島市安芸区': [34.3639, 132.5317],
    '呉市': [34.2494, 132.5658],
    '府中市': [34.5702, 133.2366],
    '尾道市': [34.4093, 133.1972],
    '廿日市市': [34.3486, 132.3314],
    '安芸郡府中町': [34.3957, 132.5029],
    '三原市': [34.4011, 133.0827],
    '三次市': [34.8055, 132.8524],
    '安芸高田市': [34.6657, 132.7058],
    '江田島市': [34.2464, 132.4746],
    '安芸郡海田町': [34.3644, 132.5332],
    '大竹市': [34.2201, 132.2217],
    '庄原市': [34.8582, 133.0177],
    '山県郡北広島町': [34.6749, 132.5398],
    '竹原市': [34.3435, 132.9103],
    '世羅郡世羅町': [34.5901, 133.0569],
    '神石郡神石高原町': [34.7397, 133.2758],
    '山県郡安芸太田町': [34.5982, 132.2359],
    '安芸郡熊野町': [34.3387, 132.5847],
    '安芸郡坂町': [34.3319, 132.5098],
    '豊田郡大崎上島町': [34.2462, 132.9056]
}

cur.execute('''
    SELECT city, count(*) as cnt, sum(patent_count), sum(subsidy_count)
    FROM corporations
    GROUP BY city
    ORDER BY cnt DESC
''')
city_stats = cur.fetchall()

markers = []
zipf_points = []
total_corps = sum(r[1] for r in city_stats)

for rank, (city, cnt, pats, subs) in enumerate(city_stats, 1):
    lat, lng = coords.get(city, [34.3963, 132.4594])
    markers.append({
        'name': city,
        'count': cnt,
        'lat': lat,
        'lng': lng,
        'patents': pats,
        'subsidies': subs,
        'rank': rank
    })
    zipf_points.append({
        'x': round(math.log(cnt), 4),
        'y': round(math.log(rank), 4),
        'name': city,
        'count': cnt,
        'rank': rank
    })

# OLS for Zipf
n = len(zipf_points)
sum_x = sum(p['x'] for p in zipf_points)
sum_y = sum(p['y'] for p in zipf_points)
sum_xx = sum(p['x']**2 for p in zipf_points)
sum_xy = sum(p['x']*p['y'] for p in zipf_points)
beta = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x**2)
alpha = (sum_y - beta * sum_x) / n

# Gini
counts_sorted = sorted([r[1] for r in city_stats])
cum_y = [0]
cur_sum = 0
for c in counts_sorted:
    cur_sum += c
    cum_y.append(round(cur_sum / total_corps * 100, 2))
lorenz_pts = []
for i, y_val in enumerate(cum_y):
    x_val = round(i / len(counts_sorted) * 100, 2)
    lorenz_pts.append({'x': x_val, 'y': y_val})

b_area = 0
for i in range(len(counts_sorted)):
    b_area += (cum_y[i] + cum_y[i+1]) / 2 * (100 / len(counts_sorted))
gini = round((5000 - b_area) / 5000, 4)

# 3. Top Address Clusters
cur.execute('''
    SELECT location, city, count(*) as cnt
    FROM corporations
    GROUP BY location
    HAVING cnt >= 3
    ORDER BY cnt DESC
    LIMIT 8
''')
clusters = [{'loc': r[0], 'city': r[1], 'cnt': r[2]} for r in cur.fetchall()]

# 4. Regional Blocs
bloc_definitions = {
    '広島都市圏': ['広島市中区', '広島市西区', '広島市南区', '広島市安佐南区', '広島市安佐北区', '広島市東区', '広島市佐伯区', '広島市安芸区', '廿日市市', '安芸郡府中町', '安芸郡海田町', '大竹市', '安芸郡熊野町', '安芸郡坂町'],
    '備後都市圏': ['福山市', '府中市', '尾道市', '三原市', '世羅郡世羅町', '神石郡神石高原町'],
    '西条学術圏': ['東広島市'],
    '芸南沿岸圏': ['呉市', '江田島市', '竹原市', '豊田郡大崎上島町'],
    '中山間県北': ['三次市', '安芸高田市', '庄原市', '山県郡北広島町', '山県郡安芸太田町']
}

blocs_data = []
for b_name, c_list in bloc_definitions.items():
    placeholders = ','.join('?' for _ in c_list)
    cur.execute(f'''
        SELECT
            count(*),
            sum(case when corporate_type = '301' then 1 else 0 end),
            sum(case when corporate_type = '302' then 1 else 0 end),
            sum(case when corporate_type = '305' then 1 else 0 end)
        FROM corporations
        WHERE city IN ({placeholders})
    ''', c_list)
    res = cur.fetchone()
    blocs_data.append({
        'name': b_name,
        'corps': res[0],
        'kabu': res[1],
        'yugen': res[2],
        'godo': res[3]
    })

stats_payload = {
    'total_corps': total_corps,
    'zipf': {
        'alpha': round(alpha, 4),
        'beta': round(beta, 4),
        'points': zipf_points
    },
    'gini': gini,
    'lorenz': lorenz_pts,
    'blocs': blocs_data,
    'mapMarkers': markers,
    'clusters': clusters
}

print(f"Stats compiled: Zipf alpha={round(alpha,4)}, beta={round(beta,4)}, Gini={gini}")

# Serialize JSON
corps_json_str = json.dumps(all_corps, ensure_ascii=False)
stats_json_str = json.dumps(stats_payload, ensure_ascii=False)

# Read HTML template
with open('scripts/template.html', 'r', encoding='utf-8') as f:
    template = f.read()

html_output = template.replace('__STATS_JSON__', stats_json_str).replace('__CORPS_JSON__', corps_json_str)

os.makedirs('site', exist_ok=True)
with open('site/index.html', 'w', encoding='utf-8') as f:
    f.write(html_output)
print(f"Generated site/index.html ({len(html_output)/1024:.1f} KB)")

os.makedirs('dist', exist_ok=True)
with open('dist/index.html', 'w', encoding='utf-8') as f:
    f.write(html_output)
print(f"Generated dist/index.html ({len(html_output)/1024:.1f} KB)")

artifact_dir = "/home/antigravity/.gemini/jetski/brain/v1/default/jetski_remote_agents_3p/dc026dd2-9b4e-4139-9ba8-efe4b4c29953"
if os.path.exists(artifact_dir):
    target = os.path.join(artifact_dir, 'hiroshima_whitepaper_editorial.html')
    shutil.copyfile('dist/index.html', target)
    print(f"Copied to artifact directory: {target}")

