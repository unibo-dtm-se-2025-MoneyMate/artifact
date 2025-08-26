import sys
import os
import gc
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
    # Setup: create a clean test database
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    dbm = DatabaseManager(TEST_DB)
    yield dbm
    # Teardown: release all managers and remove the test database
    if hasattr(dbm, "close"):
        dbm.close()
    gc.collect()  # Ensure all SQLite handles are closed
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_add_contact_valid(db):
    """
    Test adding a valid contact.
    Verifies that the contact is correctly added and retrievable.
    """
    res = db.contacts.add_contact("Mario")
    assert isinstance(res, dict)
    assert res["success"]
    contacts = db.contacts.get_contacts()["data"]
    assert any(c["name"] == "Mario" for c in contacts)

@pytest.mark.parametrize("invalid_name", ["", None])
def test_add_contact_empty_name(db, invalid_name):
    """
    Test failure when contact name is empty or None.
    Verifies that an appropriate error message is returned.
    """
    res = db.contacts.add_contact(invalid_name)
    assert isinstance(res, dict)
    assert not res["success"]
    assert "name" in res["error"].lower()

def test_delete_contact(db):
    """
    Test deleting a contact by ID.
    Verifies that after deletion the contact list is empty.
    """
    db.contacts.add_contact("Luca")
    cid = db.contacts.get_contacts()["data"][0]["id"]
    res = db.contacts.delete_contact(cid)
    assert isinstance(res, dict)
    assert res["success"]
    assert db.contacts.get_contacts()["data"] == []