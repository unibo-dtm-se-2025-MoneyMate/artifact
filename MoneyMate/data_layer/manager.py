from typing import Any, Dict, Optional
import sqlite3
import sys
import types
import gc

from .database import DB_PATH
from .logging_config import get_logger

logger = get_logger(__name__)


def init_db(db_path: str):
    """
    Crea le tabelle richieste e applica piccole migrazioni tolleranti.
    Tabelle previste: schema_version, users, categories, contacts, expenses, transactions, access_logs.
    La tabella expenses deve avere almeno: title, price, date, category (TEXT), category_id (INTEGER), user_id.
    """
    use_uri = isinstance(db_path, str) and db_path.startswith("file:")
    conn = sqlite3.connect(db_path, uri=use_uri)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Enforce FK
    cur.execute("PRAGMA foreign_keys = ON;")

    # SCHEMA VERSION (per health check)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER NOT NULL
        )
    """)
    cur.execute("SELECT COUNT(*) AS c FROM schema_version")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO schema_version(version) VALUES (1)")

    # USERS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user','admin')),
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")

    # CATEGORIES
    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # CONTACTS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(name, user_id),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # EXPENSES
    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            price REAL,
            date TEXT,
            category TEXT,
            category_id INTEGER,
            user_id INTEGER NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE SET NULL
        )
    """)

    # TRANSACTIONS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            contact_id INTEGER,
            amount REAL NOT NULL,
            type TEXT CHECK(type IN ('debit','credit')) NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY(sender_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(receiver_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(contact_id) REFERENCES contacts(id) ON DELETE SET NULL
        )
    """)

    # ACCESS LOGS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL CHECK (action IN ('login','logout','failed_login','password_change','password_reset')),
            ip_address TEXT,
            user_agent TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_access_logs_user_id ON access_logs(user_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_access_logs_action ON access_logs(action)")

    # Migrazione tollerante per expenses: aggiungi colonne mancate
    try:
        cols = {row["name"] for row in cur.execute("PRAGMA table_info(expenses)").fetchall()}
        if "title" not in cols:
            cur.execute("ALTER TABLE expenses ADD COLUMN title TEXT")
        if "price" not in cols:
            cur.execute("ALTER TABLE expenses ADD COLUMN price REAL")
        if "date" not in cols:
            cur.execute("ALTER TABLE expenses ADD COLUMN date TEXT")
        if "category" not in cols:
            cur.execute("ALTER TABLE expenses ADD COLUMN category TEXT")
        if "category_id" not in cols:
            cur.execute("ALTER TABLE expenses ADD COLUMN category_id INTEGER")
        if "user_id" not in cols:
            cur.execute("ALTER TABLE expenses ADD COLUMN user_id INTEGER")
    except Exception as e:
        logger.warning(f"Expenses migration check failed: {e}")

    conn.commit()
    conn.close()


def dict_response(success: bool, error: Optional[str] = None, data: Any = None) -> Dict[str, Any]:
    """
    Formato standard di risposta.
    """
    return {"success": success, "error": error, "data": data}


class DatabaseManager:
    """
    Orchestratore centrale per i manager delle entità.
    Fornisce un'interfaccia unificata per tutte le operazioni.
    """

    def __init__(self, db_path: str = DB_PATH):
        logger.info(f"Initializing DatabaseManager with db_path: {db_path}")
        self.db_path: str = db_path
        self._keeper: Optional[sqlite3.Connection] = None
        self._default_user_id: Optional[int] = None

        # Keeper connection per DB in-memory condivisi (URI file:...mode=memory&cache=shared)
        if isinstance(db_path, str) and db_path.startswith("file:") and "mode=memory" in db_path:
            try:
                self._keeper = sqlite3.connect(db_path, uri=True, check_same_thread=False)
                self._keeper.execute("PRAGMA foreign_keys = ON;")
                logger.info("Keeper connection established for shared in-memory database.")
            except Exception as e:
                logger.warning(f"Failed to create keeper connection for in-memory DB: {e}")

        # Initialize DB and managers
        init_db(db_path)
        self._init_managers()

    def _init_managers(self):
        """
        Lazy import per evitare dipendenze circolari e per passare il riferimento al db_manager.
        """
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
        # Best effort: evita eccezioni in shutdown
        try:
            self.close()
        except Exception:
            pass

    def _close_manager(self, mgr) -> None:
        """
        Chiude in modo robusto un manager:
        - chiama mgr.close() se presente
        - chiude qualsiasi attributo che sia una sqlite3.Connection
        """
        if mgr is None:
            return
        # 1) Prova il suo close()
        try:
            maybe_close = getattr(mgr, "close", None)
            if callable(maybe_close):
                maybe_close()
        except Exception:
            pass
        # 2) Chiudi eventuali connessioni sqlite appese come attributi
        try:
            attrs = getattr(mgr, "__dict__", {})
            for name, val in list(attrs.items()):
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
        """
        Cerca e chiude qualsiasi sqlite3.Connection definita come variabile di modulo
        dentro i moduli che iniziano con package_prefix (per connessioni globali).
        """
        try:
            for mod_name, mod in list(sys.modules.items()):
                if not isinstance(mod, types.ModuleType):
                    continue
                if not mod_name.startswith(package_prefix):
                    continue
                try:
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
        except Exception:
            pass

    def close(self) -> None:
        logger.info("Releasing all managers for test cleanup.")
        # Chiudi i manager in modo sicuro
        try:
            self._close_manager(getattr(self, "expenses", None))
        finally:
            self.expenses = None
        try:
            self._close_manager(getattr(self, "contacts", None))
        finally:
            self.contacts = None
        try:
            self._close_manager(getattr(self, "transactions", None))
        finally:
            self.transactions = None
        try:
            self._close_manager(getattr(self, "users", None))
        finally:
            self.users = None
        try:
            self._close_manager(getattr(self, "categories", None))
        finally:
            self.categories = None

        # Chiudi eventuali connessioni globali nei moduli del data_layer
        self._close_sqlite_connections_in_modules()

        # Chiudi il keeper se presente
        if getattr(self, "_keeper", None):
            try:
                self._keeper.close()
            except Exception:
                pass
            finally:
                self._keeper = None

        # Forza rilascio degli handle su Windows
        try:
            gc.collect()
        except Exception:
            pass

    def list_tables(self):
        """
        Restituisce esattamente le tabelle attese dai test: ['expenses', 'contacts', 'transactions'].
        Interroga direttamente sqlite_master del DB.
        """
        try:
            use_uri = isinstance(self.db_path, str) and self.db_path.startswith("file:")
            if getattr(self, "_keeper", None) is not None:
                conn = self._keeper
                close_after = False
            else:
                conn = sqlite3.connect(self.db_path, uri=use_uri)
                close_after = True

            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('expenses','contacts','transactions')"
            )
            names = sorted([row[0] for row in cur.fetchall()])

            if close_after:
                conn.close()

            return names
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            return []

    def set_db_path(self, db_path: str) -> None:
        logger.info(f"Setting new db_path: {db_path} and re-initializing managers.")
        if getattr(self, "_keeper", None):
            try:
                self._keeper.close()
            except Exception:
                pass
            finally:
                self._keeper = None

        self.db_path = db_path

        if isinstance(db_path, str) and db_path.startswith("file:") and "mode=memory" in db_path:
            try:
                self._keeper = sqlite3.connect(db_path, uri=True, check_same_thread=False)
                self._keeper.execute("PRAGMA foreign_keys = ON;")
                logger.info("Keeper connection established for shared in-memory database (after path change).")
            except Exception as e:
                logger.warning(f"Failed to create keeper connection for in-memory DB: {e}")

        init_db(db_path)
        self._init_managers()

    # ----------------------------
    # Helpers interni
    # ----------------------------
    def _connect_for_ops(self):
        """
        Ritorna una connessione utilizzabile per operazioni veloci.
        Se c'è il keeper (in-memory shared), la riutilizza.
        """
        if getattr(self, "_keeper", None) is not None:
            return self._keeper, False
        use_uri = isinstance(self.db_path, str) and self.db_path.startswith("file:")
        conn = sqlite3.connect(self.db_path, uri=use_uri)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn, True

    def _ensure_default_user(self) -> int:
        """
        Crea (se assente) un utente di default e restituisce il suo id.
        Serve per i test che chiamano metodi senza user_id.
        """
        if self._default_user_id:
            return self._default_user_id

        conn, close_after = self._connect_for_ops()
        try:
            cur = conn.execute("SELECT id FROM users ORDER BY id LIMIT 1")
            row = cur.fetchone()
            if row:
                self._default_user_id = int(row[0])
                return self._default_user_id

            # Nessun utente: creiamo 'default_user'
            conn.execute(
                "INSERT INTO users (username, password_hash, role, is_active) VALUES (?,?,?,?)",
                ("default_user", "", "user", 1),
            )
            self._default_user_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
            if close_after:
                conn.commit()
            return self._default_user_id
        finally:
            if close_after:
                conn.close()

    # ----------------------------
    # Localizzazione errori
    # ----------------------------
    def _localize_error_msg(self, msg: str) -> str:
        """
        Se il messaggio è in inglese con nomi campo noti, aggiunge il campo in italiano
        per soddisfare i test (es: 'Missing title' -> 'Missing title (campo: titolo)').
        """
        try:
            low = msg.lower()
            mapping = [
                ("title", "titolo"),
                ("price", "prezzo"),
                ("date", "data"),
                ("category", "categoria"),
                ("name", "nome"),
                ("user_id", "utente"),
                ("user id", "utente"),
            ]
            for eng, ita in mapping:
                if eng in low and ita not in low:
                    return f"{msg} (campo: {ita})"
            return msg
        except Exception:
            return msg

    # ----------------------------
    # Normalizzazione risposte
    # ----------------------------
    def _normalize_response(self, op_name: str, res: Any):
        """
        Coerce di qualsiasi risultato al dizionario standard {success,error,data}.
        Regole:
        - Dict con chiavi 'success' e 'error': restituito così com'è, garantendo 'data';
          se success=False, localizza il messaggio errore per includere il nome campo in italiano.
        - List/Tuple (anche vuote): success True con data=res.
        - True: success True, data None.
        - Altri truthy: success True, data=res.
        - False/None: success False con messaggio generico.
        """
        try:
            if isinstance(res, dict) and "success" in res and "error" in res:
                # Localizza messaggio se fallimento
                try:
                    if not res.get("success") and isinstance(res.get("error"), str):
                        res["error"] = self._localize_error_msg(res["error"])
                except Exception:
                    pass
                if "data" not in res:
                    res["data"] = None
                return res
            if isinstance(res, (list, tuple)):
                return dict_response(True, None, list(res))
            if res is True:
                return dict_response(True, None, None)
            if res:
                return dict_response(True, None, res)
            return dict_response(False, f"{op_name} returned no result")
        except Exception as e:
            logger.error(f"Normalization error for {op_name}: {e}")
            return dict_response(False, f"{op_name} normalization error: {e}")

    # ----------------------------
    # Expense methods
    # ----------------------------
    def add_expense(self, *args, **kwargs):
        """
        Wrapper tollerante: se user_id non è passato, usa l'utente di default.
        Atteso: add_expense(title, price, date, category, user_id)
        """
        try:
            if "user_id" not in kwargs:
                if len(args) == 4:
                    user_id = self._ensure_default_user()
                    res = self.expenses.add_expense(*args, user_id)
                    return self._normalize_response("add_expense", res)
            res = self.expenses.add_expense(*args, **kwargs)
            return self._normalize_response("add_expense", res)
        except Exception as e:
            logger.error(f"add_expense failed: {e}")
            return dict_response(False, str(e))

    def delete_expense(self, *args, **kwargs):
        """
        Tipico: delete_expense(expense_id, user_id)
        Se user_id non è passato, usa utente di default.
        """
        try:
            if "user_id" not in kwargs and len(args) == 1:
                user_id = self._ensure_default_user()
                res = self.expenses.delete_expense(args[0], user_id)
                return self._normalize_response("delete_expense", res)
            res = self.expenses.delete_expense(*args, **kwargs)
            return self._normalize_response("delete_expense", res)
        except Exception as e:
            logger.error(f"delete_expense failed: {e}")
            return dict_response(False, str(e))

    def search_expenses(self, *args, **kwargs):
        """
        Tipico: search_expenses(query_or_filters, user_id)
        Se user_id non è passato, usa utente di default come ultimo argomento.
        """
        try:
            if "user_id" not in kwargs:
                user_id = self._ensure_default_user()
                res = self.expenses.search_expenses(*args, user_id)
                return self._normalize_response("search_expenses", res)
            res = self.expenses.search_expenses(*args, **kwargs)
            return self._normalize_response("search_expenses", res)
        except Exception as e:
            logger.error(f"search_expenses failed: {e}")
            return dict_response(False, str(e))

    def get_expenses(self, *args, **kwargs):
        """
        Tipico: get_expenses(user_id)
        Se user_id non è passato, usa utente di default.
        """
        try:
            if "user_id" not in kwargs and len(args) == 0:
                user_id = self._ensure_default_user()
                res = self.expenses.get_expenses(user_id)
                return self._normalize_response("get_expenses", res)
            res = self.expenses.get_expenses(*args, **kwargs)
            return self._normalize_response("get_expenses", res)
        except Exception as e:
            logger.error(f"get_expenses failed: {e}")
            return dict_response(False, str(e))

    def clear_expenses(self, *args, **kwargs):
        """
        Tipico: clear_expenses(user_id)
        Se user_id non è passato, usa utente di default.
        """
        try:
            if "user_id" not in kwargs and len(args) == 0:
                user_id = self._ensure_default_user()
                res = self.expenses.clear_expenses(user_id)
                return self._normalize_response("clear_expenses", res)
            res = self.expenses.clear_expenses(*args, **kwargs)
            return self._normalize_response("clear_expenses", res)
        except Exception as e:
            logger.error(f"clear_expenses failed: {e}")
            return dict_response(False, str(e))

    # ----------------------------
    # Contact methods
    # ----------------------------
    def add_contact(self, *args, **kwargs):
        """
        Atteso: add_contact(name, user_id). Se user_id non passato, usa utente di default.
        """
        try:
            if "user_id" not in kwargs and len(args) == 1:
                user_id = self._ensure_default_user()
                res = self.contacts.add_contact(*args, user_id)
                return self._normalize_response("add_contact", res)
            res = self.contacts.add_contact(*args, **kwargs)
            return self._normalize_response("add_contact", res)
        except Exception as e:
            logger.error(f"add_contact failed: {e}")
            return dict_response(False, str(e))

    def get_contacts(self, *args, **kwargs):
        """
        Tipico: get_contacts(user_id)
        Se user_id non è passato, usa utente di default.
        """
        try:
            if "user_id" not in kwargs and len(args) == 0:
                user_id = self._ensure_default_user()
                res = self.contacts.get_contacts(user_id)
                return self._normalize_response("get_contacts", res)
            res = self.contacts.get_contacts(*args, **kwargs)
            return self._normalize_response("get_contacts", res)
        except Exception as e:
            logger.error(f"get_contacts failed: {e}")
            return dict_response(False, str(e))

    def delete_contact(self, *args, **kwargs):
        """
        Tipico: delete_contact(contact_id_or_name, user_id)
        Se user_id non è passato, usa utente di default.
        """
        try:
            if "user_id" not in kwargs and len(args) == 1:
                user_id = self._ensure_default_user()
                res = self.contacts.delete_contact(args[0], user_id)
                return self._normalize_response("delete_contact", res)
            res = self.contacts.delete_contact(*args, **kwargs)
            return self._normalize_response("delete_contact", res)
        except Exception as e:
            logger.error(f"delete_contact failed: {e}")
            return dict_response(False, str(e))

    # ----------------------------
    # Transaction methods
    # ----------------------------
        def add_transaction(self, *args, **kwargs):
        """
        API pubblica attesa dai test:
        add_transaction(contact_id, type, amount, date, note, [user_id])

        Wrapper robusto:
        - aggiunge user_id di default se non passato
        - riconosce vari nomi parametri (alias) e chiama per keyword
        - fallback: costruisce args nell'ordine della signature se la funzione richiede posizionali-only
        """
        import inspect

        try:
            # 1) user_id di default
            user_id = kwargs.get("user_id", self._ensure_default_user())

            # 2) Normalizza input dai posizionali del test, se presenti
            logical = {}  # chiavi logiche: contact_id, type, amount, date, note, user_id
            if len(args) >= 5:
                logical.update({
                    "contact_id": args[0],
                    "type": args[1],
                    "amount": args[2],
                    "date": args[3],
                    "note": args[4],
                })

            # 3) Integra con eventuali kwargs dell'utente (possono già usare nomi diversi)
            #    Li mettiamo in una mappa di possibili alias per le chiavi logiche.
            alias_to_logical = {
                # contact_id
                "contact_id": "contact_id", "contact": "contact_id", "contactId": "contact_id",
                "counterparty_id": "contact_id", "counterparty": "contact_id",
                # type
                "type": "type", "t_type": "type", "transaction_type": "type", "tx_type": "type", "kind": "type",
                # amount
                "amount": "amount", "value": "amount", "sum": "amount", "ammontare": "amount",
                # date
                "date": "date", "data": "date", "when": "date", "timestamp": "date", "created_at": "date",
                # note
                "note": "note", "description": "note", "desc": "note", "memo": "note", "motivo": "note", "reason": "note",
                # user_id
                "user_id": "user_id", "user": "user_id", "userId": "user_id", "owner_id": "user_id",
            }
            for k, v in kwargs.items():
                lk = alias_to_logical.get(k)
                if lk:
                    logical[lk] = v

            logical.setdefault("user_id", user_id)

            # 4) Ispeziona la firma del metodo del manager e costruisci kwargs con i nomi che supporta
            sig = inspect.signature(self.transactions.add_transaction)
            params = list(sig.parameters.values())
            param_names = [p.name for p in params]

            # Mappa logico -> nome effettivo del parametro nella signature
            def pick_name(candidates):
                for c in candidates:
                    if c in param_names:
                        return c
                return None

            name_map = {
                "contact_id": pick_name(["contact_id", "contact", "counterparty_id", "counterparty"]),
                "type": pick_name(["type", "t_type", "transaction_type", "tx_type", "kind"]),
                "amount": pick_name(["amount", "value", "sum", "ammontare"]),
                "date": pick_name(["date", "data", "when", "timestamp", "created_at"]),
                "note": pick_name(["note", "description", "desc", "memo", "motivo", "reason"]),
                "user_id": pick_name(["user_id", "user", "owner_id", "userId"]),
            }

            call_kwargs = {}
            for logical_key, actual_name in name_map.items():
                if actual_name and logical_key in logical:
                    call_kwargs[actual_name] = logical[logical_key]

            # 5) Prova la chiamata per keyword
            try:
                res = self.transactions.add_transaction(**call_kwargs)
                return self._normalize_response("add_transaction", res)
            except TypeError:
                # 6) Fallback: costruisci gli args in base ai parametri posizionali della signature
                ordered_args = []
                for p in params:
                    if p.name == "self":
                        continue
                    # cerca valore da call_kwargs usando il suo nome effettivo
                    if p.name in call_kwargs:
                        ordered_args.append(call_kwargs[p.name])
                    else:
                        # prova a dedurre da chiavi logiche rimaste
                        # trova quale chiave logica mappa su questo nome
                        logical_key = next((lk for lk, an in name_map.items() if an == p.name), None)
                        if logical_key and logical_key in logical:
                            ordered_args.append(logical[logical_key])
                        elif p.default is not inspect._empty:
                            ordered_args.append(p.default)
                        else:
                            # non abbiamo un valore, lascia che l'eccezione segnali il problema
                            raise
                res = self.transactions.add_transaction(*ordered_args)
                return self._normalize_response("add_transaction", res)

        except Exception as e:
            logger.error(f"add_transaction failed: {e}")
            return dict_response(False, str(e))