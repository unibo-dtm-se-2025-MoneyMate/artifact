"""
User registration screen for the MoneyMate GUI.

Responsibilities:
- Collect a new username and password from the user.
- Perform basic client-side checks (non-empty, minimum length).
- Call api_register_user to create the account.
- Show success/error messages and optionally return the user to the login
  screen after successful registration.

This frame is separate from LoginFrame to keep flows simple and focused.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from MoneyMate.data_layer.api import api_register_user

class RegisterFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style='Content.TFrame')
        self.controller = controller

        center = ttk.Frame(self, style='Content.TFrame')
        center.pack(expand=True)

        ttk.Label(center,
                  text="Create your MoneyMate account",
                  style='Header.TLabel',
                  background=self.controller.FRAME_COLOR).pack(pady=(0, 20))

        reg_form = ttk.LabelFrame(center, text="Register", style='TLabelframe')
        reg_form.pack(pady=10, padx=20, fill='x')

        # Username row
        r1 = ttk.Frame(reg_form, style='TLabelframe')
        r1.pack(fill='x', padx=10, pady=(10, 5))
        ttk.Label(r1, text="Username:", width=12,
                  style='TLabel', background=self.controller.FRAME_COLOR).pack(side=tk.LEFT)
        self.reg_user_entry = ttk.Entry(r1, width=30, style='TEntry')
        self.reg_user_entry.pack(side=tk.LEFT, fill='x', expand=True, padx=5)

        # Password row
        r2 = ttk.Frame(reg_form, style='TLabelframe')
        r2.pack(fill='x', padx=10, pady=5)
        ttk.Label(r2, text="Password:", width=12,
                  style='TLabel', background=self.controller.FRAME_COLOR).pack(side=tk.LEFT)
        self.reg_pass_entry = ttk.Entry(r2, show="*", width=30, style='TEntry')
        self.reg_pass_entry.pack(side=tk.LEFT, fill='x', expand=True, padx=5)

        # Actions
        actions = ttk.Frame(reg_form, style='TLabelframe')
        actions.pack(fill='x', padx=10, pady=(10, 12))
        ttk.Button(actions, text="Register", command=self.attempt_registration, style='TButton').pack(side=tk.LEFT)
        ttk.Button(actions, text="Back to Login",
                   command=lambda: self.controller.show_frame("LoginFrame"),
                   style='Secondary.TButton').pack(side=tk.LEFT, padx=10)

        # Enter key shortcuts
        self.reg_user_entry.bind("<Return>", lambda e: self.reg_pass_entry.focus())
        self.reg_pass_entry.bind("<Return>", lambda e: self.attempt_registration())

    def attempt_registration(self) -> None:
        """Validate input and call registration API."""
        username = self.reg_user_entry.get().strip()
        password = self.reg_pass_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Registration Error", "All fields are required.")
            return
        if len(password) < 6:
            messagebox.showerror("Registration Error", "Password must be at least 6 characters long.")
            return

        result = api_register_user(username, password)

        if result.get("success"):
            messagebox.showinfo("Registration Successful",
                                f"User '{username}' registered. Please log in.")
            self.clear()
            self.controller.show_frame("LoginFrame")
        else:
            messagebox.showerror("Registration Error", result.get("error") or "Unknown error.")
            self.reg_pass_entry.delete(0, tk.END)

    def clear(self) -> None:
        """Reset form fields."""
        self.reg_user_entry.delete(0, tk.END)
        self.reg_pass_entry.delete(0, tk.END)

    def refresh(self) -> None:
        """Refresh hook — just clear and focus username."""
        self.clear()
        self.reg_user_entry.focus_set()