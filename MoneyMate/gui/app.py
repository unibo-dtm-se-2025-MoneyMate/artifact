"""
Main GUI bootstrap and application shell for MoneyMate.

This module defines the MoneyMateGUI Tk root window, which:

- Sets up the global look & feel (colors, fonts, ttk styles).
- Initializes and registers all screen frames (login, register, expenses,
  categories, contacts, transactions, charts).
- Manages the logged-in user context (user_id, username).
- Provides a sidebar-based navigation once the user is authenticated.
- Wires GUI events to the data-layer API (login, logout, DB path setup).

Use run_gui() (or python -m MoneyMate) to start the desktop application.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os

# Import GUI frames (pages)
from .login_frame import LoginFrame
from .register_frame import RegisterFrame          # New separate registration screen
from .expenses_frame import ExpensesFrame
from .contacts_frame import ContactsFrame
from .transactions_frame import TransactionsFrame
from .charts_frame import ChartsFrame
from .categories_frame import CategoriesFrame

# Data layer API (for logout + DB path setup)
from MoneyMate.data_layer.api import set_db_path, api_logout_user

# Determine and create a local GUI-specific database file (isolated from tests)
db_file_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'data', 'moneymate_gui.db')
)
os.makedirs(os.path.dirname(db_file_path), exist_ok=True)
set_db_path(db_file_path)
print(f"[GUI] Using database file: {db_file_path}")

class MoneyMateGUI(tk.Tk):
    """
    Root window class.

    After login:
      - A sidebar appears with navigation buttons.
      - Each content screen (Expenses, Transactions, etc.) refreshes itself when shown.

    When logged out:
      - Only the Login / Register screens are visible.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # --- Window metadata ---
        self.title("MoneyMate")
        self.geometry("1100x750")
        self.minsize(900, 600)

        # Logged user context (set after successful login)
        self.user_id = None
        self.username = None

        # --- Shared color palette & fonts (central definition) ---
        self.BG_COLOR = "#F0F4F8"
        self.FRAME_COLOR = "#FFFFFF"
        self.PRIMARY_COLOR = "#00796B"
        self.PRIMARY_DARK = "#004D40"
        self.TEXT_COLOR = "#333333"
        self.MUTED_TEXT = "#555555"
        self.SIDEBAR_COLOR = "#E8EDF2"
        self.ERROR_COLOR = "#D32F2F"
        self.SUCCESS_COLOR = "#388E3C"

        self.HEADER_FONT = ('Arial', 16, 'bold')
        self.TITLE_FONT = ('Arial', 12, 'bold')
        self.BODY_FONT = ('Arial', 10)
        self.SMALL_FONT = ('Arial', 9)

        self.configure(background=self.BG_COLOR)

        # --- ttk Style setup (one place for visual theming) ---
        self.style = ttk.Style(self)
        self.style.theme_use('clam')

        # Generic styling
        self.style.configure('.', background=self.BG_COLOR, foreground=self.TEXT_COLOR, font=self.BODY_FONT)
        self.style.configure('TFrame', background=self.BG_COLOR)
        self.style.configure('Content.TFrame', background=self.FRAME_COLOR)

        # Labels
        self.style.configure('TLabel', background=self.BG_COLOR, foreground=self.TEXT_COLOR)
        self.style.configure('Header.TLabel', font=self.HEADER_FONT, foreground=self.PRIMARY_DARK, background=self.BG_COLOR)
        self.style.configure('Title.TLabel', font=self.TITLE_FONT, foreground=self.PRIMARY_DARK, background=self.BG_COLOR)
        self.style.configure('Muted.TLabel', foreground=self.MUTED_TEXT, background=self.BG_COLOR)
        self.style.configure('Total.TLabel', font=('Arial', 11, 'bold'), foreground=self.PRIMARY_DARK, background=self.BG_COLOR)
        self.style.configure('Balance.TLabel', font=('Arial', 11, 'bold'), foreground=self.PRIMARY_DARK, background=self.BG_COLOR)

        # Buttons (primary + variants)
        self.style.configure('TButton', font=('Arial', 10, 'bold'),
                             foreground='white', background=self.PRIMARY_COLOR,
                             padding=(10, 5), relief='flat', borderwidth=0)
        self.style.map('TButton',
                       background=[('active', self.PRIMARY_DARK), ('pressed', self.PRIMARY_DARK)],
                       foreground=[('active', 'white')])
        self.style.configure('Delete.TButton', background=self.ERROR_COLOR, foreground='white')
        self.style.map('Delete.TButton', background=[('active', '#B71C1C'), ('pressed', '#B71C1C')])
        self.style.configure('Secondary.TButton', background='#B0BEC5', foreground=self.TEXT_COLOR)
        self.style.map('Secondary.TButton', background=[('active', '#90A4AE'), ('pressed', '#90A4AE')])

        # Entries / Comboboxes
        self.style.configure('TEntry', fieldbackground=self.FRAME_COLOR, foreground=self.TEXT_COLOR,
                             borderwidth=1, relief='solid', padding=5)
        self.style.configure('TCombobox', fieldbackground=self.FRAME_COLOR, foreground=self.TEXT_COLOR,
                             borderwidth=1, padding=5)

        # Treeview styling (tables)
        self.style.configure('Treeview', rowheight=25, fieldbackground=self.FRAME_COLOR,
                             background=self.FRAME_COLOR, foreground=self.TEXT_COLOR)
        self.style.configure('Treeview.Heading', font=('Arial', 10, 'bold'),
                             background=self.PRIMARY_COLOR, foreground='white', relief='flat', padding=5)

        # Labeled frame (form group)
        self.style.configure('TLabelframe', background=self.FRAME_COLOR, borderwidth=1, relief='solid')
        self.style.configure('TLabelframe.Label', background=self.FRAME_COLOR, foreground=self.PRIMARY_DARK,
                             font=self.TITLE_FONT, padding=(10, 5))

        # Sidebar container (created after login)
        container = ttk.Frame(self, style='TFrame')
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, minsize=200, weight=0)  # Sidebar
        container.grid_columnconfigure(1, weight=1)               # Main content

        self.frames = {}

        # Sidebar (hidden until login)
        self.sidebar_frame = ttk.Frame(container, style='Sidebar.TFrame')
        self.style.configure('Sidebar.TFrame', background=self.SIDEBAR_COLOR)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew", padx=(5, 0), pady=5)
        self.sidebar_frame.grid_remove()
        self.sidebar_buttons = {}

        # Main area for screens
        self.main_area = ttk.Frame(container, style='Content.TFrame', padding=10)
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=(5, 5), pady=5)
        self.main_area.grid_rowconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        # Register all frames (screens)
        for F in (LoginFrame, RegisterFrame, ExpensesFrame, CategoriesFrame, ContactsFrame, TransactionsFrame, ChartsFrame):
            page_name = F.__name__
            frame = F(parent=self.main_area, controller=self)
            frame.configure(style='Content.TFrame')
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Start at the login page
        self.show_frame("LoginFrame")

    def show_frame(self, page_name: str) -> None:
        """Display a frame by its class name, with safe optional refresh."""
        frame = self.frames[page_name]

        # Visual selection state for sidebar buttons
        for name, button in self.sidebar_buttons.items():
            if name == page_name:
                button.state(['selected'])
            else:
                button.state(['!selected'])

        # Safe conditional refresh call
        if hasattr(frame, 'refresh') and callable(getattr(frame, 'refresh')):
            if not (page_name == "LoginFrame" and self.user_id is not None):
                try:
                    frame.refresh()
                except Exception as e:
                    print(f"[GUI] Error refreshing {page_name}: {e}")
                    messagebox.showerror("Update Error", f"Could not update data for {page_name}.\n{e}")

        frame.tkraise()

    def on_login_success(self, user_id: int, username: str) -> None:
        """Called by LoginFrame after a successful login."""
        self.user_id = user_id
        self.username = username
        print(f"[GUI] Login successful for user_id={self.user_id}, username={self.username}")
        self.setup_sidebar()
        self.sidebar_frame.grid()               # Show the sidebar
        self.show_frame("ChartsFrame")          # Show Dashboard first

    def setup_sidebar(self) -> None:
        """Create the sidebar buttons after login."""
        for widget in self.sidebar_frame.winfo_children():
            widget.destroy()
        self.sidebar_buttons = {}

        ttk.Label(
            self.sidebar_frame,
            text=f"Welcome, {self.username}",
            style='Title.TLabel',
            font=('Arial', 12, 'bold'),
            background=self.SIDEBAR_COLOR,
            padding=(15, 15)
        ).pack(pady=10, fill='x')

        buttons = {
            "Dashboard": ("ChartsFrame", "📊"),
            "Expenses": ("ExpensesFrame", "💳"),
            "Categories": ("CategoriesFrame", "🏷️"),
            "Transactions": ("TransactionsFrame", "💸"),
            "Contacts": ("ContactsFrame", "👥"),
        }

        for text, (frame_name, icon) in buttons.items():
            button_text = f" {icon}  {text}"  # Add icon
            button = ttk.Button(
                self.sidebar_frame,
                text=button_text,
                command=lambda fn=frame_name: self.show_frame(fn),
                style='Sidebar.TButton'
            )
            button.pack(pady=2, fill='x')
            self.sidebar_buttons[frame_name] = button

        logout_button = ttk.Button(
            self.sidebar_frame,
            text=" 📴  Logout",
            command=self.logout,
            style='Logout.Sidebar.TButton'
        )
        logout_button.pack(pady=20, fill='x', side='bottom', padx=10)

    def logout(self) -> None:
        """Perform logout and reset UI to LoginFrame."""
        if self.user_id:
            api_logout_user(self.user_id)  # API Call
            print(f"[GUI] Logout for user_id: {self.user_id}")

        self.user_id = None
        self.username = None
        self.sidebar_frame.grid_remove()
        for widget in self.sidebar_frame.winfo_children():
            widget.destroy()
        self.sidebar_buttons = {}
        self.show_frame("LoginFrame")


def run_gui() -> None:
    """Entrypoint for launching the GUI via python -m MoneyMate."""
    app = MoneyMateGUI()
    app.mainloop()


if __name__ == "__main__":
    run_gui()