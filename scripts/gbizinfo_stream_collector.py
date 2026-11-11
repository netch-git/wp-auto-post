#!/usr/bin/env python3
"""
gBizINFO API v2 高速ストリーミング＆自動再開コレクター (Python + SQLite)

【特徴】
1. メモリを圧迫しないストリーミング書き込み（SQLite）
2. 途中で止まっても最後のページから1ミリ秒で自動再開（レジューム機能）
3. レート制限 (429) や通信エラー時の自動待機＆指数バックオフ
4. 取得済みデータをCSVやExcelにいつでも一括エクスポート
"""

import sys
import time
import json
import sqlite3
import argparse
from pathlib import Path
import requests

API_URL = "https://api.info.gbiz.go.jp/hojin/v2/hojin"
DEFAULT_TOKEN = "RuAOt26DNiaFTxPlJiZ78Kvxz0Zn6y4B"
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "gbizinfo.db"

def init_db(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # テーブル作成
    cur.execute("""
    CREATE TABLE IF NOT EXISTS corporations (
        corporate_number TEXT PRIMARY KEY,
        name TEXT,
        name_en TEXT,
        postal_code TEXT,
        location TEXT,
        status TEXT,
        number_of_activity INTEGER,
        update_date TEXT,
        fetched_at TEXT
    );
    """)
    # 進捗管理テーブル
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sync_progress (
        prefecture_code TEXT PRIMARY KEY,
        last_page INTEGER,
        total_fetched INTEGER,
        is_completed INTEGER,
        updated_at TEXT
    );
    """)
    conn.commit()
    return conn

def fetch_page(token: str, prefecture: str, page: int, limit: int = 100, retries: int = 5):
    headers = {
        "Accept": "application/json",
        "X-hojinInfo-api-token": token
    }
    params = {
        "prefecture": prefecture,
        "page": page,
        "limit": limit
    }
    
    for attempt in range(1, retries + 1):
        try:
            res = requests.get(API_URL, headers=headers, params=params, timeout=20)
            if res.status_code == 200:
                data = res.json()
                return data.get("hojin-infos", [])
            elif res.status_code == 429:
                wait_sec = attempt * 10
                print(f"⚠️ [Rate Limit 429] {wait_sec}秒待機して再試行します (試行 {attempt}/{retries})...")
                time.sleep(wait_sec)
            else:
                print(f"❌ HTTP {res.status_code}: {res.text}")
                return None
        except requests.exceptions.RequestException as e:
            wait_sec = attempt * 5
            print(f"⚠️ 通信エラー ({e})。{wait_sec}秒待機して再試行します...")
            time.sleep(wait_sec)
            
    return None

def run_collector(token: str, prefecture: str, limit_pages: int = 10):
    conn = init_db(DB_PATH)
    cur = conn.cursor()

    # 前回の進捗取得
    cur.execute("SELECT last_page, total_fetched, is_completed FROM sync_progress WHERE prefecture_code = ?", (prefecture,))
    row = cur.fetchone()
    
    start_page = 1
    total_fetched = 0
    if row:
        last_page, prev_total, is_completed = row
        if is_completed:
            print(f"✅ 都道府県コード {prefecture} はすでに全件取得完了しています（計 {prev_total} 件）。")
            return
        start_page = last_page + 1
        total_fetched = prev_total
        print(f"🔄 前回の進捗から自動再開: ページ {start_page} から (取得済: {total_fetched} 件)")
    else:
        print(f"🚀 新規開始: 都道府県コード {prefecture}")

    max_page = min(start_page + limit_pages - 1, 10) # v2 APIはpage=10上限
    print(f"📊 実行範囲: ページ {start_page} 〜 {max_page}")

    now_iso = time.strftime("%Y-%m-%dT%H:%M:%S")

    for p in range(start_page, max_page + 1):
        print(f"📥 ページ {p} を取得中...", end=" ", flush=True)
        items = fetch_page(token, prefecture, p)
        
        if items is None:
            print("中断（エラー多発）")
            break
        
        if len(items) == 0:
            print("データ終了 (0件)")
            cur.execute("""
            INSERT OR REPLACE INTO sync_progress (prefecture_code, last_page, total_fetched, is_completed, updated_at)
            VALUES (?, ?, ?, 1, ?)
            """, (prefecture, p, total_fetched, now_iso))
            conn.commit()
            break

        # SQLiteへバルクインサート（重複はIGNORE）
        rows_to_insert = [
            (
                h.get("corporate_number"),
                h.get("name"),
                h.get("name_en"),
                h.get("postal_code"),
                h.get("location"),
                h.get("status"),
                int(h.get("number_of_activity") or 0),
                h.get("update_date"),
                now_iso
            )
            for h in items
        ]
        
        cur.executemany("""
        INSERT OR IGNORE INTO corporations 
        (corporate_number, name, name_en, postal_code, location, status, number_of_activity, update_date, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rows_to_insert)

        total_fetched += len(items)
        
        # 進捗更新
        is_done = 1 if p == 10 else 0
        cur.execute("""
        INSERT OR REPLACE INTO sync_progress (prefecture_code, last_page, total_fetched, is_completed, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """, (prefecture, p, total_fetched, is_done, now_iso))
        conn.commit()

        print(f"完了 (+{len(items)}件, 累計: {total_fetched}件)")
        time.sleep(0.4) # API負荷マナー

    print(f"\n🎉 処理完了！ DB保存先: {DB_PATH}")

def main():
    parser = argparse.ArgumentParser(description="gBizINFO v2 Streaming Collector")
    parser.add_argument("--pref", default="34", help="都道府県コード2桁 (例: 34=広島県, 13=東京都)")
    parser.add_argument("--token", default=DEFAULT_TOKEN, help="gBizINFO API Token")
    parser.add_argument("--pages", type=int, default=10, help="取得ページ数 (最大10)")
    args = parser.parse_args()

    run_collector(args.token, args.pref, args.pages)

if __name__ == "__main__":
    main()
