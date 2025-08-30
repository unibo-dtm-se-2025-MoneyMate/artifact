"""
DatabaseManager: Central orchestrator for entity managers in MoneyMate.

This class instantiates and exposes managers for expenses, contacts, transactions, and users,
ensuring modularity, single responsibility, dependency injection, configurability, error handling, resource management, and testability.
All data operations should be accessed through the appropriate manager instance.
"""

from typing import Any, Dict, Optional
from .database import DB_PATH, list_tables, init_db
from .expenses import ExpensesManager
from .contacts import ContactsManager
from .transactions import TransactionsManager
from .usermanager import UserManager
from .categories import CategoriesManager
import logging
import sqlite3
import MoneyMate.data_layer.logging_config  # Ensure global logging configuration

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Central orchestrator for entity managers.
    Provides a unified interface for all data operations.
    """

    def __enter__(self) -> "DatabaseManager":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        try:
            self.close()
        except Exception:
            pass
        return False  # don't suppress exceptions

    def close(self) -> None:
        """
        Release all entity managers for test cleanup.
        """
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

    def __init__(self, db_path: str = DB_PATH):
        logger.info(f"Initializing DatabaseManager with db_path: {db_path}")
        self.db_path: str = db_path

        self._keeper: Optional[sqlite3.Connection] = None
        if isinstance(db_path, str) and db_path.startswith("file:") and "mode=memory" in db_path:
            try:
                self._keeper = sqlite3.connect(db_path, uri=True, check_same_thread=False)
                self._keeper.execute("PRAGMA foreign_keys = ON;")
                logger.info("Keeper connection established for shared in-memory database.")
            except Exception as e:
                logger.warning(f"Failed to create keeper connection for in-memory DB: {e}")

        init_db(db_path)
        self.expenses = ExpensesManager(db_path)
        self.contacts = ContactsManager(db_path)
        self.transactions = TransactionsManager(db_path, self.contacts)
        self.users = UserManager(db_path)
        self.categories = CategoriesManager(db_path)

    def _create_managers(self, db_path: str) -> None:
        """
        Private method that creates and re-instantiates all entity managers
        with the new database path.
        """
        logger.info(f"Re-creating managers with new db_path: {db_path}")
        self.expenses = ExpensesManager(db_path)
        self.contacts = ContactsManager(db_path)
        self.transactions = TransactionsManager(db_path, self.contacts)
        self.users = UserManager(db_path)
        self.categories = CategoriesManager(db_path)

    def list_tables(self) -> Dict[str, Any]:
        """
        List all tables in the database.
        Useful for testing and diagnostics.
        """
        logger.info(f"Listing tables for db_path: {self.db_path}")
        return list_tables(db_path=self.db_path)

    def set_db_path(self, db_path: str) -> None:
        """
        Set a new database path and re-initialize all managers to use it.
        """
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
        self._create_managers(db_path)