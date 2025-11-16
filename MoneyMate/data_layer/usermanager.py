"""
High-level user management for the MoneyMate data layer.

UserManager encapsulates operations on the users table and related
access_logs, including:

- User registration with hashed passwords and simple admin registration rules.
- Authentication (username + password) and access logging (login/fail/logout).
- Password changes and admin-driven password resets.
- Role management (user/admin) with privilege checks.
- Lookup helpers used by the unified API (get_user_by_username, list_users).

All methods return dict envelopes compatible with the MoneyMate API and GUI.
"""

from typing import Any, Dict, Optional
from .database import get_connection
from werkzeug.security import generate_password_hash, check_password_hash
from .database import get_connection
from .manager import DatabaseManager

from .logging_config import get_logger
logger = get_logger(__name__)

class UserManager:
    """
    Manager class for handling user-related operations.
    """

    def __init__(self, db_path, db_manager=None):  # <-- aggiunto db_manager opzionale
        self.db_path = db_path
        self._db_manager = db_manager  # opzionale, utile per future necessità

    def dict_response(self, success: bool, error: Optional[str] = None, data: Any = None) -> Dict[str, Any]:
        """Returns a standardized dictionary for all API responses (MoneyMate convention)."""
        return {"success": success, "error": error, "data": data}

    # --- Internal helpers (best-effort, resilient if table does not exist) ---
    def _log_access(self, user_id: Optional[int], action: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> None:
        """
        Append an entry into access_logs (if the table exists).
        Silently ignore errors to avoid impacting auth flows.
        """
        try:
            with get_connection(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_schema WHERE type='table' AND name='access_logs';")
                if cur.fetchone() is None:
                    return
                cur.execute(
                    "INSERT INTO access_logs (user_id, action, ip_address, user_agent) VALUES (?, ?, ?, ?)",
                    (user_id, action, ip_address, user_agent),
                )
                conn.commit()
        except Exception as e:
            logger.debug(f"Access log write skipped ({action}) for user {user_id}: {e}")

    def register_user(self, username: str, password: str, role: str = "user") -> Dict[str, Any]:
        """
        Register a new user.
        The password is securely hashed before saving.
        Username must be unique.
        Role is optional and defaults to 'user'.
        For admin, password must be '12345'.
        Returns: dict {success, error, data}
        data: {"user_id": int} on success
        """
        username_norm = username.strip() if isinstance(username, str) else username
        password_norm = password.strip() if isinstance(password, str) else password
        if not username_norm or not password_norm:
            logger.warning("Username and password are required for registration.")
            return self.dict_response(False, "Username and password are required")
        if role == "admin" and password_norm != "12345":
            logger.warning("Admin registration failed: password for admin must be '12345'")
            return self.dict_response(False, "Admin password must be '12345'")
        password_hash = generate_password_hash(password_norm)
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                    (username_norm, password_hash, role)
                )
                conn.commit()
                user_id = cursor.lastrowid
            logger.info(f"Registered new user: {username_norm} (id={user_id}, role={role})")
            return self.dict_response(True, data={"user_id": user_id})
        except Exception as e:
            logger.error(f"Error registering user {username_norm}: {e}")
            if "UNIQUE constraint failed" in str(e):
                return self.dict_response(False, "Username already exists")
            return self.dict_response(False, str(e))

    def login_user(self, username: str, password: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Dict[str, Any]:
        """
        Authenticate a user.
        Returns user_id and role if credentials are valid.
        Returns: dict {success, error, data}
        data: {"user_id": int, "role": str} on success
        """
        username_norm = username.strip() if isinstance(username, str) else username
        password_norm = password.strip() if isinstance(password, str) else password
        if not username_norm or not password_norm:
            logger.warning("Username and password are required for authentication.")
            return self.dict_response(False, "Username and password are required")
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, password_hash, role FROM users WHERE username = ?", (username_norm,))
                row = cursor.fetchone()
            if row and check_password_hash(row[1], password_norm):
                logger.info(f"User authenticated successfully: {username_norm}")
                self._log_access(user_id=row[0], action="login", ip_address=ip_address, user_agent=user_agent)
                return self.dict_response(True, data={"user_id": row[0], "role": row[2]})
            else:
                logger.warning(f"Invalid credentials for user: {username_norm}")
                uid = row[0] if row else None
                self._log_access(user_id=uid, action="failed_login", ip_address=ip_address, user_agent=user_agent)
                return self.dict_response(False, "Invalid credentials")
        except Exception as e:
            logger.error(f"Error authenticating user {username_norm}: {e}")
            return self.dict_response(False, str(e))

    def logout_user(self, user_id: int, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Dict[str, Any]:
        self._log_access(user_id=user_id, action="logout", ip_address=ip_address, user_agent=user_agent)
        logger.info(f"User logout logged for user_id {user_id}")
        return self.dict_response(True)

    def change_password(self, user_id: int, old_password: str, new_password: str) -> Dict[str, Any]:
        new_norm = new_password.strip() if isinstance(new_password, str) else new_password
        old_norm = old_password.strip() if isinstance(old_password, str) else old_password
        if not new_norm:
            logger.warning("New password is required for password change.")
            return self.dict_response(False, "New password is required")
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
                row = cursor.fetchone()
                if not row or not check_password_hash(row[0], old_norm):
                    logger.warning(f"Password change failed: old password incorrect for user_id {user_id}")
                    return self.dict_response(False, "Old password incorrect")
                new_hash = generate_password_hash(new_norm)
                cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
                conn.commit()
            logger.info(f"Password changed successfully for user_id {user_id}")
            self._log_access(user_id=user_id, action="password_change")
            return self.dict_response(True)
        except Exception as e:
            logger.error(f"Error changing password for user_id {user_id}: {e}")
            return self.dict_response(False, str(e))

    def reset_password(self, admin_user_id: int, target_user_id: int, new_password: str) -> Dict[str, Any]:
        new_norm = new_password.strip() if isinstance(new_password, str) else new_password
        if not new_norm:
            logger.warning("New password required for password reset.")
            return self.dict_response(False, "New password is required")
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT role FROM users WHERE id = ?", (admin_user_id,))
                admin_row = cursor.fetchone()
                if not admin_row or admin_row[0] != "admin":
                    logger.warning(f"Password reset failed: user_id {admin_user_id} is not admin")
                    return self.dict_response(False, "Admin privileges required")
                new_hash = generate_password_hash(new_norm)
                cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, target_user_id))
                conn.commit()
            logger.info(f"Password reset for user_id {target_user_id} by admin {admin_user_id}")
            self._log_access(user_id=target_user_id, action="password_reset")
            return self.dict_response(True)
        except Exception as e:
            logger.error(f"Error resetting password for user_id {target_user_id}: {e}")
            return self.dict_response(False, str(e))

    def get_user_role(self, user_id: int) -> Dict[str, Any]:
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
                row = cursor.fetchone()
                if not row:
                    return self.dict_response(False, "User not found")
                return self.dict_response(True, data={"role": row[0]})
        except Exception as e:
            logger.error(f"Error fetching role for user_id {user_id}: {e}")
            return self.dict_response(False, str(e))

    def set_user_role(self, admin_user_id: int, target_user_id: int, new_role: str) -> Dict[str, Any]:
        allowed_roles = {"user", "admin"}
        if new_role not in allowed_roles:
            logger.warning(f"Attempted to set invalid role '{new_role}' for user_id {target_user_id}")
            return self.dict_response(False, f"Role must be one of {allowed_roles}")
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT role FROM users WHERE id = ?", (admin_user_id,))
                admin_row = cursor.fetchone()
                if not admin_row or admin_row[0] != "admin":
                    logger.warning(f"Role change failed: user_id {admin_user_id} is not admin")
                    return self.dict_response(False, "Admin privileges required")
                cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, target_user_id))
                conn.commit()
            logger.info(f"Role for user_id {target_user_id} set to '{new_role}' by admin {admin_user_id}")
            return self.dict_response(True)
        except Exception as e:
            logger.error(f"Error setting role for user_id {target_user_id}: {e}")
            return self.dict_response(False, str(e))

    # --- NEW METHODS FOR USER LOOKUP (Needed by api_get_user_by_username) ---

    def get_user_by_username(self, username: str) -> Dict[str, Any]:
        """
        Return user record by exact username.
        Envelope: {success, error, data: {id, username, role}|None}
        """
        username_norm = username.strip() if isinstance(username, str) else username
        if not username_norm:
            return self.dict_response(False, "Username is required")
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, username, role FROM users WHERE username = ?", (username_norm,))
                row = cursor.fetchone()
            if not row:
                return self.dict_response(False, "User not found")
            return self.dict_response(True, data={"id": row[0], "username": row[1], "role": row[2]})
        except Exception as e:
            logger.error(f"Error in get_user_by_username({username_norm}): {e}")
            return self.dict_response(False, str(e))

    def list_users(self) -> Dict[str, Any]:
        """
        Return a list of all users (id, username, role).
        Envelope: {success, error, data: [ {id, username, role}, ... ]}
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, username, role FROM users ORDER BY id ASC")
                rows = cursor.fetchall()
            data = [{"id": r[0], "username": r[1], "role": r[2]} for r in rows]
            return self.dict_response(True, data=data)
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return self.dict_response(False, str(e))