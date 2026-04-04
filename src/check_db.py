import sqlite3
import os

db_path = "chronicle_ai.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, raw_text FROM diary_entries")
    for row in cursor.fetchall():
        print(f"ID {row[0]}: {row[1][:100]}...")
    conn.close()
