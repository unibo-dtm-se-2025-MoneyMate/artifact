"""
Transaction management layer for the MoneyMate data model.

This module defines TransactionsManager, responsible for:

- CRUD operations on the transactions table with validation (type/amount/date).
- Ensuring consistency of user and contact relationships.
- Auto-resolving recipient users from contacts (virtual contact_* users).
- Computing user balances and breakdowns:
  - legacy balance, net balance, and per-contact balances.
- Providing dict-based responses suitable for DatabaseManager and the GUI API.

It is the core of the peer-to-peer debt/credit tracking logic in MoneyMate.
"""

import sqlite3
from .database import get_connection
from .validation import validate_transaction
from datetime import datetime
from .contacts import ContactsManager
from .logging_config import get_logger


logger = get_logger(__name__)

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
    Manager class for handling transaction-related database operations.
    Includes CRUD, user/contact checks, and balance computations.

    New: to_user_id can be omitted (None) if contact_id is provided.
    In that case, we auto-resolve/create a counterparty user for the given contact.
    """

    def __init__(self, db_path, contacts_manager: ContactsManager = None, db_manager=None):
        self.db_path = db_path
        self.contacts_manager = contacts_manager
        self._db_manager = db_manager

    def dict_response(self, success, error=None, data=None):
        return {"success": success, "error": error, "data": data}

    # ---------------------
    # CRUD TRANSACTIONS
    # ---------------------
    def add_transaction(self, from_user_id, to_user_id, type_, amount, date, description="", contact_id=None):
        """
        Add a transaction.
        - If to_user_id is None and contact_id is provided, we create (if needed) and use a counterparty
          user with username 'contact_{contact_id}'.
        """
        err = validate_transaction(type_, amount, date)
        if err:
            logger.warning(f"Validation failed for transaction: {err}")
            return self.dict_response(False, err)

        if not self._user_exists(from_user_id):
            return self.dict_response(False, "Sender user does not exist")

        # Auto-resolve recipient from contact if to_user_id is None
        if to_user_id is None:
            if not contact_id:
                return self.dict_response(False, "Recipient not specified (select a Contact)")
            if not (self.contacts_manager and self.contacts_manager.contact_exists(contact_id, from_user_id)):
                return self.dict_response(False, "Contact does not exist")
            to_user_id = self._ensure_counterparty_user(contact_id)

        if not self._user_exists(to_user_id):
            return self.dict_response(False, "Receiver user does not exist")
        if from_user_id == to_user_id:
            return self.dict_response(False, "Sender and receiver must be different")

        # contact_id (if provided) must belong to sender (already checked above for auto-mode)
        if contact_id and self.contacts_manager and not self.contacts_manager.contact_exists(contact_id, from_user_id):
            return self.dict_response(False, "Contact does not exist")

        try:
            with get_connection(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO transactions (from_user_id, to_user_id, type, amount, date, description, contact_id) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (from_user_id, to_user_id, type_, float(amount), date, description, contact_id)
                )
                conn.commit()
            logger.info(f"Transaction from user id={from_user_id} to user id={to_user_id} amount={float(amount)}")
            return self.dict_response(True)
        except Exception as e:
            logger.error(f"Error adding transaction: {e}")
            return self.dict_response(False, str(e))
        
    def update_transaction(self, transaction_id, user_id, type_=None, amount=None, date=None, description=None, contact_id=None):
        fields = {}
        if type_ is not None:
            type_norm = type_.lower().strip() if isinstance(type_, str) else None
            if type_norm not in ("debit", "credit"):
                return self.dict_response(False, "Invalid type (debit/credit)")
            fields["type"] = type_norm
        if amount is not None:
            try:
                val = float(amount)
            except Exception:
                return self.dict_response(False, "Invalid amount")
            if val <= 0:
                return self.dict_response(False, "Amount must be positive")
            fields["amount"] = val
        if date is not None:
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except Exception:
                return self.dict_response(False, "Invalid date format (YYYY-MM-DD required)")
            fields["date"] = date
        if description is not None:
            fields["description"] = description
        if contact_id is not None and self.contacts_manager and not self.contacts_manager.contact_exists(contact_id, user_id):
            return self.dict_response(False, "Contact does not exist")
        if contact_id is not None:
            fields["contact_id"] = contact_id

        if not fields:
            return self.dict_response(False, "No fields to update")

        try:
            with get_connection(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                set_frag = ", ".join(f"{k} = ?" for k in fields.keys())
                params = list(fields.values()) + [transaction_id, user_id]
                cursor.execute(f"UPDATE transactions SET {set_frag} WHERE id = ? AND from_user_id = ?", tuple(params))
                updated = cursor.rowcount or 0
                conn.commit()
            return self.dict_response(True, data={"updated": updated})
        except Exception as e:
            logger.error(f"Error updating transaction: {e}")
            return self.dict_response(False, str(e))

    def delete_transaction(self, transaction_id, user_id):
        try:
            with get_connection(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("DELETE FROM transactions WHERE id = ? AND from_user_id = ?", (transaction_id, user_id))
                deleted = cursor.rowcount or 0
                conn.commit()
            logger.info(f"Deleted transaction id={transaction_id} by user id={user_id} (deleted={deleted})")
            return self.dict_response(True, data={"deleted": deleted})
        except Exception as e:
            logger.error(f"Error deleting transaction: {e}")
            return self.dict_response(False, str(e))

    def get_transactions(self, user_id, as_sender=True, is_admin=False, order="date_desc", limit=None, offset=None, date_from=None, date_to=None, contact_id=None):
        try:
            with get_connection(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                params, where_parts = [], []
                if is_admin:
                    if not self._is_admin(user_id):
                        return self.dict_response(False, "Admin privileges required")
                else:
                    if as_sender:
                        where_parts.append("from_user_id = ?")
                        params.append(user_id)
                    else:
                        where_parts.append("to_user_id = ?")
                        params.append(user_id)
                if contact_id:
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

            transactions = [{k: r[k] for k in r.keys()} for r in rows]
            return self.dict_response(True, data=transactions)
        except Exception as e:
            logger.error(f"Error retrieving transactions: {e}")
            return self.dict_response(False, str(e))

    # ---------------------
    # BALANCE / ANALYTICS
    # ---------------------
    def get_user_balance(self, user_id):
        try:
            with get_connection(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT type, SUM(amount) as total FROM transactions WHERE from_user_id = ? OR to_user_id = ? GROUP BY type",
                    (user_id, user_id)
                )
                rows = cursor.fetchall()
            total_credit = sum(r["total"] for r in rows if r["type"] == "credit")
            total_debit = sum(r["total"] for r in rows if r["type"] == "debit")
            balance = total_credit - total_debit
            logger.info(f"Calculated balance for user ID={user_id}: legacy_balance={balance}")
            return self.dict_response(True, data=balance)
        except Exception as e:
            logger.error(f"Error calculating user balance: {e}")
            return self.dict_response(False, str(e))

    def get_user_net_balance(self, user_id):
        try:
            with get_connection(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT
                        COALESCE(SUM(CASE WHEN to_user_id = ? AND type='credit' THEN amount ELSE 0 END),0) AS credits_received,
                        COALESCE(SUM(CASE WHEN from_user_id = ? AND type='debit' THEN amount ELSE 0 END),0) AS debits_sent
                    FROM transactions
                    """,
                    (user_id, user_id)
                )
                row = cursor.fetchone()
            net = row["credits_received"] - row["debits_sent"]
            logger.info(f"Calculated balance for user ID={user_id}: net={net}")
            return self.dict_response(True, data=net)
        except Exception as e:
            logger.error(f"Error calculating net balance: {e}")
            return self.dict_response(False, str(e))

    def get_user_balance_breakdown(self, user_id):
        try:
            with get_connection(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT
                        COALESCE(SUM(CASE WHEN to_user_id = ? AND type='credit' THEN amount ELSE 0 END),0) AS credits_received,
                        COALESCE(SUM(CASE WHEN from_user_id = ? AND type='debit' THEN amount ELSE 0 END),0) AS debits_sent,
                        COALESCE(SUM(CASE WHEN from_user_id = ? AND type='credit' THEN amount ELSE 0 END),0) AS credits_sent,
                        COALESCE(SUM(CASE WHEN to_user_id = ? AND type='debit' THEN amount ELSE 0 END),0) AS debits_received
                    FROM transactions
                    """,
                    (user_id, user_id, user_id, user_id)
                )
                row = cursor.fetchone()
            net = row["credits_received"] - row["debits_sent"]
            legacy = (row["credits_received"] + row["credits_sent"]) - (row["debits_sent"] + row["debits_received"])
            breakdown = {
                "credits_received": row["credits_received"],
                "debits_sent": row["debits_sent"],
                "credits_sent": row["credits_sent"],
                "debits_received": row["debits_received"],
                "net": net,
                "legacy": legacy
            }
            logger.info(f"Calculated balance for user ID={user_id}: breakdown={breakdown}")
            return self.dict_response(True, data=breakdown)
        except Exception as e:
            logger.error(f"Error calculating balance breakdown: {e}")
            return self.dict_response(False, str(e))

    def get_contact_balance(self, user_id, contact_id):
        try:
            with get_connection(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT
                        COALESCE(SUM(CASE WHEN type='credit' THEN amount ELSE 0 END),0) AS credits_sent,
                        COALESCE(SUM(CASE WHEN type='debit' THEN amount ELSE 0 END),0) AS debits_sent
                    FROM transactions
                    WHERE from_user_id=? AND contact_id=?
                    """,
                    (user_id, contact_id)
                )
                row = cursor.fetchone()
            net = row["credits_sent"] - row["debits_sent"]
            data = {"credits_sent": row["credits_sent"], "debits_sent": row["debits_sent"], "net": net}
            return self.dict_response(True, data=data)
        except Exception as e:
            logger.error(f"Error calculating contact balance: {e}")
            return self.dict_response(False, str(e))

    # ---------------------
    # HELPERS
    # ---------------------
    def _user_exists(self, user_id):
        try:
            with get_connection(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM users WHERE id=?", (user_id,))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking user existence: {e}")
            return False

    def _is_admin(self, user_id):
        try:
            with get_connection(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT role FROM users WHERE id=?", (user_id,))
                row = cursor.fetchone()
                return bool(row and row["role"] == "admin")
        except Exception as e:
            logger.error(f"Error checking admin role: {e}")
            return False

    def _ensure_counterparty_user(self, contact_id: int) -> int:
        """
        Ensure there is a 'virtual' user backing the given contact.
        Username format: 'contact_{contact_id}'.
        Returns the user's id (creates it if needed).
        """
        uname = f"contact_{int(contact_id)}"
        with get_connection(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            row = cur.execute("SELECT id FROM users WHERE username = ?", (uname,)).fetchone()
            if row:
                return int(row["id"])
            # Create a minimal user row for the counterparty
            cur.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'user')",
                (uname, "",)
            )
            conn.commit()
            new_id = int(cur.execute("SELECT last_insert_rowid()").fetchone()[0])
            return new_id