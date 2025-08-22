import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import pytest
from MoneyMate.data_layer import DatabaseManager

TEST_DB = "test_transactions.db"

@pytest.fixture
def db():
    # Setup: create a clean test database
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    dbm = DatabaseManager(TEST_DB)
    yield dbm
    # Teardown: remove the test database after tests
    if hasattr(dbm, "close"):
        dbm.close()
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_add_transaction_valid(db):
    # Test adding a valid transaction for an existing contact
    db.add_contact("Anna")
    contact_id = db.get_contacts()["data"][0]["id"]
    res = db.add_transaction(contact_id, "debit", 30, "2025-08-19", "Loan")
    assert res["success"]
    tr = db.get_transactions(contact_id)["data"]
    assert len(tr) == 1
    assert tr[0]["type"] == "debit"

def test_add_transaction_invalid_type(db):
    # Test failure when transaction type is invalid
    db.add_contact("Bob")
    contact_id = db.get_contacts()["data"][0]["id"]
    res = db.add_transaction(contact_id, "loan", 30, "2025-08-19", "Loan")
    assert not res["success"]
    assert "type" in res["error"].lower()

def test_add_transaction_negative_amount(db):
    # Test failure when transaction amount is negative
    db.add_contact("Eve")
    contact_id = db.get_contacts()["data"][0]["id"]
    res = db.add_transaction(contact_id, "credit", -10, "2025-08-19", "Error")
    assert not res["success"]
    assert "amount" in res["error"].lower()

def test_delete_transaction(db):
    # Test deleting a transaction by ID
    db.add_contact("Sam")
    contact_id = db.get_contacts()["data"][0]["id"]
    db.add_transaction(contact_id, "credit", 50, "2025-08-19", "Gift")
    tid = db.get_transactions(contact_id)["data"][0]["id"]
    res = db.delete_transaction(tid)
    assert res["success"]
    assert db.get_transactions(contact_id)["data"] == []

def test_get_contact_balance(db):
    # Test calculation of contact balance (credit - debit)
    db.add_contact("Julia")
    contact_id = db.get_contacts()["data"][0]["id"]
    db.add_transaction(contact_id, "credit", 100, "2025-08-19", "Refund")
    db.add_transaction(contact_id, "debit", 40, "2025-08-19", "Loan")
    saldo = db.get_contact_balance(contact_id)
    assert saldo["success"]
    assert saldo["data"] == 60.0

def test_transaction_contact_id_invalid(db):
    # Test failure when transaction is added for a non-existent contact
    res = db.add_transaction(9999, "debit", 10, "2025-08-19", "Error")
    assert not res["success"]
    assert "contact" in res["error"].lower()