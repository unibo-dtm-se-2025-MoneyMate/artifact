import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import pytest
from MoneyMate.data_layer.manager import DatabaseManager

TEST_DB = "test_expenses.db"

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

def test_tables_exist(db):
    # Verify that all required tables are created in the database
    tables = db.list_tables()["data"]
    tables = [t for t in tables if t != "sqlite_sequence"]
    assert set(tables) == {"expenses", "contacts", "transactions"}

def test_add_expense_valid(db):
    # Test adding a valid expense
    res = db.expenses.add_expense("Expense", 20.0, "2025-08-19", "Food")
    assert res["success"]
    assert res["error"] is None
    all_expenses = db.expenses.get_expenses()["data"]
    assert len(all_expenses) == 1

def test_add_expense_missing_field(db):
    # Test failure when expense title is missing
    res = db.expenses.add_expense("", 20.0, "2025-08-19", "Food")
    assert not res["success"]
    assert "title" in res["error"].lower()

def test_add_expense_invalid_price(db):
    # Test failure when expense price is negative
    res = db.expenses.add_expense("Expense", -5, "2025-08-19", "Food")
    assert not res["success"]
    assert "price" in res["error"].lower()

def test_search_expenses(db):
    # Test searching for expenses by title or category
    db.expenses.add_expense("Expense1", 10, "2025-08-19", "Food")
    db.expenses.add_expense("Taxi", 15, "2025-08-19", "Transport")
    res = db.expenses.search_expenses("Taxi")
    assert res["success"]
    assert any("Taxi" in e["title"] for e in res["data"])

def test_delete_expense(db):
    # Test deleting an expense by ID
    db.expenses.add_expense("Expense", 20, "2025-08-19", "Food")
    eid = db.expenses.get_expenses()["data"][0]["id"]
    res = db.expenses.delete_expense(eid)
    assert res["success"]
    assert db.expenses.get_expenses()["data"] == []

def test_clear_expenses(db):
    # Test deleting all expenses
    db.expenses.add_expense("Expense", 20, "2025-08-19", "Food")
    db.expenses.add_expense("Lunch", 15, "2025-08-19", "Food")
    res = db.expenses.clear_expenses()
    assert res["success"]
    assert db.expenses.get_expenses()["data"] == []

def test_expense_date_format(db):
    # Test failure when expense date format is invalid
    res = db.expenses.add_expense("Expense", 10, "19-08-2025", "Food")
    assert not res["success"]
    assert "date" in res["error"].lower()

def test_api_response_format(db):
    # Test that the API response is always a dictionary with success, error, and data keys
    res = db.expenses.add_expense("A", 1, "2025-08-19", "Food")
    assert isinstance(res, dict)
    assert "success" in res and "error" in res and "data" in res