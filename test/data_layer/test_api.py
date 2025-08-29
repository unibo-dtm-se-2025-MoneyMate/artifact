import os
import gc
import pytest
from MoneyMate.data_layer.api import (
    api_list_tables, api_add_expense, api_get_expenses,
    api_add_contact, api_get_contacts, api_add_transaction,
    api_get_transactions, api_get_user_balance,
    set_db_path, api_register_user, api_login_user
)
from MoneyMate.data_layer.manager import DatabaseManager
from MoneyMate.data_layer.database import get_connection

TEST_DB = "test_api.db"

def setup_module(module):
    """
    Set up and initialize a clean test database before running tests.
    Ensures a known state and schema for all API tests.
    """
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    DatabaseManager(TEST_DB)
    set_db_path(TEST_DB)

def teardown_module(module):
    """
    Remove the test database after all tests have run.
    Releases API global DB reference and ensures proper file cleanup.
    """
    set_db_path(None)
    gc.collect()
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def _get_test_user():
    # Ensure a test user exists and return user_id
    res = api_register_user("apitestuser", "pw")
    if not res["success"] and "already exists" in str(res["error"]).lower():
        res = api_login_user("apitestuser", "pw")
    assert res["success"]
    return res["data"]["user_id"]

# --- Helpers added to cover new admin/role features without touching existing tests ---

def _ensure_user(username, password, role="user"):
    """
    Ensure a user (optionally with role) exists; if already present, login.
    Returns user_id.
    """
    res = api_register_user(username, password, role=role)
    if not res["success"] and "already exists" in str(res["error"]).lower():
        res = api_login_user(username, password)
    assert res["success"]
    return res["data"]["user_id"]

def _get_admin_user(username="adminuser"):
    """
    Ensure an admin user exists with the enforced password '12345'.
    Returns admin user_id.
    """
    return _ensure_user(username, "12345", role="admin")

# --- Existing tests (UNCHANGED) ---

def test_api_add_and_get_expense():
    """
    Add a new expense using the API and verify it can be retrieved.
    Checks that the expense API correctly adds and lists expenses for the user.
    """
    user_id = _get_test_user()
    res = api_add_expense("Test", 5, "2025-08-19", "Food", user_id)
    assert isinstance(res, dict)
    assert res["success"]
    res_get = api_get_expenses(user_id)
    assert isinstance(res_get, dict)
    assert any(e["title"] == "Test" for e in res_get["data"])

def test_api_add_and_get_contact():
    """
    Add a new contact using the API and verify it can be retrieved.
    Checks that the contact API correctly adds and lists contacts for the user.
    """
    user_id = _get_test_user()
    res = api_add_contact("Mario", user_id)
    assert isinstance(res, dict)
    assert res["success"]
    res_get = api_get_contacts(user_id)
    assert isinstance(res_get, dict)
    assert any(c["name"] == "Mario" for c in res_get["data"])

def test_api_add_transaction_and_balance():
    """
    Add two users, create a transaction from one to the other, and verify the balances.
    Tests the transaction API and balance calculation logic.
    """
    from_id = _get_test_user()
    res2 = api_register_user("apitestuser2", "pw")
    if not res2["success"]:
        res2 = api_login_user("apitestuser2", "pw")
    to_id = res2["data"]["user_id"]

    # Add transaction from from_id to to_id
    api_add_transaction(from_id, to_id, "credit", 50, "2025-08-19", "Loan")
    api_add_transaction(from_id, to_id, "debit", 20, "2025-08-19", "Repayment")
    saldo_sender = api_get_user_balance(from_id)
    saldo_receiver = api_get_user_balance(to_id)
    assert isinstance(saldo_sender, dict) and saldo_sender["success"]
    assert isinstance(saldo_receiver, dict) and saldo_receiver["success"]
    # Both users now have +50 credit and +20 debit in their global balance logic!
    # The function sums by user_id in either sender or receiver
    # So both will have (credit=50, debit=20) => saldo=30
    assert saldo_sender["data"] == 30
    assert saldo_receiver["data"] == 30

def test_api_response_format():
    """
    Test that all main API functions return a dictionary with 'success', 'error', and 'data' keys.
    Ensures API contract is always respected.
    """
    user_id = _get_test_user()
    funcs = [
        lambda: api_add_expense("Contract", 1, "2025-08-19", "Food", user_id),
        lambda: api_get_expenses(user_id),
        lambda: api_add_contact("TestFormat", user_id),
        lambda: api_get_contacts(user_id),
        lambda: api_add_transaction(user_id, user_id, "credit", 5, "2025-08-19", "Salary"),
        lambda: api_get_user_balance(user_id),
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
    user_id = _get_test_user()
    res = api_add_expense("", 5, "2025-08-19", "Food", user_id)
    assert isinstance(res, dict)
    assert not res["success"]
    assert "title" in str(res["error"]).lower()

# --- New tests added for admin/role features (do not replace existing ones) ---

def test_api_admin_registration_and_transactions():
    """
    Admin registration (password must be '12345') and ability to view all transactions of all users.
    """
    admin_id = _get_admin_user("admin_api")
    # Create two distinct normal users for admin visibility test
    u1 = _ensure_user("apiu1", "pw", role="user")
    u2 = _ensure_user("apiu2", "pw", role="user")

    # Add transactions in both directions
    api_add_transaction(u1, u2, "credit", 50, "2025-08-19", "Loan")
    api_add_transaction(u2, u1, "debit", 20, "2025-08-19", "Repayment")

    # Admin gets all transactions
    tr_all = api_get_transactions(admin_id, is_admin=True)
    assert isinstance(tr_all, dict) and tr_all["success"]
    assert len(tr_all["data"]) >= 2
    senders = {t["from_user_id"] for t in tr_all["data"]}
    assert u1 in senders and u2 in senders

    # Normal user gets only own sent transactions by default (as_sender=True)
    tr_user = api_get_transactions(u1)
    assert tr_user["success"]
    assert all(t["from_user_id"] == u1 for t in tr_user["data"])

def test_api_admin_wrong_password():
    """
    Test that admin registration fails with wrong password (must be exactly '12345').
    """
    res = api_register_user("wrongadmin_api", "pw", role="admin")
    assert isinstance(res, dict)
    assert not res["success"]
    assert "admin password" in str(res["error"]).lower()

def test_api_add_expense_with_category_id():
    """
    Add an expense via API with category_id linked to a user-owned category.
    Expects success and category_id present when retrieving expenses.
    """
    user_id = _get_test_user()
    # Create category for this user
    with get_connection(TEST_DB) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO categories (user_id, name) VALUES (?, ?)", (user_id, "APICat"))
        cat_id = cur.lastrowid
        conn.commit()

    res = api_add_expense("APICatExpense", 8.0, "2025-08-19", "Food", user_id, category_id=cat_id)
    assert res["success"]

    res_get = api_get_expenses(user_id)
    assert res_get["success"]
    matches = [e for e in res_get["data"] if e["title"] == "APICatExpense"]
    assert matches, "Expected the API-inserted expense to be present"
    assert "category_id" in matches[0]
    assert matches[0]["category_id"] == cat_id