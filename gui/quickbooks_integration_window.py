"""
QuickBooks Integration GUI Window

Provides a comprehensive interface for connecting to QuickBooks Online,
syncing company data, managing accounts, and exporting tax data.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import webbrowser

from services.quickbooks_integration_service import (
    QuickBooksIntegrationService,
    QuickBooksCompany,
    QuickBooksAccount,
    QuickBooksTransaction,
    QuickBooksEntityType,
    AccountType,
    TaxCategory
)
from gui.theme_manager import ThemeManager


class QuickBooksIntegrationWindow:
    """Main window for QuickBooks integration functionality"""

    def __init__(self, parent: tk.Tk, theme_manager: ThemeManager):
        self.parent = parent
        self.theme_manager = theme_manager
        self.service = QuickBooksIntegrationService()

        # Window setup
        self.window = tk.Toplevel(parent)
        self.window.title("QuickBooks Integration")
        self.window.geometry("1200x800")
        self.window.configure(bg=theme_manager.get_bg_color())

        # Initialize variables
        self.selected_company: Optional[str] = None
        self.selected_account: Optional[str] = None
        self.selected_transaction: Optional[str] = None

        # Create main layout
        self._create_menu_bar()
        self._create_main_layout()
        self._create_status_bar()

        # Load initial data
        self._refresh_company_list()

        # Apply theme
        self.theme_manager.apply_theme_to_window(self.window)

    def _create_menu_bar(self):
        """Create the menu bar"""
        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Connect Company", command=self._connect_company)
        file_menu.add_command(label="Disconnect Company", command=self._disconnect_company)
        file_menu.add_separator()
        file_menu.add_command(label="Export Data", command=self._export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Close", command=self.window.destroy)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh All", command=self._refresh_all)
        view_menu.add_command(label="Sync Selected Company", command=self._sync_selected_company)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Generate Tax Report", command=self._generate_tax_report)
        tools_menu.add_command(label="Map Tax Categories", command=self._map_tax_categories)
        tools_menu.add_separator()
        tools_menu.add_command(label="Settings", command=self._show_settings)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="QuickBooks Setup Guide", command=self._show_setup_guide)
        help_menu.add_command(label="About", command=self._show_about)

    def _create_main_layout(self):
        """Create the main layout with paned windows"""
        # Create main paned window
        main_paned = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel - Company and Account lists
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)

        # Right panel - Transaction details and actions
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=2)

        self._create_left_panel(left_frame)
        self._create_right_panel(right_frame)

    def _create_left_panel(self, parent: ttk.Frame):
        """Create the left panel with company and account lists"""
        # Company section
        company_frame = ttk.LabelFrame(parent, text="Connected Companies")
        company_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Company listbox with scrollbar
        company_list_frame = ttk.Frame(company_frame)
        company_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        company_scrollbar = ttk.Scrollbar(company_list_frame)
        company_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.company_listbox = tk.Listbox(
            company_list_frame,
            yscrollcommand=company_scrollbar.set,
            selectmode=tk.SINGLE,
            bg=self.theme_manager.get_bg_color(),
            fg=self.theme_manager.get_fg_color()
        )
        self.company_listbox.pack(fill=tk.BOTH, expand=True)
        self.company_listbox.bind('<<ListboxSelect>>', self._on_company_select)

        company_scrollbar.config(command=self.company_listbox.yview)

        # Company buttons
        company_btn_frame = ttk.Frame(company_frame)
        company_btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(company_btn_frame, text="Connect", command=self._connect_company).pack(side=tk.LEFT, padx=2)
        ttk.Button(company_btn_frame, text="Disconnect", command=self._disconnect_company).pack(side=tk.LEFT, padx=2)
        ttk.Button(company_btn_frame, text="Sync", command=self._sync_selected_company).pack(side=tk.LEFT, padx=2)

        # Account section
        account_frame = ttk.LabelFrame(parent, text="Chart of Accounts")
        account_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Account treeview
        account_tree_frame = ttk.Frame(account_frame)
        account_tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("Type", "Balance", "Currency")
        self.account_tree = ttk.Treeview(account_tree_frame, columns=columns, show="headings", height=8)

        # Configure columns
        self.account_tree.heading("Type", text="Type")
        self.account_tree.heading("Balance", text="Balance")
        self.account_tree.heading("Currency", text="Currency")

        self.account_tree.column("Type", width=100)
        self.account_tree.column("Balance", width=100, anchor=tk.E)
        self.account_tree.column("Currency", width=60)

        # Add scrollbar
        account_scrollbar = ttk.Scrollbar(account_tree_frame, orient=tk.VERTICAL, command=self.account_tree.yview)
        self.account_tree.configure(yscrollcommand=account_scrollbar.set)

        self.account_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        account_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.account_tree.bind('<<TreeviewSelect>>', self._on_account_select)

    def _create_right_panel(self, parent: ttk.Frame):
        """Create the right panel with transaction details and actions"""
        # Transaction section
        transaction_frame = ttk.LabelFrame(parent, text="Transactions")
        transaction_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Transaction treeview
        trans_tree_frame = ttk.Frame(transaction_frame)
        trans_tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("Date", "Type", "Amount", "Description", "Account")
        self.transaction_tree = ttk.Treeview(trans_tree_frame, columns=columns, show="headings", height=15)

        # Configure columns
        self.transaction_tree.heading("Date", text="Date")
        self.transaction_tree.heading("Type", text="Type")
        self.transaction_tree.heading("Amount", text="Amount")
        self.transaction_tree.heading("Description", text="Description")
        self.transaction_tree.heading("Account", text="Account")

        self.transaction_tree.column("Date", width=100)
        self.transaction_tree.column("Type", width=80)
        self.transaction_tree.column("Amount", width=100, anchor=tk.E)
        self.transaction_tree.column("Description", width=200)
        self.transaction_tree.column("Account", width=150)

        # Add scrollbar
        trans_scrollbar = ttk.Scrollbar(trans_tree_frame, orient=tk.VERTICAL, command=self.transaction_tree.yview)
        self.transaction_tree.configure(yscrollcommand=trans_scrollbar.set)

        self.transaction_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        trans_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.transaction_tree.bind('<<TreeviewSelect>>', self._on_transaction_select)

        # Transaction filter controls
        filter_frame = ttk.Frame(transaction_frame)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=2)
        self.filter_var = tk.StringVar()
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var, width=15)
        filter_combo['values'] = ("All", "Income", "Expense", "Invoice", "Bill", "Payment")
        filter_combo.current(0)
        filter_combo.pack(side=tk.LEFT, padx=2)
        filter_combo.bind('<<ComboboxSelected>>', self._apply_transaction_filter)

        ttk.Button(filter_frame, text="Clear Filter", command=self._clear_transaction_filter).pack(side=tk.LEFT, padx=2)

        # Action buttons
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(action_frame, text="Generate Tax Report", command=self._generate_tax_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Map Tax Categories", command=self._map_tax_categories).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Export for Tax Software", command=self._export_data).pack(side=tk.LEFT, padx=5)

        # Details section
        details_frame = ttk.LabelFrame(parent, text="Details")
        details_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Details text area
        details_text_frame = ttk.Frame(details_frame)
        details_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        details_scrollbar = ttk.Scrollbar(details_text_frame)
        details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.details_text = tk.Text(
            details_text_frame,
            height=8,
            wrap=tk.WORD,
            yscrollcommand=details_scrollbar.set,
            bg=self.theme_manager.get_bg_color(),
            fg=self.theme_manager.get_fg_color()
        )
        self.details_text.pack(fill=tk.BOTH, expand=True)
        details_scrollbar.config(command=self.details_text.yview)

    def _create_status_bar(self):
        """Create the status bar"""
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.window, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _connect_company(self):
        """Connect a new QuickBooks company"""
        dialog = QuickBooksConnectionDialog(self.window, self.theme_manager)
        if dialog.result:
            company_name, realm_id = dialog.result
            try:
                company_id = self.service.authenticate_company(company_name, realm_id)
                self._refresh_company_list()
                self.status_var.set(f"Connected to {company_name}")
                messagebox.showinfo("Success", f"Successfully connected to {company_name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to connect company: {str(e)}")

    def _disconnect_company(self):
        """Disconnect the selected company"""
        if not self.selected_company:
            messagebox.showwarning("Warning", "Please select a company to disconnect")
            return

        company = self.service.companies.get(self.selected_company)
        if not company:
            return

        if messagebox.askyesno("Confirm", f"Disconnect {company.company_name}?"):
            try:
                self.service.disconnect_company(self.selected_company)
                self._refresh_company_list()
                self._clear_account_list()
                self._clear_transaction_list()
                self.selected_company = None
                self.status_var.set(f"Disconnected {company.company_name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to disconnect company: {str(e)}")

    def _sync_selected_company(self):
        """Sync the selected company"""
        if not self.selected_company:
            messagebox.showwarning("Warning", "Please select a company to sync")
            return

        company = self.service.companies.get(self.selected_company)
        if not company:
            return

        def sync_worker():
            try:
                self.status_var.set(f"Syncing {company.company_name}...")
                result = self.service.sync_company(self.selected_company)
                if result:
                    self._refresh_account_list()
                    self._refresh_transaction_list()
                    self.status_var.set(f"Successfully synced {company.company_name}")
                else:
                    self.status_var.set(f"Failed to sync {company.company_name}")
            except Exception as e:
                self.status_var.set(f"Sync error: {str(e)}")
                messagebox.showerror("Error", f"Failed to sync company: {str(e)}")

        threading.Thread(target=sync_worker, daemon=True).start()

    def _generate_tax_report(self):
        """Generate tax report for selected company"""
        if not self.selected_company:
            messagebox.showwarning("Warning", "Please select a company")
            return

        current_year = datetime.now().year
        try:
            report = self.service.generate_tax_report(self.selected_company, current_year)

            # Show report in details area
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(tk.END, f"TAX REPORT - {current_year}\n")
            self.details_text.insert(tk.END, "=" * 50 + "\n\n")

            self.details_text.insert(tk.END, f"Company: {report['company_id']}\n")
            self.details_text.insert(tk.END, f"Total Transactions: {report['total_transactions']}\n\n")

            self.details_text.insert(tk.END, "INCOME:\n")
            for category, amount in report['income'].items():
                self.details_text.insert(tk.END, f"  {category}: ${amount:,.2f}\n")

            self.details_text.insert(tk.END, "\nEXPENSES:\n")
            for category, amount in report['expenses'].items():
                self.details_text.insert(tk.END, f"  {category}: ${amount:,.2f}\n")

            self.details_text.insert(tk.END, "\nSUMMARY:\n")
            summary = report['summary']
            self.details_text.insert(tk.END, f"  Total Business Income: ${summary['total_business_income']:,.2f}\n")
            self.details_text.insert(tk.END, f"  Total Business Expenses: ${summary['total_business_expenses']:,.2f}\n")
            self.details_text.insert(tk.END, f"  Net Business Income: ${summary['net_business_income']:,.2f}\n")

            if report['requires_review']:
                self.details_text.insert(tk.END, "\n⚠️  Some transactions require manual review\n")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate tax report: {str(e)}")

    def _map_tax_categories(self):
        """Map transactions to tax categories"""
        if not self.selected_company:
            messagebox.showwarning("Warning", "Please select a company")
            return

        try:
            transactions = self.service.get_transactions(self.selected_company)
            if not transactions:
                messagebox.showinfo("Info", "No transactions to map")
                return

            results = self.service.map_to_tax_categories(transactions[:50])  # Limit for performance

            # Show mapping results in details area
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(tk.END, "TAX CATEGORY MAPPING RESULTS\n")
            self.details_text.insert(tk.END, "=" * 40 + "\n\n")

            for result in results:
                self.details_text.insert(tk.END, f"Transaction: {result.transaction_id}\n")
                self.details_text.insert(tk.END, f"Category: {result.suggested_category.value}\n")
                self.details_text.insert(tk.END, f"Confidence: {result.confidence_score:.2%}\n")
                self.details_text.insert(tk.END, f"Explanation: {result.explanation}\n\n")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to map tax categories: {str(e)}")

    def _export_data(self):
        """Export data for tax software"""
        if not self.selected_company:
            messagebox.showwarning("Warning", "Please select a company")
            return

        dialog = ExportDialog(self.window, self.theme_manager)
        if dialog.result:
            format_type, filename = dialog.result
            try:
                data = self.service.export_for_tax_software(self.selected_company, format_type)

                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(data)

                self.status_var.set(f"Exported data to {filename}")
                messagebox.showinfo("Success", f"Data exported successfully to {filename}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data: {str(e)}")

    def _refresh_all(self):
        """Refresh all data"""
        self._refresh_company_list()
        if self.selected_company:
            self._refresh_account_list()
            self._refresh_transaction_list()

    def _refresh_company_list(self):
        """Refresh the company list"""
        self.company_listbox.delete(0, tk.END)
        companies = self.service.get_companies()

        for company in companies:
            display_text = f"{company.company_name} ({company.realm_id})"
            if company.last_sync:
                display_text += f" - Last sync: {company.last_sync.strftime('%Y-%m-%d %H:%M')}"
            self.company_listbox.insert(tk.END, display_text)

            # Store company ID for later retrieval
            self.company_listbox.company_ids = getattr(self.company_listbox, 'company_ids', [])
            self.company_listbox.company_ids.append(company.company_id)

    def _refresh_account_list(self):
        """Refresh the account list for selected company"""
        if not self.selected_company:
            return

        # Clear existing items
        for item in self.account_tree.get_children():
            self.account_tree.delete(item)

        try:
            accounts = self.service.get_chart_of_accounts(self.selected_company)

            for account in accounts:
                self.account_tree.insert("", tk.END, values=(
                    account.account_type.value,
                    f"{account.balance:,.2f}",
                    account.currency or "USD"
                ), tags=(account.account_id,))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load accounts: {str(e)}")

    def _refresh_transaction_list(self):
        """Refresh the transaction list for selected company"""
        if not self.selected_company:
            return

        # Clear existing items
        for item in self.transaction_tree.get_children():
            self.transaction_tree.delete(item)

        try:
            transactions = self.service.get_transactions(self.selected_company)

            for transaction in transactions:
                self.transaction_tree.insert("", tk.END, values=(
                    transaction.date.strftime("%Y-%m-%d"),
                    transaction.transaction_type.value,
                    f"{transaction.amount:,.2f}",
                    transaction.description or "",
                    transaction.account_id
                ), tags=(transaction.transaction_id,))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load transactions: {str(e)}")

    def _clear_account_list(self):
        """Clear the account list"""
        for item in self.account_tree.get_children():
            self.account_tree.delete(item)

    def _clear_transaction_list(self):
        """Clear the transaction list"""
        for item in self.transaction_tree.get_children():
            self.transaction_tree.delete(item)

    def _on_company_select(self, event):
        """Handle company selection"""
        selection = self.company_listbox.curselection()
        if selection:
            index = selection[0]
            if hasattr(self.company_listbox, 'company_ids') and index < len(self.company_listbox.company_ids):
                self.selected_company = self.company_listbox.company_ids[index]
                self._refresh_account_list()
                self._refresh_transaction_list()

                company = self.service.companies.get(self.selected_company)
                if company:
                    self.status_var.set(f"Selected: {company.company_name}")

    def _on_account_select(self, event):
        """Handle account selection"""
        selection = self.account_tree.selection()
        if selection:
            item = selection[0]
            account_id = self.account_tree.item(item, 'tags')[0]
            self.selected_account = account_id

            # Show account details
            if self.selected_company:
                accounts = self.service.accounts.get(self.selected_company, [])
                account = next((acc for acc in accounts if acc.account_id == account_id), None)
                if account:
                    self._show_account_details(account)

    def _on_transaction_select(self, event):
        """Handle transaction selection"""
        selection = self.transaction_tree.selection()
        if selection:
            item = selection[0]
            transaction_id = self.transaction_tree.item(item, 'tags')[0]
            self.selected_transaction = transaction_id

            # Show transaction details
            if self.selected_company:
                transactions = self.service.transactions.get(self.selected_company, [])
                transaction = next((tx for tx in transactions if tx.transaction_id == transaction_id), None)
                if transaction:
                    self._show_transaction_details(transaction)

    def _apply_transaction_filter(self, event=None):
        """Apply transaction filter"""
        if not self.selected_company:
            return

        filter_value = self.filter_var.get()
        transactions = self.service.get_transactions(self.selected_company)

        # Clear current list
        for item in self.transaction_tree.get_children():
            self.transaction_tree.delete(item)

        # Apply filter
        filtered_transactions = []
        if filter_value == "All":
            filtered_transactions = transactions
        elif filter_value == "Income":
            filtered_transactions = [tx for tx in transactions if tx.amount > 0]
        elif filter_value == "Expense":
            filtered_transactions = [tx for tx in transactions if tx.amount < 0]
        else:
            # Filter by transaction type
            type_map = {
                "Invoice": QuickBooksEntityType.INVOICE,
                "Bill": QuickBooksEntityType.BILL,
                "Payment": QuickBooksEntityType.PAYMENT
            }
            if filter_value in type_map:
                filtered_transactions = [tx for tx in transactions if tx.transaction_type == type_map[filter_value]]

        # Display filtered transactions
        for transaction in filtered_transactions:
            self.transaction_tree.insert("", tk.END, values=(
                transaction.date.strftime("%Y-%m-%d"),
                transaction.transaction_type.value,
                f"{transaction.amount:,.2f}",
                transaction.description or "",
                transaction.account_id
            ), tags=(transaction.transaction_id,))

    def _clear_transaction_filter(self):
        """Clear transaction filter"""
        self.filter_var.set("All")
        self._refresh_transaction_list()

    def _show_account_details(self, account: QuickBooksAccount):
        """Show account details in the details area"""
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, f"ACCOUNT DETAILS\n")
        self.details_text.insert(tk.END, "=" * 20 + "\n\n")
        self.details_text.insert(tk.END, f"Account ID: {account.account_id}\n")
        self.details_text.insert(tk.END, f"Name: {account.name}\n")
        self.details_text.insert(tk.END, f"Type: {account.account_type.value}\n")
        if account.account_sub_type:
            self.details_text.insert(tk.END, f"Sub-Type: {account.account_sub_type}\n")
        self.details_text.insert(tk.END, f"Balance: ${account.balance:,.2f}\n")
        self.details_text.insert(tk.END, f"Currency: {account.currency or 'USD'}\n")
        self.details_text.insert(tk.END, f"Active: {'Yes' if account.is_active else 'No'}\n")

    def _show_transaction_details(self, transaction: QuickBooksTransaction):
        """Show transaction details in the details area"""
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, f"TRANSACTION DETAILS\n")
        self.details_text.insert(tk.END, "=" * 25 + "\n\n")
        self.details_text.insert(tk.END, f"Transaction ID: {transaction.transaction_id}\n")
        self.details_text.insert(tk.END, f"Type: {transaction.transaction_type.value}\n")
        self.details_text.insert(tk.END, f"Date: {transaction.date.strftime('%Y-%m-%d')}\n")
        self.details_text.insert(tk.END, f"Amount: ${transaction.amount:,.2f}\n")
        self.details_text.insert(tk.END, f"Description: {transaction.description or 'N/A'}\n")
        self.details_text.insert(tk.END, f"Account ID: {transaction.account_id}\n")
        if transaction.tax_amount:
            self.details_text.insert(tk.END, f"Tax Amount: ${transaction.tax_amount:,.2f}\n")
        self.details_text.insert(tk.END, f"Taxable: {'Yes' if transaction.is_taxable else 'No'}\n")

    def _show_settings(self):
        """Show settings dialog"""
        dialog = QuickBooksSettingsDialog(self.window, self.theme_manager, self.service)
        dialog.show()

    def _show_setup_guide(self):
        """Show QuickBooks setup guide"""
        guide_text = """
QuickBooks Integration Setup Guide
==================================

1. Create a QuickBooks Developer Account:
   - Go to https://developer.intuit.com/
   - Sign up for a developer account
   - Create a new app for your integration

2. Configure OAuth 2.0:
   - In your app settings, add your redirect URI
   - Note your Client ID and Client Secret

3. Connect Your Company:
   - Use the "Connect Company" button
   - Enter your Company Name and Realm ID
   - Follow the OAuth authentication flow

4. Sync Data:
   - Select your company from the list
   - Click "Sync" to import accounts and transactions

5. Export for Tax Software:
   - Use the "Export for Tax Software" option
   - Choose CSV or IIF format
   - Import the file into your tax preparation software

For more information, visit:
https://developer.intuit.com/app/developer/qbo/docs/get-started
        """

        # Create a new window for the guide
        guide_window = tk.Toplevel(self.window)
        guide_window.title("QuickBooks Setup Guide")
        guide_window.geometry("600x400")

        text_widget = tk.Text(guide_window, wrap=tk.WORD, padx=10, pady=10)
        scrollbar = ttk.Scrollbar(guide_window, command=text_widget.yview)
        text_widget.config(yscrollcommand=scrollbar.set)

        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget.insert(tk.END, guide_text)
        text_widget.config(state=tk.DISABLED)

    def _show_about(self):
        """Show about dialog"""
        about_text = """
QuickBooks Integration Module

Version: 1.0.0
Purpose: Connect QuickBooks Online to Freedom US Tax Return

Features:
- OAuth 2.0 authentication
- Chart of accounts synchronization
- Transaction import and categorization
- Tax report generation
- Export to CSV/IIF formats

For support, please contact the development team.
        """
        messagebox.showinfo("About QuickBooks Integration", about_text)


class QuickBooksConnectionDialog:
    """Dialog for connecting a new QuickBooks company"""

    def __init__(self, parent: tk.Tk, theme_manager: ThemeManager):
        self.parent = parent
        self.theme_manager = theme_manager
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Connect QuickBooks Company")
        self.dialog.geometry("400x200")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets()
        self.theme_manager.apply_theme_to_window(self.dialog)

        # Center the dialog
        self.dialog.geometry("+{}+{}".format(
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))

        self.dialog.wait_window()

    def _create_widgets(self):
        """Create dialog widgets"""
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # Company name
        ttk.Label(frame, text="Company Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.company_name_var = tk.StringVar()
        company_name_entry = ttk.Entry(frame, textvariable=self.company_name_var, width=30)
        company_name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)

        # Realm ID
        ttk.Label(frame, text="Realm ID:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.realm_id_var = tk.StringVar()
        realm_id_entry = ttk.Entry(frame, textvariable=self.realm_id_var, width=30)
        realm_id_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)

        # Help text
        help_text = "Enter your QuickBooks Company name and Realm ID.\nThe Realm ID can be found in your QuickBooks URL."
        help_label = ttk.Label(frame, text=help_text, wraplength=350, justify=tk.LEFT)
        help_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=10)

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Connect", command=self._on_connect).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side=tk.LEFT, padx=5)

        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self._on_connect())
        self.dialog.bind('<Escape>', lambda e: self._on_cancel())

    def _on_connect(self):
        """Handle connect button"""
        company_name = self.company_name_var.get().strip()
        realm_id = self.realm_id_var.get().strip()

        if not company_name or not realm_id:
            messagebox.showerror("Error", "Please enter both company name and realm ID")
            return

        self.result = (company_name, realm_id)
        self.dialog.destroy()

    def _on_cancel(self):
        """Handle cancel button"""
        self.result = None
        self.dialog.destroy()


class ExportDialog:
    """Dialog for export options"""

    def __init__(self, parent: tk.Tk, theme_manager: ThemeManager):
        self.parent = parent
        self.theme_manager = theme_manager
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Export Data")
        self.dialog.geometry("400x150")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets()
        self.theme_manager.apply_theme_to_window(self.dialog)

        # Center the dialog
        self.dialog.geometry("+{}+{}".format(
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))

        self.dialog.wait_window()

    def _create_widgets(self):
        """Create dialog widgets"""
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # Format selection
        ttk.Label(frame, text="Export Format:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.format_var = tk.StringVar(value="csv")
        format_combo = ttk.Combobox(frame, textvariable=self.format_var, width=10)
        format_combo['values'] = ("csv", "iif")
        format_combo.grid(row=0, column=1, sticky=tk.W, pady=5)

        # File selection
        ttk.Label(frame, text="Save As:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.filename_var = tk.StringVar()
        filename_entry = ttk.Entry(frame, textvariable=self.filename_var, width=30)
        filename_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)

        ttk.Button(frame, text="Browse...", command=self._browse_file).grid(row=1, column=2, padx=5)

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10)

        ttk.Button(button_frame, text="Export", command=self._on_export).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side=tk.LEFT, padx=5)

    def _browse_file(self):
        """Browse for save location"""
        format_type = self.format_var.get()
        extension = "csv" if format_type == "csv" else "iif"
        filename = filedialog.asksaveasfilename(
            defaultextension=f".{extension}",
            filetypes=[(f"{extension.upper()} files", f"*.{extension}"), ("All files", "*.*")]
        )
        if filename:
            self.filename_var.set(filename)

    def _on_export(self):
        """Handle export button"""
        format_type = self.format_var.get()
        filename = self.filename_var.get().strip()

        if not filename:
            messagebox.showerror("Error", "Please select a save location")
            return

        self.result = (format_type, filename)
        self.dialog.destroy()

    def _on_cancel(self):
        """Handle cancel button"""
        self.result = None
        self.dialog.destroy()


class QuickBooksSettingsDialog:
    """Dialog for QuickBooks settings"""

    def __init__(self, parent: tk.Tk, theme_manager: ThemeManager, service: QuickBooksIntegrationService):
        self.parent = parent
        self.theme_manager = theme_manager
        self.service = service

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("QuickBooks Settings")
        self.dialog.geometry("400x200")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets()
        self.theme_manager.apply_theme_to_window(self.dialog)

        # Center the dialog
        self.dialog.geometry("+{}+{}".format(
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))

    def _create_widgets(self):
        """Create dialog widgets"""
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # Environment selection
        ttk.Label(frame, text="Environment:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.env_var = tk.StringVar(value=self.service.environment)
        env_combo = ttk.Combobox(frame, textvariable=self.env_var, width=15)
        env_combo['values'] = ("sandbox", "production")
        env_combo.grid(row=0, column=1, sticky=tk.W, pady=5)

        # Auto-sync setting
        self.auto_sync_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Enable automatic sync", variable=self.auto_sync_var).grid(
            row=1, column=0, columnspan=2, sticky=tk.W, pady=5
        )

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Save", command=self._on_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side=tk.LEFT, padx=5)

    def _on_save(self):
        """Handle save button"""
        self.service.environment = self.env_var.get()
        # Note: Auto-sync would need additional implementation
        messagebox.showinfo("Settings", "Settings saved successfully")
        self.dialog.destroy()

    def _on_cancel(self):
        """Handle cancel button"""
        self.dialog.destroy()

    def show(self):
        """Show the dialog"""
        self.dialog.wait_window()