"""
Unit tests for UserManager (MoneyMate Data Layer).

This test file covers:
- Successful user registration
- Duplicate username registration (should fail)
- Successful user authentication
- Failed authentication (wrong password)
- Response format (success, error, data fields)
"""

import pytest
from MoneyMate.data_layer.manager import DatabaseManager
import os

TEST_DB = "test_usermanager.db"

def setup_module(module):
    # Remove test DB file before tests
    try:
        os.remove(TEST_DB)
    except FileNotFoundError:
        pass

def teardown_module(module):
    # Remove test DB file after tests
    try:
        os.remove(TEST_DB)
    except FileNotFoundError:
        pass

def test_register_and_login_user():
    db = DatabaseManager(TEST_DB)
    
    # Register a new user
    res = db.users.register_user("testuser", "password123")
    assert res["success"], f"Registration should succeed: {res}"
    user_id = res["data"]["user_id"]
    assert isinstance(user_id, int) and user_id > 0

    # Login with correct credentials
    res_login = db.users.login_user("testuser", "password123")
    assert res_login["success"], f"Login should succeed: {res_login}"
    assert res_login["data"]["user_id"] == user_id

    # Login with incorrect password
    res_login_fail = db.users.login_user("testuser", "wrongpassword")
    assert not res_login_fail["success"], "Login should fail with wrong password"
    assert res_login_fail["error"] == "Invalid credentials"

    # Register with duplicate username
    res_dup = db.users.register_user("testuser", "password123")
    assert not res_dup["success"], "Duplicate registration should fail"
    assert "already exists" in res_dup["error"]

    # Close DB before teardown to release file (especially on Windows)
    db.close()