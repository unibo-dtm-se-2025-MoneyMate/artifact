"""
End-to-end tests for the high-level MoneyMate data layer API.

This module verifies that the api.py facade correctly wires into the
DatabaseManager and underlying managers by covering:

- Expenses: add/get, validation, categories (category_id), partial updates.
- Contacts: add/get, per-user isolation, contact-balance aggregation.
- Transactions: add/get, sent vs received filters, admin visibility vs
  non-admin isolation, partial updates (sender-only), contact binding.
- Users: registration, login, role/permissions (admin password policy).
- Balance analytics: legacy balance, NET balance, and breakdown semantics.
- API contract: every public function returns {success, error, data}.
- Database health: schema version via api_health and clean test DB setup.
"""

import os
import gc
import time
import pytest
from MoneyMate.data_layer.api import (
    api_list_tables, api_add_expense, api_get_expenses,
    api_add_contact, api_get_contacts, api_add_transaction,
    api_get_transactions, api_get_user_balance,
    set_db_path, api_register_user, api_login_user,
    api_get_user_net_balance, api_get_user_balance_breakdown, api_health,
    # New APIs under test
    api_update_expense, api_update_transaction, api_get_contact_balance,
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

# --- Existing tests (UNCHANGED in intent; updated calls to new API signature) ---

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

    # Add transactions using new signature (keywords)
    api_add_transaction(from_user_id=from_id, to_user_id=to_id, type_="credit", amount=50, date="2025-08-19", description="Loan")
    api_add_transaction(from_user_id=from_id, to_user_id=to_id, type_="debit", amount=20, date="2025-08-19", description="Repayment")
    saldo_sender = api_get_user_balance(from_id)
    saldo_receiver = api_get_user_balance(to_id)
    assert isinstance(saldo_sender, dict) and saldo_sender["success"]
    assert isinstance(saldo_receiver, dict) and saldo_receiver["success"]
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
        lambda: api_add_transaction(from_user_id=user_id, to_user_id=user_id, type_="credit", amount=5, date="2025-08-19", description="Salary"),
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

def test_api_admin_registration_and_transactions():
    """
    Admin registration (password must be '12345') and ability to view all transactions of all users.
    """
    admin_id = _get_admin_user("admin_api")
    # Create two distinct normal users for admin visibility test
    u1 = _ensure_user("apiu1", "pw", role="user")
    u2 = _ensure_user("apiu2", "pw", role="user")

    # Add transactions in both directions
    api_add_transaction(from_user_id=u1, to_user_id=u2, type_="credit", amount=50, date="2025-08-19", description="Loan")
    api_add_transaction(from_user_id=u2, to_user_id=u1, type_="debit", amount=20, date="2025-08-19", description="Repayment")

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

def test_api_net_balance_and_breakdown():
    """
    Verify NET balance semantics and detailed breakdown:
    - net = credits_received - debits_sent
    - legacy remains (credits_received + credits_sent) - (debits_sent + debits_received)
    Scenario:
      u1 -> u2: credit 50
      u1 -> u2: debit 20
    Expected:
      u1: net = 0 - 20 = -20, legacy = (0+50)-(20+0)=30
      u2: net = 50 - 0 = 50, legacy = (50+0)-(0+20)=30
    """
    u1 = _ensure_user("net_user1", "pw")
    u2 = _ensure_user("net_user2", "pw")

    # Create transactions
    api_add_transaction(from_user_id=u1, to_user_id=u2, type_="credit", amount=50, date="2025-08-19", description="Loan")
    api_add_transaction(from_user_id=u1, to_user_id=u2, type_="debit", amount=20, date="2025-08-19", description="Repayment")

    # NET balances
    net_u1 = api_get_user_net_balance(u1)
    net_u2 = api_get_user_net_balance(u2)
    assert net_u1["success"] and net_u2["success"]
    assert net_u1["data"] == -20
    assert net_u2["data"] == 50

    # Breakdown checks
    br_u1 = api_get_user_balance_breakdown(u1)
    br_u2 = api_get_user_balance_breakdown(u2)
    assert br_u1["success"] and br_u2["success"]

    b1 = br_u1["data"]
    b2 = br_u2["data"]

    assert b1["credits_received"] == 0
    assert b1["debits_sent"] == 20
    assert b1["credits_sent"] == 50
    assert b1["debits_received"] == 0
    assert b1["net"] == -20
    assert b1["legacy"] == 30

    assert b2["credits_received"] == 50
    assert b2["debits_sent"] == 0
    assert b2["credits_sent"] == 0
    assert b2["debits_received"] == 20
    assert b2["net"] == 50
    assert b2["legacy"] == 30

def test_api_get_transactions_received():
    """
    Verify that api_get_transactions(as_sender=False) returns only transactions received by the user.
    """
    u1 = _ensure_user("trx_recv_u1", "pw")
    u2 = _ensure_user("trx_recv_u2", "pw")

    # Two directions
    api_add_transaction(from_user_id=u1, to_user_id=u2, type_="credit", amount=10, date="2025-08-19", description="U1->U2")
    api_add_transaction(from_user_id=u2, to_user_id=u1, type_="debit", amount=5, date="2025-08-19", description="U2->U1")

    received = api_get_transactions(u1, as_sender=False)
    assert received["success"]
    assert len(received["data"]) >= 1
    assert all(t["to_user_id"] == u1 for t in received["data"])
    assert all(t["description"] != "U1->U2" for t in received["data"])

def test_api_non_admin_cannot_use_is_admin_flag():
    """
    A normal user passing is_admin=True must be rejected explicitly with an error.
    This prevents privilege escalation via flags.
    """
    u1 = _ensure_user("flag_user1", "pw")
    u2 = _ensure_user("flag_user2", "pw")

    # Create transactions in both directions
    api_add_transaction(from_user_id=u1, to_user_id=u2, type_="credit", amount=15, date="2025-08-19", description="u1->u2")
    api_add_transaction(from_user_id=u2, to_user_id=u1, type_="debit", amount=7, date="2025-08-19", description="u2->u1")

    res = api_get_transactions(u1, is_admin=True)
    assert isinstance(res, dict)
    assert not res["success"]
    assert "admin" in (res["error"] or "").lower()

def test_api_health_returns_schema_version():
    """
    Verify that api_health returns the current schema_version as an integer.
    """
    res = api_health()
    assert isinstance(res, dict)
    assert res["success"]
    assert isinstance(res["data"], int)

def test_api_update_expense_partial():
    """
    Verify api_update_expense supports partial updates and changes are reflected in listings.
    """
    uid = _ensure_user("upd_exp_user_api", "pw")

    # Create expense
    assert api_add_expense("E1", 10, "2025-08-19", "Food", uid)["success"]
    # Fetch its id
    e = next(e for e in api_get_expenses(uid)["data"] if e["title"] == "E1")
    eid = e["id"]

    # Update price and title
    up = api_update_expense(eid, uid, title="E1-upd", price=12.5)
    assert isinstance(up, dict) and up["success"]
    assert "updated" in up["data"]

    # Verify changes
    items = api_get_expenses(uid)["data"]
    m = next(x for x in items if x["id"] == eid)
    assert m["title"] == "E1-upd"
    assert float(m["price"]) == 12.5

def test_api_update_transaction_and_sender_only():
    """
    Verify api_update_transaction allows partial updates for the sender,
    and that a receiver attempting to update gets updated=0 (no-op).
    """
    sender = _ensure_user("upd_trx_sender_api", "pw")
    receiver = _ensure_user("upd_trx_receiver_api", "pw")

    # Create a transaction
    assert api_add_transaction(from_user_id=sender, to_user_id=receiver, type_="credit", amount=30, date="2025-08-19", description="init")["success"]
    tr = api_get_transactions(sender)["data"][0]
    tid = tr["id"]

    # Sender updates amount and description
    up_sender = api_update_transaction(tid, sender, amount=45, description="updated")
    assert up_sender["success"]
    assert up_sender["data"]["updated"] in (0, 1)  # updated likely 1

    # Verify update via listing
    cur = api_get_transactions(sender)["data"][0]
    assert float(cur["amount"]) == 45
    assert cur["description"] == "updated"

    # Receiver attempts to update -> should be a no-op (updated=0)
    up_receiver = api_update_transaction(tid, receiver, description="receiver-update-ignored")
    assert isinstance(up_receiver, dict) and up_receiver["success"]
    assert up_receiver["data"]["updated"] == 0

def test_api_contact_balance_sender_perspective():
    """
    Verify api_get_contact_balance computes credits_sent, debits_sent, net for a specific contact from the sender's perspective.
    """
    sender = _ensure_user("contact_bal_sender", "pw")
    receiver = _ensure_user("contact_bal_receiver", "pw")

    # Create a contact for sender and get its id
    assert api_add_contact("CarloAPI", sender)["success"]
    contacts = api_get_contacts(sender)
    assert contacts["success"] and contacts["data"]
    contact_id = next(c["id"] for c in contacts["data"] if c["name"] == "CarloAPI")

    # Add transactions tied to that contact (sender -> receiver)
    assert api_add_transaction(from_user_id=sender, to_user_id=receiver, type_="credit", amount=30, date="2025-08-19", description="loan", contact_id=contact_id)["success"]
    assert api_add_transaction(from_user_id=sender, to_user_id=receiver, type_="debit", amount=10, date="2025-08-19", description="repay", contact_id=contact_id)["success"]

    bal = api_get_contact_balance(sender, contact_id)
    assert isinstance(bal, dict) and bal["success"]
    data = bal["data"]
    assert data["credits_sent"] == 30
    assert data["debits_sent"] == 10
    assert data["net"] == 20