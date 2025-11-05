import tkinter as tk
from tkinter import ttk, messagebox
from MoneyMate.data_layer.api import api_register_user, api_login_user

class LoginFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Center layout
        center_frame = ttk.Frame(self)
        center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        ttk.Label(center_frame, text="MoneyMate Login", font=("Arial", 16, "bold")).pack(pady=20)

        # Login Form
        login_form = ttk.Frame(center_frame, padding="10")
        login_form.pack(pady=10)

        ttk.Label(login_form, text="Username:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.login_user_entry = ttk.Entry(login_form, width=30)
        self.login_user_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(login_form, text="Password:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.login_pass_entry = ttk.Entry(login_form, show="*", width=30)
        self.login_pass_entry.grid(row=1, column=1, padx=5, pady=5)

        login_button = ttk.Button(login_form, text="Login", command=self.attempt_login)
        login_button.grid(row=2, column=0, columnspan=2, pady=15)

        # Registration Form (initially hidden or separate)
        reg_form = ttk.Frame(center_frame, padding="10")
        reg_form.pack(pady=10)
        ttk.Label(reg_form, text="Don't have an account? Register").grid(row=0, column=0, columnspan=2, pady=5)


        ttk.Label(reg_form, text="Username:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.reg_user_entry = ttk.Entry(reg_form, width=30)
        self.reg_user_entry.grid(row=1, column=1, padx=5, pady=5)

        # You could also add email if your data layer requires it
        # ttk.Label(reg_form, text="Email:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        # self.reg_email_entry = ttk.Entry(reg_form, width=30)
        # self.reg_email_entry.grid(row=1, column=1, padx=5, pady=5)


        ttk.Label(reg_form, text="Password:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.reg_pass_entry = ttk.Entry(reg_form, show="*", width=30)
        self.reg_pass_entry.grid(row=2, column=1, padx=5, pady=5)

        # You could add password confirmation
        # ttk.Label(reg_form, text="Confirm Password:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        # self.reg_pass_confirm_entry = ttk.Entry(reg_form, show="*", width=30)
        # self.reg_pass_confirm_entry.grid(row=3, column=1, padx=5, pady=5)


        reg_button = ttk.Button(reg_form, text="Register", command=self.attempt_registration)
        reg_button.grid(row=3, column=0, columnspan=2, pady=15)


    def attempt_login(self):
        username = self.login_user_entry.get().strip()
        password = self.login_pass_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Login Error", "Username and Password are required.")
            return

        result = api_login_user(username, password)

        if result["success"]:
            user_id = result["data"]["user_id"]
            # Pass user_id and username to the main controller
            self.controller.on_login_success(user_id, username)
             # Clear fields after successful login
            self.login_user_entry.delete(0, tk.END)
            self.login_pass_entry.delete(0, tk.END)
            self.reg_user_entry.delete(0, tk.END)
            self.reg_pass_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Login Error", result["error"] or "Invalid credentials.")
            self.login_pass_entry.delete(0, tk.END) # Clear only password

    def attempt_registration(self):
        username = self.reg_user_entry.get().strip()
        password = self.reg_pass_entry.get().strip()
        # email = self.reg_email_entry.get().strip() # If you add email
        # confirm_password = self.reg_pass_confirm_entry.get().strip() # If you add confirmation

        if not username or not password: # or not email # or not confirm_password:
            messagebox.showerror("Registration Error", "All fields are required.")
            return

        # if password != confirm_password:
        #     messagebox.showerror("Registration Error", "Passwords do not match.")
        #     return

        # You might want to add password validations here (length, special characters...)

        # API call to register (assuming it doesn't require email for now)
        result = api_register_user(username, password) # Might need to pass email too

        if result["success"]:
            messagebox.showinfo("Registration Successful", f"User '{username}' registered successfully. Please log in.")
            # Clear registration fields
            self.reg_user_entry.delete(0, tk.END)
            # self.reg_email_entry.delete(0, tk.END)
            self.reg_pass_entry.delete(0, tk.END)
            # self.reg_pass_confirm_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Registration Error", result["error"] or "Unknown error during registration.")
            # Don't clear username, maybe the user just wants to change the password
            self.reg_pass_entry.delete(0, tk.END)
            # self.reg_pass_confirm_entry.delete(0, tk.END)