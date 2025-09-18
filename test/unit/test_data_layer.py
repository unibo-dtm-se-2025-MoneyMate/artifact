import pytest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from MoneyMate.data_layer.manager import DatabaseManager

TEST_DB = "test_expenses.db"

@pytest.fixture
def db():
    # Setup: crea un db pulito per ogni test
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    dbm = DatabaseManager(TEST_DB)
    # Create test users like in the working tests
    user_id = dbm.users.register_user("testuser", "testpass")["data"]["user_id"]
    user2_id = dbm.users.register_user("testuser2", "testpass2")["data"]["user_id"]
    dbm._test_user_id = user_id
    dbm._test_user2_id = user2_id
    yield dbm
    dbm.close()
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

# --- TEST SCHEMA ---

def test_tables_exist(db):
    tables = db.list_tables()["data"]
    # The new implementation includes more tables
    expected_tables = {"expenses", "contacts", "transactions", "users", "categories"}
    assert expected_tables.issubset(set(tables))

# --- TEST CRUD EXPENSES ---

def test_add_expense_valid(db):
    res = db.expenses.add_expense("Spesa", 20.0, "2025-08-19", "Food", db._test_user_id)
    assert res["success"]
    assert res["error"] is None
    all_expenses = db.expenses.get_expenses(db._test_user_id)["data"]
    assert len(all_expenses) == 1

def test_add_expense_missing_field(db):
    res = db.expenses.add_expense("", 20.0, "2025-08-19", "Food", db._test_user_id)
    assert not res["success"]
    assert "title" in res["error"].lower()  # Updated to match the actual error message

def test_add_expense_invalid_price(db):
    res = db.expenses.add_expense("Spesa", -5, "2025-08-19", "Food", db._test_user_id)
    assert not res["success"]
    assert "price" in res["error"].lower()  # Updated to match the actual error message

def test_search_expenses(db):
    db.expenses.add_expense("Spesa1", 10, "2025-08-19", "Food", db._test_user_id)
    db.expenses.add_expense("Taxi", 15, "2025-08-19", "Transport", db._test_user_id)
    res = db.expenses.search_expenses("Taxi", db._test_user_id)
    assert res["success"]
    assert any("Taxi" in e["title"] for e in res["data"])

def test_delete_expense(db):
    db.expenses.add_expense("Spesa", 20, "2025-08-19", "Food", db._test_user_id)
    eid = db.expenses.get_expenses(db._test_user_id)["data"][0]["id"]
    res = db.expenses.delete_expense(eid, db._test_user_id)
    assert res["success"]
    assert db.expenses.get_expenses(db._test_user_id)["data"] == []

def test_clear_expenses(db):
    db.expenses.add_expense("Spesa", 20, "2025-08-19", "Food", db._test_user_id)
    db.expenses.add_expense("Pranzo", 15, "2025-08-19", "Food", db._test_user_id)
    res = db.expenses.clear_expenses(db._test_user_id)
    assert res["success"]
    assert db.expenses.get_expenses(db._test_user_id)["data"] == []

# --- TEST CRUD CONTACTS ---

def test_add_contact_valid(db):
    res = db.contacts.add_contact("Mario", db._test_user_id)
    assert res["success"]
    contacts = db.contacts.get_contacts(db._test_user_id)["data"]
    assert any(c["name"] == "Mario" for c in contacts)

def test_add_contact_empty_name(db):
    res = db.contacts.add_contact("", db._test_user_id)
    assert not res["success"]
    assert "name" in res["error"].lower()  # Updated to match actual error message

def test_delete_contact(db):
    db.contacts.add_contact("Luca", db._test_user_id)
    cid = db.contacts.get_contacts(db._test_user_id)["data"][0]["id"]
    res = db.contacts.delete_contact(cid, db._test_user_id)
    assert res["success"]
    assert db.contacts.get_contacts(db._test_user_id)["data"] == []

# --- TEST CRUD TRANSACTIONS ---

def test_add_transaction_valid(db):
    # Create a contact to link the transaction to
    db.contacts.add_contact("Anna", db._test_user_id)
    contact_id = db.contacts.get_contacts(db._test_user_id)["data"][0]["id"]
    # Add transaction between the two test users, linked to the contact
    res = db.transactions.add_transaction(db._test_user_id, db._test_user2_id, "debit", 30, "2025-08-19", "Prestito", contact_id=contact_id)
    assert res["success"]
    # Get transactions for the sender user, filtered by contact
    tr = db.transactions.get_transactions(db._test_user_id, contact_id=contact_id)["data"]
    assert len(tr) == 1
    assert tr[0]["type"] == "debit"

def test_add_transaction_invalid_type(db):
    # Invalid transaction type
    res = db.transactions.add_transaction(db._test_user_id, db._test_user2_id, "loan", 30, "2025-08-19", "Prestito")
    assert not res["success"]
    assert "type" in res["error"].lower()  # Updated to match actual error message

def test_add_transaction_negative_amount(db):
    # Invalid negative amount
    res = db.transactions.add_transaction(db._test_user_id, db._test_user2_id, "credit", -10, "2025-08-19", "Errore")
    assert not res["success"]
    assert "amount" in res["error"].lower()

def test_delete_transaction(db):
    # Create a contact and transaction
    db.contacts.add_contact("Sam", db._test_user_id)
    contact_id = db.contacts.get_contacts(db._test_user_id)["data"][0]["id"]
    db.transactions.add_transaction(db._test_user_id, db._test_user2_id, "credit", 50, "2025-08-19", "Regalo", contact_id=contact_id)
    tid = db.transactions.get_transactions(db._test_user_id, contact_id=contact_id)["data"][0]["id"]
    res = db.transactions.delete_transaction(tid, db._test_user_id)
    assert res["success"]
    assert db.transactions.get_transactions(db._test_user_id, contact_id=contact_id)["data"] == []

# --- TEST CONTACT'S PORTFOLIO ---

def test_get_contact_balance(db):
    # Create a contact
    db.contacts.add_contact("Giulia", db._test_user_id)
    contact_id = db.contacts.get_contacts(db._test_user_id)["data"][0]["id"]
    # Add transactions between users linked to the contact
    db.transactions.add_transaction(db._test_user_id, db._test_user2_id, "credit", 100, "2025-08-19", "Rimborso", contact_id=contact_id)
    db.transactions.add_transaction(db._test_user_id, db._test_user2_id, "debit", 40, "2025-08-19", "Prestito", contact_id=contact_id)
    # Get balance for this contact from the user's perspective
    saldo = db.transactions.get_contact_balance(db._test_user_id, contact_id)
    assert saldo["success"]
    assert saldo["data"]["net"] == 60.0  # credit - debit = 100 - 40 = 60

# --- TEST DATA VALIDATION ---

def test_expense_date_format(db):
    res = db.expenses.add_expense("Spesa", 10, "19-08-2025", "Food", db._test_user_id)
    assert not res["success"]
    assert "date" in res["error"].lower()  # Updated to match actual error message

def test_transaction_user_id_invalid(db):
    # Test with invalid user ID
    res = db.transactions.add_transaction(9999, db._test_user2_id, "debit", 10, "2025-08-19", "Errore")
    assert not res["success"]
    assert "user" in res["error"].lower()  # Updated to match actual error message

# --- TEST API RESPONSE FORMAT ---

def test_api_response_format(db):
    res = db.expenses.add_expense("A", 1, "2025-08-19", "Food", db._test_user_id)
    assert isinstance(res, dict)
    assert "success" in res and "error" in res and "data" in res 