"""
Tkinter frame for managing contacts within the MoneyMate GUI.

Features:
- Simple form to add per-user contacts (names only).
- Search box to filter contacts by name.
- Treeview listing of all contacts for the logged-in user.
- Removal of selected contacts, with feedback on ownership and existence.

All operations are performed through the data-layer API
(api_add_contact, api_get_contacts, api_delete_contact).
"""

import tkinter as tk
from tkinter import ttk, messagebox
from MoneyMate.data_layer.api import api_add_contact, api_get_contacts, api_delete_contact

class ContactsFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style='Content.TFrame')
        self.controller = controller

        # --- Layout ---
        # Top frame for the form
        top_frame = ttk.LabelFrame(self, text="Manage Contacts", style='TLabelframe')
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # Bottom frame for the table and actions
        bottom_frame = ttk.Frame(self, style='Content.TFrame')
        bottom_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Add Contact Form (in top_frame) ---
        form = ttk.Frame(top_frame, style='TLabelframe')
        form.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(form, text="Name:", style='TLabel', background=self.controller.FRAME_COLOR).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.name_entry = ttk.Entry(form, width=40, style='TEntry')
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        add_button = ttk.Button(form, text="Add Contact", command=self.add_contact, style='TButton')
        add_button.grid(row=0, column=2, padx=15, pady=5)

        form.columnconfigure(1, weight=1) # Expand name field

        # --- Filters (in bottom_frame, top) ---
        filter_frame = ttk.Frame(bottom_frame, style='Content.TFrame')
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(filter_frame, text="Filter by name:", style='TLabel', background=self.controller.FRAME_COLOR).pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry = ttk.Entry(filter_frame, width=25, style='TEntry')
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<Return>", lambda e: self.refresh())
        
        ttk.Button(filter_frame, text="Search", command=self.refresh, style='Secondary.TButton', width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="Reset", command=self.reset_search, style='Secondary.TButton', width=10).pack(side=tk.LEFT)

        # --- Contacts Table (in bottom_frame, middle) ---
        table_container = ttk.Frame(bottom_frame)
        table_container.pack(fill=tk.BOTH, expand=True)
        
        cols = ("id", "name")
        self.table = ttk.Treeview(table_container, columns=cols, show="headings", selectmode="browse", style='Treeview')

        self.table.heading("id", text="ID")
        self.table.heading("name", text="Contact Name")

        self.table.column("id", width=50, stretch=tk.NO, anchor=tk.CENTER)
        self.table.column("name", width=300, anchor=tk.W)

        scrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- Actions (in bottom_frame, bottom) ---
        ttk.Button(bottom_frame, text="Remove Selected", command=self.remove_contact, style='Delete.TButton').pack(side=tk.RIGHT, pady=(10, 0))


    def refresh(self):
        """Load/Reload contacts for the logged-in user."""
        if not self.controller.user_id:
            for row in self.table.get_children():
                self.table.delete(row)
            return

        for row in self.table.get_children():
            self.table.delete(row)

        search_term = self.search_entry.get().strip().lower()

        result = api_get_contacts(user_id=self.controller.user_id, order="name_asc")

        if result["success"]:
            contacts = result["data"]
            filtered_contacts = contacts

            if search_term:
                 filtered_contacts = [
                     contact for contact in contacts
                     if search_term in contact.get("name", "").lower()
                 ]

            for contact in filtered_contacts:
                self.table.insert("", tk.END, values=(
                    contact.get("id", ""),
                    contact.get("name", "N/A")
                ))
        else:
            messagebox.showerror("Error Loading Contacts", result["error"] or "Could not load contacts.")

    def add_contact(self):
        if not self.controller.user_id:
            messagebox.showerror("Error", "User not logged in.")
            return

        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Contact name is required.")
            return

        result = api_add_contact(name=name, user_id=self.controller.user_id)

        if result["success"]:
            messagebox.showinfo("Success", f"Contact '{name}' added.")
            self.name_entry.delete(0, tk.END)
            self.refresh()
        else:
            messagebox.showerror("Error Adding Contact", result["error"] or "Could not add contact.")

    def remove_contact(self):
        if not self.controller.user_id:
            messagebox.showerror("Error", "User not logged in.")
            return

        selected_items = self.table.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Select a contact to remove.")
            return

        item_id = self.table.item(selected_items[0])['values'][0]
        item_name = self.table.item(selected_items[0])['values'][1]

        if not item_id:
             messagebox.showerror("Error", "Could not find the ID of the selected contact.")
             return

        if messagebox.askyesno("Confirm Removal", f"Are you sure you want to remove contact '{item_name}' (ID: {item_id})?"):
            result = api_delete_contact(contact_id=item_id, user_id=self.controller.user_id)
            if result["success"]:
                 deleted_count = result.get("data", {}).get("deleted", 0)
                 if deleted_count > 0:
                     messagebox.showinfo("Success", "Contact removed.")
                 else:
                     messagebox.showwarning("Warning", "Contact not found or does not belong to the user.")
                 self.refresh()
            else:
                messagebox.showerror("Error Removing Contact", result["error"] or "Could not remove contact.")

    def reset_search(self):
         self.search_entry.delete(0, tk.END)
         self.refresh()