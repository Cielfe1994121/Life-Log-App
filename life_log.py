import sqlite3
import datetime
import sys
import io
import os

# Database: ./life_log.db

# --- 1. 準備 ---
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')

def get_db_connection():
    """DBに接続し、テーブルを準備して、コネクションを返す"""
    # 1. 実行ファイル（.py）がある場所を自動取得
    # sys.argv[0] はこのプログラム自身のパス。abspathで「完全な住所」にする。
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    path = os.path.join(base_dir, 'life_log.db')
    conn = sqlite3.connect(path)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS life_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            event TEXT
        )
    ''')
    return conn

# --- 2. DB操作関数群 ---

def save_event(conn, event_text):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur = conn.cursor()
    cur.execute('INSERT INTO life_events (timestamp, event) VALUES (?, ?)', (now, event_text))
    conn.commit()

def fetch_events_by_date(conn, target_date):
    cur = conn.cursor()
    cur.execute("SELECT * FROM life_events WHERE timestamp LIKE ?", (f"{target_date}%",)) 
    return cur.fetchall()

def search_event(conn, search_word):
    """【修正ポイント】前後に % をつけて あいまい検索 にする"""
    cur = conn.cursor()
    cur.execute("SELECT * FROM life_events WHERE event LIKE ?", (f"%{search_word}%",))
    return cur.fetchall()

def delete_event(conn, event_id):
    cur = conn.cursor()
    cur.execute("DELETE FROM life_events WHERE id = ?", (event_id,))
    conn.commit()
    print(f"ID:{event_id}の記録を消去しました。")

# --- 3. メイン処理 ---

def main():
    conn = get_db_connection()
    
    print("--- 人生ログ入力モード（\"exit\"で終了） --- Database: ./life_log.db")
    while True:
        event_text = input("記録を打ち込んでね: ")
        if event_text.lower() == 'exit': break
        if event_text:
            save_event(conn, event_text)
            print(f"保存完了: {event_text}")

    print("\nどの記録を表示しますか？")
    print("1:今日, 2:昨日, 3:全部, 4:指定日以降すべて")
    print("直接入力（日付: 2025-12-25とか / 単語: だし巻き卵とか）")

    choice = input(">> ")
    rows = []

    if choice == "1":
        rows = fetch_events_by_date(conn, datetime.datetime.now().strftime('%Y-%m-%d'))
    elif choice == "2":
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        rows = fetch_events_by_date(conn, yesterday)
    elif choice == "3":
        cur = conn.cursor()
        cur.execute('SELECT * FROM life_events')
        rows = cur.fetchall()
    elif choice == "4":
        start_date = input("いつから？ (YYYY-MM-DD): ")
        cur = conn.cursor()
        cur.execute("SELECT * FROM life_events WHERE timestamp >= ?", (f"{start_date} 00:00:00",))
        rows = cur.fetchall()
    else:
        # 【修正ロジック】まず日付として検索し、なければ単語検索
        rows = fetch_events_by_date(conn, choice)
        if not rows:
            rows = search_event(conn, choice)
            print(f"\n--- キーワード「{choice}」の検索結果 ---")
        else:
            print(f"\n--- 日付「{choice}」の記録 ---")

    # 表示処理
    if not rows:
        print("該当する記録はありません。")
    for row in rows:
        print(f"[ID:{row[0]}][{row[1]}] {row[2]}")

    print("\n\"exit\"で終了。\"delete\"でID削除。")
    choice2 = input(">> ")
    if choice2.lower() == "delete":
        delete_id = input("削除するIDを入力: ")
        if delete_id.isdigit(): # 数字かどうかチェック
            delete_event(conn, delete_id)
        else:
            print("エラー: IDは数字で入力してください。")
    conn.close()

if __name__ == "__main__":
    main()