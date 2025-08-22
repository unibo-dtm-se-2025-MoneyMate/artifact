import sqlite3

DB_PATH = "moneymate.db"

def get_connection(db_path=DB_PATH):
    return sqlite3.connect(db_path)

def init_db(db_path=DB_PATH):
    """
    Creates the tables if they do not exist in the SQLite database.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()  # To execute SQL commands
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
    conn.commit()
    conn.close()

# --- Method to list all tables in the DB, especially useful for testing ---
def list_tables(db_path=DB_PATH):
    """
    Returns a list of all tables in the database.
    """
    try:
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return {"success": True, "error": None, "data": tables}
    except Exception as e:
        return {"success": False, "error": str(e), "data": None}