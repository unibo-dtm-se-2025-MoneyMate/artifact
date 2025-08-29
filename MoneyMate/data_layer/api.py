"""
api.py
Unified API interface for MoneyMate data layer, using DatabaseManager.

This module provides high-level functions to interact with expenses,
contacts, transactions, and users, wrapping DatabaseManager methods.
Each function returns a standardized dictionary response.

Now supports user-scoped operations for expenses, contacts, and transactions,
including tracking transactions/credit between users.
"""

from MoneyMate.data_layer.manager import DatabaseManager
import logging
import MoneyMate.data_layer.logging_config  # Ensure global logging configuration

logger = logging.getLogger(__name__)

_db = None

def get_db():
    global _db
    if _db is None:
        logger.info("Creating new DatabaseManager instance with default DB path.")
        _db = DatabaseManager()
    return _db

def set_db_path(db_path):
    """
    Set the database path for the API module.
    This allows tests or other modules to use a custom database file.
    If db_path is None, releases the global _db reference for proper cleanup.
    """
    global _db
    if db_path is None:
        logger.info("Releasing DatabaseManager instance (cleanup).")
        _db = None
    else:
        logger.info(f"Setting DatabaseManager db_path to: {db_path}")
        _db = DatabaseManager(db_path)

# --- UTILITY ---

def api_list_tables():
    """
    List all tables in the database.
    Returns: dict {success, error, data}
    """
    logger.info("API call: api_list_tables")
    return _db.list_tables()

# --- USERS API ---

def api_register_user(username, password):
    """
    Register a new user.
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_register_user (username={username})")
    return _db.users.register_user(username, password)

def api_login_user(username, password):
    """
    Authenticate a user.
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_login_user (username={username})")
    return _db.users.login_user(username, password)

# --- EXPENSES API ---

def api_add_expense(title, price, date, category, user_id):
    """
    Add a new expense for the specified user.
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_add_expense (title={title}, price={price}, date={date}, category={category}, user_id={user_id})")
    return _db.expenses.add_expense(title, price, date, category, user_id)

def api_get_expenses(user_id):
    """
    List all expenses for the specified user.
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_get_expenses (user_id={user_id})")
    return _db.expenses.get_expenses(user_id)

def api_search_expenses(query, user_id):
    """
    Search expenses by title or category for the specified user.
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_search_expenses (query={query}, user_id={user_id})")
    return _db.expenses.search_expenses(query, user_id)

def api_delete_expense(expense_id, user_id):
    """
    Delete an expense by id for the specified user.
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_delete_expense (expense_id={expense_id}, user_id={user_id})")
    return _db.expenses.delete_expense(expense_id, user_id)

def api_clear_expenses(user_id):
    """
    Delete all expenses for the specified user.
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_clear_expenses (user_id={user_id})")
    return _db.expenses.clear_expenses(user_id)

# --- CONTACTS API ---

def api_add_contact(name, user_id):
    """
    Add a new contact for the specified user.
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_add_contact (name={name}, user_id={user_id})")
    return _db.contacts.add_contact(name, user_id)

def api_get_contacts(user_id):
    """
    List all contacts for the specified user.
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_get_contacts (user_id={user_id})")
    return _db.contacts.get_contacts(user_id)

def api_delete_contact(contact_id, user_id):
    """
    Delete a contact by id for the specified user.
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_delete_contact (contact_id={contact_id}, user_id={user_id})")
    return _db.contacts.delete_contact(contact_id, user_id)

# --- TRANSACTIONS API ---

def api_add_transaction(from_user_id, to_user_id, type_, amount, date, description="", contact_id=None):
    """
    Add a new transaction between users.
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_add_transaction (from_user_id={from_user_id}, to_user_id={to_user_id}, type={type_}, amount={amount}, date={date}, description={description}, contact_id={contact_id})")
    return _db.transactions.add_transaction(from_user_id, to_user_id, type_, amount, date, description, contact_id)

def api_get_transactions(user_id, as_sender=True):
    """
    List transactions for the user.
    If as_sender is True, returns transactions sent by the user.
    If False, returns transactions received by the user.
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_get_transactions (user_id={user_id}, as_sender={as_sender})")
    return _db.transactions.get_transactions(user_id, as_sender)

def api_delete_transaction(transaction_id, user_id):
    """
    Delete a transaction by id if the user is the sender.
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_delete_transaction (transaction_id={transaction_id}, user_id={user_id})")
    return _db.transactions.delete_transaction(transaction_id, user_id)

def api_get_user_balance(user_id):
    """
    Get the current balance for a user, aggregating credits/debits.
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_get_user_balance (user_id={user_id})")
    return _db.transactions.get_user_balance(user_id)