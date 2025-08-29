import pytest
from MoneyMate.data_layer.validation import validate_expense, validate_contact, validate_transaction

# This file tests the pure validation functions for expenses, contacts, and transactions.
# It uses pytest parametrization for better coverage, readability, and scalability.
# No database or external resource is involved.

@pytest.mark.parametrize(
    "title, price, date, category", [
        ("Dinner", 10, "2025-08-19", "Food"),
        ("Taxi", 15, "2025-08-20", "Transport"),
        ("Coffee", 2, "2025-08-21", "Drinks"),
    ]
)
def test_validate_expense_ok(title, price, date, category):
    """
    Test that valid expense data passes validation (should return None).
    Using parametrization to check multiple valid cases.
    """
    assert validate_expense(title, price, date, category) is None

@pytest.mark.parametrize(
    "title",
    ["", None]
)
def test_validate_expense_missing_title(title):
    """
    Test that an expense with no title (empty or None) returns an error indicating missing title.
    """
    error = validate_expense(title, 10, "2025-08-19", "Food")
    assert error is not None
    assert "title" in error.lower()

@pytest.mark.parametrize(
    "name",
    ["", None]
)
def test_validate_contact_empty(name):
    """
    Test that an empty or None contact name returns an error indicating the name is required.
    """
    error = validate_contact(name)
    assert error is not None
    assert "required" in error.lower()

@pytest.mark.parametrize(
    "trans_type",
    ["wrong", "", None]
)
def test_validate_transaction_type_invalid(trans_type):
    """
    Test that an invalid transaction type returns an error message mentioning 'type'.
    """
    error = validate_transaction(trans_type, 10, "2025-08-19")
    assert error is not None
    assert "type" in error.lower()

@pytest.mark.parametrize(
    "amount",
    [-5, 0, -100]
)
def test_validate_transaction_negative_amount(amount):
    """
    Test that a non-positive transaction amount returns an error mentioning 'positive'.
    """
    error = validate_transaction("credit", amount, "2025-08-19")
    assert error is not None
    assert "positive" in error.lower()

def test_validate_transaction_invalid_date_format():
    """
    Test that an invalid date format is rejected with an appropriate error.
    """
    error = validate_transaction("debit", 10, "19-08-2025")
    assert error is not None
    assert "date format" in error.lower()