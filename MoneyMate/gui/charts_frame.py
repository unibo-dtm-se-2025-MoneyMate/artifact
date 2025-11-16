"""
Dashboard frame for visualizing MoneyMate financial data using charts.

This screen:

- Loads expenses, categories, and user balance breakdown via the API layer.
- Uses matplotlib to render:
  - Expenses by category (pie chart).
  - Expense trend over time (line chart).
  - Transaction flow summary (bar chart).
  - Net vs legacy balances (textual/graphical summary).
- Embeds the resulting figure into Tkinter using the TkAgg backend.

It is refreshed whenever the user navigates to the dashboard or logs in.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from collections import defaultdict
import importlib
from datetime import datetime

from MoneyMate.data_layer.api import api_get_expenses, api_get_user_balance_breakdown, api_get_categories

class ChartsFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style='Content.TFrame')
        self.controller = controller

        ttk.Label(self, text="Financial Dashboard", style='Header.TLabel', background=self.controller.FRAME_COLOR).pack(pady=10, anchor='w', padx=10)

        # Frame to contain the charts
        self.charts_container = ttk.Frame(self, style='Content.TFrame')
        self.charts_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def refresh(self):
        """Generate and display the charts."""
        def _parse_date(date_str):
            if not date_str:
                raise ValueError("empty date")
            fmts = ('%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S')
            for f in fmts:
                try:
                    return datetime.strptime(date_str, f)
                except Exception:
                    continue
            try:
                return datetime.strptime(date_str.split(' ')[0], '%Y-%m-%d')
            except Exception:
                raise
        
        if not self.controller.user_id:
            for widget in self.charts_container.winfo_children():
                widget.destroy()
            ttk.Label(self.charts_container, text="Please log in to see the dashboard.", style='Title.TLabel', background=self.controller.FRAME_COLOR).pack(pady=20)
            return

        for widget in self.charts_container.winfo_children():
            widget.destroy()

        # --- Get Style Colors ---
        BG_COLOR = self.controller.FRAME_COLOR # Chart background
        TEXT_COLOR = self.controller.TEXT_COLOR
        PRIMARY_COLOR = self.controller.PRIMARY_COLOR
        PRIMARY_DARK = self.controller.PRIMARY_DARK
        GRID_COLOR = '#E0E0E0'

        # --- Data for Charts ---
        expenses_data = []
        balance_data = None
        category_id_to_name = {}

        # 1. Load categories
        cat_result = api_get_categories(self.controller.user_id)
        if cat_result["success"]:
            category_id_to_name = {cat['id']: cat['name'] for cat in cat_result["data"]}
        else:
            print("Warning: Could not load categories for charts.")

        # 2. Load expenses
        exp_result = api_get_expenses(user_id=self.controller.user_id, limit=1000)
        if exp_result["success"]:
            expenses_data = exp_result["data"]
        else:
            messagebox.showerror("Chart Data Error", f"Could not load expenses: {exp_result['error']}")

        # 3. Load balance
        bal_result = api_get_user_balance_breakdown(self.controller.user_id)
        if bal_result["success"]:
            balance_data = bal_result["data"]
        else:
            messagebox.showerror("Chart Data Error", f"Could not load balance data: {bal_result['error']}")

        if not expenses_data and not balance_data:
             ttk.Label(self.charts_container, text="No data available for charts.", style='Title.TLabel', background=self.controller.FRAME_COLOR).pack(pady=20)
             return

        # --- Chart Creation ---
        try:
            plt = importlib.import_module('matplotlib.pyplot')
            mdates = importlib.import_module('matplotlib.dates')
            
            # Style settings to match app
            plt.rcParams.update({
                'font.family': 'sans-serif',
                'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Helvetica'],
                'font.size': 9,
                'axes.facecolor': BG_COLOR,
                'axes.edgecolor': GRID_COLOR,
                'axes.labelcolor': TEXT_COLOR,
                'axes.titlecolor': PRIMARY_DARK,
                'figure.facecolor': BG_COLOR,
                'figure.edgecolor': BG_COLOR,
                'xtick.color': TEXT_COLOR,
                'ytick.color': TEXT_COLOR,
                'text.color': TEXT_COLOR,
                'grid.color': GRID_COLOR,
                'patch.edgecolor': BG_COLOR
            })
        except Exception as e:
            print(f"matplotlib not available: {e}")
            ttk.Label(self.charts_container, text="Charts cannot be displayed (matplotlib missing)").pack(pady=10)
            return

        fig, axes = plt.subplots(2, 2, figsize=(10, 8))
        fig.subplots_adjust(hspace=0.5, wspace=0.3)

        # --- Chart 1: Expenses by Category (Pie) ---
        ax1 = axes[0, 0]
        if expenses_data:
            expenses_by_category = defaultdict(float)
            for exp in expenses_data:
                cat_id = exp.get("category_id")
                category_name = category_id_to_name.get(cat_id, exp.get("category", "Uncategorized"))
                try:
                    expenses_by_category[category_name] += float(exp.get("price", 0))
                except (ValueError, TypeError):
                    continue

            if expenses_by_category:
                labels = list(expenses_by_category.keys())
                sizes = list(expenses_by_category.values())
                colors = plt.cm.Dark2.colors 
                ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, textprops={'fontsize': 8, 'color': TEXT_COLOR}, colors=colors)
                ax1.set_title("Expenses by Category", fontsize=12, fontweight='bold')
            else:
                ax1.text(0.5, 0.5, 'No expenses found', horizontalalignment='center', verticalalignment='center', color=TEXT_COLOR)
                ax1.set_title("Expenses by Category", fontsize=12, fontweight='bold')
            ax1.axis('equal')
        else:
             ax1.text(0.5, 0.5, 'Expense data not available', horizontalalignment='center', verticalalignment='center', color=TEXT_COLOR)
             ax1.set_title("Expenses by Category", fontsize=12, fontweight='bold')

        # --- Chart 2: Expense Trend Over Time (Line) ---
        ax2 = axes[0, 1]
        if expenses_data:
            expenses_by_date = defaultdict(float)
            for exp in expenses_data:
                try:
                    date_obj = _parse_date(exp.get("date"))
                    expenses_by_date[date_obj.date()] += float(exp.get("price", 0)) # Aggregate by day
                except (ValueError, TypeError, KeyError):
                    continue

            if expenses_by_date:
                sorted_dates = sorted(expenses_by_date.keys())
                amounts = [expenses_by_date[d] for d in sorted_dates]

                ax2.plot(sorted_dates, amounts, marker='o', linestyle='-', color=PRIMARY_COLOR, markersize=4)
                ax2.set_title("Expense Trend Over Time", fontsize=12, fontweight='bold')
                ax2.set_ylabel("Amount (€)", fontsize=9)
                ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
                fig.autofmt_xdate(rotation=30, ha='right')
                ax2.tick_params(axis='x', labelsize=8)
                ax2.tick_params(axis='y', labelsize=8)
                ax2.grid(True, linestyle='--', alpha=0.6)
                ax2.set_facecolor(self.controller.FRAME_COLOR)
            else:
                 ax2.text(0.5, 0.5, 'No valid expenses found', horizontalalignment='center', verticalalignment='center', color=TEXT_COLOR)
                 ax2.set_title("Expense Trend Over Time", fontsize=12, fontweight='bold')
        else:
             ax2.text(0.5, 0.5, 'Expense data not available', horizontalalignment='center', verticalalignment='center', color=TEXT_COLOR)
             ax2.set_title("Expense Trend Over Time", fontsize=12, fontweight='bold')

        # --- Chart 3: Balance Summary (Bar) ---
        ax3 = axes[1, 0]
        if balance_data:
            labels = ['Credits Recv.', 'Debits Sent', 'Credits Sent', 'Debits Recv.']
            def _num(v):
                try: return float(v)
                except Exception: return 0.0

            values = [
                _num(balance_data.get('credits_received', 0)),
                _num(balance_data.get('debits_sent', 0)),
                _num(balance_data.get('credits_sent', 0)),
                _num(balance_data.get('debits_received', 0))
            ]
            colors = [self.controller.SUCCESS_COLOR, self.controller.ERROR_COLOR, '#AED581', '#FFAB91']

            bars = ax3.bar(labels, values, color=colors)
            ax3.set_title("Transaction Flow Summary", fontsize=12, fontweight='bold')
            ax3.set_ylabel("Amount (€)", fontsize=9)
            ax3.tick_params(axis='x', rotation=15, labelsize=8)
            ax3.grid(True, axis='y', linestyle='--', alpha=0.6)
            ax3.set_facecolor(self.controller.FRAME_COLOR)

            for bar in bars:
                 yval = bar.get_height()
                 if yval > 0:
                    ax3.text(bar.get_x() + bar.get_width()/2.0, yval, f'{yval:.2f}€', va='bottom', ha='center', fontsize=8, color=TEXT_COLOR)
        else:
            ax3.text(0.5, 0.5, 'Balance data not available', horizontalalignment='center', verticalalignment='center', color=TEXT_COLOR)
            ax3.set_title("Transaction Flow Summary", fontsize=12, fontweight='bold')

        # --- Chart 4: Net vs Legacy Balance ---
        ax4 = axes[1, 1]
        ax4.axis('off')
        if balance_data:
             net_balance = balance_data.get('net', 0)
             legacy_balance = balance_data.get('legacy', None)

             net_color = self.controller.SUCCESS_COLOR if net_balance >= 0 else self.controller.ERROR_COLOR
             
             ax4.set_title("Calculated Balances", fontsize=12, fontweight='bold', y=0.95)
             
             ax4.text(0.5, 0.65, f"{net_balance:,.2f} €", horizontalalignment='center', verticalalignment='center', fontsize=18, fontweight='bold', color=net_color)
             ax4.text(0.5, 0.55, "Net Balance", horizontalalignment='center', verticalalignment='center', fontsize=10, color=TEXT_COLOR)
             ax4.text(0.5, 0.45, "(Credits Received - Debits Sent)", horizontalalignment='center', verticalalignment='center', fontsize=8, color=self.controller.MUTED_TEXT)
             
             if legacy_balance is not None:
                 legacy_color = self.controller.SUCCESS_COLOR if legacy_balance >= 0 else self.controller.ERROR_COLOR
                 ax4.text(0.5, 0.25, f"{legacy_balance:,.2f} €", horizontalalignment='center', verticalalignment='center', fontsize=14, color=legacy_color)
                 ax4.text(0.5, 0.15, "Legacy Balance", horizontalalignment='center', verticalalignment='center', fontsize=10, color=TEXT_COLOR)
                 ax4.text(0.5, 0.05, "(Total Credits - Total Debits)", horizontalalignment='center', verticalalignment='center', fontsize=8, color=self.controller.MUTED_TEXT)
        else:
             ax4.text(0.5, 0.5, 'Balance data not available', horizontalalignment='center', verticalalignment='center', color=TEXT_COLOR)
             ax4.set_title("Calculated Balances", fontsize=12, fontweight='bold')

        # --- Embed into Tkinter Canvas ---
        try:
            backend_mod = importlib.import_module('matplotlib.backends.backend_tkagg')
            FigureCanvasTkAgg = getattr(backend_mod, 'FigureCanvasTkAgg')
        except Exception as e:
            print(f"matplotlib TkAgg backend not available: {e}")
            for widget in self.charts_container.winfo_children():
                widget.destroy()
            ttk.Label(self.charts_container, text="Charts cannot be displayed (missing Tk backend)").pack(pady=10)
            plt.close(fig)
            return

        try:
            canvas = FigureCanvasTkAgg(fig, master=self.charts_container)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(fill=tk.BOTH, expand=True)
            canvas.draw()
        except Exception as e:
            print(f"Error rendering charts: {e}")
            messagebox.showerror("Chart Error", f"Could not display charts.\n{e}")
        finally:
            plt.close(fig)