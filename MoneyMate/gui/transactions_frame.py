"""
Tkinter frame for managing person-to-person transactions in the GUI.

Key behaviors:
- Uses a contact picker to determine the counterparty (no explicit user IDs).
- Allows adding credit/debit transactions with date, amount, and description.
- Provides filtering by text and direction (All/Sent/Received).
- Displays transactions in a unified table, with derived direction and
  human-readable counterparty labels.
- Shows a dynamic total balance using api_get_user_balance_breakdown.
- Allows removal of transactions that the current user has sent.

All data operations go through the high-level MoneyMate data-layer API.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from MoneyMate.data_layer.api import (
    api_add_transaction, api_get_transactions, api_delete_transaction,
    api_get_contacts, api_get_user_balance_breakdown
)

class TransactionsFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style='Content.TFrame')
        self.controller = controller

        self.contacts_map = {}

        top_frame = ttk.LabelFrame(self, text="Add Transaction", style='TLabelframe')
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        form_grid = ttk.Frame(top_frame, style='TLabelframe')
        form_grid.pack(fill=tk.X, padx=10, pady=10)
        form_grid.columnconfigure(1, weight=1)
        form_grid.columnconfigure(3, weight=1)

        ttk.Label(form_grid, text="Date (YYYY-MM-DD):",
                  style='TLabel', background=self.controller.FRAME_COLOR).grid(row=0, column=0, padx=5, pady=8, sticky=tk.W)
        self.date_entry = ttk.Entry(form_grid, width=15, style='TEntry')
        self.date_entry.grid(row=0, column=1, padx=5, pady=8, sticky=tk.EW)
        self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))

        ttk.Label(form_grid, text="Contact:",
                  style='TLabel', background=self.controller.FRAME_COLOR).grid(row=0, column=2, padx=(15, 5), pady=8, sticky=tk.W)
        self.contact_combo = ttk.Combobox(form_grid, state="readonly", style='TCombobox')
        self.contact_combo.grid(row=0, column=3, padx=5, pady=8, sticky=tk.EW)

        ttk.Label(form_grid, text="Type:",
                  style='TLabel', background=self.controller.FRAME_COLOR).grid(row=1, column=0, padx=5, pady=8, sticky=tk.W)
        self.type_combo = ttk.Combobox(form_grid, values=["credit", "debit"],
                                       state="readonly", style='TCombobox')
        self.type_combo.grid(row=1, column=1, padx=5, pady=8, sticky=tk.EW)
        self.type_combo.set("credit")

        ttk.Label(form_grid, text="Amount (€):",
                  style='TLabel', background=self.controller.FRAME_COLOR).grid(row=1, column=2, padx=(15, 5), pady=8, sticky=tk.W)
        self.amount_entry = ttk.Entry(form_grid, width=15, style='TEntry')
        self.amount_entry.grid(row=1, column=3, padx=5, pady=8, sticky=tk.EW)

        ttk.Label(form_grid, text="Description:",
                  style='TLabel', background=self.controller.FRAME_COLOR).grid(row=2, column=0, padx=5, pady=8, sticky=tk.W)
        self.desc_entry = ttk.Entry(form_grid, style='TEntry')
        self.desc_entry.grid(row=2, column=1, columnspan=3, padx=5, pady=8, sticky=tk.EW)

        ttk.Button(form_grid, text="Add Transaction",
                   command=self.add_transaction, style='TButton').grid(row=3, column=0, columnspan=4,
                                                                       padx=5, pady=10, sticky=tk.E)

        filter_frame = ttk.Frame(self, style='Content.TFrame')
        filter_frame.pack(fill=tk.X, pady=(0, 10), padx=10)

        ttk.Label(filter_frame, text="Filter text:",
                  style='TLabel', background=self.controller.FRAME_COLOR).pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry = ttk.Entry(filter_frame, width=20, style='TEntry')
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<Return>", lambda e: self.refresh())

        self.filter_type_var = tk.StringVar(value="All")
        ttk.Label(filter_frame, text="Show:",
                  style='TLabel', background=self.controller.FRAME_COLOR).pack(side=tk.LEFT, padx=(15, 5))
        for label in ("All", "Sent", "Received"):
            ttk.Radiobutton(filter_frame, text=label, variable=self.filter_type_var,
                            value=label, command=self.refresh,
                            style='TRadiobutton').pack(side=tk.LEFT, padx=3)

        ttk.Button(filter_frame, text="Reset Filters",
                   command=self.reset_search, style='Secondary.TButton').pack(side=tk.LEFT, padx=10)

        self.balance_label = ttk.Label(filter_frame, text="Total Balance: --.-- €",
                                       style='Balance.TLabel', background=self.controller.FRAME_COLOR)
        self.balance_label.pack(side=tk.RIGHT, padx=10)

        table_container = ttk.Frame(self)
        table_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        cols = ("id", "date", "type", "direction", "counterparty", "description", "amount")
        self.table = ttk.Treeview(table_container, columns=cols, show="headings",
                                  selectmode="browse", style='Treeview')
        for col, heading in zip(cols,
                                ("ID", "Date", "Type", "Direction", "Counterparty", "Description", "Amount (€)")):
            self.table.heading(col, text=heading)

        self.table.column("id", width=40, stretch=tk.NO, anchor=tk.CENTER)
        self.table.column("date", width=100, anchor=tk.W)
        self.table.column("type", width=60, anchor=tk.CENTER)
        self.table.column("direction", width=70, anchor=tk.CENTER)
        self.table.column("counterparty", width=150, anchor=tk.W)
        self.table.column("description", width=250, anchor=tk.W)
        self.table.column("amount", width=100, anchor=tk.E)

        scrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL,
                                  command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Button(self, text="Remove Selected",
                   command=self.remove_transaction, style='Delete.TButton').pack(side=tk.RIGHT, pady=(0, 10), padx=10)

    def refresh(self) -> None:
        if not self.controller.user_id:
            self._clear_table()
            self.balance_label.config(text="Total Balance: --.-- €")
            return

        self.refresh_contacts()
        self._clear_table()

        search_term = self.search_entry.get().strip().lower()
        filter_type = self.filter_type_var.get()

        transactions = []

        if filter_type in ("All", "Sent"):
            sent_result = api_get_transactions(user_id=self.controller.user_id,
                                               as_sender=True, order="date_desc")
            if sent_result.get("success"):
                transactions.extend(sent_result["data"])
            else:
                messagebox.showerror("Error", f"Could not load sent transactions:\n{sent_result.get('error')}")

        if filter_type in ("All", "Received"):
            recv_result = api_get_transactions(user_id=self.controller.user_id,
                                               as_sender=False, order="date_desc")
            if recv_result.get("success"):
                transactions.extend(recv_result["data"])
            else:
                messagebox.showerror("Error", f"Could not load received transactions:\n{recv_result.get('error')}")

        if filter_type == "All":
            transactions.sort(key=lambda t: t.get('date', '0000-00-00'), reverse=True)

        if search_term:
            filtered = []
            for t in transactions:
                fields = [
                    str(t.get("id", "")),
                    t.get("date", ""),
                    t.get("type", ""),
                    t.get("description", ""),
                    str(t.get("amount", "")),
                    str(t.get("from_user_id", "")),
                    str(t.get("to_user_id", "")),
                ]
                if any(search_term in f.lower() for f in fields):
                    filtered.append(t)
            transactions = filtered

        contact_id_to_name = {cid: name for name, cid in self.contacts_map.items()}

        for t in transactions:
            is_sender = t.get("from_user_id") == self.controller.user_id
            direction = "Sent" if is_sender else "Received"
            counterparty_id = t.get("to_user_id") if is_sender else t.get("from_user_id")
            contact_id = t.get("contact_id")
            if contact_id and contact_id in contact_id_to_name:
                counterparty_display = contact_id_to_name[contact_id]
            else:
                counterparty_display = f"User #{counterparty_id}"
            amount = t.get("amount", 0.0)
            amount_str = f"{amount:.2f}"
            self.table.insert("", tk.END, values=(
                t.get("id", ""),
                t.get("date", ""),
                t.get("type", ""),
                direction,
                counterparty_display,
                t.get("description", ""),
                amount_str
            ))

        self.update_balance()

    def _clear_table(self) -> None:
        for row in self.table.get_children():
            self.table.delete(row)

    def refresh_contacts(self) -> None:
        if not self.controller.user_id:
            self.contact_combo['values'] = []
            self.contacts_map = {}
            return

        result = api_get_contacts(self.controller.user_id, order="name_asc")
        if result.get("success"):
            contacts = result["data"]
            self.contacts_map = {c['name']: c['id'] for c in contacts}
            self.contact_combo['values'] = list(self.contacts_map.keys())
            if contacts:
                self.contact_combo.current(0)
            else:
                self.contact_combo.set('')
        else:
            print(f"[GUI] Contact load error: {result.get('error')}")
            self.contact_combo['values'] = []
            self.contacts_map = {}

    def update_balance(self) -> None:
        if not self.controller.user_id:
            self.balance_label.config(text="Total Balance: --.-- €")
            return

        result = api_get_user_balance_breakdown(self.controller.user_id)
        if not result.get("success"):
            self.balance_label.config(text="Total Balance: Error", foreground=self.controller.ERROR_COLOR)
            return

        data = result.get("data", {})
        cr_recv = float(data.get("credits_received", 0))
        cr_sent = float(data.get("credits_sent", 0))
        db_sent = float(data.get("debits_sent", 0))
        db_recv = float(data.get("debits_received", 0))

        total = (cr_recv + cr_sent) - (db_sent + db_recv)
        color = self.controller.SUCCESS_COLOR if total >= 0 else self.controller.ERROR_COLOR
        self.balance_label.config(text=f"Total Balance: {total:.2f} €", foreground=color)

    def add_transaction(self) -> None:
        if not self.controller.user_id:
            messagebox.showerror("Error", "User not logged in.")
            return

        date = self.date_entry.get().strip()
        contact_name = self.contact_combo.get()
        trans_type = self.type_combo.get()
        amount_str = self.amount_entry.get().strip().replace(',', '.')
        desc = self.desc_entry.get().strip()

        if not (date and trans_type and amount_str and contact_name):
            messagebox.showerror("Error", "Date, Type, Amount, Contact are required.")
            return

        if not self._valid_date(date):
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD.")
            return

        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError("Amount must be positive.")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid amount: {e}")
            return

        contact_id = self.contacts_map.get(contact_name)
        if not contact_id:
            messagebox.showerror("Error", "Please select a valid contact.")
            return

        result = api_add_transaction(
            from_user_id=self.controller.user_id,
            type_=trans_type,
            amount=amount,
            date=date,
            description=desc,
            contact_id=contact_id,
            to_user_id=None  # auto-resolve
        )

        if result.get("success"):
            messagebox.showinfo("Success", "Transaction added.")
            self.amount_entry.delete(0, tk.END)
            self.desc_entry.delete(0, tk.END)
            self.refresh()
        else:
            messagebox.showerror("Add Error", result.get("error") or "Could not add transaction.")

    def remove_transaction(self) -> None:
        if not self.controller.user_id:
            messagebox.showerror("Error", "User not logged in.")
            return

        selected_items = self.table.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Select a transaction to remove.")
            return

        item_values = self.table.item(selected_items[0])['values']
        tx_id = item_values[0]
        direction = item_values[3]

        if not tx_id:
            messagebox.showerror("Error", "Cannot determine transaction ID.")
            return

        if direction != "Sent":
            messagebox.showerror("Error", "You can only remove transactions you have sent.")
            return

        if messagebox.askyesno("Confirm Removal", f"Remove transaction ID {tx_id}?"):
            from MoneyMate.data_layer.api import api_delete_transaction
            result = api_delete_transaction(transaction_id=tx_id, user_id=self.controller.user_id)
            if result.get("success"):
                deleted = result.get("data", {}).get("deleted", 0)
                if deleted > 0:
                    messagebox.showinfo("Success", "Transaction removed.")
                else:
                    messagebox.showwarning("Warning", "Transaction not found or not authorized.")
                self.refresh()
            else:
                messagebox.showerror("Removal Error", result.get("error") or "Could not remove transaction.")

    def reset_search(self) -> None:
        self.search_entry.delete(0, tk.END)
        self.filter_type_var.set("All")
        self.refresh()

    def _valid_date(self, date_str: str) -> bool:
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False