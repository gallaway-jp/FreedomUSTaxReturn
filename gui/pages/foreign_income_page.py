"""
Foreign Income and FBAR Reporting Page

Page for managing foreign income and FBAR (Foreign Bank Account Report) requirements.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, List
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.foreign_income_fbar_service import (
    ForeignIncomeFBARService,
    ForeignAccount,
    ForeignIncome,
    ForeignAccountType,
    FBARThreshold
)


class ForeignIncomePage(ttk.Frame):
    """
    Page for foreign income and FBAR reporting.

    Allows users to:
    - Add/edit/delete foreign financial accounts
    - Track foreign income sources
    - Generate FBAR filing summaries
    - Calculate foreign tax credits
    """

    def __init__(self, parent, tax_data: TaxData, main_window, config: AppConfig):
        super().__init__(parent)
        self.tax_data = tax_data
        self.main_window = main_window
        self.config = config

        # Initialize service
        self.fbar_service = ForeignIncomeFBARService(config)

        # UI components
        self.accounts_tree = None
        self.income_tree = None
        self.summary_labels = {}

        self.build_ui()
        self.load_data()

    def build_ui(self):
        """Build the page UI"""
        # Create main container with padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 10))

        title_label = ttk.Label(
            header_frame,
            text="Foreign Income & FBAR Reporting",
            font=("Arial", 16, "bold")
        )
        title_label.pack(anchor="w")

        description_label = ttk.Label(
            header_frame,
            text="Report foreign financial accounts and income sources. FBAR filing may be required if aggregate foreign account values exceed $10,000.",
            wraplength=700,
            justify="left"
        )
        description_label.pack(anchor="w", pady=(5, 0))

        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True, pady=(10, 0))

        # Foreign Accounts tab
        accounts_frame = ttk.Frame(notebook)
        notebook.add(accounts_frame, text="Foreign Accounts")

        self.build_accounts_tab(accounts_frame)

        # Foreign Income tab
        income_frame = ttk.Frame(notebook)
        notebook.add(income_frame, text="Foreign Income")

        self.build_income_tab(income_frame)

        # FBAR Summary tab
        summary_frame = ttk.Frame(notebook)
        notebook.add(summary_frame, text="FBAR Summary")

        self.build_summary_tab(summary_frame)

    def build_accounts_tab(self, parent):
        """Build the foreign accounts tab"""
        # Toolbar
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill="x", pady=(0, 10))

        ttk.Button(
            toolbar,
            text="Add Account",
            command=self.add_account
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Edit Selected",
            command=self.edit_selected_account
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Delete Selected",
            command=self.delete_selected_account
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            toolbar,
            text="FBAR Instructions",
            command=self.show_fbar_instructions
        ).pack(side="right")

        # Accounts treeview
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill="both", expand=True)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal")

        self.accounts_tree = ttk.Treeview(
            tree_frame,
            columns=("number", "institution", "type", "country", "currency", "max_value", "end_value", "status"),
            show="headings",
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )

        # Configure columns
        self.accounts_tree.heading("number", text="Account Number")
        self.accounts_tree.heading("institution", text="Institution")
        self.accounts_tree.heading("type", text="Type")
        self.accounts_tree.heading("country", text="Country")
        self.accounts_tree.heading("currency", text="Currency")
        self.accounts_tree.heading("max_value", text="Max Value")
        self.accounts_tree.heading("end_value", text="Year-End Value")
        self.accounts_tree.heading("status", text="Status")

        self.accounts_tree.column("number", width=120)
        self.accounts_tree.column("institution", width=150)
        self.accounts_tree.column("type", width=100)
        self.accounts_tree.column("country", width=80)
        self.accounts_tree.column("currency", width=70)
        self.accounts_tree.column("max_value", width=100)
        self.accounts_tree.column("end_value", width=100)
        self.accounts_tree.column("status", width=80)

        # Pack tree and scrollbars
        self.accounts_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        v_scrollbar.config(command=self.accounts_tree.yview)
        h_scrollbar.config(command=self.accounts_tree.xview)

    def build_income_tab(self, parent):
        """Build the foreign income tab"""
        # Toolbar
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill="x", pady=(0, 10))

        ttk.Button(
            toolbar,
            text="Add Income",
            command=self.add_income
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Edit Selected",
            command=self.edit_selected_income
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Delete Selected",
            command=self.delete_selected_income
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Calculate Tax Credit",
            command=self.calculate_tax_credit
        ).pack(side="right")

        # Income treeview
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill="both", expand=True)

        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal")

        self.income_tree = ttk.Treeview(
            tree_frame,
            columns=("type", "country", "amount_usd", "amount_foreign", "currency", "withholding", "description"),
            show="headings",
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )

        # Configure columns
        self.income_tree.heading("type", text="Type")
        self.income_tree.heading("country", text="Country")
        self.income_tree.heading("amount_usd", text="Amount (USD)")
        self.income_tree.heading("amount_foreign", text="Amount (Foreign)")
        self.income_tree.heading("currency", text="Currency")
        self.income_tree.heading("withholding", text="Withholding Tax")
        self.income_tree.heading("description", text="Description")

        self.income_tree.column("type", width=100)
        self.income_tree.column("country", width=80)
        self.income_tree.column("amount_usd", width=100)
        self.income_tree.column("amount_foreign", width=100)
        self.income_tree.column("currency", width=70)
        self.income_tree.column("withholding", width=100)
        self.income_tree.column("description", width=200)

        # Pack tree and scrollbars
        self.income_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        v_scrollbar.config(command=self.income_tree.yview)
        h_scrollbar.config(command=self.income_tree.xview)

    def build_summary_tab(self, parent):
        """Build the FBAR summary tab"""
        # FBAR Status section
        status_frame = ttk.LabelFrame(parent, text="FBAR Filing Status", padding="10")
        status_frame.pack(fill="x", pady=(0, 10))

        self.fbar_status_label = ttk.Label(status_frame, text="Checking FBAR requirements...")
        self.fbar_status_label.pack(anchor="w")

        self.fbar_reason_label = ttk.Label(status_frame, text="", foreground="blue")
        self.fbar_reason_label.pack(anchor="w", pady=(5, 0))

        # Summary section
        summary_frame = ttk.LabelFrame(parent, text="Summary", padding="10")
        summary_frame.pack(fill="x", pady=(0, 10))

        # Summary labels
        summary_items = [
            ("Total Foreign Accounts:", "total_accounts"),
            ("Total Max Value:", "total_max_value"),
            ("Total Year-End Value:", "total_year_end_value"),
            ("Foreign Income (USD):", "total_foreign_income"),
            ("Withholding Tax:", "total_withholding"),
            ("Available Tax Credit:", "available_credit"),
        ]

        for i, (label_text, key) in enumerate(summary_items):
            ttk.Label(summary_frame, text=label_text).grid(row=i, column=0, sticky="w", pady=2)
            self.summary_labels[key] = ttk.Label(summary_frame, text="$0.00")
            self.summary_labels[key].grid(row=i, column=1, sticky="e", pady=2, padx=(10, 0))

        # Action buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(
            button_frame,
            text="Refresh Summary",
            command=self.refresh_summary
        ).pack(side="left", padx=(0, 10))

        ttk.Button(
            button_frame,
            text="Generate FBAR Report",
            command=self.generate_fbar_report
        ).pack(side="left")

    def add_account(self):
        """Add a new foreign account"""
        dialog = ForeignAccountDialog(self, self.fbar_service, self.tax_data)
        if dialog.result:
            self.load_accounts()

    def edit_selected_account(self):
        """Edit the selected account"""
        selection = self.accounts_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an account to edit.")
            return

        # For now, show placeholder
        messagebox.showinfo("Edit Account", "Edit functionality coming soon!")

    def delete_selected_account(self):
        """Delete the selected account"""
        selection = self.accounts_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an account to delete.")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this account?"):
            # This would need to be implemented
            messagebox.showinfo("Delete Account", "Delete functionality coming soon!")

    def add_income(self):
        """Add new foreign income"""
        dialog = ForeignIncomeDialog(self, self.fbar_service, self.tax_data)
        if dialog.result:
            self.load_income()

    def edit_selected_income(self):
        """Edit the selected income"""
        selection = self.income_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select income to edit.")
            return

        # For now, show placeholder
        messagebox.showinfo("Edit Income", "Edit functionality coming soon!")

    def delete_selected_income(self):
        """Delete the selected income"""
        selection = self.income_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select income to delete.")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this income?"):
            # This would need to be implemented
            messagebox.showinfo("Delete Income", "Delete functionality coming soon!")

    def calculate_tax_credit(self):
        """Calculate foreign tax credit"""
        try:
            tax_year = self.tax_data.get_current_year()
            credit_info = self.fbar_service.calculate_foreign_tax_credit(self.tax_data, tax_year)

            if credit_info:
                message = f"""
Foreign Tax Credit Summary for {tax_year}:

Total Foreign Income: ${credit_info['total_foreign_income']:,.2f}
Total Withholding Tax: ${credit_info['total_withholding_tax']:,.2f}
Foreign Tax Credit Limit: ${credit_info['foreign_tax_credit_limit']:,.2f}
Available Credit: ${credit_info['available_credit']:,.2f}
                """
                messagebox.showinfo("Foreign Tax Credit", message.strip())
            else:
                messagebox.showerror("Calculation Error", "Failed to calculate foreign tax credit.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate tax credit: {str(e)}")

    def show_fbar_instructions(self):
        """Show FBAR filing instructions"""
        instructions = self.fbar_service.get_fbar_filing_instructions()
        messagebox.showinfo("FBAR Filing Instructions", instructions)

    def generate_fbar_report(self):
        """Generate FBAR filing report"""
        try:
            tax_year = self.tax_data.get_current_year()
            summary = self.fbar_service.generate_fbar_summary(self.tax_data, tax_year)

            if summary:
                report = f"""
FBAR Filing Report for {tax_year}

FBAR Required: {"YES" if summary['fbar_required'] else "NO"}
Reason: {summary['reason']}

Summary:
- Total Accounts: {summary['total_accounts']}
- Total Maximum Value: ${summary['total_max_value']:,.2f}
- Total Year-End Value: ${summary['total_year_end_value']:,.2f}

Accounts by Country:
"""

                for country, accounts in summary['accounts_by_country'].items():
                    report += f"- {country}: {len(accounts)} account(s)\n"

                messagebox.showinfo("FBAR Report", report.strip())
            else:
                messagebox.showerror("Report Error", "Failed to generate FBAR report.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")

    def refresh_summary(self):
        """Refresh the summary display"""
        try:
            tax_year = self.tax_data.get_current_year()

            # Update FBAR status
            fbar_required, reason = self.fbar_service.is_fbar_required(self.tax_data, tax_year)
            self.fbar_status_label.config(
                text=f"FBAR Filing Required: {'YES' if fbar_required else 'NO'}",
                foreground="red" if fbar_required else "green"
            )
            self.fbar_reason_label.config(text=reason)

            # Update summary numbers
            accounts = self.fbar_service.get_foreign_accounts(self.tax_data)
            income_sources = self.fbar_service.get_foreign_income(self.tax_data)

            self.summary_labels['total_accounts'].config(text=str(len(accounts)))
            self.summary_labels['total_max_value'].config(
                text=f"${sum(a.max_value_during_year for a in accounts):,.2f}"
            )
            self.summary_labels['total_year_end_value'].config(
                text=f"${sum(a.year_end_value for a in accounts):,.2f}"
            )
            self.summary_labels['total_foreign_income'].config(
                text=f"${sum(i.amount_usd for i in income_sources):,.2f}"
            )
            self.summary_labels['total_withholding'].config(
                text=f"${sum(i.withholding_tax for i in income_sources):,.2f}"
            )

            # Calculate tax credit
            credit_info = self.fbar_service.calculate_foreign_tax_credit(self.tax_data, tax_year)
            available_credit = credit_info.get('available_credit', 0)
            self.summary_labels['available_credit'].config(text=f"${available_credit:,.2f}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh summary: {str(e)}")

    def load_data(self):
        """Load all data"""
        self.load_accounts()
        self.load_income()
        self.refresh_summary()

    def load_accounts(self):
        """Load accounts into the treeview"""
        try:
            # Clear existing items
            for item in self.accounts_tree.get_children():
                self.accounts_tree.delete(item)

            # Load accounts
            accounts = self.fbar_service.get_foreign_accounts(self.tax_data)

            # Add to treeview
            for account in accounts:
                status = "Closed" if account.was_closed else "Active"
                self.accounts_tree.insert("", "end", values=(
                    account.account_number,
                    account.institution_name,
                    account.account_type.value.replace('_', ' ').title(),
                    account.country,
                    account.currency,
                    f"${account.max_value_during_year:,.2f}",
                    f"${account.year_end_value:,.2f}",
                    status
                ))

        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load accounts: {str(e)}")

    def load_income(self):
        """Load income into the treeview"""
        try:
            # Clear existing items
            for item in self.income_tree.get_children():
                self.income_tree.delete(item)

            # Load income
            income_sources = self.fbar_service.get_foreign_income(self.tax_data)

            # Add to treeview
            for income in income_sources:
                self.income_tree.insert("", "end", values=(
                    income.source_type.title(),
                    income.country,
                    f"${income.amount_usd:,.2f}",
                    f"{income.amount_foreign:,.2f}",
                    income.currency,
                    f"${income.withholding_tax:,.2f}",
                    income.description
                ))

        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load income: {str(e)}")

    def on_show(self):
        """Called when this page is shown"""
        self.load_data()

    def validate_page(self) -> bool:
        """Validate the page data"""
        return True

    def save_data(self):
        """Save page data to tax data model"""
        pass  # Data is saved through the service

    def load_data_from_model(self):
        """Load data from tax data model"""
        self.load_data()


class ForeignAccountDialog:
    """Dialog for adding/editing foreign accounts"""

    def __init__(self, parent, fbar_service: ForeignIncomeFBARService, tax_data: TaxData, edit_account=None):
        self.parent = parent
        self.fbar_service = fbar_service
        self.tax_data = tax_data
        self.edit_account = edit_account
        self.result = None

        self.build_dialog()

    def build_dialog(self):
        """Build the account dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Add Foreign Account")
        self.dialog.geometry("500x600")
        self.dialog.resizable(False, False)

        # Make dialog modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Form fields
        form_frame = ttk.Frame(self.dialog, padding="20")
        form_frame.pack(fill="both", expand=True)

        # Account Number
        ttk.Label(form_frame, text="Account Number:").grid(row=0, column=0, sticky="w", pady=5)
        self.account_number_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.account_number_var).grid(row=0, column=1, sticky="ew", pady=5)

        # Institution Name
        ttk.Label(form_frame, text="Institution Name:").grid(row=1, column=0, sticky="w", pady=5)
        self.institution_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.institution_var).grid(row=1, column=1, sticky="ew", pady=5)

        # Account Type
        ttk.Label(form_frame, text="Account Type:").grid(row=2, column=0, sticky="w", pady=5)
        self.account_type_var = tk.StringVar(value="bank_account")
        type_combo = ttk.Combobox(
            form_frame,
            textvariable=self.account_type_var,
            values=[t.value for t in ForeignAccountType],
            state="readonly"
        )
        type_combo.grid(row=2, column=1, sticky="ew", pady=5)

        # Country
        ttk.Label(form_frame, text="Country:").grid(row=3, column=0, sticky="w", pady=5)
        self.country_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.country_var).grid(row=3, column=1, sticky="ew", pady=5)

        # Currency
        ttk.Label(form_frame, text="Currency:").grid(row=4, column=0, sticky="w", pady=5)
        self.currency_var = tk.StringVar(value="USD")
        ttk.Entry(form_frame, textvariable=self.currency_var).grid(row=4, column=1, sticky="ew", pady=5)

        # Max Value During Year
        ttk.Label(form_frame, text="Max Value During Year ($):").grid(row=5, column=0, sticky="w", pady=5)
        self.max_value_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.max_value_var).grid(row=5, column=1, sticky="ew", pady=5)

        # Year-End Value
        ttk.Label(form_frame, text="Year-End Value ($):").grid(row=6, column=0, sticky="w", pady=5)
        self.end_value_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.end_value_var).grid(row=6, column=1, sticky="ew", pady=5)

        # Was Closed
        ttk.Label(form_frame, text="Account Closed:").grid(row=7, column=0, sticky="w", pady=5)
        self.was_closed_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(form_frame, variable=self.was_closed_var).grid(row=7, column=1, sticky="w", pady=5)

        # Closed Date (only shown if closed)
        ttk.Label(form_frame, text="Closed Date:").grid(row=8, column=0, sticky="w", pady=5)
        self.closed_date_var = tk.StringVar()
        self.closed_date_entry = ttk.Entry(form_frame, textvariable=self.closed_date_var, state="disabled")
        self.closed_date_entry.grid(row=8, column=1, sticky="ew", pady=5)

        # Bind checkbox to enable/disable date field
        self.was_closed_var.trace_add("write", self._toggle_closed_date)

        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=9, column=0, columnspan=2, pady=(20, 0))

        ttk.Button(
            button_frame,
            text="Save",
            command=self.save_account
        ).pack(side="left", padx=(0, 10))

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy
        ).pack(side="left")

        # Configure grid
        form_frame.columnconfigure(1, weight=1)

    def _toggle_closed_date(self, *args):
        """Toggle closed date field based on checkbox"""
        if self.was_closed_var.get():
            self.closed_date_entry.config(state="normal")
        else:
            self.closed_date_entry.config(state="disabled")
            self.closed_date_var.set("")

    def save_account(self):
        """Save the account"""
        try:
            # Validate inputs
            if not self.account_number_var.get().strip():
                messagebox.showerror("Validation Error", "Account number is required.")
                return

            if not self.institution_var.get().strip():
                messagebox.showerror("Validation Error", "Institution name is required.")
                return

            # Create account
            account = ForeignAccount(
                account_number=self.account_number_var.get().strip(),
                institution_name=self.institution_var.get().strip(),
                account_type=ForeignAccountType(self.account_type_var.get()),
                country=self.country_var.get().strip(),
                currency=self.currency_var.get().strip(),
                max_value_during_year=Decimal(self.max_value_var.get() or "0"),
                year_end_value=Decimal(self.end_value_var.get() or "0"),
                was_closed=self.was_closed_var.get(),
                closed_date=datetime.strptime(self.closed_date_var.get(), "%Y-%m-%d").date() if self.closed_date_var.get() else None
            )

            # Validate account data
            errors = self.fbar_service.validate_foreign_account_data(account)
            if errors:
                messagebox.showerror("Validation Error", "\n".join(errors))
                return

            # Save to service
            if self.fbar_service.add_foreign_account(self.tax_data, account):
                self.result = account
                self.dialog.destroy()
                messagebox.showinfo("Success", "Foreign account added successfully!")
            else:
                messagebox.showerror("Error", "Failed to add account. Check for duplicate account number.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save account: {str(e)}")


class ForeignIncomeDialog:
    """Dialog for adding/editing foreign income"""

    def __init__(self, parent, fbar_service: ForeignIncomeFBARService, tax_data: TaxData, edit_income=None):
        self.parent = parent
        self.fbar_service = fbar_service
        self.tax_data = tax_data
        self.edit_income = edit_income
        self.result = None

        self.build_dialog()

    def build_dialog(self):
        """Build the income dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Add Foreign Income")
        self.dialog.geometry("500x500")
        self.dialog.resizable(False, False)

        # Make dialog modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Form fields
        form_frame = ttk.Frame(self.dialog, padding="20")
        form_frame.pack(fill="both", expand=True)

        # Source Type
        ttk.Label(form_frame, text="Income Type:").grid(row=0, column=0, sticky="w", pady=5)
        self.source_type_var = tk.StringVar(value="dividends")
        type_combo = ttk.Combobox(
            form_frame,
            textvariable=self.source_type_var,
            values=["dividends", "interest", "rental", "business", "capital_gains", "other"],
            state="readonly"
        )
        type_combo.grid(row=0, column=1, sticky="ew", pady=5)

        # Country
        ttk.Label(form_frame, text="Country:").grid(row=1, column=0, sticky="w", pady=5)
        self.country_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.country_var).grid(row=1, column=1, sticky="ew", pady=5)

        # Amount USD
        ttk.Label(form_frame, text="Amount (USD):").grid(row=2, column=0, sticky="w", pady=5)
        self.amount_usd_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.amount_usd_var).grid(row=2, column=1, sticky="ew", pady=5)

        # Amount Foreign
        ttk.Label(form_frame, text="Amount (Foreign Currency):").grid(row=3, column=0, sticky="w", pady=5)
        self.amount_foreign_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.amount_foreign_var).grid(row=3, column=1, sticky="ew", pady=5)

        # Currency
        ttk.Label(form_frame, text="Foreign Currency:").grid(row=4, column=0, sticky="w", pady=5)
        self.currency_var = tk.StringVar(value="EUR")
        ttk.Entry(form_frame, textvariable=self.currency_var).grid(row=4, column=1, sticky="ew", pady=5)

        # Withholding Tax
        ttk.Label(form_frame, text="Withholding Tax ($):").grid(row=5, column=0, sticky="w", pady=5)
        self.withholding_var = tk.StringVar(value="0.00")
        ttk.Entry(form_frame, textvariable=self.withholding_var).grid(row=5, column=1, sticky="ew", pady=5)

        # Description
        ttk.Label(form_frame, text="Description:").grid(row=6, column=0, sticky="w", pady=5)
        self.description_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.description_var).grid(row=6, column=1, sticky="ew", pady=5)

        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=(20, 0))

        ttk.Button(
            button_frame,
            text="Save",
            command=self.save_income
        ).pack(side="left", padx=(0, 10))

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy
        ).pack(side="left")

        # Configure grid
        form_frame.columnconfigure(1, weight=1)

    def save_income(self):
        """Save the income"""
        try:
            # Validate inputs
            if not self.country_var.get().strip():
                messagebox.showerror("Validation Error", "Country is required.")
                return

            if not self.amount_usd_var.get():
                messagebox.showerror("Validation Error", "USD amount is required.")
                return

            # Create income
            income = ForeignIncome(
                source_type=self.source_type_var.get(),
                country=self.country_var.get().strip(),
                amount_usd=Decimal(self.amount_usd_var.get()),
                amount_foreign=Decimal(self.amount_foreign_var.get() or "0"),
                currency=self.currency_var.get().strip(),
                withholding_tax=Decimal(self.withholding_var.get() or "0"),
                description=self.description_var.get().strip()
            )

            # Save to service
            if self.fbar_service.add_foreign_income(self.tax_data, income):
                self.result = income
                self.dialog.destroy()
                messagebox.showinfo("Success", "Foreign income added successfully!")
            else:
                messagebox.showerror("Error", "Failed to add foreign income.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save income: {str(e)}")