import sqlite3
import datetime
from pathlib import Path
from typing import List, Dict, Optional

DB_NAME = "habit_cinematic.db"

def get_db_path() -> str:
    """Returns the path to the database file."""
    # Using the current working directory for simplicity as per requirements
    return DB_NAME

def init_db():
    """Initializes the database table if it doesn't exist."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS diary_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            raw_text TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def create_entry(raw_text: str, date: Optional[str] = None):
    """
    Creates a new diary entry.
    
    Args:
        raw_text: The content of the diary entry.
        date: Optional date string (YYYY-MM-DD). Defaults to today if not provided.
    """
    if date is None:
        date = datetime.date.today().isoformat()
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO diary_entries (date, raw_text) VALUES (?, ?)",
        (date, raw_text)
    )
    conn.commit()
    conn.close()

def list_entries() -> List[Dict]:
    """
    Lists all diary entries ordered by date descending.
    
    Returns:
        A list of dictionaries containing entry data.
    """
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, date, raw_text FROM diary_entries ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

if __name__ == "__main__":
    # Simple test when running the module directly
    init_db()
    print("Database initialized.")
    create_entry("Today I started the Habit Cinematic project.", "2023-10-27")
    create_entry("Another productive day coding.")
    print("Entries:")
    for entry in list_entries():
        print(entry)
