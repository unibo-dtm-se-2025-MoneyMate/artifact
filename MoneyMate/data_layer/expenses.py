from .database import get_connection
from .validation import validate_expense

class ExpensesManager:
    """
    Manager class for handling expense-related database operations.
    Each method maintains the original logic and comments for clarity and testing.
    """

    def __init__(self, db_path):
        self.db_path = db_path

    def dict_response(self, success, error=None, data=None):
        """Return a standardized dictionary for all API responses."""
        return {"success": success, "error": error, "data": data}

    # --- CRUD EXPENSES ---
    def add_expense(self, title, price, date, category):
        """
        Adds a new expense after validation.
        """
        err = validate_expense(title, price, date, category)
        if err:
            return self.dict_response(False, err)
        try:
            conn = get_connection(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO expenses (title, price, date, category) VALUES (?, ?, ?, ?)",
                (title, price, date, category)
            )
            conn.commit()
            conn.close()
            return self.dict_response(True)
        except Exception as e:
            return self.dict_response(False, str(e))

    def get_expenses(self):
        """
        Returns all expenses as a list of dicts.
        """
        try:
            conn = get_connection(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, price, date, category FROM expenses")
            rows = cursor.fetchall()  # take all the results using fetchall()
            conn.close()
            # Convert to list of dicts, not tuples
            expenses = [
                {"id": r[0], "title": r[1], "price": r[2], "date": r[3], "category": r[4]}
                for r in rows
            ]
            return self.dict_response(True, data=expenses)
        except Exception as e:
            return self.dict_response(False, str(e))

    def search_expenses(self, query):
        """
        Searches expenses by title or category.
        """
        try:
            conn = get_connection(self.db_path)
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
            return self.dict_response(True, data=expenses)
        except Exception as e:
            return self.dict_response(False, str(e))

    def delete_expense(self, expense_id):
        """
        Deletes a specific expense by ID.
        """
        try:
            conn = get_connection(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            conn.commit()
            conn.close()
            return self.dict_response(True)
        except Exception as e:
            return self.dict_response(False, str(e))

    def clear_expenses(self):
        """
        Deletes all expenses from the table.
        """
        try:
            conn = get_connection(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses")
            conn.commit()
            conn.close()
            return self.dict_response(True)
        except Exception as e:
            return self.dict_response(False, str(e))