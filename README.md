# MoneyMate - Data Layer

## Overview

MoneyMate Data Layer manages persistence and business logic for expenses, contacts, and transactions using SQLite.  
It provides a modular, validated, and fully tested Python API for all operations, following software engineering best practices.

---

## Features

- **Robust SQLite schema:** Automatically created and versioned.
- **Entity Managers:** Dedicated Python classes for expenses, contacts, and transactions.
- **Unified API:** Every operation returns a standardized Python dictionary (`success`, `error`, `data`).
- **Strong validation:** All input is validated before any database operation.
- **Structured logging:** Every operation and error is tracked with timestamp, module, and severity.
- **Configurable DB path:** The database file can be changed at runtime, supporting testing and multiple environments.
- **Comprehensive unit tests:** All modules and APIs are covered.

---

## Database Schema

| Table        | Fields                                                                              |
|--------------|-------------------------------------------------------------------------------------|
| **expenses** | id (PK), title (str), price (float), date (YYYY-MM-DD), category (str)              |
| **contacts** | id (PK), name (str)                                                                 |
| **transactions** | id (PK), contact_id (FK), type (debit/credit), amount (float), date (YYYY-MM-DD), description (str) |

Tables and constraints are created automatically during initialization.

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
│       ├── contacts.py
│       ├── database.py
│       ├── expenses.py
│       ├── logging_config.py
│       ├── manager.py
│       ├── transactions.py
│       ├── validation.py
│
├── test/
│   └── data_layer/
│       ├── __init__.py
│       ├── test_api.py
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

The database is created automatically:

```python
from MoneyMate.data_layer.manager import DatabaseManager

db = DatabaseManager()            # Uses "moneymate.db" by default
db = DatabaseManager("custom.db") # Uses a custom file (for testing/production)
```

---

### Entity Managers

Each manager provides dedicated CRUD and utility operations:

```python
# Expenses
db.expenses.add_expense("Dinner", 25.5, "2025-08-19", "Food")
db.expenses.get_expenses()
db.expenses.search_expenses("Food")
db.expenses.delete_expense(1)
db.expenses.clear_expenses()

# Contacts
db.contacts.add_contact("Mario Rossi")
db.contacts.get_contacts()
db.contacts.delete_contact(1)

# Transactions
db.transactions.add_transaction(contact_id=1, type_="credit", amount=50, date="2025-08-19", description="Loan")
db.transactions.get_transactions(contact_id=1)
db.transactions.delete_transaction(1)
db.transactions.get_contact_balance(contact_id=1)
```

---

### Unified API

High-level API functions for integration with other modules:

```python
from MoneyMate.data_layer.api import (
    api_add_expense, api_get_expenses, api_search_expenses,
    api_delete_expense, api_clear_expenses,
    api_add_contact, api_get_contacts, api_delete_contact,
    api_add_transaction, api_get_transactions, api_delete_transaction,
    api_get_contact_balance, set_db_path, api_list_tables
)

set_db_path("test_api.db")  # Change DB for API operations

res = api_add_expense("Lunch", 12, "2025-08-19", "Food")
print(res)  # {'success': True, 'error': None, 'data': None}
```

---

### Validation & Error Handling

- **Expenses:** title, price, date, and category are required; price must be positive; date format "YYYY-MM-DD".
- **Contacts:** name required.
- **Transactions:** type must be debit or credit, amount positive, date "YYYY-MM-DD", contact must exist.
- Errors are returned in the `"error"` field of the API response.

---

### Logging

Structured logging enabled by default:

- Default level: `INFO`. For debugging, set `DEBUG` in `logging_config.py`.
- Every operation logs time, module, level, and message.

---

### Dynamic Database Path

Change the database file at runtime:

```python
db.set_db_path("newfile.db")  # Change persistence file for all operations
```
Or via API:

```python
from MoneyMate.data_layer.api import set_db_path
set_db_path("test_api.db")
```

---

### API Response Format

Every API call returns a Python dictionary:

```python
{
    "success": True/False,
    "error": "Error message" or None,
    "data": object/list/value or None
}
```

---

## Automated Testing

**All modules and APIs are covered by unit tests** in `test/data_layer/`.

### Running Tests

```shell
pytest test/data_layer/
```

### Test Coverage

- **API Integration (`test_api.py`):** Add, retrieve, search, and delete expenses and contacts. Add transactions and verify contact balances. Switch DB for isolation. Validate response format and error handling.
- **Expenses (`test_expenses.py`):** Add expense (valid/invalid data). Search by title/category. Delete individual, clear all. Check date format and API response.
- **Contacts (`test_contacts.py`):** Add, retrieve, and delete contacts. Handle empty name errors.
- **Transactions (`test_transactions.py`):** Add, retrieve, and delete transactions. Validate type and amount. Calculate contact balances. Handle non-existent contacts.
- **Logging (`test_logging.py`):**  
  Test correct logging for all operations (expenses, contacts, transactions, and API calls).  
  Checks that successful operations, validation errors, and deletions are logged with correct level and message.
- **Database (`test_database.py`):** Table creation and connection.
- **Manager (`test_manager.py`):** Orchestrator and table listing.
- **Validation (`test_validation.py`):** Validation function tests for correct and error cases.

**Testing Best Practices:**
- Each test creates and destroys its own database for isolation.
- Both success and failure scenarios are covered.
- Always check API response format.

**Example test:**

```python
def test_api_add_and_get_expense():
    res = api_add_expense("Test", 5, "2025-08-19", "Food")
    assert res["success"]
    res_get = api_get_expenses()
    assert any(e["title"] == "Test" for e in res_get["data"])
```

---

## Software Engineering Principles

- **Single Responsibility:** Each manager is responsible for a single entity.
- **Dependency Injection:** Transactions manager receives contacts manager for cross-validation.
- **Configurability:** The database path is always parameterized.
- **Error handling:** Errors are explicit and handled at all layers.
- **Testing:** All modules are covered by isolated, reproducible tests.
- **Modularity:** Easy to extend or refactor, no code duplication.
- **Resource Management:** Safe DB connections via context managers.
- **Documentation:** Rich docstrings, README with practical examples.

---

## Authors & Maintenance

**Data Layer & Architecture:** Giovanardi  
**Repository:** [unibo-dtm-se-2025-MoneyMate/artifact](https://github.com/unibo-dtm-se-2025-MoneyMate/artifact)

For questions or support:
- See docstrings and source documentation.
- Open an issue on GitHub.
- Run tests to validate installation.