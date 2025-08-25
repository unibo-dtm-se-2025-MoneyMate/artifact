import os
import gc
from MoneyMate.data_layer.api import (
    api_list_tables, api_add_expense, api_get_expenses,
    api_add_contact, api_get_contacts, api_add_transaction,
    api_get_transactions, api_get_contact_balance,
    set_db_path  # new function for the database path
)
from MoneyMate.data_layer.manager import DatabaseManager

TEST_DB = "test_api.db"

def setup_module(module):
    # Set up and initialize a clean test database before running tests.
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    DatabaseManager(TEST_DB)  # Initialize DB schema
    set_db_path(TEST_DB)      # Imposta il database usato dalle API

def teardown_module(module):
    # Remove the test database after all tests have run.
    # Release API global DB reference to ensure file is not locked
    set_db_path(None)
    gc.collect()
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_api_add_and_get_expense():
    # Add a new expense using the API and verify it can be retrieved.
    res = api_add_expense("Test", 5, "2025-08-19", "Food")
    assert res["success"]
    res_get = api_get_expenses()
    # Checks that the expense API correctly adds and lists expenses.
    assert any(e["title"] == "Test" for e in res_get["data"])

def test_api_add_and_get_contact():
    # Add a new contact using the API and verify it can be retrieved.
    res = api_add_contact("Mario")
    assert res["success"]
    res_get = api_get_contacts()
    # Checks that the contact API correctly adds and lists contacts.
    assert any(c["name"] == "Mario" for c in res_get["data"])

def test_api_add_transaction_and_balance():
    # Add a contact, assign two transactions (credit and debit), and verify the balance.
    contact = api_add_contact("Giulia")
    cid = api_get_contacts()["data"][0]["id"]
    api_add_transaction(cid, "credit", 50, "2025-08-19", "Loan")
    api_add_transaction(cid, "debit", 20, "2025-08-19", "Repayment")
    saldo = api_get_contact_balance(cid)
    # This tests the transaction API and balance calculation logic.
    assert saldo["success"]
    assert saldo["data"] == 30