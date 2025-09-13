import sqlite3

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        # Crea le tabelle se non esistono già
        self.create_tables()

    def create_tables(self):
        """Crea le tabelle se non esistono già."""
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            description TEXT,
            category TEXT,
            amount REAL
        );
        """)
        self.conn.commit()

    def add_expense(self, date, description, category, amount):
        """Aggiungi una nuova spesa nel database."""
        try:
            self.cursor.execute("""
            INSERT INTO expenses (date, description, category, amount)
            VALUES (?, ?, ?, ?);
            """, (date, description, category, amount))
            self.conn.commit()
            return {"success": True, "error": None}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_expenses(self):
        """Recupera tutte le spese dal database."""
        self.cursor.execute("SELECT * FROM expenses")
        rows = self.cursor.fetchall()
        return {"data": rows}

    def delete_expense(self, expense_id):
        """Elimina una spesa dal database."""
        try:
            self.cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            self.conn.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def clear_expenses(self):
        """Elimina tutte le spese dal database."""
        try:
            self.cursor.execute("DELETE FROM expenses")
            self.conn.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def close(self):
        """Chiudi la connessione al database."""
        self.conn.close()

    def search_expenses(self, search_term):
        """Cerca le spese per descrizione nel database."""
        self.cursor.execute("""
        SELECT * FROM expenses WHERE description LIKE ?;
        """, ('%' + search_term + '%',))
        rows = self.cursor.fetchall()
        return {"data": rows}
