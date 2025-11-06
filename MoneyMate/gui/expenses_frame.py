import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from MoneyMate.data_layer.api import (
    api_add_expense, api_get_expenses, api_delete_expense,
    api_update_expense, api_get_categories, api_search_expenses
)
from datetime import datetime

class ExpensesFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style='Content.TFrame')
        self.controller = controller
        self.categories_map = {} # Dictionary to map category name -> id

        # --- Layout ---
        # Top frame for the form
        top_frame = ttk.LabelFrame(self, text="Manage Expenses", style='TLabelframe')
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # Bottom frame for the table and actions
        bottom_frame = ttk.Frame(self, style='Content.TFrame')
        bottom_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Expense Entry Form (in top_frame) ---
        form_grid = ttk.Frame(top_frame, style='TLabelframe')
        form_grid.pack(fill=tk.X, expand=True, padx=10, pady=10)

        # Configure grid columns
        form_grid.columnconfigure(1, weight=1)
        form_grid.columnconfigure(3, weight=1)

        # Row 0: Date and Amount
        ttk.Label(form_grid, text="Date (YYYY-MM-DD):", style='TLabel', background=self.controller.FRAME_COLOR).grid(row=0, column=0, padx=5, pady=8, sticky=tk.W)
        self.date_entry = ttk.Entry(form_grid, width=15, style='TEntry')
        self.date_entry.grid(row=0, column=1, padx=5, pady=8, sticky=tk.EW)
        self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))

        ttk.Label(form_grid, text="Amount (€):", style='TLabel', background=self.controller.FRAME_COLOR).grid(row=0, column=2, padx=(15, 5), pady=8, sticky=tk.W)
        self.amount_entry = ttk.Entry(form_grid, width=15, style='TEntry')
        self.amount_entry.grid(row=0, column=3, padx=5, pady=8, sticky=tk.EW)

        # Row 1: Category and Description
        ttk.Label(form_grid, text="Category:", style='TLabel', background=self.controller.FRAME_COLOR).grid(row=1, column=0, padx=5, pady=8, sticky=tk.W)
        self.category_combo = ttk.Combobox(form_grid, state="readonly", style='TCombobox', width=15)
        self.category_combo.grid(row=1, column=1, padx=5, pady=8, sticky=tk.EW)

        ttk.Label(form_grid, text="Description:", style='TLabel', background=self.controller.FRAME_COLOR).grid(row=1, column=2, padx=(15, 5), pady=8, sticky=tk.W)
        self.desc_entry = ttk.Entry(form_grid, style='TEntry')
        self.desc_entry.grid(row=1, column=3, padx=5, pady=8, sticky=tk.EW)

        # Row 2: Buttons
        button_frame = ttk.Frame(form_grid, style='TLabelframe')
        button_frame.grid(row=2, column=0, columnspan=4, pady=10, sticky=tk.E)
        
        self.add_button = ttk.Button(button_frame, text="Add Expense", command=self.add_expense, style='TButton')
        self.add_button.pack(side=tk.LEFT, padx=5)

        self.update_button = ttk.Button(button_frame, text="Save Changes", command=self.update_expense, state=tk.DISABLED, style='TButton')
        self.update_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = ttk.Button(button_frame, text="Clear Form", command=self.clear_form, style='Secondary.TButton')
        self.clear_button.pack(side=tk.LEFT, padx=5)

        # Hidden ID for editing
        self.selected_expense_id = None

        # --- Filters and Total (in bottom_frame, top part) ---
        actions_frame = ttk.Frame(bottom_frame, style='Content.TFrame')
        actions_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(actions_frame, text="Filter:", style='TLabel', background=self.controller.FRAME_COLOR).pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry = ttk.Entry(actions_frame, width=25, style='TEntry')
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<Return>", lambda e: self.refresh())
        
        ttk.Button(actions_frame, text="Search", command=self.refresh, style='Secondary.TButton', width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(actions_frame, text="Reset", command=self.reset_search, style='Secondary.TButton', width=10).pack(side=tk.LEFT, padx=2)

        self.total_label = ttk.Label(actions_frame, text="Total: 0.00 €", style='Total.TLabel', background=self.controller.FRAME_COLOR)
        self.total_label.pack(side=tk.RIGHT, padx=10)
        
        # --- Expenses Table (in bottom_frame, middle part) ---
        table_container = ttk.Frame(bottom_frame)
        table_container.pack(fill=tk.BOTH, expand=True)

        cols = ("id", "date", "description", "category_name", "amount")
        self.table = ttk.Treeview(table_container, columns=cols, show="headings", selectmode="browse", style='Treeview')

        self.table.heading("id", text="ID")
        self.table.heading("date", text="Date")
        self.table.heading("description", text="Description")
        self.table.heading("category_name", text="Category")
        self.table.heading("amount", text="Amount (€)")

        self.table.column("id", width=50, stretch=tk.NO, anchor=tk.CENTER)
        self.table.column("date", width=100, anchor=tk.W)
        self.table.column("description", width=300, anchor=tk.W)
        self.table.column("category_name", width=120, anchor=tk.W)
        self.table.column("amount", width=100, anchor=tk.E)

        scrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.table.bind("<<TreeviewSelect>>", self.on_row_select)
        
        # --- Delete Button (in bottom_frame, bottom part) ---
        ttk.Button(bottom_frame, text="Remove Selected Expense", command=self.remove_expense, style='Delete.TButton').pack(side=tk.RIGHT, pady=(10, 0))


    def refresh(self):
        if not self.controller.user_id:
            for row in self.table.get_children():
                self.table.delete(row)
            self.total_label.config(text="Total: 0.00 €")
            return

        self.refresh_categories()

        for row in self.table.get_children():
            self.table.delete(row)

        search_term = self.search_entry.get().strip()
        total = 0.0

        if search_term:
             result = api_search_expenses(query=search_term, user_id=self.controller.user_id)
        else:
             result = api_get_expenses(user_id=self.controller.user_id)

        if result["success"]:
            category_id_to_name = {v: k for k, v in self.categories_map.items()}

            for expense in result["data"]:
                try:
                    amount = float(expense.get("price", 0))
                    total += amount
                    cat_id = expense.get("category_id")
                    category_name = category_id_to_name.get(cat_id, expense.get("category", "N/A"))

                    self.table.insert("", tk.END, values=(
                        expense.get("id", ""),
                        expense.get("date", ""),
                        expense.get("title", ""),
                        category_name,
                        f"{amount:.2f}"
                    ))
                except (ValueError, TypeError) as e:
                    print(f"Error processing expense: {expense}, Error: {e}")
            self.total_label.config(text=f"Total: {total:.2f} €")
        else:
            messagebox.showerror("Error Loading Expenses", result["error"] or "Could not load expenses.")
            self.total_label.config(text="Total: Error €")

        self.clear_form()

    def refresh_categories(self):
         if not self.controller.user_id:
             self.category_combo['values'] = []
             self.categories_map = {}
             return

         result = api_get_categories(self.controller.user_id, order="name_asc")
         if result["success"]:
             categories = result["data"]
             self.categories_map = {cat['name']: cat['id'] for cat in categories}
             self.category_combo['values'] = list(self.categories_map.keys())
             if categories:
                 self.category_combo.set(categories[0]['name'])
             else:
                 self.category_combo.set('')
         else:
             print(f"Error loading categories: {result['error']}")
             self.category_combo['values'] = []
             self.categories_map = {}


    def add_expense(self):
        if not self.controller.user_id:
            messagebox.showerror("Error", "User not logged in.")
            return

        date = self.date_entry.get().strip()
        desc = self.desc_entry.get().strip()
        amount_str = self.amount_entry.get().strip().replace(',', '.')
        category_name = self.category_combo.get()

        if not date or not desc or not amount_str or not category_name:
            messagebox.showerror("Error", "All fields (Date, Description, Amount, Category) are required.")
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

        category_id = self.categories_map.get(category_name)
        
        result = api_add_expense(
            title=desc,
            price=amount,
            date=date,
            category=category_name,
            user_id=self.controller.user_id,
            category_id=category_id
        )

        if result["success"]:
            messagebox.showinfo("Success", "Expense added successfully.")
            self.refresh()
            self.clear_form()
        else:
            messagebox.showerror("Add Error", result["error"] or "Could not add expense.")

    def update_expense(self):
         if not self.controller.user_id or self.selected_expense_id is None:
            messagebox.showerror("Error", "No expense selected for editing or user not logged in.")
            return

         date = self.date_entry.get().strip()
         desc = self.desc_entry.get().strip()
         amount_str = self.amount_entry.get().strip().replace(',', '.')
         category_name = self.category_combo.get()

         if not date or not desc or not amount_str or not category_name:
            messagebox.showerror("Error", "All fields are required for editing.")
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

         category_id = self.categories_map.get(category_name)

         result = api_update_expense(
            expense_id=self.selected_expense_id,
            user_id=self.controller.user_id,
            title=desc,
            price=amount,
            date=date,
            category=category_name,
            category_id=category_id
         )

         if result["success"]:
             messagebox.showinfo("Success", "Expense updated successfully.")
             self.refresh()
             self.clear_form()
         else:
             messagebox.showerror("Update Error", result["error"] or "Could not update expense.")


    def remove_expense(self):
        if not self.controller.user_id:
            messagebox.showerror("Error", "User not logged in.")
            return

        selected_items = self.table.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Select an expense to remove.")
            return

        item_id = self.table.item(selected_items[0])['values'][0]

        if not item_id:
             messagebox.showerror("Error", "Could not find the ID of the selected expense.")
             return

        if messagebox.askyesno("Confirm Removal", f"Are you sure you want to remove expense ID {item_id}?"):
            result = api_delete_expense(expense_id=item_id, user_id=self.controller.user_id)
            if result["success"]:
                messagebox.showinfo("Success", "Expense removed.")
                self.refresh()
            else:
                messagebox.showerror("Removal Error", result["error"] or "Could not remove expense.")

    def on_row_select(self, event=None):
         selected_items = self.table.selection()
         if not selected_items:
             self.clear_form()
             return

         item_values = self.table.item(selected_items[0])['values']
         expense_id, date, desc, cat_name, amount_str = item_values

         self.selected_expense_id = expense_id

         self.date_entry.delete(0, tk.END)
         self.date_entry.insert(0, date)
         self.desc_entry.delete(0, tk.END)
         self.desc_entry.insert(0, desc)
         self.amount_entry.delete(0, tk.END)
         self.amount_entry.insert(0, amount_str.replace(' €', ''))

         if cat_name in self.category_combo['values']:
             self.category_combo.set(cat_name)
         elif cat_name == "N/A" and self.category_combo['values']:
              self.category_combo.set(self.category_combo['values'][0])
         else:
              self.category_combo.set('')

         self.update_button.config(state=tk.NORMAL)
         self.add_button.config(state=tk.DISABLED)

    def clear_form(self):
         self.selected_expense_id = None
         self.date_entry.delete(0, tk.END)
         self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
         self.desc_entry.delete(0, tk.END)
         self.amount_entry.delete(0, tk.END)
         if self.category_combo['values']:
             self.category_combo.set(self.category_combo['values'][0])
         else:
             self.category_combo.set('')

         self.table.selection_remove(self.table.selection())
         self.add_button.config(state=tk.NORMAL)
         self.update_button.config(state=tk.DISABLED)

    def reset_search(self):
         self.search_entry.delete(0, tk.END)
         self.refresh()