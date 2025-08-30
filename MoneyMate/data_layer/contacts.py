from .database import get_connection
from .validation import validate_contact
import logging
import MoneyMate.data_layer.logging_config  # Assicura la configurazione globale

logger = logging.getLogger(__name__)

class ContactsManager:
    """
    Manager class for handling contact-related database operations.
    Now supports per-user contacts.
    """

    def __init__(self, db_path):
        self.db_path = db_path

    def dict_response(self, success, error=None, data=None):
        return {"success": success, "error": error, "data": data}

    def add_contact(self, name, user_id):
        """
        Adds a new contact after validation, associated to user_id.
        """
        err = validate_contact(name)
        if err:
            logger.warning(f"Validation failed for contact '{name}': {err}")
            return self.dict_response(False, err)
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO contacts (name, user_id) VALUES (?, ?)", (name.strip() if isinstance(name, str) else name, user_id))
                conn.commit()
            logger.info(f"Contact '{name}' added successfully for user {user_id}.")
            return self.dict_response(True)
        except Exception as e:
            logger.error(f"Error adding contact '{name}' for user {user_id}: {e}")
            return self.dict_response(False, str(e))

    def get_contacts(self, user_id):
        """
        Returns all contacts for a user as a list of dicts.
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, name FROM contacts WHERE user_id = ? ORDER BY name ASC",
                    (user_id,),
                )
                rows = cursor.fetchall()
            contacts = [{"id": r["id"], "name": r["name"]} for r in rows]
            logger.info(f"Retrieved {len(contacts)} contacts for user {user_id}.")
            return self.dict_response(True, data=contacts)
        except Exception as e:
            logger.error(f"Error retrieving contacts for user {user_id}: {e}")
            return self.dict_response(False, str(e))

    def delete_contact(self, contact_id, user_id):
        """
        Deletes a specific contact by ID, only if it belongs to the user.
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM contacts WHERE id = ? AND user_id = ?", (contact_id, user_id))
                deleted = cursor.rowcount or 0
                conn.commit()
            if deleted == 0:
                logger.warning(f"Error deleting contact with ID {contact_id} for user {user_id}: not found or not owned by user.")
                return self.dict_response(False, "Contact not found or not owned by user")
            logger.info(f"Deleted contact with ID {contact_id} for user {user_id}.")
            return self.dict_response(True, data={"deleted": deleted})
        except Exception as e:
            logger.error(f"Error deleting contact with ID {contact_id} for user {user_id}: {e}")
            return self.dict_response(False, str(e))

    def contact_exists(self, contact_id, user_id):
        """
        Returns True if the contact exists for the user, False otherwise.
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM contacts WHERE id = ? AND user_id = ?", (contact_id, user_id))
                exists = cursor.fetchone() is not None
            logger.debug(f"Checked existence for contact ID {contact_id} and user {user_id}: {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error checking existence for contact ID {contact_id} and user {user_id}: {e}")
            return False