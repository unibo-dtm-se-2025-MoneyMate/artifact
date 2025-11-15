"""
System test (end-to-end) for MoneyMate.

Purpose:
- Exercise the full stack via the public data layer API (no GUI).
- Validate core business flows across modules: users, categories, expenses, contacts, transactions.
- Assert balances semantics, admin visibility, and access_logs auditing.
- Ensure API envelopes and data shapes are consistent.

"""

import pytest
from MoneyMate.data_layer.api import (
    set_db_path, api_health, api_list_tables,
    api_register_user, api_login_user, api_logout_user,
    api_add_category, api_get_categories,
    api_add_expense, api_get_expenses, api_search_expenses, api_update_expense,
    api_add_contact, api_get_contacts,
    api_add_transaction, api_get_transactions,
    api_get_user_net_balance, api_get_user_balance_breakdown,
)
from MoneyMate.data_layer.database import get_connection


def test_system_end_to_end(tmp_path):
    # ---------- Arrange: fresh database bound to API facade ----------
    db_file = tmp_path / "system_e2e.db"
    set_db_path(str(db_file))

    try:
        # ---------- Health and schema ----------
        h = api_health()
        assert isinstance(h, dict) and h["success"], "api_health must succeed"
        assert isinstance(h["data"], int), "api_health must return schema version (int)"

        tables = api_list_tables()
        assert tables["success"]
        tset = set(tables["data"])
        assert {"users", "contacts", "expenses", "transactions", "categories"}.issubset(tset), "Core tables missing"

        # ---------- Users: admin + two normal users ----------
        admin = api_register_user("e2e_admin", "12345", role="admin")
        assert admin["success"], f"Admin registration failed: {admin}"
        admin_id = admin["data"]["user_id"]

        alice = api_register_user("e2e_alice", "pw")
        if not alice["success"]:
            alice = api_login_user("e2e_alice", "pw")
        assert alice["success"], f"Alice not available: {alice}"
        alice_id = alice["data"]["user_id"]

        bob = api_register_user("e2e_bob", "pw")
        if not bob["success"]:
            bob = api_login_user("e2e_bob", "pw")
        assert bob["success"], f"Bob not available: {bob}"
        bob_id = bob["data"]["user_id"]

        # Trigger one failed login to validate access_logs later (if present)
        bad_login = api_login_user("e2e_alice", "wrong")
        assert not bad_login["success"]

        # Successful logins (also for access_logs)
        assert api_login_user("e2e_alice", "pw")["success"]
        assert api_login_user("e2e_bob", "pw")["success"]

        # ---------- Categories for Alice ----------
        assert api_add_category(alice_id, "Food", description="Meals")["success"]
        assert api_add_category(alice_id, "Transport", description="Commute")["success"]

        cats = api_get_categories(alice_id)
        assert cats["success"] and len(cats["data"]) >= 2
        food_id = next(c["id"] for c in cats["data"] if c["name"] == "Food")

        # ---------- Expenses for Alice (with category_id) ----------
        assert api_add_expense("Lunch", 12.50, "2025-08-19", "Food", alice_id, category_id=food_id)["success"]
        assert api_add_expense("Bus Ticket", 2.25, "2025-08-19", "Transport", alice_id)["success"]

        exps = api_get_expenses(alice_id)
        assert exps["success"] and len(exps["data"]) >= 2
        lunch = next(e for e in exps["data"] if e["title"] == "Lunch")
        assert "category_id" in lunch and lunch["category_id"] == food_id

        # Update expense (partial) and verify
        eid = lunch["id"]
        up = api_update_expense(eid, alice_id, price=13.00)
        assert up["success"] and up["data"]["updated"] in (0, 1)
        exps2 = api_get_expenses(alice_id)
        lunch2 = next(e for e in exps2["data"] if e["id"] == eid)
        assert float(lunch2["price"]) == 13.00

        # Search
        s = api_search_expenses("Lunch", alice_id)
        assert s["success"] and any(e["title"] == "Lunch" for e in s["data"])

        # ---------- Contacts for Alice ----------
        assert api_add_contact("Bob", alice_id)["success"]
        contacts = api_get_contacts(alice_id)
        assert contacts["success"] and contacts["data"]
        contact_id = next(c["id"] for c in contacts["data"] if c["name"] == "Bob")

        # ---------- Transactions (Alice -> Bob) ----------
        # Use explicit to_user_id=bob_id and bind contact_id for traceability
        assert api_add_transaction(
            from_user_id=alice_id, to_user_id=bob_id,
            type_="credit", amount=50, date="2025-08-19", description="Loan", contact_id=contact_id
        )["success"]

        assert api_add_transaction(
            from_user_id=alice_id, to_user_id=bob_id,
            type_="debit", amount=20, date="2025-08-19", description="Repayment", contact_id=contact_id
        )["success"]

        # Listings: sender vs receiver vs admin
        tx_alice_sent = api_get_transactions(alice_id, as_sender=True)
        assert tx_alice_sent["success"] and len(tx_alice_sent["data"]) >= 2
        assert all(t["from_user_id"] == alice_id for t in tx_alice_sent["data"])

        tx_bob_recv = api_get_transactions(bob_id, as_sender=False)
        assert tx_bob_recv["success"] and len(tx_bob_recv["data"]) >= 2
        assert all(t["to_user_id"] == bob_id for t in tx_bob_recv["data"])

        tx_admin_all = api_get_transactions(admin_id, is_admin=True)
        assert tx_admin_all["success"] and len(tx_admin_all["data"]) >= 2
        # Admin should see transactions with Alice as sender and Bob as recipient
        senders = {t["from_user_id"] for t in tx_admin_all["data"]}
        recipients = {t["to_user_id"] for t in tx_admin_all["data"]}
        assert alice_id in senders
        assert bob_id in recipients

        # ---------- Balances semantics ----------
        # Scenario:
        #  Alice -> Bob: credit 50, debit 20
        # Expected:
        #  Alice: net = 0 - 20 = -20
        #  Bob:   net = 50 - 0 = 50
        net_alice = api_get_user_net_balance(alice_id)
        net_bob = api_get_user_net_balance(bob_id)
        assert net_alice["success"] and net_bob["success"]
        assert net_alice["data"] == -20
        assert net_bob["data"] == 50

        br_alice = api_get_user_balance_breakdown(alice_id)
        br_bob = api_get_user_balance_breakdown(bob_id)
        assert br_alice["success"] and br_bob["success"]
        A = br_alice["data"]; B = br_bob["data"]
        assert A["credits_received"] == 0 and A["debits_sent"] == 20 and A["credits_sent"] == 50 and A["debits_received"] == 0
        assert A["net"] == -20 and A["legacy"] == 30
        assert B["credits_received"] == 50 and B["debits_sent"] == 0 and B["credits_sent"] == 0 and B["debits_received"] == 20
        assert B["net"] == 50 and B["legacy"] == 30

        # ---------- Auditing / access logs (best effort) ----------
        # access_logs presence depends on schema; check counts if table exists
        with get_connection(str(db_file)) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_schema WHERE type='table' AND name='access_logs';")
            if cur.fetchone():
                cur.execute("SELECT COUNT(*) FROM access_logs WHERE action='failed_login'")
                failed = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM access_logs WHERE action='login'")
                logins = cur.fetchone()[0]
                assert failed >= 1
                assert logins >= 2

        # ---------- Logout paths (no-op but should succeed) ----------
        assert api_logout_user(alice_id)["success"]
        assert api_logout_user(bob_id)["success"]

    finally:
        # ---------- Teardown: release API DB singleton and GC ----------
        set_db_path(None)