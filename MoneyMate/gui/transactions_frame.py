import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from MoneyMate.data_layer.api import (
    api_add_transaction, api_get_transactions, api_delete_transaction,
    api_get_contacts, api_get_contact_balance, api_get_user_net_balance
)
from datetime import datetime

class TransactionsFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style='Content.TFrame')
        self.controller = controller
        self.contacts_map = {} # Dictionary to map contact name -> id

        # --- Layout ---
        top_frame = ttk.LabelFrame(self, text="Add Transaction", style='TLabelframe')
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        bottom_frame = ttk.Frame(self, style='Content.TFrame')
        bottom_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Add Transaction Form (in top_frame) ---
        form_grid = ttk.Frame(top_frame, style='TLabelframe')
        form_grid.pack(fill=tk.X, padx=10, pady=10)
        
        form_grid.columnconfigure(1, weight=1)
        form_grid.columnconfigure(3, weight=1)

        # Row 0: Date and Contact
        ttk.Label(form_grid, text="Date (YYYY-MM-DD):", style='TLabel', background=self.controller.FRAME_COLOR).grid(row=0, column=0, padx=5, pady=8, sticky=tk.W)
        self.date_entry = ttk.Entry(form_grid, width=15, style='TEntry')
        self.date_entry.grid(row=0, column=1, padx=5, pady=8, sticky=tk.EW)
        self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))

        ttk.Label(form_grid, text="Contact:", style='TLabel', background=self.controller.FRAME_COLOR).grid(row=0, column=2, padx=(15, 5), pady=8, sticky=tk.W)
        self.contact_combo = ttk.Combobox(form_grid, state="readonly", style='TCombobox')
        self.contact_combo.grid(row=0, column=3, padx=5, pady=8, sticky=tk.EW)

        # Row 1: Type and Amount
        ttk.Label(form_grid, text="Type:", style='TLabel', background=self.controller.FRAME_COLOR).grid(row=1, column=0, padx=5, pady=8, sticky=tk.W)
        self.type_combo = ttk.Combobox(form_grid, values=["credit", "debit"], state="readonly", style='TCombobox')
        self.type_combo.grid(row=1, column=1, padx=5, pady=8, sticky=tk.EW)
        self.type_combo.set("credit")

        ttk.Label(form_grid, text="Amount (€):", style='TLabel', background=self.controller.FRAME_COLOR).grid(row=1, column=2, padx=(15, 5), pady=8, sticky=tk.W)
        self.amount_entry = ttk.Entry(form_grid, width=15, style='TEntry')
        self.amount_entry.grid(row=1, column=3, padx=5, pady=8, sticky=tk.EW)

        # Row 2: Description and Button
        ttk.Label(form_grid, text="Description:", style='TLabel', background=self.controller.FRAME_COLOR).grid(row=2, column=0, padx=5, pady=8, sticky=tk.W)
        self.desc_entry = ttk.Entry(form_grid, style='TEntry')
        self.desc_entry.grid(row=2, column=1, columnspan=3, padx=5, pady=8, sticky=tk.EW)

        add_button = ttk.Button(form_grid, text="Add Transaction", command=self.add_transaction, style='TButton')
        add_button.grid(row=3, column=0, columnspan=4, padx=5, pady=10, sticky=tk.E)

        # --- Filters, Balance, and Actions (in bottom_frame) ---
        filter_frame = ttk.Frame(bottom_frame, style='Content.TFrame')
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(filter_frame, text="Filter text:", style='TLabel', background=self.controller.FRAME_COLOR).pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry = ttk.Entry(filter_frame, width=20, style='TEntry')
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<Return>", lambda e: self.refresh())

        self.filter_type_var = tk.StringVar(value="All")
        ttk.Label(filter_frame, text="Show:", style='TLabel', background=self.controller.FRAME_COLOR).pack(side=tk.LEFT, padx=(15, 5))
        ttk.Radiobutton(filter_frame, text="All", variable=self.filter_type_var, value="All", command=self.refresh, style='TRadiobutton').pack(side=tk.LEFT, padx=3)
        ttk.Radiobutton(filter_frame, text="Sent", variable=self.filter_type_var, value="Sent", command=self.refresh, style='TRadiobutton').pack(side=tk.LEFT, padx=3)
        ttk.Radiobutton(filter_frame, text="Received", variable=self.filter_type_var, value="Received", command=self.refresh, style='TRadiobutton').pack(side=tk.LEFT, padx=3)
        ttk.Button(filter_frame, text="Reset Filters", command=self.reset_search, style='Secondary.TButton').pack(side=tk.LEFT, padx=10)

        self.balance_label = ttk.Label(filter_frame, text="Net Balance: --.-- €", style='Balance.TLabel', background=self.controller.FRAME_COLOR)
        self.balance_label.pack(side=tk.RIGHT, padx=10)

        # --- Transactions Table (in bottom_frame) ---
        table_container = ttk.Frame(bottom_frame)
        table_container.pack(fill=tk.BOTH, expand=True)

        cols = ("id", "date", "type", "direction", "counterparty", "description", "amount")
        self.table = ttk.Treeview(table_container, columns=cols, show="headings", selectmode="browse", style='Treeview')

        self.table.heading("id", text="ID")
        self.table.heading("date", text="Date")
        self.table.heading("type", text="Type")
        self.table.heading("direction", text="Direction")
        self.table.heading("counterparty", text="Counterparty")
        self.table.heading("description", text="Description")
        self.table.heading("amount", text="Amount (€)")

        self.table.column("id", width=40, stretch=tk.NO, anchor=tk.CENTER)
        self.table.column("date", width=100, anchor=tk.W)
        self.table.column("type", width=60, anchor=tk.CENTER)
        self.table.column("direction", width=70, anchor=tk.CENTER)
        self.table.column("counterparty", width=150, anchor=tk.W)
        self.table.column("description", width=250, anchor=tk.W)
        self.table.column("amount", width=100, anchor=tk.E)

        scrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Remove Button
        self.remove_button = ttk.Button(bottom_frame, text="Remove Selected", command=self.remove_transaction, style='Delete.TButton')
        self.remove_button.pack(side=tk.RIGHT, pady=(10, 0))


    def refresh(self):
        if not self.controller.user_id:
            for row in self.table.get_children():
                self.table.delete(row)
            self.balance_label.config(text="Net Balance: --.-- €")
            return

        self.refresh_contacts()

        for row in self.table.get_children():
            self.table.delete(row)

        search_term = self.search_entry.get().strip().lower()
        filter_type = self.filter_type_var.get()

        transactions_to_display = []

        if filter_type in ("All", "Sent"):
             result_sent = api_get_transactions(user_id=self.controller.user_id, as_sender=True, order="date_desc")
             if result_sent["success"]:
                 transactions_to_display.extend(result_sent["data"])
             else:
                 messagebox.showerror("Error", f"Could not load sent transactions: {result_sent['error']}")

        if filter_type in ("All", "Received"):
             result_received = api_get_transactions(user_id=self.controller.user_id, as_sender=False, order="date_desc")
             if result_received["success"]:
                 transactions_to_display.extend(result_received["data"])
             else:
                 messagebox.showerror("Error", f"Could not load received transactions: {result_received['error']}")

        if filter_type == "All":
             transactions_to_display.sort(key=lambda t: t.get('date', '0000-00-00'), reverse=True)


        if search_term:
             filtered_transactions = []
             for t in transactions_to_display:
                 search_in = [
                     str(t.get("id", "")),
                     t.get("date", ""),
                     t.get("type", ""),
                     str(t.get("from_user_id", "")),
                     str(t.get("to_user_id", "")),
                     t.get("description", ""),
                     str(t.get("amount", ""))
                 ]
                 if any(search_term in field.lower() for field in search_in):
                     filtered_transactions.append(t)
             transactions_to_display = filtered_transactions

        contact_id_to_name_map = {v: k for k, v in self.contacts_map.items()} 
        user_id_to_name_map = {self.controller.user_id: self.controller.username}
        
        for t in transactions_to_display:
            is_sender = t.get("from_user_id") == self.controller.user_id
            direction = "Sent" if is_sender else "Received"
            counterparty_id = t.get("to_user_id") if is_sender else t.get("from_user_id")

            counterparty_name = f"User ID: {counterparty_id}"
            contact_id_in_tx = t.get("contact_id")
            if is_sender and contact_id_in_tx:
                 found_name = next((name for name, cid in self.contacts_map.items() if cid == contact_id_in_tx), None)
                 if found_name:
                     counterparty_name = found_name
            
            amount = t.get("amount", 0.0)
            amount_str = f"{amount:.2f}"

            self.table.insert("", tk.END, values=(
                t.get("id", ""),
                t.get("date", ""),
                t.get("type", ""),
                direction,
                counterparty_name,
                t.get("description", ""),
                amount_str
            ))

        self.update_balance()

    def refresh_contacts(self):
         if not self.controller.user_id:
             self.contact_combo['values'] = []
             self.contacts_map = {}
             return

         result = api_get_contacts(self.controller.user_id, order="name_asc")
         if result["success"]:
             contacts = result["data"]
             self.contacts_map = {c['name']: c['id'] for c in contacts}
             self.contact_combo['values'] = list(self.contacts_map.keys())
             if contacts:
                 self.contact_combo.current(0)
             else:
                 self.contact_combo.set('')
         else:
             print(f"Error loading contacts: {result['error']}")
             self.contact_combo['values'] = []
             self.contacts_map = {}

    def update_balance(self):
         if not self.controller.user_id:
             self.balance_label.config(text="Net Balance: --.-- €")
             return

         result = api_get_user_net_balance(self.controller.user_id)
         if result["success"]:
             balance = result["data"]
             color = self.controller.SUCCESS_COLOR if balance >= 0 else self.controller.ERROR_COLOR
             self.balance_label.config(text=f"Net Balance: {balance:.2f} €", foreground=color)
         else:
             self.balance_label.config(text="Net Balance: Error €", foreground=self.controller.ERROR_COLOR)

    def add_transaction(self):
        if not self.controller.user_id:
            messagebox.showerror("Error", "User not logged in.")
            return

        date = self.date_entry.get().strip()
        contact_name = self.contact_combo.get()
        trans_type = self.type_combo.get()
        amount_str = self.amount_entry.get().strip().replace(',', '.')
        desc = self.desc_entry.get().strip()

        if not date or not contact_name or not trans_type or not amount_str:
            messagebox.showerror("Error", "All fields (Date, Contact, Type, Amount) are required.")
            return
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
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
        if contact_id is None:
            messagebox.showerror("Error", f"Contact '{contact_name}' not found.")
            return

        try:
            to_user_id_str = simpledialog.askstring("Recipient User ID",
                                                   f"Enter the numeric User ID for '{contact_name}':\n(This is a temporary step)",
                                                   parent=self)
            if to_user_id_str is None: return
            to_user_id = int(to_user_id_str)
            if to_user_id == self.controller.user_id:
                 messagebox.showerror("Error", "You cannot send a transaction to yourself.")
                 return
        except (ValueError, TypeError):
             messagebox.showerror("Error", "Invalid user ID.")
             return
        
        result = api_add_transaction(
            from_user_id=self.controller.user_id,
            to_user_id=to_user_id,
            type_=trans_type,
            amount=amount,
            date=date,
            description=desc,
            contact_id=contact_id
        )

        if result["success"]:
            messagebox.showinfo("Success", "Transaction added.")
            self.refresh()
            self.amount_entry.delete(0, tk.END)
            self.desc_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error Adding Transaction", result["error"] or "Could not add transaction.")

    def remove_transaction(self):
        if not self.controller.user_id:
            messagebox.showerror("Error", "User not logged in.")
            return

        selected_items = self.table.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Select a transaction to remove.")
            return

        item_values = self.table.item(selected_items[0])['values']
        item_id = item_values[0]
        direction = item_values[3]

        if not item_id:
             messagebox.showerror("Error", "Could not find the ID of the selected transaction.")
             return

        if direction != "Sent":
             messagebox.showerror("Error", "You can only remove transactions you have sent.")
             return

        if messagebox.askyesno("Confirm Removal", f"Are you sure you want to remove transaction ID {item_id}?"):
            result = api_delete_transaction(transaction_id=item_id, user_id=self.controller.user_id)
            if result["success"]:
                 deleted_count = result.get("data", {}).get("deleted", 0)
                 if deleted_count > 0:
                     messagebox.showinfo("Success", "Transaction removed.")
                 else:
                     messagebox.showwarning("Warning", "Transaction not found or you are not authorized.")
                 self.refresh()
            else:
                messagebox.showerror("Error Removing Transaction", result["error"] or "Could not remove transaction.")

    def reset_search(self):
         self.search_entry.delete(0, tk.END)
         self.filter_type_var.set("All")
         self.refresh()