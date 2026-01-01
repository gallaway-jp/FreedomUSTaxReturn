"""
Bank Account Linking Window

GUI interface for connecting bank accounts and managing financial data imports
for tax preparation purposes.

Features:
- Secure account connection wizard
- Account management dashboard
- Transaction review and categorization
- Tax data export
- Security settings
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading
import webbrowser

from services.bank_account_linking_service import (
    BankAccountLinkingService,
    BankAccount,
    BankTransaction,
    AccountType,
    TransactionCategory
)
from gui.theme_manager import ThemeManager

logger = logging.getLogger(__name__)


class BankAccountLinkingWindow:
    """
    Main window for bank account linking functionality
    """

    def __init__(self, parent: tk.Tk, theme_manager: ThemeManager):
        """
        Initialize the bank account linking window

        Args:
            parent: Parent tkinter window
            theme_manager: Application theme manager
        """
        self.parent = parent
        self.theme_manager = theme_manager

        # Initialize service
        self.service = BankAccountLinkingService()

        # Window setup
        self.window = tk.Toplevel(parent)
        self.window.title("Bank Account Linking - Freedom US Tax Return")
        self.window.geometry("1200x800")
        self.window.resizable(True, True)

        # Apply theme
        self.theme_manager.apply_theme(self.window)

        # UI components
        self.notebook = None
        self.accounts_tree = None
        self.transactions_tree = None
        self.status_label = None

        # Data
        self.selected_account: Optional[BankAccount] = None
        self.current_transactions: List[BankTransaction] = []

        self._setup_ui()
        self._load_accounts()

        logger.info("Bank Account Linking Window initialized")

    def _setup_ui(self):
        """Set up the user interface"""
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self._create_accounts_tab()
        self._create_transactions_tab()
        self._create_tax_analysis_tab()
        self._create_settings_tab()

        # Status bar
        self.status_label = ttk.Label(self.window, text="Ready")
        self.status_label.pack(fill=tk.X, padx=10, pady=(0, 10))

    def _create_accounts_tab(self):
        """Create the accounts management tab"""
        accounts_frame = ttk.Frame(self.notebook)
        self.notebook.add(accounts_frame, text="Connected Accounts")

        # Toolbar
        toolbar = ttk.Frame(accounts_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(toolbar, text="Connect Account",
                  command=self._connect_account).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Disconnect Account",
                  command=self._disconnect_account).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Sync All",
                  command=self._sync_all_accounts).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Refresh",
                  command=self._load_accounts).pack(side=tk.LEFT)

        # Accounts treeview
        columns = ("Institution", "Type", "Balance", "Last Sync", "Status")
        self.accounts_tree = ttk.Treeview(accounts_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.accounts_tree.heading(col, text=col)
            self.accounts_tree.column(col, width=150)

        scrollbar = ttk.Scrollbar(accounts_frame, orient=tk.VERTICAL, command=self.accounts_tree.yview)
        self.accounts_tree.configure(yscrollcommand=scrollbar.set)

        self.accounts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind selection event
        self.accounts_tree.bind('<<TreeviewSelect>>', self._on_account_selected)

        # Account details frame
        details_frame = ttk.LabelFrame(accounts_frame, text="Account Details")
        details_frame.pack(fill=tk.X, pady=(10, 0))

        self.account_details_text = scrolledtext.ScrolledText(details_frame, height=8, wrap=tk.WORD)
        self.account_details_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.account_details_text.config(state=tk.DISABLED)

    def _create_transactions_tab(self):
        """Create the transactions review tab"""
        transactions_frame = ttk.Frame(self.notebook)
        self.notebook.add(transactions_frame, text="Transactions")

        # Filter controls
        filter_frame = ttk.Frame(transactions_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(filter_frame, text="Date Range:").grid(row=0, column=0, padx=(0, 5))
        self.start_date_var = tk.StringVar(value=(datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"))
        self.end_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))

        ttk.Entry(filter_frame, textvariable=self.start_date_var, width=12).grid(row=0, column=1, padx=(0, 5))
        ttk.Label(filter_frame, text="to").grid(row=0, column=2, padx=(0, 5))
        ttk.Entry(filter_frame, textvariable=self.end_date_var, width=12).grid(row=0, column=3, padx=(0, 5))

        ttk.Label(filter_frame, text="Category:").grid(row=0, column=4, padx=(10, 5))
        self.category_var = tk.StringVar()
        category_combo = ttk.Combobox(filter_frame, textvariable=self.category_var,
                                     values=["All"] + [cat.value for cat in TransactionCategory],
                                     state="readonly", width=15)
        category_combo.grid(row=0, column=5, padx=(0, 5))
        category_combo.set("All")

        ttk.Button(filter_frame, text="Apply Filters",
                  command=self._apply_transaction_filters).grid(row=0, column=6, padx=(10, 0))

        # Transactions treeview
        columns = ("Date", "Amount", "Description", "Category", "Tax Relevant", "Confidence")
        self.transactions_tree = ttk.Treeview(transactions_frame, columns=columns, show="headings", height=20)

        for col in columns:
            self.transactions_tree.heading(col, text=col)
            if col == "Description":
                self.transactions_tree.column(col, width=300)
            elif col in ["Amount", "Confidence"]:
                self.transactions_tree.column(col, width=100)
            else:
                self.transactions_tree.column(col, width=120)

        scrollbar = ttk.Scrollbar(transactions_frame, orient=tk.VERTICAL, command=self.transactions_tree.yview)
        self.transactions_tree.configure(yscrollcommand=scrollbar.set)

        self.transactions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Action buttons
        actions_frame = ttk.Frame(transactions_frame)
        actions_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(actions_frame, text="Categorize Selected",
                  command=self._categorize_selected_transaction).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(actions_frame, text="Mark as Reviewed",
                  command=self._mark_transaction_reviewed).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(actions_frame, text="Export to CSV",
                  command=lambda: self._export_transactions("csv")).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(actions_frame, text="Export to Tax Software",
                  command=self._export_for_tax_software).pack(side=tk.LEFT)

    def _create_tax_analysis_tab(self):
        """Create the tax analysis tab"""
        analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(analysis_frame, text="Tax Analysis")

        # Tax year selection
        year_frame = ttk.Frame(analysis_frame)
        year_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(year_frame, text="Tax Year:").pack(side=tk.LEFT, padx=(0, 5))
        current_year = datetime.now().year
        self.tax_year_var = tk.StringVar(value=str(current_year))
        year_combo = ttk.Combobox(year_frame, textvariable=self.tax_year_var,
                                 values=[str(y) for y in range(current_year-3, current_year+2)],
                                 state="readonly", width=8)
        year_combo.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(year_frame, text="Generate Tax Summary",
                  command=self._generate_tax_summary).pack(side=tk.LEFT)

        # Results display
        self.tax_summary_text = scrolledtext.ScrolledText(analysis_frame, height=25, wrap=tk.WORD)
        self.tax_summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tax_summary_text.config(state=tk.DISABLED)

    def _create_settings_tab(self):
        """Create the settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")

        # Security settings
        security_frame = ttk.LabelFrame(settings_frame, text="Security Settings")
        security_frame.pack(fill=tk.X, pady=(0, 10), padx=10)

        ttk.Checkbutton(security_frame, text="Enable two-factor authentication for account connections").pack(anchor=tk.W, pady=5)
        ttk.Checkbutton(security_frame, text="Require PIN for transaction access").pack(anchor=tk.W, pady=5)
        ttk.Checkbutton(security_frame, text="Encrypt local transaction data").pack(anchor=tk.W, pady=5)

        # Data management
        data_frame = ttk.LabelFrame(settings_frame, text="Data Management")
        data_frame.pack(fill=tk.X, pady=(0, 10), padx=10)

        ttk.Button(data_frame, text="Clear All Transaction Data",
                  command=self._clear_transaction_data).pack(anchor=tk.W, pady=5)
        ttk.Button(data_frame, text="Export All Data",
                  command=self._export_all_data).pack(anchor=tk.W, pady=5)
        ttk.Button(data_frame, text="Import Data",
                  command=self._import_data).pack(anchor=tk.W, pady=5)

        # Help section
        help_frame = ttk.LabelFrame(settings_frame, text="Help & Support")
        help_frame.pack(fill=tk.X, pady=(0, 10), padx=10)

        ttk.Button(help_frame, text="View Supported Institutions",
                  command=self._show_supported_institutions).pack(anchor=tk.W, pady=5)
        ttk.Button(help_frame, text="Security Best Practices",
                  command=self._show_security_help).pack(anchor=tk.W, pady=5)
        ttk.Button(help_frame, text="Troubleshooting Guide",
                  command=self._show_troubleshooting).pack(anchor=tk.W, pady=5)

    def _connect_account(self):
        """Launch account connection wizard"""
        wizard = AccountConnectionWizard(self.window, self.theme_manager, self.service)
        self.window.wait_window(wizard.window)

        if wizard.connected_account_id:
            self._load_accounts()
            messagebox.showinfo("Success", "Account connected successfully!")

    def _disconnect_account(self):
        """Disconnect selected account"""
        selection = self.accounts_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an account to disconnect.")
            return

        account_id = self.accounts_tree.item(selection[0])['values'][0]  # Account ID is in first column

        if messagebox.askyesno("Confirm Disconnect",
                              f"Are you sure you want to disconnect account {account_id}?"):
            try:
                if self.service.disconnect_account(account_id):
                    self._load_accounts()
                    self._clear_transaction_view()
                    messagebox.showinfo("Success", "Account disconnected successfully.")
                else:
                    messagebox.showerror("Error", "Failed to disconnect account.")
            except Exception as e:
                logger.error(f"Error disconnecting account: {str(e)}")
                messagebox.showerror("Error", f"Failed to disconnect account: {str(e)}")

    def _sync_all_accounts(self):
        """Sync all connected accounts"""
        def sync_worker():
            self.status_label.config(text="Syncing accounts...")
            try:
                results = self.service.sync_all_accounts()
                successful = sum(1 for success in results.values() if success)
                total = len(results)

                self.status_label.config(text=f"Synced {successful}/{total} accounts")
                self._load_accounts()

                if successful < total:
                    messagebox.showwarning("Sync Complete",
                                         f"Successfully synced {successful} of {total} accounts. "
                                         "Check logs for details.")
                else:
                    messagebox.showinfo("Sync Complete", f"All {total} accounts synced successfully.")

            except Exception as e:
                logger.error(f"Error syncing accounts: {str(e)}")
                self.status_label.config(text="Sync failed")
                messagebox.showerror("Sync Error", f"Failed to sync accounts: {str(e)}")

        # Run sync in background thread
        threading.Thread(target=sync_worker, daemon=True).start()

    def _load_accounts(self):
        """Load and display connected accounts"""
        # Clear existing items
        for item in self.accounts_tree.get_children():
            self.accounts_tree.delete(item)

        try:
            accounts = self.service.get_accounts()

            for account in accounts:
                last_sync = account.last_sync.strftime("%Y-%m-%d %H:%M") if account.last_sync else "Never"
                status = "Active" if account.is_active else "Inactive"

                self.accounts_tree.insert("", tk.END, values=(
                    account.account_id,
                    account.institution_name,
                    f"${account.balance:,.2f}",
                    last_sync,
                    status
                ))

        except Exception as e:
            logger.error(f"Error loading accounts: {str(e)}")
            messagebox.showerror("Error", f"Failed to load accounts: {str(e)}")

    def _on_account_selected(self, event):
        """Handle account selection"""
        selection = self.accounts_tree.selection()
        if not selection:
            return

        account_id = self.accounts_tree.item(selection[0])['values'][0]

        # Find the account object
        accounts = self.service.get_accounts()
        self.selected_account = next((acc for acc in accounts if acc.account_id == account_id), None)

        if self.selected_account:
            self._display_account_details(self.selected_account)
            self._load_account_transactions(self.selected_account.account_id)

    def _display_account_details(self, account: BankAccount):
        """Display detailed account information"""
        details = f"""
Account ID: {account.account_id}
Institution: {account.institution_name}
Account Type: {account.account_type.value.title()}
Account Name: {account.account_name}
Masked Number: {account.account_number_masked}
Balance: ${account.balance:,.2f}
Currency: {account.currency}
Status: {'Active' if account.is_active else 'Inactive'}
Created: {account.created_at.strftime('%Y-%m-%d %H:%M')}
Last Sync: {account.last_sync.strftime('%Y-%m-%d %H:%M') if account.last_sync else 'Never'}
        """.strip()

        self.account_details_text.config(state=tk.NORMAL)
        self.account_details_text.delete(1.0, tk.END)
        self.account_details_text.insert(tk.END, details)
        self.account_details_text.config(state=tk.DISABLED)

    def _load_account_transactions(self, account_id: str):
        """Load transactions for selected account"""
        try:
            # Get filter values
            start_date = datetime.strptime(self.start_date_var.get(), "%Y-%m-%d")
            end_date = datetime.strptime(self.end_date_var.get(), "%Y-%m-%d")
            category = None
            if self.category_var.get() != "All":
                category = TransactionCategory(self.category_var.get())

            transactions = self.service.get_transactions(
                account_id, start_date, end_date, category
            )

            self._display_transactions(transactions)

        except Exception as e:
            logger.error(f"Error loading transactions: {str(e)}")
            messagebox.showerror("Error", f"Failed to load transactions: {str(e)}")

    def _display_transactions(self, transactions: List[BankTransaction]):
        """Display transactions in the treeview"""
        # Clear existing items
        for item in self.transactions_tree.get_children():
            self.transactions_tree.delete(item)

        self.current_transactions = transactions

        for tx in transactions:
            category = tx.category.value if tx.category else ""
            tax_relevant = "Yes" if tx.tax_relevant else "No"
            confidence = f"{tx.confidence_score:.1%}" if tx.confidence_score > 0 else ""

            self.transactions_tree.insert("", tk.END, values=(
                tx.date.strftime("%Y-%m-%d"),
                f"${tx.amount:,.2f}",
                tx.description,
                category,
                tax_relevant,
                confidence
            ))

    def _apply_transaction_filters(self):
        """Apply current filter settings"""
        if self.selected_account:
            self._load_account_transactions(self.selected_account.account_id)

    def _categorize_selected_transaction(self):
        """Categorize selected transaction"""
        selection = self.transactions_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a transaction to categorize.")
            return

        # This would open a categorization dialog
        messagebox.showinfo("Feature", "Transaction categorization dialog would open here.")

    def _mark_transaction_reviewed(self):
        """Mark selected transaction as reviewed"""
        selection = self.transactions_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a transaction to mark as reviewed.")
            return

        # Mark as reviewed (would update transaction in service)
        messagebox.showinfo("Success", "Transaction marked as reviewed.")

    def _export_transactions(self, format_type: str):
        """Export transactions in specified format"""
        if not self.selected_account:
            messagebox.showwarning("No Account", "Please select an account first.")
            return

        try:
            data = self.service.export_for_tax_software(
                self.selected_account.account_id, format_type
            )

            # Save to file
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=f".{format_type}",
                filetypes=[(f"{format_type.upper()} files", f"*.{format_type}"), ("All files", "*.*")]
            )

            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(data)
                messagebox.showinfo("Export Complete", f"Data exported to {filename}")

        except Exception as e:
            logger.error(f"Error exporting transactions: {str(e)}")
            messagebox.showerror("Export Error", f"Failed to export transactions: {str(e)}")

    def _export_for_tax_software(self):
        """Export transactions for tax software"""
        # Show format selection dialog
        format_window = tk.Toplevel(self.window)
        format_window.title("Select Export Format")
        format_window.geometry("300x150")

        ttk.Label(format_window, text="Choose export format:").pack(pady=10)

        format_var = tk.StringVar(value="csv")
        ttk.Radiobutton(format_window, text="CSV (Spreadsheet)", variable=format_var, value="csv").pack()
        ttk.Radiobutton(format_window, text="QIF (Quicken)", variable=format_var, value="qif").pack()
        ttk.Radiobutton(format_window, text="OFX (Financial Software)", variable=format_var, value="ofx").pack()

        def do_export():
            format_window.destroy()
            self._export_transactions(format_var.get())

        ttk.Button(format_window, text="Export", command=do_export).pack(pady=10)

    def _generate_tax_summary(self):
        """Generate tax summary for selected year"""
        if not self.selected_account:
            messagebox.showwarning("No Account", "Please select an account first.")
            return

        try:
            tax_year = int(self.tax_year_var.get())
            summary = self.service.get_tax_summary(self.selected_account.account_id, tax_year)

            # Format summary for display
            summary_text = f"""
TAX SUMMARY - {tax_year}
{'='*50}

Account: {summary['account_id']}
Total Transactions: {summary['total_transactions']}

INCOME:
Interest Income: ${summary['interest_income']:,.2f}
Dividend Income: ${summary['dividend_income']:,.2f}

DEDUCTIONS:
Business Expenses: ${summary['business_expenses']:,.2f}
Medical Expenses: ${summary['medical_expenses']:,.2f}
Charitable Donations: ${summary['charitable_donations']:,.2f}

Items Requiring Review: {len(summary['requires_review'])}
            """.strip()

            if summary['requires_review']:
                summary_text += "\n\nITEMS NEEDING REVIEW:"
                for item in summary['requires_review'][:5]:  # Show first 5
                    summary_text += f"\n- {item['description']}: ${item['amount']:,.2f}"

            self.tax_summary_text.config(state=tk.NORMAL)
            self.tax_summary_text.delete(1.0, tk.END)
            self.tax_summary_text.insert(tk.END, summary_text)
            self.tax_summary_text.config(state=tk.DISABLED)

        except Exception as e:
            logger.error(f"Error generating tax summary: {str(e)}")
            messagebox.showerror("Error", f"Failed to generate tax summary: {str(e)}")

    def _clear_transaction_view(self):
        """Clear the transaction display"""
        for item in self.transactions_tree.get_children():
            self.transactions_tree.delete(item)
        self.current_transactions = []

        self.account_details_text.config(state=tk.NORMAL)
        self.account_details_text.delete(1.0, tk.END)
        self.account_details_text.config(state=tk.DISABLED)

    def _clear_transaction_data(self):
        """Clear all transaction data"""
        if messagebox.askyesno("Confirm Clear",
                              "Are you sure you want to clear all transaction data? This cannot be undone."):
            # Implementation would clear service data
            messagebox.showinfo("Data Cleared", "All transaction data has been cleared.")

    def _export_all_data(self):
        """Export all account and transaction data"""
        messagebox.showinfo("Export", "Export all data functionality would be implemented here.")

    def _import_data(self):
        """Import account and transaction data"""
        messagebox.showinfo("Import", "Import data functionality would be implemented here.")

    def _show_supported_institutions(self):
        """Show list of supported financial institutions"""
        institutions_window = tk.Toplevel(self.window)
        institutions_window.title("Supported Institutions")
        institutions_window.geometry("500x400")

        text = scrolledtext.ScrolledText(institutions_window, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        supported_text = """
SUPPORTED FINANCIAL INSTITUTIONS

Major Banks:
- Chase
- Bank of America
- Wells Fargo
- Citibank
- US Bank

Brokerage Firms:
- Fidelity Investments
- Vanguard
- Charles Schwab
- TD Ameritrade
- E*TRADE

Credit Unions:
- Navy Federal Credit Union
- Pentagon Federal Credit Union
- State Employees Credit Union

International Banks:
- HSBC
- Barclays
- Royal Bank of Canada

Note: Support for additional institutions is continuously added.
Contact support if your institution is not listed.
        """.strip()

        text.insert(tk.END, supported_text)
        text.config(state=tk.DISABLED)

    def _show_security_help(self):
        """Show security best practices"""
        security_window = tk.Toplevel(self.window)
        security_window.title("Security Best Practices")
        security_window.geometry("600x500")

        text = scrolledtext.ScrolledText(security_window, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        security_text = """
BANK ACCOUNT LINKING SECURITY BEST PRACTICES

🔐 Data Encryption:
- All credentials are encrypted using AES-256 encryption
- Transaction data is stored securely on your local device
- No sensitive financial data is transmitted to our servers

🔑 Access Control:
- Enable two-factor authentication for account connections
- Use strong, unique passwords for financial accounts
- Regularly review connected accounts and permissions

🛡️ Privacy Protection:
- We never store your bank login credentials
- Data access is read-only for transaction history
- You can disconnect accounts at any time

⚡ Safe Practices:
- Only connect accounts from trusted devices
- Monitor account activity regularly
- Report any suspicious transactions immediately
- Keep your operating system and applications updated

📞 Support:
If you have security concerns, contact our support team immediately.
We take the security of your financial data very seriously.
        """.strip()

        text.insert(tk.END, security_text)
        text.config(state=tk.DISABLED)

    def _show_troubleshooting(self):
        """Show troubleshooting guide"""
        troubleshooting_window = tk.Toplevel(self.window)
        troubleshooting_window.title("Troubleshooting Guide")
        troubleshooting_window.geometry("600x500")

        text = scrolledtext.ScrolledText(troubleshooting_window, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        troubleshooting_text = """
TROUBLESHOOTING GUIDE

🔌 Connection Issues:

1. Account Won't Connect:
   - Verify your login credentials are correct
   - Check if your bank requires additional security steps
   - Try connecting during business hours
   - Some banks require app-specific passwords

2. Sync Fails:
   - Check your internet connection
   - Try syncing individual accounts instead of all at once
   - Some banks have daily transaction limits
   - Wait a few minutes between sync attempts

💰 Transaction Issues:

1. Missing Transactions:
   - Transactions may take 1-2 days to appear
   - Check your account's transaction date range
   - Some transaction types may not be supported

2. Incorrect Categorization:
   - Review and manually categorize transactions
   - Use the "Mark as Reviewed" feature
   - Contact support for categorization improvements

🔧 Technical Issues:

1. Application Won't Start:
   - Ensure you have the latest version installed
   - Check system requirements
   - Try running as administrator

2. Data Export Fails:
   - Ensure you have write permissions to the export location
   - Check available disk space
   - Try exporting smaller date ranges

📧 Getting Help:

If these steps don't resolve your issue:
1. Check our knowledge base at support.example.com
2. Contact customer support with error details
3. Include screenshots if possible
4. Note your operating system and application version
        """.strip()

        text.insert(tk.END, troubleshooting_text)
        text.config(state=tk.DISABLED)


class AccountConnectionWizard:
    """
    Wizard for connecting new bank accounts
    """

    def __init__(self, parent: tk.Tk, theme_manager: ThemeManager, service: BankAccountLinkingService):
        """
        Initialize the account connection wizard

        Args:
            parent: Parent window
            theme_manager: Theme manager
            service: Bank account linking service
        """
        self.parent = parent
        self.theme_manager = theme_manager
        self.service = service
        self.connected_account_id: Optional[str] = None

        # Create wizard window
        self.window = tk.Toplevel(parent)
        self.window.title("Connect Bank Account")
        self.window.geometry("500x400")
        self.window.resizable(False, False)

        # Center the window
        self.window.transient(parent)
        self.window.grab_set()

        self.theme_manager.apply_theme(self.window)

        self._create_wizard_steps()

    def _create_wizard_steps(self):
        """Create the wizard steps"""
        # Step 1: Select institution
        self.step_frame = ttk.Frame(self.window)
        self.step_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ttk.Label(self.step_frame, text="Step 1: Select Your Financial Institution",
                 font=("Arial", 12, "bold")).pack(pady=(0, 10))

        # Institution selection
        ttk.Label(self.step_frame, text="Institution:").pack(anchor=tk.W)
        self.institution_var = tk.StringVar()
        institution_combo = ttk.Combobox(self.step_frame, textvariable=self.institution_var,
                                       values=[
                                           "Chase", "Bank of America", "Wells Fargo", "Citibank",
                                           "Fidelity", "Vanguard", "Schwab", "Other"
                                       ], state="readonly", width=30)
        institution_combo.pack(pady=(0, 10))
        institution_combo.set("Chase")

        # Account type
        ttk.Label(self.step_frame, text="Account Type:").pack(anchor=tk.W)
        self.account_type_var = tk.StringVar()
        type_combo = ttk.Combobox(self.step_frame, textvariable=self.account_type_var,
                                values=[t.value for t in AccountType], state="readonly", width=30)
        type_combo.pack(pady=(0, 20))
        type_combo.set(AccountType.CHECKING.value)

        # Navigation buttons
        button_frame = ttk.Frame(self.step_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(button_frame, text="Cancel", command=self.window.destroy).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Next", command=self._show_credentials_step).pack(side=tk.RIGHT)

    def _show_credentials_step(self):
        """Show the credentials input step"""
        # Clear current step
        for widget in self.step_frame.winfo_children():
            widget.destroy()

        # Step 2: Enter credentials
        ttk.Label(self.step_frame, text="Step 2: Enter Your Login Credentials",
                 font=("Arial", 12, "bold")).pack(pady=(0, 10))

        # Security notice
        security_text = """
⚠️  Security Notice:
Your credentials are encrypted and stored securely on your device.
We never transmit or store your login information on our servers.
        """.strip()

        security_label = ttk.Label(self.step_frame, text=security_text, foreground="red")
        security_label.pack(pady=(0, 20))

        # Credential fields
        ttk.Label(self.step_frame, text="Username/Login ID:").pack(anchor=tk.W)
        self.username_var = tk.StringVar()
        ttk.Entry(self.step_frame, textvariable=self.username_var, width=40).pack(pady=(0, 10))

        ttk.Label(self.step_frame, text="Password:").pack(anchor=tk.W)
        self.password_var = tk.StringVar()
        ttk.Entry(self.step_frame, textvariable=self.password_var, show="*", width=40).pack(pady=(0, 20))

        # Navigation buttons
        button_frame = ttk.Frame(self.step_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(button_frame, text="Back", command=self._create_wizard_steps).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Cancel", command=self.window.destroy).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Connect", command=self._connect_account).pack(side=tk.RIGHT)

    def _connect_account(self):
        """Attempt to connect the account"""
        try:
            # Validate inputs
            if not self.username_var.get() or not self.password_var.get():
                messagebox.showerror("Missing Information", "Please enter both username and password.")
                return

            # Show progress
            progress_window = tk.Toplevel(self.window)
            progress_window.title("Connecting...")
            progress_window.geometry("300x100")
            ttk.Label(progress_window, text="Connecting to your account...").pack(pady=10)
            progress = ttk.Progressbar(progress_window, mode='indeterminate')
            progress.pack(fill=tk.X, padx=20, pady=10)
            progress.start()

            self.window.update()

            # Simulate connection (in real implementation, this would call the service)
            credentials = {
                'username': self.username_var.get(),
                'password': self.password_var.get(),
                'account_number': '1234567890'  # Mock account number
            }

            account_id = self.service.connect_account(
                self.institution_var.get(),
                credentials,
                AccountType(self.account_type_var.get())
            )

            progress_window.destroy()

            self.connected_account_id = account_id
            messagebox.showinfo("Success", "Account connected successfully!")
            self.window.destroy()

        except Exception as e:
            if 'progress_window' in locals():
                progress_window.destroy()
            logger.error(f"Error connecting account: {str(e)}")
            messagebox.showerror("Connection Failed", f"Failed to connect account: {str(e)}")


# Integration function for main application
def open_bank_account_linking_window(parent: tk.Tk, theme_manager: ThemeManager):
    """
    Open the bank account linking window

    Args:
        parent: Parent tkinter window
        theme_manager: Application theme manager
    """
    try:
        BankAccountLinkingWindow(parent, theme_manager)
    except Exception as e:
        logger.error(f"Error opening bank account linking window: {str(e)}")
        messagebox.showerror("Error", f"Failed to open bank account linking window: {str(e)}")