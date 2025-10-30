# main_app.py

import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import os
from datetime import datetime
from typing import List, Dict
import pandas as pd


class Transaction:
    """Represents a financial transaction with full metadata."""
    
    def __init__(self, description: str, amount: float, transaction_type: str, 
                 category: str = "Other", date: str = None, transaction_id: int = None):
        self.description = description
        self.amount = float(amount)
        self.transaction_type = transaction_type
        self.category = category
        self.date = date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.transaction_id = transaction_id or id(self)
    
    def to_dict(self) -> Dict:
        """Convert transaction to dictionary for JSON serialization."""
        return {
            'id': self.transaction_id,
            'description': self.description,
            'amount': self.amount,
            'type': self.transaction_type,
            'category': self.category,
            'date': self.date
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Transaction':
        """Create transaction from dictionary."""
        return cls(
            description=data['description'],
            amount=data['amount'],
            transaction_type=data['type'],
            category=data.get('category', 'Other'),
            date=data.get('date'),
            transaction_id=data.get('id')
        )


class Budget:
    """Manages all transactions with persistence and analytics."""
    
    CATEGORIES = {
        'Income': ['Salary', 'Freelance', 'Investment', 'Gift', 'Other'],
        'Expense': ['Food', 'Transportation', 'Utilities', 'Entertainment', 
                    'Healthcare', 'Shopping', 'Education', 'Other']
    }
    
    def __init__(self, data_file: str = "budget_data.json"):
        self.transactions: List[Transaction] = []
        self.data_file = data_file
        self.load_data()
    
    def add_transaction(self, transaction: Transaction) -> None:
        """Add a transaction and save to file."""
        self.transactions.append(transaction)
        self.save_data()
    
    def remove_transaction(self, transaction_id: int) -> bool:
        """Remove a transaction by ID."""
        initial_length = len(self.transactions)
        self.transactions = [t for t in self.transactions if t.transaction_id != transaction_id]
        if len(self.transactions) < initial_length:
            self.save_data()
            return True
        return False
    
    def update_transaction(self, transaction_id: int, updated_data: Dict) -> bool:
        """Update an existing transaction."""
        for transaction in self.transactions:
            if transaction.transaction_id == transaction_id:
                transaction.description = updated_data.get('description', transaction.description)
                transaction.amount = float(updated_data.get('amount', transaction.amount))
                transaction.transaction_type = updated_data.get('type', transaction.transaction_type)
                transaction.category = updated_data.get('category', transaction.category)
                self.save_data()
                return True
        return False
    
    def get_summary(self) -> Dict:
        """Calculate financial summary using NumPy."""
        if not self.transactions:
            return {
                'total_income': 0.0,
                'total_expense': 0.0,
                'balance': 0.0,
                'transaction_count': 0,
                'avg_income': 0.0,
                'avg_expense': 0.0
            }
        
        income_amounts = [t.amount for t in self.transactions if t.transaction_type == 'Income']
        expense_amounts = [t.amount for t in self.transactions if t.transaction_type == 'Expense']
        
        income_array = np.array(income_amounts) if income_amounts else np.array([0])
        expense_array = np.array(expense_amounts) if expense_amounts else np.array([0])
        
        total_income = float(np.sum(income_array))
        total_expense = float(np.sum(expense_array))
        
        return {
            'total_income': total_income,
            'total_expense': total_expense,
            'balance': total_income - total_expense,
            'transaction_count': len(self.transactions),
            'avg_income': float(np.mean(income_array)),
            'avg_expense': float(np.mean(expense_array))
        }
    
    def get_expense_by_category(self) -> Dict[str, float]:
        """Get expenses grouped by category."""
        category_totals = {}
        for transaction in self.transactions:
            if transaction.transaction_type == 'Expense':
                category = transaction.category
                category_totals[category] = category_totals.get(category, 0) + transaction.amount
        return category_totals
    
    def save_data(self) -> None:
        """Save all transactions to JSON file."""
        try:
            data = [t.to_dict() for t in self.transactions]
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def load_data(self) -> None:
        """Load transactions from JSON file."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.transactions = [Transaction.from_dict(t) for t in data]
            except Exception as e:
                print(f"Error loading data: {e}")
                self.transactions = []
    
    def export_to_csv(self, filepath: str) -> bool:
        """Export transactions to CSV file."""
        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Date', 'Description', 'Type', 'Category', 'Amount'])
                for t in self.transactions:
                    writer.writerow([t.date, t.description, t.transaction_type, t.category, t.amount])
            return True
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False


class BudgetApp:
    """Main application with enhanced GUI and features."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Personal Budget Manager Pro")
        self.root.geometry("1200x700")
        self.root.configure(bg="#f5f5f5")
        
        # Apply modern theme
        style = ttk.Style()
        style.theme_use('clam')
        
        self.budget = Budget()
        self.current_chart_type = "bar"  # 'bar' or 'pie'
        
        self._setup_ui()
        self.update_dashboard()
    
    def _setup_ui(self) -> None:
        """Setup the complete user interface."""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export to CSV", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle Chart Type", command=self.toggle_chart)
        
        # Main container with two columns
        main_container = tk.Frame(self.root, bg="#f5f5f5")
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel
        left_panel = tk.Frame(main_container, bg="#f5f5f5")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Right panel
        right_panel = tk.Frame(main_container, bg="#f5f5f5")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Setup left panel components
        self._setup_input_frame(left_panel)
        self._setup_summary_frame(left_panel)
        self._setup_transaction_list(left_panel)
        
        # Setup right panel components
        self._setup_chart_frame(right_panel)
    
    def _setup_input_frame(self, parent: tk.Frame) -> None:
        """Setup the transaction input form."""
        input_frame = tk.LabelFrame(parent, text="Add New Transaction", padx=15, pady=15, 
                                    bg="white", font=('Arial', 10, 'bold'))
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Description
        tk.Label(input_frame, text="Description:", bg="white", font=('Arial', 9)).grid(
            row=0, column=0, padx=5, pady=5, sticky='w')
        self.desc_entry = tk.Entry(input_frame, width=35, font=('Arial', 9))
        self.desc_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        
        # Amount
        tk.Label(input_frame, text="Amount ($):", bg="white", font=('Arial', 9)).grid(
            row=1, column=0, padx=5, pady=5, sticky='w')
        self.amount_entry = tk.Entry(input_frame, width=35, font=('Arial', 9))
        self.amount_entry.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        
        # Type
        tk.Label(input_frame, text="Type:", bg="white", font=('Arial', 9)).grid(
            row=2, column=0, padx=5, pady=5, sticky='w')
        self.type_var = tk.StringVar(value="Expense")
        self.type_menu = ttk.Combobox(input_frame, textvariable=self.type_var, 
                                      values=["Income", "Expense"], state="readonly", 
                                      width=33, font=('Arial', 9))
        self.type_menu.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        self.type_menu.bind("<<ComboboxSelected>>", self._on_type_change)
        
        # Category
        tk.Label(input_frame, text="Category:", bg="white", font=('Arial', 9)).grid(
            row=3, column=0, padx=5, pady=5, sticky='w')
        self.category_var = tk.StringVar(value="Other")
        self.category_menu = ttk.Combobox(input_frame, textvariable=self.category_var, 
                                          values=Budget.CATEGORIES['Expense'], 
                                          state="readonly", width=33, font=('Arial', 9))
        self.category_menu.grid(row=3, column=1, padx=5, pady=5, sticky='ew')
        
        # Buttons frame
        btn_frame = tk.Frame(input_frame, bg="white")
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        add_btn = tk.Button(btn_frame, text="Add Transaction", command=self.add_transaction,
                           bg="#4CAF50", fg="white", font=('Arial', 9, 'bold'),
                           padx=20, pady=5, cursor="hand2")
        add_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = tk.Button(btn_frame, text="Clear Fields", command=self._clear_fields,
                             bg="#2196F3", fg="white", font=('Arial', 9, 'bold'),
                             padx=20, pady=5, cursor="hand2")
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        input_frame.columnconfigure(1, weight=1)
    
    def _setup_summary_frame(self, parent: tk.Frame) -> None:
        """Setup the financial summary display."""
        summary_frame = tk.LabelFrame(parent, text="Financial Summary", padx=15, pady=15,
                                      bg="white", font=('Arial', 10, 'bold'))
        summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create labels for summary data
        self.summary_labels = {}
        labels_info = [
            ('total_income', 'Total Income:', '#4CAF50'),
            ('total_expense', 'Total Expense:', '#F44336'),
            ('balance', 'Current Balance:', '#2196F3'),
            ('transaction_count', 'Total Transactions:', '#FF9800')
        ]
        
        for idx, (key, label_text, color) in enumerate(labels_info):
            frame = tk.Frame(summary_frame, bg="white")
            frame.pack(fill=tk.X, pady=2)
            
            tk.Label(frame, text=label_text, bg="white", font=('Arial', 9, 'bold'),
                    fg="#333").pack(side=tk.LEFT)
            
            value_label = tk.Label(frame, text="$0.00", bg="white", 
                                  font=('Arial', 9, 'bold'), fg=color)
            value_label.pack(side=tk.RIGHT)
            self.summary_labels[key] = value_label
    
    def _setup_transaction_list(self, parent: tk.Frame) -> None:
        """Setup the transaction history list."""
        list_frame = tk.LabelFrame(parent, text="Transaction History", padx=10, pady=10,
                                   bg="white", font=('Arial', 10, 'bold'))
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview with scrollbar
        tree_scroll = ttk.Scrollbar(list_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.transaction_tree = ttk.Treeview(list_frame, yscrollcommand=tree_scroll.set,
                                            selectmode='browse', height=10)
        self.transaction_tree.pack(fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.transaction_tree.yview)
        
        # Define columns
        self.transaction_tree['columns'] = ('Date', 'Description', 'Type', 'Category', 'Amount')
        self.transaction_tree.column('#0', width=0, stretch=tk.NO)
        self.transaction_tree.column('Date', width=130, anchor='w')
        self.transaction_tree.column('Description', width=150, anchor='w')
        self.transaction_tree.column('Type', width=80, anchor='center')
        self.transaction_tree.column('Category', width=100, anchor='w')
        self.transaction_tree.column('Amount', width=100, anchor='e')
        
        # Define headings
        self.transaction_tree.heading('Date', text='Date', anchor='w')
        self.transaction_tree.heading('Description', text='Description', anchor='w')
        self.transaction_tree.heading('Type', text='Type', anchor='center')
        self.transaction_tree.heading('Category', text='Category', anchor='w')
        self.transaction_tree.heading('Amount', text='Amount', anchor='e')
        
        # Buttons for transaction management
        btn_frame = tk.Frame(list_frame, bg="white")
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        delete_btn = tk.Button(btn_frame, text="Delete Selected", command=self.delete_transaction,
                              bg="#F44336", fg="white", font=('Arial', 8, 'bold'),
                              padx=10, pady=3, cursor="hand2")
        delete_btn.pack(side=tk.LEFT, padx=2)
        
        refresh_btn = tk.Button(btn_frame, text="Refresh", command=self.refresh_transaction_list,
                               bg="#9E9E9E", fg="white", font=('Arial', 8, 'bold'),
                               padx=10, pady=3, cursor="hand2")
        refresh_btn.pack(side=tk.LEFT, padx=2)
    
    def _setup_chart_frame(self, parent: tk.Frame) -> None:
        """Setup the chart display area."""
        self.chart_frame = tk.LabelFrame(parent, text="Visual Analytics", padx=10, pady=10,
                                         bg="white", font=('Arial', 10, 'bold'))
        self.chart_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create matplotlib figure
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(6, 8), dpi=90)
        self.fig.tight_layout(pad=3.0)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _on_type_change(self, event=None) -> None:
        """Update category options when transaction type changes."""
        trans_type = self.type_var.get()
        categories = Budget.CATEGORIES.get(trans_type, ['Other'])
        self.category_menu['values'] = categories
        self.category_var.set(categories[0])
    
    def _clear_fields(self) -> None:
        """Clear all input fields."""
        self.desc_entry.delete(0, tk.END)
        self.amount_entry.delete(0, tk.END)
        self.type_var.set("Expense")
        self.category_var.set("Other")
        self._on_type_change()
    
    def add_transaction(self) -> None:
        """Add a new transaction with validation."""
        description = self.desc_entry.get().strip()
        amount_str = self.amount_entry.get().strip()
        trans_type = self.type_var.get()
        category = self.category_var.get()
        
        # Validation
        if not description:
            messagebox.showerror("Validation Error", "Description cannot be empty.")
            return
        
        if not amount_str:
            messagebox.showerror("Validation Error", "Amount cannot be empty.")
            return
        
        try:
            amount = float(amount_str)
            if amount <= 0:
                messagebox.showerror("Validation Error", "Amount must be greater than 0.")
                return
        except ValueError:
            messagebox.showerror("Validation Error", "Please enter a valid number for amount.")
            return
        
        # Create and add transaction
        new_transaction = Transaction(description, amount, trans_type, category)
        self.budget.add_transaction(new_transaction)
        
        self._clear_fields()
        self.update_dashboard()
        messagebox.showinfo("Success", "Transaction added successfully!")
    
    def delete_transaction(self) -> None:
        """Delete the selected transaction."""
        selected = self.transaction_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a transaction to delete.")
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this transaction?"):
            item = self.transaction_tree.item(selected[0])
            transaction_id = item['values'][0] if item['values'] else None
            
            if transaction_id and self.budget.remove_transaction(transaction_id):
                self.update_dashboard()
                messagebox.showinfo("Success", "Transaction deleted successfully!")
            else:
                messagebox.showerror("Error", "Failed to delete transaction.")
    
    def refresh_transaction_list(self) -> None:
        """Refresh the transaction list display."""
        # Clear existing items
        for item in self.transaction_tree.get_children():
            self.transaction_tree.delete(item)
        
        # Add all transactions
        for transaction in reversed(self.budget.transactions):
            amount_str = f"${transaction.amount:.2f}"
            if transaction.transaction_type == 'Expense':
                amount_str = f"-{amount_str}"
            
            self.transaction_tree.insert('', 'end', values=(
                transaction.transaction_id,
                transaction.date[:16],
                transaction.description[:30],
                transaction.transaction_type,
                transaction.category,
                amount_str
            ))
    
    def update_dashboard(self) -> None:
        """Update all dashboard components."""
        summary = self.budget.get_summary()
        
        # Update summary labels
        self.summary_labels['total_income'].config(text=f"${summary['total_income']:.2f}")
        self.summary_labels['total_expense'].config(text=f"${summary['total_expense']:.2f}")
        
        balance = summary['balance']
        balance_color = '#4CAF50' if balance >= 0 else '#F44336'
        self.summary_labels['balance'].config(text=f"${balance:.2f}", fg=balance_color)
        self.summary_labels['transaction_count'].config(text=str(summary['transaction_count']))
        
        # Update transaction list
        self.refresh_transaction_list()
        
        # Update charts
        self._update_charts(summary)
    
    def _update_charts(self, summary: Dict) -> None:
        """Update both chart displays."""
        # Clear previous plots
        self.ax1.clear()
        self.ax2.clear()
        
        # Chart 1: Income vs Expense Bar Chart
        labels = ['Income', 'Expense']
        values = [summary['total_income'], summary['total_expense']]
        colors = ['#4CAF50', '#F44336']
        
        bars = self.ax1.bar(labels, values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
        self.ax1.set_ylabel('Amount ($)', fontsize=10, fontweight='bold')
        self.ax1.set_title('Income vs. Expense Overview', fontsize=11, fontweight='bold')
        self.ax1.grid(axis='y', alpha=0.3, linestyle='--')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            self.ax1.text(bar.get_x() + bar.get_width()/2., height,
                         f'${height:.2f}',
                         ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # Chart 2: Expense by Category Pie Chart
        expense_by_category = self.budget.get_expense_by_category()
        
        if expense_by_category:
            categories = list(expense_by_category.keys())
            amounts = list(expense_by_category.values())
            
            colors_pie = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#BB8FCE', '#85C1E2']
            wedges, texts, autotexts = self.ax2.pie(amounts, labels=categories, autopct='%1.1f%%',
                                                     colors=colors_pie[:len(categories)], startangle=90)
            
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(8)
            
            self.ax2.set_title('Expense Breakdown by Category', fontsize=11, fontweight='bold')
        else:
            self.ax2.text(0.5, 0.5, 'No expense data available', 
                         ha='center', va='center', fontsize=10)
            self.ax2.set_xlim(0, 1)
            self.ax2.set_ylim(0, 1)
        
        self.canvas.draw()
    
    def toggle_chart(self) -> None:
        """Toggle between different chart views."""
        self.update_dashboard()
        messagebox.showinfo("Chart Updated", "Chart view has been refreshed!")
    
    def export_data(self) -> None:
        """Export transaction data to CSV."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Transactions to CSV"
        )
        
        if filepath:
            if self.budget.export_to_csv(filepath):
                messagebox.showinfo("Export Successful", f"Data exported to:\n{filepath}")
            else:
                messagebox.showerror("Export Failed", "Failed to export data to CSV.")


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = BudgetApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()