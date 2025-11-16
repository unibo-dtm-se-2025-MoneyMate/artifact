"""
Authentication subsystem tests (stdlib unittest variant).

This module exercises the low-level auth.py API using a single in-memory
SQLite connection, covering:

- User registration with email + password.
- Login with session creation and verification via a token.
- Logout semantics (session invalidation).
- Lockout behavior after repeated failed logins.
- Password change flow and re-authentication with the new password.
"""

import sqlite3
import unittest
from MoneyMate.data_layer.auth import (
    init_auth_schema,
    register_user,
    authenticate,
    verify_session,
    logout,
    change_password,
)

class TestAuthStdlib(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        init_auth_schema(self.conn)

    def test_register_login_verify_logout(self):
        ok, uid, reason = register_user(self.conn, "bob", "bob@example.com", "StrongPassw0rd!")
        self.assertTrue(ok, reason)
        self.assertIsInstance(uid, int)

        res = authenticate(self.conn, "bob", "StrongPassw0rd!")
        self.assertTrue(res.ok, res.reason)
        self.assertIsNotNone(res.token)

        valid, row, err = verify_session(self.conn, res.token)
        self.assertTrue(valid, err)
        self.assertEqual(row["username"], "bob")

        logout(self.conn, res.token)
        valid2, row2, err2 = verify_session(self.conn, res.token)
        self.assertFalse(valid2)

    def test_wrong_password_and_lockout(self):
        register_user(self.conn, "carol", "carol@example.com", "AnotherStrong1!")
        # 5 tentativi falliti di default
        for _ in range(5):
            res = authenticate(self.conn, "carol", "bad")
            self.assertFalse(res.ok)
        # adesso dovrebbe essere lockato
        res2 = authenticate(self.conn, "carol", "AnotherStrong1!")
        self.assertFalse(res2.ok)
        self.assertIn("bloccato", res2.reason.lower())

    def test_change_password(self):
        ok, uid, _ = register_user(self.conn, "dave", "dave@example.com", "OldPassword123!")
        self.assertTrue(ok)
        # login con vecchia
        res = authenticate(self.conn, "dave", "OldPassword123!")
        self.assertTrue(res.ok)
        # cambio password
        ok2, reason = change_password(self.conn, uid, "OldPassword123!", "NewPassword456!")
        self.assertTrue(ok2, reason)
        # login con nuova
        res2 = authenticate(self.conn, "dave", "NewPassword456!")
        self.assertTrue(res2.ok)
        # login con vecchia deve fallire
        res3 = authenticate(self.conn, "dave", "OldPassword123!")
        self.assertFalse(res3.ok)

if __name__ == "__main__":
    unittest.main()