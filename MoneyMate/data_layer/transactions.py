from .database import get_connection
from .validation import validate_transaction
import logging
from datetime import datetime
import MoneyMate.data_layer.logging_config  # Ensure global logging configuration

logger = logging.getLogger(__name__)

def _order_clause(order: str) -> str:
    mapping = {
        "date_desc": "ORDER BY date DESC, id DESC",
        "date_asc": "ORDER BY date ASC, id ASC",
        "created_desc": "ORDER BY created_at DESC, id DESC",
        "created_asc": "ORDER BY created_at ASC, id ASC",
    }
    return mapping.get((order or "date_desc"), mapping["date_desc"])

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
        # Enforce sender != receiver (DB CHECK not easily alterable post-creation)
        if from_user_id == to_user_id:
            logger.warning(f"Transaction validation failed: from_user_id and to_user_id are the same ({from_user_id}).")
            return self.dict_response(False, "Sender and receiver must be different")
        # Contact cross-validation: contact must belong to sender (by design)
        if contact_id and not self.contacts_manager.contact_exists(contact_id, from_user_id):
            logger.warning(f"Transaction validation failed: contact_id {contact_id} does not exist for user {from_user_id}.")
            return self.dict_response(False, "Contact does not exist")
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO transactions (from_user_id, to_user_id, type, amount, date, description, contact_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (from_user_id, to_user_id, type_, float(amount), date, description, contact_id)
                )
                conn.commit()
            logger.info(f"Transaction from user {from_user_id} to user {to_user_id} of type '{type_}' and amount {amount} added successfully.")
            return self.dict_response(True)
        except Exception as e:
            error_msg = f"Error adding transaction from user {from_user_id} to user {to_user_id}: {str(e)}"
            logger.error(error_msg)
            return self.dict_response(False, error_msg)

    def update_transaction(self, transaction_id, user_id, type_=None, amount=None, date=None, description=None, contact_id=None):
        """
        Partially update a transaction if the user is the sender (owner).
        Validates provided fields; ignores None fields.
        Returns {'updated': 0|1}.
        """
        fields = {}
        # Validate provided fields
        if type_ is not None:
            type_norm = type_.lower().strip() if isinstance(type_, str) else None
            if type_norm not in ("debit", "credit"):
                return self.dict_response(False, "Invalid type (debit/credit)")
            fields["type"] = type_norm
        if amount is not None:
            try:
                amount_val = float(amount)
            except Exception:
                return self.dict_response(False, "Invalid amount")
            if amount_val <= 0:
                return self.dict_response(False, "Amount must be positive")
            fields["amount"] = amount_val
        if date is not None:
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except Exception:
                return self.dict_response(False, "Invalid date format (YYYY-MM-DD required)")
            fields["date"] = date
        if description is not None:
            fields["description"] = description
        if contact_id is not None:
            # contact must belong to the sender (user_id)
            if not self.contacts_manager.contact_exists(contact_id, user_id):
                return self.dict_response(False, "Contact does not exist")
            fields["contact_id"] = contact_id

        if not fields:
            return self.dict_response(False, "No fields to update")

        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                # Only allow update if the user is the sender
                set_frag = ", ".join(f"{k} = ?" for k in fields.keys())
                params = list(fields.values()) + [transaction_id, user_id]
                cursor.execute(f"UPDATE transactions SET {set_frag} WHERE id = ? AND from_user_id = ?", tuple(params))
                updated = cursor.rowcount or 0
                conn.commit()
            if updated == 0:
                logger.warning(f"Update transaction noop or not authorized: id={transaction_id}, user={user_id}.")
            else:
                logger.info(f"Updated transaction id={transaction_id} for user {user_id}.")
            return self.dict_response(True, data={"updated": updated})
        except Exception as e:
            error_msg = f"Error updating transaction id={transaction_id} for user {user_id}: {str(e)}"
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
                return bool(row and row["role"] == "admin")
        except Exception as e:
            logger.error(f"Error checking admin role for user ID {user_id}: {e}")
            return False

    def get_transactions(self, user_id, as_sender=True, is_admin=False, order="date_desc", limit=None, offset=None, date_from=None, date_to=None, contact_id=None):
        """
        Retrieves transactions from the database.
        If is_admin is True, validates the user's role and returns ALL transactions.
        If as_sender is True, returns those WHERE from_user_id=user_id.
        If False, returns those WHERE to_user_id=user_id.
        Supports deterministic ordering, pagination, and optional date/contact filters.
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                params = []
                where_parts = []
                if is_admin:
                    # Enforce role check instead of trusting the flag blindly
                    if not self._is_admin(user_id):
                        logger.warning(f"Transactions access denied: user {user_id} is not admin but requested is_admin=True.")
                        return self.dict_response(False, "Admin privileges required")
                else:
                    if as_sender:
                        where_parts.append("from_user_id = ?")
                        params.append(user_id)
                    else:
                        where_parts.append("to_user_id = ?")
                        params.append(user_id)
                if contact_id is not None:
                    where_parts.append("contact_id = ?")
                    params.append(contact_id)
                if date_from:
                    where_parts.append("date >= ?")
                    params.append(date_from)
                if date_to:
                    where_parts.append("date <= ?")
                    params.append(date_to)
                where_sql = (" WHERE " + " AND ".join(where_parts)) if where_parts else ""
                sql = f"SELECT id, from_user_id, to_user_id, type, amount, date, description, contact_id FROM transactions{where_sql} {_order_clause(order)}"
                if limit is not None:
                    sql += " LIMIT ?"
                    params.append(int(limit))
                    if offset is not None:
                        sql += " OFFSET ?"
                        params.append(int(offset))
                cursor.execute(sql, tuple(params))
                rows = cursor.fetchall()
            transactions = [
                {
                    "id": r["id"],
                    "from_user_id": r["from_user_id"],
                    "to_user_id": r["to_user_id"],
                    "type": r["type"],
                    "amount": r["amount"],
                    "date": r["date"],
                    "description": r["description"],
                    "contact_id": r["contact_id"]
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
        Idempotent semantics: return success=True with deleted count, without leaking authorization.
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM transactions WHERE id = ? AND from_user_id = ?", (transaction_id, user_id))
                deleted = cursor.rowcount or 0
                conn.commit()
            if deleted == 0:
                logger.warning(f"Delete transaction noop (not found or not owned): id={transaction_id}, user={user_id}.")
            else:
                logger.info(f"Deleted transaction with ID {transaction_id} for user {user_id}.")
            return self.dict_response(True, data={"deleted": deleted})
        except Exception as e:
            error_msg = f"Error deleting transaction with ID {transaction_id} for user {user_id}: {str(e)}"
            logger.error(error_msg)
            return self.dict_response(False, error_msg)

    def get_user_balance(self, user_id):
        """
        LEGACY semantics (kept for backward compatibility and tests):
        Calculates balance = total credit − total debit across ALL transactions
        where the user appears either as sender or receiver.
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                # Sum all credits and debits where user is sender or receiver
                cursor.execute(
                    """
                    SELECT type, SUM(amount) AS total FROM transactions
                    WHERE (from_user_id = ? OR to_user_id = ?)
                    GROUP BY type
                    """,
                    (user_id, user_id)
                )
                results = cursor.fetchall()

            total_credit = 0.0
            total_debit = 0.0

            for row in results:
                transaction_type = row["type"]
                total_amount = row["total"]
                if transaction_type == "credit":
                    total_credit += total_amount
                elif transaction_type == "debit":
                    total_debit += total_amount
                else:
                    logger.warning(f"Unknown transaction type '{transaction_type}' for user ID {user_id}")

            balance = total_credit - total_debit

            logger.info(f"(LEGACY) Calculated balance for user ID {user_id}: {balance} (credit={total_credit}, debit={total_debit})")
            return self.dict_response(True, data=balance)
        except Exception as e:
            error_msg = f"Error calculating balance for user ID {user_id}: {str(e)}"
            logger.error(error_msg)
            return self.dict_response(False, error_msg)

    def get_user_net_balance(self, user_id):
        """
        NET semantics (recommended for GUI):
        balance_net = credits_received (to_user_id=user AND type = 'credit')
                       - debits_sent (from_user_id=user AND type = 'debit')
        This avoids symmetry between sender and receiver on the same transaction.
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT
                        COALESCE(SUM(CASE WHEN to_user_id = ? AND type = 'credit' THEN amount ELSE 0 END), 0) AS credits_received,
                        COALESCE(SUM(CASE WHEN from_user_id = ? AND type = 'debit' THEN amount ELSE 0 END), 0) AS debits_sent
                    FROM transactions
                    """,
                    (user_id, user_id)
                )
                row = cursor.fetchone()
                credits_received = row["credits_received"]
                debits_sent = row["debits_sent"]

            balance_net = credits_received - debits_sent
            logger.info(f"(NET) Calculated net balance for user ID {user_id}: {balance_net} (credits_received={credits_received}, debits_sent={debits_sent})")
            return self.dict_response(True, data=balance_net)
        except Exception as e:
            error_msg = f"Error calculating net balance for user ID {user_id}: {str(e)}"
            logger.error(error_msg)
            return self.dict_response(False, error_msg)

    def get_user_balance_breakdown(self, user_id):
        """
        Detailed breakdown for GUI analytics:
        Returns a dict with:
        - credits_received
        - debits_sent
        - credits_sent
        - debits_received
        - net (credits_received - debits_sent)
        - legacy ((credits_received + credits_sent) - (debits_sent + debits_received))
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT
                        COALESCE(SUM(CASE WHEN to_user_id = ? AND type = 'credit' THEN amount ELSE 0 END), 0) AS credits_received,
                        COALESCE(SUM(CASE WHEN from_user_id = ? AND type = 'debit' THEN amount ELSE 0 END), 0) AS debits_sent,
                        COALESCE(SUM(CASE WHEN from_user_id = ? AND type = 'credit' THEN amount ELSE 0 END), 0) AS credits_sent,
                        COALESCE(SUM(CASE WHEN to_user_id = ? AND type = 'debit' THEN amount ELSE 0 END), 0) AS debits_received
                    FROM transactions
                    """,
                    (user_id, user_id, user_id, user_id)
                )
                row = cursor.fetchone()
                credits_received = row["credits_received"]
                debits_sent = row["debits_sent"]
                credits_sent = row["credits_sent"]
                debits_received = row["debits_received"]

            net = credits_received - debits_sent
            legacy = (credits_received + credits_sent) - (debits_sent + debits_received)

            breakdown = {
                "credits_received": credits_received,
                "debits_sent": debits_sent,
                "credits_sent": credits_sent,
                "debits_received": debits_received,
                "net": net,
                "legacy": legacy,
            }
            logger.info(f"(BREAKDOWN) Balance breakdown for user ID {user_id}: {breakdown}")
            return self.dict_response(True, data=breakdown)
        except Exception as e:
            error_msg = f"Error calculating balance breakdown for user ID {user_id}: {str(e)}"
            logger.error(error_msg)
            return self.dict_response(False, error_msg)

    def get_contact_balance(self, user_id, contact_id):
        """
        Balance for a specific contact from the sender's perspective:
        - credits_sent: sum of amounts where from_user_id=user_id AND contact_id matches AND type='credit'
        - debits_sent: sum of amounts where from_user_id=user_id AND contact_id matches AND type='debit'
        - net = credits_sent - debits_sent
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT
                        COALESCE(SUM(CASE WHEN type = 'credit' THEN amount ELSE 0 END), 0) AS credits_sent,
                        COALESCE(SUM(CASE WHEN type = 'debit' THEN amount ELSE 0 END), 0) AS debits_sent
                    FROM transactions
                    WHERE from_user_id = ? AND contact_id = ?
                    """,
                    (user_id, contact_id)
                )
                row = cursor.fetchone()
                credits_sent = row["credits_sent"]
                debits_sent = row["debits_sent"]
            net = credits_sent - debits_sent
            data = {"credits_sent": credits_sent, "debits_sent": debits_sent, "net": net}
            logger.info(f"(CONTACT BALANCE) user={user_id}, contact={contact_id}: {data}")
            return self.dict_response(True, data=data)
        except Exception as e:
            error_msg = f"Error calculating contact balance for user {user_id} and contact {contact_id}: {str(e)}"
            logger.error(error_msg)
            return self.dict_response(False, error_msg)