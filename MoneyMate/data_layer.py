import sqlite3
from typing import Dict, Any, Optional
from datetime import datetime

DB_PATH = "moneymate.db"

def dict_response(success: bool, error: Optional[str] = None, data: Any = None) -> Dict[str, Any]:
    """Return a standardized dictionary for all API responses."""
    return {"success": success, "error": error, "data": data}

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """
        Creates the tables if they do not exist in the SQLite database.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()  # To execute SQL commands
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

    # --- Method to list all tables in the DB, especially useful for testing ---
    def list_tables(self):
        """
        Returns a list of all tables in the database.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            return dict_response(True, data=tables)
        except Exception as e:
            return dict_response(False, str(e))

    # --- VALIDATION METHODS ---
    def _validate_expense(self, title, price, date, category):
        # Check if title is missing with specific error
        if not title:
            return "Missing title"
        if not all([price, date, category]):
            return "All fields required"
        try:
            price_val = float(price)
            if price_val <= 0:
                return "Price must be positive"
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

    # --- Added: method to check if the contact exists ---
    def _contact_exists(self, contact_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM contacts WHERE id = ?", (contact_id,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

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
            cursor.execute("SELECT id, title, price, date, category FROM expenses")
            rows = cursor.fetchall()  # take all the results using fetchall()
            conn.close()
            # Convert to list of dicts, not tuples
            expenses = [
                {"id": r[0], "title": r[1], "price": r[2], "date": r[3], "category": r[4]}
                for r in rows
            ]
            return dict_response(True, data=expenses)
        except Exception as e:
            return dict_response(False, str(e))

    def search_expenses(self, query):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Search by title or category
            cursor.execute(
                "SELECT id, title, price, date, category FROM expenses WHERE title LIKE ? OR category LIKE ?",
                (f"%{query}%", f"%{query}%")
            )
            rows = cursor.fetchall()
            conn.close()
            # Convert to list of dicts, not tuples
            expenses = [
                {"id": r[0], "title": r[1], "price": r[2], "date": r[3], "category": r[4]}
                for r in rows
            ]
            return dict_response(True, data=expenses)
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
            cursor.execute("SELECT id, name FROM contacts")
            rows = cursor.fetchall()
            conn.close()
            # Convert to list of dicts, not tuples
            contacts = [{"id": r[0], "name": r[1]} for r in rows]
            return dict_response(True, data=contacts)
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
        # Check that the contact_id exists (required by test)
        if not self._contact_exists(contact_id):
            return dict_response(False, "Contact does not exist")
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
                cursor.execute("SELECT id, contact_id, type, amount, date, description FROM transactions WHERE contact_id = ?", (contact_id,))
            else:
                cursor.execute("SELECT id, contact_id, type, amount, date, description FROM transactions")
            rows = cursor.fetchall()
            conn.close()
            # Convert to list of dicts, not tuples
            transactions = [
                {
                    "id": r[0],
                    "contact_id": r[1],
                    "type": r[2],
                    "amount": r[3],
                    "date": r[4],
                    "description": r[5]
                }
                for r in rows
            ]
            return dict_response(True, data=transactions)
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

    def get_contact_balance(self, contact_id):
        """
        Calculates the balance for a specific contact by summing all 'credit' and 'debit' transactions.
        Also returns total credits and debits separately for more detailed reporting.
        """
        CREDIT = "credit"
        DEBIT = "debit"

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Retrieve the sum of amounts for each transaction type for the given contact
            cursor.execute(
                "SELECT type, SUM(amount) FROM transactions WHERE contact_id = ? GROUP BY type",
                (contact_id,)
            )
            results = cursor.fetchall()
            conn.close()

            total_credit = 0
            total_debit = 0

            # Process each transaction type; log any unknown types for debugging
            for transaction_type, total_amount in results:
                if transaction_type == CREDIT:
                    total_credit += total_amount
                elif transaction_type == DEBIT:
                    total_debit += total_amount
                else:
                    print(f"Warning: Unknown transaction type '{transaction_type}' for contact ID {contact_id}")

            balance = total_credit - total_debit

            # Return only the balance as required by the test (not a dict of credits/debits)
            return dict_response(True, data=balance)
        except Exception as e:
            # Provide a more descriptive error message and log it for debugging
            error_msg = f"Error calculating balance for contact ID {contact_id}: {str(e)}"
            print(error_msg)
            return dict_response(False, error_msg)