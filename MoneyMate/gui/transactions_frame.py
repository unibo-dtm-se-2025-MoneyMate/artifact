import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from MoneyMate.data_layer.api import (
    api_add_transaction, api_get_transactions, api_delete_transaction,
    api_get_contacts, api_get_contact_balance, api_get_user_net_balance
)
from datetime import datetime

class TransactionsFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.contacts_map = {} # Dictionary to map contact name -> id

        # --- Layout ---
        top_frame = ttk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        mid_frame = ttk.Frame(self)
        mid_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        # --- Add Transaction Form (in top_frame) ---
        form = ttk.LabelFrame(top_frame, text="Add Transaction", padding="10")
        form.pack(fill=tk.X)

        ttk.Label(form, text="Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.date_entry = ttk.Entry(form, width=12)
        self.date_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))

        ttk.Label(form, text="Contact:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.contact_combo = ttk.Combobox(form, state="readonly", width=20)
        self.contact_combo.grid(row=0, column=3, padx=5, pady=5, sticky=tk.EW)
        # Will be populated in refresh_contacts

        ttk.Label(form, text="Type:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.type_combo = ttk.Combobox(form, values=["credit", "debit"], state="readonly", width=8)
        self.type_combo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        self.type_combo.set("credit") # Default

        ttk.Label(form, text="Amount (€):").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.amount_entry = ttk.Entry(form, width=10)
        self.amount_entry.grid(row=1, column=3, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(form, text="Description:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.desc_entry = ttk.Entry(form, width=40)
        self.desc_entry.grid(row=2, column=1, padx=5, pady=5, columnspan=3, sticky=tk.EW)


        add_button = ttk.Button(form, text="Add", command=self.add_transaction)
        add_button.grid(row=2, column=4, padx=15, pady=5, sticky=tk.E)

        form.columnconfigure(1, weight=0)
        form.columnconfigure(3, weight=1) # Expand contact and description fields

        # --- Transactions Table (in mid_frame) ---
        cols = ("id", "date", "type", "direction", "counterparty", "description", "amount")
        self.table = ttk.Treeview(mid_frame, columns=cols, show="headings", selectmode="browse")

        self.table.heading("id", text="ID")
        self.table.heading("date", text="Date")
        self.table.heading("type", text="Type")
        self.table.heading("direction", text="Direction") # "Sent" or "Received"
        self.table.heading("counterparty", text="Counterparty") # User Name
        self.table.heading("description", text="Description")
        self.table.heading("amount", text="Amount (€)")

        self.table.column("id", width=40, stretch=tk.NO, anchor=tk.CENTER)
        self.table.column("date", width=100, anchor=tk.CENTER)
        self.table.column("type", width=60, anchor=tk.CENTER)
        self.table.column("direction", width=70, anchor=tk.CENTER)
        self.table.column("counterparty", width=150)
        self.table.column("description", width=250)
        self.table.column("amount", width=100, anchor=tk.E)

        # Scrollbar
        scrollbar = ttk.Scrollbar(mid_frame, orient=tk.VERTICAL, command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Event (currently unused for edit, only delete)
        # self.table.bind("<<TreeviewSelect>>", self.on_row_select)

         # --- Filters, Balance, and Actions (in bottom_frame) ---
        filter_frame = ttk.Frame(bottom_frame)
        filter_frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        ttk.Label(filter_frame, text="Filter text:").grid(row=0, column=0, padx=2, pady=2)
        self.search_entry = ttk.Entry(filter_frame, width=20)
        self.search_entry.grid(row=0, column=1, padx=2, pady=2)
        self.search_entry.bind("<Return>", lambda e: self.refresh())

        self.filter_type_var = tk.StringVar(value="All")
        ttk.Label(filter_frame, text="Show:").grid(row=0, column=2, padx=5, pady=2)
        ttk.Radiobutton(filter_frame, text="All", variable=self.filter_type_var, value="All", command=self.refresh).grid(row=0, column=3)
        ttk.Radiobutton(filter_frame, text="Sent", variable=self.filter_type_var, value="Sent", command=self.refresh).grid(row=0, column=4)
        ttk.Radiobutton(filter_frame, text="Received", variable=self.filter_type_var, value="Received", command=self.refresh).grid(row=0, column=5)
        ttk.Button(filter_frame, text="Reset Filters", command=self.reset_search).grid(row=0, column=6, padx=10)

        # User Balance
        self.balance_label = ttk.Label(bottom_frame, text="Net Balance: --.-- €", font=("Arial", 11, "bold"))
        self.balance_label.pack(side=tk.LEFT, padx=20)

        # Remove Button (active only on SENT transactions)
        self.remove_button = ttk.Button(bottom_frame, text="Remove Selected", command=self.remove_transaction)
        self.remove_button.pack(side=tk.RIGHT, padx=10)


    def refresh(self):
        """Load/Reload transactions and contacts."""
        if not self.controller.user_id:
            for row in self.table.get_children():
                self.table.delete(row)
            self.balance_label.config(text="Net Balance: --.-- €")
            return

        # 1. Update contacts combobox
        self.refresh_contacts()

        # 2. Clear table
        for row in self.table.get_children():
            self.table.delete(row)

        # 3. Determine filters
        search_term = self.search_entry.get().strip().lower()
        filter_type = self.filter_type_var.get() # All, Sent, Received

        transactions_to_display = []

        # 4. Get transactions (sent and/or received)
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

        # Sort by date (most recent first) if we merged sent and received
        if filter_type == "All":
             transactions_to_display.sort(key=lambda t: t.get('date', '0000-00-00'), reverse=True)


        # 5. Filter by text (client-side, API doesn't have text search for transactions)
        if search_term:
             filtered_transactions = []
             for t in transactions_to_display:
                 # Search in description, type, amount, date, counterparty ID (if available)
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


        # 6. Populate table
        #    We need a way to map user_id -> username for the "Counterparty" column.
        #    For now, just show the user ID. A better solution would require an
        #    `api_get_user_info(user_id)` API or for `api_get_transactions` to return names.
        contact_id_to_name_map = {v: k for k, v in self.contacts_map.items()} # Inverse map for ID->Name
        # Add current user to map for self-reference if needed (though API prevents self-transactions)
        user_id_to_name_map = {self.controller.user_id: self.controller.username}
        # In a real app, you'd fetch usernames for counterparty_ids here.

        for t in transactions_to_display:
            is_sender = t.get("from_user_id") == self.controller.user_id
            direction = "Sent" if is_sender else "Received"
            counterparty_id = t.get("to_user_id") if is_sender else t.get("from_user_id")

            # Try to find the contact name associated with the counterparty ID
            # This is an approximation: ideally the API should provide names,
            # or we'd have a way to ask `get_username_by_id`.
            # We use the contacts map IF the ID corresponds to a known contact.
            counterparty_name = f"User ID: {counterparty_id}" # Default to ID
            contact_id_in_tx = t.get("contact_id")
            if is_sender and contact_id_in_tx:
                 # If sent and contact_id exists, look in contacts map
                 found_name = next((name for name, cid in self.contacts_map.items() if cid == contact_id_in_tx), None)
                 if found_name:
                     counterparty_name = found_name
            # If received, we don't have a direct contact link in the simple model
            # A more complex model might link transactions to contacts from both sides
            # or require fetching the sender's username via API.


            amount = t.get("amount", 0.0)
            amount_str = f"{amount:.2f}"

            self.table.insert("", tk.END, values=(
                t.get("id", ""),
                t.get("date", ""),
                t.get("type", ""),
                direction,
                counterparty_name, # Show name if found, else ID
                t.get("description", ""),
                amount_str
            ))

        # 7. Update net balance
        self.update_balance()

    def refresh_contacts(self):
         """Update the contacts combobox."""
         if not self.controller.user_id:
             self.contact_combo['values'] = []
             self.contacts_map = {}
             return

         result = api_get_contacts(self.controller.user_id, order="name_asc")
         if result["success"]:
             contacts = result["data"]
             # Map Contact Name -> Contact ID
             self.contacts_map = {c['name']: c['id'] for c in contacts}
             self.contact_combo['values'] = list(self.contacts_map.keys())
             if contacts:
                 self.contact_combo.current(0) # Select the first one
             else:
                 self.contact_combo.set('')
         else:
             print(f"Error loading contacts: {result['error']}")
             self.contact_combo['values'] = []
             self.contacts_map = {}

    def update_balance(self):
         """Update the net balance label."""
         if not self.controller.user_id:
             self.balance_label.config(text="Net Balance: --.-- €")
             return

         result = api_get_user_net_balance(self.controller.user_id)
         if result["success"]:
             balance = result["data"]
             self.balance_label.config(text=f"Net Balance: {balance:.2f} €")
         else:
             self.balance_label.config(text="Net Balance: Error €")

    def add_transaction(self):
        if not self.controller.user_id:
            messagebox.showerror("Error", "User not logged in.")
            return

        date = self.date_entry.get().strip()
        contact_name = self.contact_combo.get()
        trans_type = self.type_combo.get()
        amount_str = self.amount_entry.get().strip().replace(',', '.')
        desc = self.desc_entry.get().strip()

        # Validations
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

        # Determine to_user_id: This is a simplification!
        # The `add_transaction` API requires `to_user_id`. We don't have a way to know this
        # just from the contact name. Assume (WRONGLY) that the contact represents
        # another user. A way to associate contacts with user_ids is needed.
        # ---- TEMPORARY WORKAROUND: Ask for recipient user ID ---
        # This is bad UX, but necessary given the API
        try:
            to_user_id_str = simpledialog.askstring("Recipient User ID",
                                                   f"Enter the numeric User ID for '{contact_name}':",
                                                   parent=self)
            if to_user_id_str is None: return # Cancelled
            to_user_id = int(to_user_id_str)
            if to_user_id == self.controller.user_id:
                 messagebox.showerror("Error", "You cannot send a transaction to yourself.")
                 return
        except (ValueError, TypeError):
             messagebox.showerror("Error", "Invalid user ID.")
             return
        # ---- END TEMPORARY WORKAROUND ---

        # API Call
        result = api_add_transaction(
            from_user_id=self.controller.user_id,
            to_user_id=to_user_id, # Use the entered ID
            type_=trans_type,
            amount=amount,
            date=date,
            description=desc,
            contact_id=contact_id # Associate with the selected contact
        )

        if result["success"]:
            messagebox.showinfo("Success", "Transaction added.")
            self.refresh()
            # Partially clear form (keep date and type)
            self.contact_combo.set('')
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
        direction = item_values[3] # "Sent" or "Received"

        if not item_id:
             messagebox.showerror("Error", "Could not find the ID of the selected transaction.")
             return

        # IMPORTANT: Only allow deletion if the transaction was SENT by the current user
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
                 self.refresh() # Reload
            else:
                messagebox.showerror("Error Removing Transaction", result["error"] or "Could not remove transaction.")

    def reset_search(self):
         """Clears filters and reloads."""
         self.search_entry.delete(0, tk.END)
         self.filter_type_var.set("All")
         self.refresh()