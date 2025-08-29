from .database import get_connection
from .validation import validate_transaction
import logging
import MoneyMate.data_layer.logging_config  # Ensure global logging configuration

logger = logging.getLogger(__name__)

class TransactionsManager:
    """
    Manager for user-to-user transactions: supports tracking debiti/crediti tra utenti.
    """

    def __init__(self, db_path, contacts_manager):
        self.db_path = db_path
        self.contacts_manager = contacts_manager

    def dict_response(self, success, error=None, data=None):
        return {"success": success, "error": error, "data": data}

    def add_transaction(self, from_user_id, to_user_id, type_, amount, date, description="", contact_id=None):
        """
        Adds a new transaction between users.
        Validates input and ensures users exist and are different (if needed).
        """
        err = validate_transaction(type_, amount, date)
        if err:
            logger.warning(f"Validation failed for transaction (from_user_id={from_user_id}, to_user_id={to_user_id}, type={type_}, amount={amount}): {err}")
            return self.dict_response(False, err)
        # --- User existence check for sender and receiver ---
        if not self._user_exists(from_user_id):
            logger.warning(f"Transaction validation failed: from_user_id {from_user_id} does not exist.")
            return self.dict_response(False, "Sender user does not exist")
        if not self._user_exists(to_user_id):
            logger.warning(f"Transaction validation failed: to_user_id {to_user_id} does not exist.")
            return self.dict_response(False, "Receiver user does not exist")
        if contact_id and not self.contacts_manager.contact_exists(contact_id, from_user_id):
            logger.warning(f"Transaction validation failed: contact_id {contact_id} does not exist for user {from_user_id}.")
            return self.dict_response(False, "Contact does not exist")
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO transactions (from_user_id, to_user_id, type, amount, date, description, contact_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (from_user_id, to_user_id, type_, amount, date, description, contact_id)
                )
                conn.commit()
            logger.info(f"Transaction from user {from_user_id} to user {to_user_id} of type '{type_}' and amount {amount} added successfully.")
            return self.dict_response(True)
        except Exception as e:
            error_msg = f"Error adding transaction from user {from_user_id} to user {to_user_id}: {str(e)}"
            logger.error(error_msg)
            return self.dict_response(False, error_msg)

    def _user_exists(self, user_id):
        """
        Returns True if the user exists, False otherwise.
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking existence for user ID {user_id}: {e}")
            return False

    def _is_admin(self, user_id):
        """
        Returns True if the given user has role 'admin', False otherwise.
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
                row = cursor.fetchone()
                return bool(row and row[0] == "admin")
        except Exception as e:
            logger.error(f"Error checking admin role for user ID {user_id}: {e}")
            return False

    def get_transactions(self, user_id, as_sender=True, is_admin=False):
        """
        Retrieves transactions from the database.
        If is_admin is True, validates the user's role and returns ALL transactions.
        If as_sender is True, returns those WHERE from_user_id=user_id.
        If False, returns those WHERE to_user_id=user_id.
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                if is_admin:
                    # Enforce role check instead of trusting the flag blindly
                    if not self._is_admin(user_id):
                        logger.warning(f"Transactions access denied: user {user_id} is not admin but requested is_admin=True.")
                        return self.dict_response(False, "Admin privileges required")
                    cursor.execute("SELECT id, from_user_id, to_user_id, type, amount, date, description, contact_id FROM transactions")
                elif as_sender:
                    cursor.execute("SELECT id, from_user_id, to_user_id, type, amount, date, description, contact_id FROM transactions WHERE from_user_id = ?", (user_id,))
                else:
                    cursor.execute("SELECT id, from_user_id, to_user_id, type, amount, date, description, contact_id FROM transactions WHERE to_user_id = ?", (user_id,))
                rows = cursor.fetchall()
            transactions = [
                {
                    "id": r[0],
                    "from_user_id": r[1],
                    "to_user_id": r[2],
                    "type": r[3],
                    "amount": r[4],
                    "date": r[5],
                    "description": r[6],
                    "contact_id": r[7]
                }
                for r in rows
            ]
            logger.info(f"Retrieved {len(transactions)} transactions for user {user_id} (is_admin={is_admin}, as_sender={as_sender}).")
            return self.dict_response(True, data=transactions)
        except Exception as e:
            error_msg = f"Error retrieving transactions for user {user_id}: {str(e)}"
            logger.error(error_msg)
            return self.dict_response(False, error_msg)

    def delete_transaction(self, transaction_id, user_id):
        """
        Deletes a transaction by id if the user is the sender.
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM transactions WHERE id = ? AND from_user_id = ?", (transaction_id, user_id))
                conn.commit()
            logger.info(f"Deleted transaction with ID {transaction_id} for user {user_id}.")
            return self.dict_response(True)
        except Exception as e:
            error_msg = f"Error deleting transaction with ID {transaction_id} for user {user_id}: {str(e)}"
            logger.error(error_msg)
            return self.dict_response(False, error_msg)

    def get_user_balance(self, user_id):
        """
        Calculates the balance for a user based on transactions (credit received, debit sent).
        Note: The function sums credit and debit for both sent and received transactions.
        """
        CREDIT = "credit"
        DEBIT = "debit"

        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                # Sum all credits and debits where user is sender or receiver
                cursor.execute(
                    """
                    SELECT type, SUM(amount) FROM transactions
                    WHERE (from_user_id = ? OR to_user_id = ?)
                    GROUP BY type
                    """,
                    (user_id, user_id)
                )
                results = cursor.fetchall()

            total_credit = 0
            total_debit = 0

            for transaction_type, total_amount in results:
                if transaction_type == CREDIT:
                    total_credit += total_amount
                elif transaction_type == DEBIT:
                    total_debit += total_amount
                else:
                    logger.warning(f"Unknown transaction type '{transaction_type}' for user ID {user_id}")

            balance = total_credit - total_debit

            logger.info(f"Calculated balance for user ID {user_id}: {balance} (credit={total_credit}, debit={total_debit})")
            return self.dict_response(True, data=balance)
        except Exception as e:
            error_msg = f"Error calculating balance for user ID {user_id}: {str(e)}"
            logger.error(error_msg)
            return self.dict_response(False, error_msg)