# MoneyMate - Data Layer

## Overview

MoneyMate Data Layer manages persistence and business logic for users, categories, expenses, contacts, and transactions using SQLite.
It provides a modular, validated, and fully tested Python API with deterministic listings, pagination, and auditing, following software engineering best practices.

---

## Features

- Robust SQLite schema: auto-created and versioned; safe connection handling (context managers).
- User accounts and roles: register, login/logout, change/reset password; roles: user/admin with admin-only actions.
- Admin registration code: "12345" (academic policy, NOT for production).
- Best-effort auditing: records login, logout, failed_login, password_change, password_reset into access_logs.
- Entity managers: dedicated Python classes for users, expenses, contacts, transactions, and categories.
- Unified API: every operation returns a standardized dictionary: {"success", "error", "data"}.
- Strong validation: inputs validated before DB operations; clear error messages.
- Deterministic listings: stable ordering for reliable UX and tests.
- Pagination and filters: limit, offset, date_from, date_to on expenses and transactions; pagination on categories.
- Search: case-insensitive expense search by title/category.
- Category behavior: per-user categories; expenses keep category_id after category deletion (no hard FK).
- Structured logging: consistent logs with module, level, and message; opt-in root logging via MONEYMATE_CONFIGURE_LOGGING=1.
- Configurable DB path: change at runtime for tests/environments.
- Row access convenience: sqlite3.Row row_factory for dict-like access.
- Comprehensive unit tests: modules and APIs covered.

---

## Database Schema

| Table             | Fields                                                                                                                         |
|-------------------|--------------------------------------------------------------------------------------------------------------------------------|
| users             | id (PK), username (unique), password_hash, role ("user"|"admin")                                                               |
| access_logs       | id (PK), user_id (nullable FK-like), action ("login"|"logout"|"failed_login"|"password_change"|"password_reset"), ts, ip, ua  |
| categories        | id (PK), name (str), user_id (owner)                                                                                           |
| expenses          | id (PK), title (str), price (float), date (YYYY-MM-DD), category_id (nullable, kept after category delete)                     |
| contacts          | id (PK), name (str)                                                                                                            |
| transactions      | id (PK), contact_id (FK), type (debit/credit), amount (float), date (YYYY-MM-DD), description (str)                            |

Notes:
- Tables and indices are created automatically during initialization.
- access_logs writes are best-effort and skipped safely if the table is not yet present.

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
│
├── test/
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
│       └── test_validation.py
│
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

### Database Initialization

The database is created automatically and uses sqlite3.Row for convenient access:

```python
from MoneyMate.data_layer.manager import DatabaseManager

# Default DB path: "moneymate.db"
db = DatabaseManager()

# Custom file (testing/production)
db = DatabaseManager("custom.db")

# Context manager support
with DatabaseManager("session.db") as db:
    tables = db.list_tables()
```

---

### User Accounts and Roles

```python
from MoneyMate.data_layer.usermanager import UserManager

um = UserManager("auth.db")

# Register (admin registration requires password "12345" for academic purposes)
um.register_user(username="alice", password="s3cret")           # role defaults to "user"
um.register_user(username="root",  password="12345", role="admin")

# Login / Logout (audited best-effort)
login = um.login_user("alice", "s3cret", ip_address="127.0.0.1", user_agent="cli/1.0")
# -> {"success": True, "error": None, "data": {"user_id": 1, "role": "user"}}

um.logout_user(user_id=login["data"]["user_id"])

# Change / Reset password
um.change_password(user_id=1, old_password="s3cret", new_password="n3wpass")
um.reset_password(admin_user_id=2, target_user_id=1, new_password="resetByAdmin")

# Get / Set role (admin-only for setting)
um.get_user_role(user_id=1)
um.set_user_role(admin_user_id=2, target_user_id=1, new_role="admin")
```

All methods return {"success", "error", "data"} and log meaningful warnings/errors; auditing writes to access_logs when available.

> Important (academic policy): Admin registration currently requires the password "12345".
> This is intended for coursework/testing only. Do not use this policy in production.

---

### Entity Managers

CRUD and utilities for expenses, contacts, transactions, and categories.

```python
# Expenses
db.expenses.add_expense("Dinner", 25.5, "2025-08-19", category_id=1)
db.expenses.get_expenses(limit=20, offset=0, date_from="2025-08-01", date_to="2025-08-31")
db.expenses.search_expenses("Food")  # case-insensitive by title/category
db.expenses.delete_expense(1)
db.expenses.clear_expenses()

# Contacts
db.contacts.add_contact("Mario Rossi")
db.contacts.get_contacts()  # name ASC
db.contacts.delete_contact(1)

# Categories (per-user ownership validated on insert)
db.categories.add_category("Food", user_id=1)
db.categories.get_categories(limit=50, offset=0)  # name ASC
db.categories.delete_category(1)  # expenses keep category_id (no hard FK)

# Transactions
db.transactions.add_transaction(contact_id=1, type_="credit", amount=50, date="2025-08-19", description="Loan")
db.transactions.get_transactions(limit=20, offset=0, date_from="2025-08-01", date_to="2025-08-31")
db.transactions.delete_transaction(1)
db.transactions.get_contact_balance(contact_id=1)
```

Deterministic ordering:
- Expenses/Transactions: date DESC, id DESC
- Contacts/Categories: name ASC

---

### Unified API

High-level API functions forward ordering/pagination/filter params and keep a consistent response format.

```python
from MoneyMate.data_layer.api import (
    api_add_expense, api_get_expenses, api_search_expenses,
    api_delete_expense, api_clear_expenses,
    api_add_contact, api_get_contacts, api_delete_contact,
    api_add_transaction, api_get_transactions, api_delete_transaction,
    api_get_contact_balance, set_db_path, api_list_tables,
    api_add_category, api_get_categories, api_delete_category
)

set_db_path("test_api.db")  # Switch DB for API calls

res = api_add_expense("Lunch", 12, "2025-08-19", category_id=1)
print(res)  # {'success': True, 'error': None, 'data': None}

# Pagination and filters example
api_get_expenses(limit=10, offset=0, date_from="2025-08-01", date_to="2025-08-31")
api_get_transactions(limit=10, offset=0)
api_get_categories(limit=50, offset=0)
```

---

### Validation & Error Handling

- Expenses: title, price, date required; price > 0; date format "YYYY-MM-DD".
- Contacts: name required.
- Transactions: type in {"debit","credit"}, amount > 0, date "YYYY-MM-DD", contact must exist.
- Categories: name required; ownership validated on insert.
- Users: unique username; secure password hashing; admin registration policy ("12345" for academic use).
- Clear delete semantics: category deletion returns success with deleted=0 when noop (per tests).
- All API calls return {"success", "error", "data"}; errors are explicit and logged.

---

### Logging

- Structured logging across modules.
- Root logging opt-in via environment variable:
  - export MONEYMATE_CONFIGURE_LOGGING=1
- Operation outcomes and validation errors are logged with appropriate levels.

---

### Security & Privacy

- Admin registration code: "12345" is an academic/testing policy to simplify evaluation. Do NOT use in production.
  - For production, replace this policy with a secure onboarding flow or a configurable secret (e.g., set an environment variable like MONEYMATE_ADMIN_REG_CODE and update UserManager.register_user accordingly).
  - Encourage immediate password change for any admin account created with this code.
- Auditing may record IP address and user agent. Treat access_logs as potentially sensitive (PII). Enable and retain according to applicable privacy regulations.

---

### Dynamic Database Path

Change the database file at runtime:

```python
db.set_db_path("newfile.db")
```

Or via API:

```python
from MoneyMate.data_layer.api import set_db_path
set_db_path("test_api.db")
```

---

### API Response Format

```python
{
    "success": True/False,
    "error": "Error message" or None,
    "data": object/list/value or None
}
```

---

## Automated Testing

All modules and APIs are covered by unit tests in test/data_layer/.

### Running Tests

```shell
pytest test/data_layer/
```

### Test Coverage (high-level)

- API integration: expenses, contacts, transactions, categories; DB switching; response format and errors.
- Expenses: add/search/delete/clear; date format; deterministic ordering; pagination/filters.
- Contacts: add/list/delete; name validation; deterministic ordering.
- Categories: add/list/delete; ownership validation; preserved category_id behavior.
- Transactions: add/list/delete; validations; balances; pagination/filters.
- Users & roles: registration/login/logout; change/reset password; role get/set; auditing.
- Logging: correct levels/messages for success, validation errors, and deletions.
- Database/Manager: connection, table creation, list_tables, context manager behavior.
- Validation utilities: success and error scenarios.

Testing best practices:
- Each test uses its own DB for isolation.
- Both success and failure paths are covered.
- Response format is always asserted.

---

## Software Engineering Principles

- Single Responsibility & Modularity: managers per entity; minimal coupling.
- Dependency Injection: managers accept dependencies explicitly where needed.
- Configurability: parameterized DB path; environment-controlled logging.
- Error Handling: explicit, consistent, and user-facing via standardized responses.
- Determinism & Observability: stable ordering; extensive logging and auditing.
- Resource Management: safe DB connections via context managers.
- Documentation & Tests: rich docstrings; comprehensive examples and unit tests.

---

## Authors & Maintenance

Data Layer & Architecture: Giovanardi  
Repository: https://github.com/unibo-dtm-se-2025-MoneyMate/artifact

For questions or support:
- See docstrings and source.
- Open an issue on GitHub.
- Run tests to validate installation.