import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
from datetime import datetime, timedelta
from tkcalendar import DateEntry
import pandas as pd

class ExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Expense Tracker")
        self.root.geometry("1000x600")
        
        # Initialize data structures
        self.expenses = []
        self.categories = ["Food", "Transportation", "Housing", "Entertainment", "Utilities", "Other"]
        
        # Load saved expenses
        self.load_expenses()
        
        # Create main container
        self.main_container = ttk.Notebook(root)
        self.main_container.pack(expand=True, fill="both", padx=10, pady=5)
        
        # Create tabs
        self.create_input_tab()
        self.create_view_tab()
        self.create_analysis_tab()
        
        # Update displays
        self.update_expense_tree()
        self.update_analysis()

    def create_input_tab(self):
        input_frame = ttk.Frame(self.main_container, padding="20")
        self.main_container.add(input_frame, text="Add Expense")
        
        # Expense Name
        ttk.Label(input_frame, text="Expense Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.name_entry = ttk.Entry(input_frame, width=30)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Amount
        ttk.Label(input_frame, text="Amount ($):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.amount_entry = ttk.Entry(input_frame, width=30)
        self.amount_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Category
        ttk.Label(input_frame, text="Category:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(input_frame, textvariable=self.category_var, 
                                         values=self.categories)
        self.category_combo.grid(row=2, column=1, padx=5, pady=5)
        
        # Date
        ttk.Label(input_frame, text="Date:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.date_picker = DateEntry(input_frame, width=27, background='darkblue', 
                                   foreground='white', date_pattern='yyyy-mm-dd')
        self.date_picker.grid(row=3, column=1, padx=5, pady=5)
        
        # Notes
        ttk.Label(input_frame, text="Notes:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.notes_entry = tk.Text(input_frame, width=30, height=4)
        self.notes_entry.grid(row=4, column=1, padx=5, pady=5)
        
        # Add Button
        ttk.Button(input_frame, text="Add Expense", command=self.add_expense).grid(row=5, column=0, columnspan=2, pady=20)

    def create_view_tab(self):
        view_frame = ttk.Frame(self.main_container, padding="20")
        self.main_container.add(view_frame, text="View Expenses")
        
        # Filter Frame
        filter_frame = ttk.LabelFrame(view_frame, text="Filters", padding="10")
        filter_frame.pack(fill="x", pady=5)
        
        # Category Filter
        ttk.Label(filter_frame, text="Category:").grid(row=0, column=0, padx=5, pady=5)
        self.filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var, 
                                  values=["All"] + self.categories)
        filter_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # Date Range Filter
        ttk.Label(filter_frame, text="Date Range:").grid(row=0, column=2, padx=5, pady=5)
        self.date_filter_var = tk.StringVar(value="All Time")
        date_filter_combo = ttk.Combobox(filter_frame, textvariable=self.date_filter_var, 
                                       values=["All Time", "Today", "This Week", "This Month", 
                                              "This Year", "Custom Range"])
        date_filter_combo.grid(row=0, column=3, padx=5, pady=5)
        
        # Custom Date Range
        self.start_date_label = ttk.Label(filter_frame, text="Start Date:")
        self.start_date_picker = DateEntry(filter_frame, width=12, background='darkblue', 
                                         foreground='white', date_pattern='yyyy-mm-dd')
        self.end_date_label = ttk.Label(filter_frame, text="End Date:")
        self.end_date_picker = DateEntry(filter_frame, width=12, background='darkblue', 
                                       foreground='white', date_pattern='yyyy-mm-dd')
        
        # Export Button
        ttk.Button(filter_frame, text="Export to Excel", 
                  command=self.export_to_excel).grid(row=0, column=6, padx=5, pady=5)
        
        # Bind filters
        self.date_filter_var.trace('w', self.on_date_filter_change)
        self.filter_var.trace('w', lambda *args: self.update_expense_tree())
        
        # Treeview
        columns = ("Date", "Name", "Amount", "Category", "Notes")
        self.tree = ttk.Treeview(view_frame, columns=columns, show="headings")
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(view_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons
        button_frame = ttk.Frame(view_frame)
        button_frame.pack(fill="x", pady=10)
        
        ttk.Button(button_frame, text="Delete Selected", 
                  command=self.delete_expense).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Edit Selected", 
                  command=self.edit_expense).pack(side="left", padx=5)

    def create_analysis_tab(self):
        analysis_frame = ttk.Frame(self.main_container, padding="20")
        self.main_container.add(analysis_frame, text="Analysis")
        
        # Create matplotlib figure
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(12, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=analysis_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Statistics Frame
        stats_frame = ttk.LabelFrame(analysis_frame, text="Statistics", padding="10")
        stats_frame.pack(fill="x", pady=10)
        
        self.stats_labels = {
            "total": ttk.Label(stats_frame, text="Total Expenses: $0"),
            "average": ttk.Label(stats_frame, text="Average Expense: $0"),
            "highest": ttk.Label(stats_frame, text="Highest Expense: $0"),
            "count": ttk.Label(stats_frame, text="Number of Expenses: 0")
        }
        
        for label in self.stats_labels.values():
            label.pack(anchor="w", pady=2)

    def add_expense(self):
        try:
            name = self.name_entry.get()
            amount = float(self.amount_entry.get())
            category = self.category_var.get()
            date = self.date_picker.get_date().strftime("%Y-%m-%d")
            notes = self.notes_entry.get("1.0", "end-1c")
            
            if name and category:
                expense = {
                    "name": name,
                    "amount": amount,
                    "category": category,
                    "date": date,
                    "notes": notes
                }
                self.expenses.append(expense)
                self.save_expenses()
                self.clear_inputs()
                self.update_expense_tree()
                self.update_analysis()
                messagebox.showinfo("Success", "Expense added successfully!")
            else:
                messagebox.showwarning("Input Error", "Please fill in all required fields.")
        except ValueError:
            messagebox.showwarning("Input Error", "Please enter a valid amount.")

    def edit_expense(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select an expense to edit.")
            return
        
        item = self.tree.item(selected[0])
        values = item['values']
        
        # Create edit window
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Expense")
        edit_window.geometry("300x400")
        
        # Edit fields
        ttk.Label(edit_window, text="Name:").pack(pady=5)
        name_entry = ttk.Entry(edit_window)
        name_entry.insert(0, values[1])
        name_entry.pack()
        
        ttk.Label(edit_window, text="Amount:").pack(pady=5)
        amount_entry = ttk.Entry(edit_window)
        amount_entry.insert(0, values[2].replace('$', ''))
        amount_entry.pack()
        
        ttk.Label(edit_window, text="Category:").pack(pady=5)
        category_var = tk.StringVar(value=values[3])
        category_combo = ttk.Combobox(edit_window, textvariable=category_var, 
                                    values=self.categories)
        category_combo.pack()
        
        ttk.Label(edit_window, text="Notes:").pack(pady=5)
        notes_entry = tk.Text(edit_window, height=4)
        notes_entry.insert("1.0", values[4])
        notes_entry.pack()
        
        def save_changes():
            try:
                # Find and update the expense in the list
                for expense in self.expenses:
                    if (expense['date'] == values[0] and 
                        expense['name'] == values[1] and 
                        expense['category'] == values[3]):
                        expense['name'] = name_entry.get()
                        expense['amount'] = float(amount_entry.get())
                        expense['category'] = category_var.get()
                        expense['notes'] = notes_entry.get("1.0", "end-1c")
                        break
                
                self.save_expenses()
                self.update_expense_tree()
                self.update_analysis()
                edit_window.destroy()
                messagebox.showinfo("Success", "Expense updated successfully!")
            except ValueError:
                messagebox.showwarning("Input Error", "Please enter a valid amount.")
        
        ttk.Button(edit_window, text="Save Changes", command=save_changes).pack(pady=20)

    def delete_expense(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select an expense to delete.")
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this expense?"):
            item = self.tree.item(selected[0])
            values = item['values']
            
            # Find and remove the expense
            for expense in self.expenses[:]:
                if (expense['date'] == values[0] and 
                    expense['name'] == values[1] and 
                    expense['category'] == values[3]):
                    self.expenses.remove(expense)
                    break
            
            self.save_expenses()
            self.update_expense_tree()
            self.update_analysis()

    def on_date_filter_change(self, *args):
        if self.date_filter_var.get() == "Custom Range":
            self.start_date_label.grid(row=1, column=2, padx=5, pady=5)
            self.start_date_picker.grid(row=1, column=3, padx=5, pady=5)
            self.end_date_label.grid(row=1, column=4, padx=5, pady=5)
            self.end_date_picker.grid(row=1, column=5, padx=5, pady=5)
        else:
            self.start_date_label.grid_remove()
            self.start_date_picker.grid_remove()
            self.end_date_label.grid_remove()
            self.end_date_picker.grid_remove()
        self.update_expense_tree()

    def get_date_filter_range(self):
        filter_type = self.date_filter_var.get()
        today = datetime.now().date()
        
        if filter_type == "All Time":
            return None, None
        elif filter_type == "Today":
            return today, today
        elif filter_type == "This Week":
            start = today - timedelta(days=today.weekday())
            return start, today
        elif filter_type == "This Month":
            start = today.replace(day=1)
            return start, today
        elif filter_type == "This Year":
            start = today.replace(month=1, day=1)
            return start, today
        elif filter_type == "Custom Range":
            return self.start_date_picker.get_date(), self.end_date_picker.get_date()
        return None, None

    def update_expense_tree(self):
        self.tree.delete(*self.tree.get_children())
        category_filter = self.filter_var.get()
        start_date, end_date = self.get_date_filter_range()
        
        filtered_expenses = []
        for expense in self.expenses:
            expense_date = datetime.strptime(expense['date'], "%Y-%m-%d").date()
            
            # Apply category filter
            if category_filter != "All" and expense['category'] != category_filter:
                continue
            
            # Apply date filter
            if start_date and end_date:
                if not (start_date <= expense_date <= end_date):
                    continue
            
            filtered_expenses.append(expense)
            self.tree.insert("", "end", values=(
                expense['date'],
                expense['name'],
                f"${expense['amount']:.2f}",
                expense['category'],
                                expense['notes']
            ))

    def update_analysis(self):
        if not self.expenses:
            self.ax1.clear()
            self.ax2.clear()
            self.canvas.draw()
            return

        # Prepare data
        df = pd.DataFrame(self.expenses)
        df['amount'] = df['amount'].astype(float)

        # Pie Chart - Expenses by Category
        category_summary = df.groupby('category')['amount'].sum()
        self.ax1.clear()
        self.ax1.pie(category_summary, labels=category_summary.index, autopct='%1.1f%%', startangle=140)
        self.ax1.set_title('Expenses by Category')

        # Bar Chart - Expenses Over Time
        df['date'] = pd.to_datetime(df['date'])
        date_summary = df.groupby(df['date'].dt.to_period('M'))['amount'].sum()
        self.ax2.clear()
        date_summary.plot(kind='bar', ax=self.ax2, color='skyblue')
        self.ax2.set_title('Monthly Expenses')
        self.ax2.set_xlabel('Date')
        self.ax2.set_ylabel('Amount ($)')

        self.canvas.draw()

        # Update Statistics
        total_expenses = df['amount'].sum()
        average_expense = df['amount'].mean()
        highest_expense = df['amount'].max()
        expense_count = len(df)

        self.stats_labels['total'].config(text=f"Total Expenses: ${total_expenses:.2f}")
        self.stats_labels['average'].config(text=f"Average Expense: ${average_expense:.2f}")
        self.stats_labels['highest'].config(text=f"Highest Expense: ${highest_expense:.2f}")
        self.stats_labels['count'].config(text=f"Number of Expenses: {expense_count}")

    def export_to_excel(self):
        if not self.expenses:
            messagebox.showwarning("No Data", "There are no expenses to export.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", 
                                                 filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
        if file_path:
            df = pd.DataFrame(self.expenses)
            df.to_excel(file_path, index=False)
            messagebox.showinfo("Success", "Expenses exported successfully!")

    def save_expenses(self):
        with open('expenses.json', 'w') as f:
            json.dump(self.expenses, f)

    def load_expenses(self):
        try:
            with open('expenses.json', 'r') as f:
                self.expenses = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.expenses = []

    def clear_inputs(self):
        self.name_entry.delete(0, tk.END)
        self.amount_entry.delete(0, tk.END)
        self.category_var.set("")
        self.date_picker.set_date(datetime.now())
        self.notes_entry.delete('1.0', tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTracker(root)
    root.mainloop()
