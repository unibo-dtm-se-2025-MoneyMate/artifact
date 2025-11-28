"""
Transactions manager tests.

These tests exercise TransactionsManager via DatabaseManager, covering:

- Adding valid transactions between users and listing them.
- Validation of invalid type and non-positive amounts.
- Deletion semantics: sender can delete, receiver deletes result in deleted=0.
- User existence checks for sender ids.
- Admin visibility vs normal user isolation (is_admin flag).
- Explicit rejection when non-admins request is_admin=True.
- Balance analytics: net and breakdown semantics for a simple scenario.
- Per-test DB setup with admin/sender/receiver users and safe cleanup.
"""

import sys
import os
import gc
import time
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from MoneyMate.data_layer.manager import DatabaseManager

TEST_DB = "test_transactions.db"

@pytest.fixture
def db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    dbm = DatabaseManager(TEST_DB)
    # Add admin and two users for transaction tests
    admin_res = dbm.users.register_user("admin", "12345", role="admin")
    assert admin_res["success"]
    admin_id = admin_res["data"]["user_id"]
    sender_res = dbm.users.register_user("sender", "pw")
    if not sender_res["success"]:
        sender_res = dbm.users.login_user("sender", "pw")
    from_id = sender_res["data"]["user_id"]
    receiver_res = dbm.users.register_user("receiver", "pw")
    if not receiver_res["success"]:
        receiver_res = dbm.users.login_user("receiver", "pw")
    to_id = receiver_res["data"]["user_id"]
    dbm._from_user_id = from_id
    dbm._to_user_id = to_id
    dbm._admin_id = admin_id
    yield dbm
    if hasattr(dbm, "close"):
        dbm.close()
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

def test_add_transaction_valid(db):
    """Test adding a valid transaction between two users."""
    res = db.transactions.add_transaction(db._from_user_id, db._to_user_id, "debit", 30, "2025-08-19", "Loan")
    assert isinstance(res, dict)
    assert res["success"]
    tr = db.transactions.get_transactions(db._from_user_id)["data"]
    assert len(tr) == 1
    assert tr[0]["type"] == "debit"

@pytest.mark.parametrize(
    "type, amount, error_field",
    [
        ("loan", 30, "type"),
        ("credit", -10, "amount"),
    ]
)
def test_add_transaction_invalid_fields(db, type, amount, error_field):
    """Test error when transaction has invalid type or negative amount."""
    res = db.transactions.add_transaction(db._from_user_id, db._to_user_id, type, amount, "2025-08-19", "Loan")
    assert isinstance(res, dict)
    assert not res["success"]
    assert error_field in res["error"].lower()

def test_delete_transaction(db):
    """Test deleting a transaction by ID for a user."""
    db.transactions.add_transaction(db._from_user_id, db._to_user_id, "credit", 50, "2025-08-19", "Gift")
    tid = db.transactions.get_transactions(db._from_user_id)["data"][0]["id"]
    res = db.transactions.delete_transaction(tid, db._from_user_id)
    assert isinstance(res, dict)
    assert res["success"]
    assert db.transactions.get_transactions(db._from_user_id)["data"] == []

def test_receiver_cannot_delete_transaction(db):
    """
    Authorization: the receiver should NOT be able to delete a transaction
    they don't own (sender-only). With idempotent semantics, the call succeeds
    but deletes 0 rows and logs a 'noop'.
    """
    db.transactions.add_transaction(db._from_user_id, db._to_user_id, "credit", 25, "2025-08-19", "Gift")
    tid = db.transactions.get_transactions(db._from_user_id)["data"][0]["id"]
    res = db.transactions.delete_transaction(tid, db._to_user_id)
    assert isinstance(res, dict)
    assert res["success"]
    assert res["data"]["deleted"] == 0

def test_get_user_balance(db):
    """Test calculation of user balance (credit - debit)."""
    db.transactions.add_transaction(db._from_user_id, db._to_user_id, "credit", 100, "2025-08-19", "Refund")
    db.transactions.add_transaction(db._from_user_id, db._to_user_id, "debit", 40, "2025-08-19", "Loan")
    saldo = db.transactions.get_user_balance(db._from_user_id)
    assert isinstance(saldo, dict)
    assert saldo["success"]
    assert saldo["data"] == 60.0

@pytest.mark.parametrize("invalid_user_id", [9999, -1, None])
def test_transaction_user_id_invalid(db, invalid_user_id):
    """Test error if transaction is added for a non-existent user."""
    res = db.transactions.add_transaction(invalid_user_id, db._to_user_id, "debit", 10, "2025-08-19", "Error")
    assert isinstance(res, dict)
    assert not res["success"]
    assert "user" in res["error"].lower()

def test_admin_can_view_all_transactions(db):
    """Test that admin can view all transactions from all users."""
    db.transactions.add_transaction(db._from_user_id, db._to_user_id, "credit", 50, "2025-08-19", "Gift")
    db.transactions.add_transaction(db._to_user_id, db._from_user_id, "debit", 25, "2025-08-19", "Repay")
    sender_tr = db.transactions.get_transactions(db._from_user_id, as_sender=True)
    assert sender_tr["success"]
    assert all(tr["from_user_id"] == db._from_user_id for tr in sender_tr["data"])
    admin_tr = db.transactions.get_transactions(db._admin_id, is_admin=True)
    assert admin_tr["success"]
    assert len(admin_tr["data"]) >= 2
    ids = {tr["from_user_id"] for tr in admin_tr["data"]}
    assert db._from_user_id in ids and db._to_user_id in ids

def test_admin_flag_does_not_leak_for_normal_user(db):
    """Test that normal user cannot use is_admin to see all transactions."""
    db.transactions.add_transaction(db._from_user_id, db._to_user_id, "credit", 10, "2025-08-19", "Pay")
    user_tr = db.transactions.get_transactions(db._from_user_id, is_admin=False)
    assert user_tr["success"]
    assert all(tr["from_user_id"] == db._from_user_id for tr in user_tr["data"])

def test_non_admin_cannot_use_is_admin_flag(db):
    """
    Even if a normal user passes is_admin=True explicitly, the call must be rejected
    with an 'Admin privileges required' error (no privilege escalation via flag).
    """
    db.transactions.add_transaction(db._from_user_id, db._to_user_id, "debit", 5, "2025-08-19", "flag-check")
    res = db.transactions.get_transactions(db._from_user_id, is_admin=True)
    assert isinstance(res, dict)
    assert not res["success"]
    assert "admin" in (res["error"] or "").lower()

def test_net_balance_and_breakdown_manager(db):
    """
    Test NET balance and breakdown at manager layer.
    Scenario:
      from -> to: credit 50
      from -> to: debit 20
    Expected:
      from: net = -20, legacy = 30
      to:   net = 50,  legacy = 30
    """
    db.transactions.add_transaction(db._from_user_id, db._to_user_id, "credit", 50, "2025-08-19", "Loan")
    db.transactions.add_transaction(db._from_user_id, db._to_user_id, "debit", 20, "2025-08-19", "Repayment")

    net_from = db.transactions.get_user_net_balance(db._from_user_id)
    net_to = db.transactions.get_user_net_balance(db._to_user_id)
    assert net_from["success"] and net_to["success"]
    assert net_from["data"] == -20
    assert net_to["data"] == 50

    br_from = db.transactions.get_user_balance_breakdown(db._from_user_id)
    br_to = db.transactions.get_user_balance_breakdown(db._to_user_id)
    assert br_from["success"] and br_to["success"]

    b1 = br_from["data"]
    b2 = br_to["data"]

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

def test_update_transaction_invalid_type_and_amount(db):
    """
    update_transaction should validate type and amount for partial updates.
    """
    res = db.transactions.add_transaction(db._from_user_id, db._to_user_id, "credit", 10, "2025-08-19", "Init")
    assert res["success"]
    tid = db.transactions.get_transactions(db._from_user_id)["data"][0]["id"]

    # Invalid type
    upd_type = db.transactions.update_transaction(tid, db._from_user_id, type_="wrong")
    assert not upd_type["success"]
    assert "type" in upd_type["error"].lower()

    # Non-numeric amount
    upd_amount = db.transactions.update_transaction(tid, db._from_user_id, amount="abc")
    assert not upd_amount["success"]
    assert "amount" in upd_amount["error"].lower()

    # Non-positive amount
    upd_amount2 = db.transactions.update_transaction(tid, db._from_user_id, amount=0)
    assert not upd_amount2["success"]
    assert "positive" in upd_amount2["error"].lower()


def test_get_transactions_with_date_range_and_contact_filter(db):
    """
    get_transactions should honor date_from/date_to and contact_id filters.
    """
    # Create a contact-bound transaction indirectly by using DatabaseManager-level flow
    # We just insert a contact and refer to its id directly for this low-level test.
    from MoneyMate.data_layer.database import get_connection

    with get_connection(TEST_DB) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO contacts (user_id, name) VALUES (?, ?)",
            (db._from_user_id, "TestContact"),
        )
        contact_id = cur.lastrowid
        conn.commit()

    # Two transactions for same contact on different dates
    db.transactions.add_transaction(
        db._from_user_id, db._to_user_id, "credit", 10, "2025-01-10", "T1", contact_id=contact_id
    )
    db.transactions.add_transaction(
        db._from_user_id, db._to_user_id, "credit", 20, "2025-03-10", "T2", contact_id=contact_id
    )

    # Filter to only February–February range → expect no results
    feb = db.transactions.get_transactions(
        db._from_user_id,
        as_sender=True,
        date_from="2025-02-01",
        date_to="2025-02-28",
        contact_id=contact_id,
    )
    assert feb["success"]
    assert feb["data"] == []

    # Filter to March only → expect T2
    march = db.transactions.get_transactions(
        db._from_user_id,
        as_sender=True,
        date_from="2025-03-01",
        date_to="2025-03-31",
        contact_id=contact_id,
    )
    assert march["success"]
    assert len(march["data"]) == 1
    assert march["data"][0]["description"] == "T2"

def test_add_transaction_receiver_does_not_exist(db):
    """
    When to_user_id points to a non-existent user, add_transaction must fail
    with a clear error, without inserting anything.
    """
    from MoneyMate.data_layer.database import get_connection

    # Create a sender manually using the underlying DB to avoid auto user creation
    with get_connection(TEST_DB) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username, password_hash, role, is_active) VALUES (?,?,?,?)",
                    ("tx_sender_raw", "", "user", 1))
        sender_id = cur.lastrowid
        conn.commit()

    res = db.transactions.add_transaction(
        from_user_id=sender_id,
        to_user_id=999999,  # non-existent receiver
        type_="credit",
        amount=10,
        date="2025-08-19",
        description="bad",
        contact_id=None,
    )
    assert not res["success"]
    assert "receiver" in (res["error"] or "").lower()


def test_add_transaction_same_sender_and_receiver(db):
    """
    add_transaction must reject transactions where sender and receiver are the same,
    as enforced in the manager (and schema CHECK).
    """
    # Use an existing user from the fixture as both sender and receiver
    uid = db._from_user_id
    res = db.transactions.add_transaction(
        from_user_id=uid,
        to_user_id=uid,
        type_="credit",
        amount=10,
        date="2025-08-19",
        description="self",
        contact_id=None,
    )
    assert not res["success"]
    assert "sender" in (res["error"] or "").lower() or "receiver" in (res["error"] or "").lower()

def test_get_transactions_admin_with_filters(db):
    """
    Admin listing with date and contact filters should respect is_admin=True
    and return matching rows only.
    """
    from MoneyMate.data_layer.database import get_connection

    # Create a contact for sender and get its id
    with get_connection(TEST_DB) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO contacts (user_id, name) VALUES (?, ?)", (db._from_user_id, "AdminContact"))
        contact_id = cur.lastrowid
        conn.commit()

    # Two transactions: one in Jan, one in March for that contact
    db.transactions.add_transaction(db._from_user_id, db._to_user_id, "credit", 10, "2025-01-10", "Jan", contact_id=contact_id)
    db.transactions.add_transaction(db._from_user_id, db._to_user_id, "credit", 20, "2025-03-10", "Mar", contact_id=contact_id)

    # Admin filters to March only, with this contact_id
    res = db.transactions.get_transactions(
        user_id=db._admin_id,
        is_admin=True,
        as_sender=True,  # ignored for admin, but we pass it
        contact_id=contact_id,
        date_from="2025-03-01",
        date_to="2025-03-31",
    )
    assert res["success"]
    descs = [t["description"] for t in res["data"]]
    assert "Mar" in descs
    assert "Jan" not in descs