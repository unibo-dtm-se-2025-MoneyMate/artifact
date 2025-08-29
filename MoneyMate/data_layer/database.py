"""
Database utilities for MoneyMate: initialization, connections, and schema management.

This module:
- Defines a default DB_PATH for the manager default.
- Initializes the SQLite database with all required tables.
- Ensures PRAGMA foreign_keys=ON for every connection.
- Provides a helper to list existing tables.

Schema extensions:
- categories (per-user custom categories)
- notes (notes attached to an expense OR transaction OR contact)
- attachments (files attached to expense/transaction/contact)
- access_logs (security/audit log)
- Strengthened foreign key relationships among users, contacts, expenses, transactions
  with sensible ON DELETE behaviors and indexes.
"""

import sqlite3
from typing import Dict, Any

# Default database path used by DatabaseManager when no path is provided.
DB_PATH = "moneymate.db"

def get_connection(db_path: str):
    """
    Return a new SQLite connection with foreign key support enabled.
    - Supports SQLite URI for shared in-memory DBs (e.g., file:moneymate?mode=memory&cache=shared).
    """
    # If using an SQLite connection URI, enable uri=True for proper handling.
    if isinstance(db_path, str) and db_path.startswith("file:"):
        conn = sqlite3.connect(db_path, uri=True)
    else:
        conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path: str) -> Dict[str, Any]:
    """
    Initialize the database with necessary tables if they don't exist.
    Creates base tables and new extended tables with proper FKs and indexes.
    Also performs light, backward-compatible migrations when needed.
    """
    try:
        conn = get_connection(db_path)
        cur = conn.cursor()

        # Schema versioning (basic)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER NOT NULL
            );
        """)
        cur.execute("SELECT COUNT(*) FROM schema_version;")
        count = cur.fetchone()[0]
        if count == 0:
            # Start at version 1 for initial baseline of this codebase.
            cur.execute("INSERT INTO schema_version (version) VALUES (1);")

        # Core tables (order matters for FKs)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user','admin')),
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)

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

        # Keep existing textual category for backward compatibility
        cur.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                price REAL NOT NULL CHECK (price >= 0),
                date TEXT NOT NULL,
                category TEXT, -- legacy textual category
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_expenses_user_id ON expenses(user_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date);")
        # Composite index useful for GUI filtering by user/date
        cur.execute("CREATE INDEX IF NOT EXISTS idx_expenses_user_date ON expenses(user_id, date);")

        # Transactions between users
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER NOT NULL,
                to_user_id INTEGER NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('credit','debit')),
                amount REAL NOT NULL CHECK (amount >= 0),
                date TEXT NOT NULL,
                description TEXT,
                contact_id INTEGER, -- optional link to a contact
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (from_user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (to_user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE SET NULL
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_transactions_from_user ON transactions(from_user_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_transactions_to_user ON transactions(to_user_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);")
        # Composite indexes for common filtered/ordered views in GUI
        cur.execute("CREATE INDEX IF NOT EXISTS idx_transactions_from_user_date ON transactions(from_user_id, date);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_transactions_to_user_date ON transactions(to_user_id, date);")
        # NOTE: We also enforce sender != receiver at application layer (SQLite cannot ALTER ADD CHECK easily).

        # Extended tables

        # Per-user custom categories
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

        # If expenses.category_id doesn't exist, add it (nullable, keeps legacy text 'category')
        cur.execute("PRAGMA table_info(expenses);")
        expense_cols = {row[1] for row in cur.fetchall()}
        if "category_id" not in expense_cols:
            try:
                cur.execute("ALTER TABLE expenses ADD COLUMN category_id INTEGER;")
            except Exception:
                # In case of older SQLite or edge cases, ignore; app will handle absence gracefully.
                pass

        # Ensure index on expenses.category_id if column is present (post-ALTER or already there)
        cur.execute("PRAGMA table_info(expenses);")
        expense_cols_after = {row[1] for row in cur.fetchall()}
        if "category_id" in expense_cols_after:
            cur.execute("CREATE INDEX IF NOT EXISTS idx_expenses_category_id ON expenses(category_id);")

        # Notes: can belong to exactly one of expense/transaction/contact (at least one not NULL)
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

        # Attachments: file pointers attached to expense/transaction/contact (at least one)
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

        # Access/Security logs
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

        conn.commit()
        return {"success": True, "error": None, "data": "initialized"}
    except Exception as e:
        return {"success": False, "error": str(e), "data": None}
    finally:
        try:
            conn.close()
        except Exception:
            pass

def list_tables(db_path: str) -> Dict[str, Any]:
    """
    Return a list of user-defined tables in the database.
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
        tables = [r[0] for r in rows]
        return {"success": True, "error": None, "data": tables}
    except Exception as e:
        return {"success": False, "error": str(e), "data": []}
    finally:
        try:
            conn.close()
        except Exception:
            pass

def get_schema_version(db_path: str) -> Dict[str, Any]:
    """
    Return the current schema version (integer) if available.
    """
    try:
        conn = get_connection(db_path)
        cur = conn.cursor()
        cur.execute("SELECT version FROM schema_version LIMIT 1;")
        row = cur.fetchone()
        version = row[0] if row else None
        return {"success": True, "error": None, "data": version}
    except Exception as e:
        return {"success": False, "error": str(e), "data": None}
    finally:
        try:
            conn.close()
        except Exception:
            pass