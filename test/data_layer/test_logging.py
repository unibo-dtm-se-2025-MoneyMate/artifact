import os
import gc
import pytest

from MoneyMate.data_layer.manager import DatabaseManager
from MoneyMate.data_layer.api import (
    api_add_expense, api_add_contact, api_add_transaction,
    api_delete_expense, api_delete_contact, api_delete_transaction,
    api_search_expenses, api_get_contact_balance,
    set_db_path, api_clear_expenses
)

TEST_DB = "test_logging.db"

def setup_module(module):
    """
    Module setup: ensure a clean test database is created for logging tests.
    """
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    # Initialize DB schema via manager to ensure all tables exist
    DatabaseManager(TEST_DB)
    set_db_path(TEST_DB)

def teardown_module(module):
    """
    Module teardown: release API DB reference and clean up the test database file.
    """
    set_db_path(None)
    gc.collect()
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

@pytest.fixture
def db():
    """
    Fixture for direct manager-based logging tests.
    Ensures a fresh DatabaseManager instance using TEST_DB.
    """
    dbm = DatabaseManager(TEST_DB)
    yield dbm
    if hasattr(dbm, "close"):
        dbm.close()
    gc.collect()

def test_expense_logging(caplog, db):
    """
    Test logging for expense operations: add, invalid add, delete, clear.
    Verifies correct log level and message for each case.
    """
    # INFO log for successful expense add
    with caplog.at_level("INFO"):
        result = db.expenses.add_expense("LogTestExpense", 23.0, "2025-08-19", "Transport")
        assert "Expense 'LogTestExpense' added successfully." in caplog.text
        assert result["success"]

    # WARNING log for invalid expense add
    with caplog.at_level("WARNING"):
        bad = db.expenses.add_expense("", 23.0, "2025-08-19", "Transport")
        assert "Validation failed for expense" in caplog.text
        assert not bad["success"]

    # INFO log for expense delete (error or success)
    with caplog.at_level("INFO"):
        result_del = db.expenses.delete_expense(9999)  # Should not exist
        assert "Error deleting expense" in caplog.text or "Deleted expense" in caplog.text

    # INFO log for clearing expenses
    with caplog.at_level("INFO"):
        result_clear = db.expenses.clear_expenses()
        assert "Cleared all expenses from the database." in caplog.text
        assert result_clear["success"]

def test_contacts_logging(caplog, db):
    """
    Test logging for contact operations: add, invalid add, delete.
    Verifies correct log level and message for each case.
    """
    # INFO log for successful contact add
    with caplog.at_level("INFO"):
        res = db.contacts.add_contact("LogContact")
        assert "Contact 'LogContact' added successfully." in caplog.text
        assert res["success"]

    # WARNING log for invalid contact add
    with caplog.at_level("WARNING"):
        bad = db.contacts.add_contact("")
        assert "Validation failed for contact" in caplog.text
        assert not bad["success"]

    # INFO log for contact delete (error or success)
    with caplog.at_level("INFO"):
        res_del = db.contacts.delete_contact(9999)
        assert "Error deleting contact" in caplog.text or "Deleted contact" in caplog.text

def test_transactions_logging(caplog, db):
    """
    Test logging for transaction operations: add, invalid type, delete, balance.
    Verifies correct log level and message for each case.
    """
    db.contacts.add_contact("TransLogger")
    contact_id = db.contacts.get_contacts()["data"][0]["id"]

    # INFO log for successful transaction add
    with caplog.at_level("INFO"):
        res = db.transactions.add_transaction(contact_id, "debit", 10.0, "2025-08-19", "Log")
        assert "Transaction for contact_id" in caplog.text
        assert res["success"]

    # WARNING log for invalid transaction type
    with caplog.at_level("WARNING"):
        bad = db.transactions.add_transaction(contact_id, "wrongtype", 10.0, "2025-08-19", "Log")
        assert "Validation failed for transaction" in caplog.text
        assert not bad["success"]

    # INFO log for transaction delete (error or success)
    with caplog.at_level("INFO"):
        res_del = db.transactions.delete_transaction(9999)
        assert "Error deleting transaction" in caplog.text or "Deleted transaction" in caplog.text

    # INFO log for balance calculation
    with caplog.at_level("INFO"):
        bal = db.transactions.get_contact_balance(contact_id)
        assert "Calculated balance for contact ID" in caplog.text
        assert bal["success"]

def test_api_logging(caplog):
    """
    API-level logging checks using set_db_path and API functions.
    Verifies that each API call produces the expected log message.
    """
    set_db_path(TEST_DB)
    # INFO logs for API calls
    with caplog.at_level("INFO"):
        api_add_contact("APILogContact")
        assert "API call: api_add_contact" in caplog.text

        api_add_expense("APILogExpense", 33.0, "2025-08-19", "Food")
        assert "API call: api_add_expense" in caplog.text

        api_add_transaction(1, "credit", 50, "2025-08-19", "API")
        assert "API call: api_add_transaction" in caplog.text

        api_search_expenses("Food")
        assert "API call: api_search_expenses" in caplog.text

        api_get_contact_balance(1)
        assert "API call: api_get_contact_balance" in caplog.text

        api_delete_expense(9999)
        assert "API call: api_delete_expense" in caplog.text

        api_delete_contact(9999)
        assert "API call: api_delete_contact" in caplog.text

        api_delete_transaction(9999)
        assert "API call: api_delete_transaction" in caplog.text

        api_clear_expenses()
        assert "API call: api_clear_expenses" in caplog.text

    set_db_path(None)