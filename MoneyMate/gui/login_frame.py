import tkinter as tk
from tkinter import ttk, messagebox
from MoneyMate.data_layer.api import api_register_user, api_login_user

class LoginFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style='Content.TFrame') # Use content frame style
        self.controller = controller

        # Center layout
        center_frame = ttk.Frame(self, style='Content.TFrame')
        # Place in middle of the main content area
        center_frame.pack(expand=True)

        ttk.Label(center_frame, text="Welcome to MoneyMate", style='Header.TLabel', background=self.controller.FRAME_COLOR).pack(pady=(0, 20))

        # Use a PanedWindow to make login/register collapsible or side-by-side
        # For simplicity, we'll just stack them cleanly.

        # --- Login Form ---
        login_form = ttk.LabelFrame(center_frame, text="Login", style='TLabelframe')
        login_form.pack(pady=10, padx=20, fill='x')

        # Username
        l1_frame = ttk.Frame(login_form, style='TLabelframe')
        l1_frame.pack(fill='x', padx=10, pady=(10, 5))
        ttk.Label(l1_frame, text="Username:", width=10, style='TLabel', background=self.controller.FRAME_COLOR).pack(side=tk.LEFT)
        self.login_user_entry = ttk.Entry(l1_frame, width=30, style='TEntry')
        self.login_user_entry.pack(side=tk.LEFT, fill='x', expand=True, padx=5)

        # Password
        l2_frame = ttk.Frame(login_form, style='TLabelframe')
        l2_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(l2_frame, text="Password:", width=10, style='TLabel', background=self.controller.FRAME_COLOR).pack(side=tk.LEFT)
        self.login_pass_entry = ttk.Entry(l2_frame, show="*", width=30, style='TEntry')
        self.login_pass_entry.pack(side=tk.LEFT, fill='x', expand=True, padx=5)

        login_button = ttk.Button(login_form, text="Login", command=self.attempt_login, style='TButton')
        login_button.pack(pady=15, padx=10)

        # --- Registration Form ---
        reg_form = ttk.LabelFrame(center_frame, text="Register New Account", style='TLabelframe')
        reg_form.pack(pady=20, padx=20, fill='x')

        # Reg Username
        r1_frame = ttk.Frame(reg_form, style='TLabelframe')
        r1_frame.pack(fill='x', padx=10, pady=(10, 5))
        ttk.Label(r1_frame, text="Username:", width=10, style='TLabel', background=self.controller.FRAME_COLOR).pack(side=tk.LEFT)
        self.reg_user_entry = ttk.Entry(r1_frame, width=30, style='TEntry')
        self.reg_user_entry.pack(side=tk.LEFT, fill='x', expand=True, padx=5)

        # Reg Password
        r2_frame = ttk.Frame(reg_form, style='TLabelframe')
        r2_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(r2_frame, text="Password:", width=10, style='TLabel', background=self.controller.FRAME_COLOR).pack(side=tk.LEFT)
        self.reg_pass_entry = ttk.Entry(r2_frame, show="*", width=30, style='TEntry')
        self.reg_pass_entry.pack(side=tk.LEFT, fill='x', expand=True, padx=5)

        reg_button = ttk.Button(reg_form, text="Register", command=self.attempt_registration, style='Secondary.TButton')
        reg_button.pack(pady=15, padx=10)

        # Bind Enter key for quick login
        self.login_user_entry.bind("<Return>", lambda e: self.login_pass_entry.focus())
        self.login_pass_entry.bind("<Return>", lambda e: self.attempt_login())

    def attempt_login(self):
        username = self.login_user_entry.get().strip()
        password = self.login_pass_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Login Error", "Username and Password are required.")
            return

        result = api_login_user(username, password)

        if result["success"]:
            user_id = result["data"]["user_id"]
            self.controller.on_login_success(user_id, username)
            self.clear_forms()
        else:
            messagebox.showerror("Login Error", result["error"] or "Invalid credentials.")
            self.login_pass_entry.delete(0, tk.END)

    def attempt_registration(self):
        username = self.reg_user_entry.get().strip()
        password = self.reg_pass_entry.get().strip()

        if not username or not password: 
            messagebox.showerror("Registration Error", "All fields are required.")
            return

        # You might want to add password validations here (length, special characters...)
        if len(password) < 6:
            messagebox.showerror("Registration Error", "Password must be at least 6 characters long.")
            return

        result = api_register_user(username, password) 

        if result["success"]:
            messagebox.showinfo("Registration Successful", f"User '{username}' registered successfully. Please log in.")
            self.clear_forms()
        else:
            messagebox.showerror("Registration Error", result["error"] or "Unknown error during registration.")
            self.reg_pass_entry.delete(0, tk.END)

    def clear_forms(self):
        """Clears all entry fields."""
        self.login_user_entry.delete(0, tk.END)
        self.login_pass_entry.delete(0, tk.END)
        self.reg_user_entry.delete(0, tk.END)
        self.reg_pass_entry.delete(0, tk.END)

    def refresh(self):
        # Clear forms when logging out and returning to this page
        self.clear_forms()
        self.login_user_entry.focus_set()