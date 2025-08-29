import sqlite3
import logging
import MoneyMate.data_layer.logging_config  # Ensure global logging configuration

DB_PATH = "moneymate.db"
logger = logging.getLogger(__name__)

def get_connection(db_path=DB_PATH):
    try:
        conn = sqlite3.connect(db_path)
        logger.debug(f"Opened SQLite connection to {db_path}")
        return conn
    except Exception as e:
        logger.error(f"Failed to open SQLite connection to {db_path}: {e}")
        raise

def init_db(db_path=DB_PATH):
    """
    Creates the tables if they do not exist in the SQLite database.
    """
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            logger.info(f"Initializing database and creating tables if they do not exist (db_path={db_path})")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    price REAL NOT NULL,
                    date TEXT NOT NULL,
                    category TEXT NOT NULL
                )""")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL
                )""")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact_id INTEGER NOT NULL,
                    type TEXT CHECK(type IN ('debit', 'credit')) NOT NULL,
                    amount REAL NOT NULL,
                    date TEXT NOT NULL,
                    description TEXT,
                    FOREIGN KEY(contact_id) REFERENCES contacts(id)
                )""")
            # --- Add users table creation here ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL
                )
            """)
            conn.commit()
            logger.info("Database tables created and initialization committed.")
    except Exception as e:
        logger.error(f"Error initializing database at {db_path}: {e}")
        raise

# --- Method to list all tables in the DB, especially useful for testing ---
def list_tables(db_path=DB_PATH):
    """
    Returns a list of all tables in the database.
    """
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            logger.debug(f"Listing all tables in the database (db_path={db_path})")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"Found tables: {tables}")
        return {"success": True, "error": None, "data": tables}
    except Exception as e:
        logger.error(f"Error listing tables in database {db_path}: {e}")
        return {"success": False, "error": str(e), "data": None}