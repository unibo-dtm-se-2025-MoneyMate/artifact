"""
DatabaseManager: Central orchestrator for entity managers in MoneyMate.

This class instantiates and exposes managers for expenses, contacts, transactions, and users,
ensuring modularity, single responsibility, dependency injection, configurability, error handling, resource management, and testability.
All data operations should be accessed through the appropriate manager instance.
"""

from typing import Any, Dict, Optional
import sqlite3
from .database import DB_PATH, list_tables, init_db
from .logging_config import get_logger

logger = get_logger(__name__)


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
        Return the dict response format (as the working tests expect).
        """
        try:
            return list_tables(self.db_path)
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            return {"success": False, "error": str(e), "data": []}

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

