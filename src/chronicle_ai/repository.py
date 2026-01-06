"""
Chronicle AI - Repository Layer

SQLite-based storage for diary entries with full CRUD operations.
"""

import sqlite3
from pathlib import Path
from typing import List, Optional
from datetime import date, timedelta

from .models import Entry


# Default database location (can be overridden via environment variable)
DEFAULT_DB_NAME = "chronicle_ai.db"


class EntryRepository:
    """
    Repository for managing diary entries in SQLite database.
    
    Provides CRUD operations and query functions for Entry objects.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the repository with optional custom database path.
        
        Args:
            db_path: Path to SQLite database file. Uses DEFAULT_DB_NAME if not provided.
        """
        self.db_path = db_path or DEFAULT_DB_NAME
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory configured."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """Initialize the database schema if not exists."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Check if we need to migrate (add new columns)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='diary_entries'")
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            # Check for existing columns and add missing ones
            cursor.execute("PRAGMA table_info(diary_entries)")
            columns = {row['name'] for row in cursor.fetchall()}
            
            if 'narrative_text' not in columns:
                cursor.execute("ALTER TABLE diary_entries ADD COLUMN narrative_text TEXT")
            if 'title' not in columns:
                cursor.execute("ALTER TABLE diary_entries ADD COLUMN title TEXT")
        else:
            # Create table with all columns
            cursor.execute("""
                CREATE TABLE diary_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    raw_text TEXT NOT NULL,
                    narrative_text TEXT,
                    title TEXT
                )
            """)
        
        conn.commit()
        conn.close()
    
    def create_entry(self, entry: Entry) -> Entry:
        """
        Create a new diary entry in the database.
        
        Args:
            entry: Entry object to save (id will be assigned)
            
        Returns:
            Entry with assigned id
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO diary_entries (date, raw_text, narrative_text, title) 
               VALUES (?, ?, ?, ?)""",
            (entry.date, entry.raw_text, entry.narrative_text, entry.title)
        )
        
        entry.id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return entry
    
    def update_entry(self, entry: Entry) -> Entry:
        """
        Update an existing entry in the database.
        
        Args:
            entry: Entry object with id set
            
        Returns:
            Updated entry
        """
        if entry.id is None:
            raise ValueError("Cannot update entry without id")
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """UPDATE diary_entries 
               SET date = ?, raw_text = ?, narrative_text = ?, title = ?
               WHERE id = ?""",
            (entry.date, entry.raw_text, entry.narrative_text, entry.title, entry.id)
        )
        
        conn.commit()
        conn.close()
        
        return entry
    
    def get_entry_by_id(self, entry_id: int) -> Optional[Entry]:
        """
        Retrieve an entry by its ID.
        
        Args:
            entry_id: The unique entry identifier
            
        Returns:
            Entry if found, None otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, date, raw_text, narrative_text, title FROM diary_entries WHERE id = ?",
            (entry_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Entry.from_dict(dict(row))
        return None
    
    def list_entries(self, limit: Optional[int] = None) -> List[Entry]:
        """
        List all entries ordered by date descending.
        
        Args:
            limit: Maximum number of entries to return (None for all)
            
        Returns:
            List of Entry objects
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT id, date, raw_text, narrative_text, title FROM diary_entries ORDER BY date DESC, id DESC"
        if limit:
            query += f" LIMIT {int(limit)}"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        return [Entry.from_dict(dict(row)) for row in rows]
    
    def list_recent_entries(self, n: int = 7) -> List[Entry]:
        """
        Get the N most recent entries.
        
        Args:
            n: Number of entries to retrieve
            
        Returns:
            List of Entry objects
        """
        return self.list_entries(limit=n)
    
    def list_entries_between_dates(self, start_date: str, end_date: str) -> List[Entry]:
        """
        Get entries within a date range (inclusive).
        
        Args:
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            
        Returns:
            List of Entry objects
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT id, date, raw_text, narrative_text, title 
               FROM diary_entries 
               WHERE date >= ? AND date <= ?
               ORDER BY date DESC, id DESC""",
            (start_date, end_date)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [Entry.from_dict(dict(row)) for row in rows]
    
    def list_entries_last_n_days(self, days: int = 7) -> List[Entry]:
        """
        Get entries from the last N days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of Entry objects
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)
        return self.list_entries_between_dates(
            start_date.isoformat(),
            end_date.isoformat()
        )
    
    def delete_entry(self, entry_id: int) -> bool:
        """
        Delete an entry by ID.
        
        Args:
            entry_id: The entry ID to delete
            
        Returns:
            True if entry was deleted, False if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM diary_entries WHERE id = ?", (entry_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted


# Global repository instance for convenience
_default_repo: Optional[EntryRepository] = None


def get_repository(db_path: Optional[str] = None) -> EntryRepository:
    """
    Get the default repository instance (creates one if needed).
    
    Args:
        db_path: Optional custom database path
        
    Returns:
        EntryRepository instance
    """
    global _default_repo
    if _default_repo is None or db_path is not None:
        _default_repo = EntryRepository(db_path)
    return _default_repo
