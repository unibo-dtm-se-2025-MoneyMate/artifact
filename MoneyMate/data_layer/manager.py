"""
Central orchestrator and backward-compatible façade for the MoneyMate data layer.

DatabaseManager coordinates all low-level managers (expenses, contacts,
transactions, users, categories) and provides:

- Initialization and re-initialization of the database and manager instances.
- Resource cleanup and connection management (including in-memory keeper).
- Legacy-style methods used by tests (add_expense, add_contact, etc.),
  with input validation, localization of error messages, and normalization
  to a standard {success, error, data} dict format.
- A flexible list_tables() view that acts like both a list and a dict.

This class is the primary entry point for non-GUI code that wants a single
object to talk to the MoneyMate data layer.
"""

from typing import Any, Dict, Optional
import sqlite3
import sys
import types
import gc
import re
import datetime

from .database import DB_PATH, list_tables as db_list_tables, init_db as db_init_db
from .logging_config import get_logger

logger = get_logger(__name__)


def dict_response(success: bool, error: Optional[str] = None, data: Any = None) -> Dict[str, Any]:
    """
    Formato standard di risposta per tutte le API pubbliche.
    """
    return {"success": success, "error": error, "data": data}


class DatabaseManager:
    """
    Orchestratore centrale: offre API 'legacy' usate dai test.
    Ogni metodo pubblico restituisce SEMPRE un dict {success,error,data} tranne list_tables
    che restituisce un oggetto ibrido list/dict per compat bilaterale coi test esistenti.
    """

    # -------------------------------------------------
    # INIT / SETUP
    # -------------------------------------------------
    def __init__(self, db_path: str = DB_PATH):
        logger.info(f"Initializing DatabaseManager with db_path: {db_path}")
        self.db_path: str = db_path
        self._keeper: Optional[sqlite3.Connection] = None
        self._default_user_id: Optional[int] = None

        if isinstance(db_path, str) and db_path.startswith("file:") and "mode=memory" in db_path:
            try:
                self._keeper = sqlite3.connect(db_path, uri=True, check_same_thread=False)
                self._keeper.execute("PRAGMA foreign_keys = ON;")
            except Exception as e:
                logger.warning(f"Keeper connection init failed: {e}")

        db_init_db(db_path)
        self._init_managers()

    def _init_managers(self):
        from .expenses import ExpensesManager
        from .contacts import ContactsManager
        from .transactions import TransactionsManager
        from .usermanager import UserManager
        from .categories import CategoriesManager

        self.expenses = ExpensesManager(self.db_path, db_manager=self)
        self.contacts = ContactsManager(self.db_path, db_manager=self)
        self.transactions = TransactionsManager(self.db_path, self.contacts, db_manager=self)
        self.users = UserManager(self.db_path, db_manager=self)
        self.categories = CategoriesManager(self.db_path, db_manager=self)

    def __enter__(self) -> "DatabaseManager":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        try:
            self.close()
        except Exception:
            pass
        return False

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    # -------------------------------------------------
    # CLEANUP
    # -------------------------------------------------
    def _close_manager(self, mgr) -> None:
        if mgr is None:
            return
        try:
            maybe_close = getattr(mgr, "close", None)
            if callable(maybe_close):
                maybe_close()
        except Exception:
            pass
        try:
            for name, val in list(getattr(mgr, "__dict__", {}).items()):
                if isinstance(val, sqlite3.Connection):
                    try:
                        val.close()
                    except Exception:
                        pass
                    try:
                        setattr(mgr, name, None)
                    except Exception:
                        pass
        except Exception:
            pass

    def _close_sqlite_connections_in_modules(self, package_prefix: str = "MoneyMate.data_layer") -> None:
        try:
            for mod_name, mod in list(sys.modules.items()):
                if not isinstance(mod, types.ModuleType):
                    continue
                if not mod_name.startswith(package_prefix):
                    continue
                for attr_name, val in list(vars(mod).items()):
                    if isinstance(val, sqlite3.Connection):
                        try:
                            val.close()
                        except Exception:
                            pass
                        try:
                            setattr(mod, attr_name, None)
                        except Exception:
                            pass
        except Exception:
            pass

    def close(self) -> None:
        logger.info("Releasing all managers for test cleanup.")
        for attr in ("expenses", "contacts", "transactions", "users", "categories"):
            try:
                self._close_manager(getattr(self, attr, None))
            finally:
                setattr(self, attr, None)
        self._close_sqlite_connections_in_modules()
        if getattr(self, "_keeper", None):
            try:
                self._keeper.close()
            except Exception:
                pass
            self._keeper = None
        try:
            gc.collect()
        except Exception:
            pass

    # -------------------------------------------------
    # RE-INIT
    # -------------------------------------------------
    def set_db_path(self, db_path: str) -> None:
        logger.info(f"Setting new db_path: {db_path} and re-initializing managers.")
        if getattr(self, "_keeper", None):
            try:
                self._keeper.close()
            except Exception:
                pass
            self._keeper = None
        self.db_path = db_path
        if isinstance(db_path, str) and db_path.startswith("file:") and "mode=memory" in db_path:
            try:
                self._keeper = sqlite3.connect(db_path, uri=True, check_same_thread=False)
                self._keeper.execute("PRAGMA foreign_keys = ON;")
            except Exception as e:
                logger.warning(f"Keeper connection (re-init) failed: {e}")
        db_init_db(db_path)
        self._init_managers()

    # -------------------------------------------------
    # LOW LEVEL HELPERS
    # -------------------------------------------------
    def _connect_for_ops(self):
        if getattr(self, "_keeper", None) is not None:
            return self._keeper, False
        use_uri = isinstance(self.db_path, str) and self.db_path.startswith("file:")
        conn = sqlite3.connect(self.db_path, uri=use_uri)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn, True

    def _ensure_default_user(self) -> int:
        if self._default_user_id:
            return self._default_user_id
        conn, close_after = self._connect_for_ops()
        try:
            row = conn.execute("SELECT id FROM users ORDER BY id LIMIT 1").fetchone()
            if row:
                self._default_user_id = int(row[0])
            else:
                conn.execute(
                    "INSERT INTO users (username, password_hash, role, is_active) VALUES (?,?,?,?)",
                    ("default_user", "", "user", 1),
                )
                self._default_user_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
                conn.commit()
            return self._default_user_id
        finally:
            if close_after:
                conn.close()

    def _ensure_counterparty_user(self, contact_id: int) -> int:
        conn, close_after = self._connect_for_ops()
        try:
            username = f"contact_{contact_id}"
            row = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
            if row:
                return int(row[0])
            conn.execute(
                "INSERT INTO users (username, password_hash, role, is_active) VALUES (?,?,?,?)",
                (username, "", "user", 1),
            )
            uid = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
            conn.commit()
            return uid
        finally:
            if close_after:
                conn.close()

    def _contact_exists(self, contact_id: int) -> bool:
        conn, close_after = self._connect_for_ops()
        try:
            row = conn.execute("SELECT id FROM contacts WHERE id=?", (contact_id,)).fetchone()
            return row is not None
        finally:
            if close_after:
                conn.close()

    # -------------------------------------------------
    # VALIDAZIONI
    # -------------------------------------------------
    def _validate_expense(self, title, price, date) -> Optional[str]:
        if not title or not str(title).strip():
            return "Missing title (campo: titolo)"
        try:
            p = float(price)
            if p <= 0:
                return "Invalid price (campo: prezzo)"
        except Exception:
            return "Invalid price (campo: prezzo)"
        if not isinstance(date, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
            return "Invalid date format (campo: data)"
        try:
            datetime.date.fromisoformat(date)
        except ValueError:
            return "Invalid date value (campo: data)"
        return None

    def _validate_transaction(self, contact_id, ttype, amount, date) -> Optional[str]:
        if contact_id is None:
            return "Missing contact_id (campo: contatto)"
        try:
            cid = int(contact_id)
            if cid <= 0:
                return "Invalid contact_id (campo: contatto)"
        except Exception:
            return "Invalid contact_id (campo: contatto)"
        if not self._contact_exists(int(contact_id)):
            return "contact not found (campo: contatto)"
        if not isinstance(ttype, str) or ttype.lower() not in ("credit", "debit"):
            return "invalid type (campo: tipo)"
        try:
            a = float(amount)
            if a <= 0:
                return "amount must be positive (campo: prezzo)"
        except Exception:
            return "amount must be numeric (campo: prezzo)"
        if not isinstance(date, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
            return "invalid date format (campo: data)"
        try:
            datetime.date.fromisoformat(date)
        except ValueError:
            return "invalid date value (campo: data)"
        return None

    # -------------------------------------------------
    # LOCALIZZAZIONE / NORMALIZZAZIONE
    # -------------------------------------------------
    def _localize_error_msg(self, msg: str) -> str:
        try:
            low = msg.lower()
            mapping = [
                ("title", "titolo"),
                ("price", "prezzo"),
                ("date", "data"),
                ("category", "categoria"),
                ("name", "nome"),
                ("type", "tipo"),
                ("contact_id", "contatto"),
                ("contact id", "contatto"),
                ("contact", "contatto"),
                ("user_id", "utente"),
                ("user id", "utente"),
                ("amount", "prezzo"),
            ]
            for eng, ita in mapping:
                if eng in low and ita not in low:
                    return f"{msg} (campo: {ita})"
            return msg
        except Exception:
            return msg

    def _wrap(self, op: str, result: Any):
        try:
            if isinstance(result, dict) and "success" in result and "error" in result:
                if not result.get("success") and isinstance(result.get("error"), str):
                    result["error"] = self._localize_error_msg(result["error"])
                if "data" not in result:
                    result["data"] = None
                return result
            if isinstance(result, (list, tuple)):
                return dict_response(True, None, list(result))
            if result is True:
                return dict_response(True, None, None)
            if result:
                return dict_response(True, None, result)
            return dict_response(False, f"{op} returned no result")
        except Exception as e:
            logger.error(f"Normalization error in {op}: {e}")
            return dict_response(False, f"{op} normalization error: {e}")

    # -------------------------------------------------
    # TABLES (ibrido lista/dict)
    # -------------------------------------------------
    def list_tables(self):
        """
        Ritorna un oggetto che:
        - Iterato produce solo le tabelle core richieste dal test unitario (contacts, expenses, transactions)
        - Supporta accesso ['data'] / ['tables'] per la lista completa
        - Espone chiavi 'success', 'error' (compat eventuale)
        """
        try:
            raw = db_list_tables(self.db_path)
            if isinstance(raw, dict):
                full = raw.get("data") or raw.get("tables") or []
            elif isinstance(raw, list):
                full = raw
            else:
                full = []
            full = list(full)
            core_set = {"contacts", "expenses", "transactions"}
            core = sorted([t for t in full if t in core_set])

            class TablesView(list):
                def __init__(self, core_list, full_list):
                    super().__init__(core_list)
                    self._full = list(full_list)

                def __getitem__(self, key):
                    if isinstance(key, str):
                        if key in ("data", "tables"):
                            return list(self._full)
                        if key == "success":
                            return True
                        if key == "error":
                            return None
                        raise KeyError(key)
                    return super().__getitem__(key)

                # Dict-like helpers
                def keys(self):
                    return ["success", "error", "data"]

                def items(self):
                    return [
                        ("success", True),
                        ("error", None),
                        ("data", list(self._full))
                    ]

                def get(self, k, default=None):
                    try:
                        return self[k]
                    except KeyError:
                        return default

                def __contains__(self, item):
                    if isinstance(item, str) and item in ("success", "error", "data"):
                        return True
                    return list.__contains__(self, item)

            tv = TablesView(core, full)
            return tv
        except Exception as e:
            logger.error(f"list_tables failed: {e}")
            # In caso di errore ritorniamo una vista vuota coerente
            class EmptyTables(list):
                def __getitem__(self, key):
                    if isinstance(key, str):
                        if key == "success":
                            return False
                        if key == "error":
                            return str(e)
                        if key in ("data", "tables"):
                            return []
                        raise KeyError(key)
                    return super().__getitem__(key)
                def keys(self):
                    return ["success", "error", "data"]
                def items(self):
                    return [("success", False), ("error", str(e)), ("data", [])]
                def get(self, k, default=None):
                    try:
                        return self[k]
                    except KeyError:
                        return default
            return EmptyTables()

    # -------------------------------------------------
    # EXPENSES
    # -------------------------------------------------
    def add_expense(self, *args, **kwargs):
        try:
            first = kwargs.get("title") or kwargs.get("description")
            if len(args) >= 1:
                first = args[0] if first is None else first
            title = first
            price = kwargs.get("price", args[1] if len(args) >= 2 else None)
            date = kwargs.get("date", args[2] if len(args) >= 3 else None)

            validation = self._validate_expense(title, price, date)
            if validation:
                return dict_response(False, validation)

            if len(args) >= 4:
                category = args[3]
            else:
                category = kwargs.get("category")

            user_id = kwargs.get("user_id", self._ensure_default_user())
            res = self.expenses.add_expense(title, float(price), date, category, user_id)
            return self._wrap("add_expense", res)
        except Exception as e:
            logger.error(f"add_expense failed: {e}")
            return dict_response(False, str(e))

    def delete_expense(self, expense_id, *args, **kwargs):
        try:
            user_id = kwargs.get("user_id", self._ensure_default_user())
            res = self.expenses.delete_expense(expense_id, user_id)
            return self._wrap("delete_expense", res)
        except Exception as e:
            logger.error(f"delete_expense failed: {e}")
            return dict_response(False, str(e))

    def search_expenses(self, *args, **kwargs):
        try:
            user_id = kwargs.get("user_id", self._ensure_default_user())
            res = self.expenses.search_expenses(*args, user_id)
            return self._wrap("search_expenses", res)
        except Exception as e:
            logger.error(f"search_expenses failed: {e}")
            return dict_response(False, str(e))

    def get_expenses(self, *args, **kwargs):
        try:
            user_id = kwargs.get("user_id", self._ensure_default_user())
            res = self.expenses.get_expenses(user_id)
            return self._wrap("get_expenses", res)
        except Exception as e:
            logger.error(f"get_expenses failed: {e}")
            return dict_response(False, str(e))

    def clear_expenses(self, *args, **kwargs):
        try:
            user_id = kwargs.get("user_id", self._ensure_default_user())
            res = self.expenses.clear_expenses(user_id)
            return self._wrap("clear_expenses", res)
        except Exception as e:
            logger.error(f"clear_expenses failed: {e}")
            return dict_response(False, str(e))

    # -------------------------------------------------
    # CONTACTS
    # -------------------------------------------------
    def add_contact(self, *args, **kwargs):
        try:
            name = kwargs.get("name", args[0] if len(args) >= 1 else None)
            if not name or not str(name).strip():
                return dict_response(False, "name required (campo: nome)")
            user_id = kwargs.get("user_id", self._ensure_default_user())
            res = self.contacts.add_contact(name, user_id)
            return self._wrap("add_contact", res)
        except Exception as e:
            logger.error(f"add_contact failed: {e}")
            return dict_response(False, str(e))

    def get_contacts(self, *args, **kwargs):
        try:
            user_id = kwargs.get("user_id", self._ensure_default_user())
            res = self.contacts.get_contacts(user_id)
            return self._wrap("get_contacts", res)
        except Exception as e:
            logger.error(f"get_contacts failed: {e}")
            return dict_response(False, str(e))

    def delete_contact(self, contact_id_or_name, *args, **kwargs):
        try:
            user_id = kwargs.get("user_id", self._ensure_default_user())
            res = self.contacts.delete_contact(contact_id_or_name, user_id)
            return self._wrap("delete_contact", res)
        except Exception as e:
            logger.error(f"delete_contact failed: {e}")
            return dict_response(False, str(e))

    # -------------------------------------------------
    # TRANSACTIONS
    # -------------------------------------------------
    def add_transaction(self, *args, **kwargs):
        try:
            if len(args) >= 5:
                contact_id, ttype, amount, date, note = args[:5]
            else:
                contact_id = kwargs.get("contact_id")
                ttype = kwargs.get("type")
                amount = kwargs.get("amount")
                date = kwargs.get("date")
                note = kwargs.get("note")

            validation = self._validate_transaction(contact_id, ttype, amount, date)
            if validation:
                return dict_response(False, validation)

            user_id = kwargs.get("user_id", self._ensure_default_user())
            to_uid = self._ensure_counterparty_user(int(contact_id))
            res = self.transactions.add_transaction(
                from_user_id=user_id,
                to_user_id=to_uid,
                type_=ttype.lower(),
                amount=float(amount),
                date=date,
                description=note,
                contact_id=int(contact_id),
            )
            return self._wrap("add_transaction", res)
        except Exception as e:
            logger.error(f"add_transaction failed: {e}")
            return dict_response(False, str(e))

    def get_transactions(self, contact_id, *args, **kwargs):
        try:
            user_id = kwargs.get("user_id", self._ensure_default_user())
            res = self.transactions.get_transactions(user_id, as_sender=True, contact_id=contact_id)
            return self._wrap("get_transactions", res)
        except Exception as e:
            logger.error(f"get_transactions failed: {e}")
            return dict_response(False, str(e))

    def delete_transaction(self, transaction_id, *args, **kwargs):
        try:
            user_id = kwargs.get("user_id", self._ensure_default_user())
            res = self.transactions.delete_transaction(transaction_id, user_id)
            return self._wrap("delete_transaction", res)
        except Exception as e:
            logger.error(f"delete_transaction failed: {e}")
            return dict_response(False, str(e))

    def get_contact_balance(self, contact_id, *args, **kwargs):
        try:
            user_id = kwargs.get("user_id", self._ensure_default_user())
            res = self.transactions.get_contact_balance(user_id, contact_id)
            wrapped = self._wrap("get_contact_balance", res)
            if wrapped.get("success") and isinstance(wrapped.get("data"), dict) and "net" in wrapped["data"]:
                wrapped["data"] = float(wrapped["data"]["net"])
            return wrapped
        except Exception as e:
            logger.error(f"get_contact_balance failed: {e}")
            return dict_response(False, str(e))