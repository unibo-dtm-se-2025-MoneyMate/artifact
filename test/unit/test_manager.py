import os
import gc
import pytest
from MoneyMate.data_layer.manager import DatabaseManager

TEST_DB = "test_manager.db"

def setup_module(module):
    """
    Set up a clean test database before running tests.
    This ensures no previous test artifacts affect test results.
    """
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    # Initialize DB schema to ensure all tables exist before tests run
    DatabaseManager(TEST_DB)

def teardown_module(module):
    """
    Remove the test database after all tests have run.
    Ensures proper cleanup and releases all file handles.
    """
    gc.collect()  # Force garbage collection to close any lingering SQLite handles
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

@pytest.fixture
def dbm():
    """
    Yields a fresh DatabaseManager instance for each test.
    Ensures isolation and proper resource management.
    """
    dbm = DatabaseManager(TEST_DB)
    yield dbm
    if hasattr(dbm, "close"):
        dbm.close()
    gc.collect()

def test_database_manager_list_tables(dbm):
    """
    Test that the DatabaseManager can list all tables in the database.
    Verifies that the three main tables exist.
    """
    tables = dbm.list_tables()["data"]
    assert set(tables) >= {"contacts", "expenses", "transactions"}