"""
Login screen for the MoneyMate GUI.

This frame:

- Presents username and password fields with a minimal, centered layout.
- Calls the data-layer api_login_user to authenticate.
- Notifies the main MoneyMateGUI on successful login, so it can update
  user context and navigation.
- Provides a button to navigate to the registration screen.

The frame is also responsible for clearing its fields when refreshed.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from MoneyMate.data_layer.api import api_login_user

class LoginFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style='Content.TFrame')
        self.controller = controller

        # Center container to keep form visually balanced.
        center_frame = ttk.Frame(self, style='Content.TFrame')
        center_frame.pack(expand=True)

        ttk.Label(center_frame,
                  text="Welcome to MoneyMate",
                  style='Header.TLabel',
                  background=self.controller.FRAME_COLOR).pack(pady=(0, 20))

        # --- Login form group ---
        login_form = ttk.LabelFrame(center_frame, text="Login", style='TLabelframe')
        login_form.pack(pady=10, padx=20, fill='x')

        # Username row
        row_user = ttk.Frame(login_form, style='TLabelframe')
        row_user.pack(fill='x', padx=10, pady=(10, 5))
        ttk.Label(row_user, text="Username:", width=10,
                  style='TLabel', background=self.controller.FRAME_COLOR).pack(side=tk.LEFT)
        self.login_user_entry = ttk.Entry(row_user, width=30, style='TEntry')
        self.login_user_entry.pack(side=tk.LEFT, fill='x', expand=True, padx=5)

        # Password row
        row_pass = ttk.Frame(login_form, style='TLabelframe')
        row_pass.pack(fill='x', padx=10, pady=5)
        ttk.Label(row_pass, text="Password:", width=10,
                  style='TLabel', background=self.controller.FRAME_COLOR).pack(side=tk.LEFT)
        self.login_pass_entry = ttk.Entry(row_pass, show="*", width=30, style='TEntry')
        self.login_pass_entry.pack(side=tk.LEFT, fill='x', expand=True, padx=5)

        # Actions row
        actions = ttk.Frame(login_form, style='TLabelframe')
        actions.pack(fill='x', padx=10, pady=(10, 12))
        ttk.Button(actions, text="Login", command=self.attempt_login, style='TButton').pack(side=tk.LEFT)
        ttk.Button(actions, text="Create an account",
                   command=lambda: self.controller.show_frame("RegisterFrame"),
                   style='Secondary.TButton').pack(side=tk.LEFT, padx=10)

        # Keyboard shortcuts: Enter moves focus / triggers login
        self.login_user_entry.bind("<Return>", lambda e: self.login_pass_entry.focus())
        self.login_pass_entry.bind("<Return>", lambda e: self.attempt_login())

    def attempt_login(self) -> None:
        """Validate user input and call the login API."""
        username = self.login_user_entry.get().strip()
        password = self.login_pass_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Login Error", "Username and Password are required.")
            return

        result = api_login_user(username, password)

        if result.get("success"):
            user_id = result["data"]["user_id"]
            self.controller.on_login_success(user_id, username)
            self.clear_forms()
        else:
            messagebox.showerror("Login Error", result.get("error") or "Invalid credentials.")
            self.login_pass_entry.delete(0, tk.END)

    def clear_forms(self) -> None:
        """Reset all input fields to blank."""
        self.login_user_entry.delete(0, tk.END)
        self.login_pass_entry.delete(0, tk.END)

    def refresh(self) -> None:
        """Called when returning to this frame; just clear and focus."""
        self.clear_forms()
        self.login_user_entry.focus_set()