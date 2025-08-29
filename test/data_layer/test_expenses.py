import sys
import os
import gc
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from MoneyMate.data_layer.manager import DatabaseManager
from MoneyMate.data_layer.database import get_connection

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
    user_id = dbm.users.register_user("expensesuser", "pw")["data"]["user_id"]
    dbm._test_user_id = user_id
    yield dbm
    if hasattr(dbm, "close"):
        dbm.close()
    gc.collect()
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_tables_exist(db):
    """
    Verify that all required tables are created in the database (core + extended).
    """
    tables = db.list_tables()["data"]
    tables = [t for t in tables if t != "sqlite_sequence"]
    assert set(tables) >= {"expenses", "contacts", "transactions", "users", "categories", "notes", "attachments", "access_logs"}

def test_add_expense_valid(db):
    """
    Test adding a valid expense for a user.
    Verifies that the expense is added and retrievable.
    """
    res = db.expenses.add_expense("Expense", 20.0, "2025-08-19", "Food", db._test_user_id)
    assert isinstance(res, dict)
    assert res["success"]
    assert res["error"] is None
    all_expenses = db.expenses.get_expenses(db._test_user_id)["data"]
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
    res = db.expenses.add_expense(title, price, date, category, db._test_user_id)
    assert isinstance(res, dict)
    assert not res["success"]
    assert error_field in res["error"].lower()

def test_search_expenses(db):
    """
    Test searching for expenses by title or category for a user.
    Verifies that filtering works correctly.
    """
    db.expenses.add_expense("Expense1", 10, "2025-08-19", "Food", db._test_user_id)
    db.expenses.add_expense("Taxi", 15, "2025-08-19", "Transport", db._test_user_id)
    res = db.expenses.search_expenses("Taxi", db._test_user_id)
    assert isinstance(res, dict)
    assert res["success"]
    assert any("Taxi" in e["title"] for e in res["data"])

def test_delete_expense(db):
    """
    Test deleting an expense by ID for a user.
    Verifies that the expense list is empty after deletion.
    """
    db.expenses.add_expense("Expense", 20, "2025-08-19", "Food", db._test_user_id)
    eid = db.expenses.get_expenses(db._test_user_id)["data"][0]["id"]
    res = db.expenses.delete_expense(eid, db._test_user_id)
    assert isinstance(res, dict)
    assert res["success"]
    assert db.expenses.get_expenses(db._test_user_id)["data"] == []

def test_clear_expenses(db):
    """
    Test deleting all expenses for a user.
    Verifies that the expenses table is empty after clearing.
    """
    db.expenses.add_expense("Expense", 20, "2025-08-19", "Food", db._test_user_id)
    db.expenses.add_expense("Lunch", 15, "2025-08-19", "Food", db._test_user_id)
    res = db.expenses.clear_expenses(db._test_user_id)
    assert isinstance(res, dict)
    assert res["success"]
    assert db.expenses.get_expenses(db._test_user_id)["data"] == []

def test_api_response_format(db):
    """
    Test that the API response is always a dictionary with success, error, and data keys.
    Ensures API contract is respected.
    """
    res = db.expenses.add_expense("A", 1, "2025-08-19", "Food", db._test_user_id)
    assert isinstance(res, dict)
    assert "success" in res and "error" in res and "data" in res

def test_add_expense_with_category_id_valid(db):
    """
    Add an expense linked to a user-owned category (via category_id).
    Expects success and that category_id is present in the retrieved expense.
    """
    # Create a category for this user
    with get_connection(TEST_DB) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO categories (user_id, name) VALUES (?, ?)", (db._test_user_id, "FoodCat"))
        cat_id = cur.lastrowid
        conn.commit()

    res = db.expenses.add_expense("ExpenseCat", 12.0, "2025-08-19", "Food", db._test_user_id, category_id=cat_id)
    assert res["success"]

    all_expenses = db.expenses.get_expenses(db._test_user_id)["data"]
    # Find our expense and ensure category_id is included and correct
    matches = [e for e in all_expenses if e["title"] == "ExpenseCat"]
    assert matches, "Expected to find the expense we just inserted"
    assert "category_id" in matches[0]
    assert matches[0]["category_id"] == cat_id

def test_add_expense_with_category_id_invalid_user(db):
    """
    Attempt to add an expense with a category_id belonging to another user.
    Expects validation failure.
    """
    # Create another user and a category for that user
    other_user_id = db.users.register_user("otheruser", "pw")["data"]["user_id"]
    with get_connection(TEST_DB) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO categories (user_id, name) VALUES (?, ?)", (other_user_id, "OtherCat"))
        other_cat_id = cur.lastrowid
        conn.commit()

    res = db.expenses.add_expense("WrongCat", 9.0, "2025-08-19", "Misc", db._test_user_id, category_id=other_cat_id)
    assert not res["success"]
    assert "invalid category" in res["error"].lower()