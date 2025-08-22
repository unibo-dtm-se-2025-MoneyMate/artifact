"""
api.py
Unified API interface for MoneyMate data layer, using DatabaseManager.

This module provides high-level functions to interact with expenses,
contacts, and transactions, wrapping DatabaseManager methods.
Each function returns a standardized dictionary response.

"""

from data_layer import DatabaseManager

_db = DatabaseManager()

# --- UTILITY ---

def api_list_tables():
    """
    List all tables in the database.
    Returns: dict {success, error, data}
    """
    return _db.list_tables()


# --- EXPENSES API ---

def api_add_expense(title, price, date, category):
    """
    Add a new expense.
    Returns: dict {success, error, data}
    """
    return _db.add_expense(title, price, date, category)

def api_get_expenses():
    """
    List all expenses.
    Returns: dict {success, error, data}
    """
    return _db.get_expenses()

def api_search_expenses(query):
    """
    Search expenses by title or category.
    Returns: dict {success, error, data}
    """
    return _db.search_expenses(query)

def api_delete_expense(expense_id):
    """
    Delete an expense by id.
    Returns: dict {success, error, data}
    """
    return _db.delete_expense(expense_id)

def api_clear_expenses():
    """
    Delete all expenses.
    Returns: dict {success, error, data}
    """
    return _db.clear_expenses()


# --- CONTACTS API ---

def api_add_contact(name):
    """
    Add a new contact.
    Returns: dict {success, error, data}
    """
    return _db.add_contact(name)

def api_get_contacts():
    """
    List all contacts.
    Returns: dict {success, error, data}
    """
    return _db.get_contacts()

def api_delete_contact(contact_id):
    """
    Delete a contact by id.
    Returns: dict {success, error, data}
    """
    return _db.delete_contact(contact_id)


# --- TRANSACTIONS API ---

def api_add_transaction(contact_id, type_, amount, date, description=""):
    """
    Add a new transaction for a contact.
    Returns: dict {success, error, data}
    """
    return _db.add_transaction(contact_id, type_, amount, date, description)

def api_get_transactions(contact_id=None):
    """
    List transactions. Optionally filter by contact_id.
    Returns: dict {success, error, data}
    """
    return _db.get_transactions(contact_id)

def api_delete_transaction(transaction_id):
    """
    Delete a transaction by id.
    Returns: dict {success, error, data}
    """
    return _db.delete_transaction(transaction_id)

def api_get_contact_balance(contact_id):
    """
    Get the current balance for a given contact.
    Returns: dict {success, error, data}
    """
    return _db.get_contact_balance(contact_id)