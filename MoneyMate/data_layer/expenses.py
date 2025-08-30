from .database import get_connection
from .validation import validate_expense
import logging
import MoneyMate.data_layer.logging_config  # Assicura che la configurazione sia sempre attiva

logger = logging.getLogger(__name__)

def _order_clause(order: str) -> str:
    mapping = {
        "date_desc": "ORDER BY date DESC, id DESC",
        "date_asc": "ORDER BY date ASC, id ASC",
        "created_desc": "ORDER BY created_at DESC, id DESC",
        "created_asc": "ORDER BY created_at ASC, id ASC",
    }
    return mapping.get((order or "date_desc"), mapping["date_desc"])

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
                cursor = conn.cursor()
                if include_category_fk and category_id is not None:
                    # Validate that category_id belongs to the same user
                    if not self._category_belongs_to_user(conn, category_id, user_id):
                        logger.warning(f"Expense validation failed: category_id {category_id} does not belong to user {user_id}.")
                        return self.dict_response(False, "Invalid category for this user")
                    cursor.execute(
                        "INSERT INTO expenses (title, price, date, category, user_id, category_id) VALUES (?, ?, ?, ?, ?, ?)",
                        (title, price, date, category, user_id, category_id)
                    )
                else:
                    # Backward-compatible path (no category_id column or not provided)
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

    def get_expenses(self, user_id, order="date_desc", limit=None, offset=None, date_from=None, date_to=None):
        """
        Returns all expenses for a specific user as a list of dicts.
        Includes category_id if supported by schema.
        Supports deterministic ordering, pagination, and optional date range filtering.
        """
        try:
            with get_connection(self.db_path) as conn:
                include_category_fk = self._has_column(conn, "expenses", "category_id")
                select_cols = "id, title, price, date, category" + (", category_id" if include_category_fk else "")
                where = ["user_id = ?"]
                params = [user_id]
                if date_from:
                    where.append("date >= ?")
                    params.append(date_from)
                if date_to:
                    where.append("date <= ?")
                    params.append(date_to)
                where_sql = " WHERE " + " AND ".join(where)
                sql = f"SELECT {select_cols} FROM expenses{where_sql} {_order_clause(order)}"
                if limit is not None:
                    sql += " LIMIT ?"
                    params.append(int(limit))
                    if offset is not None:
                        sql += " OFFSET ?"
                        params.append(int(offset))
                cursor = conn.cursor()
                cursor.execute(sql, tuple(params))
                rows = cursor.fetchall()
            expenses = []
            for r in rows:
                base = {"id": r["id"], "title": r["title"], "price": r["price"], "date": r["date"], "category": r["category"]}
                if include_category_fk:
                    base["category_id"] = r["category_id"]
                expenses.append(base)
            logger.info(f"Retrieved {len(expenses)} expenses for user {user_id}.")
            return self.dict_response(True, data=expenses)
        except Exception as e:
            logger.error(f"Error retrieving expenses for user {user_id}: {e}")
            return self.dict_response(False, str(e))

    def search_expenses(self, query, user_id, order="date_desc", limit=None, offset=None, date_from=None, date_to=None):
        """
        Searches expenses by title or category (legacy text), filtered by user.
        Includes category_id if supported by schema.
        Case-insensitive search. Supports pagination and date range.
        """
        try:
            with get_connection(self.db_path) as conn:
                include_category_fk = self._has_column(conn, "expenses", "category_id")
                select_cols = "id, title, price, date, category" + (", category_id" if include_category_fk else "")
                where = ["user_id = ?", "(title LIKE ? COLLATE NOCASE OR category LIKE ? COLLATE NOCASE)"]
                params = [user_id, f"%{query}%", f"%{query}%"]
                if date_from:
                    where.append("date >= ?")
                    params.append(date_from)
                if date_to:
                    where.append("date <= ?")
                    params.append(date_to)
                where_sql = " WHERE " + " AND ".join(where)
                sql = f"SELECT {select_cols} FROM expenses{where_sql} {_order_clause(order)}"
                if limit is not None:
                    sql += " LIMIT ?"
                    params.append(int(limit))
                    if offset is not None:
                        sql += " OFFSET ?"
                        params.append(int(offset))
                cursor = conn.cursor()
                cursor.execute(sql, tuple(params))
                rows = cursor.fetchall()
            expenses = []
            for r in rows:
                base = {"id": r["id"], "title": r["title"], "price": r["price"], "date": r["date"], "category": r["category"]}
                if include_category_fk:
                    base["category_id"] = r["category_id"]
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
                deleted = cursor.rowcount or 0
                conn.commit()
            if deleted == 0:
                logger.warning(f"Error deleting expense with ID {expense_id} for user {user_id}: not found or not owned by user.")
                return self.dict_response(False, "Expense not found or not owned by user")
            logger.info(f"Deleted expense with ID {expense_id} for user {user_id}.")
            return self.dict_response(True, data={"deleted": deleted})
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
                deleted = cursor.rowcount or 0
                conn.commit()
            logger.info(f"Cleared all expenses for user {user_id}.")
            return self.dict_response(True, data={"deleted": deleted})
        except Exception as e:
            logger.error(f"Error clearing expenses for user {user_id}: {e}")
            return self.dict_response(False, str(e))