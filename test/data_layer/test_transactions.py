import sys
import os
import gc
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from MoneyMate.data_layer.manager import DatabaseManager

TEST_DB = "test_transactions.db"

@pytest.fixture
def db():
    """
    Pytest fixture for DatabaseManager.
    Ensures isolation and proper cleanup for each test.
    """
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    dbm = DatabaseManager(TEST_DB)
    # Add two users for transaction tests
    from_id = dbm.users.register_user("sender", "pw")["data"]["user_id"]
    to_id = dbm.users.register_user("receiver", "pw")["data"]["user_id"]
    dbm._from_user_id = from_id
    dbm._to_user_id = to_id
    yield dbm
    if hasattr(dbm, "close"):
        dbm.close()
    gc.collect()
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_add_transaction_valid(db):
    """
    Test adding a valid transaction between two users.
    Verifies that the transaction is added and retrievable.
    """
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
    """
    Test failure when transaction has invalid type or negative amount.
    Verifies that an appropriate error message is returned.
    """
    res = db.transactions.add_transaction(db._from_user_id, db._to_user_id, type, amount, "2025-08-19", "Loan")
    assert isinstance(res, dict)
    assert not res["success"]
    assert error_field in res["error"].lower()

def test_delete_transaction(db):
    """
    Test deleting a transaction by ID for a user.
    Verifies that the transaction list is empty after deletion.
    """
    db.transactions.add_transaction(db._from_user_id, db._to_user_id, "credit", 50, "2025-08-19", "Gift")
    tid = db.transactions.get_transactions(db._from_user_id)["data"][0]["id"]
    res = db.transactions.delete_transaction(tid, db._from_user_id)
    assert isinstance(res, dict)
    assert res["success"]
    assert db.transactions.get_transactions(db._from_user_id)["data"] == []

def test_get_user_balance(db):
    """
    Test calculation of user balance (credit - debit).
    Verifies that the balance is correctly computed for the user.
    """
    db.transactions.add_transaction(db._from_user_id, db._to_user_id, "credit", 100, "2025-08-19", "Refund")
    db.transactions.add_transaction(db._from_user_id, db._to_user_id, "debit", 40, "2025-08-19", "Loan")
    saldo = db.transactions.get_user_balance(db._from_user_id)
    assert isinstance(saldo, dict)
    assert saldo["success"]
    assert saldo["data"] == 60.0

@pytest.mark.parametrize("invalid_user_id", [9999, -1, None])
def test_transaction_user_id_invalid(db, invalid_user_id):
    """
    Test failure when transaction is added for a non-existent user.
    Verifies that the proper error message is returned.
    """
    res = db.transactions.add_transaction(invalid_user_id, db._to_user_id, "debit", 10, "2025-08-19", "Error")
    assert isinstance(res, dict)
    assert not res["success"]
    assert "user" in res["error"].lower()