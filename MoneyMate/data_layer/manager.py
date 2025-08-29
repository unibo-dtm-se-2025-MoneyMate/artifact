"""
DatabaseManager: Central orchestrator for entity managers in MoneyMate.

This class instantiates and exposes managers for expenses, contacts, transactions, and users,
ensuring modularity, single responsibility, dependency injection, configurability, error handling, resource management, and testability.
All data operations should be accessed through the appropriate manager instance.

Design principles:
- Each manager (ExpensesManager, ContactsManager, TransactionsManager, UserManager) is isolated in its own file.
- ContactsManager is injected into TransactionsManager to handle cross-entity validation.
- Database path is configurable for production and testing environments.
- Utility methods such as list_tables are accessible for maintenance and health checks.
- This approach follows best practices for software architecture, avoiding code duplication,
  supporting future scalability, and facilitating CI/CD workflows (e.g. GitHub Actions).

Usage:
    db = DatabaseManager()
    db.expenses.add_expense(...)
    db.contacts.get_contacts()
    db.transactions.get_contact_balance(...)
    db.users.register_user(...)
    db.users.change_password(...)
    db.users.reset_password(...)
    db.users.get_user_role(...)
    db.users.set_user_role(...)
"""

from .database import DB_PATH, list_tables, init_db
from .expenses import ExpensesManager
from .contacts import ContactsManager
from .transactions import TransactionsManager
from .usermanager import UserManager
import logging
import MoneyMate.data_layer.logging_config  # Ensure global logging configuration

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Central orchestrator for entity managers.
    Provides a unified interface for all data operations.
    """
    def close(self):
        """
        Release all entity managers for test cleanup.
        """
        logger.info("Releasing all managers for test cleanup.")
        self.expenses = None
        self.contacts = None
        self.transactions = None
        self.users = None

    def __init__(self, db_path=DB_PATH):
        # Initialize the database and managers
        logger.info(f"Initializing DatabaseManager with db_path: {db_path}")
        init_db(db_path)
        self.expenses = ExpensesManager(db_path)
        self.contacts = ContactsManager(db_path)
        self.transactions = TransactionsManager(db_path, self.contacts)
        self.users = UserManager(db_path)

    def _create_managers(self, db_path):
        """
        Private method that creates and re-instantiates all entity managers
        with the new database path.
        This is used when changing the database path at runtime.
        """
        logger.info(f"Re-creating managers with new db_path: {db_path}")
        self.expenses = ExpensesManager(db_path)
        self.contacts = ContactsManager(db_path)
        self.transactions = TransactionsManager(db_path, self.contacts)
        self.users = UserManager(db_path)

    def list_tables(self):
        """
        List all tables in the database.
        Useful for testing and diagnostics.
        """
        logger.info(f"Listing tables for db_path: {self.expenses.db_path}")
        return list_tables(db_path=self.expenses.db_path)
    

    def set_db_path(self, db_path):
        """
        Set a new database path and re-initialize all managers to use it.
        """
        logger.info(f"Setting new db_path: {db_path} and re-initializing managers.")
        self.db_path = db_path
        init_db(db_path)
        self._create_managers(db_path)