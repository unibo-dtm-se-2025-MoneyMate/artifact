from .database import get_connection
from .validation import validate_expense
import logging
import MoneyMate.data_layer.logging_config  # Assicura che la configurazione sia sempre attiva

logger = logging.getLogger(__name__)

class ExpensesManager:
    """
    Manager class for handling expense-related database operations.
    Now supports per-user expense tracking and optional category_id.
    """

    def __init__(self, db_path):
        self.db_path = db_path

    def dict_response(self, success, error=None, data=None):
        return {"success": success, "error": error, "data": data}

    # --- Internal helpers ---
    def _has_column(self, conn, table_name: str, column_name: str) -> bool:
        """
        Return True if the given table has the specified column.
        Useful for backward-compatible behavior across schema versions.
        """
        try:
            cur = conn.cursor()
            cur.execute(f"PRAGMA table_info({table_name});")
            cols = {row[1] for row in cur.fetchall()}
            return column_name in cols
        except Exception as e:
            logger.error(f"Error checking column {column_name} in table {table_name}: {e}")
            return False

    def _category_belongs_to_user(self, conn, category_id: int, user_id: int) -> bool:
        """
        Validate that the category belongs to the user. Returns False if not found.
        """
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM categories WHERE id = ? AND user_id = ?", (category_id, user_id))
            return cur.fetchone() is not None
        except Exception as e:
            logger.error(f"Error validating category_id {category_id} for user {user_id}: {e}")
            return False

    # --- CRUD EXPENSES ---
    def add_expense(self, title, price, date, category, user_id, category_id=None):
        """
        Adds a new expense after validation. Associates expense with user_id.
        Optionally links to categories.id when category_id is provided and the schema supports it.
        """
        err = validate_expense(title, price, date, category)
        if err:
            logger.warning(f"Validation failed for expense '{title}': {err}")
            return self.dict_response(False, err)
        try:
            with get_connection(self.db_path) as conn:
                include_category_fk = self._has_column(conn, "expenses", "category_id")
                if include_category_fk and category_id is not None:
                    # Validate that category_id belongs to the same user
                    if not self._category_belongs_to_user(conn, category_id, user_id):
                        logger.warning(f"Expense validation failed: category_id {category_id} does not belong to user {user_id}.")
                        return self.dict_response(False, "Invalid category for this user")
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO expenses (title, price, date, category, user_id, category_id) VALUES (?, ?, ?, ?, ?, ?)",
                        (title, price, date, category, user_id, category_id)
                    )
                else:
                    # Backward-compatible path (no category_id column or not provided)
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
        Includes category_id if supported by schema.
        """
        try:
            with get_connection(self.db_path) as conn:
                include_category_fk = self._has_column(conn, "expenses", "category_id")
                if include_category_fk:
                    select_sql = "SELECT id, title, price, date, category, category_id FROM expenses WHERE user_id = ?"
                else:
                    select_sql = "SELECT id, title, price, date, category FROM expenses WHERE user_id = ?"
                cursor = conn.cursor()
                cursor.execute(select_sql, (user_id,))
                rows = cursor.fetchall()
            expenses = []
            for r in rows:
                base = {"id": r[0], "title": r[1], "price": r[2], "date": r[3], "category": r[4]}
                if len(r) > 5:  # category_id present
                    base["category_id"] = r[5]
                expenses.append(base)
            logger.info(f"Retrieved {len(expenses)} expenses for user {user_id}.")
            return self.dict_response(True, data=expenses)
        except Exception as e:
            logger.error(f"Error retrieving expenses for user {user_id}: {e}")
            return self.dict_response(False, str(e))

    def search_expenses(self, query, user_id):
        """
        Searches expenses by title or category, filtered by user.
        Includes category_id if supported by schema.
        """
        try:
            with get_connection(self.db_path) as conn:
                include_category_fk = self._has_column(conn, "expenses", "category_id")
                if include_category_fk:
                    select_sql = (
                        "SELECT id, title, price, date, category, category_id "
                        "FROM expenses WHERE user_id = ? AND (title LIKE ? OR category LIKE ?)"
                    )
                else:
                    select_sql = (
                        "SELECT id, title, price, date, category "
                        "FROM expenses WHERE user_id = ? AND (title LIKE ? OR category LIKE ?)"
                    )
                cursor = conn.cursor()
                cursor.execute(select_sql, (user_id, f"%{query}%", f"%{query}%"))
                rows = cursor.fetchall()
            expenses = []
            for r in rows:
                base = {"id": r[0], "title": r[1], "price": r[2], "date": r[3], "category": r[4]}
                if len(r) > 5:  # category_id present
                    base["category_id"] = r[5]
                expenses.append(base)
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