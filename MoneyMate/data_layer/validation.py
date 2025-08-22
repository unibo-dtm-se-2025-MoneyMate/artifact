from datetime import datetime

# --- VALIDATION METHODS ---
def validate_expense(title, price, date, category):
    """
    Validates expense fields: title, price, date, category.
    Returns an error string if something is wrong, otherwise None.
    """
    # Check if title is missing with specific error
    if not title:
        return "Missing title"
    if not all([price, date, category]):
        return "All fields required"
    try:
        price_val = float(price)
        if price_val <= 0:
            return "Price must be positive"
    except Exception:
        return "Invalid price"
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except Exception:
        return "Invalid date format (YYYY-MM-DD required)"
    return None

def validate_contact(name):
    """
    Validates contact name. Returns error string if invalid, otherwise None.
    """
    if not name:
        return "Contact name required"
    return None

def validate_transaction(type_, amount, date):
    """
    Validates transaction fields: type, amount, date.
    Returns error string if invalid, otherwise None.
    """
    if type_ not in ("debit", "credit"):
        return "Invalid type (debit/credit)"
    if amount <= 0:
        return "Amount must be positive"
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except Exception:
        return "Invalid date format (YYYY-MM-DD required)"
    return None