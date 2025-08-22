from .database import get_connection
from .validation import validate_transaction

class TransactionsManager:
    """
    Manager class for handling transaction-related database operations.
    Keeps original method logic and comments, uses ContactsManager for validation.
    """

    def __init__(self, db_path, contacts_manager):
        self.db_path = db_path
        self.contacts_manager = contacts_manager

    def dict_response(self, success, error=None, data=None):
        """Return a standardized dictionary for all API responses."""
        return {"success": success, "error": error, "data": data}

    # --- CRUD TRANSACTIONS ---
    def add_transaction(self, contact_id, type_, amount, date, description=""):
        """
        Adds a new transaction for the specified contact.
        Validates the input before inserting the transaction into the database.
        Returns a standardized response indicating success or failure.
        """
        err = validate_transaction(type_, amount, date)
        if err:
            return self.dict_response(False, err)
        # Check that the contact_id exists (required by test)
        if not self.contacts_manager.contact_exists(contact_id):
            return self.dict_response(False, "Contact does not exist")
        try:
            conn = get_connection(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO transactions (contact_id, type, amount, date, description) VALUES (?, ?, ?, ?, ?)",
                (contact_id, type_, amount, date, description)
            )
            conn.commit()
            conn.close()
            return self.dict_response(True)
        except Exception as e:
            error_msg = f"Error adding transaction for contact ID {contact_id}: {str(e)}"
            print(error_msg)
            return self.dict_response(False, error_msg)

    def get_transactions(self, contact_id=None):
        """
        Retrieves transactions from the database.
        If a contact_id is specified, only transactions for that contact are returned.
        Otherwise, all transactions are returned.
        Returns a standardized response with the transaction data or an error message.
        """
        try:
            conn = get_connection(self.db_path)
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
            return self.dict_response(True, data=transactions)
        except Exception as e:
            error_msg = f"Error retrieving transactions: {str(e)}"
            print(error_msg)
            return self.dict_response(False, error_msg)

    def delete_transaction(self, transaction_id):
        """
        Deletes a transaction from the database using its transaction ID.
        Returns a standardized response indicating success or failure.
        """
        try:
            conn = get_connection(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
            conn.commit()
            conn.close()
            return self.dict_response(True)
        except Exception as e:
            error_msg = f"Error deleting transaction with ID {transaction_id}: {str(e)}"
            print(error_msg)
            return self.dict_response(False, error_msg)

    def get_contact_balance(self, contact_id):
        """
        Calculates the balance for a specific contact by summing all 'credit' and 'debit' transactions.
        Also returns total credits and debits separately for more detailed reporting.
        """
        CREDIT = "credit"
        DEBIT = "debit"

        try:
            conn = get_connection(self.db_path)
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
            return self.dict_response(True, data=balance)
        except Exception as e:
            # Provide a more descriptive error message and log it for debugging
            error_msg = f"Error calculating balance for contact ID {contact_id}: {str(e)}"
            print(error_msg)
            return self.dict_response(False, error_msg)