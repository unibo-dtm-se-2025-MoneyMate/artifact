"""
Category management layer for the MoneyMate data model.

This module defines CategoriesManager, a small ORM-like helper responsible for:

- CRUD operations on the categories table (per-user categories).
- Enforcing basic validation and uniqueness (name per user).
- Supporting ordering and pagination for category listing.
- Providing consistent dict-based responses compatible with DatabaseManager.

It directly uses the shared SQLite connection helpers from database.py.
"""

from .database import get_connection
from .database import get_connection
from .manager import DatabaseManager # Ensure global logging configuration

from .logging_config import get_logger
logger = get_logger(__name__)

def _order_clause(order: str) -> str:
    mapping = {
        "name_asc": "ORDER BY name ASC, id ASC",
        "name_desc": "ORDER BY name DESC, id DESC",
        "created_asc": "ORDER BY created_at ASC, id ASC",
        "created_desc": "ORDER BY created_at DESC, id DESC",
    }
    return mapping.get((order or "name_asc"), mapping["name_asc"])

class CategoriesManager:
    """
    Manager class for handling category-related database operations.
    """

    def __init__(self, db_path, db_manager=None):  # <-- aggiunto db_manager opzionale
        self.db_path = db_path
        self._db_manager = db_manager  # opzionale, per eventuali future esigenze


    def dict_response(self, success, error=None, data=None):
        return {"success": success, "error": error, "data": data}

    def add_category(self, user_id, name, description=None, color=None, icon=None):
        """
        Adds a new category for the given user. (name must be unique per user)
        """
        name_norm = name.strip() if isinstance(name, str) else name
        if not name_norm:
            return self.dict_response(False, "Category name required")
        try:
            with get_connection(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO categories (user_id, name, description, color, icon) VALUES (?, ?, ?, ?, ?)",
                    (user_id, name_norm, description, color, icon),
                )
                conn.commit()
            logger.info(f"Category '{name_norm}' added for user {user_id}.")
            return self.dict_response(True)
        except Exception as e:
            logger.error(f"Error adding category '{name_norm}' for user {user_id}: {e}")
            if "UNIQUE constraint failed" in str(e):
                return self.dict_response(False, "Category already exists for this user")
            return self.dict_response(False, str(e))

    def get_categories(self, user_id, order="name_asc", limit=None, offset=None):
        """
        Lists categories for a given user.
        Supports optional ordering and pagination.
        """
        try:
            with get_connection(self.db_path) as conn:
                cur = conn.cursor()
                sql = f"SELECT id, name, description, color, icon FROM categories WHERE user_id = ? {_order_clause(order)}"
                params = [user_id]
                if limit is not None:
                    sql += " LIMIT ?"
                    params.append(int(limit))
                    if offset is not None:
                        sql += " OFFSET ?"
                        params.append(int(offset))
                cur.execute(sql, tuple(params))
                rows = cur.fetchall()
            cats = [
                {"id": r["id"], "name": r["name"], "description": r["description"], "color": r["color"], "icon": r["icon"]}
                for r in rows
            ]
            logger.info(f"Retrieved {len(cats)} categories for user {user_id} (order={order}).")
            return self.dict_response(True, data=cats)
        except Exception as e:
            logger.error(f"Error retrieving categories for user {user_id}: {e}")
            return self.dict_response(False, str(e))

    def delete_category(self, category_id, user_id):
        """
        Deletes a category by ID if it belongs to the user.
        Note: expenses referencing this category_id will be left as-is;
        consider cleaning or reassigning at a higher layer if needed.

        Idempotent semantics: always return success with deleted count.
        """
        try:
            with get_connection(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM categories WHERE id = ? AND user_id = ?", (category_id, user_id))
                deleted = cur.rowcount or 0
                conn.commit()
            if deleted == 0:
                logger.warning(f"Delete category noop: id={category_id}, user={user_id} (not found or not owned).")
            else:
                logger.info(f"Deleted category id={category_id} for user {user_id}.")
            return self.dict_response(True, data={"deleted": deleted})
        except Exception as e:
            logger.error(f"Error deleting category id={category_id} for user {user_id}: {e}")
            return self.dict_response(False, str(e))

    def category_exists_for_user(self, category_id, user_id) -> bool:
        """
        Helper for cross-entity validation: check if category belongs to user.
        """
        try:
            with get_connection(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute("SELECT 1 FROM categories WHERE id = ? AND user_id = ?", (category_id, user_id))
                return cur.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking category existence id={category_id} for user {user_id}: {e}")

            return False