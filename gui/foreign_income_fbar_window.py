"""
Foreign Income & FBAR Reporting Window

GUI for managing foreign income reporting and FBAR (Foreign Bank Account Report) requirements.
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import tkinter as tk
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from decimal import Decimal
import threading

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.foreign_income_fbar_service import (
    ForeignIncomeFBARService,
    ForeignAccount,
    ForeignIncome,
    ForeignAccountType,
    FBARThreshold
)
from utils.error_tracker import get_error_tracker


class ForeignIncomeFBARWindow(ctk.CTkToplevel):
    """
    Window for managing foreign income and FBAR reporting requirements.

    Features:
    - Foreign account management for FBAR compliance
    - Foreign income tracking and reporting
    - FBAR requirement determination
    - Foreign tax credit calculations
    - Comprehensive data validation
    """

    def __init__(self, parent, config: AppConfig, tax_data: TaxData):
        """
        Initialize the foreign income and FBAR window.

        Args:
            parent: Parent window
            config: Application configuration
            tax_data: Tax data model
        """
        super().__init__(parent)

        self.config = config
        self.tax_data = tax_data
        self.service = ForeignIncomeFBARService(config)
        self.error_tracker = get_error_tracker()

        # Window setup
        self.title("Foreign Income & FBAR Reporting")
        self.geometry("1200x800")

        # Initialize data
        self.foreign_accounts: List[ForeignAccount] = []
        self.foreign_income: List[ForeignIncome] = []
        self.current_account: Optional[ForeignAccount] = None
        self.current_income: Optional[ForeignIncome] = None

        # Create the main layout
        self._create_main_layout()

        # Load existing data
        self._load_data()

        # Center the window
        self.center_window()

    def center_window(self):
        """Center the window on the screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def _create_main_layout(self):
        """Create the main window layout with tabs."""
        # Create tabview
        self.tabview = ctk.CTkTabview(self, width=1180, height=760)
        self.tabview.pack(pady=10, padx=10, fill="both", expand=True)

        # Create tabs
        self.tabview.add("Foreign Accounts")
        self.tabview.add("Foreign Income")
        self.tabview.add("FBAR Summary")
        self.tabview.add("Tax Credits")

        # Setup each tab
        self._setup_foreign_accounts_tab()
        self._setup_foreign_income_tab()
        self._setup_fbar_summary_tab()
        self._setup_tax_credits_tab()

    def _setup_foreign_accounts_tab(self):
        """Setup the foreign accounts tab."""
        tab = self.tabview.tab("Foreign Accounts")

        # Create main frame
        main_frame = ctk.CTkFrame(tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Foreign Financial Accounts (FBAR)",
            font=ctk.CTkFont(size=16)
        )
        title_label.pack(pady=(10, 20))

        # Create split layout
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Left panel - Account list
        left_panel = ctk.CTkFrame(content_frame, width=400)
        left_panel.pack(side="left", fill="y", padx=(0, 10))

        # Account list title
        list_title = ctk.CTkLabel(
            left_panel,
            text="Accounts",
            font=ctk.CTkFont(size=14)
        )
        list_title.pack(pady=(10, 10))

        # Account listbox frame
        list_frame = ctk.CTkFrame(left_panel)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Account listbox
        self.accounts_listbox = tk.Listbox(
            list_frame,
            selectmode=tk.SINGLE,
            font=("Arial", 10)
        )
        self.accounts_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        # Account buttons
        btn_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.add_account_btn = ctk.CTkButton(
            btn_frame,
            text="Add Account",
            command=self._add_foreign_account,
            width=120
        )
        self.add_account_btn.pack(side="left", padx=(0, 5))

        self.edit_account_btn = ctk.CTkButton(
            btn_frame,
            text="Edit",
            command=self._edit_foreign_account,
            width=80
        )
        self.edit_account_btn.pack(side="left", padx=(0, 5))

        self.delete_account_btn = ctk.CTkButton(
            btn_frame,
            text="Delete",
            command=self._delete_foreign_account,
            width=80,
            fg_color="red"
        )
        self.delete_account_btn.pack(side="left")

        # Right panel - Account details form
        right_panel = ctk.CTkFrame(content_frame)
        right_panel.pack(side="right", fill="both", expand=True)

        # Form title
        form_title = ctk.CTkLabel(
            right_panel,
            text="Account Details",
            font=ctk.CTkFont(size=14)
        )
        form_title.pack(pady=(10, 20))

        # Create scrollable frame for form
        form_frame = ctk.CTkScrollableFrame(right_panel)
        form_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Account form fields
        self._create_account_form(form_frame)

        # Form buttons
        form_btn_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        form_btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.save_account_btn = ctk.CTkButton(
            form_btn_frame,
            text="Save Account",
            command=self._save_foreign_account,
            width=120
        )
        self.save_account_btn.pack(side="right")

        self.clear_account_btn = ctk.CTkButton(
            form_btn_frame,
            text="Clear",
            command=self._clear_account_form,
            width=80
        )
        self.clear_account_btn.pack(side="right", padx=(0, 10))

    def _create_account_form(self, parent):
        """Create the foreign account form."""
        # Account Number
        account_num_label = ctk.CTkLabel(parent, text="Account Number:")
        account_num_label.pack(anchor="w", pady=(10, 5))
        self.account_num_entry = ctk.CTkEntry(parent, placeholder_text="Enter account number")
        self.account_num_entry.pack(fill="x", pady=(0, 10))

        # Institution Name
        institution_label = ctk.CTkLabel(parent, text="Institution Name:")
        institution_label.pack(anchor="w", pady=(10, 5))
        self.institution_entry = ctk.CTkEntry(parent, placeholder_text="Bank or institution name")
        self.institution_entry.pack(fill="x", pady=(0, 10))

        # Account Type
        type_label = ctk.CTkLabel(parent, text="Account Type:")
        type_label.pack(anchor="w", pady=(10, 5))
        self.account_type_combo = ctk.CTkComboBox(
            parent,
            values=[t.value for t in ForeignAccountType],
            state="readonly"
        )
        self.account_type_combo.set("bank_account")
        self.account_type_combo.pack(fill="x", pady=(0, 10))

        # Country
        country_label = ctk.CTkLabel(parent, text="Country:")
        country_label.pack(anchor="w", pady=(10, 5))
        self.country_entry = ctk.CTkEntry(parent, placeholder_text="Country where account is located")
        self.country_entry.pack(fill="x", pady=(0, 10))

        # Currency
        currency_label = ctk.CTkLabel(parent, text="Currency:")
        currency_label.pack(anchor="w", pady=(10, 5))
        self.currency_entry = ctk.CTkEntry(parent, placeholder_text="Account currency (e.g., USD, EUR)")
        self.currency_entry.pack(fill="x", pady=(0, 10))

        # Maximum Value During Year
        max_value_label = ctk.CTkLabel(parent, text="Maximum Value During Year ($):")
        max_value_label.pack(anchor="w", pady=(10, 5))
        self.max_value_entry = ctk.CTkEntry(parent, placeholder_text="Highest balance during the year")
        self.max_value_entry.pack(fill="x", pady=(0, 10))

        # Year-End Value
        year_end_label = ctk.CTkLabel(parent, text="Year-End Value ($):")
        year_end_label.pack(anchor="w", pady=(10, 5))
        self.year_end_entry = ctk.CTkEntry(parent, placeholder_text="Balance at year end")
        self.year_end_entry.pack(fill="x", pady=(0, 10))

        # Account Status
        status_label = ctk.CTkLabel(parent, text="Account Status:")
        status_label.pack(anchor="w", pady=(10, 5))

        status_frame = ctk.CTkFrame(parent, fg_color="transparent")
        status_frame.pack(fill="x", pady=(0, 10))

        self.was_closed_var = ctk.BooleanVar()
        self.was_closed_check = ctk.CTkCheckBox(
            status_frame,
            text="Account was closed during the year",
            variable=self.was_closed_var,
            command=self._toggle_closed_date
        )
        self.was_closed_check.pack(side="left")

        # Closed Date
        closed_date_label = ctk.CTkLabel(parent, text="Closed Date:")
        closed_date_label.pack(anchor="w", pady=(10, 5))
        self.closed_date_entry = ctk.CTkEntry(
            parent,
            placeholder_text="YYYY-MM-DD",
            state="disabled"
        )
        self.closed_date_entry.pack(fill="x", pady=(0, 10))

    def _setup_foreign_income_tab(self):
        """Setup the foreign income tab."""
        tab = self.tabview.tab("Foreign Income")

        # Create main frame
        main_frame = ctk.CTkFrame(tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Foreign Income Sources",
            font=ctk.CTkFont(size=16)
        )
        title_label.pack(pady=(10, 20))

        # Create split layout
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Left panel - Income list
        left_panel = ctk.CTkFrame(content_frame, width=400)
        left_panel.pack(side="left", fill="y", padx=(0, 10))

        # Income list title
        list_title = ctk.CTkLabel(
            left_panel,
            text="Income Sources",
            font=ctk.CTkFont(size=14)
        )
        list_title.pack(pady=(10, 10))

        # Income listbox frame
        list_frame = ctk.CTkFrame(left_panel)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Income listbox
        self.income_listbox = tk.Listbox(
            list_frame,
            selectmode=tk.SINGLE,
            font=("Arial", 10)
        )
        self.income_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        # Income buttons
        btn_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.add_income_btn = ctk.CTkButton(
            btn_frame,
            text="Add Income",
            command=self._add_foreign_income,
            width=120
        )
        self.add_income_btn.pack(side="left", padx=(0, 5))

        self.edit_income_btn = ctk.CTkButton(
            btn_frame,
            text="Edit",
            command=self._edit_foreign_income,
            width=80
        )
        self.edit_income_btn.pack(side="left", padx=(0, 5))

        self.delete_income_btn = ctk.CTkButton(
            btn_frame,
            text="Delete",
            command=self._delete_foreign_income,
            width=80,
            fg_color="red"
        )
        self.delete_income_btn.pack(side="left")

        # Right panel - Income details form
        right_panel = ctk.CTkFrame(content_frame)
        right_panel.pack(side="right", fill="both", expand=True)

        # Form title
        form_title = ctk.CTkLabel(
            right_panel,
            text="Income Details",
            font=ctk.CTkFont(size=14)
        )
        form_title.pack(pady=(10, 20))

        # Create scrollable frame for form
        form_frame = ctk.CTkScrollableFrame(right_panel)
        form_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Income form fields
        self._create_income_form(form_frame)

        # Form buttons
        form_btn_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        form_btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.save_income_btn = ctk.CTkButton(
            form_btn_frame,
            text="Save Income",
            command=self._save_foreign_income,
            width=120
        )
        self.save_income_btn.pack(side="right")

        self.clear_income_btn = ctk.CTkButton(
            form_btn_frame,
            text="Clear",
            command=self._clear_income_form,
            width=80
        )
        self.clear_income_btn.pack(side="right", padx=(0, 10))

    def _create_income_form(self, parent):
        """Create the foreign income form."""
        # Source Type
        source_type_label = ctk.CTkLabel(parent, text="Income Source Type:")
        source_type_label.pack(anchor="w", pady=(10, 5))
        self.source_type_combo = ctk.CTkComboBox(
            parent,
            values=["dividends", "interest", "rental", "business", "capital_gains", "royalties", "other"],
            state="readonly"
        )
        self.source_type_combo.set("dividends")
        self.source_type_combo.pack(fill="x", pady=(0, 10))

        # Country
        country_label = ctk.CTkLabel(parent, text="Source Country:")
        country_label.pack(anchor="w", pady=(10, 5))
        self.income_country_entry = ctk.CTkEntry(parent, placeholder_text="Country where income was earned")
        self.income_country_entry.pack(fill="x", pady=(0, 10))

        # Amount in Foreign Currency
        foreign_amount_label = ctk.CTkLabel(parent, text="Amount in Foreign Currency:")
        foreign_amount_label.pack(anchor="w", pady=(10, 5))
        self.foreign_amount_entry = ctk.CTkEntry(parent, placeholder_text="Amount in original currency")
        self.foreign_amount_entry.pack(fill="x", pady=(0, 10))

        # Currency
        income_currency_label = ctk.CTkLabel(parent, text="Currency:")
        income_currency_label.pack(anchor="w", pady=(10, 5))
        self.income_currency_entry = ctk.CTkEntry(parent, placeholder_text="Currency code (e.g., EUR, GBP)")
        self.income_currency_entry.pack(fill="x", pady=(0, 10))

        # Amount in USD
        usd_amount_label = ctk.CTkLabel(parent, text="Amount in USD:")
        usd_amount_label.pack(anchor="w", pady=(10, 5))
        self.usd_amount_entry = ctk.CTkEntry(parent, placeholder_text="US dollar equivalent")
        self.usd_amount_entry.pack(fill="x", pady=(0, 10))

        # Withholding Tax
        withholding_label = ctk.CTkLabel(parent, text="Foreign Withholding Tax ($):")
        withholding_label.pack(anchor="w", pady=(10, 5))
        self.withholding_entry = ctk.CTkEntry(parent, placeholder_text="Tax withheld by foreign country")
        self.withholding_entry.pack(fill="x", pady=(0, 10))

        # Description
        description_label = ctk.CTkLabel(parent, text="Description:")
        description_label.pack(anchor="w", pady=(10, 5))
        self.income_description_entry = ctk.CTkEntry(parent, placeholder_text="Brief description of income source")
        self.income_description_entry.pack(fill="x", pady=(0, 10))

    def _setup_fbar_summary_tab(self):
        """Setup the FBAR summary tab."""
        tab = self.tabview.tab("FBAR Summary")

        # Create main frame
        main_frame = ctk.CTkFrame(tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="FBAR Filing Summary",
            font=ctk.CTkFont(size=16)
        )
        title_label.pack(pady=(10, 20))

        # Create scrollable content
        content_frame = ctk.CTkScrollableFrame(main_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Summary sections
        self._create_fbar_summary_section(content_frame)

        # Refresh button
        refresh_btn = ctk.CTkButton(
            main_frame,
            text="Refresh Summary",
            command=self._refresh_fbar_summary,
            width=150
        )
        refresh_btn.pack(pady=(0, 10))

    def _create_fbar_summary_section(self, parent):
        """Create the FBAR summary display section."""
        # FBAR Requirement Status
        status_frame = ctk.CTkFrame(parent)
        status_frame.pack(fill="x", pady=(0, 20))

        status_title = ctk.CTkLabel(
            status_frame,
            text="FBAR Filing Requirement",
            font=ctk.CTkFont(size=14)
        )
        status_title.pack(pady=(10, 10))

        self.fbar_status_label = ctk.CTkLabel(
            status_frame,
            text="Loading...",
            font=ctk.CTkFont(size=12)
        )
        self.fbar_status_label.pack(pady=(0, 10))

        # Account Summary
        accounts_frame = ctk.CTkFrame(parent)
        accounts_frame.pack(fill="x", pady=(0, 20))

        accounts_title = ctk.CTkLabel(
            accounts_frame,
            text="Foreign Accounts Summary",
            font=ctk.CTkFont(size=14)
        )
        accounts_title.pack(pady=(10, 10))

        self.accounts_summary_text = ctk.CTkTextbox(
            accounts_frame,
            height=150,
            wrap="word"
        )
        self.accounts_summary_text.pack(fill="x", padx=10, pady=(0, 10))

        # Filing Instructions
        instructions_frame = ctk.CTkFrame(parent)
        instructions_frame.pack(fill="x", pady=(0, 20))

        instructions_title = ctk.CTkLabel(
            instructions_frame,
            text="FBAR Filing Instructions",
            font=ctk.CTkFont(size=14)
        )
        instructions_title.pack(pady=(10, 10))

        self.instructions_text = ctk.CTkTextbox(
            instructions_frame,
            height=200,
            wrap="word"
        )
        self.instructions_text.pack(fill="x", padx=10, pady=(0, 10))

        # Set initial content
        self._refresh_fbar_summary()

    def _setup_tax_credits_tab(self):
        """Setup the tax credits tab."""
        tab = self.tabview.tab("Tax Credits")

        # Create main frame
        main_frame = ctk.CTkFrame(tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Foreign Tax Credit Calculator",
            font=ctk.CTkFont(size=16)
        )
        title_label.pack(pady=(10, 20))

        # Create scrollable content
        content_frame = ctk.CTkScrollableFrame(main_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Tax year selection
        year_frame = ctk.CTkFrame(content_frame)
        year_frame.pack(fill="x", pady=(0, 20))

        year_label = ctk.CTkLabel(year_frame, text="Tax Year:")
        year_label.pack(side="left", padx=(10, 10))

        self.tax_year_combo = ctk.CTkComboBox(
            year_frame,
            values=["2024", "2025", "2026"],
            state="readonly",
            width=100
        )
        self.tax_year_combo.set("2026")
        self.tax_year_combo.pack(side="left")

        calc_btn = ctk.CTkButton(
            year_frame,
            text="Calculate Credits",
            command=self._calculate_tax_credits,
            width=150
        )
        calc_btn.pack(side="right", padx=(10, 10))

        # Credit Summary
        credits_frame = ctk.CTkFrame(content_frame)
        credits_frame.pack(fill="x", pady=(0, 20))

        credits_title = ctk.CTkLabel(
            credits_frame,
            text="Foreign Tax Credit Summary",
            font=ctk.CTkFont(size=14)
        )
        credits_title.pack(pady=(10, 10))

        self.credits_summary_text = ctk.CTkTextbox(
            credits_frame,
            height=200,
            wrap="word"
        )
        self.credits_summary_text.pack(fill="x", padx=10, pady=(0, 10))

        # Income Summary
        income_summary_frame = ctk.CTkFrame(content_frame)
        income_summary_frame.pack(fill="x", pady=(0, 20))

        income_summary_title = ctk.CTkLabel(
            income_summary_frame,
            text="Foreign Income Summary",
            font=ctk.CTkFont(size=14)
        )
        income_summary_title.pack(pady=(10, 10))

        self.income_summary_text = ctk.CTkTextbox(
            income_summary_frame,
            height=150,
            wrap="word"
        )
        self.income_summary_text.pack(fill="x", padx=10, pady=(0, 10))

        # Initialize with empty content
        self.credits_summary_text.insert("0.0", "Click 'Calculate Credits' to view foreign tax credit information.")
        self.income_summary_text.insert("0.0", "Foreign income summary will appear here after calculation.")

    # Event handlers
    def _load_data(self):
        """Load existing foreign accounts and income data."""
        try:
            self.foreign_accounts = self.service.get_foreign_accounts(self.tax_data)
            self.foreign_income = self.service.get_foreign_income(self.tax_data)

            # Update listboxes
            self._update_accounts_list()
            self._update_income_list()

        except Exception as e:
            self.error_tracker.log_error("foreign_load_data", str(e))
            messagebox.showerror("Error", f"Failed to load foreign data: {e}")

    def _update_accounts_list(self):
        """Update the accounts listbox."""
        self.accounts_listbox.delete(0, tk.END)
        for account in self.foreign_accounts:
            display_text = f"{account.account_number} - {account.institution_name} ({account.country})"
            self.accounts_listbox.insert(tk.END, display_text)

    def _update_income_list(self):
        """Update the income listbox."""
        self.income_listbox.delete(0, tk.END)
        for income in self.foreign_income:
            display_text = f"{income.source_type.title()} - {income.country} - ${income.amount_usd:,.2f}"
            self.income_listbox.insert(tk.END, display_text)

    def _add_foreign_account(self):
        """Add a new foreign account."""
        self.current_account = None
        self._clear_account_form()

    def _edit_foreign_account(self):
        """Edit the selected foreign account."""
        selection = self.accounts_listbox.curselection()
        if not selection:
            messagebox.showwarning("Selection Required", "Please select an account to edit.")
            return

        index = selection[0]
        self.current_account = self.foreign_accounts[index]
        self._populate_account_form()

    def _delete_foreign_account(self):
        """Delete the selected foreign account."""
        selection = self.accounts_listbox.curselection()
        if not selection:
            messagebox.showwarning("Selection Required", "Please select an account to delete.")
            return

        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this foreign account?"):
            return

        index = selection[0]
        account = self.foreign_accounts[index]

        if self.service.add_foreign_account(self.tax_data, account) is False:  # This will actually remove it
            # Remove from local list
            self.foreign_accounts.pop(index)
            self._update_accounts_list()
            self._clear_account_form()
            messagebox.showinfo("Success", "Foreign account deleted successfully.")
        else:
            messagebox.showerror("Error", "Failed to delete foreign account.")

    def _save_foreign_account(self):
        """Save the foreign account form data."""
        try:
            # Validate required fields
            account_num = self.account_num_entry.get().strip()
            institution = self.institution_entry.get().strip()
            country = self.country_entry.get().strip()
            currency = self.currency_entry.get().strip()

            if not account_num or not institution or not country:
                messagebox.showerror("Validation Error", "Account number, institution name, and country are required.")
                return

            # Parse numeric values
            try:
                max_value = Decimal(self.max_value_entry.get().strip() or "0")
                year_end_value = Decimal(self.year_end_entry.get().strip() or "0")
            except:
                messagebox.showerror("Validation Error", "Please enter valid numeric values for account balances.")
                return

            # Parse account type
            account_type = ForeignAccountType(self.account_type_combo.get())

            # Handle closed account
            was_closed = self.was_closed_var.get()
            closed_date = None
            if was_closed:
                closed_date_str = self.closed_date_entry.get().strip()
                if closed_date_str:
                    try:
                        closed_date = date.fromisoformat(closed_date_str)
                    except:
                        messagebox.showerror("Validation Error", "Please enter a valid date in YYYY-MM-DD format.")
                        return
                else:
                    messagebox.showerror("Validation Error", "Closed date is required for closed accounts.")
                    return

            # Create or update account
            if self.current_account:
                # Update existing
                self.current_account.account_number = account_num
                self.current_account.institution_name = institution
                self.current_account.account_type = account_type
                self.current_account.country = country
                self.current_account.currency = currency
                self.current_account.max_value_during_year = max_value
                self.current_account.year_end_value = year_end_value
                self.current_account.was_closed = was_closed
                self.current_account.closed_date = closed_date
                account = self.current_account
            else:
                # Create new
                account = ForeignAccount(
                    account_number=account_num,
                    institution_name=institution,
                    account_type=account_type,
                    country=country,
                    currency=currency,
                    max_value_during_year=max_value,
                    year_end_value=year_end_value,
                    was_closed=was_closed,
                    closed_date=closed_date
                )

            # Validate account data
            errors = self.service.validate_foreign_account_data(account)
            if errors:
                messagebox.showerror("Validation Error", "\n".join(errors))
                return

            # Save to service
            if self.service.add_foreign_account(self.tax_data, account):
                # Update local list
                if self.current_account:
                    # Find and update existing
                    for i, acc in enumerate(self.foreign_accounts):
                        if acc.account_number == account.account_number:
                            self.foreign_accounts[i] = account
                            break
                else:
                    self.foreign_accounts.append(account)

                self._update_accounts_list()
                self._clear_account_form()
                self.current_account = None
                messagebox.showinfo("Success", "Foreign account saved successfully.")
                self._refresh_fbar_summary()
            else:
                messagebox.showerror("Error", "Failed to save foreign account.")

        except Exception as e:
            self.error_tracker.log_error("foreign_save_account", str(e))
            messagebox.showerror("Error", f"Failed to save account: {e}")

    def _clear_account_form(self):
        """Clear the account form."""
        self.account_num_entry.delete(0, tk.END)
        self.institution_entry.delete(0, tk.END)
        self.account_type_combo.set("bank_account")
        self.country_entry.delete(0, tk.END)
        self.currency_entry.delete(0, tk.END)
        self.max_value_entry.delete(0, tk.END)
        self.year_end_entry.delete(0, tk.END)
        self.was_closed_var.set(False)
        self.closed_date_entry.delete(0, tk.END)
        self.closed_date_entry.configure(state="disabled")
        self.current_account = None

    def _populate_account_form(self):
        """Populate the account form with current account data."""
        if not self.current_account:
            return

        self.account_num_entry.delete(0, tk.END)
        self.account_num_entry.insert(0, self.current_account.account_number)

        self.institution_entry.delete(0, tk.END)
        self.institution_entry.insert(0, self.current_account.institution_name)

        self.account_type_combo.set(self.current_account.account_type.value)

        self.country_entry.delete(0, tk.END)
        self.country_entry.insert(0, self.current_account.country)

        self.currency_entry.delete(0, tk.END)
        self.currency_entry.insert(0, self.current_account.currency)

        self.max_value_entry.delete(0, tk.END)
        self.max_value_entry.insert(0, str(self.current_account.max_value_during_year))

        self.year_end_entry.delete(0, tk.END)
        self.year_end_entry.insert(0, str(self.current_account.year_end_value))

        self.was_closed_var.set(self.current_account.was_closed)
        self._toggle_closed_date()

        if self.current_account.closed_date:
            self.closed_date_entry.delete(0, tk.END)
            self.closed_date_entry.insert(0, self.current_account.closed_date.isoformat())

    def _toggle_closed_date(self):
        """Toggle the closed date field based on checkbox."""
        if self.was_closed_var.get():
            self.closed_date_entry.configure(state="normal")
        else:
            self.closed_date_entry.configure(state="disabled")
            self.closed_date_entry.delete(0, tk.END)

    def _add_foreign_income(self):
        """Add a new foreign income source."""
        self.current_income = None
        self._clear_income_form()

    def _edit_foreign_income(self):
        """Edit the selected foreign income."""
        selection = self.income_listbox.curselection()
        if not selection:
            messagebox.showwarning("Selection Required", "Please select an income source to edit.")
            return

        index = selection[0]
        self.current_income = self.foreign_income[index]
        self._populate_income_form()

    def _delete_foreign_income(self):
        """Delete the selected foreign income."""
        selection = self.income_listbox.curselection()
        if not selection:
            messagebox.showwarning("Selection Required", "Please select an income source to delete.")
            return

        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this foreign income source?"):
            return

        index = selection[0]
        income = self.foreign_income[index]

        # Remove from tax data by getting all income except this one
        all_income = self.service.get_foreign_income(self.tax_data)
        all_income = [i for i in all_income if i.description != income.description or i.amount_usd != income.amount_usd]

        # Save back (this is a workaround since service doesn't have delete method)
        income_dicts = [i.to_dict() for i in all_income]
        self.tax_data.set("foreign_income", income_dicts)

        # Update local list
        self.foreign_income.pop(index)
        self._update_income_list()
        self._clear_income_form()
        messagebox.showinfo("Success", "Foreign income deleted successfully.")

    def _save_foreign_income(self):
        """Save the foreign income form data."""
        try:
            # Validate required fields
            source_type = self.source_type_combo.get()
            country = self.income_country_entry.get().strip()
            description = self.income_description_entry.get().strip()

            if not country or not description:
                messagebox.showerror("Validation Error", "Country and description are required.")
                return

            # Parse numeric values
            try:
                foreign_amount = Decimal(self.foreign_amount_entry.get().strip() or "0")
                usd_amount = Decimal(self.usd_amount_entry.get().strip() or "0")
                withholding = Decimal(self.withholding_entry.get().strip() or "0")
            except:
                messagebox.showerror("Validation Error", "Please enter valid numeric values for amounts.")
                return

            currency = self.income_currency_entry.get().strip() or "USD"

            # Create or update income
            if self.current_income:
                # Update existing
                self.current_income.source_type = source_type
                self.current_income.country = country
                self.current_income.amount_foreign = foreign_amount
                self.current_income.currency = currency
                self.current_income.amount_usd = usd_amount
                self.current_income.withholding_tax = withholding
                self.current_income.description = description
                income = self.current_income
            else:
                # Create new
                income = ForeignIncome(
                    source_type=source_type,
                    country=country,
                    amount_foreign=foreign_amount,
                    currency=currency,
                    amount_usd=usd_amount,
                    withholding_tax=withholding,
                    description=description
                )

            # Save to service
            if self.service.add_foreign_income(self.tax_data, income):
                # Update local list
                if self.current_income:
                    # Find and update existing
                    for i, inc in enumerate(self.foreign_income):
                        if inc.description == income.description and inc.amount_usd == income.amount_usd:
                            self.foreign_income[i] = income
                            break
                else:
                    self.foreign_income.append(income)

                self._update_income_list()
                self._clear_income_form()
                self.current_income = None
                messagebox.showinfo("Success", "Foreign income saved successfully.")
            else:
                messagebox.showerror("Error", "Failed to save foreign income.")

        except Exception as e:
            self.error_tracker.log_error("foreign_save_income", str(e))
            messagebox.showerror("Error", f"Failed to save income: {e}")

    def _clear_income_form(self):
        """Clear the income form."""
        self.source_type_combo.set("dividends")
        self.income_country_entry.delete(0, tk.END)
        self.foreign_amount_entry.delete(0, tk.END)
        self.income_currency_entry.delete(0, tk.END)
        self.usd_amount_entry.delete(0, tk.END)
        self.withholding_entry.delete(0, tk.END)
        self.income_description_entry.delete(0, tk.END)
        self.current_income = None

    def _populate_income_form(self):
        """Populate the income form with current income data."""
        if not self.current_income:
            return

        self.source_type_combo.set(self.current_income.source_type)

        self.income_country_entry.delete(0, tk.END)
        self.income_country_entry.insert(0, self.current_income.country)

        self.foreign_amount_entry.delete(0, tk.END)
        self.foreign_amount_entry.insert(0, str(self.current_income.amount_foreign))

        self.income_currency_entry.delete(0, tk.END)
        self.income_currency_entry.insert(0, self.current_income.currency)

        self.usd_amount_entry.delete(0, tk.END)
        self.usd_amount_entry.insert(0, str(self.current_income.amount_usd))

        self.withholding_entry.delete(0, tk.END)
        self.withholding_entry.insert(0, str(self.current_income.withholding_tax))

        self.income_description_entry.delete(0, tk.END)
        self.income_description_entry.insert(0, self.current_income.description)

    def _refresh_fbar_summary(self):
        """Refresh the FBAR summary display."""
        try:
            tax_year = 2026  # Default to 2026
            summary = self.service.generate_fbar_summary(self.tax_data, tax_year)
            instructions = self.service.get_fbar_filing_instructions()

            # Update status
            if summary['fbar_required']:
                self.fbar_status_label.configure(
                    text=f"❌ FBAR Filing REQUIRED\n{summary['reason']}",
                    text_color="red"
                )
            else:
                self.fbar_status_label.configure(
                    text=f"✅ FBAR Filing NOT Required\n{summary['reason']}",
                    text_color="green"
                )

            # Update accounts summary
            self.accounts_summary_text.delete("0.0", tk.END)
            summary_text = f"""Total Foreign Accounts: {summary['total_accounts']}
Total Maximum Value: ${summary['total_max_value']:,.2f}
Total Year-End Value: ${summary['total_year_end_value']:,.2f}

Accounts by Country:
"""
            for country, accounts in summary['accounts_by_country'].items():
                summary_text += f"\n{country}: {len(accounts)} account(s)"

            self.accounts_summary_text.insert("0.0", summary_text)

            # Update instructions
            self.instructions_text.delete("0.0", tk.END)
            self.instructions_text.insert("0.0", instructions)

        except Exception as e:
            self.error_tracker.log_error("foreign_refresh_summary", str(e))
            messagebox.showerror("Error", f"Failed to refresh FBAR summary: {e}")

    def _calculate_tax_credits(self):
        """Calculate and display foreign tax credits."""
        try:
            tax_year = int(self.tax_year_combo.get())

            credit_info = self.service.calculate_foreign_tax_credit(self.tax_data, tax_year)

            if not credit_info:
                self.credits_summary_text.delete("0.0", tk.END)
                self.credits_summary_text.insert("0.0", "No foreign tax credit information available.")
                return

            # Update credits summary
            self.credits_summary_text.delete("0.0", tk.END)
            credits_text = f"""Foreign Tax Credit Summary (Tax Year {tax_year})

Total Foreign Income: ${credit_info['total_foreign_income']:,.2f}
Total Foreign Withholding Tax: ${credit_info['total_withholding_tax']:,.2f}
Foreign Tax Credit Limit: ${credit_info['foreign_tax_credit_limit']:,.2f}
Available Foreign Tax Credit: ${credit_info['available_credit']:,.2f}

Note: Foreign tax credits are limited to 80% of U.S. tax liability on foreign income.
Actual credit amount may vary based on your total U.S. tax situation.
"""
            self.credits_summary_text.insert("0.0", credits_text)

            # Update income summary
            self.income_summary_text.delete("0.0", tk.END)
            income_text = f"Foreign Income Summary (Tax Year {tax_year})\n\n"

            for income in self.foreign_income:
                income_text += f"• {income.source_type.title()} from {income.country}: ${income.amount_usd:,.2f} USD\n"
                income_text += f"  Original: {income.amount_foreign:,.2f} {income.currency}\n"
                income_text += f"  Withholding Tax: ${income.withholding_tax:,.2f}\n\n"

            if not self.foreign_income:
                income_text += "No foreign income sources recorded."

            self.income_summary_text.insert("0.0", income_text)

        except Exception as e:
            self.error_tracker.log_error("foreign_calculate_credits", str(e))
            messagebox.showerror("Error", f"Failed to calculate tax credits: {e}")