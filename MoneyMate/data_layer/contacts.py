"""
Contact management layer for the MoneyMate data model.

This module defines ContactsManager, which encapsulates operations on the
contacts table and provides:

- Per-user CRUD operations for contacts.
- Validation of contact names via validation.py.
- Ordering and simple filtering hooks (name-based).
- Helper to check the existence of a contact for a given user.

All methods return standard dict envelopes to integrate cleanly with
DatabaseManager and the GUI API layer.
"""

import sqlite3
from typing import Any, Optional, Dict
from .database import get_connection
from .validation import validate_contact
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

def dict_response(success: bool, error: Optional[str] = None, data: Any = None) -> Dict[str, Any]:
    return {"success": success, "error": error if not success else None, "data": data}

class ContactsManager:
    """
    Manager class for handling contact-related database operations.
    Supports per-user contacts.
    """

    def __init__(self, db_path, db_manager=None):
        self.db_path = db_path
        self._db_manager = db_manager

    # -----------------
    # CRUD CONTACTS
    # -----------------
    def add_contact(self, name, user_id):
        err = validate_contact(name)
        if err:
            logger.warning(f"Validation failed for contact '{name}': {err}")
            return dict_response(False, err)
        try:
            with get_connection(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO contacts (name, user_id) VALUES (?, ?)",
                    (name.strip() if isinstance(name, str) else name, user_id)
                )
                conn.commit()
            logger.info(f"Contact '{name}' added successfully for user {user_id}.")
            return dict_response(True)
        except Exception as e:
            msg = str(e)
            logger.error(f"Error adding contact '{name}' for user {user_id}: {msg}")
            if "UNIQUE constraint failed" in msg:
                return dict_response(False, "Contact already exists for this user")
            return dict_response(False, msg)

    def get_contacts(self, user_id, order="name_asc"):
        try:
            with get_connection(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                sql = f"SELECT id, name FROM contacts WHERE user_id = ? {_order_clause(order)}"
                cursor.execute(sql, (user_id,))
                rows = cursor.fetchall()
            contacts = [{"id": r["id"], "name": r["name"]} for r in rows]
            logger.info(f"Retrieved {len(contacts)} contacts for user {user_id} (order={order}).")
            return dict_response(True, data=contacts)
        except Exception as e:
            logger.error(f"Error retrieving contacts for user {user_id}: {e}")
            return dict_response(False, str(e))

    def delete_contact(self, contact_id, user_id):
        try:
            with get_connection(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM contacts WHERE id = ? AND user_id = ?",
                    (contact_id, user_id)
                )
                deleted = cursor.rowcount or 0
                conn.commit()
            if deleted == 0:
                logger.warning(f"Delete contact noop: id={contact_id}, user={user_id} (not found or not owned).")
            else:
                logger.info(f"Deleted contact with ID {contact_id} for user {user_id}.")
            return dict_response(True, data={"deleted": deleted})
        except Exception as e:
            logger.error(f"Error deleting contact with ID {contact_id} for user {user_id}: {e}")
            return dict_response(False, str(e))

    def contact_exists(self, contact_id, user_id):
        try:
            with get_connection(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM contacts WHERE id = ? AND user_id = ?",
                    (contact_id, user_id)
                )
                exists = cursor.fetchone() is not None
            logger.debug(f"Checked existence for contact ID {contact_id} and user {user_id}: {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error checking existence for contact ID {contact_id} and user {user_id}: {e}")
            return False
