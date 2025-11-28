import os
import sqlite3
from pathlib import Path

from MoneyMate.data_layer.schema_utils import (
    ensure_auth_schema,
    _table_exists,
    _table_columns,
)


TEST_DB = "test_schema_utils.db"


def setup_module(module):
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def teardown_module(module):
    try:
        os.remove(TEST_DB)
    except FileNotFoundError:
        pass


def _new_conn():
    # Simple helper to create a connection with Row factory
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row
    return conn


def test_ensure_auth_schema_creates_minimal_structures():
    """
    ensure_auth_schema must create the minimal auth-related schema on an empty DB:
    - users with required columns
    - sessions
    - access_logs
    - schema_version with at least one row.
    """
    conn = _new_conn()
    try:
        ensure_auth_schema(conn)
        conn.commit()

        # users table exists and has the expected columns
        assert _table_exists(conn, "users")
        user_cols = _table_columns(conn, "users")
        for col in ("id", "username", "password_hash", "role", "is_active", "created_at"):
            assert col in user_cols

        # sessions and access_logs tables exist
        assert _table_exists(conn, "sessions")
        assert _table_exists(conn, "access_logs")

        # schema_version table exists and has at least one row
        assert _table_exists(conn, "schema_version")
        cur = conn.execute("SELECT COUNT(*) FROM schema_version")
        count = cur.fetchone()[0]
        assert count >= 1
    finally:
        conn.close()


def test_ensure_auth_schema_is_idempotent():
    """
    Calling ensure_auth_schema multiple times must be safe and non-destructive.
    The set of core tables should remain stable.
    """
    conn = _new_conn()
    try:
        # First run
        ensure_auth_schema(conn)
        conn.commit()

        # Capture a snapshot of tables and columns
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables_before = [r[0] for r in cur.fetchall()]
        cols_before = {t: _table_columns(conn, t) for t in tables_before}

        # Second run
        ensure_auth_schema(conn)
        conn.commit()

        # Compare after second run
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables_after = [r[0] for r in cur.fetchall()]
        cols_after = {t: _table_columns(conn, t) for t in tables_after}

        assert tables_before == tables_after
        assert cols_before == cols_after
    finally:
        conn.close()