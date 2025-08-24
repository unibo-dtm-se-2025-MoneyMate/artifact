import os
import pytest
from MoneyMate.data_layer.database import init_db, get_connection, list_tables

TEST_DB = "test_db_module.db"

def setup_module(module):
    # Set up a clean test database before running tests.
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    init_db(TEST_DB)

def teardown_module(module):
    # Remove the test database after all tests have run.
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_tables_created():
    # Check if all required tables are created in the database.
    tables = list_tables(TEST_DB)["data"]
    # This test ensures that the database schema is correctly initialized.
    assert set(tables) >= {"contacts", "expenses", "transactions"}

def test_get_connection():
    # Test that get_connection returns an active connection to the database.
    conn = get_connection(TEST_DB)
    # This verifies that the database connection utility works and does not raise errors.
    assert conn is not None
    conn.close()