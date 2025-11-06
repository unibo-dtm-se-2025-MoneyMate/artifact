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
        self.geometry("1100x750") # Slightly larger for better spacing
        self.minsize(900, 600) # Set a minimum size

        self.user_id = None # Will be set after login
        self.username = None

        # --- Define Color Palette & Fonts ---
        self.BG_COLOR = "#F0F4F8"       # Light blue-gray background
        self.FRAME_COLOR = "#FFFFFF"    # White for content frames
        self.PRIMARY_COLOR = "#00796B"  # Teal for primary actions
        self.PRIMARY_DARK = "#004D40"   # Darker teal for headers/hover
        self.TEXT_COLOR = "#333333"      # Dark gray for text
        self.MUTED_TEXT = "#555555"     # Lighter gray for secondary text
        self.SIDEBAR_COLOR = "#E8EDF2"   # Light gray for sidebar
        self.ERROR_COLOR = "#D32F2F"     # Red for errors
        self.SUCCESS_COLOR = "#388E3C"   # Green for success
        
        # Use Arial as a safer, common font
        self.HEADER_FONT = ('Arial', 16, 'bold')
        self.TITLE_FONT = ('Arial', 12, 'bold')
        self.BODY_FONT = ('Arial', 10)
        self.SMALL_FONT = ('Arial', 9)

        # --- Configure Main Window ---
        self.configure(background=self.BG_COLOR)

        # --- Configure Global Styles ---
        self.style = ttk.Style(self)
        self.style.theme_use('clam') # 'clam' is a good base for customization

        # General Widget Styles
        self.style.configure('.', background=self.BG_COLOR, foreground=self.TEXT_COLOR, font=self.BODY_FONT)
        self.style.configure('TFrame', background=self.BG_COLOR)
        self.style.configure('Content.TFrame', background=self.FRAME_COLOR) # Special style for main content area

        # Labels
        self.style.configure('TLabel', background=self.BG_COLOR, foreground=self.TEXT_COLOR)
        self.style.configure('Header.TLabel', font=self.HEADER_FONT, foreground=self.PRIMARY_DARK, background=self.BG_COLOR)
        self.style.configure('Title.TLabel', font=self.TITLE_FONT, foreground=self.PRIMARY_DARK, background=self.BG_COLOR)
        self.style.configure('Muted.TLabel', foreground=self.MUTED_TEXT, background=self.BG_COLOR)
        self.style.configure('Total.TLabel', font=('Arial', 11, 'bold'), foreground=self.PRIMARY_DARK, background=self.BG_COLOR)
        self.style.configure('Balance.TLabel', font=('Arial', 11, 'bold'), foreground=self.PRIMARY_DARK, background=self.BG_COLOR)

        # Buttons
        self.style.configure('TButton', font=('Arial', 10, 'bold'), foreground='white', background=self.PRIMARY_COLOR, padding=(10, 5), relief='flat', borderwidth=0)
        self.style.map('TButton',
            background=[('active', self.PRIMARY_DARK), ('pressed', self.PRIMARY_DARK)],
            foreground=[('active', 'white')]
        )
        self.style.configure('Delete.TButton', background=self.ERROR_COLOR, foreground='white')
        self.style.map('Delete.TButton', background=[('active', '#B71C1C'), ('pressed', '#B71C1C')])
        self.style.configure('Secondary.TButton', background='#B0BEC5', foreground=self.TEXT_COLOR)
        self.style.map('Secondary.TButton', background=[('active', '#90A4AE'), ('pressed', '#90A4AE')])


        # Entries and Comboboxes
        self.style.configure('TEntry', fieldbackground=self.FRAME_COLOR, foreground=self.TEXT_COLOR, borderwidth=1, relief='solid', padding=5)
        self.style.map('TEntry', bordercolor=[('focus', self.PRIMARY_COLOR)])
        self.style.configure('TCombobox', fieldbackground=self.FRAME_COLOR, foreground=self.TEXT_COLOR, borderwidth=1, padding=5)
        self.style.map('TCombobox', bordercolor=[('focus', self.PRIMARY_COLOR)], arrowcolor=[('!disabled', self.PRIMARY_COLOR)])

        # Treeview (Tables)
        self.style.configure('Treeview', rowheight=25, fieldbackground=self.FRAME_COLOR, background=self.FRAME_COLOR, foreground=self.TEXT_COLOR)
        self.style.configure('Treeview.Heading', font=('Arial', 10, 'bold'), background=self.PRIMARY_COLOR, foreground='white', relief='flat', padding=5)
        self.style.map('Treeview.Heading', background=[('active', self.PRIMARY_DARK), ('pressed', self.PRIMARY_DARK)])
        self.style.layout('Treeview', [('Treeview.treearea', {'sticky': 'nswe'})]) # Remove borders

        # LabelFrame
        self.style.configure('TLabelframe', background=self.FRAME_COLOR, borderwidth=1, relief='solid')
        self.style.configure('TLabelframe.Label', background=self.FRAME_COLOR, foreground=self.PRIMARY_DARK, font=self.TITLE_FONT, padding=(10, 5))
        
        # Radiobutton
        self.style.configure('TRadiobutton', background=self.BG_COLOR, foreground=self.TEXT_COLOR, font=self.SMALL_FONT)
        self.style.map('TRadiobutton', indicatorcolor=[('selected', self.PRIMARY_COLOR)])

        # --- Main Layout ---
        container = ttk.Frame(self, style='TFrame')
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, minsize=200, weight=0) # Sidebar (fixed width)
        container.grid_columnconfigure(1, weight=1)               # Main area (flexible)

        self.frames = {}

        # --- Sidebar ---
        self.sidebar_frame = ttk.Frame(container, style='Sidebar.TFrame')
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew", padx=(5, 0), pady=5)
        self.style.configure('Sidebar.TFrame', background=self.SIDEBAR_COLOR)
        
        # Sidebar Buttons
        self.style.configure('Sidebar.TButton',
            font=('Arial', 11, 'bold'),
            foreground=self.PRIMARY_DARK,
            background=self.SIDEBAR_COLOR,
            anchor='w',
            padding=(15, 10),
            relief='flat',
            borderwidth=0
        )
        self.style.map('Sidebar.TButton',
            background=[
                ('active', '#D6DEE5'),
                ('selected', self.FRAME_COLOR) # Style for the active button
            ],
            foreground=[
                ('selected', self.PRIMARY_COLOR)
            ]
        )
        self.style.configure('Logout.Sidebar.TButton', foreground=self.MUTED_TEXT)
        self.style.map('Logout.Sidebar.TButton', foreground=[('active', self.ERROR_COLOR)], background=[('active', '#F5E6E6')])

        self.sidebar_frame.grid_remove() # Hide sidebar initially
        self.sidebar_buttons = {} # To track active button

        # --- Main Area ---
        self.main_area = ttk.Frame(container, style='Content.TFrame', padding=10)
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=(5, 5), pady=5)
        self.main_area.grid_rowconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        # Add all frames (including login)
        for F in (LoginFrame, ExpensesFrame, ContactsFrame, TransactionsFrame, ChartsFrame):
            page_name = F.__name__
            frame = F(parent=self.main_area, controller=self)
            # Apply the content frame style to all main pages
            frame.configure(style='Content.TFrame') 
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("LoginFrame")

    def show_frame(self, page_name):
        '''Show a frame by name'''
        frame = self.frames[page_name]
        
        # Update sidebar button styles
        for name, button in self.sidebar_buttons.items():
            if name == page_name:
                button.state(['selected'])
            else:
                button.state(['!selected'])

        if hasattr(frame, 'refresh') and callable(getattr(frame, 'refresh')):
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
        self.setup_sidebar() 
        self.sidebar_frame.grid() # Show the sidebar
        self.show_frame("ChartsFrame") # Show Dashboard first

    def setup_sidebar(self):
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
            "Transactions": ("TransactionsFrame", "💸"),
            "Contacts": ("ContactsFrame", "👥"),
         }

         for text, (frame_name, icon) in buttons.items():
            button_text = f" {icon}  {text}" # Add icon
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


    def logout(self):
        """Perform logout."""
        if self.user_id:
             api_logout_user(self.user_id) # API Call
             print(f"Logout for user_id: {self.user_id}")

        self.user_id = None
        self.username = None
        self.sidebar_frame.grid_remove() 
        for widget in self.sidebar_frame.winfo_children(): 
            widget.destroy()
        self.sidebar_buttons = {}
        self.show_frame("LoginFrame")


def run_gui():
    app = MoneyMateGUI()
    app.mainloop()

if __name__ == "__main__":
    run_gui()