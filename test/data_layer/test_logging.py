import os
import gc
import time
import pytest

from MoneyMate.data_layer.manager import DatabaseManager
from MoneyMate.data_layer.api import (
    api_add_expense, api_add_contact, api_add_transaction,
    api_delete_expense, api_delete_contact, api_delete_transaction,
    api_search_expenses, api_get_user_balance,
    set_db_path, api_clear_expenses, api_register_user, api_login_user
)

TEST_DB = "test_logging.db"

def setup_module(module):
    """
    Module setup: ensure a clean test database is created for logging tests.
    """
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    DatabaseManager(TEST_DB)
    set_db_path(TEST_DB)

def teardown_module(module):
    """
    Module teardown: release API DB reference and clean up the test database file.
    Adds a retry loop to avoid Windows file locks.
    """
    set_db_path(None)
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

@pytest.fixture
def db():
    """
    Fixture for direct manager-based logging tests.
    Ensures a fresh DatabaseManager instance using TEST_DB.
    """
    dbm = DatabaseManager(TEST_DB)
    user_res = dbm.users.register_user("loguser", "pw")
    if not user_res["success"]:
        # If already exists, login instead
        login_res = dbm.users.login_user("loguser", "pw")
        assert login_res["success"]
        user_id = login_res["data"]["user_id"]
    else:
        user_id = user_res["data"]["user_id"]
    dbm._test_user_id = user_id
    yield dbm
    if hasattr(dbm, "close"):
        dbm.close()
    gc.collect()

def test_expense_logging(caplog, db):
    """
    Test logging for expense operations: add, invalid add, delete, clear.
    Verifies correct log level and message for each case.
    """
    with caplog.at_level("INFO"):
        result = db.expenses.add_expense("LogTestExpense", 23.0, "2025-08-19", "Transport", db._test_user_id)
        assert "Expense 'LogTestExpense' added for user" in caplog.text
        assert result["success"]

    with caplog.at_level("WARNING"):
        bad = db.expenses.add_expense("", 23.0, "2025-08-19", "Transport", db._test_user_id)
        assert "Validation failed for expense" in caplog.text
        assert not bad["success"]

    with caplog.at_level("INFO"):
        result_del = db.expenses.delete_expense(9999, db._test_user_id)
        assert "Error deleting expense" in caplog.text or "Deleted expense" in caplog.text

    with caplog.at_level("INFO"):
        result_clear = db.expenses.clear_expenses(db._test_user_id)
        assert "Cleared all expenses for user" in caplog.text
        assert result_clear["success"]

def test_contacts_logging(caplog, db):
    """
    Test logging for contact operations: add, invalid add, delete.
    Verifies correct log level and message for each case.
    """
    with caplog.at_level("INFO"):
        res = db.contacts.add_contact("LogContact", db._test_user_id)
        assert "Contact 'LogContact' added successfully for user" in caplog.text
        assert res["success"]

    with caplog.at_level("WARNING"):
        bad = db.contacts.add_contact("", db._test_user_id)
        assert "Validation failed for contact" in caplog.text
        assert not bad["success"]

    with caplog.at_level("INFO"):
        res_del = db.contacts.delete_contact(9999, db._test_user_id)
        assert "Error deleting contact" in caplog.text or "Deleted contact" in caplog.text

def test_transactions_logging(caplog, db):
    """
    Test logging for transaction operations: add, invalid type, delete, balance.
    Verifies correct log level and message for each case.
    """
    # We need two users for transactions
    sender_id = db._test_user_id
    receiver_res = db.users.register_user("logreceiver", "pw")
    if not receiver_res["success"]:
        receiver_res = db.users.login_user("logreceiver", "pw")
    receiver_id = receiver_res["data"]["user_id"]

    with caplog.at_level("INFO"):
        res = db.transactions.add_transaction(sender_id, receiver_id, "debit", 10.0, "2025-08-19", "Log")
        assert "Transaction from user" in caplog.text
        assert res["success"]

    with caplog.at_level("WARNING"):
        bad = db.transactions.add_transaction(sender_id, receiver_id, "wrongtype", 10.0, "2025-08-19", "Log")
        assert "Validation failed for transaction" in caplog.text
        assert not bad["success"]

    with caplog.at_level("INFO"):
        res_del = db.transactions.delete_transaction(9999, sender_id)
        assert "Error deleting transaction" in caplog.text or "Deleted transaction" in caplog.text

    with caplog.at_level("INFO"):
        bal = db.transactions.get_user_balance(sender_id)
        assert "Calculated balance for user ID" in caplog.text
        assert bal["success"]

def test_api_logging(caplog):
    """
    API-level logging checks using set_db_path and API functions.
    Verifies that each API call produces the expected log message.
    """
    set_db_path(TEST_DB)
    user_res = api_register_user("apiloguser", "pw")
    if not user_res["success"]:
        user_res = api_login_user("apiloguser", "pw")
    user_id = user_res["data"]["user_id"]
    with caplog.at_level("INFO"):
        api_add_contact("APILogContact", user_id)
        assert "API call: api_add_contact" in caplog.text

        api_add_expense("APILogExpense", 33.0, "2025-08-19", "Food", user_id)
        assert "API call: api_add_expense" in caplog.text

        api_add_transaction(user_id, user_id, "credit", 50, "2025-08-19", "API")
        assert "API call: api_add_transaction" in caplog.text

        api_search_expenses("Food", user_id)
        assert "API call: api_search_expenses" in caplog.text

        api_get_user_balance(user_id)
        assert "API call: api_get_user_balance" in caplog.text

        api_delete_expense(9999, user_id)
        assert "API call: api_delete_expense" in caplog.text

        api_delete_contact(9999, user_id)
        assert "API call: api_delete_contact" in caplog.text

        api_delete_transaction(9999, user_id)
        assert "API call: api_delete_transaction" in caplog.text

        api_clear_expenses(user_id)
        assert "API call: api_clear_expenses" in caplog.text

    set_db_path(None)