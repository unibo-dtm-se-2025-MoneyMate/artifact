from .database import get_connection
from .validation import validate_expense
import logging
import MoneyMate.data_layer.logging_config  # Assicura che la configurazione sia sempre attiva

logger = logging.getLogger(__name__)

class ExpensesManager:
    """
    Manager class for handling expense-related database operations.
    Now supports per-user expense tracking.
    """

    def __init__(self, db_path):
        self.db_path = db_path

    def dict_response(self, success, error=None, data=None):
        return {"success": success, "error": error, "data": data}

    # --- CRUD EXPENSES ---
    def add_expense(self, title, price, date, category, user_id):
        """
        Adds a new expense after validation. Associates expense with user_id.
        """
        err = validate_expense(title, price, date, category)
        if err:
            logger.warning(f"Validation failed for expense '{title}': {err}")
            return self.dict_response(False, err)
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO expenses (title, price, date, category, user_id) VALUES (?, ?, ?, ?, ?)",
                    (title, price, date, category, user_id)
                )
                conn.commit()
            logger.info(f"Expense '{title}' added for user {user_id}.")
            return self.dict_response(True)
        except Exception as e:
            logger.error(f"Error adding expense '{title}': {e}")
            return self.dict_response(False, str(e))

    def get_expenses(self, user_id):
        """
        Returns all expenses for a specific user as a list of dicts.
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, title, price, date, category FROM expenses WHERE user_id = ?",
                    (user_id,)
                )
                rows = cursor.fetchall()
            expenses = [
                {"id": r[0], "title": r[1], "price": r[2], "date": r[3], "category": r[4]}
                for r in rows
            ]
            logger.info(f"Retrieved {len(expenses)} expenses for user {user_id}.")
            return self.dict_response(True, data=expenses)
        except Exception as e:
            logger.error(f"Error retrieving expenses for user {user_id}: {e}")
            return self.dict_response(False, str(e))

    def search_expenses(self, query, user_id):
        """
        Searches expenses by title or category, filtered by user.
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, title, price, date, category FROM expenses WHERE user_id = ? AND (title LIKE ? OR category LIKE ?)",
                    (user_id, f"%{query}%", f"%{query}%")
                )
                rows = cursor.fetchall()
            expenses = [
                {"id": r[0], "title": r[1], "price": r[2], "date": r[3], "category": r[4]}
                for r in rows
            ]
            logger.info(f"Searched expenses for user {user_id} with query '{query}': found {len(expenses)} results.")
            return self.dict_response(True, data=expenses)
        except Exception as e:
            logger.error(f"Error searching expenses for user {user_id} with query '{query}': {e}")
            return self.dict_response(False, str(e))

    def delete_expense(self, expense_id, user_id):
        """
        Deletes a specific expense by ID, only if it belongs to the user.
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user_id))
                conn.commit()
            logger.info(f"Deleted expense with ID {expense_id} for user {user_id}.")
            return self.dict_response(True)
        except Exception as e:
            logger.error(f"Error deleting expense with ID {expense_id} for user {user_id}: {e}")
            return self.dict_response(False, str(e))

    def clear_expenses(self, user_id):
        """
        Deletes all expenses from the table for a user.
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM expenses WHERE user_id = ?", (user_id,))
                conn.commit()
            logger.info(f"Cleared all expenses for user {user_id}.")
            return self.dict_response(True)
        except Exception as e:
            logger.error(f"Error clearing expenses for user {user_id}: {e}")
            return self.dict_response(False, str(e))