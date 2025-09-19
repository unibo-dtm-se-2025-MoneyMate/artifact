import os
import sqlite3
from pathlib import Path

# Percorso di default del DB, sovrascrivibile con variabile d'ambiente
DEFAULT_DB_PATH = os.environ.get("MONEYMATE_DB", "MoneyMate/data/moneymate.db")
SCHEMA_FILE = Path("sql/auth_schema.sql")

def ensure_parent_dir(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

def init_with_sql(conn: sqlite3.Connection):
    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_FILE}")
    with SCHEMA_FILE.open("r", encoding="utf-8") as f:
        sql = f.read()
    conn.executescript(sql)

def init_with_module(conn: sqlite3.Connection) -> bool:
    try:
        # Se esiste, usa la funzione del tuo modulo per inizializzare lo schema
        from MoneyMate.data_layer.auth import init_auth_schema  # type: ignore
        init_auth_schema(conn)  # Assunto: accetta una sqlite3.Connection
        return True
    except Exception as e:
        print(f"[init_db] init_auth_schema non usata (fallback allo SQL): {e}")
        return False

def main():
    db_path = Path(DEFAULT_DB_PATH)
    ensure_parent_dir(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        used_module = init_with_module(conn)
        if not used_module:
            init_with_sql(conn)
    print(f"[init_db] Database inizializzato in: {db_path.resolve()}")

if __name__ == "__main__":
    main()