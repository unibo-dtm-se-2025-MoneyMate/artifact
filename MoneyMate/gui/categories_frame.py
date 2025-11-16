"""
Tkinter frame for managing expense categories in the GUI.

Responsibilities:
- Display a form for adding new categories (name + optional description).
- Show the current user's categories in a Treeview table.
- Allow removal of the selected category without affecting existing expenses.
- Interact with the data layer via api_add_category, api_get_categories,
  and api_delete_category.

The frame is plugged into MoneyMateGUI and refreshed per logged-in user.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from MoneyMate.data_layer.api import api_add_category, api_get_categories, api_delete_category

class CategoriesFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style='Content.TFrame')
        self.controller = controller

        # --- Layout ---
        top_frame = ttk.LabelFrame(self, text="Manage Categories", style='TLabelframe')
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        bottom_frame = ttk.Frame(self, style='Content.TFrame')
        bottom_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Add Category Form (in top_frame) ---
        form_grid = ttk.Frame(top_frame, style='TLabelframe')
        form_grid.pack(fill=tk.X, padx=10, pady=10)

        form_grid.columnconfigure(1, weight=1)

        # Row 0: Name
        ttk.Label(form_grid, text="Name:", style='TLabel', background=controller.FRAME_COLOR).grid(row=0, column=0, padx=5, pady=8, sticky=tk.W)
        self.name_entry = ttk.Entry(form_grid, style='TEntry')
        self.name_entry.grid(row=0, column=1, padx=5, pady=8, sticky=tk.EW)
        
        # Row 1: Description
        ttk.Label(form_grid, text="Description:", style='TLabel', background=controller.FRAME_COLOR).grid(row=1, column=0, padx=5, pady=8, sticky=tk.W)
        self.desc_entry = ttk.Entry(form_grid, style='TEntry')
        self.desc_entry.grid(row=1, column=1, padx=5, pady=8, sticky=tk.EW)
        
        # Row 2: Button
        add_button = ttk.Button(form_grid, text="Add Category", command=self.add_category, style='TButton')
        add_button.grid(row=2, column=0, columnspan=2, padx=5, pady=10, sticky=tk.E)

        # --- Categories Table (in bottom_frame) ---
        table_container = ttk.Frame(bottom_frame)
        table_container.pack(fill=tk.BOTH, expand=True)
        
        cols = ("id", "name", "description")
        self.table = ttk.Treeview(table_container, columns=cols, show="headings", selectmode="browse", style='Treeview')

        self.table.heading("id", text="ID")
        self.table.heading("name", text="Name")
        self.table.heading("description", text="Description")

        self.table.column("id", width=50, stretch=tk.NO, anchor=tk.CENTER)
        self.table.column("name", width=150, anchor=tk.W)
        self.table.column("description", width=250, anchor=tk.W)

        scrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- Actions (in bottom_frame, bottom) ---
        ttk.Button(bottom_frame, text="Remove Selected", command=self.remove_category, style='Delete.TButton').pack(side=tk.RIGHT, pady=(10, 0))


    def refresh(self):
        """Load/Reload categories for the logged-in user."""
        if not self.controller.user_id:
            for row in self.table.get_children():
                self.table.delete(row)
            return

        for row in self.table.get_children():
            self.table.delete(row)

        result = api_get_categories(user_id=self.controller.user_id, order="name_asc")

        if result["success"]:
            categories = result["data"]
            for cat in categories:
                self.table.insert("", tk.END, values=(
                    cat.get("id", ""),
                    cat.get("name", "N/A"),
                    cat.get("description", "")
                ))
        else:
            messagebox.showerror("Error Loading Categories", result["error"] or "Could not load categories.")
        
        self.clear_form()

    def add_category(self):
        """Add a new category using data from the form."""
        if not self.controller.user_id:
            messagebox.showerror("Error", "User not logged in.")
            return

        name = self.name_entry.get().strip()
        desc = self.desc_entry.get().strip()

        if not name:
            messagebox.showerror("Error", "Category name is required.")
            return

        result = api_add_category(
            user_id=self.controller.user_id,
            name=name,
            description=desc if desc else None
        )

        if result["success"]:
            messagebox.showinfo("Success", f"Category '{name}' added.")
            self.refresh()
        else:
            messagebox.showerror("Error Adding Category", result["error"] or "Could not add category.")
    
    def clear_form(self):
        """Clears the form fields and deselects from table."""
        self.name_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.table.selection_remove(self.table.selection())

    def remove_category(self):
        """Removes the selected category."""
        if not self.controller.user_id:
            messagebox.showerror("Error", "User not logged in.")
            return

        selected_items = self.table.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Select a category to remove.")
            return

        item_values = self.table.item(selected_items[0])['values']
        item_id = item_values[0]
        item_name = item_values[1]

        if not item_id:
             messagebox.showerror("Error", "Could not find the ID of the selected category.")
             return

        if messagebox.askyesno("Confirm Removal", f"Are you sure you want to remove category '{item_name}' (ID: {item_id})?\n\n(This will not affect existing expenses.)"):
            result = api_delete_category(category_id=item_id, user_id=self.controller.user_id)
            if result["success"]:
                 deleted_count = result.get("data", {}).get("deleted", 0)
                 if deleted_count > 0:
                     messagebox.showinfo("Success", "Category removed.")
                 else:
                     messagebox.showwarning("Warning", "Category not found or does not belong to the user.")
                 self.refresh()
            else:
                messagebox.showerror("Error Removing Category", result["error"] or "Could not remove category.")