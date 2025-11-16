"""
Tkinter frame for managing expenses in the MoneyMate GUI.

This screen provides UX:

- Form to add and edit expenses (date, amount, category, description).
- Category selection tied to the current user's categories.
- Search/filter by text, with optional environment-driven limits and batching
  to keep the UI responsive on large datasets.
- Incremental insertion of table rows with diagnostic logging.
- Clear-all operation to remove all of the user's expenses.

Underlying operations use the data-layer API functions
(api_add_expense, api_update_expense, api_get_expenses, api_search_expenses,
 api_delete_expense, api_clear_expenses, api_get_categories).
"""

import os
import time
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import tracemalloc

from MoneyMate.data_layer.api import (
    api_add_expense, api_get_expenses, api_delete_expense,
    api_update_expense, api_get_categories, api_search_expenses,
    api_clear_expenses
)

class ExpensesFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style='Content.TFrame')
        self.controller = controller

        # Config
        self.max_rows = self._read_int_env("MONEYMATE_EXPENSES_LIMIT", 250)
        self.batch_size = self._read_int_env("MONEYMATE_EXPENSES_BATCH", 50)
        self.force_sync_insert = os.environ.get("MONEYMATE_SYNC_GUI") == "1"
        self.fake_mode = os.environ.get("MONEYMATE_EXPENSES_FAKE") == "1"

        # State
        self.categories_map = {}
        self.selected_expense_id = None
        self.expenses_buffer = []
        self.insert_index = 0
        self.total_accumulator = 0.0
        self.loading_label = None
        self.progress_label = None
        self.category_id_to_name = {}

        # Loop suppression flags / counters
        self._suppress_select_event = False
        self._clear_form_count = 0
        self._select_event_count = 0

        # --- UI ---
        top = ttk.LabelFrame(self, text=f"Manage Expenses (limit={self.max_rows}, batch={self.batch_size})", style='TLabelframe')
        top.pack(fill=tk.X, padx=10, pady=10)
        fg = ttk.Frame(top, style='TLabelframe')
        fg.pack(fill=tk.X, padx=10, pady=10)
        fg.columnconfigure(1, weight=1)
        fg.columnconfigure(3, weight=1)

        # Date
        ttk.Label(fg, text="Date (YYYY-MM-DD):", style='TLabel', background=self.controller.FRAME_COLOR).grid(row=0, column=0, sticky=tk.W, padx=5, pady=8)
        self.date_entry = ttk.Entry(fg, width=15, style='TEntry')
        self.date_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=8)
        self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))

        # Amount
        ttk.Label(fg, text="Amount (€):", style='TLabel', background=self.controller.FRAME_COLOR).grid(row=0, column=2, sticky=tk.W, padx=(15,5), pady=8)
        self.amount_entry = ttk.Entry(fg, width=15, style='TEntry')
        self.amount_entry.grid(row=0, column=3, sticky=tk.EW, padx=5, pady=8)

        # Category
        ttk.Label(fg, text="Category:", style='TLabel', background=self.controller.FRAME_COLOR).grid(row=1, column=0, sticky=tk.W, padx=5, pady=8)
        self.category_combo = ttk.Combobox(fg, state="readonly", style='TCombobox', width=15)
        self.category_combo.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=8)

        # Description
        ttk.Label(fg, text="Description:", style='TLabel', background=self.controller.FRAME_COLOR).grid(row=1, column=2, sticky=tk.W, padx=(15,5), pady=8)
        self.desc_entry = ttk.Entry(fg, style='TEntry')
        self.desc_entry.grid(row=1, column=3, sticky=tk.EW, padx=5, pady=8)

        # Buttons row
        btn_row = ttk.Frame(fg, style='TLabelframe')
        btn_row.grid(row=2, column=0, columnspan=4, pady=10, sticky=tk.E)
        self.add_button = ttk.Button(btn_row, text="Add Expense", command=self.add_expense, style='TButton')
        self.add_button.pack(side=tk.LEFT, padx=5)
        self.update_button = ttk.Button(btn_row, text="Save Changes", command=self.update_expense, state=tk.DISABLED, style='TButton')
        self.update_button.pack(side=tk.LEFT, padx=5)
        self.clear_button = ttk.Button(btn_row, text="Clear Form", command=self.clear_form, style='Secondary.TButton')
        self.clear_button.pack(side=tk.LEFT, padx=5)

        # Actions / filters
        actions = ttk.Frame(self, style='Content.TFrame')
        actions.pack(fill=tk.X, padx=10, pady=(0,10))
        ttk.Label(actions, text="Filter:", style='TLabel', background=self.controller.FRAME_COLOR).pack(side=tk.LEFT, padx=(0,5))
        self.search_entry = ttk.Entry(actions, width=25, style='TEntry')
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<Return>", lambda e: self.refresh())
        ttk.Button(actions, text="Search", command=self.refresh, style='Secondary.TButton').pack(side=tk.LEFT)
        ttk.Button(actions, text="Reset", command=self.reset_search, style='Secondary.TButton').pack(side=tk.LEFT)
        ttk.Button(actions, text="Clear All", command=self.clear_all_expenses, style='Delete.TButton').pack(side=tk.LEFT, padx=12)
        self.total_label = ttk.Label(actions, text="Total: 0.00 €", style='Total.TLabel', background=self.controller.FRAME_COLOR)
        self.total_label.pack(side=tk.RIGHT)

        # Table
        table_container = ttk.Frame(self)
        table_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        cols = ("id", "date", "description", "category_name", "amount")
        self.table = ttk.Treeview(table_container, columns=cols, show="headings", selectmode="browse", style='Treeview')
        for c, h in zip(cols, ("ID", "Date", "Description", "Category", "Amount (€)")):
            self.table.heading(c, text=h)
        self.table.column("id", width=50, anchor=tk.CENTER)
        self.table.column("date", width=100, anchor=tk.W)
        self.table.column("description", width=300, anchor=tk.W)
        self.table.column("category_name", width=120, anchor=tk.W)
        self.table.column("amount", width=100, anchor=tk.E)
        sb = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.table.yview)
        self.table.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.table.bind("<<TreeviewSelect>>", self.on_row_select)

        ttk.Button(self, text="Remove Selected Expense", command=self.remove_expense, style='Delete.TButton').pack(side=tk.RIGHT, padx=10, pady=(0,10))

    # Refresh logic
    def refresh(self):
        if not self.controller.user_id:
            self._clear_table()
            self.total_label.config(text="Total: 0.00 €")
            return

        self.refresh_categories()
        self._clear_table()
        self.selected_expense_id = None
        self.total_accumulator = 0.0

        search_term = self.search_entry.get().strip()
        tracemalloc.start()
        t_fetch_start = time.perf_counter()

        if self.fake_mode:
            rows = self._generate_fake_expenses(800 if not search_term else 250)
            result = {"success": True, "data": rows}
        else:
            if search_term:
                result = api_search_expenses(query=search_term, user_id=self.controller.user_id)
            else:
                result = api_get_expenses(
                    user_id=self.controller.user_id,
                    order="date_desc",
                    limit=self.max_rows,
                    offset=0
                )

        fetch_dt = time.perf_counter() - t_fetch_start
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"[DIAG] fetch_time={fetch_dt:.3f}s rows={len(result.get('data', []))} mem={current/1024:.1f}KB peak={peak/1024:.1f}KB search={repr(search_term)} limit={self.max_rows}")

        if not result.get("success"):
            messagebox.showerror("Error Loading Expenses", result.get("error") or "Could not load expenses.")
            self.total_label.config(text="Total: Error €")
            return

        self.expenses_buffer = result["data"]
        self.insert_index = 0
        self.category_id_to_name = {v: k for k, v in self.categories_map.items()}

        if self.force_sync_insert:
            t_ins_start = time.perf_counter()
            for exp in self.expenses_buffer:
                self._insert_one(exp)
            ins_dt = time.perf_counter() - t_ins_start
            print(f"[DIAG] sync_insert rows={len(self.expenses_buffer)} time={ins_dt:.3f}s")
            self._finalize_insertion()
        else:
            self._show_loading()
            self._insert_chunk()

    # Chunk insertion
    def _insert_chunk(self):
        start = time.perf_counter()
        end = min(self.insert_index + self.batch_size, len(self.expenses_buffer))
        for i in range(self.insert_index, end):
            self._insert_one(self.expenses_buffer[i])
        inserted = end - self.insert_index
        self.insert_index = end
        dt = time.perf_counter() - start
        if self.progress_label:
            self.progress_label.config(text=f"Inserted {self.insert_index}/{len(self.expenses_buffer)} (batch {inserted} in {dt:.3f}s)")
        print(f"[DIAG] batch_insert inserted={inserted} total_index={self.insert_index} dt={dt:.3f}s")
        if self.insert_index < len(self.expenses_buffer):
            self.after(5, self._insert_chunk)
        else:
            self._finalize_insertion()

    def _insert_one(self, expense):
        try:
            amount = float(expense.get("price", 0))
            self.total_accumulator += amount
            cat_id = expense.get("category_id")
            category_name = self.category_id_to_name.get(cat_id, expense.get("category", "N/A"))
            self.table.insert("", tk.END, values=(
                expense.get("id", ""),
                expense.get("date", ""),
                expense.get("title", ""),
                category_name,
                f"{amount:.2f}"
            ))
        except Exception as e:
            print(f"[DIAG] skip row error={e}")

    def _finalize_insertion(self):
        self._hide_loading()
        self.total_label.config(text=f"Total: {self.total_accumulator:.2f} €")
        self.clear_form()

    # Loading indicators
    def _show_loading(self):
        if not self.loading_label:
            self.loading_label = ttk.Label(self.table, text="Loading...", background=self.controller.FRAME_COLOR)
            self.loading_label.place(relx=0.5, rely=0.45, anchor='center')
        if not self.progress_label:
            self.progress_label = ttk.Label(self.table, text="Starting...", background=self.controller.FRAME_COLOR)
            self.progress_label.place(relx=0.5, rely=0.55, anchor='center')

    def _hide_loading(self):
        if self.loading_label:
            self.loading_label.destroy()
            self.loading_label = None
        if self.progress_label:
            self.progress_label.destroy()
            self.progress_label = None

    # Categories
    def refresh_categories(self):
        if not self.controller.user_id:
            self.category_combo['values'] = []
            self.categories_map = {}
            return
        result = api_get_categories(self.controller.user_id, order="name_asc")
        if result.get("success"):
            cats = result["data"]
            self.categories_map = {c['name']: c['id'] for c in cats}
            self.category_combo['values'] = list(self.categories_map.keys())
            self.category_combo.set(cats[0]['name'] if cats else '')
        else:
            self.categories_map = {}
            self.category_combo['values'] = []

    # Fake data
    def _generate_fake_expenses(self, n):
        data = []
        today = datetime.now()
        for i in range(n):
            d = today.replace(day=(i % 28) + 1)
            data.append({
                "id": i + 1,
                "title": f"Item {i+1}",
                "price": (i % 17) + 1.15,
                "date": d.strftime("%Y-%m-%d"),
                "category": "Misc",
                "category_id": None
            })
        return data

    # CRUD
    def add_expense(self):
        if not self.controller.user_id:
            messagebox.showerror("Error", "User not logged in.")
            return
        date = self.date_entry.get().strip()
        desc = self.desc_entry.get().strip()
        amount_str = self.amount_entry.get().strip().replace(',', '.')
        category_name = self.category_combo.get()
        if not (date and desc and amount_str and category_name):
            messagebox.showerror("Error", "All fields required.")
            return
        if not self._valid_date(date):
            messagebox.showerror("Error", "Invalid date format.")
            return
        amount = self._parse_amount(amount_str)
        if amount is None:
            return
        cat_id = self.categories_map.get(category_name)
        result = api_add_expense(title=desc, price=amount, date=date,
                                 category=category_name, user_id=self.controller.user_id,
                                 category_id=cat_id)
        if result.get("success"):
            messagebox.showinfo("Success", "Expense added.")
            self.refresh()
        else:
            messagebox.showerror("Add Error", result.get("error") or "Could not add expense.")

    def update_expense(self):
        if not self.controller.user_id or self.selected_expense_id is None:
            messagebox.showerror("Error", "No expense selected.")
            return
        date = self.date_entry.get().strip()
        desc = self.desc_entry.get().strip()
        amount_str = self.amount_entry.get().strip().replace(',', '.')
        category_name = self.category_combo.get()
        if not (date and desc and amount_str and category_name):
            messagebox.showerror("Error", "All fields required.")
            return
        if not self._valid_date(date):
            messagebox.showerror("Error", "Invalid date format.")
            return
        amount = self._parse_amount(amount_str)
        if amount is None:
            return
        cat_id = self.categories_map.get(category_name)
        result = api_update_expense(expense_id=self.selected_expense_id,
                                    user_id=self.controller.user_id,
                                    title=desc, price=amount, date=date,
                                    category=category_name, category_id=cat_id)
        if result.get("success"):
            messagebox.showinfo("Success", "Expense updated.")
            self.refresh()
        else:
            messagebox.showerror("Update Error", result.get("error") or "Could not update expense.")

    def remove_expense(self):
        if not self.controller.user_id:
            messagebox.showerror("Error", "User not logged in.")
            return
        sel = self.table.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select an expense.")
            return
        item_id = self.table.item(sel[0])['values'][0]
        if not item_id:
            messagebox.showerror("Error", "Invalid selection.")
            return
        if messagebox.askyesno("Confirm", f"Remove expense ID {item_id}?"):
            result = api_delete_expense(expense_id=item_id, user_id=self.controller.user_id)
            if result.get("success"):
                messagebox.showinfo("Success", "Expense removed.")
                self.refresh()
            else:
                messagebox.showerror("Removal Error", result.get("error") or "Could not remove expense.")

    def clear_all_expenses(self):
        if not self.controller.user_id:
            messagebox.showerror("Error", "User not logged in.")
            return
        if messagebox.askyesno("Confirm Bulk Removal", "Remove ALL your expenses?"):
            result = api_clear_expenses(user_id=self.controller.user_id)
            if result.get("success"):
                deleted = result.get("data", {}).get("deleted", 0)
                messagebox.showinfo("Clear All", f"Removed {deleted} expense(s).")
                self.refresh()
            else:
                messagebox.showerror("Bulk Removal Error", result.get("error") or "Could not clear expenses.")

    # Selection helpers
    def on_row_select(self, event=None):
        if self._suppress_select_event:
            return
        self._select_event_count += 1
        sel = self.table.selection()
        if not sel:
            return  # Non richiamiamo clear_form qui per evitare loop
        values = self.table.item(sel[0])['values']
        if len(values) < 5:
            return
        exp_id, date, desc, cat_name, amount_str = values
        self.selected_expense_id = exp_id
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, date)
        self.desc_entry.delete(0, tk.END)
        self.desc_entry.insert(0, desc)
        self.amount_entry.delete(0, tk.END)
        self.amount_entry.insert(0, amount_str.replace(" €", ""))
        if cat_name in self.category_combo['values']:
            self.category_combo.set(cat_name)
        if hasattr(self.update_button, "config"):
            self.update_button.config(state=tk.NORMAL)
        if hasattr(self.add_button, "config"):
            self.add_button.config(state=tk.DISABLED)
        print(f"[DIAG] select_event_count={self._select_event_count}")

    def clear_form(self):
        self._clear_form_count += 1
        self._suppress_select_event = True
        self.selected_expense_id = None
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.desc_entry.delete(0, tk.END)
        self.amount_entry.delete(0, tk.END)
        if self.category_combo['values']:
            self.category_combo.set(self.category_combo['values'][0])
        else:
            self.category_combo.set('')
        current_sel = self.table.selection()
        if current_sel:
            # rimuovi selezione solo se esiste
            try:
                self.table.selection_remove(current_sel)
            except Exception:
                pass
        if hasattr(self.add_button, "config"):
            self.add_button.config(state=tk.NORMAL)
        if hasattr(self.update_button, "config"):
            self.update_button.config(state=tk.DISABLED)
        self._suppress_select_event = False
        print(f"[DIAG] clear_form_count={self._clear_form_count}")

    def reset_search(self):
        self.search_entry.delete(0, tk.END)
        self.refresh()

    # Validators / utils
    def _valid_date(self, d):
        try:
            datetime.strptime(d, "%Y-%m-%d")
            return True
        except Exception:
            return False

    def _parse_amount(self, v):
        try:
            f = float(v)
            if f <= 0:
                raise ValueError("Amount must be positive")
            return f
        except Exception as e:
            messagebox.showerror("Error", f"Invalid amount: {e}")
            return None

    def _clear_table(self):
        for r in self.table.get_children():
            self.table.delete(r)

    def _read_int_env(self, key, default):
        raw = os.environ.get(key)
        if not raw:
            return default
        try:
            val = int(raw)
            return val if val > 0 else default
        except Exception:
            return default