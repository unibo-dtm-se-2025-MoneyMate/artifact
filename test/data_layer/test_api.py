import os
import gc
import pytest
from MoneyMate.data_layer.api import (
    api_list_tables, api_add_expense, api_get_expenses,
    api_add_contact, api_get_contacts, api_add_transaction,
    api_get_transactions, api_get_contact_balance,
    set_db_path
)
from MoneyMate.data_layer.manager import DatabaseManager

TEST_DB = "test_api.db"

def setup_module(module):
    """
    Set up and initialize a clean test database before running tests.
    Ensures a known state and schema for all API tests.
    """
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    DatabaseManager(TEST_DB)  # Initialize DB schema
    set_db_path(TEST_DB)      # Set the database used by the API

def teardown_module(module):
    """
    Remove the test database after all tests have run.
    Releases API global DB reference and ensures proper file cleanup.
    """
    set_db_path(None)
    gc.collect()
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_api_add_and_get_expense():
    """
    Add a new expense using the API and verify it can be retrieved.
    Checks that the expense API correctly adds and lists expenses.
    """
    res = api_add_expense("Test", 5, "2025-08-19", "Food")
    assert isinstance(res, dict)
    assert res["success"]
    res_get = api_get_expenses()
    assert isinstance(res_get, dict)
    assert any(e["title"] == "Test" for e in res_get["data"])

def test_api_add_and_get_contact():
    """
    Add a new contact using the API and verify it can be retrieved.
    Checks that the contact API correctly adds and lists contacts.
    """
    res = api_add_contact("Mario")
    assert isinstance(res, dict)
    assert res["success"]
    res_get = api_get_contacts()
    assert isinstance(res_get, dict)
    assert any(c["name"] == "Mario" for c in res_get["data"])

def test_api_add_transaction_and_balance():
    """
    Add a contact, assign two transactions (credit and debit), and verify the balance.
    Tests the transaction API and balance calculation logic.
    """
    contact = api_add_contact("Giulia")
    cid = api_get_contacts()["data"][0]["id"]
    api_add_transaction(cid, "credit", 50, "2025-08-19", "Loan")
    api_add_transaction(cid, "debit", 20, "2025-08-19", "Repayment")
    saldo = api_get_contact_balance(cid)
    assert isinstance(saldo, dict)
    assert saldo["success"]
    assert saldo["data"] == 30

def test_api_response_format():
    """
    Test that all main API functions return a dictionary with 'success', 'error', and 'data' keys.
    Ensures API contract is always respected.
    """
    funcs = [
        lambda: api_add_expense("Contract", 1, "2025-08-19", "Food"),
        api_get_expenses,
        lambda: api_add_contact("TestFormat"),
        api_get_contacts,
        lambda: api_add_transaction(1, "credit", 5, "2025-08-19", "Salary"),
        lambda: api_get_contact_balance(1),
        api_list_tables,
    ]
    for func in funcs:
        res = func()
        assert isinstance(res, dict)
        assert "success" in res and "error" in res and "data" in res

def test_api_add_expense_invalid():
    """
    Test that adding an expense with missing title fails and returns an appropriate error.
    """
    res = api_add_expense("", 5, "2025-08-19", "Food")
    assert isinstance(res, dict)
    assert not res["success"]
    assert "title" in str(res["error"]).lower()