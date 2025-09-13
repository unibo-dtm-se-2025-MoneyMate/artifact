import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from collections import defaultdict

# ==========================
# FRAME PRINCIPALE
# ==========================
class MoneyMateApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MoneyMate - Gestione Finanziaria")
        self.geometry("950x700")
        self.resizable(True, True)

        # Storage centrale
        self.expenses = []   # [(date, desc, amount)]
        self.contacts = []   # [(name, phone)]
        self.debts = []      # [(creditore, debitore, amount)]

        # Container principale
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        # Creazione barra laterale
        sidebar = ttk.Frame(container, width=200, relief="sunken")
        sidebar.grid(row=0, column=0, rowspan=4, sticky="ns")

        # Sezione menu con icone (commenta e aggiungi le icone necessarie)
        menu_sections = {
            "Spese": lambda: self.show_frame(ExpensesFrame),
            "Contatti": lambda: self.show_frame(ContactsFrame),
            "Debiti/Crediti": lambda: self.show_frame(DebtsCreditsFrame),
            "Grafici": lambda: self.show_frame(ChartsFrame),
        }

        for index, (label, command) in enumerate(menu_sections.items()):
            button = ttk.Button(sidebar, text=label, command=command, width=20)
            button.grid(row=index, column=0, padx=10, pady=10)

        # Creazione area centrale
        self.frames = {}
        for F in (ExpensesFrame, ContactsFrame, DebtsCreditsFrame, ChartsFrame):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=1, sticky="nsew")

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

        self.show_frame(ExpensesFrame)

    def show_frame(self, cont):
        frame = self.frames[cont]
        if hasattr(frame, "refresh"):
            frame.refresh()
        frame.tkraise()

import tkinter as tk
from tkinter import ttk, messagebox

class ExpensesFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Titolo della sezione
        ttk.Label(self, text="Inserisci una spesa", font=("Arial", 14)).pack(pady=10)
        form_frame = ttk.Frame(self)
        form_frame.pack(pady=10)

        # Campo Data
        ttk.Label(form_frame, text="Data (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5)
        self.date_entry = ttk.Entry(form_frame)
        self.date_entry.grid(row=0, column=1, padx=5, pady=5)

        # Campo Descrizione
        ttk.Label(form_frame, text="Descrizione:").grid(row=1, column=0, padx=5, pady=5)
        self.desc_entry = ttk.Entry(form_frame)
        self.desc_entry.grid(row=1, column=1, padx=5, pady=5)

        # Campo Categoria
        ttk.Label(form_frame, text="Categoria:").grid(row=2, column=0, padx=5, pady=5)
        self.category_combo = ttk.Combobox(
            form_frame,
            values=["Cibo", "Trasporti", "Affitto", "Svago", "Shopping", "Altro"]
        )
        self.category_combo.grid(row=2, column=1, padx=5, pady=5)

        # Campo Importo
        ttk.Label(form_frame, text="Importo (€):").grid(row=3, column=0, padx=5, pady=5)
        self.amount_entry = ttk.Entry(form_frame)
        self.amount_entry.grid(row=3, column=1, padx=5, pady=5)

        # Bottone Aggiungi
        ttk.Button(form_frame, text="Aggiungi", command=self.add_expense).grid(
            row=4, column=0, columnspan=2, pady=10
        )

        # Barra di ricerca
        search_frame = ttk.Frame(self)
        search_frame.pack(pady=5)
        ttk.Label(search_frame, text="Cerca:").pack(side="left")
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side="left", padx=5)
        ttk.Button(search_frame, text="Filtra", command=self.filter_expenses).pack(side="left")
        ttk.Button(search_frame, text="Reset", command=self.refresh_table).pack(side="left")

        # Tabella delle spese
        self.table = ttk.Treeview(
            self,
            columns=("data", "descrizione", "categoria", "importo"),
            show="headings"
        )
        self.table.heading("data", text="Data")
        self.table.heading("descrizione", text="Descrizione")
        self.table.heading("categoria", text="Categoria")
        self.table.heading("importo", text="Importo")
        self.table.pack(fill="both", expand=True)

        # Bottoni gestione
        ttk.Button(self, text="Rimuovi selezionato", command=self.remove_expense).pack(pady=5)
        ttk.Button(self, text="Modifica selezionato", command=self.edit_expense).pack(pady=5)

        # Totale spese
        self.total_label = ttk.Label(self, text="Totale spese: 0.00 €", font=("Arial", 12, "bold"))
        self.total_label.pack(pady=10)

    def add_expense(self):
        date = self.date_entry.get().strip()
        desc = self.desc_entry.get().strip()
        category = self.category_combo.get().strip() or "Altro"
        amount = self.amount_entry.get().strip()

        # Verifica che tutti i campi obbligatori siano presenti
        if not date or not desc or not amount:
            messagebox.showerror("Errore", "Inserisci tutti i campi obbligatori!")
            return {"success": False, "error": "Tutti i campi sono obbligatori!"}

        try:
            # Gestisce la virgola come separatore decimale
            amount = float(amount.replace(',', '.'))
        except ValueError:
            messagebox.showerror("Errore", "L'importo deve essere un numero!")
            return {"success": False, "error": "L'importo deve essere un numero valido!"}

        # Salvataggio della spesa (da aggiungere alla lista/array di spese)
        self.controller.expenses.append({"date": date, "description": desc, "category": category, "amount": amount})

        # Aggiorna la tabella per visualizzare la nuova spesa
        self.refresh_table()

        # Pulisci i campi
        self.date_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.category_combo.set("")
        self.amount_entry.delete(0, tk.END)

        return {"success": True, "error": None}

    def remove_expense(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("Attenzione", "Seleziona una riga da rimuovere.")
            return
        index = self.table.index(selected[0])
        self.table.delete(selected)
        del self.controller.expenses[index]
        self.update_total()

    def update_total(self):
        total = sum(expense["amount"] for expense in self.controller.expenses)
        self.total_label.config(text=f"Totale spese: {total:.2f} €")

    def filter_expenses(self):
        query = self.search_entry.get().strip().lower()
        filtered = [
            exp for exp in self.controller.expenses
            if query in exp["date"].lower() or query in exp["description"].lower() or query in exp["category"].lower()
        ]
        self.refresh_table(filtered)

    def refresh_table(self, data=None):
        # Pulisci tabella
        for row in self.table.get_children():
            self.table.delete(row)
        # Ricarica dati (filtrati o tutti)
        data = data if data is not None else self.controller.expenses
        for expense in data:
            self.table.insert("", "end", values=(expense["date"], expense["description"], expense["category"], f"{expense['amount']:.2f} €"))
        self.update_total()

    def edit_expense(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("Attenzione", "Seleziona una riga da modificare.")
            return

        index = self.table.index(selected[0])
        old_data = self.controller.expenses[index]

        # Popup di modifica
        popup = tk.Toplevel(self)
        popup.title("Modifica spesa")

        labels = ["Data (YYYY-MM-DD)", "Descrizione", "Categoria", "Importo (€)"]
        entries = []

        for i, (label, value) in enumerate(zip(labels, old_data.values())):
            ttk.Label(popup, text=label).grid(row=i, column=0, padx=5, pady=5)
            e = ttk.Entry(popup)
            e.grid(row=i, column=1, padx=5, pady=5)
            e.insert(0, value)
            entries.append(e)

        def save_changes():
            try:
                new_date = entries[0].get().strip()
                new_desc = entries[1].get().strip()
                new_cat = entries[2].get().strip() or "Altro"
                new_amount = float(entries[3].get().strip())
            except ValueError:
                messagebox.showerror("Errore", "Importo non valido.")
                return

            # Aggiorna nei dati
            self.controller.expenses[index] = {"date": new_date, "description": new_desc, "category": new_cat, "amount": new_amount}

            # Ricarica tabella
            self.refresh_table()
            popup.destroy()

        ttk.Button(popup, text="Salva", command=save_changes).grid(row=4, column=0, columnspan=2, pady=10)

        
# ==========================
# FRAME CONTATTI (con ricerca e modifica)
# ==========================
class ContactsFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ttk.Label(self, text="Gestione Contatti", font=("Arial", 14)).pack(pady=10)
        form_frame = ttk.Frame(self)
        form_frame.pack(pady=10)

        ttk.Label(form_frame, text="Nome:").grid(row=0, column=0, padx=5, pady=5)
        self.name_entry = ttk.Entry(form_frame)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Telefono:").grid(row=1, column=0, padx=5, pady=5)
        self.phone_entry = ttk.Entry(form_frame)
        self.phone_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(form_frame, text="Aggiungi Contatto", command=self.add_contact).grid(row=2, column=0, columnspan=2, pady=10)

        # Barra di ricerca
        search_frame = ttk.Frame(self)
        search_frame.pack(pady=5)
        ttk.Label(search_frame, text="Cerca:").pack(side="left")
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side="left", padx=5)
        ttk.Button(search_frame, text="Filtra", command=self.filter_contacts).pack(side="left")

        self.table = ttk.Treeview(self, columns=("nome", "telefono"), show="headings")
        self.table.heading("nome", text="Nome")
        self.table.heading("telefono", text="Telefono")
        self.table.pack(fill="both", expand=True)

        ttk.Button(self, text="Rimuovi selezionato", command=self.remove_contact).pack(pady=5)
        ttk.Button(self, text="Modifica selezionato", command=self.edit_contact).pack(pady=5)

    def add_contact(self):
        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()

        if not name or not phone:
            messagebox.showerror("Errore", "Inserisci tutti i campi!")
            return

        # Verifica validità del numero di telefono (esempio base)
        if not phone.isdigit() or len(phone) != 10:
            messagebox.showerror("Errore", "Il numero di telefono deve contenere 10 cifre.")
            return

        self.controller.contacts.append((name, phone))
        self.table.insert("", "end", values=(name, phone))
        self.name_entry.delete(0, tk.END)
        self.phone_entry.delete(0, tk.END)

    def remove_contact(self):
        selected = self.table.selection()
        if not selected:
            return
        index = self.table.index(selected[0])
        self.table.delete(selected)
        del self.controller.contacts[index]

    def edit_contact(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("Attenzione", "Seleziona un contatto da modificare.")
            return

        # Recupera il contatto selezionato
        selected_item = selected[0]
        item_values = self.table.item(selected_item, 'values')

        # Popup per modificare il contatto
        popup = tk.Toplevel(self)
        popup.title("Modifica Contatto")

        ttk.Label(popup, text="Nome:").grid(row=0, column=0, padx=5, pady=5)
        new_name = ttk.Entry(popup)
        new_name.insert(0, item_values[0])
        new_name.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(popup, text="Telefono:").grid(row=1, column=0, padx=5, pady=5)
        new_phone = ttk.Entry(popup)
        new_phone.insert(0, item_values[1])
        new_phone.grid(row=1, column=1, padx=5, pady=5)

        def save_changes():
            updated_name = new_name.get().strip()
            updated_phone = new_phone.get().strip()

            if not updated_name or not updated_phone:
                messagebox.showerror("Errore", "Inserisci tutti i campi!")
                return

            # Verifica validità del numero di telefono
            if not updated_phone.isdigit() or len(updated_phone) != 10:
                messagebox.showerror("Errore", "Il numero di telefono deve contenere 10 cifre.")
                return

            # Aggiorna il contatto
            index = self.table.index(selected_item)
            self.controller.contacts[index] = (updated_name, updated_phone)
            self.refresh_table()
            popup.destroy()

        ttk.Button(popup, text="Salva", command=save_changes).grid(row=2, column=0, columnspan=2, pady=10)

    def filter_contacts(self):
        query = self.search_entry.get().strip().lower()
        filtered = [
            contact for contact in self.controller.contacts
            if query in contact[0].lower() or query in contact[1].lower()
        ]
        self.refresh_table(filtered)

    def refresh_table(self, data=None):
        # Pulisci tabella
        for row in self.table.get_children():
            self.table.delete(row)
        # Ricarica dati (filtrati o tutti)
        data = data if data is not None else self.controller.contacts
        for name, phone in data:
            self.table.insert("", "end", values=(name, phone))


# ==========================
# FRAME DEBITI/CREDITI (con ricerca e modifica)
# ==========================
class DebtsCreditsFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ttk.Label(self, text="Gestione Debiti/Crediti", font=("Arial", 14)).pack(pady=10)
        form_frame = ttk.Frame(self)
        form_frame.pack(pady=10)

        ttk.Label(form_frame, text="Creditore:").grid(row=0, column=0, padx=5, pady=5)
        self.creditor_entry = ttk.Entry(form_frame)
        self.creditor_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Debitore:").grid(row=1, column=0, padx=5, pady=5)
        self.debtor_entry = ttk.Entry(form_frame)
        self.debtor_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Importo (€):").grid(row=2, column=0, padx=5, pady=5)
        self.amount_entry = ttk.Entry(form_frame)
        self.amount_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Button(form_frame, text="Aggiungi", command=self.add_debt).grid(row=3, column=0, columnspan=2, pady=10)

        # Barra di ricerca
        search_frame = ttk.Frame(self)
        search_frame.pack(pady=5)
        ttk.Label(search_frame, text="Cerca:").pack(side="left")
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side="left", padx=5)
        ttk.Button(search_frame, text="Filtra", command=self.filter_debts).pack(side="left")

        self.table = ttk.Treeview(self, columns=("creditore", "debitore", "importo"), show="headings")
        self.table.heading("creditore", text="Creditore")
        self.table.heading("debitore", text="Debitore")
        self.table.heading("importo", text="Importo")
        self.table.pack(fill="both", expand=True)

        ttk.Button(self, text="Rimuovi selezionato", command=self.remove_debt).pack(pady=5)
        ttk.Button(self, text="Modifica selezionato", command=self.edit_debt).pack(pady=5)

    def add_debt(self):
        creditor = self.creditor_entry.get().strip()
        debtor = self.debtor_entry.get().strip()
        amount = self.amount_entry.get().strip()

        if not creditor or not debtor or not amount:
            messagebox.showerror("Errore", "Inserisci tutti i campi!")
            return

        try:
            amount = float(amount)
            if amount <= 0:
                messagebox.showerror("Errore", "L'importo deve essere maggiore di zero.")
                return
        except ValueError:
            messagebox.showerror("Errore", "L'importo deve essere un numero valido!")
            return

        self.controller.debts.append((creditor, debtor, amount))
        self.table.insert("", "end", values=(creditor, debtor, f"{amount:.2f} €"))

        self.creditor_entry.delete(0, tk.END)
        self.debtor_entry.delete(0, tk.END)
        self.amount_entry.delete(0, tk.END)

    def remove_debt(self):
        selected = self.table.selection()
        if not selected:
            return
        index = self.table.index(selected[0])
        self.table.delete(selected)
        del self.controller.debts[index]

    def edit_debt(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("Attenzione", "Seleziona un debito/credito da modificare.")
            return

        # Recupera il debito/credito selezionato
        selected_item = selected[0]
        item_values = self.table.item(selected_item, 'values')

        # Popup per modificare il debito/credito
        popup = tk.Toplevel(self)
        popup.title("Modifica Debito/Credito")

        ttk.Label(popup, text="Creditore:").grid(row=0, column=0, padx=5, pady=5)
        new_creditor = ttk.Entry(popup)
        new_creditor.insert(0, item_values[0])
        new_creditor.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(popup, text="Debitore:").grid(row=1, column=0, padx=5, pady=5)
        new_debtor = ttk.Entry(popup)
        new_debtor.insert(0, item_values[1])
        new_debtor.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(popup, text="Importo (€):").grid(row=2, column=0, padx=5, pady=5)
        new_amount = ttk.Entry(popup)
        new_amount.insert(0, item_values[2].replace(" €", ""))
        new_amount.grid(row=2, column=1, padx=5, pady=5)

        def save_changes():
            updated_creditor = new_creditor.get().strip()
            updated_debtor = new_debtor.get().strip()
            updated_amount = new_amount.get().strip()

            if not updated_creditor or not updated_debtor or not updated_amount:
                messagebox.showerror("Errore", "Inserisci tutti i campi!")
                return

            try:
                updated_amount = float(updated_amount)
                if updated_amount <= 0:
                    messagebox.showerror("Errore", "L'importo deve essere maggiore di zero.")
                    return
            except ValueError:
                messagebox.showerror("Errore", "L'importo deve essere un numero valido!")
                return

            # Aggiorna il debito/credito
            index = self.table.index(selected_item)
            self.controller.debts[index] = (updated_creditor, updated_debtor, updated_amount)
            self.refresh_table()
            popup.destroy()

        ttk.Button(popup, text="Salva", command=save_changes).grid(row=3, column=0, columnspan=2, pady=10)

    def filter_debts(self):
        query = self.search_entry.get().strip().lower()
        filtered = [
            debt for debt in self.controller.debts
            if query in debt[0].lower() or query in debt[1].lower() or query in str(debt[2])
        ]
        self.refresh_table(filtered)

    def refresh_table(self, data=None):
        # Pulisci tabella
        for row in self.table.get_children():
            self.table.delete(row)
        # Ricarica dati (filtrati o tutti)
        data = data if data is not None else self.controller.debts
        for creditor, debtor, amount in data:
            self.table.insert("", "end", values=(creditor, debtor, f"{amount:.2f} €"))


# ==========================
# FRAME GRAFICI (aggiornato con categorie)
# ==========================
class ChartsFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ttk.Label(self, text="Grafici Finanziari", font=("Arial", 14)).pack(pady=10)
        self.canvas_frame = ttk.Frame(self)
        self.canvas_frame.pack(fill="both", expand=True)

        # Filtro per intervallo temporale (opzionale)
        self.timeframe_var = tk.StringVar(value="Mese")
        ttk.Label(self, text="Filtra per:").pack(pady=5)
        timeframe_menu = ttk.OptionMenu(self, self.timeframe_var, "Mese", "Settimana", "Mese", "Anno")
        timeframe_menu.pack(pady=5)
        ttk.Button(self, text="Aggiorna Grafico", command=self.refresh).pack(pady=5)

    def refresh(self):
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

        if not self.controller.expenses:
            ttk.Label(self.canvas_frame, text="Nessuna spesa registrata").pack(pady=20)
            return

        # Ottieni l'intervallo temporale selezionato
        timeframe = self.timeframe_var.get()

        # =======================
        # Distribuzione per CATEGORIA
        # =======================
        per_category = defaultdict(float)
        for _, _, category, amount in self.controller.expenses:
            per_category[category] += amount

        # =======================
        # Distribuzione per DATA
        # =======================
        per_date = defaultdict(float)

        if timeframe == "Mese":
            for date, _, _, amount in self.controller.expenses:
                month = date[:7]  # YYYY-MM (mese)
                per_date[month] += amount
        elif timeframe == "Settimana":
            for date, _, _, amount in self.controller.expenses:
                week = self.get_week_from_date(date)  # Funzione per ottenere la settimana
                per_date[week] += amount
        elif timeframe == "Anno":
            for date, _, _, amount in self.controller.expenses:
                year = date[:4]  # Anno
                per_date[year] += amount

        # Creazione figure matplotlib
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))

        # Torta per categoria
        axes[0].pie(
            per_category.values(),
            labels=per_category.keys(),
            autopct="%1.1f%%",
            startangle=90
        )
        axes[0].set_title("Distribuzione Spese per Categoria")

        # Barre per data
        axes[1].bar(per_date.keys(), per_date.values())
        axes[1].set_title(f"Spese per {timeframe}")
        axes[1].tick_params(axis='x', rotation=45)

        plt.tight_layout()

        # Inserimento nel frame Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        plt.close(fig)  # evita conflitti di rendering

    def get_week_from_date(self, date):
        from datetime import datetime
        # Estrae la settimana dell'anno (es. "Settimana 23")
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        return f"Settimana {date_obj.isocalendar()[1]}"


# ==========================
# AVVIO APP
# ==========================
if __name__ == "__main__":
    app = MoneyMateApp()
    app.mainloop()