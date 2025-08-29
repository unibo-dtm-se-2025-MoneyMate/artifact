"""
UserManager: User account management for MoneyMate Data Layer.

This class handles user registration, authentication, password management, and role support.
Maintains separation between authentication and business logic.
Follows best practices for modularity, dependency injection, configurability, error handling, and resource management.
"""

import logging
from .database import get_connection
from werkzeug.security import generate_password_hash, check_password_hash

logger = logging.getLogger(__name__)

class UserManager:
    """
    Manager for all user-related operations:
    - Registration
    - Authentication
    - Password management (reset/change)
    - Role management (preparation for future extensions)
    """

    def __init__(self, db_path):
        self.db_path = db_path

    def dict_response(self, success, error=None, data=None):
        """Returns a standardized dictionary for all API responses (MoneyMate convention)."""
        return {"success": success, "error": error, "data": data}

    # --- Internal helpers (best-effort, resilient if table does not exist) ---
    def _log_access(self, user_id, action, ip_address=None, user_agent=None):
        """
        Append an entry into access_logs (if the table exists).
        Silently ignore errors to avoid impacting auth flows.
        """
        try:
            with get_connection(self.db_path) as conn:
                cur = conn.cursor()
                # Verify table existence once (cheap PRAGMA)
                # Use sqlite_schema for consistency with other introspection queries
                cur.execute("SELECT name FROM sqlite_schema WHERE type='table' AND name='access_logs';")
                if cur.fetchone() is None:
                    return  # schema not yet migrated; skip logging
                cur.execute(
                    "INSERT INTO access_logs (user_id, action, ip_address, user_agent) VALUES (?, ?, ?, ?)",
                    (user_id, action, ip_address, user_agent),
                )
                conn.commit()
        except Exception as e:
            # Do not raise; only log
            logger.debug(f"Access log write skipped ({action}) for user {user_id}: {e}")

    def register_user(self, username, password, role="user"):
        """
        Register a new user.
        The password is securely hashed before saving.
        Username must be unique.
        Role is optional and defaults to 'user'.
        For admin, password must be '12345'.
        Returns: dict {success, error, data}
        data: {"user_id": int} on success
        """
        if not username or not password:
            logger.warning("Username and password are required for registration.")
            return self.dict_response(False, "Username and password are required")
        if role == "admin" and password != "12345":
            logger.warning("Admin registration failed: password for admin must be '12345'")
            return self.dict_response(False, "Admin password must be '12345'")
        password_hash = generate_password_hash(password)
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                    (username, password_hash, role)
                )
                conn.commit()
                user_id = cursor.lastrowid
            logger.info(f"Registered new user: {username} (id={user_id}, role={role})")
            # Registration could be logged if needed (not a security event like auth)
            return self.dict_response(True, data={"user_id": user_id})
        except Exception as e:
            logger.error(f"Error registering user {username}: {e}")
            if "UNIQUE constraint failed" in str(e):
                return self.dict_response(False, "Username already exists")
            return self.dict_response(False, str(e))

    def login_user(self, username, password):
        """
        Authenticate a user.
        Returns user_id and role if credentials are valid.
        Returns: dict {success, error, data}
        data: {"user_id": int, "role": str} on success
        """
        if not username or not password:
            logger.warning("Username and password are required for authentication.")
            return self.dict_response(False, "Username and password are required")
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, password_hash, role FROM users WHERE username = ?", (username,))
                row = cursor.fetchone()
            if row and check_password_hash(row[1], password):
                logger.info(f"User authenticated successfully: {username}")
                self._log_access(user_id=row[0], action="login")
                return self.dict_response(True, data={"user_id": row[0], "role": row[2]})
            else:
                logger.warning(f"Invalid credentials for user: {username}")
                # If we know the user id (username exists), log failed_login with that id
                uid = row[0] if row else None
                self._log_access(user_id=uid, action="failed_login")
                return self.dict_response(False, "Invalid credentials")
        except Exception as e:
            logger.error(f"Error authenticating user {username}: {e}")
            return self.dict_response(False, str(e))

    def change_password(self, user_id, old_password, new_password):
        """
        Change password for a user, requires old password for confirmation.
        Returns: dict {success, error, data}
        """
        if not new_password:
            logger.warning("New password is required for password change.")
            return self.dict_response(False, "New password is required")
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
                row = cursor.fetchone()
                if not row or not check_password_hash(row[0], old_password):
                    logger.warning(f"Password change failed: old password incorrect for user_id {user_id}")
                    return self.dict_response(False, "Old password incorrect")
                new_hash = generate_password_hash(new_password)
                cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
                conn.commit()
            logger.info(f"Password changed successfully for user_id {user_id}")
            self._log_access(user_id=user_id, action="password_change")
            return self.dict_response(True)
        except Exception as e:
            logger.error(f"Error changing password for user_id {user_id}: {e}")
            return self.dict_response(False, str(e))

    def reset_password(self, admin_user_id, target_user_id, new_password):
        """
        Reset password for another user (admin only).
        Returns: dict {success, error, data}
        """
        if not new_password:
            logger.warning("New password required for password reset.")
            return self.dict_response(False, "New password is required")
        try:
            # Check admin privileges
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT role FROM users WHERE id = ?", (admin_user_id,))
                admin_row = cursor.fetchone()
                if not admin_row or admin_row[0] != "admin":
                    logger.warning(f"Password reset failed: user_id {admin_user_id} is not admin")
                    return self.dict_response(False, "Admin privileges required")
                # Reset password for target user
                new_hash = generate_password_hash(new_password)
                cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, target_user_id))
                conn.commit()
            logger.info(f"Password reset for user_id {target_user_id} by admin {admin_user_id}")
            self._log_access(user_id=target_user_id, action="password_reset")
            return self.dict_response(True)
        except Exception as e:
            logger.error(f"Error resetting password for user_id {target_user_id}: {e}")
            return self.dict_response(False, str(e))

    def get_user_role(self, user_id):
        """
        Get the role of a user.
        Returns: dict {success, error, data}
        """
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

    def set_user_role(self, admin_user_id, target_user_id, new_role):
        """
        Update the role of a user (admin only).
        Returns: dict {success, error, data}
        """
        allowed_roles = {"user", "admin"}
        if new_role not in allowed_roles:
            logger.warning(f"Attempted to set invalid role '{new_role}' for user_id {target_user_id}")
            return self.dict_response(False, f"Role must be one of {allowed_roles}")
        try:
            # Check admin privileges
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT role FROM users WHERE id = ?", (admin_user_id,))
                admin_row = cursor.fetchone()
                if not admin_row or admin_row[0] != "admin":
                    logger.warning(f"Role change failed: user_id {admin_user_id} is not admin")
                    return self.dict_response(False, "Admin privileges required")
                # Update target user's role
                cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, target_user_id))
                conn.commit()
            logger.info(f"Role for user_id {target_user_id} set to '{new_role}' by admin {admin_user_id}")
            return self.dict_response(True)
        except Exception as e:
            logger.error(f"Error setting role for user_id {target_user_id}: {e}")
            return self.dict_response(False, str(e))