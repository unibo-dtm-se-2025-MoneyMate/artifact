import sys
import os
import gc
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
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

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