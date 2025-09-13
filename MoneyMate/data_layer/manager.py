"""
DatabaseManager: Central orchestrator for entity managers in MoneyMate.

This class instantiates and exposes managers for expenses, contacts, transactions, and users,
ensuring modularity, single responsibility, dependency injection, configurability, error handling, resource management, and testability.
All data operations should be accessed through the appropriate manager instance.
"""

from typing import Any, Dict, Optional
import sqlite3
from .database import DB_PATH, list_tables
from .logging_config import get_logger

logger = get_logger(__name__)


def init_db(db_path: str):
    """
    Create all required tables if they don't already exist.
    Tests expect at least: contacts, expenses, transactions, users, access_logs.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # USERS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    """)

    # CONTACTS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name, user_id),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # EXPENSES
    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titolo TEXT NOT NULL,
            prezzo REAL NOT NULL,
            data TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # TRANSACTIONS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            contact_id INTEGER,
            amount REAL NOT NULL,
            type TEXT CHECK(type IN ('debit','credit')) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(sender_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(receiver_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(contact_id) REFERENCES contacts(id) ON DELETE SET NULL
        )
    """)

    # ACCESS LOGS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


def dict_response(success: bool, error: Optional[str] = None, data: Any = None) -> Dict[str, Any]:
    """
    Standardized response format used across all managers.
    """
    return {"success": success, "error": error, "data": data}


class DatabaseManager:
    """
    Central orchestrator for entity managers.
    Provides a unified interface for all data operations.
    """

    def __init__(self, db_path: str = DB_PATH):
        logger.info(f"Initializing DatabaseManager with db_path: {db_path}")
        self.db_path: str = db_path
        self._keeper: Optional[sqlite3.Connection] = None

        # Keeper connection for shared in-memory database
        if isinstance(db_path, str) and db_path.startswith("file:") and "mode=memory" in db_path:
            try:
                self._keeper = sqlite3.connect(db_path, uri=True, check_same_thread=False)
                self._keeper.execute("PRAGMA foreign_keys = ON;")
                logger.info("Keeper connection established for shared in-memory database.")
            except Exception as e:
                logger.warning(f"Failed to create keeper connection for in-memory DB: {e}")

        # Initialize DB and managers
        init_db(db_path)
        self._init_managers()

    def _init_managers(self):
        """
        Lazy imports to avoid circular dependencies.
        Initializes all managers with db_manager reference if needed.
        """
        from .expenses import ExpensesManager
        from .contacts import ContactsManager
        from .transactions import TransactionsManager
        from .usermanager import UserManager
        from .categories import CategoriesManager

        self.expenses = ExpensesManager(self.db_path, db_manager=self)
        self.contacts = ContactsManager(self.db_path, db_manager=self)
        self.transactions = TransactionsManager(self.db_path, self.contacts, db_manager=self)
        self.users = UserManager(self.db_path, db_manager=self)
        self.categories = CategoriesManager(self.db_path, db_manager=self)

    def __enter__(self) -> "DatabaseManager":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        try:
            self.close()
        except Exception:
            pass
        return False

    def close(self) -> None:
        logger.info("Releasing all managers for test cleanup.")
        self.expenses = None
        self.contacts = None
        self.transactions = None
        self.users = None
        self.categories = None
        if getattr(self, "_keeper", None):
            try:
                self._keeper.close()
            except Exception:
                pass
            finally:
                self._keeper = None

    def list_tables(self):
        """
        Return the raw list of tables (as tests expect).
        """
        try:
            tables = list_tables(self.db_path)
            if isinstance(tables, dict):
                return tables.get("tables", [])
            return tables
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            return []

    def set_db_path(self, db_path: str) -> None:
        logger.info(f"Setting new db_path: {db_path} and re-initializing managers.")
        if getattr(self, "_keeper", None):
            try:
                self._keeper.close()
            except Exception:
                pass
            finally:
                self._keeper = None

        self.db_path = db_path

        if isinstance(db_path, str) and db_path.startswith("file:") and "mode=memory" in db_path:
            try:
                self._keeper = sqlite3.connect(db_path, uri=True, check_same_thread=False)
                self._keeper.execute("PRAGMA foreign_keys = ON;")
                logger.info("Keeper connection established for shared in-memory database (after path change).")
            except Exception as e:
                logger.warning(f"Failed to create keeper connection for in-memory DB: {e}")

        init_db(db_path)
        self._init_managers()

    # ----------------------------
    # Expense methods
    # ----------------------------
    def add_expense(self, *args, **kwargs):
        try:
            return self.expenses.add_expense(*args, **kwargs)
        except Exception as e:
            logger.error(f"add_expense failed: {e}")
            return dict_response(False, str(e))

    def delete_expense(self, *args, **kwargs):
        try:
            return self.expenses.delete_expense(*args, **kwargs)
        except Exception as e:
            logger.error(f"delete_expense failed: {e}")
            return dict_response(False, str(e))

    def search_expenses(self, *args, **kwargs):
        try:
            return self.expenses.search_expenses(*args, **kwargs)
        except Exception as e:
            logger.error(f"search_expenses failed: {e}")
            return dict_response(False, str(e))

    def get_expenses(self, *args, **kwargs):
        try:
            return self.expenses.get_expenses(*args, **kwargs)
        except Exception as e:
            logger.error(f"get_expenses failed: {e}")
            return dict_response(False, str(e))

    def clear_expenses(self, *args, **kwargs):
        try:
            return self.expenses.clear_expenses(*args, **kwargs)
        except Exception as e:
            logger.error(f"clear_expenses failed: {e}")
            return dict_response(False, str(e))

    # ----------------------------
    # Contact methods
    # ----------------------------
    def add_contact(self, *args, **kwargs):
        try:
            return self.contacts.add_contact(*args, **kwargs)
        except Exception as e:
            logger.error(f"add_contact failed: {e}")
            return dict_response(False, str(e))

    def delete_contact(self, *args, **kwargs):
        try:
            return self.contacts.delete_contact(*args, **kwargs)
        except Exception as e:
            logger.error(f"delete_contact failed: {e}")
            return dict_response(False, str(e))

    def get_contacts(self, *args, **kwargs):
        try:
            return self.contacts.get_contacts(*args, **kwargs)
        except Exception as e:
            logger.error(f"get_contacts failed: {e}")
            return dict_response(False, str(e))

    # ----------------------------
    # Transaction methods
    # ----------------------------
    def add_transaction(self, *args, **kwargs):
        try:
            return self.transactions.add_transaction(*args, **kwargs)
        except Exception as e:
            logger.error(f"add_transaction failed: {e}")
            return dict_response(False, str(e))

    def delete_transaction(self, *args, **kwargs):
        try:
            return self.transactions.delete_transaction(*args, **kwargs)
        except Exception as e:
            logger.error(f"delete_transaction failed: {e}")
            return dict_response(False, str(e))

    def get_contact_balance(self, *args, **kwargs):
        try:
            return self.transactions.get_contact_balance(*args, **kwargs)
        except Exception as e:
            logger.error(f"get_contact_balance failed: {e}")
            return dict_response(False, str(e))

