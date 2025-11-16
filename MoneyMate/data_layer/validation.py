"""
Validation helpers for MoneyMate domain entities.

This module centralizes field-level validation for:

- Expenses: title, price, date, and category semantics.
- Contacts: required and non-empty names.
- Transactions: type (debit/credit), amount, and date.

Each validator returns either an error string describing the problem or None
if the input is considered valid, enabling consistent error messages across
managers and GUI layers.
"""

from datetime import datetime
from typing import Optional, Any
from .database import get_connection


# --- VALIDATION METHODS ---

def validate_expense(title: Optional[str], price: Any, date: Optional[str], category: Optional[str]) -> Optional[str]:
    """
    Validate expense fields: title, price, date, category.
    Returns an error string if something is wrong, otherwise None.

    Rules:
    - title: required, non-empty after trimming
    - price: required, numeric (float-castable), strictly > 0
    - date: required, format YYYY-MM-DD
    - category: required (legacy text), non-empty after trimming
    """
    # Normalize string fields
    title_norm = title.strip() if isinstance(title, str) else title
    category_norm = category.strip() if isinstance(category, str) else category

    # Specific title check (dedicated message for clearer UX)
    if not title_norm:
        return "Missing title"

    # Explicit presence checks (avoid treating 0 as missing)
    if price is None or date is None or category_norm is None or category_norm == "":
        return "All fields required"

    # Price must be numeric and positive
    try:
        price_val = float(price)
    except Exception:
        return "Invalid price"
    if price_val <= 0:
        return "Price must be positive"

    # Date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except Exception:
        return "Invalid date format (YYYY-MM-DD required)"

    return None


def validate_contact(name: Optional[str]) -> Optional[str]:
    """
    Validate contact name.
    Returns an error string if invalid, otherwise None.

    Rules:
    - name: required, non-empty after trimming
    """
    name_norm = name.strip() if isinstance(name, str) else name
    if not name_norm:
        return "Contact name required"
    return None


def validate_transaction(type_: Optional[str], amount: Any, date: Optional[str]) -> Optional[str]:
    """
    Validate transaction fields: type, amount, date.
    Returns an error string if invalid, otherwise None.

    Rules:
    - type: required, one of {'debit', 'credit'} (case-insensitive)
    - amount: required, numeric (float-castable), strictly > 0
    - date: required, format YYYY-MM-DD
    """
    # Type normalization and validation
    type_norm = type_.lower().strip() if isinstance(type_, str) else None
    if type_norm not in ("debit", "credit"):
        return "Invalid type (debit/credit)"

    # Amount must be numeric and positive
    try:
        amount_val = float(amount)
    except Exception:
        return "Invalid amount"
    if amount_val <= 0:
        return "Amount must be positive"

    # Date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except Exception:
        return "Invalid date format (YYYY-MM-DD required)"

    return None