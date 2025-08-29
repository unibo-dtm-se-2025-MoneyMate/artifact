from .database import get_connection
import logging
import MoneyMate.data_layer.logging_config  # Ensure global logging configuration

logger = logging.getLogger(__name__)

class CategoriesManager:
    """
    Manager class for handling category-related database operations.
    Per-user custom categories to be used optionally by expenses via category_id.
    """

    def __init__(self, db_path):
        self.db_path = db_path

    def dict_response(self, success, error=None, data=None):
        return {"success": success, "error": error, "data": data}

    def add_category(self, user_id, name, description=None, color=None, icon=None):
        """
        Adds a new category for the given user. (name must be unique per user)
        """
        if not name:
            return self.dict_response(False, "Category name required")
        try:
            with get_connection(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO categories (user_id, name, description, color, icon) VALUES (?, ?, ?, ?, ?)",
                    (user_id, name, description, color, icon),
                )
                conn.commit()
            logger.info(f"Category '{name}' added for user {user_id}.")
            return self.dict_response(True)
        except Exception as e:
            logger.error(f"Error adding category '{name}' for user {user_id}: {e}")
            if "UNIQUE constraint failed" in str(e):
                return self.dict_response(False, "Category already exists for this user")
            return self.dict_response(False, str(e))

    def get_categories(self, user_id):
        """
        Lists categories for a given user.
        """
        try:
            with get_connection(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, name, description, color, icon FROM categories WHERE user_id = ? ORDER BY name ASC", (user_id,))
                rows = cur.fetchall()
            cats = [
                {"id": r[0], "name": r[1], "description": r[2], "color": r[3], "icon": r[4]}
                for r in rows
            ]
            logger.info(f"Retrieved {len(cats)} categories for user {user_id}.")
            return self.dict_response(True, data=cats)
        except Exception as e:
            logger.error(f"Error retrieving categories for user {user_id}: {e}")
            return self.dict_response(False, str(e))

    def delete_category(self, category_id, user_id):
        """
        Deletes a category by ID if it belongs to the user.
        Note: expenses referencing this category_id will be left as-is;
        consider cleaning or reassigning at a higher layer if needed.
        """
        try:
            with get_connection(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM categories WHERE id = ? AND user_id = ?", (category_id, user_id))
                conn.commit()
            logger.info(f"Deleted category id={category_id} for user {user_id}.")
            return self.dict_response(True)
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