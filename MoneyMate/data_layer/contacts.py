from .database import get_connection
from .validation import validate_contact

def dict_response(success, error=None, data=None):
    """Return a standardized dictionary for all API responses."""
    return {"success": success, "error": error, "data": data}

# --- CRUD CONTACTS ---
def add_contact(name):
    """
    Adds a new contact after validation.
    """
    err = validate_contact(name)
    if err:
        return dict_response(False, err)
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO contacts (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        return dict_response(True)
    except Exception as e:
        return dict_response(False, str(e))

def get_contacts():
    """
    Returns all contacts as a list of dicts.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM contacts")
        rows = cursor.fetchall()
        conn.close()
        # Convert to list of dicts, not tuples
        contacts = [{"id": r[0], "name": r[1]} for r in rows]
        return dict_response(True, data=contacts)
    except Exception as e:
        return dict_response(False, str(e))

def delete_contact(contact_id):
    """
    Deletes a specific contact by ID.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        conn.commit()
        conn.close()
        return dict_response(True)
    except Exception as e:
        return dict_response(False, str(e))

# --- Added: method to check if the contact exists ---
def contact_exists(contact_id):
    """
    Returns True if the contact exists, False otherwise.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM contacts WHERE id = ?", (contact_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists