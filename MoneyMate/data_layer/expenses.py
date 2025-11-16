"""
Expense management layer for the MoneyMate data model.

This module defines ExpensesManager, which handles:

- CRUD operations on the expenses table, scoped per user.
- Validation of input fields (title, price, date, category) via validation.py.
- Optional support for category_id foreign key, with schema autodetection.
- Filtering and pagination (date range, ordering, limit/offset).
- Normalized dict responses for use by DatabaseManager and the GUI.

It focuses on data integrity and compatibility with evolving DB schemas.
"""

import sqlite3
from datetime import datetime
from typing import Optional, Any, Dict
from .database import get_connection
from .validation import validate_expense
from .logging_config import get_logger

logger = get_logger(__name__)


def _order_clause(order: str) -> str:
    mapping = {
        "date_desc": "ORDER BY date DESC, id DESC",
        "date_asc": "ORDER BY date ASC, id ASC",
        "created_desc": "ORDER BY created_at DESC, id DESC",
        "created_asc": "ORDER BY created_at ASC, id ASC",
    }
    return mapping.get((order or "date_desc"), mapping["date_desc"])


def dict_response(success: bool, error: Optional[str] = None, data: Any = None) -> Dict[str, Any]:
    return {"success": success, "error": error if not success else None, "data": data}


class ExpensesManager:
    """
    Manager class for handling expense-related database operations.
    Supports per-user expense tracking and optional category_id.
    """

    def __init__(self, db_path, db_manager=None):
        self.db_path = db_path
        self._db_manager = db_manager

    def _get_db_manager(self):
        if self._db_manager is None:
            from .manager import DatabaseManager
            self._db_manager = DatabaseManager(self.db_path)
        return self._db_manager

    def _has_column(self, conn, table_name: str, column_name: str) -> bool:
        try:
            cur = conn.cursor()
            cur.execute(f"PRAGMA table_info({table_name});")
            cols = {row[1] for row in cur.fetchall()}
            return column_name in cols
        except Exception as e:
            logger.error(f"Error checking column {column_name} in table {table_name}: {e}")
            return False

    def _category_belongs_to_user(self, conn, category_id: int, user_id: int) -> bool:
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM categories WHERE id = ? AND user_id = ?", (category_id, user_id))
            return cur.fetchone() is not None
        except Exception as e:
            logger.error(f"Error validating category_id {category_id} for user {user_id}: {e}")
            return False

    # -----------------
    # CRUD EXPENSES
    # -----------------
    def add_expense(self, title, price, date, category, user_id, category_id=None):
        err = validate_expense(title, price, date, category)
        if err:
            logger.warning(f"Validation failed for expense '{title}': {err}")
            return dict_response(False, err)

        try:
            datetime.strptime(date, "%Y-%m-%d")
        except Exception:
            return dict_response(False, "Invalid date format (YYYY-MM-DD required)")

        try:
            with get_connection(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                include_category_fk = self._has_column(conn, "expenses", "category_id")
                cursor = conn.cursor()
                if include_category_fk and category_id is not None:
                    if not self._category_belongs_to_user(conn, category_id, user_id):
                        return dict_response(False, "Invalid category for this user")
                    cursor.execute(
                        "INSERT INTO expenses (title, price, date, category, user_id, category_id) VALUES (?, ?, ?, ?, ?, ?)",
                        (title, price, date, category, user_id, category_id)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO expenses (title, price, date, category, user_id) VALUES (?, ?, ?, ?, ?)",
                        (title, price, date, category, user_id)
                    )
                conn.commit()
            # Log di successo conforme ai test
            logger.info(f"Expense '{title}' added for user id={user_id}")
            return dict_response(True)
        except Exception as e:
            logger.error(f"Error adding expense '{title}': {e}")
            return dict_response(False, str(e))

    def update_expense(self, expense_id, user_id, title=None, price=None, date=None, category=None, category_id=None):
        fields = {}

        if title is not None:
            title_norm = title.strip() if isinstance(title, str) else title
            if not title_norm:
                return dict_response(False, "Missing title")
            fields["title"] = title_norm

        if price is not None:
            try:
                price_val = float(price)
            except Exception:
                return dict_response(False, "Invalid price")
            if price_val <= 0:
                return dict_response(False, "Price must be positive")
            fields["price"] = price_val

        if date is not None:
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except Exception:
                return dict_response(False, "Invalid date format (YYYY-MM-DD required)")
            fields["date"] = date

        if category is not None:
            category_norm = category.strip() if isinstance(category, str) else category
            if not category_norm:
                return dict_response(False, "All fields required")
            fields["category"] = category_norm

        try:
            with get_connection(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                include_category_fk = self._has_column(conn, "expenses", "category_id")
                if category_id is not None:
                    if not include_category_fk:
                        return dict_response(False, "Categories not supported by schema")
                    if not self._category_belongs_to_user(conn, category_id, user_id):
                        return dict_response(False, "Invalid category for this user")
                    fields["category_id"] = category_id

                if not fields:
                    return dict_response(False, "No fields to update")

                set_frag = ", ".join(f"{k} = ?" for k in fields.keys())
                params = list(fields.values()) + [expense_id, user_id]
                cursor = conn.cursor()
                cursor.execute(f"UPDATE expenses SET {set_frag} WHERE id = ? AND user_id = ?", tuple(params))
                updated = cursor.rowcount or 0
                conn.commit()
            return dict_response(True, data={"updated": updated})
        except Exception as e:
            logger.error(f"Error updating expense id={expense_id}: {e}")
            return dict_response(False, str(e))

    def get_expenses(self, user_id, order="date_desc", limit=None, offset=None, date_from=None, date_to=None):
        try:
            with get_connection(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
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

            expenses = [dict(row) for row in rows]
            return dict_response(True, data=expenses)
        except Exception as e:
            logger.error(f"Error retrieving expenses for user {user_id}: {e}")
            return dict_response(False, str(e))

    def search_expenses(self, query, user_id, order="date_desc", limit=None, offset=None, date_from=None, date_to=None):
        try:
            with get_connection(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
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

            expenses = [dict(row) for row in rows]
            return dict_response(True, data=expenses)
        except Exception as e:
            logger.error(f"Error searching expenses for user {user_id}: {e}")
            return dict_response(False, str(e))

    def delete_expense(self, expense_id, user_id):
        try:
            with get_connection(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user_id))
                deleted = cursor.rowcount or 0
                conn.commit()
            # Log conforme ai test: cerca la stringa "Deleted expense"
            logger.info(f"Deleted expense id={expense_id} for user id={user_id}")
            return dict_response(True, data={"deleted": deleted})
        except Exception as e:
            logger.error(f"Error deleting expense id={expense_id}: {e}")
            return dict_response(False, str(e))

    def clear_expenses(self, user_id):
        try:
            with get_connection(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("DELETE FROM expenses WHERE user_id = ?", (user_id,))
                deleted = cursor.rowcount or 0
                conn.commit()
            logger.info(f"Cleared all expenses for user id={user_id} (deleted={deleted})")
            return dict_response(True, data={"deleted": deleted})
        except Exception as e:
            logger.error(f"Error clearing expenses for user {user_id}: {e}")
            return dict_response(False, str(e))