"""
Helper utilities for ensuring and migrating authentication-related schema.

This module focuses on aligning an existing SQLite database with the minimal
schema required by the authentication stack and tests:

- Ensures the presence and shape of the users table (required columns).
- Ensures sessions and access_logs tables, plus supporting indexes.
- Optionally applies an external SQL script (sql/auth_schema.sql) if present.
- Maintains a basic schema_version row for health checks.

It is intentionally tolerant and non-destructive, designed for incremental
migration of older or partially initialized databases.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, Set


REQUIRED_USER_COLUMNS = {
    "id",
    "username",
    "password_hash",
    "role",
    "is_active",
    "created_at",
}


def _project_root() -> Path:
    # Questo file è in MoneyMate/data_layer/schema_utils.py
    # repo_root = .../artifact
    return Path(__file__).resolve().parents[2]


def _auth_sql_path() -> Path:
    return _project_root() / "sql" / "auth_schema.sql"


def _exec_script(conn: sqlite3.Connection, sql_text: str) -> None:
    conn.executescript(sql_text)


def _table_columns(conn: sqlite3.Connection, table: str) -> Set[str]:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cur.fetchall()}  # name at index 1


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1", (table,)
    )
    return cur.fetchone() is not None


def _ensure_schema_version(conn: sqlite3.Connection) -> None:
    conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
    cur = conn.execute("SELECT COUNT(*) FROM schema_version")
    if cur.fetchone()[0] == 0:
        conn.execute("INSERT INTO schema_version(version) VALUES (1)")


def _ensure_access_logs(conn: sqlite3.Connection) -> None:
    _exec_script(
        conn,
        """
        CREATE TABLE IF NOT EXISTS access_logs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER,
          action TEXT NOT NULL CHECK (action IN ('login','logout','failed_login','password_change','password_reset')),
          ip_address TEXT,
          user_agent TEXT,
          created_at TEXT NOT NULL DEFAULT (datetime('now')),
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS idx_access_logs_user_id ON access_logs(user_id);
        CREATE INDEX IF NOT EXISTS idx_access_logs_action ON access_logs(action);
        """,
    )


def _apply_sql_file_if_present(conn: sqlite3.Connection) -> None:
    path = _auth_sql_path()
    if path.exists():
        sql_text = path.read_text(encoding="utf-8")
        _exec_script(conn, sql_text)


def _migrate_users_table(conn: sqlite3.Connection) -> None:
    if not _table_exists(conn, "users"):
        # Se non esiste affatto, creiamola con lo schema completo minimo richiesto
        _exec_script(
            conn,
            """
            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT NOT NULL UNIQUE,
              password_hash TEXT NOT NULL,
              role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user','admin')),
              is_active INTEGER NOT NULL DEFAULT 1,
              created_at TEXT NOT NULL DEFAULT (datetime('now')),
              updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            """,
        )
        return

    cols = _table_columns(conn, "users")

    if "password_hash" not in cols:
        # Aggiungiamo la colonna con default vuoto per soddisfare NOT NULL
        conn.execute(
            "ALTER TABLE users ADD COLUMN password_hash TEXT NOT NULL DEFAULT ''"
        )

    if "role" not in cols:
        conn.execute(
            "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'"
        )
        # Non possiamo aggiungere facilmente il CHECK via ALTER in SQLite: non è necessario per i test.

    if "is_active" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")

    if "created_at" not in cols:
        conn.execute(
            "ALTER TABLE users ADD COLUMN created_at TEXT NOT NULL DEFAULT (datetime('now'))"
        )

    # updated_at facoltativo per i test; se manca, lo aggiungiamo come NULLable
    if "updated_at" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN updated_at TEXT")


def _ensure_sessions_table(conn: sqlite3.Connection) -> None:
    _exec_script(
        conn,
        """
        CREATE TABLE IF NOT EXISTS sessions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          session_token TEXT NOT NULL UNIQUE,
          created_at TEXT NOT NULL DEFAULT (datetime('now')),
          expires_at TEXT,
          is_active INTEGER NOT NULL DEFAULT 1,
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token);
        """,
    )


def ensure_auth_schema(conn: sqlite3.Connection) -> None:
    """
    Garantisce che il DB disponga dello schema minimo richiesto dai test:
    - users (con password_hash, role, ecc.)
    - sessions
    - access_logs
    - schema_version con almeno una riga
    Tollerante: usa il file sql/auth_schema.sql se presente, poi migra eventuali colonne mancanti.
    """
    # 1) Prova ad applicare lo script SQL del repo se presente (idempotente grazie a IF NOT EXISTS)
    _apply_sql_file_if_present(conn)

    # 2) Migra/garantisce 'users' e colonne minime
    _migrate_users_table(conn)

    # 3) Assicura tabelle collegate
    _ensure_sessions_table(conn)
    _ensure_access_logs(conn)

    # 4) Versione schema per health-check
    _ensure_schema_version(conn)