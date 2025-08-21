import sqlite3
from typing import Dict, Any, Optional
from datetime import datetime

DB_PATH = "moneymate.db"

def dict_response(success: bool, error: Optional[str] = None, data: Any = None) -> Dict[str, Any]:
    """return a standardized dictionary for all API responses."""
    return {"success": success, "error": error, "data": data}

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Creates the tables if they do not exist in the SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor() # To execute SQL commands
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                price REAL NOT NULL,
                date TEXT NOT NULL,
                category TEXT NOT NULL
            )""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER NOT NULL,
                type TEXT CHECK(type IN ('debit', 'credit')) NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY(contact_id) REFERENCES contacts(id)
            )""")
        conn.commit()
        conn.close()


      # --- VALIDATION METHODS ---  

    def _validate_expense(self, title, price, date, category):  
        if not all([title, price, date, category]):
            return "All fields required"
        try:
            float(price)
        except Exception:
            return "Invalid price"
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except Exception:
            return "Invalid date format (YYYY-MM-DD required)"
        return None

    def _validate_contact(self, name):
        if not name:
            return "Contact name required"
        return None

    def _validate_transaction(self, contact_id, type_, amount, date):
        if type_ not in ("debit", "credit"):
            return "Invalid type (debit/credit)"
        if amount <= 0:
            return "Amount must be positive"
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except Exception:
            return "Invalid date format (YYYY-MM-DD required)"
        return None
    

        # --- CRUD EXPENSES ---

    def add_expense(self, title, price, date, category):
        err = self._validate_expense(title, price, date, category)
        if err:
            return dict_response(False, err)
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO expenses (title, price, date, category) VALUES (?, ?, ?, ?)",
                (title, price, date, category)
            )
            conn.commit()
            conn.close()
            return dict_response(True)
        except Exception as e:
            return dict_response(False, str(e))

    def get_expenses(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM expenses")
            data = cursor.fetchall()   #take all the results using fetchall()
            conn.close()
            return dict_response(True, data=data)
        except Exception as e:
            return dict_response(False, str(e))

    def search_expenses(self, query):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Cerca title o category
            cursor.execute(
                "SELECT * FROM expenses WHERE title LIKE ? OR category LIKE ?",
                (f"%{query}%", f"%{query}%") #search using STR
            )
            data = cursor.fetchall()
            conn.close()
            return dict_response(True, data=data)
        except Exception as e:
            return dict_response(False, str(e))

    def delete_expense(self, expense_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            conn.commit()
            conn.close()
            return dict_response(True)
        except Exception as e:
            return dict_response(False, str(e))

    def clear_expenses(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses")
            conn.commit()
            conn.close()
            return dict_response(True)
        except Exception as e:
            return dict_response(False, str(e))
        
        
        # --- CRUD CONTACTS ---

    def add_contact(self, name):
        err = self._validate_contact(name)
        if err:
            return dict_response(False, err)
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO contacts (name) VALUES (?)", (name,))
            conn.commit()
            conn.close()
            return dict_response(True)
        except Exception as e:
            return dict_response(False, str(e))

    def get_contacts(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM contacts")
            data = cursor.fetchall()
            conn.close()
            return dict_response(True, data=data)
        except Exception as e:
            return dict_response(False, str(e))

    def delete_contact(self, contact_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
            conn.commit()
            conn.close()
            return dict_response(True)
        except Exception as e:
            return dict_response(False, str(e))
        

        # --- CRUD TRANSACTIONS ---

    def add_transaction(self, contact_id, type_, amount, date, description=""):
        """
        Adds a new transaction for the specified contact.
        Validates the input before inserting the transaction into the database.
        Returns a standardized response indicating success or failure.
        """
        err = self._validate_transaction(contact_id, type_, amount, date)
        if err:
            return dict_response(False, err)
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO transactions (contact_id, type, amount, date, description) VALUES (?, ?, ?, ?, ?)",
                (contact_id, type_, amount, date, description)
            )
            conn.commit()
            conn.close()
            return dict_response(True)
        
        except Exception as e:
            error_msg = f"Error adding transaction for contact ID {contact_id}: {str(e)}"
            print(error_msg)
            return dict_response(False, error_msg)

    def get_transactions(self, contact_id=None):
        """
        Retrieves transactions from the database.
        If a contact_id is specified, only transactions for that contact are returned.
        Otherwise, all transactions are returned.
        Returns a standardized response with the transaction data or an error message.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            if contact_id:
                cursor.execute("SELECT * FROM transactions WHERE contact_id = ?", (contact_id,))
            else:
                cursor.execute("SELECT * FROM transactions")
            data = cursor.fetchall()
            conn.close()
            return dict_response(True, data=data)
        
        except Exception as e:
            error_msg = f"Error retrieving transactions: {str(e)}"
            print(error_msg)
            return dict_response(False, error_msg)

    def delete_transaction(self, transaction_id):
        """
        Deletes a transaction from the database using its transaction ID.
        Returns a standardized response indicating success or failure.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
            conn.commit()
            conn.close()
            return dict_response(True)
        
        except Exception as e:
            error_msg = f"Error deleting transaction with ID {transaction_id}: {str(e)}"
            print(error_msg)
            return dict_response(False, error_msg)