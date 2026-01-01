"""
Modern Foreign Income and FBAR Reporting Page

CustomTkinter implementation for managing foreign income and FBAR requirements.
"""

import customtkinter as ctk
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, date
from decimal import Decimal
from tkinter import messagebox

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.foreign_income_fbar_service import (
    ForeignIncomeFBARService,
    ForeignAccount,
    ForeignIncome,
    ForeignAccountType,
    FBARThreshold
)


class ModernForeignIncomePage(ctk.CTkFrame):
    """
    Modern page for foreign income and FBAR reporting using CustomTkinter.

    Features:
    - Tabbed interface for accounts, income, and FBAR summary
    - Modern dialogs for data entry
    - Real-time validation and calculations
    - Expandable sections for better organization
    """

    def __init__(self, parent, tax_data: TaxData, config: AppConfig,
                 on_complete_callback: Optional[Callable] = None):
        """
        Initialize the modern foreign income page.

        Args:
            parent: Parent widget
            tax_data: Tax data model
            config: Application configuration
            on_complete_callback: Callback when page is completed
        """
        super().__init__(parent)
        self.tax_data = tax_data
        self.config = config
        self.on_complete_callback = on_complete_callback

        # Initialize service
        self.fbar_service = ForeignIncomeFBARService(config)

        # UI components
        self.tabview = None
        self.accounts_scrollable_frame = None
        self.income_scrollable_frame = None
        self.summary_scrollable_frame = None

        # Data storage
        self.accounts_data = []
        self.income_data = []

        self.build_ui()
        self.load_data()

    def build_ui(self):
        """Build the modern UI with tabbed interface"""
        # Header section
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        title_label = ctk.CTkLabel(
            header_frame,
            text="Foreign Income & FBAR Reporting",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(anchor="w", pady=(10, 5))

        description_label = ctk.CTkLabel(
            header_frame,
            text="Report foreign financial accounts and income sources. FBAR filing may be required if aggregate foreign account values exceed $10,000.",
            font=ctk.CTkFont(size=12),
            wraplength=700,
            justify="left"
        )
        description_label.pack(anchor="w", pady=(0, 10))

        # Tabview for different sections
        self.tabview = ctk.CTkTabview(self, width=800, height=600)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Create tabs
        self.tabview.add("Foreign Accounts")
        self.tabview.add("Foreign Income")
        self.tabview.add("FBAR Summary")

        # Build each tab
        self.build_accounts_tab()
        self.build_income_tab()
        self.build_summary_tab()

        # Navigation buttons
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=20, pady=(0, 20))

        # Previous button (if needed)
        prev_button = ctk.CTkButton(
            nav_frame,
            text="← Previous",
            command=self._on_previous,
            width=120
        )
        prev_button.pack(side="left")

        # Complete button
        complete_button = ctk.CTkButton(
            nav_frame,
            text="Complete Foreign Income",
            command=self._on_complete,
            fg_color="green",
            hover_color="dark green",
            width=200
        )
        complete_button.pack(side="right")

    def build_accounts_tab(self):
        """Build the foreign accounts tab with modern UI"""
        tab = self.tabview.tab("Foreign Accounts")

        # Toolbar
        toolbar_frame = ctk.CTkFrame(tab, fg_color="transparent")
        toolbar_frame.pack(fill="x", padx=10, pady=(10, 5))

        # Buttons
        add_button = ctk.CTkButton(
            toolbar_frame,
            text="+ Add Account",
            command=self.add_account,
            width=120
        )
        add_button.pack(side="left", padx=(0, 10))

        edit_button = ctk.CTkButton(
            toolbar_frame,
            text="Edit Selected",
            command=self.edit_selected_account,
            width=120
        )
        edit_button.pack(side="left", padx=(0, 10))

        delete_button = ctk.CTkButton(
            toolbar_frame,
            text="Delete Selected",
            command=self.delete_selected_account,
            fg_color="red",
            hover_color="dark red",
            width=120
        )
        delete_button.pack(side="left", padx=(0, 10))

        # Instructions button
        instructions_button = ctk.CTkButton(
            toolbar_frame,
            text="FBAR Instructions",
            command=self.show_fbar_instructions,
            width=140
        )
        instructions_button.pack(side="right")

        # Scrollable frame for accounts
        self.accounts_scrollable_frame = ctk.CTkScrollableFrame(tab)
        self.accounts_scrollable_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # Header for accounts list
        header_label = ctk.CTkLabel(
            self.accounts_scrollable_frame,
            text="Foreign Financial Accounts",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header_label.pack(anchor="w", pady=(10, 15))

        # Placeholder for accounts - will be populated in load_data
        self.accounts_container = ctk.CTkFrame(self.accounts_scrollable_frame, fg_color="transparent")
        self.accounts_container.pack(fill="x", pady=(0, 10))

    def build_income_tab(self):
        """Build the foreign income tab with modern UI"""
        tab = self.tabview.tab("Foreign Income")

        # Toolbar
        toolbar_frame = ctk.CTkFrame(tab, fg_color="transparent")
        toolbar_frame.pack(fill="x", padx=10, pady=(10, 5))

        # Buttons
        add_button = ctk.CTkButton(
            toolbar_frame,
            text="+ Add Income",
            command=self.add_income,
            width=120
        )
        add_button.pack(side="left", padx=(0, 10))

        edit_button = ctk.CTkButton(
            toolbar_frame,
            text="Edit Selected",
            command=self.edit_selected_income,
            width=120
        )
        edit_button.pack(side="left", padx=(0, 10))

        delete_button = ctk.CTkButton(
            toolbar_frame,
            text="Delete Selected",
            command=self.delete_selected_income,
            fg_color="red",
            hover_color="dark red",
            width=120
        )
        delete_button.pack(side="left", padx=(0, 10))

        # Tax credit button
        credit_button = ctk.CTkButton(
            toolbar_frame,
            text="Calculate Tax Credit",
            command=self.calculate_tax_credit,
            fg_color="blue",
            hover_color="dark blue",
            width=150
        )
        credit_button.pack(side="right")

        # Scrollable frame for income
        self.income_scrollable_frame = ctk.CTkScrollableFrame(tab)
        self.income_scrollable_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # Header for income list
        header_label = ctk.CTkLabel(
            self.income_scrollable_frame,
            text="Foreign Income Sources",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header_label.pack(anchor="w", pady=(10, 15))

        # Placeholder for income - will be populated in load_data
        self.income_container = ctk.CTkFrame(self.income_scrollable_frame, fg_color="transparent")
        self.income_container.pack(fill="x", pady=(0, 10))

    def build_summary_tab(self):
        """Build the FBAR summary tab with modern UI"""
        tab = self.tabview.tab("FBAR Summary")

        # Scrollable frame for summary
        self.summary_scrollable_frame = ctk.CTkScrollableFrame(tab)
        self.summary_scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Header
        header_label = ctk.CTkLabel(
            self.summary_scrollable_frame,
            text="FBAR Filing Summary",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header_label.pack(anchor="w", pady=(10, 20))

        # Summary container
        self.summary_container = ctk.CTkFrame(self.summary_scrollable_frame)
        self.summary_container.pack(fill="x", pady=(0, 20))

        # Placeholder content - will be populated in load_data
        loading_label = ctk.CTkLabel(
            self.summary_container,
            text="Loading FBAR summary...",
            font=ctk.CTkFont(size=12)
        )
        loading_label.pack(pady=20)

    def load_data(self):
        """Load foreign accounts and income data"""
        try:
            # Load accounts
            self.accounts_data = self.fbar_service.get_foreign_accounts(self.tax_data)
            self.refresh_accounts_display()

            # Load income
            self.income_data = self.fbar_service.get_foreign_income(self.tax_data)
            self.refresh_income_display()

            # Load summary
            self.refresh_summary_display()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load foreign income data: {str(e)}")

    def refresh_accounts_display(self):
        """Refresh the accounts display"""
        # Clear existing accounts
        for widget in self.accounts_container.winfo_children():
            widget.destroy()

        if not self.accounts_data:
            # No accounts message
            no_accounts_label = ctk.CTkLabel(
                self.accounts_container,
                text="No foreign accounts added yet.\nClick 'Add Account' to get started.",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            no_accounts_label.pack(pady=20)
            return

        # Display accounts
        for i, account in enumerate(self.accounts_data):
            self._create_account_card(account, i)

    def _create_account_card(self, account: ForeignAccount, index: int):
        """Create a card for displaying account information"""
        card = ctk.CTkFrame(self.accounts_container)
        card.pack(fill="x", pady=(0, 10), padx=5)

        # Header with account info
        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(10, 5))

        # Account number and institution
        account_label = ctk.CTkLabel(
            header_frame,
            text=f"{account.account_number} - {account.institution_name}",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        account_label.pack(anchor="w")

        # Type and country
        type_country_label = ctk.CTkLabel(
            header_frame,
            text=f"{account.account_type.value.replace('_', ' ').title()} • {account.country}",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        type_country_label.pack(anchor="w", pady=(2, 0))

        # Values
        values_frame = ctk.CTkFrame(card, fg_color="transparent")
        values_frame.pack(fill="x", padx=15, pady=(0, 10))

        # Max value
        max_value_label = ctk.CTkLabel(
            values_frame,
            text=f"Max Value: ${account.max_value_during_year:,.2f} {account.currency}",
            font=ctk.CTkFont(size=12)
        )
        max_value_label.pack(anchor="w", pady=(0, 2))

        # Year-end value
        end_value_label = ctk.CTkLabel(
            values_frame,
            text=f"Year-End Value: ${account.year_end_value:,.2f} {account.currency}",
            font=ctk.CTkFont(size=12)
        )
        end_value_label.pack(anchor="w", pady=(0, 5))

        # Status
        status_text = "Active"
        if account.was_closed:
            status_text = f"Closed {account.closed_date.strftime('%Y-%m-%d') if account.closed_date else ''}"

        status_label = ctk.CTkLabel(
            values_frame,
            text=f"Status: {status_text}",
            font=ctk.CTkFont(size=11),
            text_color="green" if not account.was_closed else "orange"
        )
        status_label.pack(anchor="w")

        # Action buttons
        buttons_frame = ctk.CTkFrame(card, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=15, pady=(0, 10))

        edit_button = ctk.CTkButton(
            buttons_frame,
            text="Edit",
            command=lambda: self.edit_account(account, index),
            width=80,
            height=28
        )
        edit_button.pack(side="left", padx=(0, 10))

        delete_button = ctk.CTkButton(
            buttons_frame,
            text="Delete",
            command=lambda: self.delete_account(index),
            fg_color="red",
            hover_color="dark red",
            width=80,
            height=28
        )
        delete_button.pack(side="left")

    def refresh_income_display(self):
        """Refresh the income display"""
        # Clear existing income
        for widget in self.income_container.winfo_children():
            widget.destroy()

        if not self.income_data:
            # No income message
            no_income_label = ctk.CTkLabel(
                self.income_container,
                text="No foreign income added yet.\nClick 'Add Income' to get started.",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            no_income_label.pack(pady=20)
            return

        # Display income
        for i, income in enumerate(self.income_data):
            self._create_income_card(income, i)

    def _create_income_card(self, income: ForeignIncome, index: int):
        """Create a card for displaying income information"""
        card = ctk.CTkFrame(self.income_container)
        card.pack(fill="x", pady=(0, 10), padx=5)

        # Header with income info
        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(10, 5))

        # Type and country
        type_label = ctk.CTkLabel(
            header_frame,
            text=f"{income.source_type.title()} • {income.country}",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        type_label.pack(anchor="w")

        # Description
        desc_label = ctk.CTkLabel(
            header_frame,
            text=income.description,
            font=ctk.CTkFont(size=11),
            text_color="gray",
            wraplength=400
        )
        desc_label.pack(anchor="w", pady=(2, 0))

        # Values
        values_frame = ctk.CTkFrame(card, fg_color="transparent")
        values_frame.pack(fill="x", padx=15, pady=(0, 10))

        # USD amount
        usd_label = ctk.CTkLabel(
            values_frame,
            text=f"Amount (USD): ${income.amount_usd:,.2f}",
            font=ctk.CTkFont(size=12)
        )
        usd_label.pack(anchor="w", pady=(0, 2))

        # Foreign amount
        foreign_label = ctk.CTkLabel(
            values_frame,
            text=f"Amount ({income.currency}): {income.amount_foreign:,.2f}",
            font=ctk.CTkFont(size=12)
        )
        foreign_label.pack(anchor="w", pady=(0, 2))

        # Withholding tax
        withholding_label = ctk.CTkLabel(
            values_frame,
            text=f"Withholding Tax: ${income.withholding_tax:,.2f}",
            font=ctk.CTkFont(size=12)
        )
        withholding_label.pack(anchor="w")

        # Action buttons
        buttons_frame = ctk.CTkFrame(card, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=15, pady=(0, 10))

        edit_button = ctk.CTkButton(
            buttons_frame,
            text="Edit",
            command=lambda: self.edit_income(income, index),
            width=80,
            height=28
        )
        edit_button.pack(side="left", padx=(0, 10))

        delete_button = ctk.CTkButton(
            buttons_frame,
            text="Delete",
            command=lambda: self.delete_income(index),
            fg_color="red",
            hover_color="dark red",
            width=80,
            height=28
        )
        delete_button.pack(side="left")

    def refresh_summary_display(self):
        """Refresh the FBAR summary display"""
        # Clear existing summary
        for widget in self.summary_container.winfo_children():
            widget.destroy()

        try:
            # Get FBAR summary
            summary = self.fbar_service.generate_fbar_summary(self.tax_data, 2025)

            if not summary:
                error_label = ctk.CTkLabel(
                    self.summary_container,
                    text="Unable to generate FBAR summary.",
                    font=ctk.CTkFont(size=12),
                    text_color="red"
                )
                error_label.pack(pady=20)
                return

            # FBAR requirement status
            status_frame = ctk.CTkFrame(self.summary_container)
            status_frame.pack(fill="x", padx=15, pady=(10, 15))

            status_title = ctk.CTkLabel(
                status_frame,
                text="FBAR Filing Requirement",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            status_title.pack(anchor="w", pady=(10, 5))

            required = summary.get('fbar_required', False)
            status_color = "green" if not required else "orange"
            status_text = "NOT Required" if not required else "REQUIRED"

            status_label = ctk.CTkLabel(
                status_frame,
                text=status_text,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=status_color
            )
            status_label.pack(anchor="w", pady=(0, 5))

            reason_label = ctk.CTkLabel(
                status_frame,
                text=summary.get('reason', ''),
                font=ctk.CTkFont(size=12),
                wraplength=500
            )
            reason_label.pack(anchor="w", pady=(0, 10))

            # Account summary
            if summary.get('total_accounts', 0) > 0:
                accounts_frame = ctk.CTkFrame(self.summary_container)
                accounts_frame.pack(fill="x", padx=15, pady=(0, 15))

                accounts_title = ctk.CTkLabel(
                    accounts_frame,
                    text="Account Summary",
                    font=ctk.CTkFont(size=14, weight="bold")
                )
                accounts_title.pack(anchor="w", pady=(10, 10))

                total_accounts_label = ctk.CTkLabel(
                    accounts_frame,
                    text=f"Total Accounts: {summary['total_accounts']}",
                    font=ctk.CTkFont(size=12)
                )
                total_accounts_label.pack(anchor="w", pady=(0, 5))

                max_value_label = ctk.CTkLabel(
                    accounts_frame,
                    text=f"Total Maximum Value: ${summary['total_max_value']:,.2f}",
                    font=ctk.CTkFont(size=12)
                )
                max_value_label.pack(anchor="w", pady=(0, 5))

                end_value_label = ctk.CTkLabel(
                    accounts_frame,
                    text=f"Total Year-End Value: ${summary['total_year_end_value']:,.2f}",
                    font=ctk.CTkFont(size=12)
                )
                end_value_label.pack(anchor="w")

                # Accounts by country
                if summary.get('accounts_by_country'):
                    countries_title = ctk.CTkLabel(
                        accounts_frame,
                        text="Accounts by Country:",
                        font=ctk.CTkFont(size=12, weight="bold")
                    )
                    countries_title.pack(anchor="w", pady=(10, 5))

                    for country, accounts in summary['accounts_by_country'].items():
                        country_label = ctk.CTkLabel(
                            accounts_frame,
                            text=f"• {country}: {len(accounts)} account(s)",
                            font=ctk.CTkFont(size=11)
                        )
                        country_label.pack(anchor="w", pady=(0, 2))

            # Foreign income summary
            if self.income_data:
                income_frame = ctk.CTkFrame(self.summary_container)
                income_frame.pack(fill="x", padx=15, pady=(0, 15))

                income_title = ctk.CTkLabel(
                    income_frame,
                    text="Foreign Income Summary",
                    font=ctk.CTkFont(size=14, weight="bold")
                )
                income_title.pack(anchor="w", pady=(10, 10))

                total_income = sum(income.amount_usd for income in self.income_data)
                total_withholding = sum(income.withholding_tax for income in self.income_data)

                total_income_label = ctk.CTkLabel(
                    income_frame,
                    text=f"Total Foreign Income: ${total_income:,.2f}",
                    font=ctk.CTkFont(size=12)
                )
                total_income_label.pack(anchor="w", pady=(0, 5))

                withholding_label = ctk.CTkLabel(
                    income_frame,
                    text=f"Total Withholding Tax: ${total_withholding:,.2f}",
                    font=ctk.CTkFont(size=12)
                )
                withholding_label.pack(anchor="w")

        except Exception as e:
            error_label = ctk.CTkLabel(
                self.summary_container,
                text=f"Error loading FBAR summary: {str(e)}",
                font=ctk.CTkFont(size=12),
                text_color="red"
            )
            error_label.pack(pady=20)

    # Account management methods
    def add_account(self):
        """Add a new foreign account"""
        dialog = ModernForeignAccountDialog(self, self.fbar_service, self.tax_data)
        self.wait_window(dialog)

        if dialog.result:
            self.load_data()

    def edit_account(self, account: ForeignAccount, index: int):
        """Edit an existing account"""
        dialog = ModernForeignAccountDialog(self, self.fbar_service, self.tax_data, edit_account=account)
        self.wait_window(dialog)

        if dialog.result:
            self.load_data()

    def edit_selected_account(self):
        """Edit the selected account (placeholder for now)"""
        messagebox.showinfo("Info", "Please use the Edit button on the account card.")

    def delete_account(self, index: int):
        """Delete an account"""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this foreign account?"):
            try:
                # Remove from data
                if 0 <= index < len(self.accounts_data):
                    self.accounts_data.pop(index)

                    # Save back to tax data
                    account_dicts = [a.to_dict() for a in self.accounts_data]
                    self.tax_data.set("foreign_accounts", account_dicts)

                    self.refresh_accounts_display()
                    self.refresh_summary_display()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete account: {str(e)}")

    def delete_selected_account(self):
        """Delete selected account (placeholder)"""
        messagebox.showinfo("Info", "Please use the Delete button on the account card.")

    # Income management methods
    def add_income(self):
        """Add new foreign income"""
        dialog = ModernForeignIncomeDialog(self, self.fbar_service, self.tax_data)
        self.wait_window(dialog)

        if dialog.result:
            self.load_data()

    def edit_income(self, income: ForeignIncome, index: int):
        """Edit existing income"""
        dialog = ModernForeignIncomeDialog(self, self.fbar_service, self.tax_data, edit_income=income)
        self.wait_window(dialog)

        if dialog.result:
            self.load_data()

    def edit_selected_income(self):
        """Edit selected income (placeholder)"""
        messagebox.showinfo("Info", "Please use the Edit button on the income card.")

    def delete_income(self, index: int):
        """Delete income"""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this foreign income?"):
            try:
                # Remove from data
                if 0 <= index < len(self.income_data):
                    self.income_data.pop(index)

                    # Save back to tax data
                    income_dicts = [i.to_dict() for i in self.income_data]
                    self.tax_data.set("foreign_income", income_dicts)

                    self.refresh_income_display()
                    self.refresh_summary_display()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete income: {str(e)}")

    def delete_selected_income(self):
        """Delete selected income (placeholder)"""
        messagebox.showinfo("Info", "Please use the Delete button on the income card.")

    def calculate_tax_credit(self):
        """Calculate foreign tax credit"""
        try:
            credit_info = self.fbar_service.calculate_foreign_tax_credit(self.tax_data, 2025)

            if credit_info:
                message = f"""Foreign Tax Credit Calculation:

Total Foreign Income: ${credit_info.get('total_foreign_income', 0):,.2f}
Total Withholding Tax: ${credit_info.get('total_withholding_tax', 0):,.2f}
Foreign Tax Credit Limit: ${credit_info.get('foreign_tax_credit_limit', 0):,.2f}
Available Credit: ${credit_info.get('available_credit', 0):,.2f}"""

                messagebox.showinfo("Foreign Tax Credit", message)
            else:
                messagebox.showwarning("Warning", "Unable to calculate foreign tax credit.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate tax credit: {str(e)}")

    def show_fbar_instructions(self):
        """Show FBAR filing instructions"""
        instructions = self.fbar_service.get_fbar_filing_instructions()

        # Create a dialog to show instructions
        dialog = ctk.CTkToplevel(self)
        dialog.title("FBAR Filing Instructions")
        dialog.geometry("600x500")

        # Scrollable text
        scrollable_frame = ctk.CTkScrollableFrame(dialog)
        scrollable_frame.pack(fill="both", expand=True, padx=20, pady=20)

        instructions_label = ctk.CTkLabel(
            scrollable_frame,
            text=instructions,
            font=ctk.CTkFont(size=11),
            justify="left",
            wraplength=550
        )
        instructions_label.pack(anchor="w", pady=10)

        # Close button
        close_button = ctk.CTkButton(
            scrollable_frame,
            text="Close",
            command=dialog.destroy
        )
        close_button.pack(pady=(20, 0))

    def _on_previous(self):
        """Handle previous button click"""
        if self.on_complete_callback:
            self.on_complete_callback("previous")

    def _on_complete(self):
        """Handle complete button click"""
        if self.on_complete_callback:
            self.on_complete_callback("complete")


class ModernForeignAccountDialog(ctk.CTkToplevel):
    """
    Modern dialog for adding/editing foreign accounts.
    """

    def __init__(self, parent, fbar_service: ForeignIncomeFBARService, tax_data: TaxData,
                 edit_account: Optional[ForeignAccount] = None):
        """
        Initialize the account dialog.

        Args:
            parent: Parent window
            fbar_service: FBAR service instance
            tax_data: Tax data model
            edit_account: Account to edit (None for new account)
        """
        super().__init__(parent)
        self.fbar_service = fbar_service
        self.tax_data = tax_data
        self.edit_account = edit_account
        self.result = None

        self.title("Add Foreign Account" if not edit_account else "Edit Foreign Account")
        self.geometry("500x600")

        # Make dialog modal
        self.grab_set()

        self.build_ui()
        if edit_account:
            self.load_account_data()

    def build_ui(self):
        """Build the dialog UI"""
        # Scrollable frame
        scrollable_frame = ctk.CTkScrollableFrame(self)
        scrollable_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ctk.CTkLabel(
            scrollable_frame,
            text="Foreign Account Information",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(10, 20))

        # Account details section
        details_frame = ctk.CTkFrame(scrollable_frame)
        details_frame.pack(fill="x", pady=(0, 15))

        # Account number
        account_label = ctk.CTkLabel(details_frame, text="Account Number:")
        account_label.pack(anchor="w", padx=15, pady=(15, 5))

        self.account_entry = ctk.CTkEntry(details_frame, placeholder_text="Enter account number")
        self.account_entry.pack(fill="x", padx=15, pady=(0, 10))

        # Institution name
        institution_label = ctk.CTkLabel(details_frame, text="Institution Name:")
        institution_label.pack(anchor="w", padx=15, pady=(0, 5))

        self.institution_entry = ctk.CTkEntry(details_frame, placeholder_text="Enter institution name")
        self.institution_entry.pack(fill="x", padx=15, pady=(0, 10))

        # Account type
        type_label = ctk.CTkLabel(details_frame, text="Account Type:")
        type_label.pack(anchor="w", padx=15, pady=(0, 5))

        self.type_optionmenu = ctk.CTkOptionMenu(
            details_frame,
            values=[t.value.replace('_', ' ').title() for t in ForeignAccountType]
        )
        self.type_optionmenu.pack(fill="x", padx=15, pady=(0, 10))

        # Country
        country_label = ctk.CTkLabel(details_frame, text="Country:")
        country_label.pack(anchor="w", padx=15, pady=(0, 5))

        self.country_entry = ctk.CTkEntry(details_frame, placeholder_text="Enter country")
        self.country_entry.pack(fill="x", padx=15, pady=(0, 10))

        # Currency
        currency_label = ctk.CTkLabel(details_frame, text="Currency:")
        currency_label.pack(anchor="w", padx=15, pady=(0, 5))

        self.currency_entry = ctk.CTkEntry(details_frame, placeholder_text="USD")
        self.currency_entry.pack(fill="x", padx=15, pady=(0, 10))

        # Values section
        values_frame = ctk.CTkFrame(scrollable_frame)
        values_frame.pack(fill="x", pady=(0, 15))

        values_title = ctk.CTkLabel(values_frame, text="Account Values", font=ctk.CTkFont(weight="bold"))
        values_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Max value during year
        max_value_label = ctk.CTkLabel(values_frame, text="Maximum Value During Year:")
        max_value_label.pack(anchor="w", padx=15, pady=(0, 5))

        self.max_value_entry = ctk.CTkEntry(values_frame, placeholder_text="0.00")
        self.max_value_entry.pack(fill="x", padx=15, pady=(0, 10))

        # Year-end value
        end_value_label = ctk.CTkLabel(values_frame, text="Year-End Value:")
        end_value_label.pack(anchor="w", padx=15, pady=(0, 5))

        self.end_value_entry = ctk.CTkEntry(values_frame, placeholder_text="0.00")
        self.end_value_entry.pack(fill="x", padx=15, pady=(0, 10))

        # Status section
        status_frame = ctk.CTkFrame(scrollable_frame)
        status_frame.pack(fill="x", pady=(0, 20))

        status_title = ctk.CTkLabel(status_frame, text="Account Status", font=ctk.CTkFont(weight="bold"))
        status_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Closed checkbox
        self.closed_var = ctk.BooleanVar()
        closed_checkbox = ctk.CTkCheckBox(
            status_frame,
            text="Account was closed during the year",
            variable=self.closed_var,
            command=self._on_closed_changed
        )
        closed_checkbox.pack(anchor="w", padx=15, pady=(0, 10))

        # Closed date
        closed_date_label = ctk.CTkLabel(status_frame, text="Closed Date:")
        closed_date_label.pack(anchor="w", padx=15, pady=(0, 5))

        self.closed_date_entry = ctk.CTkEntry(status_frame, placeholder_text="YYYY-MM-DD")
        self.closed_date_entry.pack(fill="x", padx=15, pady=(0, 15))
        self.closed_date_entry.configure(state="disabled")

        # Buttons
        buttons_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(10, 0))

        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            command=self._on_cancel,
            width=100
        )
        cancel_button.pack(side="left", padx=(0, 10))

        save_button = ctk.CTkButton(
            buttons_frame,
            text="Save",
            command=self._on_save,
            fg_color="green",
            hover_color="dark green",
            width=100
        )
        save_button.pack(side="right")

    def _on_closed_changed(self):
        """Handle closed checkbox change"""
        if self.closed_var.get():
            self.closed_date_entry.configure(state="normal")
        else:
            self.closed_date_entry.configure(state="disabled")
            self.closed_date_entry.delete(0, "end")

    def load_account_data(self):
        """Load existing account data for editing"""
        if self.edit_account:
            self.account_entry.insert(0, self.edit_account.account_number)
            self.institution_entry.insert(0, self.edit_account.institution_name)
            self.type_optionmenu.set(self.edit_account.account_type.value.replace('_', ' ').title())
            self.country_entry.insert(0, self.edit_account.country)
            self.currency_entry.insert(0, self.edit_account.currency)
            self.max_value_entry.insert(0, str(self.edit_account.max_value_during_year))
            self.end_value_entry.insert(0, str(self.edit_account.year_end_value))

            if self.edit_account.was_closed:
                self.closed_var.set(True)
                self.closed_date_entry.configure(state="normal")
                if self.edit_account.closed_date:
                    self.closed_date_entry.insert(0, self.edit_account.closed_date.strftime('%Y-%m-%d'))

    def _on_cancel(self):
        """Handle cancel button"""
        self.result = None
        self.destroy()

    def _on_save(self):
        """Handle save button"""
        try:
            # Validate and collect data
            account_data = self._collect_account_data()
            if not account_data:
                return

            # Create or update account
            if self.edit_account:
                # Update existing account
                updated_account = ForeignAccount(**account_data)
                # In a real implementation, you'd update the specific account
                # For now, we'll just create a new one
                success = self.fbar_service.add_foreign_account(self.tax_data, updated_account)
            else:
                # Create new account
                account = ForeignAccount(**account_data)
                success = self.fbar_service.add_foreign_account(self.tax_data, account)

            if success:
                self.result = True
                self.destroy()
            else:
                messagebox.showerror("Error", "Failed to save foreign account.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save account: {str(e)}")

    def _collect_account_data(self) -> Optional[Dict[str, Any]]:
        """Collect and validate account data from form"""
        try:
            # Basic validation
            account_number = self.account_entry.get().strip()
            institution = self.institution_entry.get().strip()
            country = self.country_entry.get().strip()

            if not account_number or not institution or not country:
                messagebox.showerror("Validation Error", "Account number, institution, and country are required.")
                return None

            # Parse values
            try:
                max_value = Decimal(self.max_value_entry.get().strip() or "0")
                end_value = Decimal(self.end_value_entry.get().strip() or "0")
            except:
                messagebox.showerror("Validation Error", "Invalid numeric values for account amounts.")
                return None

            # Account type
            type_str = self.type_optionmenu.get().lower().replace(' ', '_')
            account_type = ForeignAccountType(type_str)

            # Closed status
            was_closed = self.closed_var.get()
            closed_date = None
            if was_closed:
                date_str = self.closed_date_entry.get().strip()
                if date_str:
                    try:
                        closed_date = date.fromisoformat(date_str)
                    except:
                        messagebox.showerror("Validation Error", "Invalid date format. Use YYYY-MM-DD.")
                        return None

            return {
                'account_number': account_number,
                'institution_name': institution,
                'account_type': account_type,
                'country': country,
                'currency': self.currency_entry.get().strip() or "USD",
                'max_value_during_year': max_value,
                'year_end_value': end_value,
                'was_closed': was_closed,
                'closed_date': closed_date,
            }

        except Exception as e:
            messagebox.showerror("Error", f"Failed to collect account data: {str(e)}")
            return None


class ModernForeignIncomeDialog(ctk.CTkToplevel):
    """
    Modern dialog for adding/editing foreign income.
    """

    def __init__(self, parent, fbar_service: ForeignIncomeFBARService, tax_data: TaxData,
                 edit_income: Optional[ForeignIncome] = None):
        """
        Initialize the income dialog.

        Args:
            parent: Parent window
            fbar_service: FBAR service instance
            tax_data: Tax data model
            edit_income: Income to edit (None for new income)
        """
        super().__init__(parent)
        self.fbar_service = fbar_service
        self.tax_data = tax_data
        self.edit_income = edit_income
        self.result = None

        self.title("Add Foreign Income" if not edit_income else "Edit Foreign Income")
        self.geometry("500x550")

        # Make dialog modal
        self.grab_set()

        self.build_ui()
        if edit_income:
            self.load_income_data()

    def build_ui(self):
        """Build the dialog UI"""
        # Scrollable frame
        scrollable_frame = ctk.CTkScrollableFrame(self)
        scrollable_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ctk.CTkLabel(
            scrollable_frame,
            text="Foreign Income Information",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(10, 20))

        # Income details section
        details_frame = ctk.CTkFrame(scrollable_frame)
        details_frame.pack(fill="x", pady=(0, 15))

        # Source type
        type_label = ctk.CTkLabel(details_frame, text="Income Source Type:")
        type_label.pack(anchor="w", padx=15, pady=(15, 5))

        self.type_optionmenu = ctk.CTkOptionMenu(
            details_frame,
            values=["dividends", "interest", "rental", "business", "other"]
        )
        self.type_optionmenu.pack(fill="x", padx=15, pady=(0, 10))

        # Country
        country_label = ctk.CTkLabel(details_frame, text="Country of Source:")
        country_label.pack(anchor="w", padx=15, pady=(0, 5))

        self.country_entry = ctk.CTkEntry(details_frame, placeholder_text="Enter country")
        self.country_entry.pack(fill="x", padx=15, pady=(0, 10))

        # Description
        desc_label = ctk.CTkLabel(details_frame, text="Description:")
        desc_label.pack(anchor="w", padx=15, pady=(0, 5))

        self.desc_entry = ctk.CTkEntry(details_frame, placeholder_text="Brief description of income source")
        self.desc_entry.pack(fill="x", padx=15, pady=(0, 10))

        # Values section
        values_frame = ctk.CTkFrame(scrollable_frame)
        values_frame.pack(fill="x", pady=(0, 15))

        values_title = ctk.CTkLabel(values_frame, text="Income Amounts", font=ctk.CTkFont(weight="bold"))
        values_title.pack(anchor="w", padx=15, pady=(15, 10))

        # USD amount
        usd_label = ctk.CTkLabel(values_frame, text="Amount in USD:")
        usd_label.pack(anchor="w", padx=15, pady=(0, 5))

        self.usd_entry = ctk.CTkEntry(values_frame, placeholder_text="0.00")
        self.usd_entry.pack(fill="x", padx=15, pady=(0, 10))

        # Foreign amount
        foreign_label = ctk.CTkLabel(values_frame, text="Amount in Foreign Currency:")
        foreign_label.pack(anchor="w", padx=15, pady=(0, 5))

        self.foreign_entry = ctk.CTkEntry(values_frame, placeholder_text="0.00")
        self.foreign_entry.pack(fill="x", padx=15, pady=(0, 10))

        # Currency
        currency_label = ctk.CTkLabel(values_frame, text="Foreign Currency:")
        currency_label.pack(anchor="w", padx=15, pady=(0, 5))

        self.currency_entry = ctk.CTkEntry(values_frame, placeholder_text="EUR")
        self.currency_entry.pack(fill="x", padx=15, pady=(0, 10))

        # Withholding tax
        withholding_label = ctk.CTkLabel(values_frame, text="Withholding Tax Paid:")
        withholding_label.pack(anchor="w", padx=15, pady=(0, 5))

        self.withholding_entry = ctk.CTkEntry(values_frame, placeholder_text="0.00")
        self.withholding_entry.pack(fill="x", padx=15, pady=(0, 15))

        # Buttons
        buttons_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(10, 0))

        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            command=self._on_cancel,
            width=100
        )
        cancel_button.pack(side="left", padx=(0, 10))

        save_button = ctk.CTkButton(
            buttons_frame,
            text="Save",
            command=self._on_save,
            fg_color="green",
            hover_color="dark green",
            width=100
        )
        save_button.pack(side="right")

    def load_income_data(self):
        """Load existing income data for editing"""
        if self.edit_income:
            self.type_optionmenu.set(self.edit_income.source_type)
            self.country_entry.insert(0, self.edit_income.country)
            self.desc_entry.insert(0, self.edit_income.description)
            self.usd_entry.insert(0, str(self.edit_income.amount_usd))
            self.foreign_entry.insert(0, str(self.edit_income.amount_foreign))
            self.currency_entry.insert(0, self.edit_income.currency)
            self.withholding_entry.insert(0, str(self.edit_income.withholding_tax))

    def _on_cancel(self):
        """Handle cancel button"""
        self.result = None
        self.destroy()

    def _on_save(self):
        """Handle save button"""
        try:
            # Validate and collect data
            income_data = self._collect_income_data()
            if not income_data:
                return

            # Create or update income
            if self.edit_income:
                # Update existing income
                updated_income = ForeignIncome(**income_data)
                # In a real implementation, you'd update the specific income
                # For now, we'll just create a new one
                success = self.fbar_service.add_foreign_income(self.tax_data, updated_income)
            else:
                # Create new income
                income = ForeignIncome(**income_data)
                success = self.fbar_service.add_foreign_income(self.tax_data, income)

            if success:
                self.result = True
                self.destroy()
            else:
                messagebox.showerror("Error", "Failed to save foreign income.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save income: {str(e)}")

    def _collect_income_data(self) -> Optional[Dict[str, Any]]:
        """Collect and validate income data from form"""
        try:
            # Basic validation
            source_type = self.type_optionmenu.get()
            country = self.country_entry.get().strip()
            description = self.desc_entry.get().strip()

            if not country or not description:
                messagebox.showerror("Validation Error", "Country and description are required.")
                return None

            # Parse values
            try:
                amount_usd = Decimal(self.usd_entry.get().strip() or "0")
                amount_foreign = Decimal(self.foreign_entry.get().strip() or "0")
                withholding_tax = Decimal(self.withholding_entry.get().strip() or "0")
            except:
                messagebox.showerror("Validation Error", "Invalid numeric values for income amounts.")
                return None

            return {
                'source_type': source_type,
                'country': country,
                'amount_usd': amount_usd,
                'amount_foreign': amount_foreign,
                'currency': self.currency_entry.get().strip() or "USD",
                'withholding_tax': withholding_tax,
                'description': description,
            }

        except Exception as e:
            messagebox.showerror("Error", f"Failed to collect income data: {str(e)}")
            return None