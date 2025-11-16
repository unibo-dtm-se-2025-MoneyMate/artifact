"""
Contacts manager tests.

These tests exercise the ContactsManager through DatabaseManager to ensure:

- Adding a valid contact for a user and retrieving it.
- Validation of empty/None contact names with clear error messages.
- Deleting a contact by id and observing an empty list afterwards.
- Proper per-test isolation and Windows-safe DB cleanup.
"""

import sys
import os
import gc
import time
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from MoneyMate.data_layer.manager import DatabaseManager

TEST_DB = "test_contacts.db"

@pytest.fixture
def db():
    """
    Pytest fixture for DatabaseManager.
    Ensures isolation and proper cleanup for each test.
    """
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    dbm = DatabaseManager(TEST_DB)
    # Add a test user and store its ID
    user_id = dbm.users.register_user("contactsuser", "pw")["data"]["user_id"]
    dbm._test_user_id = user_id
    yield dbm
    if hasattr(dbm, "close"):
        dbm.close()
    gc.collect()
    for _ in range(10):
        try:
            if os.path.exists(TEST_DB):
                os.remove(TEST_DB)
            break
        except PermissionError:
            time.sleep(0.2)
    if os.path.exists(TEST_DB):
        raise PermissionError(f"Unable to delete test database file: {TEST_DB}")

def test_add_contact_valid(db):
    """
    Test adding a valid contact.
    Verifies that the contact is correctly added and retrievable for the user.
    """
    res = db.contacts.add_contact("Mario", db._test_user_id)
    assert isinstance(res, dict)
    assert res["success"]
    contacts = db.contacts.get_contacts(db._test_user_id)["data"]
    assert any(c["name"] == "Mario" for c in contacts)

@pytest.mark.parametrize("invalid_name", ["", None])
def test_add_contact_empty_name(db, invalid_name):
    """
    Test failure when contact name is empty or None.
    Verifies that an appropriate error message is returned.
    """
    res = db.contacts.add_contact(invalid_name, db._test_user_id)
    assert isinstance(res, dict)
    assert not res["success"]
    assert "name" in res["error"].lower()

def test_delete_contact(db):
    """
    Test deleting a contact by ID.
    Verifies that after deletion the contact list is empty for the user.
    """
    db.contacts.add_contact("Luca", db._test_user_id)
    cid = db.contacts.get_contacts(db._test_user_id)["data"][0]["id"]
    res = db.contacts.delete_contact(cid, db._test_user_id)
    assert isinstance(res, dict)
    assert res["success"]
    assert db.contacts.get_contacts(db._test_user_id)["data"] == []