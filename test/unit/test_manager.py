import os
from MoneyMate.data_layer.manager import DatabaseManager

TEST_DB = "test_manager.db"

def setup_module(module):
    # Set up a clean test database before running tests.
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def teardown_module(module):
    # Remove the test database after all tests have run.
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_database_manager_list_tables():
    # Test that the DatabaseManager can list all tables in the database.
    dbm = DatabaseManager(TEST_DB)
    tables = dbm.list_tables()["data"]
    assert set(tables) >= {"contacts", "expenses", "transactions"}  # TO VERIFY THAT THE 3 MAIN TABLES EXIST