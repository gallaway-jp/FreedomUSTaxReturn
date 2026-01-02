"""
Modern Income Dialogs - CustomTkinter Implementation

Dialog classes for entering different types of income with modern UI.
"""

import customtkinter as ctk
from typing import Optional, Dict, Any, Callable
import re
from datetime import datetime


class ModernIncomeDialog(ctk.CTkToplevel):
    """
    Base class for modern income entry dialogs.

    Provides common functionality for all income type dialogs.
    """

    def __init__(self, parent, config, title: str, on_save: Callable[[Dict[str, Any]], None],
                 item_data: Optional[Dict[str, Any]] = None, edit_index: Optional[int] = None):
        """
        Initialize the income dialog.

        Args:
            parent: Parent widget
            config: Application configuration
            title: Dialog title
            on_save: Callback when data is saved
            item_data: Existing data for editing
            edit_index: Index of item being edited
        """
        super().__init__(parent)

        self.config = config
        self.on_save = on_save
        self.item_data = item_data or {}
        self.edit_index = edit_index

        # Configure dialog
        self.title(title)
        self.geometry("700x600")
        self.resizable(True, True)

        self.transient(parent)
        self.grab_set()

        # Center on parent
        self._center_on_parent()

        # Build the dialog
        self._build_dialog()

        # Load existing data if editing
        if self.item_data:
            self._load_data()

    def _center_on_parent(self):
        """Center the dialog on its parent"""
        self.update_idletasks()
        parent = self.master
        if parent:
            parent_x = parent.winfo_x()
            parent_y = parent.winfo_y()
            parent_width = parent.winfo_width()
            parent_height = parent.winfo_height()

            dialog_width = self.winfo_width()
            dialog_height = self.winfo_height()

            x = parent_x + (parent_width - dialog_width) // 2
            y = parent_y + (parent_height - dialog_height) // 2

            self.geometry(f"+{x}+{y}")

    def _build_dialog(self):
        """Build the dialog structure"""
        # Main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text=self.title(),
            font=ctk.CTkFont(size=18)
        )
        self.title_label.pack(pady=(0, 20))

        # Scrollable content area
        self.content_frame = ctk.CTkScrollableFrame(self.main_frame)
        self.content_frame.pack(fill="both", expand=True, pady=(0, 20))

        # Build form content (to be overridden by subclasses)
        self._build_form_content()

        # Button frame
        button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(20, 0))

        # Cancel button
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            fg_color="transparent",
            border_width=1
        )
        cancel_button.pack(side="right", padx=(10, 0))

        # Save button
        self.save_button = ctk.CTkButton(
            button_frame,
            text="Save",
            command=self._on_save_clicked
        )
        self.save_button.pack(side="right")

    def _build_form_content(self):
        """Build the form content (to be overridden by subclasses)"""
        pass

    def _load_data(self):
        """Load existing data into the form (to be overridden by subclasses)"""
        pass

    def _validate_data(self) -> tuple[bool, str]:
        """Validate the form data (to be overridden by subclasses)"""
        return True, ""

    def _collect_data(self) -> Dict[str, Any]:
        """Collect data from the form (to be overridden by subclasses)"""
        return {}

    def _on_save_clicked(self):
        """Handle save button click"""
        # Validate data
        is_valid, error_message = self._validate_data()
        if not is_valid:
            # Show error message
            error_dialog = ctk.CTkToplevel(self)
            error_dialog.title("Validation Error")
            error_dialog.geometry("400x150")

            error_dialog.transient(self)
            error_dialog.grab_set()

            error_frame = ctk.CTkFrame(error_dialog)
            error_frame.pack(fill="both", expand=True, padx=20, pady=20)

            error_label = ctk.CTkLabel(
                error_frame,
                text="❌ " + error_message,
                font=ctk.CTkFont(size=12),
                wraplength=350
            )
            error_label.pack(pady=(0, 20))

            ctk.CTkButton(error_frame, text="OK", command=error_dialog.destroy).pack()

            return

        # Collect data
        data = self._collect_data()

        # Call save callback
        self.on_save(data)

        # Close dialog
        self.destroy()


class ModernW2Dialog(ModernIncomeDialog):
    """Dialog for entering W-2 wage information"""

    def __init__(self, parent, config, on_save: Callable[[Dict[str, Any]], None],
                 item_data: Optional[Dict[str, Any]] = None, edit_index: Optional[int] = None):
        super().__init__(parent, config, "Add W-2 Income", on_save, item_data, edit_index)

    def _build_form_content(self):
        """Build the W-2 form content"""
        # Employer information
        employer_frame = ctk.CTkFrame(self.content_frame)
        employer_frame.pack(fill="x", pady=(0, 20))

        employer_title = ctk.CTkLabel(
            employer_frame,
            text="🏢 Employer Information",
            font=ctk.CTkFont(size=14)
        )
        employer_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Employer name
        self.employer_entry = self._create_labeled_entry(
            employer_frame, "Employer Name:", "Enter the name of your employer"
        )

        # Employer EIN
        self.ein_entry = self._create_labeled_entry(
            employer_frame, "Employer EIN:", "Enter the employer's EIN (XX-XXXXXXX)"
        )

        # Wage information
        wage_frame = ctk.CTkFrame(self.content_frame)
        wage_frame.pack(fill="x", pady=(0, 20))

        wage_title = ctk.CTkLabel(
            wage_frame,
            text="💰 Wage Information",
            font=ctk.CTkFont(size=14)
        )
        wage_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Wages, tips, and other compensation
        self.wages_entry = self._create_labeled_currency_entry(
            wage_frame, "Wages, Tips & Other Compensation:", "Box 1 from W-2"
        )

        # Federal income tax withheld
        self.federal_tax_entry = self._create_labeled_currency_entry(
            wage_frame, "Federal Income Tax Withheld:", "Box 2 from W-2"
        )

        # Social Security wages
        self.ss_wages_entry = self._create_labeled_currency_entry(
            wage_frame, "Social Security Wages:", "Box 3 from W-2"
        )

        # Social Security tax withheld
        self.ss_tax_entry = self._create_labeled_currency_entry(
            wage_frame, "Social Security Tax Withheld:", "Box 4 from W-2"
        )

        # Medicare wages
        self.medicare_wages_entry = self._create_labeled_currency_entry(
            wage_frame, "Medicare Wages:", "Box 5 from W-2"
        )

        # Medicare tax withheld
        self.medicare_tax_entry = self._create_labeled_currency_entry(
            wage_frame, "Medicare Tax Withheld:", "Box 6 from W-2"
        )

    def _create_labeled_entry(self, parent, label_text: str, placeholder: str = ""):
        """Create a labeled entry field"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=(0, 10))

        label = ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=12))
        label.pack(anchor="w", pady=(0, 5))

        entry = ctk.CTkEntry(frame, placeholder_text=placeholder)
        entry.pack(fill="x")

        return entry

    def _create_labeled_currency_entry(self, parent, label_text: str, placeholder: str = ""):
        """Create a labeled currency entry field"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=(0, 10))

        label = ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=12))
        label.pack(anchor="w", pady=(0, 5))

        entry_frame = ctk.CTkFrame(frame, fg_color="transparent")
        entry_frame.pack(fill="x")

        dollar_label = ctk.CTkLabel(entry_frame, text="$", font=ctk.CTkFont(size=12))
        dollar_label.pack(side="left", padx=(0, 5))

        entry = ctk.CTkEntry(entry_frame, placeholder_text=placeholder)
        entry.pack(side="left", fill="x", expand=True)

        return entry

    def _load_data(self):
        """Load existing W-2 data"""
        self.employer_entry.insert(0, self.item_data.get('employer', ''))
        self.ein_entry.insert(0, self.item_data.get('ein', ''))
        self.wages_entry.insert(0, self._format_currency(self.item_data.get('wages', 0)))
        self.federal_tax_entry.insert(0, self._format_currency(self.item_data.get('federal_tax_withheld', 0)))
        self.ss_wages_entry.insert(0, self._format_currency(self.item_data.get('ss_wages', 0)))
        self.ss_tax_entry.insert(0, self._format_currency(self.item_data.get('ss_tax_withheld', 0)))
        self.medicare_wages_entry.insert(0, self._format_currency(self.item_data.get('medicare_wages', 0)))
        self.medicare_tax_entry.insert(0, self._format_currency(self.item_data.get('medicare_tax_withheld', 0)))

    def _format_currency(self, amount: float) -> str:
        """Format amount as currency string"""
        return f"{amount:,.2f}"

    def _parse_currency(self, currency_str: str) -> float:
        """Parse currency string to float"""
        try:
            # Remove commas and dollar signs
            clean_str = currency_str.replace(',', '').replace('$', '').strip()
            return float(clean_str)
        except ValueError:
            return 0.0

    def _validate_data(self) -> tuple[bool, str]:
        """Validate W-2 data"""
        if not self.employer_entry.get().strip():
            return False, "Employer name is required."

        wages = self._parse_currency(self.wages_entry.get())
        if wages <= 0:
            return False, "Wages must be greater than zero."

        return True, ""

    def _collect_data(self) -> Dict[str, Any]:
        """Collect W-2 data from form"""
        return {
            'employer': self.employer_entry.get().strip(),
            'ein': self.ein_entry.get().strip(),
            'wages': self._parse_currency(self.wages_entry.get()),
            'federal_tax_withheld': self._parse_currency(self.federal_tax_entry.get()),
            'ss_wages': self._parse_currency(self.ss_wages_entry.get()),
            'ss_tax_withheld': self._parse_currency(self.ss_tax_entry.get()),
            'medicare_wages': self._parse_currency(self.medicare_wages_entry.get()),
            'medicare_tax_withheld': self._parse_currency(self.medicare_tax_entry.get())
        }


class ModernInterestDialog(ModernIncomeDialog):
    """Dialog for entering interest income"""

    def __init__(self, parent, config, on_save: Callable[[Dict[str, Any]], None],
                 item_data: Optional[Dict[str, Any]] = None, edit_index: Optional[int] = None):
        super().__init__(parent, config, "Add Interest Income", on_save, item_data, edit_index)

    def _build_form_content(self):
        """Build the interest income form content"""
        # Payer information
        payer_frame = ctk.CTkFrame(self.content_frame)
        payer_frame.pack(fill="x", pady=(0, 20))

        payer_title = ctk.CTkLabel(
            payer_frame,
            text="🏦 Payer Information",
            font=ctk.CTkFont(size=14)
        )
        payer_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Payer name
        self.payer_entry = self._create_labeled_entry(
            payer_frame, "Payer Name:", "Name of bank or financial institution"
        )

        # Payer EIN
        self.ein_entry = self._create_labeled_entry(
            payer_frame, "Payer EIN:", "Enter the payer's EIN (XX-XXXXXXX)"
        )

        # Interest information
        interest_frame = ctk.CTkFrame(self.content_frame)
        interest_frame.pack(fill="x", pady=(0, 20))

        interest_title = ctk.CTkLabel(
            interest_frame,
            text="💰 Interest Information",
            font=ctk.CTkFont(size=14)
        )
        interest_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Interest amount
        self.amount_entry = self._create_labeled_currency_entry(
            interest_frame, "Interest Amount:", "Box 1 from Form 1099-INT"
        )

        # Tax-exempt interest
        self.tax_exempt_entry = self._create_labeled_currency_entry(
            interest_frame, "Tax-Exempt Interest:", "Box 8 from Form 1099-INT"
        )

        # Federal tax withheld
        self.federal_tax_entry = self._create_labeled_currency_entry(
            interest_frame, "Federal Tax Withheld:", "Box 4 from Form 1099-INT"
        )

    def _create_labeled_entry(self, parent, label_text: str, placeholder: str = ""):
        """Create a labeled entry field"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=(0, 10))

        label = ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=12))
        label.pack(anchor="w", pady=(0, 5))

        entry = ctk.CTkEntry(frame, placeholder_text=placeholder)
        entry.pack(fill="x")

        return entry

    def _create_labeled_currency_entry(self, parent, label_text: str, placeholder: str = ""):
        """Create a labeled currency entry field"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=(0, 10))

        label = ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=12))
        label.pack(anchor="w", pady=(0, 5))

        entry_frame = ctk.CTkFrame(frame, fg_color="transparent")
        entry_frame.pack(fill="x")

        dollar_label = ctk.CTkLabel(entry_frame, text="$", font=ctk.CTkFont(size=12))
        dollar_label.pack(side="left", padx=(0, 5))

        entry = ctk.CTkEntry(entry_frame, placeholder_text=placeholder)
        entry.pack(side="left", fill="x", expand=True)

        return entry

    def _load_data(self):
        """Load existing interest data"""
        self.payer_entry.insert(0, self.item_data.get('payer', ''))
        self.ein_entry.insert(0, self.item_data.get('ein', ''))
        self.amount_entry.insert(0, self._format_currency(self.item_data.get('amount', 0)))
        self.tax_exempt_entry.insert(0, self._format_currency(self.item_data.get('tax_exempt', 0)))
        self.federal_tax_entry.insert(0, self._format_currency(self.item_data.get('federal_tax_withheld', 0)))

    def _format_currency(self, amount: float) -> str:
        """Format amount as currency string"""
        return f"{amount:,.2f}"

    def _parse_currency(self, currency_str: str) -> float:
        """Parse currency string to float"""
        try:
            # Remove commas and dollar signs
            clean_str = currency_str.replace(',', '').replace('$', '').strip()
            return float(clean_str)
        except ValueError:
            return 0.0

    def _validate_data(self) -> tuple[bool, str]:
        """Validate interest data"""
        if not self.payer_entry.get().strip():
            return False, "Payer name is required."

        amount = self._parse_currency(self.amount_entry.get())
        if amount < 0:
            return False, "Interest amount cannot be negative."

        return True, ""

    def _collect_data(self) -> Dict[str, Any]:
        """Collect interest data from form"""
        return {
            'payer': self.payer_entry.get().strip(),
            'ein': self.ein_entry.get().strip(),
            'amount': self._parse_currency(self.amount_entry.get()),
            'tax_exempt': self._parse_currency(self.tax_exempt_entry.get()),
            'federal_tax_withheld': self._parse_currency(self.federal_tax_entry.get())
        }


class ModernDividendDialog(ModernIncomeDialog):
    """Dialog for entering dividend income"""

    def __init__(self, parent, config, on_save: Callable[[Dict[str, Any]], None],
                 item_data: Optional[Dict[str, Any]] = None, edit_index: Optional[int] = None):
        super().__init__(parent, config, "Add Dividend Income", on_save, item_data, edit_index)

    def _build_form_content(self):
        """Build the dividend income form content"""
        # Payer information
        payer_frame = ctk.CTkFrame(self.content_frame)
        payer_frame.pack(fill="x", pady=(0, 20))

        payer_title = ctk.CTkLabel(
            payer_frame,
            text="🏢 Payer Information",
            font=ctk.CTkFont(size=14)
        )
        payer_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Payer name
        self.payer_entry = self._create_labeled_entry(
            payer_frame, "Payer Name:", "Name of corporation or mutual fund"
        )

        # Payer EIN
        self.ein_entry = self._create_labeled_entry(
            payer_frame, "Payer EIN:", "Enter the payer's EIN (XX-XXXXXXX)"
        )

        # Dividend information
        dividend_frame = ctk.CTkFrame(self.content_frame)
        dividend_frame.pack(fill="x", pady=(0, 20))

        dividend_title = ctk.CTkLabel(
            dividend_frame,
            text="📈 Dividend Information",
            font=ctk.CTkFont(size=14)
        )
        dividend_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Ordinary dividends
        self.ordinary_dividends_entry = self._create_labeled_currency_entry(
            dividend_frame, "Ordinary Dividends:", "Box 1a from Form 1099-DIV"
        )

        # Qualified dividends
        self.qualified_dividends_entry = self._create_labeled_currency_entry(
            dividend_frame, "Qualified Dividends:", "Box 1b from Form 1099-DIV"
        )

        # Total dividends
        self.total_dividends_entry = self._create_labeled_currency_entry(
            dividend_frame, "Total Dividends:", "Box 1a + 1b from Form 1099-DIV"
        )

        # Federal tax withheld
        self.federal_tax_entry = self._create_labeled_currency_entry(
            dividend_frame, "Federal Tax Withheld:", "Box 4 from Form 1099-DIV"
        )

    def _create_labeled_entry(self, parent, label_text: str, placeholder: str = ""):
        """Create a labeled entry field"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=(0, 10))

        label = ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=12))
        label.pack(anchor="w", pady=(0, 5))

        entry = ctk.CTkEntry(frame, placeholder_text=placeholder)
        entry.pack(fill="x")

        return entry

    def _create_labeled_currency_entry(self, parent, label_text: str, placeholder: str = ""):
        """Create a labeled currency entry field"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=(0, 10))

        label = ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=12))
        label.pack(anchor="w", pady=(0, 5))

        entry_frame = ctk.CTkFrame(frame, fg_color="transparent")
        entry_frame.pack(fill="x")

        dollar_label = ctk.CTkLabel(entry_frame, text="$", font=ctk.CTkFont(size=12))
        dollar_label.pack(side="left", padx=(0, 5))

        entry = ctk.CTkEntry(entry_frame, placeholder_text=placeholder)
        entry.pack(side="left", fill="x", expand=True)

        return entry

    def _load_data(self):
        """Load existing dividend data"""
        self.payer_entry.insert(0, self.item_data.get('payer', ''))
        self.ein_entry.insert(0, self.item_data.get('ein', ''))
        self.ordinary_dividends_entry.insert(0, self._format_currency(self.item_data.get('ordinary_dividends', 0)))
        self.qualified_dividends_entry.insert(0, self._format_currency(self.item_data.get('qualified_dividends', 0)))
        self.total_dividends_entry.insert(0, self._format_currency(self.item_data.get('total_dividends', 0)))
        self.federal_tax_entry.insert(0, self._format_currency(self.item_data.get('federal_tax_withheld', 0)))

    def _format_currency(self, amount: float) -> str:
        """Format amount as currency string"""
        return f"{amount:,.2f}"

    def _parse_currency(self, currency_str: str) -> float:
        """Parse currency string to float"""
        try:
            # Remove commas and dollar signs
            clean_str = currency_str.replace(',', '').replace('$', '').strip()
            return float(clean_str)
        except ValueError:
            return 0.0

    def _validate_data(self) -> tuple[bool, str]:
        """Validate dividend data"""
        if not self.payer_entry.get().strip():
            return False, "Payer name is required."

        ordinary = self._parse_currency(self.ordinary_dividends_entry.get())
        qualified = self._parse_currency(self.qualified_dividends_entry.get())
        total = self._parse_currency(self.total_dividends_entry.get())

        if ordinary < 0 or qualified < 0 or total < 0:
            return False, "Dividend amounts cannot be negative."

        if total != (ordinary + qualified):
            return False, "Total dividends should equal ordinary + qualified dividends."

        return True, ""

    def _collect_data(self) -> Dict[str, Any]:
        """Collect dividend data from form"""
        return {
            'payer': self.payer_entry.get().strip(),
            'ein': self.ein_entry.get().strip(),
            'ordinary_dividends': self._parse_currency(self.ordinary_dividends_entry.get()),
            'qualified_dividends': self._parse_currency(self.qualified_dividends_entry.get()),
            'total_dividends': self._parse_currency(self.total_dividends_entry.get()),
            'federal_tax_withheld': self._parse_currency(self.federal_tax_entry.get())
        }


class ModernSelfEmploymentDialog(ModernIncomeDialog):
    """Dialog for entering self-employment income"""

    def __init__(self, parent, config, on_save: Callable[[Dict[str, Any]], None],
                 item_data: Optional[Dict[str, Any]] = None, edit_index: Optional[int] = None):
        super().__init__(parent, config, "Add Self-Employment Income", on_save, item_data, edit_index)

    def _build_form_content(self):
        """Build the self-employment form content"""
        # Create tabbed interface
        self.tabview = ctk.CTkTabview(self.content_frame)
        self.tabview.pack(fill="both", expand=True)

        # Business Info tab
        self._build_business_tab()

        # Income tab
        self._build_income_tab()

        # Expenses tab
        self._build_expenses_tab()

        # Vehicle tab
        self._build_vehicle_tab()

        # Home Office tab
        self._build_home_office_tab()

    def _build_business_tab(self):
        """Build the business information tab"""
        business_tab = self.tabview.add("Business Info")

        business_frame = ctk.CTkFrame(business_tab, fg_color="transparent")
        business_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Business name
        self.business_name_entry = self._create_labeled_entry(
            business_frame, "Business Name:", "Name of your business or trade"
        )

        # Business type
        self.business_type_entry = self._create_labeled_entry(
            business_frame, "Business Type:", "Type of business (e.g., consulting, retail)"
        )

        # Business address
        self.business_address_entry = self._create_labeled_entry(
            business_frame, "Business Address:", "Business location address"
        )

        # Business EIN
        self.business_ein_entry = self._create_labeled_entry(
            business_frame, "Business EIN:", "Employer Identification Number (XX-XXXXXXX)"
        )

        # Accounting method
        accounting_frame = ctk.CTkFrame(business_frame, fg_color="transparent")
        accounting_frame.pack(fill="x", pady=(10, 0))

        accounting_label = ctk.CTkLabel(
            accounting_frame, text="Accounting Method:",
            font=ctk.CTkFont(size=12)
        )
        accounting_label.pack(anchor="w", pady=(0, 5))

        self.accounting_method = ctk.StringVar(value="cash")
        cash_radio = ctk.CTkRadioButton(
            accounting_frame, text="Cash", variable=self.accounting_method, value="cash"
        )
        cash_radio.pack(anchor="w", pady=(0, 5))

        accrual_radio = ctk.CTkRadioButton(
            accounting_frame, text="Accrual", variable=self.accounting_method, value="accrual"
        )
        accrual_radio.pack(anchor="w")

    def _build_income_tab(self):
        """Build the income tab"""
        income_tab = self.tabview.add("Income")

        income_frame = ctk.CTkFrame(income_tab, fg_color="transparent")
        income_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Gross receipts
        self.gross_receipts_entry = self._create_labeled_currency_entry(
            income_frame, "Gross Receipts:", "Total income from all sources"
        )

        # Returns and allowances
        self.returns_allowances_entry = self._create_labeled_currency_entry(
            income_frame, "Returns and Allowances:", "Refunds, credits, or allowances"
        )

        # Net profit calculation
        net_frame = ctk.CTkFrame(income_frame)
        net_frame.pack(fill="x", pady=(20, 0))

        net_title = ctk.CTkLabel(
            net_frame,
            text="📊 Net Profit Calculation",
            font=ctk.CTkFont(size=14)
        )
        net_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Net profit (calculated)
        self.net_profit_label = ctk.CTkLabel(
            net_frame,
            text="Net Profit: $0.00",
            font=ctk.CTkFont(size=12)
        )
        self.net_profit_label.pack(anchor="w", padx=15, pady=(0, 15))

        # Bind events to update calculation
        self.gross_receipts_entry.bind("<KeyRelease>", self._update_net_profit)
        self.returns_allowances_entry.bind("<KeyRelease>", self._update_net_profit)

    def _build_expenses_tab(self):
        """Build the expenses tab"""
        expenses_tab = self.tabview.add("Expenses")

        expenses_frame = ctk.CTkFrame(expenses_tab, fg_color="transparent")
        expenses_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Common business expenses
        expenses = [
            ("Advertising", "advertising"),
            ("Car and Truck Expenses", "car_truck"),
            ("Commissions and Fees", "commissions"),
            ("Contract Labor", "contract_labor"),
            ("Depletion", "depletion"),
            ("Depreciation", "depreciation"),
            ("Employee Benefit Programs", "employee_benefits"),
            ("Insurance", "insurance"),
            ("Interest", "interest_expense"),
            ("Legal and Professional Services", "legal_professional"),
            ("Office Expense", "office_expense"),
            ("Pension and Profit-Sharing Plans", "pension_plans"),
            ("Rent or Lease", "rent_lease"),
            ("Repairs and Maintenance", "repairs_maintenance"),
            ("Supplies", "supplies"),
            ("Taxes and Licenses", "taxes_licenses"),
            ("Travel", "travel"),
            ("Utilities", "utilities"),
            ("Wages", "wages_expense"),
            ("Other Expenses", "other_expenses")
        ]

        self.expense_entries = {}
        for label_text, key in expenses:
            entry = self._create_labeled_currency_entry(expenses_frame, f"{label_text}:", "")
            self.expense_entries[key] = entry

        # Total expenses label
        self.total_expenses_label = ctk.CTkLabel(
            expenses_frame,
            text="Total Expenses: $0.00",
            font=ctk.CTkFont(size=12)
        )
        self.total_expenses_label.pack(anchor="w", padx=15, pady=(20, 0))

        # Bind events to update total
        for entry in self.expense_entries.values():
            entry.bind("<KeyRelease>", self._update_total_expenses)

    def _build_vehicle_tab(self):
        """Build the vehicle expenses tab"""
        vehicle_tab = self.tabview.add("Vehicle")

        vehicle_frame = ctk.CTkFrame(vehicle_tab, fg_color="transparent")
        vehicle_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Vehicle method
        method_frame = ctk.CTkFrame(vehicle_frame, fg_color="transparent")
        method_frame.pack(fill="x", pady=(0, 20))

        method_label = ctk.CTkLabel(
            method_frame, text="Vehicle Expense Method:",
            font=ctk.CTkFont(size=12)
        )
        method_label.pack(anchor="w", pady=(0, 5))

        self.vehicle_method = ctk.StringVar(value="standard_mileage")
        mileage_radio = ctk.CTkRadioButton(
            method_frame, text="Standard Mileage Rate",
            variable=self.vehicle_method, value="standard_mileage"
        )
        mileage_radio.pack(anchor="w", pady=(0, 5))

        actual_radio = ctk.CTkRadioButton(
            method_frame, text="Actual Expenses",
            variable=self.vehicle_method, value="actual_expenses"
        )
        actual_radio.pack(anchor="w")

        # Mileage information
        mileage_frame = ctk.CTkFrame(vehicle_frame)
        mileage_frame.pack(fill="x", pady=(0, 20))

        mileage_title = ctk.CTkLabel(
            mileage_frame,
            text="🛣️ Mileage Information",
            font=ctk.CTkFont(size=14)
        )
        mileage_title.pack(anchor="w", padx=15, pady=(15, 10))

        self.business_miles_entry = self._create_labeled_entry(
            mileage_frame, "Business Miles Driven:", "Total business miles for the year"
        )

        self.mileage_rate_entry = self._create_labeled_entry(
            mileage_frame, "Mileage Rate (per mile):", "IRS standard rate (e.g., 0.67)"
        )

        # Actual expenses
        actual_frame = ctk.CTkFrame(vehicle_frame)
        actual_frame.pack(fill="x", pady=(0, 20))

        actual_title = ctk.CTkLabel(
            actual_frame,
            text="🚗 Actual Vehicle Expenses",
            font=ctk.CTkFont(size=14)
        )
        actual_title.pack(anchor="w", padx=15, pady=(15, 10))

        self.gas_fuel_entry = self._create_labeled_currency_entry(actual_frame, "Gas/Fuel:", "")
        self.maintenance_entry = self._create_labeled_currency_entry(actual_frame, "Maintenance:", "")
        self.insurance_entry = self._create_labeled_currency_entry(actual_frame, "Insurance:", "")
        self.vehicle_depreciation_entry = self._create_labeled_currency_entry(actual_frame, "Depreciation:", "")
        self.vehicle_lease_entry = self._create_labeled_currency_entry(actual_frame, "Lease Payments:", "")

    def _build_home_office_tab(self):
        """Build the home office expenses tab"""
        home_tab = self.tabview.add("Home Office")

        home_frame = ctk.CTkFrame(home_tab, fg_color="transparent")
        home_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Home office method
        method_frame = ctk.CTkFrame(home_frame, fg_color="transparent")
        method_frame.pack(fill="x", pady=(0, 20))

        method_label = ctk.CTkLabel(
            method_frame, text="Home Office Method:",
            font=ctk.CTkFont(size=12)
        )
        method_label.pack(anchor="w", pady=(0, 5))

        self.home_office_method = ctk.StringVar(value="simplified")
        simplified_radio = ctk.CTkRadioButton(
            method_frame, text="Simplified Method ($5 per sq ft, max 300 sq ft)",
            variable=self.home_office_method, value="simplified"
        )
        simplified_radio.pack(anchor="w", pady=(0, 5))

        actual_radio = ctk.CTkRadioButton(
            method_frame, text="Actual Expenses",
            variable=self.home_office_method, value="actual"
        )
        actual_radio.pack(anchor="w")

        # Simplified method
        simplified_frame = ctk.CTkFrame(home_frame)
        simplified_frame.pack(fill="x", pady=(0, 20))

        simplified_title = ctk.CTkLabel(
            simplified_frame,
            text="🏠 Simplified Method",
            font=ctk.CTkFont(size=14)
        )
        simplified_title.pack(anchor="w", padx=15, pady=(15, 10))

        self.office_sq_ft_entry = self._create_labeled_entry(
            simplified_frame, "Office Square Footage:", "Square feet used exclusively for business"
        )

        # Actual expenses method
        actual_frame = ctk.CTkFrame(home_frame)
        actual_frame.pack(fill="x", pady=(0, 20))

        actual_title = ctk.CTkLabel(
            actual_frame,
            text="🏠 Actual Home Office Expenses",
            font=ctk.CTkFont(size=14)
        )
        actual_title.pack(anchor="w", padx=15, pady=(15, 10))

        self.rent_mortgage_entry = self._create_labeled_currency_entry(actual_frame, "Rent/Mortgage:", "")
        self.utilities_home_entry = self._create_labeled_currency_entry(actual_frame, "Utilities:", "")
        self.home_insurance_entry = self._create_labeled_currency_entry(actual_frame, "Home Insurance:", "")
        self.repairs_home_entry = self._create_labeled_currency_entry(actual_frame, "Repairs:", "")
        self.depreciation_home_entry = self._create_labeled_currency_entry(actual_frame, "Depreciation:", "")

        self.total_home_sq_ft_entry = self._create_labeled_entry(
            actual_frame, "Total Home Square Footage:", "Total square footage of your home"
        )

    def _create_labeled_entry(self, parent, label_text: str, placeholder: str = ""):
        """Create a labeled entry field"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 10))

        label = ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=12))
        label.pack(anchor="w", pady=(0, 5))

        entry = ctk.CTkEntry(frame, placeholder_text=placeholder)
        entry.pack(fill="x")

        return entry

    def _create_labeled_currency_entry(self, parent, label_text: str, placeholder: str = ""):
        """Create a labeled currency entry field"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 10))

        label = ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=12))
        label.pack(anchor="w", pady=(0, 5))

        entry_frame = ctk.CTkFrame(frame, fg_color="transparent")
        entry_frame.pack(fill="x")

        dollar_label = ctk.CTkLabel(entry_frame, text="$", font=ctk.CTkFont(size=12))
        dollar_label.pack(side="left", padx=(0, 5))

        entry = ctk.CTkEntry(entry_frame, placeholder_text=placeholder)
        entry.pack(side="left", fill="x", expand=True)

        return entry

    def _update_net_profit(self, event=None):
        """Update the net profit calculation"""
        gross = self._parse_currency(self.gross_receipts_entry.get())
        returns = self._parse_currency(self.returns_allowances_entry.get())
        net = gross - returns
        self.net_profit_label.configure(text=f"Net Profit: ${net:,.2f}")

    def _update_total_expenses(self, event=None):
        """Update the total expenses calculation"""
        total = sum(self._parse_currency(entry.get()) for entry in self.expense_entries.values())
        self.total_expenses_label.configure(text=f"Total Expenses: ${total:,.2f}")

    def _load_data(self):
        """Load existing self-employment data"""
        # Business info
        self.business_name_entry.insert(0, self.item_data.get('business_name', ''))
        self.business_type_entry.insert(0, self.item_data.get('business_type', ''))
        self.business_address_entry.insert(0, self.item_data.get('business_address', ''))
        self.business_ein_entry.insert(0, self.item_data.get('business_ein', ''))
        self.accounting_method.set(self.item_data.get('accounting_method', 'cash'))

        # Income
        self.gross_receipts_entry.insert(0, self._format_currency(self.item_data.get('gross_receipts', 0)))
        self.returns_allowances_entry.insert(0, self._format_currency(self.item_data.get('returns_allowances', 0)))

        # Expenses
        expenses = self.item_data.get('expenses', {})
        for key, entry in self.expense_entries.items():
            entry.insert(0, self._format_currency(expenses.get(key, 0)))

        # Vehicle
        self.vehicle_method.set(self.item_data.get('vehicle_method', 'standard_mileage'))
        vehicle = self.item_data.get('vehicle', {})
        self.business_miles_entry.insert(0, str(vehicle.get('business_miles', '')))
        self.mileage_rate_entry.insert(0, str(vehicle.get('mileage_rate', '')))
        self.gas_fuel_entry.insert(0, self._format_currency(vehicle.get('gas_fuel', 0)))
        self.maintenance_entry.insert(0, self._format_currency(vehicle.get('maintenance', 0)))
        self.insurance_entry.insert(0, self._format_currency(vehicle.get('insurance', 0)))
        self.vehicle_depreciation_entry.insert(0, self._format_currency(vehicle.get('depreciation', 0)))
        self.vehicle_lease_entry.insert(0, self._format_currency(vehicle.get('lease', 0)))

        # Home office
        self.home_office_method.set(self.item_data.get('home_office_method', 'simplified'))
        home_office = self.item_data.get('home_office', {})
        self.office_sq_ft_entry.insert(0, str(home_office.get('office_sq_ft', '')))
        self.rent_mortgage_entry.insert(0, self._format_currency(home_office.get('rent_mortgage', 0)))
        self.utilities_home_entry.insert(0, self._format_currency(home_office.get('utilities', 0)))
        self.home_insurance_entry.insert(0, self._format_currency(home_office.get('insurance', 0)))
        self.repairs_home_entry.insert(0, self._format_currency(home_office.get('repairs', 0)))
        self.depreciation_home_entry.insert(0, self._format_currency(home_office.get('depreciation', 0)))
        self.total_home_sq_ft_entry.insert(0, str(home_office.get('total_home_sq_ft', '')))

        # Update calculations
        self._update_net_profit()
        self._update_total_expenses()

    def _format_currency(self, amount: float) -> str:
        """Format amount as currency string"""
        return f"{amount:,.2f}"

    def _parse_currency(self, currency_str: str) -> float:
        """Parse currency string to float"""
        try:
            # Remove commas and dollar signs
            clean_str = currency_str.replace(',', '').replace('$', '').strip()
            return float(clean_str)
        except ValueError:
            return 0.0

    def _validate_data(self) -> tuple[bool, str]:
        """Validate self-employment data"""
        if not self.business_name_entry.get().strip():
            return False, "Business name is required."

        gross = self._parse_currency(self.gross_receipts_entry.get())
        if gross < 0:
            return False, "Gross receipts cannot be negative."

        return True, ""

    def _collect_data(self) -> Dict[str, Any]:
        """Collect self-employment data from form"""
        # Collect expenses
        expenses = {}
        for key, entry in self.expense_entries.items():
            expenses[key] = self._parse_currency(entry.get())

        # Collect vehicle data
        vehicle = {
            'method': self.vehicle_method.get(),
            'business_miles': int(self.business_miles_entry.get() or 0),
            'mileage_rate': float(self.mileage_rate_entry.get() or 0),
            'gas_fuel': self._parse_currency(self.gas_fuel_entry.get()),
            'maintenance': self._parse_currency(self.maintenance_entry.get()),
            'insurance': self._parse_currency(self.insurance_entry.get()),
            'depreciation': self._parse_currency(self.vehicle_depreciation_entry.get()),
            'lease': self._parse_currency(self.vehicle_lease_entry.get())
        }

        # Collect home office data
        home_office = {
            'method': self.home_office_method.get(),
            'office_sq_ft': int(self.office_sq_ft_entry.get() or 0),
            'rent_mortgage': self._parse_currency(self.rent_mortgage_entry.get()),
            'utilities': self._parse_currency(self.utilities_home_entry.get()),
            'insurance': self._parse_currency(self.home_insurance_entry.get()),
            'repairs': self._parse_currency(self.repairs_home_entry.get()),
            'depreciation': self._parse_currency(self.depreciation_home_entry.get()),
            'total_home_sq_ft': int(self.total_home_sq_ft_entry.get() or 0)
        }

        # Calculate net profit
        gross_receipts = self._parse_currency(self.gross_receipts_entry.get())
        returns_allowances = self._parse_currency(self.returns_allowances_entry.get())
        total_expenses = sum(expenses.values())

        # Add vehicle expenses to total
        if vehicle['method'] == 'standard_mileage':
            vehicle_expense = vehicle['business_miles'] * vehicle['mileage_rate']
        else:
            vehicle_expense = (vehicle['gas_fuel'] + vehicle['maintenance'] + vehicle['insurance'] +
                             vehicle['depreciation'] + vehicle['lease'])
        total_expenses += vehicle_expense

        # Add home office expenses
        if home_office['method'] == 'simplified':
            home_office_expense = min(home_office['office_sq_ft'] * 5, 1500)  # $5 per sq ft, max $1500
        else:
            home_office_expense = (home_office['rent_mortgage'] + home_office['utilities'] +
                                 home_office['insurance'] + home_office['repairs'] +
                                 home_office['depreciation'])
            if home_office['total_home_sq_ft'] > 0:
                business_percentage = home_office['office_sq_ft'] / home_office['total_home_sq_ft']
                home_office_expense *= business_percentage

        total_expenses += home_office_expense
        net_profit = gross_receipts - returns_allowances - total_expenses

        return {
            'business_name': self.business_name_entry.get().strip(),
            'business_type': self.business_type_entry.get().strip(),
            'business_address': self.business_address_entry.get().strip(),
            'business_ein': self.business_ein_entry.get().strip(),
            'accounting_method': self.accounting_method.get(),
            'gross_receipts': gross_receipts,
            'returns_allowances': returns_allowances,
            'expenses': expenses,
            'vehicle': vehicle,
            'home_office': home_office,
            'total_expenses': total_expenses,
            'net_profit': net_profit
        }


class ModernRetirementDialog(ModernIncomeDialog):
    """Dialog for entering retirement distributions"""

    def __init__(self, parent, config, on_save: Callable[[Dict[str, Any]], None],
                 item_data: Optional[Dict[str, Any]] = None, edit_index: Optional[int] = None):
        super().__init__(parent, config, "Add Retirement Distribution", on_save, item_data, edit_index)

    def _build_form_content(self):
        """Build the retirement distribution form content"""
        # Payer information
        payer_frame = ctk.CTkFrame(self.content_frame)
        payer_frame.pack(fill="x", pady=(0, 20))

        payer_title = ctk.CTkLabel(
            payer_frame,
            text="🏦 Payer Information",
            font=ctk.CTkFont(size=14)
        )
        payer_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Payer name
        self.payer_entry = self._create_labeled_entry(
            payer_frame, "Payer Name:", "Name of financial institution or plan administrator"
        )

        # Account type
        account_frame = ctk.CTkFrame(payer_frame, fg_color="transparent")
        account_frame.pack(fill="x", pady=(10, 0))

        account_label = ctk.CTkLabel(
            account_frame, text="Account Type:",
            font=ctk.CTkFont(size=12)
        )
        account_label.pack(anchor="w", pady=(0, 5))

        self.account_type = ctk.StringVar(value="ira")
        ira_radio = ctk.CTkRadioButton(
            account_frame, text="IRA", variable=self.account_type, value="ira"
        )
        ira_radio.pack(anchor="w", pady=(0, 5))

        roth_radio = ctk.CTkRadioButton(
            account_frame, text="Roth IRA", variable=self.account_type, value="roth_ira"
        )
        roth_radio.pack(anchor="w", pady=(0, 5))

        sep_radio = ctk.CTkRadioButton(
            account_frame, text="SEP IRA", variable=self.account_type, value="sep_ira"
        )
        sep_radio.pack(anchor="w", pady=(0, 5))

        simple_radio = ctk.CTkRadioButton(
            account_frame, text="SIMPLE IRA", variable=self.account_type, value="simple_ira"
        )
        simple_radio.pack(anchor="w", pady=(0, 5))

        pension_radio = ctk.CTkRadioButton(
            account_frame, text="Pension/401(k)", variable=self.account_type, value="pension_401k"
        )
        pension_radio.pack(anchor="w")

        # Distribution information
        dist_frame = ctk.CTkFrame(self.content_frame)
        dist_frame.pack(fill="x", pady=(0, 20))

        dist_title = ctk.CTkLabel(
            dist_frame,
            text="💰 Distribution Information",
            font=ctk.CTkFont(size=14)
        )
        dist_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Gross distribution
        self.gross_dist_entry = self._create_labeled_currency_entry(
            dist_frame, "Gross Distribution:", "Box 1 from Form 1099-R"
        )

        # Taxable amount
        self.taxable_amount_entry = self._create_labeled_currency_entry(
            dist_frame, "Taxable Amount:", "Box 2a from Form 1099-R"
        )

        # Federal tax withheld
        self.federal_tax_entry = self._create_labeled_currency_entry(
            dist_frame, "Federal Tax Withheld:", "Box 4 from Form 1099-R"
        )

        # Distribution code
        self.distribution_code_entry = self._create_labeled_entry(
            dist_frame, "Distribution Code:", "Box 7 from Form 1099-R (e.g., 7 for normal distribution)"
        )

    def _create_labeled_entry(self, parent, label_text: str, placeholder: str = ""):
        """Create a labeled entry field"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=(0, 10))

        label = ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=12))
        label.pack(anchor="w", pady=(0, 5))

        entry = ctk.CTkEntry(frame, placeholder_text=placeholder)
        entry.pack(fill="x")

        return entry

    def _create_labeled_currency_entry(self, parent, label_text: str, placeholder: str = ""):
        """Create a labeled currency entry field"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=(0, 10))

        label = ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=12))
        label.pack(anchor="w", pady=(0, 5))

        entry_frame = ctk.CTkFrame(frame, fg_color="transparent")
        entry_frame.pack(fill="x")

        dollar_label = ctk.CTkLabel(entry_frame, text="$", font=ctk.CTkFont(size=12))
        dollar_label.pack(side="left", padx=(0, 5))

        entry = ctk.CTkEntry(entry_frame, placeholder_text=placeholder)
        entry.pack(side="left", fill="x", expand=True)

        return entry

    def _load_data(self):
        """Load existing retirement data"""
        self.payer_entry.insert(0, self.item_data.get('payer', ''))
        self.account_type.set(self.item_data.get('account_type', 'ira'))
        self.gross_dist_entry.insert(0, self._format_currency(self.item_data.get('gross_distribution', 0)))
        self.taxable_amount_entry.insert(0, self._format_currency(self.item_data.get('taxable_amount', 0)))
        self.federal_tax_entry.insert(0, self._format_currency(self.item_data.get('federal_tax_withheld', 0)))
        self.distribution_code_entry.insert(0, self.item_data.get('distribution_code', ''))

    def _format_currency(self, amount: float) -> str:
        """Format amount as currency string"""
        return f"{amount:,.2f}"

    def _parse_currency(self, currency_str: str) -> float:
        """Parse currency string to float"""
        try:
            # Remove commas and dollar signs
            clean_str = currency_str.replace(',', '').replace('$', '').strip()
            return float(clean_str)
        except ValueError:
            return 0.0

    def _validate_data(self) -> tuple[bool, str]:
        """Validate retirement data"""
        if not self.payer_entry.get().strip():
            return False, "Payer name is required."

        gross = self._parse_currency(self.gross_dist_entry.get())
        taxable = self._parse_currency(self.taxable_amount_entry.get())

        if gross < 0 or taxable < 0:
            return False, "Distribution amounts cannot be negative."

        if taxable > gross:
            return False, "Taxable amount cannot exceed gross distribution."

        return True, ""

    def _collect_data(self) -> Dict[str, Any]:
        """Collect retirement data from form"""
        return {
            'payer': self.payer_entry.get().strip(),
            'account_type': self.account_type.get(),
            'gross_distribution': self._parse_currency(self.gross_dist_entry.get()),
            'taxable_amount': self._parse_currency(self.taxable_amount_entry.get()),
            'federal_tax_withheld': self._parse_currency(self.federal_tax_entry.get()),
            'distribution_code': self.distribution_code_entry.get().strip()
        }


class ModernSocialSecurityDialog(ModernIncomeDialog):
    """Dialog for entering Social Security benefits"""

    def __init__(self, parent, config, on_save: Callable[[Dict[str, Any]], None],
                 item_data: Optional[Dict[str, Any]] = None, edit_index: Optional[int] = None):
        super().__init__(parent, config, "Add Social Security Benefits", on_save, item_data, edit_index)

    def _build_form_content(self):
        """Build the Social Security benefits form content"""
        # Benefits information
        benefits_frame = ctk.CTkFrame(self.content_frame)
        benefits_frame.pack(fill="x", pady=(0, 20))

        benefits_title = ctk.CTkLabel(
            benefits_frame,
            text="👴 Social Security Benefits",
            font=ctk.CTkFont(size=14)
        )
        benefits_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Gross benefits
        self.gross_benefits_entry = self._create_labeled_currency_entry(
            benefits_frame, "Gross Benefits Received:", "Total benefits received during the year"
        )

        # Repayment amount
        self.repayment_entry = self._create_labeled_currency_entry(
            benefits_frame, "Repayment Amount:", "Any benefits repaid to SSA"
        )

        # Net benefits calculation
        net_frame = ctk.CTkFrame(benefits_frame)
        net_frame.pack(fill="x", pady=(20, 0))

        net_title = ctk.CTkLabel(
            net_frame,
            text="📊 Net Benefits Calculation",
            font=ctk.CTkFont(size=14)
        )
        net_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Net benefits (calculated)
        self.net_benefits_label = ctk.CTkLabel(
            net_frame,
            text="Net Benefits: $0.00",
            font=ctk.CTkFont(size=12)
        )
        self.net_benefits_label.pack(anchor="w", padx=15, pady=(0, 15))

        # Bind events to update calculation
        self.gross_benefits_entry.bind("<KeyRelease>", self._update_net_benefits)
        self.repayment_entry.bind("<KeyRelease>", self._update_net_benefits)

    def _create_labeled_currency_entry(self, parent, label_text: str, placeholder: str = ""):
        """Create a labeled currency entry field"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=(0, 10))

        label = ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=12))
        label.pack(anchor="w", pady=(0, 5))

        entry_frame = ctk.CTkFrame(frame, fg_color="transparent")
        entry_frame.pack(fill="x")

        dollar_label = ctk.CTkLabel(entry_frame, text="$", font=ctk.CTkFont(size=12))
        dollar_label.pack(side="left", padx=(0, 5))

        entry = ctk.CTkEntry(entry_frame, placeholder_text=placeholder)
        entry.pack(side="left", fill="x", expand=True)

        return entry

    def _update_net_benefits(self, event=None):
        """Update the net benefits calculation"""
        gross = self._parse_currency(self.gross_benefits_entry.get())
        repayment = self._parse_currency(self.repayment_entry.get())
        net = gross - repayment
        self.net_benefits_label.configure(text=f"Net Benefits: ${net:,.2f}")

    def _load_data(self):
        """Load existing Social Security data"""
        self.gross_benefits_entry.insert(0, self._format_currency(self.item_data.get('gross_benefits', 0)))
        self.repayment_entry.insert(0, self._format_currency(self.item_data.get('repayment', 0)))
        self._update_net_benefits()

    def _format_currency(self, amount: float) -> str:
        """Format amount as currency string"""
        return f"{amount:,.2f}"

    def _parse_currency(self, currency_str: str) -> float:
        """Parse currency string to float"""
        try:
            # Remove commas and dollar signs
            clean_str = currency_str.replace(',', '').replace('$', '').strip()
            return float(clean_str)
        except ValueError:
            return 0.0

    def _validate_data(self) -> tuple[bool, str]:
        """Validate Social Security data"""
        gross = self._parse_currency(self.gross_benefits_entry.get())
        repayment = self._parse_currency(self.repayment_entry.get())

        if gross < 0 or repayment < 0:
            return False, "Benefit amounts cannot be negative."

        if repayment > gross:
            return False, "Repayment cannot exceed gross benefits."

        return True, ""

    def _collect_data(self) -> Dict[str, Any]:
        """Collect Social Security data from form"""
        gross = self._parse_currency(self.gross_benefits_entry.get())
        repayment = self._parse_currency(self.repayment_entry.get())
        net = gross - repayment

        return {
            'gross_benefits': gross,
            'repayment': repayment,
            'net_benefits': net
        }


class ModernCapitalGainDialog(ModernIncomeDialog):
    """Dialog for entering capital gains and losses"""

    def __init__(self, parent, config, on_save: Callable[[Dict[str, Any]], None],
                 item_data: Optional[Dict[str, Any]] = None, edit_index: Optional[int] = None):
        super().__init__(parent, config, "Add Capital Gain/Loss", on_save, item_data, edit_index)

    def _build_form_content(self):
        """Build the capital gain form content"""
        # Asset information
        asset_frame = ctk.CTkFrame(self.content_frame)
        asset_frame.pack(fill="x", pady=(0, 20))

        asset_title = ctk.CTkLabel(
            asset_frame,
            text="📊 Asset Information",
            font=ctk.CTkFont(size=14)
        )
        asset_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Description
        self.description_entry = self._create_labeled_entry(
            asset_frame, "Asset Description:", "Description of the asset (e.g., 100 shares of AAPL)"
        )

        # Holding period
        holding_frame = ctk.CTkFrame(asset_frame, fg_color="transparent")
        holding_frame.pack(fill="x", pady=(10, 0))

        holding_label = ctk.CTkLabel(
            holding_frame, text="Holding Period:",
            font=ctk.CTkFont(size=12)
        )
        holding_label.pack(anchor="w", pady=(0, 5))

        self.holding_period = ctk.StringVar(value="short_term")
        short_radio = ctk.CTkRadioButton(
            holding_frame, text="Short-term (held 1 year or less)",
            variable=self.holding_period, value="short_term"
        )
        short_radio.pack(anchor="w", pady=(0, 5))

        long_radio = ctk.CTkRadioButton(
            holding_frame, text="Long-term (held more than 1 year)",
            variable=self.holding_period, value="long_term"
        )
        long_radio.pack(anchor="w")

        # Transaction information
        trans_frame = ctk.CTkFrame(self.content_frame)
        trans_frame.pack(fill="x", pady=(0, 20))

        trans_title = ctk.CTkLabel(
            trans_frame,
            text="💰 Transaction Details",
            font=ctk.CTkFont(size=14)
        )
        trans_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Date acquired
        self.date_acquired_entry = self._create_labeled_entry(
            trans_frame, "Date Acquired:", "MM/DD/YYYY"
        )

        # Date sold
        self.date_sold_entry = self._create_labeled_entry(
            trans_frame, "Date Sold:", "MM/DD/YYYY"
        )

        # Sales price
        self.sales_price_entry = self._create_labeled_currency_entry(
            trans_frame, "Sales Price:", "Total amount received from sale"
        )

        # Cost basis
        self.cost_basis_entry = self._create_labeled_currency_entry(
            trans_frame, "Cost Basis:", "Original purchase price plus adjustments"
        )

        # Adjustments to basis
        self.adjustments_entry = self._create_labeled_currency_entry(
            trans_frame, "Adjustments to Basis:", "Commissions, fees, etc."
        )

        # Adjusted basis calculation
        basis_frame = ctk.CTkFrame(trans_frame)
        basis_frame.pack(fill="x", pady=(20, 0))

        basis_title = ctk.CTkLabel(
            basis_frame,
            text="📊 Adjusted Basis Calculation",
            font=ctk.CTkFont(size=14)
        )
        basis_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Adjusted basis (calculated)
        self.adjusted_basis_label = ctk.CTkLabel(
            basis_frame,
            text="Adjusted Basis: $0.00",
            font=ctk.CTkFont(size=12)
        )
        self.adjusted_basis_label.pack(anchor="w", padx=15, pady=(0, 10))

        # Gain/Loss (calculated)
        self.gain_loss_label = ctk.CTkLabel(
            basis_frame,
            text="Gain/Loss: $0.00",
            font=ctk.CTkFont(size=12)
        )
        self.gain_loss_label.pack(anchor="w", padx=15, pady=(0, 15))

        # Bind events to update calculations
        self.cost_basis_entry.bind("<KeyRelease>", self._update_calculations)
        self.adjustments_entry.bind("<KeyRelease>", self._update_calculations)
        self.sales_price_entry.bind("<KeyRelease>", self._update_calculations)

    def _create_labeled_entry(self, parent, label_text: str, placeholder: str = ""):
        """Create a labeled entry field"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=(0, 10))

        label = ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=12))
        label.pack(anchor="w", pady=(0, 5))

        entry = ctk.CTkEntry(frame, placeholder_text=placeholder)
        entry.pack(fill="x")

        return entry

    def _create_labeled_currency_entry(self, parent, label_text: str, placeholder: str = ""):
        """Create a labeled currency entry field"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=(0, 10))

        label = ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=12))
        label.pack(anchor="w", pady=(0, 5))

        entry_frame = ctk.CTkFrame(frame, fg_color="transparent")
        entry_frame.pack(fill="x")

        dollar_label = ctk.CTkLabel(entry_frame, text="$", font=ctk.CTkFont(size=12))
        dollar_label.pack(side="left", padx=(0, 5))

        entry = ctk.CTkEntry(entry_frame, placeholder_text=placeholder)
        entry.pack(side="left", fill="x", expand=True)

        return entry

    def _update_calculations(self, event=None):
        """Update the adjusted basis and gain/loss calculations"""
        cost_basis = self._parse_currency(self.cost_basis_entry.get())
        adjustments = self._parse_currency(self.adjustments_entry.get())
        sales_price = self._parse_currency(self.sales_price_entry.get())

        adjusted_basis = cost_basis + adjustments
        gain_loss = sales_price - adjusted_basis

        self.adjusted_basis_label.configure(text=f"Adjusted Basis: ${adjusted_basis:,.2f}")
        self.gain_loss_label.configure(text=f"Gain/Loss: ${gain_loss:,.2f}")

    def _load_data(self):
        """Load existing capital gain data"""
        self.description_entry.insert(0, self.item_data.get('description', ''))
        self.holding_period.set(self.item_data.get('holding_period', 'short_term'))
        self.date_acquired_entry.insert(0, self.item_data.get('date_acquired', ''))
        self.date_sold_entry.insert(0, self.item_data.get('date_sold', ''))
        self.sales_price_entry.insert(0, self._format_currency(self.item_data.get('sales_price', 0)))
        self.cost_basis_entry.insert(0, self._format_currency(self.item_data.get('cost_basis', 0)))
        self.adjustments_entry.insert(0, self._format_currency(self.item_data.get('adjustments', 0)))
        self._update_calculations()

    def _format_currency(self, amount: float) -> str:
        """Format amount as currency string"""
        return f"{amount:,.2f}"

    def _parse_currency(self, currency_str: str) -> float:
        """Parse currency string to float"""
        try:
            # Remove commas and dollar signs
            clean_str = currency_str.replace(',', '').replace('$', '').strip()
            return float(clean_str)
        except ValueError:
            return 0.0

    def _validate_data(self) -> tuple[bool, str]:
        """Validate capital gain data"""
        if not self.description_entry.get().strip():
            return False, "Asset description is required."

        sales_price = self._parse_currency(self.sales_price_entry.get())
        cost_basis = self._parse_currency(self.cost_basis_entry.get())

        if sales_price < 0 or cost_basis < 0:
            return False, "Prices cannot be negative."

        # Validate dates
        if self.date_acquired_entry.get().strip():
            try:
                datetime.strptime(self.date_acquired_entry.get().strip(), '%m/%d/%Y')
            except ValueError:
                return False, "Date acquired must be in MM/DD/YYYY format."

        if self.date_sold_entry.get().strip():
            try:
                datetime.strptime(self.date_sold_entry.get().strip(), '%m/%d/%Y')
            except ValueError:
                return False, "Date sold must be in MM/DD/YYYY format."

        return True, ""

    def _collect_data(self) -> Dict[str, Any]:
        """Collect capital gain data from form"""
        cost_basis = self._parse_currency(self.cost_basis_entry.get())
        adjustments = self._parse_currency(self.adjustments_entry.get())
        sales_price = self._parse_currency(self.sales_price_entry.get())

        adjusted_basis = cost_basis + adjustments
        gain_loss = sales_price - adjusted_basis

        return {
            'description': self.description_entry.get().strip(),
            'holding_period': self.holding_period.get(),
            'date_acquired': self.date_acquired_entry.get().strip(),
            'date_sold': self.date_sold_entry.get().strip(),
            'sales_price': sales_price,
            'cost_basis': cost_basis,
            'adjustments': adjustments,
            'adjusted_basis': adjusted_basis,
            'gain_loss': gain_loss
        }


class ModernRentalDialog(ModernIncomeDialog):
    """Dialog for entering rental income"""

    def __init__(self, parent, config, on_save: Callable[[Dict[str, Any]], None],
                 item_data: Optional[Dict[str, Any]] = None, edit_index: Optional[int] = None):
        super().__init__(parent, config, "Add Rental Income", on_save, item_data, edit_index)

    def _build_form_content(self):
        """Build the rental income form content"""
        # Property information
        property_frame = ctk.CTkFrame(self.content_frame)
        property_frame.pack(fill="x", pady=(0, 20))

        property_title = ctk.CTkLabel(
            property_frame,
            text="🏠 Property Information",
            font=ctk.CTkFont(size=14)
        )
        property_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Property address
        self.property_address_entry = self._create_labeled_entry(
            property_frame, "Property Address:", "Full address of the rental property"
        )

        # Property type
        type_frame = ctk.CTkFrame(property_frame, fg_color="transparent")
        type_frame.pack(fill="x", pady=(10, 0))

        type_label = ctk.CTkLabel(
            type_frame, text="Property Type:",
            font=ctk.CTkFont(size=12)
        )
        type_label.pack(anchor="w", pady=(0, 5))

        self.property_type = ctk.StringVar(value="residential")
        residential_radio = ctk.CTkRadioButton(
            type_frame, text="Residential", variable=self.property_type, value="residential"
        )
        residential_radio.pack(anchor="w", pady=(0, 5))

        commercial_radio = ctk.CTkRadioButton(
            type_frame, text="Commercial", variable=self.property_type, value="commercial"
        )
        commercial_radio.pack(anchor="w")

        # Income information
        income_frame = ctk.CTkFrame(self.content_frame)
        income_frame.pack(fill="x", pady=(0, 20))

        income_title = ctk.CTkLabel(
            income_frame,
            text="💰 Rental Income",
            font=ctk.CTkFont(size=14)
        )
        income_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Gross rental income
        self.gross_rental_entry = self._create_labeled_currency_entry(
            income_frame, "Gross Rental Income:", "Total rent received from all tenants"
        )

        # Expenses information
        expenses_frame = ctk.CTkFrame(self.content_frame)
        expenses_frame.pack(fill="x", pady=(0, 20))

        expenses_title = ctk.CTkLabel(
            expenses_frame,
            text="💸 Rental Expenses",
            font=ctk.CTkFont(size=14)
        )
        expenses_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Common rental expenses
        expenses = [
            ("Advertising", "advertising"),
            ("Auto/Travel", "auto_travel"),
            ("Cleaning/Maintenance", "cleaning_maintenance"),
            ("Commissions", "commissions"),
            ("Insurance", "insurance"),
            ("Legal/Professional Fees", "legal_fees"),
            ("Management Fees", "management_fees"),
            ("Mortgage Interest", "mortgage_interest"),
            ("Repairs", "repairs"),
            ("Supplies", "supplies"),
            ("Taxes", "taxes"),
            ("Utilities", "utilities"),
            ("Depreciation", "depreciation"),
            ("Other Expenses", "other_expenses")
        ]

        self.expense_entries = {}
        for label_text, key in expenses:
            entry = self._create_labeled_currency_entry(expenses_frame, f"{label_text}:", "")
            self.expense_entries[key] = entry

        # Net income calculation
        net_frame = ctk.CTkFrame(self.content_frame)
        net_frame.pack(fill="x", pady=(0, 20))

        net_title = ctk.CTkLabel(
            net_frame,
            text="📊 Net Rental Income Calculation",
            font=ctk.CTkFont(size=14)
        )
        net_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Net income (calculated)
        self.net_income_label = ctk.CTkLabel(
            net_frame,
            text="Net Rental Income: $0.00",
            font=ctk.CTkFont(size=12)
        )
        self.net_income_label.pack(anchor="w", padx=15, pady=(0, 15))

        # Bind events to update calculation
        self.gross_rental_entry.bind("<KeyRelease>", self._update_net_income)
        for entry in self.expense_entries.values():
            entry.bind("<KeyRelease>", self._update_net_income)

    def _create_labeled_entry(self, parent, label_text: str, placeholder: str = ""):
        """Create a labeled entry field"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=(0, 10))

        label = ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=12))
        label.pack(anchor="w", pady=(0, 5))

        entry = ctk.CTkEntry(frame, placeholder_text=placeholder)
        entry.pack(fill="x")

        return entry

    def _create_labeled_currency_entry(self, parent, label_text: str, placeholder: str = ""):
        """Create a labeled currency entry field"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=(0, 10))

        label = ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=12))
        label.pack(anchor="w", pady=(0, 5))

        entry_frame = ctk.CTkFrame(frame, fg_color="transparent")
        entry_frame.pack(fill="x")

        dollar_label = ctk.CTkLabel(entry_frame, text="$", font=ctk.CTkFont(size=12))
        dollar_label.pack(side="left", padx=(0, 5))

        entry = ctk.CTkEntry(entry_frame, placeholder_text=placeholder)
        entry.pack(side="left", fill="x", expand=True)

        return entry

    def _update_net_income(self, event=None):
        """Update the net rental income calculation"""
        gross = self._parse_currency(self.gross_rental_entry.get())
        total_expenses = sum(self._parse_currency(entry.get()) for entry in self.expense_entries.values())
        net = gross - total_expenses
        self.net_income_label.configure(text=f"Net Rental Income: ${net:,.2f}")

    def _load_data(self):
        """Load existing rental data"""
        self.property_address_entry.insert(0, self.item_data.get('property_address', ''))
        self.property_type.set(self.item_data.get('property_type', 'residential'))
        self.gross_rental_entry.insert(0, self._format_currency(self.item_data.get('gross_rental_income', 0)))

        # Load expenses
        expenses = self.item_data.get('expenses', {})
        for key, entry in self.expense_entries.items():
            entry.insert(0, self._format_currency(expenses.get(key, 0)))

        self._update_net_income()

    def _format_currency(self, amount: float) -> str:
        """Format amount as currency string"""
        return f"{amount:,.2f}"

    def _parse_currency(self, currency_str: str) -> float:
        """Parse currency string to float"""
        try:
            # Remove commas and dollar signs
            clean_str = currency_str.replace(',', '').replace('$', '').strip()
            return float(clean_str)
        except ValueError:
            return 0.0

    def _validate_data(self) -> tuple[bool, str]:
        """Validate rental data"""
        if not self.property_address_entry.get().strip():
            return False, "Property address is required."

        gross = self._parse_currency(self.gross_rental_entry.get())
        if gross < 0:
            return False, "Gross rental income cannot be negative."

        return True, ""

    def _collect_data(self) -> Dict[str, Any]:
        """Collect rental data from form"""
        gross_income = self._parse_currency(self.gross_rental_entry.get())
        expenses = {}
        for key, entry in self.expense_entries.items():
            expenses[key] = self._parse_currency(entry.get())

        total_expenses = sum(expenses.values())
        net_income = gross_income - total_expenses

        return {
            'property_address': self.property_address_entry.get().strip(),
            'property_type': self.property_type.get(),
            'gross_rental_income': gross_income,
            'expenses': expenses,
            'total_expenses': total_expenses,
            'net_income': net_income
        }