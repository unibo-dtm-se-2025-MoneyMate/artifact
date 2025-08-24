from MoneyMate.data_layer.validation import validate_expense, validate_contact, validate_transaction

def test_validate_expense_ok():
    # Test that a valid expense passes validation (returns None).
    assert validate_expense("Dinner", 10, "2025-08-19", "Food") is None

def test_validate_expense_missing_title():
    # Test that an expense with no title returns an error indicating missing title.
    assert "title" in validate_expense("", 10, "2025-08-19", "Food").lower()

def test_validate_contact_empty():
    # Test that an empty contact name returns an error indicating the name is required.
    assert "required" in validate_contact("")

def test_validate_transaction_type_invalid():
    # Test that an invalid transaction type returns an error.
    assert "type" in validate_transaction("wrong", 10, "2025-08-19").lower()

def test_validate_transaction_negative_amount():
    # Test that a negative transaction amount returns an error.
    assert "positive" in validate_transaction("credit", -5, "2025-08-19").lower()