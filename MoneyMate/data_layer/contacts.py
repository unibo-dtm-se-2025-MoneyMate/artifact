from .database import get_connection
from .validation import validate_contact
import logging
import MoneyMate.data_layer.logging_config  # Assicura la configurazione globale

logger = logging.getLogger(__name__)

class ContactsManager:
    """
    Manager class for handling contact-related database operations.
    Maintains original logic and comments for all CRUD methods.
    """

    def __init__(self, db_path):
        self.db_path = db_path

    def dict_response(self, success, error=None, data=None):
        """Return a standardized dictionary for all API responses."""
        return {"success": success, "error": error, "data": data}

    # --- CRUD CONTACTS ---
    def add_contact(self, name):
        """
        Adds a new contact after validation.
        """
        err = validate_contact(name)
        if err:
            logger.warning(f"Validation failed for contact '{name}': {err}")
            return self.dict_response(False, err)
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO contacts (name) VALUES (?)", (name,))
                conn.commit()
            logger.info(f"Contact '{name}' added successfully.")
            return self.dict_response(True)
        except Exception as e:
            logger.error(f"Error adding contact '{name}': {e}")
            return self.dict_response(False, str(e))

    def get_contacts(self):
        """
        Returns all contacts as a list of dicts.
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM contacts")
                rows = cursor.fetchall()
            contacts = [{"id": r[0], "name": r[1]} for r in rows]
            logger.info(f"Retrieved {len(contacts)} contacts from the database.")
            return self.dict_response(True, data=contacts)
        except Exception as e:
            logger.error(f"Error retrieving contacts: {e}")
            return self.dict_response(False, str(e))

    def delete_contact(self, contact_id):
        """
        Deletes a specific contact by ID.
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
                conn.commit()
            logger.info(f"Deleted contact with ID {contact_id}.")
            return self.dict_response(True)
        except Exception as e:
            logger.error(f"Error deleting contact with ID {contact_id}: {e}")
            return self.dict_response(False, str(e))

    # --- Added: method to check if the contact exists ---
    def contact_exists(self, contact_id):
        """
        Returns True if the contact exists, False otherwise.
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM contacts WHERE id = ?", (contact_id,))
                exists = cursor.fetchone() is not None
            logger.debug(f"Checked existence for contact ID {contact_id}: {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error checking existence for contact ID {contact_id}: {e}")
            return False