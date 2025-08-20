import sqlite3
from typing import Dict, Any, Optional
from datetime import datetime

DB_PATH = "moneymate.db"

def dict_response(success: bool, error: Optional[str] = None, data: Any = None) -> Dict[str, Any]:
    """return a standardized dictionary for all API responses."""
    return {"success": success, "error": error, "data": data}

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Creates the tables if they do not exist in the SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor() # To execute SQL commands
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                price REAL NOT NULL,
                date TEXT NOT NULL,
                category TEXT NOT NULL
            )""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER NOT NULL,
                type TEXT CHECK(type IN ('debit', 'credit')) NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY(contact_id) REFERENCES contacts(id)
            )""")
        conn.commit()
        conn.close()