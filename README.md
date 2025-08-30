# MoneyMate - Data Layer

A modular, validated, and fully tested Python data layer for a simple personal finance app. It manages users, contacts, categories, expenses, and user-to-user transactions with SQLite, providing:
- Clear Python APIs that return standardized results
- Strong application-level validation
- Deterministic listings (stable ordering), pagination, and filters
- Auditing of auth events (best-effort)
- Structured logging across all operations
- A thread-safe API facade with a process-wide DatabaseManager singleton

This README documents the overall design, features, schema, APIs, and testing approach.

---

## Features

- SQLite schema and migrations
  - Automatic schema initialization on first use
  - Foreign keys enabled; indices for common queries
  - Constraints on new DBs (amount/price > 0, sender != receiver)
  - Simple schema_version table to represent a versioned baseline
  - sqlite3.Row row_factory for dict-like access
- Entity managers (single responsibility)
  - Users, Contacts, Categories, Expenses, Transactions
- Unified API Facade
  - All operations return a dict: {"success", "error", "data"}
  - Optional ordering, pagination, and filters are forwarded where supported
- Validation and normalization
  - Application-level validation for fields, types, ranges, and cross-entity ownership
  - Trim/normalize inputs where applicable (e.g., contact/category names, expense updates)
- Deterministic listings
  - Stable default ORDER BY: date DESC for expenses/transactions; name ASC for contacts/categories
- Search
  - Case-insensitive search for expenses by title/category (legacy text)
- Categories behavior
  - Per-user categories; expenses may store an optional category_id
  - No hard FK: deleting a category does not nullify the expense’s category_id (by design)
- Logging and auditing
  - INFO/WARN/ERROR logs across operations
  - Best-effort access_logs for login/logout/failed_login/password_change/password_reset
- Thread-safe API singleton
  - Safe global access to the DatabaseManager; support for runtime DB path switching

---

## Database Schema

Core tables (subset of columns):

| Table         | Key Fields (subset)                                                                                       |
|---------------|------------------------------------------------------------------------------------------------------------|
| users         | id (PK), username (unique), password_hash, role ("user"/"admin"), created_at                              |
| contacts      | id (PK), user_id (FK), name (unique per user), created_at                                                 |
| categories    | id (PK), user_id (FK), name (unique per user), description, color, icon, created_at                       |
| expenses      | id (PK), user_id (FK), title, price (> 0), date (YYYY-MM-DD), category (legacy text), category_id (opt)   |
| transactions  | id (PK), from_user_id (FK), to_user_id (FK), type ("debit"/"credit"), amount (> 0), date, description, contact_id (FK, nullable), created_at, CHECK(from_user_id <> to_user_id) |
| access_logs   | id (PK), user_id (nullable), action in {"login","logout","failed_login","password_change","password_reset"}, ip_address, user_agent, created_at |
| notes         | id (PK), user_id (FK), expense_id/transaction_id/contact_id (one required), content, created_at           |
| attachments   | id (PK), user_id (FK), expense_id/transaction_id/contact_id (one required), file_path, mime_type, size    |

Notes:
- PRAGMA foreign_keys=ON per connection.
- Indices on frequently filtered fields (e.g., user_id, date, composites).
- expenses.category_id is optional without a hard FK (historical preservation); ownership validation is enforced in code.

---

## Project Structure

```
<root directory>
├── MoneyMate/
│   ├── __init__.py
│   ├── __main__.py
│   └── data_layer/
│       ├── __init__.py
│       ├── api.py
│       ├── categories.py
│       ├── contacts.py
│       ├── database.py
│       ├── expenses.py
│       ├── logging_config.py
│       ├── manager.py
│       ├── transactions.py
│       ├── usermanager.py
│       └── validation.py
└── test/
│   └── data_layer/
│       ├── __init__.py
│       ├── test_api.py
│       ├── test_categories.py
│       ├── test_contacts.py
│       ├── test_database.py
│       ├── test_expenses.py
│       ├── test_logging.py
│       ├── test_manager.py
│       ├── test_transactions.py
│       ├── test_usermanager.py
│       └── test_validation.py
├── .github/
│   └── workflows/
│       ├── check.yml
│       └── deploy.yml
├── MANIFEST.in
├── LICENSE
├── pyproject.toml
├── README.md
├── renovate.json
├── requirements-dev.txt
├── requirements.txt
├── setup.py
└── Dockerfile
```

---

## Usage

### Initialize a DatabaseManager

```python
from MoneyMate.data_layer.manager import DatabaseManager

# Default DB path: "moneymate.db"
db = DatabaseManager()

# Custom DB file
db = DatabaseManager("custom.db")

# Context manager support
with DatabaseManager("session.db") as db:
    tables = db.list_tables()
    print(tables)
```

### Thread-safe API Facade (Singleton)

```python
from MoneyMate.data_layer.api import get_db, set_db_path, api_list_tables

# Switch DB file for API calls (also supports cleanup with None)
set_db_path("api_demo.db")

# Thread-safe singleton manager (created lazily)
db = get_db()

print(api_list_tables())  # -> {"success": True, "error": None, "data": [...]}
```

---

## Users and Roles

Academic policy (for coursework): admin registration requires password "12345". Never use this policy in production.

```python
from MoneyMate.data_layer.usermanager import UserManager

um = UserManager("auth.db")

# Register users (role defaults to "user")
um.register_user("alice", "s3cret")
um.register_user("root", "12345", role="admin")  # academic admin code

# Login / Logout (audited best-effort if access_logs exists)
login = um.login_user("alice", "s3cret", ip_address="127.0.0.1", user_agent="cli/1.0")
uid = login["data"]["user_id"]
um.logout_user(user_id=uid)

# Change / Reset password
um.change_password(user_id=uid, old_password="s3cret", new_password="n3wpass")
um.reset_password(admin_user_id=2, target_user_id=uid, new_password="resetByAdmin")

# Role operations
um.get_user_role(user_id=uid)
um.set_user_role(admin_user_id=2, target_user_id=uid, new_role="admin")
```

All methods consistently return {"success", "error", "data"} and log meaningful events.

---

## Contacts and Categories

Contacts are owned by a single user. Categories are per-user and can be referenced by expenses via category_id (ownership validated).

```python
# Contacts (manager layer)
db.contacts.add_contact(name="Mario Rossi", user_id=1)
db.contacts.get_contacts(user_id=1, order="name_asc")
db.contacts.delete_contact(contact_id=10, user_id=1)  # {"deleted": 0 or 1}; logs "noop" if nothing deleted

# Categories (manager layer)
db.categories.add_category(user_id=1, name="Food", color="#ff0000", icon="🍎")
db.categories.get_categories(user_id=1, order="name_asc", limit=50, offset=0)
db.categories.delete_category(category_id=5, user_id=1)  # idempotent delete
```

---

## Expenses

Validation: title required; price > 0; date "YYYY-MM-DD"; category (legacy text) required. Optionally link category_id if it belongs to the same user.

```python
# Add expense (manager layer)
db.expenses.add_expense(
    title="Dinner",
    price=25.50,
    date="2025-08-19",
    category="Food",   # legacy text
    user_id=1,
    category_id=12     # optional; must belong to user_id=1 if provided
)

# List and search (deterministic ordering; pagination and date filters)
db.expenses.get_expenses(user_id=1, order="date_desc", limit=10, offset=0, date_from="2025-08-01", date_to="2025-08-31")
db.expenses.search_expenses("Food", user_id=1)

# Partial update (normalizes and validates fields)
db.expenses.update_expense(expense_id=3, user_id=1, title="Dinner with friends", price=27.00)

# Delete (idempotent)
db.expenses.delete_expense(expense_id=3, user_id=1)  # {"deleted": 1} or {"deleted": 0}
db.expenses.clear_expenses(user_id=1)
```

---

## Transactions

Transactions are between two different users (from_user_id and to_user_id). The sender may link a contact they own (contact_id). Types are "debit" and "credit".

```python
# Add (validates: users exist, sender != receiver, amount/date/type valid, optional contact belongs to sender)
db.transactions.add_transaction(
    from_user_id=1, to_user_id=2, type_="credit", amount=50, date="2025-08-19",
    description="Loan", contact_id=7
)
db.transactions.add_transaction(
    from_user_id=1, to_user_id=2, type_="debit", amount=20, date="2025-08-20",
    description="Repayment"
)

# List
db.transactions.get_transactions(user_id=1, as_sender=True)    # sent by user 1
db.transactions.get_transactions(user_id=1, as_sender=False)   # received by user 1

# Admin visibility
db.transactions.get_transactions(user_id=2, is_admin=True)     # only if user_id=2 has role 'admin'

# Partial update (sender-only)
db.transactions.update_transaction(transaction_id=10, user_id=1, amount=45, description="Updated note")

# Delete (sender-only, idempotent)
db.transactions.delete_transaction(transaction_id=10, user_id=1)  # {"deleted": 1} or {"deleted": 0}
```

### Balances

Two semantics are provided:

- Legacy (symmetric): credit − debit across all transactions where the user is sender or receiver.
- Net (recommended): credits_received − debits_sent.

```python
# Legacy
db.transactions.get_user_balance(user_id=1)  # {"success": True, "data": 30.0, ...} in example below

# Net
db.transactions.get_user_net_balance(user_id=1)  # {"success": True, "data": -20.0, ...}

# Breakdown
db.transactions.get_user_balance_breakdown(user_id=1)
# -> {"credits_received": 0, "debits_sent": 20, "credits_sent": 50, "debits_received": 0, "net": -20, "legacy": 30}

# Contact balance (sender perspective)
db.transactions.get_contact_balance(user_id=1, contact_id=7)
# -> {"credits_sent": X, "debits_sent": Y, "net": X - Y}
```

Example scenario (U1 -> U2: credit 50; U1 -> U2: debit 20):
- U1 legacy = (0 + 50) - (20 + 0) = 30; net = 0 - 20 = -20
- U2 legacy = (50 + 0) - (0 + 20) = 30; net = 50 - 0 = 50

---

## Unified API Facade

All operations are also available via the high-level API in MoneyMate.data_layer.api. The API is thread-safe, logs every call, and forwards ordering/pagination/filtering where supported.

```python
from MoneyMate.data_layer.api import (
    set_db_path, get_db,
    api_register_user, api_login_user, api_logout_user,
    api_get_user_role, api_set_user_role, api_change_password, api_reset_password,
    api_add_contact, api_get_contacts, api_delete_contact,
    api_add_category, api_get_categories, api_delete_category,
    api_add_expense, api_update_expense, api_get_expenses, api_search_expenses, api_delete_expense, api_clear_expenses,
    api_add_transaction, api_update_transaction, api_get_transactions, api_delete_transaction,
    api_get_user_balance, api_get_user_net_balance, api_get_user_balance_breakdown, api_get_contact_balance,
    api_list_tables, api_health,
)

set_db_path("api_demo.db")

# Users
u1 = api_register_user("alice", "pw")["data"]["user_id"]
u2 = api_register_user("bob", "pw")["data"]["user_id"]

# Contacts & Categories
api_add_contact("Carlo", u1)
api_add_category(user_id=u1, name="Food", color="#FF0000", icon="🍎")

# Expenses
api_add_expense(title="Lunch", price=12, date="2025-08-19", category="Food", user_id=u1)
api_get_expenses(user_id=u1, limit=10, offset=0)
api_search_expenses(query="Lunch", user_id=u1)

# Transactions and balances
api_add_transaction(from_user_id=u1, to_user_id=u2, type_="credit", amount=50, date="2025-08-19", description="Loan")
api_add_transaction(from_user_id=u1, to_user_id=u2, type_="debit", amount=20, date="2025-08-20", description="Repayment")

api_get_transactions(user_id=u1, as_sender=True)
api_get_user_balance(u1)
api_get_user_net_balance(u1)
api_get_user_balance_breakdown(u1)
```

---

## Validation & Error Handling

- Expenses: title (trimmed, required), price numeric > 0, date "YYYY-MM-DD", category (legacy text) required.
- Contacts: name required (trimmed), unique per user.
- Transactions: type ∈ {"debit","credit"} (case-insensitive), amount > 0, date "YYYY-MM-DD"; users must exist; sender != receiver; optional contact_id must belong to sender.
- Categories: name required (trimmed), unique per user; optional attributes (description, color, icon).
- Users: unique username; secure password hashing; academic admin registration policy ("12345"); auditing for auth events.
- Idempotent delete: return success=True with data={"deleted": 0 or 1}; warnings logged on no-op.
- All API/manager calls return {"success", "error", "data"} with explicit error messages and consistent logging.

---

## Logging

- Module-level structured logs for diagnostics and test observability.
- Root logger configuration can be disabled via environment variable:
  - export MONEYMATE_CONFIGURE_LOGGING=false  # to disable
  - export MONEYMATE_LOG_LEVEL=INFO          # to change level (default INFO)

---

## Security & Privacy Notes

- Admin registration code "12345" exists for academic/testing evaluation only; not for production use.
- Access logs may record IP address and user agent; handle these as potentially sensitive.

---

## Automated Testing

Unit tests verify modules and integrated APIs in test/data_layer/.

### Running Tests

```bash
pytest test/data_layer/
```

### Test Coverage (high-level)

- API integration: expenses, contacts, transactions, categories, user flows; DB switching; response format and errors
- Expenses: add/search/delete/clear; validation; deterministic ordering; pagination and date filters
- Contacts: add/list/delete; name validation; ordering and uniqueness handling
- Categories: add/list/delete; pagination and ownership; preserved category_id behavior
- Transactions: add/list/delete; validation (users/contact/type/amount/date); admin visibility; balances (legacy/net/breakdown); filters
- Users & roles: registration/login/logout; admin registration policy; change/reset password; role get/set; auditing (test_usermanager.py)
- Logging: success and failure paths; idempotent delete "noop" warnings
- Database/Manager: initialization, table listing, foreign keys, context manager semantics
- Validation: direct validator functions for correct/incorrect inputs

---

## Software Engineering Principles

- Modularity and single responsibility per manager
- Dependency injection for cross-entity validation (e.g., TransactionsManager uses ContactsManager)
- Configurability (DB path, logging via environment)
- Determinism and observability (stable ordering, structured logs, auditing)
- Resource management (short-lived connections; context managers)
- Clear API contracts and comprehensive test coverage

---

## Authors & Maintenance

Data Layer & Architecture: Giovanardi  
Repository: https://github.com/unibo-dtm-se-2025-MoneyMate/artifact

For questions:
- Refer to docstrings and source
- Open an issue on GitHub
- Run tests to validate the setup