"""
Additional tests for DatabaseManager focusing on validation and normalization
helpers (_validate_expense, _validate_transaction, _localize_error_msg, _wrap).

These tests increase coverage of manager.py without changing external behavior.
"""

import os
import gc
import pytest

from MoneyMate.data_layer.manager import DatabaseManager

TEST_DB = "test_manager_internal.db"


@pytest.fixture
def db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    dbm = DatabaseManager(TEST_DB)
    yield dbm
    if hasattr(dbm, "close"):
        dbm.close()
    gc.collect()
    try:
        os.remove(TEST_DB)
    except FileNotFoundError:
        pass


def test_add_expense_validation_errors(db):
    """
    add_expense should surface localized validation errors for title, price and date.
    This drives _validate_expense branches in manager.py.
    """
    # Missing title
    res_title = db.add_expense("", 10, "2025-08-19", "Food")
    assert not res_title["success"]
    assert "titolo" in (res_title["error"] or "").lower()

    # Invalid price (negative)
    res_price = db.add_expense("E", -5, "2025-08-19", "Food")
    assert not res_price["success"]
    assert "prezzo" in (res_price["error"] or "").lower()

    # Invalid date format
    res_date = db.add_expense("E", 10, "19-08-2025", "Food")
    assert not res_date["success"]
    assert "data" in (res_date["error"] or "").lower()


def test_add_transaction_validation_errors(db):
    """
    add_transaction should surface localized validation errors for:
    - missing/invalid contact_id
    - invalid type
    - invalid amount
    - invalid date
    This drives _validate_transaction branches.
    """
    # Missing contact_id
    res_no_contact = db.add_transaction(None, "credit", 10, "2025-08-19", "note")
    assert not res_no_contact["success"]
    assert "contatto" in (res_no_contact["error"] or "").lower()

    # Invalid contact_id (<=0)
    res_bad_contact = db.add_transaction(0, "credit", 10, "2025-08-19", "note")
    assert not res_bad_contact["success"]
    assert "contatto" in (res_bad_contact["error"] or "").lower()

    # Non-existent contact id
    res_missing_contact = db.add_transaction(9999, "credit", 10, "2025-08-19", "note")
    assert not res_missing_contact["success"]
    assert "contatto" in (res_missing_contact["error"] or "").lower()

    # Invalid type
    # First create a real contact through legacy add_contact to pass contact_id check
    c = db.add_contact("Bob")
    assert c["success"]
    contact_id = db.get_contacts()["data"][0]["id"]

    res_bad_type = db.add_transaction(contact_id, "loan", 10, "2025-08-19", "note")
    assert not res_bad_type["success"]
    assert "tipo" in (res_bad_type["error"] or "").lower()

    # Non-numeric amount
    res_bad_amount = db.add_transaction(contact_id, "credit", "abc", "2025-08-19", "note")
    assert not res_bad_amount["success"]
    assert "prezzo" in (res_bad_amount["error"] or "").lower()

    # Invalid date format
    res_bad_date = db.add_transaction(contact_id, "credit", 10, "19-08-2025", "note")
    assert not res_bad_date["success"]
    assert "data" in (res_bad_date["error"] or "").lower()


def test_wrap_normalization_for_various_return_types(db):
    """
    Exercise _wrap via public methods so that:
    - dicts are passed through with ensured 'data' key,
    - lists/tuples are wrapped as success,
    - truthy scalars are wrapped as success with data.
    """
    # list_tables returns a hybrid, but underlying logic uses _wrap internally.
    # Here we simply ensure that a manual list normalized via _wrap behaves.
    res = db._wrap("op", {"success": False, "error": "Error message"})
    assert isinstance(res, dict)
    assert not res["success"]
    # error should be localized (if possible) or left as-is
    assert "error" in res

    # list -> success with data=list(...)
    wrapped_list = db._wrap("op", [1, 2, 3])
    assert wrapped_list["success"]
    assert wrapped_list["data"] == [1, 2, 3]

    # tuple -> success with data=list(...)
    wrapped_tuple = db._wrap("op", (4, 5))
    assert wrapped_tuple["success"]
    assert wrapped_tuple["data"] == [4, 5]

    # truthy scalar
    wrapped_scalar = db._wrap("op", 42)
    assert wrapped_scalar["success"]
    assert wrapped_scalar["data"] == 42

def test_clear_expenses_and_get_transactions_legacy(db):
    """
    Use legacy DatabaseManager methods:
    - add_expense / clear_expenses
    - add_contact / add_transaction / get_transactions / get_contact_balance

    This drives several paths in manager.py (legacy adapter methods).
    """
    # Legacy add_expense and clear_expenses (no explicit user_id)
    r1 = db.add_expense("Legacy1", 10.0, "2025-08-19", "Food")
    r2 = db.add_expense("Legacy2", 15.0, "2025-08-19", "Food")
    assert r1["success"] and r2["success"]

    res_list = db.get_expenses()
    assert res_list["success"]
    assert len(res_list["data"]) == 2

    cleared = db.clear_expenses()
    assert cleared["success"]
    assert db.get_expenses()["data"] == []

    # Now use legacy contacts/transactions API
    c = db.add_contact("LegacyContact")
    assert c["success"]
    cid = db.get_contacts()["data"][0]["id"]

    t = db.add_transaction(cid, "credit", 20, "2025-08-19", "Loan")
    assert t["success"]

    tr = db.get_transactions(cid)
    assert tr["success"]
    assert len(tr["data"]) == 1

    bal = db.get_contact_balance(cid)
    assert bal["success"]
    # get_contact_balance returns net as float in data
    assert isinstance(bal["data"], float)
    assert bal["data"] == 20.0