from .database import get_connection
from .validation import validate_expense
import logging
import MoneyMate.data_layer.logging_config  # Assicura che la configurazione sia sempre attiva

logger = logging.getLogger(__name__)

class ExpensesManager:
    """
    Manager class for handling expense-related database operations.
    Each method maintains the original logic and comments for clarity and testing.
    """

    def __init__(self, db_path):
        self.db_path = db_path

    def dict_response(self, success, error=None, data=None):
        """Return a standardized dictionary for all API responses."""
        return {"success": success, "error": error, "data": data}

    # --- CRUD EXPENSES ---
    def add_expense(self, title, price, date, category):
        """
        Adds a new expense after validation.
        Uses a context manager for DB connection for safe resource handling.
        """
        err = validate_expense(title, price, date, category)
        if err:
            logger.warning(f"Validation failed for expense '{title}': {err}")
            return self.dict_response(False, err)
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO expenses (title, price, date, category) VALUES (?, ?, ?, ?)",
                    (title, price, date, category)
                )
                conn.commit()
            logger.info(f"Expense '{title}' added successfully.")
            return self.dict_response(True)
        except Exception as e:
            logger.error(f"Error adding expense '{title}': {e}")
            return self.dict_response(False, str(e))

    def get_expenses(self):
        """
        Returns all expenses as a list of dicts.
        Uses a context manager for DB connection.
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, title, price, date, category FROM expenses")
                rows = cursor.fetchall()
            expenses = [
                {"id": r[0], "title": r[1], "price": r[2], "date": r[3], "category": r[4]}
                for r in rows
            ]
            logger.info(f"Retrieved {len(expenses)} expenses from the database.")
            return self.dict_response(True, data=expenses)
        except Exception as e:
            logger.error(f"Error retrieving expenses: {e}")
            return self.dict_response(False, str(e))

    def search_expenses(self, query):
        """
        Searches expenses by title or category.
        Uses a context manager for DB connection.
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, title, price, date, category FROM expenses WHERE title LIKE ? OR category LIKE ?",
                    (f"%{query}%", f"%{query}%")
                )
                rows = cursor.fetchall()
            expenses = [
                {"id": r[0], "title": r[1], "price": r[2], "date": r[3], "category": r[4]}
                for r in rows
            ]
            logger.info(f"Searched expenses with query '{query}': found {len(expenses)} results.")
            return self.dict_response(True, data=expenses)
        except Exception as e:
            logger.error(f"Error searching expenses with query '{query}': {e}")
            return self.dict_response(False, str(e))

    def delete_expense(self, expense_id):
        """
        Deletes a specific expense by ID.
        Uses a context manager for DB connection.
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
                conn.commit()
            logger.info(f"Deleted expense with ID {expense_id}.")
            return self.dict_response(True)
        except Exception as e:
            logger.error(f"Error deleting expense with ID {expense_id}: {e}")
            return self.dict_response(False, str(e))

    def clear_expenses(self):
        """
        Deletes all expenses from the table.
        Uses a context manager for DB connection.
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM expenses")
                conn.commit()
            logger.info("Cleared all expenses from the database.")
            return self.dict_response(True)
        except Exception as e:
            logger.error(f"Error clearing expenses: {e}")
            return self.dict_response(False, str(e))