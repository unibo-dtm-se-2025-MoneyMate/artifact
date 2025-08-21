import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
from MoneyMate.data_layer import DatabaseManager

TEST_DB = "test_expenses.db"

@pytest.fixture
def db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    dbm = DatabaseManager(TEST_DB)
    yield dbm
    # If you have a close() method, call it
    if hasattr(dbm, "close"):
        dbm.close()
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_tables_exist(db):
    tables = db.list_tables()["data"]  # <-- accedi alla chiave "data"
    assert set(tables) == {"expenses", "contacts", "transactions"}

def test_add_expense_valid(db):
    res = db.add_expense("Expense", 20.0, "2025-08-19", "Food")
    assert res["success"]
    assert res["error"] is None
    all_expenses = db.get_expenses()["data"]
    assert len(all_expenses) == 1

def test_add_expense_missing_field(db):
    res = db.add_expense("", 20.0, "2025-08-19", "Food")
    assert not res["success"]
    assert "title" in res["error"].lower()

def test_add_expense_invalid_price(db):
    res = db.add_expense("Expense", -5, "2025-08-19", "Food")
    assert not res["success"]
    assert "price" in res["error"].lower()

def test_search_expenses(db):
    db.add_expense("Expense1", 10, "2025-08-19", "Food")
    db.add_expense("Taxi", 15, "2025-08-19", "Transport")
    res = db.search_expenses("Taxi")
    assert res["success"]
    assert any("Taxi" in e["title"] for e in res["data"])

def test_delete_expense(db):
    db.add_expense("Expense", 20, "2025-08-19", "Food")
    eid = db.get_expenses()["data"][0]["id"]
    res = db.delete_expense(eid)
    assert res["success"]
    assert db.get_expenses()["data"] == []

def test_clear_expenses(db):
    db.add_expense("Expense", 20, "2025-08-19", "Food")
    db.add_expense("Lunch", 15, "2025-08-19", "Food")
    res = db.clear_expenses()
    assert res["success"]
    assert db.get_expenses()["data"] == []

def test_add_contact_valid(db):
    res = db.add_contact("Mario")
    assert res["success"]
    contacts = db.get_contacts()["data"]
    assert any(c["name"] == "Mario" for c in contacts)

def test_add_contact_empty_name(db):
    res = db.add_contact("")
    assert not res["success"]
    assert "name" in res["error"].lower()

def test_delete_contact(db):
    db.add_contact("Luca")
    cid = db.get_contacts()["data"][0]["id"]
    res = db.delete_contact(cid)
    assert res["success"]
    assert db.get_contacts()["data"] == []

def test_add_transaction_valid(db):
    db.add_contact("Anna")
    contact_id = db.get_contacts()["data"][0]["id"]
    res = db.add_transaction(contact_id, "debit", 30, "2025-08-19", "Loan")
    assert res["success"]
    tr = db.get_transactions(contact_id)["data"]
    assert len(tr) == 1
    assert tr[0]["type"] == "debit"

def test_add_transaction_invalid_type(db):
    db.add_contact("Bob")
    contact_id = db.get_contacts()["data"][0]["id"]
    res = db.add_transaction(contact_id, "loan", 30, "2025-08-19", "Loan")
    assert not res["success"]
    assert "type" in res["error"].lower()

def test_add_transaction_negative_amount(db):
    db.add_contact("Eve")
    contact_id = db.get_contacts()["data"][0]["id"]
    res = db.add_transaction(contact_id, "credit", -10, "2025-08-19", "Error")
    assert not res["success"]
    assert "amount" in res["error"].lower()

def test_delete_transaction(db):
    db.add_contact("Sam")
    contact_id = db.get_contacts()["data"][0]["id"]
    db.add_transaction(contact_id, "credit", 50, "2025-08-19", "Gift")
    tid = db.get_transactions(contact_id)["data"][0]["id"]
    res = db.delete_transaction(tid)
    assert res["success"]
    assert db.get_transactions(contact_id)["data"] == []

def test_get_contact_balance(db):
    db.add_contact("Julia")
    contact_id = db.get_contacts()["data"][0]["id"]
    db.add_transaction(contact_id, "credit", 100, "2025-08-19", "Refund")
    db.add_transaction(contact_id, "debit", 40, "2025-08-19", "Loan")
    saldo = db.get_contact_balance(contact_id)
    assert saldo["success"]
    assert saldo["data"] == 60.0

def test_expense_date_format(db):
    res = db.add_expense("Expense", 10, "19-08-2025", "Food")
    assert not res["success"]
    assert "date" in res["error"].lower()

def test_transaction_contact_id_invalid(db):
    res = db.add_transaction(9999, "debit", 10, "2025-08-19", "Error")
    assert not res["success"]
    assert "contact" in res["error"].lower()

def test_api_response_format(db):
    res = db.add_expense("A", 1, "2025-08-19", "Food")
    assert isinstance(res, dict)
    assert "success" in res and "error" in res and "data" in res