import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from collections import defaultdict
import matplotlib.dates as mdates
from datetime import datetime

from MoneyMate.data_layer.api import api_get_expenses, api_get_user_balance_breakdown, api_get_categories

class ChartsFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ttk.Label(self, text="Financial Dashboard", font=("Arial", 16, "bold")).pack(pady=10)

        # Frame to contain the charts
        self.charts_container = ttk.Frame(self)
        self.charts_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Refresh button (might not be needed if you refresh when frame is shown)
        # refresh_button = ttk.Button(self, text="Refresh Charts", command=self.refresh)
        # refresh_button.pack(pady=5)

    def refresh(self):
        """Generate and display the charts."""
        if not self.controller.user_id:
            messagebox.showwarning("Info", "Log in to view charts.")
            # Clear previous charts if any
            for widget in self.charts_container.winfo_children():
                widget.destroy()
            ttk.Label(self.charts_container, text="Please log in to see the dashboard.").pack(pady=20)
            return

        # Clear previous charts
        for widget in self.charts_container.winfo_children():
            widget.destroy()

        # --- Data for Charts ---
        expenses_data = []
        balance_data = None
        category_id_to_name = {} # Map Category ID -> Name

        # 1. Load categories to map IDs to Names
        cat_result = api_get_categories(self.controller.user_id)
        if cat_result["success"]:
            category_id_to_name = {cat['id']: cat['name'] for cat in cat_result["data"]}
        else:
            print("Warning: Could not load categories for charts.")


        # 2. Load all expenses (no filters for now, for aggregate charts)
        exp_result = api_get_expenses(user_id=self.controller.user_id, limit=1000) # High limit for data
        if exp_result["success"]:
            expenses_data = exp_result["data"]
        else:
            messagebox.showerror("Chart Data Error", f"Could not load expenses: {exp_result['error']}")
            # Don't block, maybe the balance chart works

        # 3. Load balance breakdown
        bal_result = api_get_user_balance_breakdown(self.controller.user_id)
        if bal_result["success"]:
            balance_data = bal_result["data"]
        else:
            messagebox.showerror("Chart Data Error", f"Could not load balance data: {bal_result['error']}")

        # --- Chart Creation ---
        if not expenses_data and not balance_data:
             ttk.Label(self.charts_container, text="No data available for charts.").pack(pady=20)
             return

        # Use subplots to organize charts
        # Increase figsize if needed
        fig, axes = plt.subplots(2, 2, figsize=(10, 8)) # 2x2 grid
        fig.subplots_adjust(hspace=0.4, wspace=0.3) # Spacing between charts


        # --- Chart 1: Expenses by Category (Pie) ---
        ax1 = axes[0, 0]
        if expenses_data:
            expenses_by_category = defaultdict(float)
            for exp in expenses_data:
                cat_id = exp.get("category_id")
                # Use name from ID if possible, else legacy name, else 'Uncategorized'
                category_name = category_id_to_name.get(cat_id, exp.get("category", "Uncategorized"))
                try:
                    expenses_by_category[category_name] += float(exp.get("price", 0))
                except (ValueError, TypeError):
                    continue # Skip expenses with invalid amount

            if expenses_by_category:
                labels = list(expenses_by_category.keys())
                sizes = list(expenses_by_category.values())
                ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, textprops={'fontsize': 8})
                ax1.set_title("Expenses by Category", fontsize=10)
            else:
                ax1.text(0.5, 0.5, 'No expenses found', horizontalalignment='center', verticalalignment='center')
                ax1.set_title("Expenses by Category", fontsize=10)
            ax1.axis('equal') # Ensure pie is drawn as a circle
        else:
             ax1.text(0.5, 0.5, 'Expense data not available', horizontalalignment='center', verticalalignment='center')
             ax1.set_title("Expenses by Category", fontsize=10)


        # --- Chart 2: Expense Trend Over Time (Line/Bar) ---
        ax2 = axes[0, 1]
        if expenses_data:
            expenses_by_date = defaultdict(float)
            dates = []
            for exp in expenses_data:
                try:
                    # Convert date string to datetime object for sorting and plotting
                    date_obj = datetime.strptime(exp.get("date"), '%Y-%m-%d')
                    dates.append(date_obj)
                    expenses_by_date[date_obj] += float(exp.get("price", 0))
                except (ValueError, TypeError, KeyError):
                    continue # Skip invalid dates or amounts

            if expenses_by_date:
                # Sort dates for line chart
                sorted_dates = sorted(expenses_by_date.keys())
                amounts = [expenses_by_date[d] for d in sorted_dates]

                ax2.plot(sorted_dates, amounts, marker='o', linestyle='-')
                ax2.set_title("Expense Trend Over Time", fontsize=10)
                ax2.set_xlabel("Date", fontsize=8)
                ax2.set_ylabel("Amount (€)", fontsize=8)

                # Format X-axis to show dates nicely
                ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                ax2.xaxis.set_major_locator(mdates.AutoDateLocator()) # Find best dates to show
                fig.autofmt_xdate() # Rotate date labels automatically
                ax2.tick_params(axis='x', labelsize=7)
                ax2.tick_params(axis='y', labelsize=8)
                ax2.grid(True, linestyle='--', alpha=0.6)
            else:
                 ax2.text(0.5, 0.5, 'No valid expenses found', horizontalalignment='center', verticalalignment='center')
                 ax2.set_title("Expense Trend Over Time", fontsize=10)
        else:
             ax2.text(0.5, 0.5, 'Expense data not available', horizontalalignment='center', verticalalignment='center')
             ax2.set_title("Expense Trend Over Time", fontsize=10)


        # --- Chart 3: Balance Summary (Bar) ---
        ax3 = axes[1, 0]
        if balance_data:
            labels = ['Credits Received', 'Debits Sent', 'Credits Sent', 'Debits Received']
            values = [
                balance_data.get('credits_received', 0),
                balance_data.get('debits_sent', 0),
                balance_data.get('credits_sent', 0),
                balance_data.get('debits_received', 0)
            ]
            colors = ['green', 'red', 'lightgreen', 'salmon']

            bars = ax3.bar(labels, values, color=colors)
            ax3.set_title("Transaction Flow Summary", fontsize=10)
            ax3.set_ylabel("Amount (€)", fontsize=8)
            ax3.tick_params(axis='x', rotation=15, labelsize=7)
            ax3.tick_params(axis='y', labelsize=8)

            # Add labels above bars
            for bar in bars:
                 yval = bar.get_height()
                 if yval != 0: # Show only if > 0
                    ax3.text(bar.get_x() + bar.get_width()/2.0, yval, f'{yval:.2f}€', va='bottom', ha='center', fontsize=7) # va: vertical alignment

        else:
            ax3.text(0.5, 0.5, 'Balance data not available', horizontalalignment='center', verticalalignment='center')
            ax3.set_title("Transaction Flow Summary", fontsize=10)


        # --- Chart 4: Net vs Legacy Balance (Could be text or simple graphic) ---
        ax4 = axes[1, 1]
        ax4.axis('off') # Hide axes to just show text
        if balance_data:
             net_balance = balance_data.get('net', 0)
             legacy_balance = balance_data.get('legacy', None) # Assuming API provides it

             textstr = f'Net Balance: {net_balance:.2f} €\n(Credits Received - Debits Sent)\n\n'
             if legacy_balance is not None:
                 textstr += f'Legacy Balance: {legacy_balance:.2f} €\n(Total Credits - Total Debits)'

             ax4.text(0.5, 0.5, textstr, horizontalalignment='center', verticalalignment='center', fontsize=10, bbox=dict(boxstyle="round,pad=0.5", fc="wheat", alpha=0.5))
             ax4.set_title("Calculated Balances", fontsize=10, y=0.9) # Position title lower
        else:
             ax4.text(0.5, 0.5, 'Balance data not available', horizontalalignment='center', verticalalignment='center')
             ax4.set_title("Calculated Balances", fontsize=10)


        # --- Embed into Tkinter Canvas ---
        try:
            canvas = FigureCanvasTkAgg(fig, master=self.charts_container)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(fill=tk.BOTH, expand=True)
            canvas.draw()
        except Exception as e:
             print(f"Error rendering charts: {e}")
             messagebox.showerror("Chart Error", f"Could not display charts.\n{e}")
        finally:
             # Close the figure to free memory, even on error
             plt.close(fig)