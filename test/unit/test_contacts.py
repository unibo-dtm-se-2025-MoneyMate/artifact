import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import pytest
from MoneyMate.data_layer import DatabaseManager

TEST_DB = "test_contacts.db"

@pytest.fixture
def db():
    # Setup: create a clean test database
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    dbm = DatabaseManager(TEST_DB)
    yield dbm
    # Teardown: remove the test database after tests
    if hasattr(dbm, "close"):
        dbm.close()
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_add_contact_valid(db):
    # Test adding a valid contact
    res = db.add_contact("Mario")
    assert res["success"]
    contacts = db.get_contacts()["data"]
    assert any(c["name"] == "Mario" for c in contacts)

def test_add_contact_empty_name(db):
    # Test failure when contact name is empty
    res = db.add_contact("")
    assert not res["success"]
    assert "name" in res["error"].lower()

def test_delete_contact(db):
    # Test deleting a contact by ID
    db.add_contact("Luca")
    cid = db.get_contacts()["data"][0]["id"]
    res = db.delete_contact(cid)
    assert res["success"]
    assert db.get_contacts()["data"] == []