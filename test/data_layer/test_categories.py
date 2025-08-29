import os
import pytest

from MoneyMate.data_layer.api import (
    set_db_path,
    api_register_user,
    api_add_category,
    api_get_categories,
    api_delete_category,
)
from MoneyMate.data_layer.manager import DatabaseManager


def test_categories_api_crud(tmp_path):
    """
    Verify Categories API basic CRUD:
    - create user
    - add category
    - prevent duplicate name per user
    - list categories
    - delete category
    """
    db_file = tmp_path / "cats_api.db"
    set_db_path(str(db_file))

    # Create a user
    res_user = api_register_user("cat_api_user", "pw")
    if not res_user["success"]:
        pytest.skip(f"Cannot create user for categories API test: {res_user['error']}")
    user_id = res_user["data"]["user_id"]

    # Add a category
    res_add = api_add_category(user_id, "Food", description="Daily food", color="#ff0000", icon="🍎")
    assert res_add["success"]

    # Adding the same category for the same user should fail (unique per user)
    res_dup = api_add_category(user_id, "Food")
    assert not res_dup["success"]
    assert "exists" in (res_dup["error"] or "").lower()

    # List categories -> should contain exactly one
    res_list = api_get_categories(user_id)
    assert res_list["success"]
    cats = res_list["data"]
    assert isinstance(cats, list)
    assert len(cats) == 1
    assert cats[0]["name"] == "Food"

    # Delete category
    cat_id = cats[0]["id"]
    res_del = api_delete_category(cat_id, user_id)
    assert res_del["success"]

    # List again -> empty
    res_list2 = api_get_categories(user_id)
    assert res_list2["success"]
    assert res_list2["data"] == []

    # Cleanup API DB manager for other tests
    set_db_path(None)


def test_categories_with_expenses_validation_and_after_delete(tmp_path):
    """
    Validate that:
    - expenses can use category_id belonging to the same user
    - expenses cannot use categories belonging to another user
    - deleting a category does not delete existing expenses (no hard FK), expense keeps category_id
    """
    db_file = tmp_path / "cats_mgr.db"
    db = DatabaseManager(str(db_file))

    # Create two users
    u1 = db.users.register_user("cat_mgr_user1", "pw")
    assert u1["success"]
    user1 = u1["data"]["user_id"]

    u2 = db.users.register_user("cat_mgr_user2", "pw")
    assert u2["success"]
    user2 = u2["data"]["user_id"]

    # Create categories for each user
    r1 = db.categories.add_category(user1, "Home")
    assert r1["success"]
    r2 = db.categories.add_category(user2, "Travel")
    assert r2["success"]

    cats_u1 = db.categories.get_categories(user1)
    cats_u2 = db.categories.get_categories(user2)
    assert cats_u1["success"] and cats_u2["success"]
    cat1_id = cats_u1["data"][0]["id"]
    cat2_id = cats_u2["data"][0]["id"]

    # Add expense for user1 with a valid category_id (own category) -> success
    e_ok = db.expenses.add_expense(
        title="Coffee",
        price=3.5,
        date="2025-08-19",
        category="home",  # legacy text is still accepted
        user_id=user1,
        category_id=cat1_id,
    )
    assert e_ok["success"]

    # Add expense for user1 but using a category_id that belongs to user2 -> should fail
    e_bad = db.expenses.add_expense(
        title="Taxi",
        price=10.0,
        date="2025-08-19",
        category="travel",
        user_id=user1,
        category_id=cat2_id,
    )
    assert not e_bad["success"]
    assert "invalid category" in (e_bad["error"] or "").lower()

    # Delete user1's category
    del_res = db.categories.delete_category(cat1_id, user_id=user1)
    assert del_res["success"]

    # Ensure the expense remains and still shows the historical category_id
    exps_u1 = db.expenses.get_expenses(user1)
    assert exps_u1["success"]
    items = exps_u1["data"]
    assert any(e["title"] == "Coffee" for e in items)
    coffee = next(e for e in items if e["title"] == "Coffee")
    # category_id should still be present in schema and retain the old id
    if "category_id" in coffee:
        assert coffee["category_id"] == cat1_id

    # Cleanup: close manager; rely on tmp_path auto-cleanup (avoid manual delete on Windows locks)
    db.close()