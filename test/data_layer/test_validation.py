"""
Pure validation tests (no database).

This file verifies the behavior of validation.py helpers:

- validate_expense: multiple valid cases, missing title or other fields,
  price edge cases, non-numeric price, and whitespace-only fields.
- validate_contact: empty/None/whitespace-only names are rejected.
- validate_transaction: invalid type, case-insensitive type matching,
  non-positive or non-numeric amounts, and invalid date formats.

Each test asserts that returned error messages mention the relevant field.
"""

import pytest
from MoneyMate.data_layer.validation import validate_expense, validate_contact, validate_transaction

# --- validate_expense ---

@pytest.mark.parametrize(
    "title, price, date, category", [
        ("Dinner", 10, "2025-08-19", "Food"),
        ("Taxi", 15.75, "2025-08-20", "Transport"),
        ("Coffee", "2.00", "2025-08-21", "Drinks"),  # price as numeric string should be accepted
    ]
)
def test_validate_expense_ok(title, price, date, category):
    """
    Test that valid expense data passes validation (should return None).
    Using parametrization to check multiple valid cases.
    """
    assert validate_expense(title, price, date, category) is None

@pytest.mark.parametrize("title", ["", None, "   "])
def test_validate_expense_missing_title(title):
    """
    Test that an expense with no title (empty/None/whitespace) returns an error indicating missing title.
    """
    error = validate_expense(title, 10, "2025-08-19", "Food")
    assert error is not None
    assert "title" in error.lower()

@pytest.mark.parametrize(
    "date, category",
    [
        (None, "Food"),        # missing date
        ("2025-08-19", ""),    # empty category
        ("2025-08-19", None),  # missing category
        ("2025-08-19", "   "), # whitespace-only category
    ]
)
def test_validate_expense_missing_non_title_fields(date, category):
    """
    validate_expense should flag other required fields (date/category) when missing/empty/whitespace.
    """
    err = validate_expense("Item", 10, date, category)
    assert err is not None
    assert "required" in err.lower()

@pytest.mark.parametrize(
    "price, msg_sub",
    [(-5, "positive"), (0, "positive"), ("abc", "price")]
)
def test_validate_expense_price_edges(price, msg_sub):
    """
    validate_expense should reject:
    - negative or zero price (message mentions 'positive')
    - non-numeric price (message mentions 'price')
    """
    err = validate_expense("Item", price, "2025-08-19", "Food")
    assert err is not None
    assert msg_sub in err.lower()

# --- validate_contact ---

@pytest.mark.parametrize("name", ["", None, "   "])
def test_validate_contact_empty(name):
    """
    Test that an empty/None/whitespace contact name returns an error indicating the name is required.
    """
    error = validate_contact(name)
    assert error is not None
    assert "required" in error.lower()

# --- validate_transaction ---

@pytest.mark.parametrize("trans_type", ["wrong", "", None])
def test_validate_transaction_type_invalid(trans_type):
    """
    Test that an invalid transaction type returns an error message mentioning 'type'.
    """
    error = validate_transaction(trans_type, 10, "2025-08-19")
    assert error is not None
    assert "type" in error.lower()

def test_validate_transaction_type_case_insensitive():
    """
    Transaction type should be validated case-insensitively (e.g., 'CrEdIt' is valid).
    """
    error = validate_transaction("CrEdIt", 10, "2025-08-19")
    assert error is None

@pytest.mark.parametrize("amount", [-5, 0, -100])
def test_validate_transaction_negative_amount(amount):
    """
    Test that a non-positive transaction amount returns an error mentioning 'positive'.
    """
    error = validate_transaction("credit", amount, "2025-08-19")
    assert error is not None
    assert "positive" in error.lower()

def test_validate_transaction_non_numeric_amount():
    """
    A non-numeric amount should be rejected with an error mentioning 'amount'.
    """
    error = validate_transaction("debit", "ten", "2025-08-19")
    assert error is not None
    assert "amount" in error.lower()

@pytest.mark.parametrize("bad_date", ["19-08-2025", None])
def test_validate_transaction_invalid_date_format(bad_date):
    """
    Test that an invalid or None date is rejected with an appropriate error mentioning 'date format'.
    """
    error = validate_transaction("debit", 10, bad_date)
    assert error is not None
    assert "date format" in error.lower()