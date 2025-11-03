import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from MoneyMate.data_layer.api import (
    api_add_expense, api_get_expenses, api_delete_expense,
    api_update_expense, api_get_categories, api_search_expenses # Added for categories combobox and search
)
from datetime import datetime # For date validation

class ExpensesFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.categories_map = {} # Dictionary to map category name -> id

        # --- Layout ---
        top_frame = ttk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        mid_frame = ttk.Frame(self)
        mid_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        # --- Expense Entry Form (in top_frame) ---
        form = ttk.LabelFrame(top_frame, text="Add/Edit Expense", padding="10")
        form.pack(fill=tk.X)

        ttk.Label(form, text="Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.date_entry = ttk.Entry(form, width=12)
        self.date_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        # Pre-fill with today's date
        self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))


        ttk.Label(form, text="Description:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.desc_entry = ttk.Entry(form, width=30)
        self.desc_entry.grid(row=1, column=1, padx=5, pady=5, columnspan=3, sticky=tk.EW)

        ttk.Label(form, text="Amount (€):").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.amount_entry = ttk.Entry(form, width=10)
        self.amount_entry.grid(row=0, column=3, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(form, text="Category:").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.category_combo = ttk.Combobox(form, state="readonly", width=15)
        self.category_combo.grid(row=0, column=5, padx=5, pady=5, sticky=tk.EW)
        # Combobox will be populated in refresh_categories

        # Add/Update/Clear Buttons
        self.add_button = ttk.Button(form, text="Add", command=self.add_expense)
        self.add_button.grid(row=1, column=4, padx=5, pady=10, sticky=tk.E)

        self.update_button = ttk.Button(form, text="Save Changes", command=self.update_expense, state=tk.DISABLED)
        self.update_button.grid(row=1, column=5, padx=5, pady=10, sticky=tk.W)

        self.clear_button = ttk.Button(form, text="Clear Form", command=self.clear_form)
        self.clear_button.grid(row=1, column=6, padx=5, pady=10, sticky=tk.W)

        # Hidden ID for editing
        self.selected_expense_id = None

        # Configure column expansion in the form
        form.columnconfigure(1, weight=1) # Description expands
        form.columnconfigure(3, weight=0) # Amount fixed
        form.columnconfigure(5, weight=0) # Category fixed


        # --- Expenses Table (in mid_frame) ---
        cols = ("id", "date", "description", "category_name", "amount") # Added ID and Category Name
        self.table = ttk.Treeview(mid_frame, columns=cols, show="headings", selectmode="browse")

        self.table.heading("id", text="ID")
        self.table.heading("date", text="Date")
        self.table.heading("description", text="Description")
        self.table.heading("category_name", text="Category") # Show category name
        self.table.heading("amount", text="Amount (€)")

        # Hide ID column but make it accessible
        self.table.column("id", width=40, stretch=tk.NO, anchor=tk.CENTER)
        self.table.column("date", width=100, anchor=tk.CENTER)
        self.table.column("description", width=300)
        self.table.column("category_name", width=120, anchor=tk.W)
        self.table.column("amount", width=100, anchor=tk.E)


        # Scrollbar
        scrollbar = ttk.Scrollbar(mid_frame, orient=tk.VERTICAL, command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Row selection event
        self.table.bind("<<TreeviewSelect>>", self.on_row_select)

         # --- Filters and Total (in bottom_frame) ---
        filter_frame = ttk.Frame(bottom_frame)
        filter_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(filter_frame, text="Filter by text:").pack(side=tk.LEFT)
        self.search_entry = ttk.Entry(filter_frame, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<Return>", lambda e: self.refresh()) # Filter on Enter
        ttk.Button(filter_frame, text="Search", command=self.refresh).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="Reset", command=self.reset_search).pack(side=tk.LEFT)

        # Remove Button
        ttk.Button(bottom_frame, text="Remove Selected", command=self.remove_expense).pack(side=tk.LEFT, padx=20)

        # Total Label
        self.total_label = ttk.Label(bottom_frame, text="Total: 0.00 €", font=("Arial", 11, "bold"))
        self.total_label.pack(side=tk.RIGHT, padx=10)


    def refresh(self):
        """Load/reload expenses for the logged-in user."""
        if not self.controller.user_id:
            # Clear table if no user
            for row in self.table.get_children():
                self.table.delete(row)
            self.total_label.config(text="Total: 0.00 €")
            return

        # First, update available categories in the combobox
        self.refresh_categories()

        # Clear the table before repopulating
        for row in self.table.get_children():
            self.table.delete(row)

        search_term = self.search_entry.get().strip()
        total = 0.0

        # Call the API to get expenses
        # Note: Search is now done by the `search_expenses` API if `search_term` is present
        if search_term:
             result = api_search_expenses(query=search_term, user_id=self.controller.user_id)
        else:
             result = api_get_expenses(user_id=self.controller.user_id) # Default order date_desc

        if result["success"]:
            # Build category ID -> Name map for display
            category_id_to_name = {v: k for k, v in self.categories_map.items()}

            for expense in result["data"]:
                try:
                    amount = float(expense.get("price", 0))
                    total += amount
                    # Get category name from ID if possible, otherwise use legacy text
                    cat_id = expense.get("category_id")
                    category_name = category_id_to_name.get(cat_id, expense.get("category", "N/A")) # Fallback to legacy 'category' field

                    # Insert into table
                    self.table.insert("", tk.END, values=(
                        expense.get("id", ""),
                        expense.get("date", ""),
                        expense.get("title", ""),
                        category_name, # Show category name
                        f"{amount:.2f}" # Format amount
                    ))
                except (ValueError, TypeError) as e:
                    print(f"Error processing expense: {expense}, Error: {e}")
            self.total_label.config(text=f"Total: {total:.2f} €")
        else:
            messagebox.showerror("Error Loading Expenses", result["error"] or "Could not load expenses.")
            self.total_label.config(text="Total: Error €")

        self.clear_form() # Clear the form after refreshing

    def refresh_categories(self):
         """Update the list of categories in the combobox."""
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
                 self.category_combo.set(categories[0]['name']) # Pre-select the first one
             else:
                 self.category_combo.set('') # No categories
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
        category_name = self.category_combo.get() # Get selected name

        # Basic validation
        if not date or not desc or not amount_str or not category_name:
            messagebox.showerror("Error", "All fields (Date, Description, Amount, Category) are required.")
            return

        try:
            # Validate date format
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

        # Get category ID from name
        category_id = self.categories_map.get(category_name)
        if category_id is None:
             # If no ID (e.g., no categories defined), we might want
             # to pass None or handle differently. Use None for now.
             # The legacy text 'category' field is still required by add_expense API.
             print(f"Warning: Category '{category_name}' not found in ID map, passing name only.")

        # API Call
        result = api_add_expense(
            title=desc,
            price=amount,
            date=date,
            category=category_name, # Pass name as required legacy field
            user_id=self.controller.user_id,
            category_id=category_id # Pass ID if we have it
        )

        if result["success"]:
            messagebox.showinfo("Success", "Expense added successfully.")
            self.refresh() # Reload table
            self.clear_form() # Clear form fields
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

         # Validations (similar to add_expense)
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

         # API update call
         result = api_update_expense(
            expense_id=self.selected_expense_id,
            user_id=self.controller.user_id,
            title=desc,
            price=amount,
            date=date,
            category=category_name, # Also pass name for legacy field
            category_id=category_id
         )

         if result["success"]:
             messagebox.showinfo("Success", "Expense updated successfully.")
             self.refresh() # Reload table
             self.clear_form() # Clear and reset form state
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

        item_id = self.table.item(selected_items[0])['values'][0] # Get ID from the first column

        if not item_id:
             messagebox.showerror("Error", "Could not find the ID of the selected expense.")
             return

        if messagebox.askyesno("Confirm Removal", f"Are you sure you want to remove expense ID {item_id}?"):
            result = api_delete_expense(expense_id=item_id, user_id=self.controller.user_id)
            if result["success"]:
                messagebox.showinfo("Success", "Expense removed.")
                self.refresh() # Reload table
            else:
                messagebox.showerror("Removal Error", result["error"] or "Could not remove expense.")

    def on_row_select(self, event=None):
         """Populate the form when a row is selected."""
         selected_items = self.table.selection()
         if not selected_items:
             self.clear_form() # Deselected, clear form
             return

         item_values = self.table.item(selected_items[0])['values']
         expense_id, date, desc, cat_name, amount_str = item_values

         self.selected_expense_id = expense_id # Save ID for update

         # Clear and populate the form
         self.date_entry.delete(0, tk.END)
         self.date_entry.insert(0, date)
         self.desc_entry.delete(0, tk.END)
         self.desc_entry.insert(0, desc)
         self.amount_entry.delete(0, tk.END)
         self.amount_entry.insert(0, amount_str.replace(' €', '')) # Remove euro symbol

         # Select the category in the combobox
         if cat_name in self.category_combo['values']:
             self.category_combo.set(cat_name)
         elif cat_name == "N/A" and self.category_combo['values']:
              self.category_combo.set(self.category_combo['values'][0]) # Fallback to first if N/A
         else:
              self.category_combo.set('') # Category not found or no categories

         # Enable/Disable buttons
         self.update_button.config(state=tk.NORMAL)
         self.add_button.config(state=tk.DISABLED)

    def clear_form(self):
         """Clears the form fields and resets button states."""
         self.selected_expense_id = None
         self.date_entry.delete(0, tk.END)
         self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d')) # Reset to today's date
         self.desc_entry.delete(0, tk.END)
         self.amount_entry.delete(0, tk.END)
         if self.category_combo['values']:
             self.category_combo.set(self.category_combo['values'][0]) # Reset to first category
         else:
             self.category_combo.set('')

         self.table.selection_remove(self.table.selection()) # Deselect rows
         self.add_button.config(state=tk.NORMAL)
         self.update_button.config(state=tk.DISABLED)

    def reset_search(self):
         """Clears the search bar and reloads all expenses."""
         self.search_entry.delete(0, tk.END)
         self.refresh()