import gc
import pytest
from MoneyMate.data_layer.manager import DatabaseManager

@pytest.fixture
def dbm(tmp_path):
    """
    Provide a fresh DatabaseManager instance backed by a per-test temporary DB file.
    Using tmp_path avoids Windows file locks and manual cleanup.
    """
    db_path = tmp_path / "test_manager.db"
    db = DatabaseManager(str(db_path))
    yield db
    if hasattr(db, "close"):
        db.close()
    gc.collect()

def test_database_manager_list_tables(dbm):
    """Test that the DatabaseManager can list all tables in the database."""
    tables = dbm.list_tables()["data"]
    assert set(tables) >= {"users", "contacts", "expenses", "transactions"}

def test_manager_admin_role_support(dbm):
    """Test that manager supports admin role logic."""
    res = dbm.users.register_user("admin", "12345", role="admin")
    assert res["success"]
    admin_id = res["data"]["user_id"]
    role = dbm.users.get_user_role(admin_id)
    assert role["success"]
    assert role["data"]["role"] == "admin"

def test_manager_can_upgrade_user_role(dbm):
    """Test upgrading a normal user to admin via manager."""
    admin_res = dbm.users.register_user("adminx", "12345", role="admin")
    user_res = dbm.users.register_user("usertest", "pw")
    assert user_res["success"]
    admin_id = admin_res["data"]["user_id"]
    user_id = user_res["data"]["user_id"]
    upgrade_res = dbm.users.set_user_role(admin_id, user_id, "admin")
    assert upgrade_res["success"]
    assert dbm.users.get_user_role(user_id)["data"]["role"] == "admin"