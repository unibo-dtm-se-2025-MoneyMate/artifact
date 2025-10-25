import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from MoneyMate.data_layer.api import api_add_contact, api_get_contacts, api_delete_contact
# You might want to add api_update_contact if it exists

class ContactsFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # --- Layout ---
        top_frame = ttk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        mid_frame = ttk.Frame(self)
        mid_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        # --- Add Contact Form (in top_frame) ---
        form = ttk.LabelFrame(top_frame, text="Add Contact", padding="10")
        form.pack(fill=tk.X)

        ttk.Label(form, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.name_entry = ttk.Entry(form, width=40)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        # You could add other fields like email or notes here
        # ttk.Label(form, text="Email:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        # self.email_entry = ttk.Entry(form, width=40)
        # self.email_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)

        add_button = ttk.Button(form, text="Add", command=self.add_contact)
        add_button.grid(row=0, column=2, padx=15, pady=5) # Moved to the same row

        form.columnconfigure(1, weight=1) # Expand name field

        # --- Contacts Table (in mid_frame) ---
        cols = ("id", "name") # Added ID
        self.table = ttk.Treeview(mid_frame, columns=cols, show="headings", selectmode="browse")

        self.table.heading("id", text="ID")
        self.table.heading("name", text="Contact Name")

        self.table.column("id", width=50, stretch=tk.NO, anchor=tk.CENTER)
        self.table.column("name", width=300)

        # Scrollbar
        scrollbar = ttk.Scrollbar(mid_frame, orient=tk.VERTICAL, command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Selection event (currently only for deletion)
        # self.table.bind("<<TreeviewSelect>>", self.on_row_select)

         # --- Filters and Actions (in bottom_frame) ---
        filter_frame = ttk.Frame(bottom_frame)
        filter_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(filter_frame, text="Filter by name:").pack(side=tk.LEFT)
        self.search_entry = ttk.Entry(filter_frame, width=25)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<Return>", lambda e: self.refresh()) # Filter on Enter
        ttk.Button(filter_frame, text="Search", command=self.refresh).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="Reset", command=self.reset_search).pack(side=tk.LEFT)

        # Remove Button
        ttk.Button(bottom_frame, text="Remove Selected", command=self.remove_contact).pack(side=tk.LEFT, padx=20)
        # You could add an "Edit" button here if you implement editing


    def refresh(self):
        """Load/Reload contacts for the logged-in user."""
        if not self.controller.user_id:
            for row in self.table.get_children():
                self.table.delete(row)
            return

        for row in self.table.get_children():
            self.table.delete(row)

        search_term = self.search_entry.get().strip().lower()

        # Call API to get contacts (no search API seems available, filter client-side)
        result = api_get_contacts(user_id=self.controller.user_id, order="name_asc") # Order by name

        if result["success"]:
            contacts = result["data"]
            filtered_contacts = contacts # Default to all contacts

            # Filter results if there's a search term
            if search_term:
                 filtered_contacts = [
                     contact for contact in contacts
                     if search_term in contact.get("name", "").lower()
                 ]

            # Populate table with filtered contacts
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
        # email = self.email_entry.get().strip() # If you add email

        if not name:
            messagebox.showerror("Error", "Contact name is required.")
            return

        # API Call
        result = api_add_contact(name=name, user_id=self.controller.user_id) # Add other fields if needed

        if result["success"]:
            messagebox.showinfo("Success", f"Contact '{name}' added.")
            self.name_entry.delete(0, tk.END)
            # self.email_entry.delete(0, tk.END)
            self.refresh() # Reload table
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

        item_id = self.table.item(selected_items[0])['values'][0] # Get ID
        item_name = self.table.item(selected_items[0])['values'][1] # Get name for confirmation

        if not item_id:
             messagebox.showerror("Error", "Could not find the ID of the selected contact.")
             return

        if messagebox.askyesno("Confirm Removal", f"Are you sure you want to remove contact '{item_name}' (ID: {item_id})?"):
            result = api_delete_contact(contact_id=item_id, user_id=self.controller.user_id)
            if result["success"]:
                 # Check if anything was actually deleted
                 deleted_count = result.get("data", {}).get("deleted", 0)
                 if deleted_count > 0:
                     messagebox.showinfo("Success", "Contact removed.")
                 else:
                     messagebox.showwarning("Warning", "Contact not found or does not belong to the user.")
                 self.refresh() # Reload table
            else:
                messagebox.showerror("Error Removing Contact", result["error"] or "Could not remove contact.")

    def reset_search(self):
         """Clears the search bar and reloads all contacts."""
         self.search_entry.delete(0, tk.END)
         self.refresh()

    # You could add on_row_select and edit_contact here if needed
    # def on_row_select(self, event=None): ...
    # def edit_contact(self): ...