"""
UserManager unit tests.

This module focuses on the user management layer exposed via DatabaseManager:

- Registration and login for normal users, including duplicate detection.
- Admin registration with a forced password ("12345") and role retrieval.
- Changing and resetting passwords with proper admin role checks.
- Access_logs auditing for login, failed_login, password_change,
  password_reset, and logout events.
- Robustness around invalid roles and querying roles for non-existent users.
"""

import pytest
from MoneyMate.data_layer.manager import DatabaseManager
from MoneyMate.data_layer.database import get_connection
import os
import gc
import time

TEST_DB = "test_usermanager.db"

def setup_module(module):
    # Remove test DB file before tests
    try:
        os.remove(TEST_DB)
    except FileNotFoundError:
        pass

def teardown_module(module):
    # Remove test DB file after tests
    # Retry if file is locked (Windows)
    for _ in range(10):
        try:
            os.remove(TEST_DB)
            break
        except PermissionError:
            time.sleep(0.2)
    # If still not deleted, raise for visibility
    if os.path.exists(TEST_DB):
        raise PermissionError(f"Unable to delete test database file: {TEST_DB}")

def test_register_and_login_user():
    """Test registration and authentication for a normal user."""
    db = DatabaseManager(TEST_DB)
    res = db.users.register_user("testuser", "password123")
    assert res["success"], "Registration should succeed: {}".format(res)
    user_id = res["data"]["user_id"]
    assert isinstance(user_id, int) and user_id > 0

    res_login = db.users.login_user("testuser", "password123")
    assert res_login["success"], "Login should succeed: {}".format(res_login)
    assert res_login["data"]["user_id"] == user_id

    res_login_fail = db.users.login_user("testuser", "wrongpassword")
    assert not res_login_fail["success"], "Login should fail with wrong password"
    assert res_login_fail["error"] == "Invalid credentials"

    res_dup = db.users.register_user("testuser", "password123")
    assert not res_dup["success"], "Duplicate registration should fail"
    assert "already exists" in res_dup["error"]

    # Response format always contains keys
    assert all(k in res for k in ("success", "error", "data"))

    db.close()
    gc.collect()

def test_admin_registration_and_role():
    """Admin registration requires password '12345' and sets role to admin."""
    db = DatabaseManager(TEST_DB)
    # Try invalid admin password
    res_invalid = db.users.register_user("adminuser1", "wrong", role="admin")
    assert not res_invalid["success"]
    assert "admin password" in res_invalid["error"].lower()

    # Valid admin registration
    res_admin = db.users.register_user("adminuser", "12345", role="admin")
    assert res_admin["success"]
    admin_id = res_admin["data"]["user_id"]

    # Check role
    role_res = db.users.get_user_role(admin_id)
    assert role_res["success"]
    assert role_res["data"]["role"] == "admin"

    # Upgrade normal user to admin
    res_user = db.users.register_user("normaluser", "pw")
    assert res_user["success"]
    user_id = res_user["data"]["user_id"]
    role_set = db.users.set_user_role(admin_id, user_id, "admin")
    assert role_set["success"]
    assert db.users.get_user_role(user_id)["data"]["role"] == "admin"

    db.close()
    gc.collect()

def test_change_and_reset_password():
    """Test password change and reset (admin required for reset)."""
    db = DatabaseManager(TEST_DB)
    # Register admin and normal user
    res_adm = db.users.register_user("adm", "12345", role="admin")
    res_usr = db.users.register_user("usr", "pw")
    admin_id = res_adm["data"]["user_id"]
    user_id = res_usr["data"]["user_id"]

    # Change password for user
    change = db.users.change_password(user_id, "pw", "newpw")
    assert change["success"]
    login_new = db.users.login_user("usr", "newpw")
    assert login_new["success"]

    # Attempt change with wrong old password (should fail)
    bad_change = db.users.change_password(user_id, "wrong", "newer")
    assert not bad_change["success"]
    assert "old password" in bad_change["error"].lower()

    # Reset password as admin
    reset = db.users.reset_password(admin_id, user_id, "resetpw")
    assert reset["success"]
    login_reset = db.users.login_user("usr", "resetpw")
    assert login_reset["success"]

    # Non-admin cannot reset
    notadm_reset = db.users.reset_password(user_id, admin_id, "failpw")
    assert not notadm_reset["success"]
    assert "admin privileges" in notadm_reset["error"].lower()

    db.close()
    gc.collect()

def test_access_logs_auditing():
    """
    Verify that access_logs records login, failed_login, password_change, password_reset, and logout events.
    Uses deltas to avoid flaky counts when tests run multiple times.
    """
    db = DatabaseManager(TEST_DB)
    # Unique users to avoid collisions with other tests
    res_admin = db.users.register_user("audit_admin", "12345", role="admin")
    if not res_admin["success"]:
        # user may exist if the test re-runs; just login to retrieve id
        admin_id = db.users.login_user("audit_admin", "12345")["data"]["user_id"]
    else:
        admin_id = res_admin["data"]["user_id"]

    res_user = db.users.register_user("audit_user", "pw")
    if not res_user["success"]:
        user_id = db.users.login_user("audit_user", "pw")["data"]["user_id"]
    else:
        user_id = res_user["data"]["user_id"]

    def get_count(action, uid):
        with get_connection(TEST_DB) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM access_logs WHERE user_id IS ? AND action = ?",
                (uid, action),
            )
            return cur.fetchone()[0]

    # Baselines
    base_login = get_count("login", user_id)
    base_failed = get_count("failed_login", user_id)
    base_change = get_count("password_change", user_id)
    base_reset = get_count("password_reset", user_id)
    base_logout = get_count("logout", user_id)

    # Trigger events
    assert db.users.login_user("audit_user", "pw")["success"]
    assert not db.users.login_user("audit_user", "wrong")["success"]
    assert db.users.change_password(user_id, "pw", "pw2")["success"]
    assert db.users.reset_password(admin_id, user_id, "pw3")["success"]
    assert db.users.logout_user(user_id)["success"]

    # Post counts (expect +1 for each)
    assert get_count("login", user_id) == base_login + 1
    assert get_count("failed_login", user_id) == base_failed + 1
    assert get_count("password_change", user_id) == base_change + 1
    assert get_count("password_reset", user_id) == base_reset + 1
    assert get_count("logout", user_id) == base_logout + 1

    db.close()
    gc.collect()

def test_user_role_invalid_and_role_query_nonexistent():
    """
    Additional robustness:
    - Setting an invalid role should fail with a clear error.
    - Querying role for a non-existent user should return an error.
    """
    db = DatabaseManager(TEST_DB)
    # Admin + user for role change
    adm = db.users.register_user("role_admin", "12345", role="admin")
    assert adm["success"]
    admin_id = adm["data"]["user_id"]
    usr = db.users.register_user("role_user", "pw")
    assert usr["success"]
    user_id = usr["data"]["user_id"]

    bad = db.users.set_user_role(admin_id, user_id, "superuser")
    assert isinstance(bad, dict)
    assert not bad["success"]
    assert "role" in (bad["error"] or "").lower()

    # Non-existent user_id
    notfound = db.users.get_user_role(999999)
    assert isinstance(notfound, dict)
    assert not notfound["success"]
    assert "not found" in (notfound["error"] or "").lower()

    db.close()
    gc.collect()