"""
api.py
Unified API interface for MoneyMate data layer, using DatabaseManager.

This module provides high-level functions to interact with expenses,
contacts, transactions, and users, wrapping DatabaseManager methods.
Each function returns a standardized dictionary response.

Now supports user-scoped operations for expenses, contacts, and transactions,
including tracking transactions/credit between users.

Extended:
- User roles (admin/user): admin can view all transactions
- Admin registration policy: enforced in UserManager (password '12345')
- API now forwards 'role' to user registration and 'is_admin' to transactions listing
- Optional category_id for expenses (backward compatible)
- Deterministic ordering and optional pagination/filtering for listings
- Thread-safe DatabaseManager singleton via double-checked locking
- Update APIs for expenses and transactions
- Contact balance API for user+contact breakdown
"""


import threading
from .database import init_db, list_tables
from .manager import DatabaseManager

from .logging_config import get_logger
logger = get_logger(__name__)

_db = None
_db_lock = threading.Lock()

def get_db():
    """
    Return a process-wide DatabaseManager instance.
    Thread-safe (double-checked locking).
    """
    global _db
    if _db is None:
        with _db_lock:
            if _db is None:
                logger.info("Creating new DatabaseManager instance with default DB path.")
                _db = DatabaseManager()
    return _db

def set_db_path(db_path):
    """
    Set the database path for the API module.
    This allows tests or other modules to use a custom database file.
    If db_path is None, releases the global _db reference for proper cleanup.
    Thread-safe with the same lock used in get_db.
    """
    global _db
    with _db_lock:
        if db_path is None:
            logger.info("Releasing DatabaseManager instance (cleanup).")
            try:
                if _db is not None and hasattr(_db, "close"):
                    _db.close()
            finally:
                _db = None
        else:
            logger.info(f"Setting DatabaseManager db_path to: {db_path}")
            # Close existing manager (if any) before swapping
            if _db is not None and hasattr(_db, "close"):
                _db.close()
            _db = DatabaseManager(db_path)

# --- UTILITY ---

def api_list_tables():
    """
    List all tables in the database.
    Returns: dict {success, error, data}
    """
    logger.info("API call: api_list_tables")
    return get_db().list_tables()

def api_health(): 
    """
    Lightweight health check for GUI integration.
    Returns: dict {success, error, data: int (schema_version)}
    """
    logger.info("API call: api_health")
    from .database import get_schema_version  # import relativo corretto

    # Use the current db_path from the manager to read version
    db = get_db()
    version_resp = get_schema_version(db.db_path)
    return version_resp


# --- USERS API ---

def api_register_user(username, password, role="user"):
    """
    Register a new user.
    Role defaults to 'user'. For 'admin', UserManager enforces password '12345'.
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_register_user (username={username}, role={role})")
    return get_db().users.register_user(username, password, role)

def api_login_user(username, password, ip_address=None, user_agent=None):
    """
    Authenticate a user.
    Optionally records ip_address and user_agent to access_logs for auditing.
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_login_user (username={username})")
    return get_db().users.login_user(username, password, ip_address=ip_address, user_agent=user_agent)

def api_logout_user(user_id, ip_address=None, user_agent=None):
    """
    Log a user logout event into access_logs (best-effort).
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_logout_user (user_id={user_id})")
    return get_db().users.logout_user(user_id, ip_address=ip_address, user_agent=user_agent)

# Optional high-level APIs for user management (not required by current tests)
def api_change_password(user_id, old_password, new_password):
    logger.info(f"API call: api_change_password (user_id={user_id})")
    return get_db().users.change_password(user_id, old_password, new_password)

def api_reset_password(admin_user_id, target_user_id, new_password):
    logger.info(f"API call: api_reset_password (admin_user_id={admin_user_id}, target_user_id={target_user_id})")
    return get_db().users.reset_password(admin_user_id, target_user_id, new_password)

def api_get_user_role(user_id):
    logger.info(f"API call: api_get_user_role (user_id={user_id})")
    return get_db().users.get_user_role(user_id)

def api_set_user_role(admin_user_id, target_user_id, new_role):
    logger.info(f"API call: api_set_user_role (admin_user_id={admin_user_id}, target_user_id={target_user_id}, new_role={new_role})")
    return get_db().users.set_user_role(admin_user_id, target_user_id, new_role)

# --- CATEGORIES API (optional, for GUI management) ---

def api_add_category(user_id, name, description=None, color=None, icon=None):
    """
    Add a new category for the specified user.
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_add_category (user_id={user_id}, name={name})")
    return get_db().categories.add_category(user_id, name, description, color, icon)

def api_get_categories(user_id, order="name_asc", limit=None, offset=None):
    """
    List categories for the specified user.
    Optional ordering and pagination.
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_get_categories (user_id={user_id}, order={order}, limit={limit}, offset={offset})")
    return get_db().categories.get_categories(user_id, order=order, limit=limit, offset=offset)

def api_delete_category(category_id, user_id):
    """
    Delete a category by id for the specified user.
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_delete_category (category_id={category_id}, user_id={user_id})")
    return get_db().categories.delete_category(category_id, user_id)

# --- EXPENSES API ---

def api_add_expense(title, price, date, category, user_id, category_id=None):
    """
    Add a new expense for the specified user.
    Optional category_id (FK to categories) is supported if present in schema.
    Returns: dict {success, error, data}
    """
    logger.info(
        f"API call: api_add_expense (title={title}, price={price}, date={date}, "
        f"category={category}, user_id={user_id}, category_id={category_id})"
    )
    return get_db().expenses.add_expense(title, price, date, category, user_id, category_id=category_id)

def api_update_expense(expense_id, user_id, title=None, price=None, date=None, category=None, category_id=None):
    """
    Update an existing expense (partial updates allowed) if it belongs to the user.
    Returns: dict {success, error, data: {'updated': int}}
    """
    logger.info(
        f"API call: api_update_expense (expense_id={expense_id}, user_id={user_id}, "
        f"title={title}, price={price}, date={date}, category={category}, category_id={category_id})"
    )
    return get_db().expenses.update_expense(expense_id, user_id, title=title, price=price, date=date, category=category, category_id=category_id)

def api_get_expenses(user_id, order="date_desc", limit=None, offset=None, date_from=None, date_to=None):
    """
    List all expenses for the specified user.
    Optional ordering, pagination, and date range filtering.
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_get_expenses (user_id={user_id}, order={order}, limit={limit}, offset={offset}, date_from={date_from}, date_to={date_to})")
    return get_db().expenses.get_expenses(user_id, order=order, limit=limit, offset=offset, date_from=date_from, date_to=date_to)

def api_search_expenses(query, user_id, order="date_desc", limit=None, offset=None, date_from=None, date_to=None):
    """
    Search expenses by title or category for the specified user.
    Case-insensitive search. Optional ordering, pagination, and date range.
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_search_expenses (query={query}, user_id={user_id}, order={order}, limit={limit}, offset={offset}, date_from={date_from}, date_to={date_to})")
    return get_db().expenses.search_expenses(query, user_id, order=order, limit=limit, offset=offset, date_from=date_from, date_to=date_to)

def api_delete_expense(expense_id, user_id):
    """
    Delete an expense by id for the specified user.
    Returns: dict {success, error, data: {'deleted': int}}
    """
    logger.info(f"API call: api_delete_expense (expense_id={expense_id}, user_id={user_id})")
    return get_db().expenses.delete_expense(expense_id, user_id)

def api_clear_expenses(user_id):
    """
    Delete all expenses for the specified user.
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_clear_expenses (user_id={user_id})")
    return get_db().expenses.clear_expenses(user_id)

# --- CONTACTS API ---

def api_add_contact(name, user_id):
    """
    Add a new contact for the specified user.
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_add_contact (name={name}, user_id={user_id})")
    return get_db().contacts.add_contact(name, user_id)

def api_get_contacts(user_id, order="name_asc"):
    """
    List all contacts for the specified user.
    Optional ordering.
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_get_contacts (user_id={user_id}, order={order})")
    return get_db().contacts.get_contacts(user_id, order=order)

def api_delete_contact(contact_id, user_id):
    """
    Delete a contact by id for the specified user.
    Returns: dict {success, error, data: {'deleted': int}}
    """
    logger.info(f"API call: api_delete_contact (contact_id={contact_id}, user_id={user_id})")
    return get_db().contacts.delete_contact(contact_id, user_id)

# --- TRANSACTIONS API ---

def api_add_transaction(from_user_id, to_user_id, type_, amount, date, description="", contact_id=None):
    """
    Add a new transaction between users.
    Returns: dict {success, error, data}
    """
    logger.info(
        f"API call: api_add_transaction (from_user_id={from_user_id}, to_user_id={to_user_id}, "
        f"type={type_}, amount={amount}, date={date}, description={description}, contact_id={contact_id})"
    )
    return get_db().transactions.add_transaction(from_user_id, to_user_id, type_, amount, date, description, contact_id)

def api_update_transaction(transaction_id, user_id, type_=None, amount=None, date=None, description=None, contact_id=None):
    """
    Update a transaction if the user is the sender (partial updates allowed).
    Returns: dict {success, error, data: {'updated': int}}
    """
    logger.info(
        f"API call: api_update_transaction (transaction_id={transaction_id}, user_id={user_id}, "
        f"type={type_}, amount={amount}, date={date}, description={description}, contact_id={contact_id})"
    )
    return get_db().transactions.update_transaction(transaction_id, user_id, type_=type_, amount=amount, date=date, description=description, contact_id=contact_id)

def api_get_transactions(user_id, as_sender=True, is_admin=False, order="date_desc", limit=None, offset=None, date_from=None, date_to=None, contact_id=None):
    """
    List transactions for the user.
    If is_admin is True, returns all transactions in the system (validated by data layer).
    Otherwise:
      - If as_sender is True, returns transactions sent by the user.
      - If False, returns transactions received by the user.
    Optional ordering, pagination, date range, and contact filter.
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_get_transactions (user_id={user_id}, as_sender={as_sender}, is_admin={is_admin}, order={order}, limit={limit}, offset={offset}, date_from={date_from}, date_to={date_to}, contact_id={contact_id})")
    return get_db().transactions.get_transactions(user_id, as_sender=as_sender, is_admin=is_admin, order=order, limit=limit, offset=offset, date_from=date_from, date_to=date_to, contact_id=contact_id)

def api_delete_transaction(transaction_id, user_id):
    """
    Delete a transaction by id if the user is the sender.
    Returns: dict {success, error, data: {'deleted': int}}
    """
    logger.info(f"API call: api_delete_transaction (transaction_id={transaction_id}, user_id={user_id})")
    return get_db().transactions.delete_transaction(transaction_id, user_id)

def api_get_user_balance(user_id):
    """
    Get the current balance for a user (LEGACY semantics: credit - debit over all tx where user is sender or receiver).
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_get_user_balance (user_id={user_id})")
    return get_db().transactions.get_user_balance(user_id)

def api_get_user_net_balance(user_id):
    """
    Get the NET balance for a user (recommended for GUI): credits_received - debits_sent.
    Returns: dict {success, error, data}
    """
    logger.info(f"API call: api_get_user_net_balance (user_id={user_id})")
    return get_db().transactions.get_user_net_balance(user_id)

def api_get_user_balance_breakdown(user_id):
    """
    Get a detailed balance breakdown for a user.
    Returns: dict {success, error, data: {credits_received, debits_sent, credits_sent, debits_received, net, legacy}}
    """
    logger.info(f"API call: api_get_user_balance_breakdown (user_id={user_id})")
    return get_db().transactions.get_user_balance_breakdown(user_id)

def api_get_contact_balance(user_id, contact_id):
    """
    Get balance breakdown for a specific contact from the sender's perspective
    (only transactions where the user is sender and contact_id matches).
    Returns: dict {success, error, data: {credits_sent, debits_sent, net}}
    """
    logger.info(f"API call: api_get_contact_balance (user_id={user_id}, contact_id={contact_id})")
    return get_db().transactions.get_contact_balance(user_id, contact_id)