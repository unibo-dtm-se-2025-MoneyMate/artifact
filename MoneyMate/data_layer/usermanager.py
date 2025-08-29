"""
UserManager: User account management for MoneyMate Data Layer.

This class handles user registration and authentication, maintaining separation between authentication and business logic.
It follows project best practices for modularity, structured logging, and standardized API responses.
"""

import logging
from .database import get_connection
from werkzeug.security import generate_password_hash, check_password_hash

logger = logging.getLogger(__name__)

class UserManager:
    """
    Manager for all user-related operations (registration, authentication).
    """

    def __init__(self, db_path):
        self.db_path = db_path

    def dict_response(self, success, error=None, data=None):
        """Returns a standardized dictionary for all API responses (MoneyMate convention)."""
        return {"success": success, "error": error, "data": data}

    def register_user(self, username, password):
        """
        Register a new user.
        The password is securely hashed before saving.
        Username must be unique.
        Returns: dict {success, error, data}
        data: {"user_id": int} on success
        """
        if not username or not password:
            logger.warning("Username and password are required for registration.")
            return self.dict_response(False, "Username and password are required")
        password_hash = generate_password_hash(password)
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, password_hash)
                )
                conn.commit()
                user_id = cursor.lastrowid
            logger.info(f"Registered new user: {username} (id={user_id})")
            return self.dict_response(True, data={"user_id": user_id})
        except Exception as e:
            logger.error(f"Error registering user {username}: {e}")
            if "UNIQUE constraint failed" in str(e):
                return self.dict_response(False, "Username already exists")
            return self.dict_response(False, str(e))

    def login_user(self, username, password):
        """
        Authenticate a user.
        Returns user_id if credentials are valid.
        Returns: dict {success, error, data}
        data: {"user_id": int} on success
        """
        if not username or not password:
            logger.warning("Username and password are required for authentication.")
            return self.dict_response(False, "Username and password are required")
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
                row = cursor.fetchone()
            if row and check_password_hash(row[1], password):
                logger.info(f"User authenticated successfully: {username}")
                return self.dict_response(True, data={"user_id": row[0]})
            else:
                logger.warning(f"Invalid credentials for user: {username}")
                return self.dict_response(False, "Invalid credentials")
        except Exception as e:
            logger.error(f"Error authenticating user {username}: {e}")
            return self.dict_response(False, str(e))