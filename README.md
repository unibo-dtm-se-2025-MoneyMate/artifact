# MoneyMate - Data Layer

A modular, validated, and fully tested Python data layer for a simple personal finance app.  
It manages users, contacts, categories, expenses, and user-to-user transactions with SQLite, providing:
- Clear Python APIs that return standardized results
- Strong application-level validation
- Deterministic listings (stable ordering), pagination, and filters
- Auditing of auth events (best-effort)
- Structured logging across operations
- A thread-safe API facade with a process-wide `DatabaseManager` singleton

This README describes design, schema, API style, and usage.  
(Structure and content kept intentionally close to the previous version.)

---

## Features

- **SQLite schema + bootstrap**
  - Automatic schema initialization on first use
  - Foreign keys enabled (PRAGMA `foreign_keys=ON`)
  - Basic indexing on frequently queried fields
  - Simple `schema_version` baseline table
- **Managers (single responsibility)**
  - Users, Contacts, Categories, Expenses, Transactions
- **Unified API Facade**
  - All operations return a dict: `{"success", "error", "data"}`
  - Optional ordering, pagination, and filtering where supported
- **Validation & Normalization**
  - Fields trimmed, types/ranges checked, ownership enforced
- **Deterministic listings**
  - Stable default ordering (e.g. recent-first for dated entities, name ASC for named entities)
- **Search**
  - Case-insensitive expense search on title / category (legacy text)
- **Categories behavior**
  - Categories per user; optional `category_id` in expenses (legacy text category kept)
- **Transactions**
  - Enforces `from_user_id != to_user_id`
  - Balance calculations: legacy & net (plus breakdown helper)
- **Logging / Auditing (best-effort)**
  - Auth events (login/logout/failed login/password change/reset)
- **Thread-safe singleton**
  - Facade-level access with dynamic DB file switching
- **Idempotent destructive operations**
  - Deletes return counts; “no-op” situations logged

---

## Database Schema (Core Tables – subset)

| Table        | Key Fields (subset)                                                                                                                          |
|--------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| `users`      | `id`, `username` (unique), `password_hash`, `role` ("user"/"admin"), `created_at`                                                             |
| `contacts`   | `id`, `user_id` (FK), `name` (unique per user), `created_at`                                                                                  |
| `categories` | `id`, `user_id` (FK), `name` (unique per user), `description`, `color`, `icon`, `created_at`                                                  |
| `expenses`   | `id`, `user_id` (FK), `title`, `price` (> 0), `date` (YYYY-MM-DD), `category` (legacy text), `category_id` (optional)                         |
| `transactions` | `id`, `from_user_id` (FK), `to_user_id` (FK), `type` ("debit"/"credit"), `amount` (> 0), `date`, `description`, `contact_id` (nullable FK), `created_at`, CHECK(from_user_id <> to_user_id) |
| `access_logs` | `id`, `user_id` (nullable), `action` in {"login","logout","failed_login","password_change","password_reset"}, `ip_address`, `user_agent`, `created_at` |
| `notes` *(if present / future)* | `id`, `user_id` (FK), optional link to `expense_id` / `transaction_id` / `contact_id`, `content`, `created_at`             |
| `attachments` *(if present / future)* | `id`, `user_id` (FK), optional link to `expense_id` / `transaction_id` / `contact_id`, `file_path`, `mime_type`, `size` |

Notes:
- Ownership constraints (e.g. a category used by an expense must belong to the same user) enforced at application level.
- `category_id` optional to preserve legacy text categorization.
- Indices applied where needed (e.g. `user_id`, `date`).

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
    └── data_layer/
        ├── __init__.py
        ├── test_api.py
        ├── test_categories.py
        ├── test_contacts.py
        ├── test_database.py
        ├── test_expenses.py
        ├── test_logging.py
        ├── test_manager.py
        ├── test_transactions.py
        ├── test_usermanager.py
        └── test_validation.py
```

---

## Usage

### Initialize a `DatabaseManager`

```python
from MoneyMate.data_layer.manager import DatabaseManager

# Default DB path (e.g. "moneymate.db")
db = DatabaseManager()

# Custom file
db = DatabaseManager("custom.db")

# Context manager
with DatabaseManager("session.db") as db:
    print(db.list_tables())
```

### Thread-safe API Facade

```python
from MoneyMate.data_layer.api import (
    get_db, set_db_path, api_list_tables
)

set_db_path("api_demo.db")  # Switch underlying DB file (lazy init)
db = get_db()
print(api_list_tables())    # {"success": True, "error": None, "data": [...]}
```

---

## Users and Roles

Academic policy (course context): admin registration requires password `"12345"`. (Do not use this policy in production.)

```python
from MoneyMate.data_layer.usermanager import UserManager

um = UserManager("auth.db")
um.register_user("alice", "pw123")
um.register_user("root", "12345", role="admin")  # academic admin rule

login = um.login_user("alice", "pw123", ip_address="127.0.0.1", user_agent="cli/1.0")
uid = login["data"]["user_id"]

um.logout_user(user_id=uid)
um.change_password(user_id=uid, old_password="pw123", new_password="newpass")
um.reset_password(admin_user_id=2, target_user_id=uid, new_password="resetByAdmin")
um.get_user_role(user_id=uid)
um.set_user_role(admin_user_id=2, target_user_id=uid, new_role="admin")
```

All return the standard envelope: `{"success", "error", "data"}`.

---

## Contacts and Categories

```python
# Contacts
db.contacts.add_contact(name="Mario Rossi", user_id=1)
db.contacts.get_contacts(user_id=1, order="name_asc")
db.contacts.delete_contact(contact_id=10, user_id=1)  # {"deleted": 0 or 1}

# Categories
db.categories.add_category(user_id=1, name="Food", color="#ff0000", icon="🍎")
db.categories.get_categories(user_id=1, order="name_asc", limit=50, offset=0)
db.categories.delete_category(category_id=5, user_id=1)
```

---

## Expenses

Validation rules: title required; price > 0; date `YYYY-MM-DD`; legacy text `category` required; optional `category_id` must belong to the same user.

```python
db.expenses.add_expense(
    title="Dinner",
    price=25.50,
    date="2025-08-19",
    category="Food",     # legacy text
    user_id=1,
    category_id=12       # optional
)

db.expenses.get_expenses(
    user_id=1,
    order="date_desc",
    limit=10,
    offset=0,
    date_from="2025-08-01",
    date_to="2025-08-31"
)

db.expenses.search_expenses("Food", user_id=1)

db.expenses.update_expense(
    expense_id=3,
    user_id=1,
    title="Dinner with friends",
    price=27.00
)

db.expenses.delete_expense(expense_id=3, user_id=1)
db.expenses.clear_expenses(user_id=1)
```

---

## Transactions

Transactions connect two distinct users; optional `contact_id` must belong to the sender. Types: `"debit"`, `"credit"`.

```python
db.transactions.add_transaction(
    from_user_id=1,
    to_user_id=2,
    type_="credit",
    amount=50,
    date="2025-08-19",
    description="Loan",
    contact_id=7
)

db.transactions.add_transaction(
    from_user_id=1,
    to_user_id=2,
    type_="debit",
    amount=20,
    date="2025-08-20",
    description="Repayment"
)

# Listings (as sender / as receiver)
db.transactions.get_transactions(user_id=1, as_sender=True)
db.transactions.get_transactions(user_id=1, as_sender=False)

# Admin view (if user has role 'admin')
db.transactions.get_transactions(user_id=2, is_admin=True)

# Partial update (sender only)
db.transactions.update_transaction(
    transaction_id=10,
    user_id=1,
    amount=45,
    description="Updated note"
)

# Delete (sender only, idempotent)
db.transactions.delete_transaction(transaction_id=10, user_id=1)
```

### Balances

Two semantics:

- **Legacy**: `(credits_received + credits_sent) - (debits_sent + debits_received)`
- **Net**: `credits_received - debits_sent`

```python
db.transactions.get_user_balance(user_id=1)
db.transactions.get_user_net_balance(user_id=1)
db.transactions.get_user_balance_breakdown(user_id=1)
db.transactions.get_contact_balance(user_id=1, contact_id=7)
```

Example scenario (User 1 → User 2: credit 50; then debit 20):
- User 1 legacy = (0 + 50) - (20 + 0) = 30; net = 0 - 20 = -20
- User 2 legacy = (50 + 0) - (0 + 20) = 30; net = 50 - 0 = 50

---

## Unified API Facade (Function-Based)

All manager operations are made available through `api.py` with the same envelope pattern. Example:

```python
from MoneyMate.data_layer.api import (
    set_db_path, api_register_user, api_add_expense,
    api_get_expenses, api_add_transaction,
    api_get_user_balance, api_get_user_net_balance
)

set_db_path("api_demo.db")

u1 = api_register_user("alice", "pw")["data"]["user_id"]
u2 = api_register_user("bob",   "pw")["data"]["user_id"]

api_add_expense(title="Lunch", price=12, date="2025-08-19", category="Food", user_id=u1)
api_get_expenses(user_id=u1, limit=10, offset=0)

api_add_transaction(from_user_id=u1, to_user_id=u2, type_="credit", amount=50, date="2025-08-19", description="Loan")
api_add_transaction(from_user_id=u1, to_user_id=u2, type_="debit", amount=20, date="2025-08-20", description="Repayment")

api_get_user_balance(u1)
api_get_user_net_balance(u1)
```

---

## Validation & Error Handling (Summary)

- **Expenses**: title (trimmed, required), price > 0, date format, legacy category required.
- **Contacts**: name required, unique per user.
- **Transactions**: allowed types, amount > 0, valid date, users exist, `from_user_id != to_user_id`, optional contact ownership enforced.
- **Categories**: name required, unique per user.
- **Users**: unique username; academic admin registration rule (do not use in production).
- **Deletes**: idempotent, return `{"deleted": 0}` if nothing removed.
- **Envelope** consistent across all methods.

---

## Logging

- Operations log at INFO; failures/warnings (e.g. no-op delete) logged explicitly.
- To disable automatic basic logging setup:  
  Set environment variable (example):  
  `export MONEYMATE_CONFIGURE_LOGGING=false`  
  (If such environment handling is present in the codebase.)

---

## Security & Privacy Notes

- Admin registration shortcut (`"12345"`) exists only for academic/testing scenarios.
- Access logs may include IP and user agent where provided; treat accordingly.
- Passwords should be stored hashed (refer to implementation in `usermanager.py`).

---

## Automated Testing

Tests validate:
- API facade consistency
- CRUD operations for each manager
- Validation and error paths
- Logging side-effects (where applicable)
- Balance calculations

Run:

```bash
pytest test/data_layer/
```

---

## Software Engineering Principles Applied

- **Modularity**: one manager per entity
- **Validation boundary**: application layer before persistence
- **Determinism**: stable ordering & predictable pagination
- **Observability**: logging + structured return values
- **Resource management**: context-managed database usage
- **Consistency**: uniform envelope for all operations

---

## Authors & Maintenance

Data Layer & Architecture: Giovanardi  
Repository: https://github.com/unibo-dtm-se-2025-MoneyMate/artifact

For questions:
- Consult source & docstrings
- Open a GitHub issue
- Run tests to validate environment

---