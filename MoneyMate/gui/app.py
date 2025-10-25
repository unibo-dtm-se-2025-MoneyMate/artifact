import tkinter as tk
from tkinter import ttk, messagebox
import os # To set the DB path

# Import specific frames
from .login_frame import LoginFrame
from .expenses_frame import ExpensesFrame
from .contacts_frame import ContactsFrame
from .transactions_frame import TransactionsFrame
from .charts_frame import ChartsFrame

# Import data layer APIs
from MoneyMate.data_layer.api import set_db_path, api_logout_user

# Set the database path (IMPORTANT!)
# Make sure the path is correct relative to where you run the app
# You might want to make this configurable
db_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'moneymate_gui.db'))
os.makedirs(os.path.dirname(db_file_path), exist_ok=True) # Create the data folder if it doesn't exist
set_db_path(db_file_path)
print(f"GUI: Using database: {db_file_path}")


class MoneyMateGUI(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title("MoneyMate")
        self.geometry("1000x750")

        self.user_id = None # Will be set after login
        self.username = None

        container = ttk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1) # Sidebar column
        container.grid_columnconfigure(1, weight=3) # Main area wider

        self.frames = {}

        # --- Sidebar ---
        self.sidebar_frame = ttk.Frame(container, width=200, style='Sidebar.TFrame')
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.sidebar_frame.grid_remove() # Hide sidebar initially

        # Style for the sidebar (optional)
        style = ttk.Style(self)
        style.configure('Sidebar.TFrame', background='#e0e0e0')
        style.configure('Sidebar.TButton', padding=10, width=20)


        # --- Main Area ---
        self.main_area = ttk.Frame(container)
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.main_area.grid_rowconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        # Add all frames (including login)
        for F in (LoginFrame, ExpensesFrame, ContactsFrame, TransactionsFrame, ChartsFrame):
            page_name = F.__name__
            frame = F(parent=self.main_area, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("LoginFrame")

    def show_frame(self, page_name):
        '''Show a frame by name'''
        frame = self.frames[page_name]
        # If the frame has a 'refresh' method, call it before showing
        if hasattr(frame, 'refresh') and callable(getattr(frame, 'refresh')):
             # Don't refresh the login frame after login
             if not (page_name == "LoginFrame" and self.user_id is not None):
                try:
                    frame.refresh()
                except Exception as e:
                    print(f"Error refreshing frame {page_name}: {e}")
                    messagebox.showerror("Update Error", f"Could not update data for {page_name}.\n{e}")

        frame.tkraise()

    def on_login_success(self, user_id, username):
        """Called by LoginFrame after a successful login."""
        self.user_id = user_id
        self.username = username
        print(f"Login successful for user_id: {self.user_id}, username: {self.username}")
        self.setup_sidebar() # Configure and show the sidebar
        self.sidebar_frame.grid() # Show the sidebar
        self.show_frame("ExpensesFrame") # Show the expenses frame after login

    def setup_sidebar(self):
         """Create the sidebar buttons after login."""
         # Clear any previous buttons
         for widget in self.sidebar_frame.winfo_children():
            widget.destroy()

         ttk.Label(self.sidebar_frame, text=f"User: {self.username}", background='#e0e0e0', font=("Arial", 10, "bold")).pack(pady=10)

         # Navigation buttons
         buttons = {
            "📊 Dashboard/Charts": "ChartsFrame",
            "💸 Expenses": "ExpensesFrame",
            "👥 Contacts": "ContactsFrame",
            "🤝 Transactions": "TransactionsFrame",
         }

         for text, frame_name in buttons.items():
            button = ttk.Button(
                self.sidebar_frame,
                text=text,
                command=lambda fn=frame_name: self.show_frame(fn),
                style='Sidebar.TButton'
            )
            button.pack(pady=5, fill='x')

         # Logout button
         logout_button = ttk.Button(
                self.sidebar_frame,
                text="🔒 Logout",
                command=self.logout,
                style='Sidebar.TButton'
            )
         logout_button.pack(pady=20, fill='x', side='bottom')


    def logout(self):
        """Perform logout."""
        if self.user_id:
            # You might want to call the logout API here if implemented
            # to invalidate server-side tokens or log the event
             api_logout_user(self.user_id) # API Call
             print(f"Logout for user_id: {self.user_id}")

        self.user_id = None
        self.username = None
        self.sidebar_frame.grid_remove() # Hide sidebar
        for widget in self.sidebar_frame.winfo_children(): # Clear sidebar
            widget.destroy()
        self.show_frame("LoginFrame") # Go back to the login screen


def run_gui():
    app = MoneyMateGUI()
    app.mainloop()

if __name__ == "__main__":
     # This allows running the app directly from this file
     # Ensure the CWD is the project root or MoneyMate is in PYTHONPATH
    run_gui()