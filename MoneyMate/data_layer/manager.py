"""
DatabaseManager: Central orchestrator for entity managers in MoneyMate.

This class instantiates and exposes managers for expenses, contacts, and transactions,
ensuring modularity, single responsibility and testability. All data operations should be accessed 
through the appropriate manager instance.

Design principles:
- Each manager (ExpensesManager, ContactsManager, TransactionsManager) is isolated in its own file.
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
"""

from .database import DB_PATH, list_tables, init_db
from .expenses import ExpensesManager
from .contacts import ContactsManager
from .transactions import TransactionsManager

class DatabaseManager:
    """
    Central orchestrator for entity managers.
    Provides a unified interface for all data operations.
    """
    def close(self):
        """
        Release all entity managers for test cleanup.
        """
        self.expenses = None
        self.contacts = None
        self.transactions = None
    
    def __init__(self, db_path=DB_PATH):
        # Initialize the database and managers
        init_db(db_path)
        self.expenses = ExpensesManager(db_path)
        self.contacts = ContactsManager(db_path)
        self.transactions = TransactionsManager(db_path, self.contacts)

    def _create_managers(self, db_path):
        """
        Private method that creates and re-instantiates all entity managers
        with the new database path.
        This is used when changing the database path at runtime.
        """
        self.expenses = ExpensesManager(db_path)
        self.contacts = ContactsManager(db_path)
        self.transactions = TransactionsManager(db_path, self.contacts)

    def list_tables(self):
        """
        List all tables in the database.
        Useful for testing and diagnostics.
        """
        return list_tables(db_path=self.expenses.db_path)
    

    def set_db_path(self, db_path):
        """
        Set a new database path and re-initialize all managers to use it.
        """
        self.db_path = db_path
        init_db(db_path)
        self._create_managers(db_path)