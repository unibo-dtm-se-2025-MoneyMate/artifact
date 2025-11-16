"""
Core SQLite schema and connection utilities for MoneyMate.

This module is the central place for:

- Creating and configuring SQLite connections (foreign keys, row factory).
- Initializing and migrating the MoneyMate database schema:
  users, contacts, expenses, transactions, categories, notes, attachments,
  access_logs, and schema_version.
- Performing non-destructive migrations to keep older DBs compatible.
- Exposing helpers to query schema_version and list user tables.

It is used by DatabaseManager and by higher-level modules that need a DB path.
"""

import sqlite3
from typing import Dict, Any, Optional

# Default database path used by DatabaseManager when no path is provided.
DB_PATH = "moneymate.db"

# Simple schema versioning scaffold
SCHEMA_VERSION = 2  # v2: tightened CHECKS, migration scaffold

def get_connection(db_path: str) -> sqlite3.Connection:
    """
    Return a new SQLite connection with foreign key support enabled.
    """
    if isinstance(db_path, str) and db_path.startswith("file:"):
        conn = sqlite3.connect(db_path, uri=True)
    else:
        conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def _get_current_version(cur: sqlite3.Cursor) -> Optional[int]:
    cur.execute("SELECT COUNT(*) AS cnt FROM sqlite_schema WHERE type='table' AND name='schema_version';")
    exists = cur.fetchone()["cnt"] > 0
    if not exists:
        return None
    cur.execute("SELECT version FROM schema_version LIMIT 1;")
    row = cur.fetchone()
    return int(row["version"]) if row else None

def _set_version(cur: sqlite3.Cursor, version: int) -> None:
    cur.execute("DELETE FROM schema_version;")
    cur.execute("INSERT INTO schema_version (version) VALUES (?);", (version,))

def _migrate(cur: sqlite3.Cursor, from_version: int, to_version: int) -> None:
    """
    Non-destructive migration scaffold.
    """
    _set_version(cur, to_version)

def init_db(db_path: str) -> Dict[str, Any]:
    """
    Initialize the database with necessary tables.
    """
    try:
        conn = get_connection(db_path)
        cur = conn.cursor()

        # Schema version table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER NOT NULL
            );
        """)
        current_version = _get_current_version(cur)
        if current_version is None:
            _set_version(cur, SCHEMA_VERSION)

        # Users
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user','admin')),
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)

        # Contacts
        cur.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE (user_id, name),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_contacts_user_id ON contacts(user_id);")

        # Expenses
        cur.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                price REAL NOT NULL CHECK (price > 0),
                date TEXT NOT NULL,
                category TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                category_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_expenses_user_id ON expenses(user_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_expenses_user_date ON expenses(user_id, date);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_expenses_category_id ON expenses(category_id);")

        # Transactions
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER NOT NULL,
                to_user_id INTEGER NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('credit','debit')),
                amount REAL NOT NULL CHECK (amount > 0),
                date TEXT NOT NULL,
                description TEXT,
                contact_id INTEGER,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                CHECK (from_user_id <> to_user_id),
                FOREIGN KEY (from_user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (to_user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE SET NULL
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_transactions_from_user ON transactions(from_user_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_transactions_to_user ON transactions(to_user_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_transactions_from_user_date ON transactions(from_user_id, date);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_transactions_to_user_date ON transactions(to_user_id, date);")

        # Categories
        cur.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                color TEXT,
                icon TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE (user_id, name),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_categories_user_id ON categories(user_id);")

        # Notes
        cur.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                expense_id INTEGER,
                transaction_id INTEGER,
                contact_id INTEGER,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (expense_id) REFERENCES expenses(id) ON DELETE CASCADE,
                FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
                FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE,
                CHECK (expense_id IS NOT NULL OR transaction_id IS NOT NULL OR contact_id IS NOT NULL)
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_notes_user_id ON notes(user_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_notes_expense_id ON notes(expense_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_notes_transaction_id ON notes(transaction_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_notes_contact_id ON notes(contact_id);")

        # Attachments
        cur.execute("""
            CREATE TABLE IF NOT EXISTS attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                expense_id INTEGER,
                transaction_id INTEGER,
                contact_id INTEGER,
                file_path TEXT NOT NULL,
                mime_type TEXT,
                size_bytes INTEGER,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (expense_id) REFERENCES expenses(id) ON DELETE CASCADE,
                FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
                FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE,
                CHECK (expense_id IS NOT NULL OR transaction_id IS NOT NULL OR contact_id IS NOT NULL)
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_attachments_user_id ON attachments(user_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_attachments_expense_id ON attachments(expense_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_attachments_transaction_id ON attachments(transaction_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_attachments_contact_id ON attachments(contact_id);")

        # Access logs
        cur.execute("""
            CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL CHECK (action IN (
                    'login','logout','failed_login','password_change','password_reset'
                )),
                ip_address TEXT,
                user_agent TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_access_logs_user_id ON access_logs(user_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_access_logs_action ON access_logs(action);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_access_logs_created_at ON access_logs(created_at);")

        # --- NON-DESTRUCTIVE MIGRATIONS (before commit) ---

        # Ensure expenses.category_id exists (old DBs)
        try:
            cur.execute("PRAGMA table_info(expenses);")
            expense_cols = {row["name"] for row in cur.fetchall()}
            if "category_id" not in expense_cols:
                cur.execute("ALTER TABLE expenses ADD COLUMN category_id INTEGER;")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_expenses_category_id ON expenses(category_id);")
        except Exception:
            pass

        # Ensure categories.user_id exists (old DBs)
        try:
            cur.execute("PRAGMA table_info(categories);")
            cat_cols = {row["name"] for row in cur.fetchall()}
            if "user_id" not in cat_cols:
                cur.execute("ALTER TABLE categories ADD COLUMN user_id INTEGER;")
        except Exception:
            pass

        # Ensure transactions.from_user_id / to_user_id exist (old DBs)
        try:
            cur.execute("PRAGMA table_info(transactions);")
            tx_cols = {row["name"] for row in cur.fetchall()}
            if "from_user_id" not in tx_cols:
                cur.execute("ALTER TABLE transactions ADD COLUMN from_user_id INTEGER;")
            if "to_user_id" not in tx_cols:
                cur.execute("ALTER TABLE transactions ADD COLUMN to_user_id INTEGER;")
        except Exception:
            pass

        # Ensure users.is_active exists (used by user manager)
        try:
            cur.execute("PRAGMA table_info(users);")
            usr_cols = {row["name"] for row in cur.fetchall()}
            if "is_active" not in usr_cols:
                cur.execute("ALTER TABLE users ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1;")
        except Exception:
            pass

        # Bump schema version if needed
        current_version = _get_current_version(cur)
        if current_version is not None and current_version < SCHEMA_VERSION:
            _migrate(cur, current_version, SCHEMA_VERSION)

        conn.commit()
        return {"success": True, "error": None, "data": "initialized"}
    except Exception as e:
        return {"success": False, "error": str(e), "data": None}
    finally:
        try:
            conn.close()
        except Exception:
            pass

def get_schema_version(db_path: str) -> Dict[str, Any]:
    try:
        conn = get_connection(db_path)
        cur = conn.cursor()
        cur.execute("SELECT version FROM schema_version LIMIT 1;")
        row = cur.fetchone()
        version = int(row["version"]) if row else None
        return {"success": True, "error": None, "data": version}
    except Exception as e:
        return {"success": False, "error": str(e), "data": None}
    finally:
        try:
            conn.close()
        except Exception:
            pass

def list_tables(db_path: str) -> Dict[str, Any]:
    """
    Return a dict with 'data' key containing user-defined tables.
    """
    try:
        conn = get_connection(db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT name
            FROM sqlite_schema
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name;
        """)
        rows = cur.fetchall()
        tables = [r["name"] for r in rows]
        return {"success": True, "error": None, "data": tables}
    except Exception as e:
        return {"success": False, "error": str(e), "data": []}
    finally:
        try:
            conn.close()
        except Exception:
            pass