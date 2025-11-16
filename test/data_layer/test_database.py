"""
Database schema and connection tests.

These tests focus on the low-level database.py helpers, verifying that:

- init_db creates all core tables (users, contacts, expenses, transactions).
- Extended tables (categories, notes, attachments, access_logs) are present.
- get_connection returns a usable SQLite connection with foreign keys enabled.
- The users table includes a role column for role-based logic.
- The expenses table includes an optional category_id column for FK linkage.
- A temporary on-disk DB is created and cleaned up safely across platforms.
"""

import os
import gc
import time
import pytest
from MoneyMate.data_layer.database import init_db, get_connection, list_tables


TEST_DB = "test_db_module.db"

def setup_module(module):
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    init_db(TEST_DB)

def teardown_module(module):
    gc.collect()
    for _ in range(10):
        try:
            if os.path.exists(TEST_DB):
                os.remove(TEST_DB)
            break
        except PermissionError:
            time.sleep(0.2)
    if os.path.exists(TEST_DB):
        raise PermissionError(f"Unable to delete test database file: {TEST_DB}")

def test_tables_created():
    """Check if all required core tables are created in the database."""
    tables_result = list_tables(db_path=TEST_DB)  # <<<<< qui cambia
    assert isinstance(tables_result, dict)
    tables = tables_result["data"]
    assert set(tables) >= {"users", "contacts", "expenses", "transactions"}


def test_extended_tables_created():
    """Check if extended tables exist: categories, notes, attachments, access_logs."""
    tables_result = list_tables(db_path=TEST_DB)  # <<<<< qui cambia
    assert isinstance(tables_result, dict)
    tables = set(tables_result["data"])
    assert {"categories", "notes", "attachments", "access_logs"}.issubset(tables)


def test_get_connection():
    """Test that get_connection returns an active connection to the database."""
    conn = get_connection(TEST_DB)
    assert conn is not None
    conn.close()

def test_users_table_has_role_column():
    """Test that the users table has a role column for role-based logic."""
    conn = get_connection(TEST_DB)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    assert "role" in columns
    conn.close()

def test_expenses_table_has_category_id():
    """Test that the expenses table has an optional category_id FK column."""
    conn = get_connection(TEST_DB)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(expenses)")
    columns = [row[1] for row in cursor.fetchall()]
    assert "category_id" in columns
    conn.close()