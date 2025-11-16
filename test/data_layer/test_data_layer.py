"""
Legacy data layer wrapper tests.

This module tests the compatibility wrapper DatabaseManager defined in
test_manager.py (re-exported as data_layer.DatabaseManager), ensuring:

- list_tables() exposes the expected core tables (expenses, contacts, transactions).
- Legacy add/get/search/delete/clear flows for expenses and contacts work.
- Transaction CRUD and contact balance calculations behave as expected.
- Validation errors for expenses and transactions are localized and shaped
  into the standard {success, error, data} response format.
"""

import pytest
import os
from data_layer import DatabaseManager

TEST_DB = "test_expenses.db"

@pytest.fixture
def db():
    # Setup: crea un db pulito per ogni test
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    dbm = DatabaseManager(TEST_DB)
    yield dbm
    dbm.close()
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

# --- TEST SCHEMA ---

def test_tables_exist(db):
    tables = db.list_tables()
    assert set(tables) == {"expenses", "contacts", "transactions"}

# --- TEST CRUD EXPENSES ---

def test_add_expense_valid(db):
    res = db.add_expense("Spesa", 20.0, "2025-08-19", "Food")
    assert res["success"]
    assert res["error"] is None
    all_expenses = db.get_expenses()["data"]
    assert len(all_expenses) == 1

def test_add_expense_missing_field(db):
    res = db.add_expense("", 20.0, "2025-08-19", "Food")
    assert not res["success"]
    assert "titolo" in res["error"].lower()

def test_add_expense_invalid_price(db):
    res = db.add_expense("Spesa", -5, "2025-08-19", "Food")
    assert not res["success"]
    assert "prezzo" in res["error"].lower()

def test_search_expenses(db):
    db.add_expense("Spesa1", 10, "2025-08-19", "Food")
    db.add_expense("Taxi", 15, "2025-08-19", "Transport")
    res = db.search_expenses("Taxi")
    assert res["success"]
    assert any("Taxi" in e["title"] for e in res["data"])

def test_delete_expense(db):
    db.add_expense("Spesa", 20, "2025-08-19", "Food")
    eid = db.get_expenses()["data"][0]["id"]
    res = db.delete_expense(eid)
    assert res["success"]
    assert db.get_expenses()["data"] == []

def test_clear_expenses(db):
    db.add_expense("Spesa", 20, "2025-08-19", "Food")
    db.add_expense("Pranzo", 15, "2025-08-19", "Food")
    res = db.clear_expenses()
    assert res["success"]
    assert db.get_expenses()["data"] == []

# --- TEST CRUD CONTACTS ---

def test_add_contact_valid(db):
    res = db.add_contact("Mario")
    assert res["success"]
    contacts = db.get_contacts()["data"]
    assert any(c["name"] == "Mario" for c in contacts)

def test_add_contact_empty_name(db):
    res = db.add_contact("")
    assert not res["success"]
    assert "nome" in res["error"].lower()

def test_delete_contact(db):
    db.add_contact("Luca")
    cid = db.get_contacts()["data"][0]["id"]
    res = db.delete_contact(cid)
    assert res["success"]
    assert db.get_contacts()["data"] == []

# --- TEST CRUD TRANSACTIONS ---

def test_add_transaction_valid(db):
    db.add_contact("Anna")
    contact_id = db.get_contacts()["data"][0]["id"]
    res = db.add_transaction(contact_id, "debit", 30, "2025-08-19", "Prestito")
    assert res["success"]
    tr = db.get_transactions(contact_id)["data"]
    assert len(tr) == 1
    assert tr[0]["type"] == "debit"

def test_add_transaction_invalid_type(db):
    db.add_contact("Bob")
    contact_id = db.get_contacts()["data"][0]["id"]
    res = db.add_transaction(contact_id, "loan", 30, "2025-08-19", "Prestito")
    assert not res["success"]
    assert "tipo" in res["error"].lower()

def test_add_transaction_negative_amount(db):
    db.add_contact("Eve")
    contact_id = db.get_contacts()["data"][0]["id"]
    res = db.add_transaction(contact_id, "credit", -10, "2025-08-19", "Errore")
    assert not res["success"]
    assert "amount" in res["error"].lower()

def test_delete_transaction(db):
    db.add_contact("Sam")
    contact_id = db.get_contacts()["data"][0]["id"]
    db.add_transaction(contact_id, "credit", 50, "2025-08-19", "Regalo")
    tid = db.get_transactions(contact_id)["data"][0]["id"]
    res = db.delete_transaction(tid)
    assert res["success"]
    assert db.get_transactions(contact_id)["data"] == []

# --- TEST CONTACT'S PORTFOLIO ---

def test_get_contact_balance(db):
    db.add_contact("Giulia")
    contact_id = db.get_contacts()["data"][0]["id"]
    db.add_transaction(contact_id, "credit", 100, "2025-08-19", "Rimborso")
    db.add_transaction(contact_id, "debit", 40, "2025-08-19", "Prestito")
    saldo = db.get_contact_balance(contact_id)
    assert saldo["success"]
    assert saldo["data"] == 60.0

# --- TEST DATA VALIDATION ---

def test_expense_date_format(db):
    res = db.add_expense("Spesa", 10, "19-08-2025", "Food")
    assert not res["success"]
    assert "data" in res["error"].lower()

def test_transaction_contact_id_invalid(db):
    res = db.add_transaction(9999, "debit", 10, "2025-08-19", "Errore")
    assert not res["success"]
    assert "contatto" in res["error"].lower()

# --- TEST API RESPONSE FORMAT ---

def test_api_response_format(db):
    res = db.add_expense("A", 1, "2025-08-19", "Food")
    assert isinstance(res, dict)
    assert "success" in res and "error" in res and "data" in res 