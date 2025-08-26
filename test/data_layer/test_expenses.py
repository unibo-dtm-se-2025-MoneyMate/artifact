import sys
import os
import gc
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from MoneyMate.data_layer.manager import DatabaseManager

TEST_DB = "test_expenses.db"

@pytest.fixture
def db():
    """
    Pytest fixture for DatabaseManager.
    Ensures isolation and proper cleanup for each test.
    """
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    dbm = DatabaseManager(TEST_DB)
    yield dbm
    if hasattr(dbm, "close"):
        dbm.close()
    gc.collect()  # Release any open SQLite handles
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_tables_exist(db):
    """
    Verify that all required tables are created in the database.
    """
    tables = db.list_tables()["data"]
    tables = [t for t in tables if t != "sqlite_sequence"]
    assert set(tables) == {"expenses", "contacts", "transactions"}

def test_add_expense_valid(db):
    """
    Test adding a valid expense.
    Verifies that the expense is added and retrievable.
    """
    res = db.expenses.add_expense("Expense", 20.0, "2025-08-19", "Food")
    assert isinstance(res, dict)
    assert res["success"]
    assert res["error"] is None
    all_expenses = db.expenses.get_expenses()["data"]
    assert len(all_expenses) == 1

@pytest.mark.parametrize(
    "title, price, date, category, error_field",
    [
        ("", 20.0, "2025-08-19", "Food", "title"),
        ("Expense", -5, "2025-08-19", "Food", "price"),
        ("Expense", 10, "19-08-2025", "Food", "date"),
    ]
)
def test_add_expense_invalid_fields(db, title, price, date, category, error_field):
    """
    Test failure when expense has missing or invalid fields (empty title, negative price, invalid date).
    Checks that the corresponding error message is returned.
    """
    res = db.expenses.add_expense(title, price, date, category)
    assert isinstance(res, dict)
    assert not res["success"]
    assert error_field in res["error"].lower()

def test_search_expenses(db):
    """
    Test searching for expenses by title or category.
    Verifies that filtering works correctly.
    """
    db.expenses.add_expense("Expense1", 10, "2025-08-19", "Food")
    db.expenses.add_expense("Taxi", 15, "2025-08-19", "Transport")
    res = db.expenses.search_expenses("Taxi")
    assert isinstance(res, dict)
    assert res["success"]
    assert any("Taxi" in e["title"] for e in res["data"])

def test_delete_expense(db):
    """
    Test deleting an expense by ID.
    Verifies that the expense list is empty after deletion.
    """
    db.expenses.add_expense("Expense", 20, "2025-08-19", "Food")
    eid = db.expenses.get_expenses()["data"][0]["id"]
    res = db.expenses.delete_expense(eid)
    assert isinstance(res, dict)
    assert res["success"]
    assert db.expenses.get_expenses()["data"] == []

def test_clear_expenses(db):
    """
    Test deleting all expenses.
    Verifies that the expenses table is empty after clearing.
    """
    db.expenses.add_expense("Expense", 20, "2025-08-19", "Food")
    db.expenses.add_expense("Lunch", 15, "2025-08-19", "Food")
    res = db.expenses.clear_expenses()
    assert isinstance(res, dict)
    assert res["success"]
    assert db.expenses.get_expenses()["data"] == []

def test_api_response_format(db):
    """
    Test that the API response is always a dictionary with success, error, and data keys.
    Ensures API contract is respected.
    """
    res = db.expenses.add_expense("A", 1, "2025-08-19", "Food")
    assert isinstance(res, dict)
    assert "success" in res and "error" in res and "data" in res