from .database import get_connection
from .validation import validate_contact

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
            return self.dict_response(False, err)
        try:
            # Use context manager for safe connection handling
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO contacts (name) VALUES (?)", (name,))
                conn.commit()
            return self.dict_response(True)
        except Exception as e:
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
            # Convert to list of dicts, not tuples
            contacts = [{"id": r[0], "name": r[1]} for r in rows]
            return self.dict_response(True, data=contacts)
        except Exception as e:
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
            return self.dict_response(True)
        except Exception as e:
            return self.dict_response(False, str(e))

    # --- Added: method to check if the contact exists ---
    def contact_exists(self, contact_id):
        """
        Returns True if the contact exists, False otherwise.
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM contacts WHERE id = ?", (contact_id,))
            exists = cursor.fetchone() is not None
        return exists