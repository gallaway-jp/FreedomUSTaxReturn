"""
Estate and Trust Tax Returns Window - Modernized UI

GUI for managing estate and trust tax returns (Form 1041).
Supports estates, trusts, and fiduciary income tax reporting.
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.estate_trust_service import (
    EstateTrustService,
    EstateTrustReturn,
    TrustBeneficiary,
    TrustIncome,
    TrustDeductions,
    TrustType,
    EstateType,
    IncomeDistributionType
)
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton
from utils.error_tracker import get_error_tracker


class EstateTrustWindow:
    """
    Modern window for managing estate and trust tax returns.

    Features:
    - Estate and trust return creation and management
    - Beneficiary management with modern UI
    - Income and deduction tracking
    - Form 1041 generation
    - K-1 form generation for beneficiaries
    - Tax calculation and liability estimation
    - Professional CustomTkinter interface
    """

    def __init__(self, parent: ctk.CTk, config: AppConfig, tax_data: Optional[TaxData] = None, accessibility_service: Optional[AccessibilityService] = None):
        """
        Initialize estate and trust tax returns window.

        Args:
            parent: Parent window
            config: Application configuration
            tax_data: Tax return data to analyze
            accessibility_service: Accessibility service instance
        """
        self.parent = parent
        self.config = config
        self.tax_data = tax_data
        self.accessibility_service = accessibility_service
        self.error_tracker = get_error_tracker()

        # Initialize service
        self.estate_service = EstateTrustService(config)

        # Current data
        self.returns: List[EstateTrustReturn] = []
        self.current_return: Optional[EstateTrustReturn] = None

        # UI components
        self.window: Optional[ctk.CTkToplevel] = None
        self.tabview: Optional[ctk.CTkTabview] = None
        self.progress_var: Optional[ctk.DoubleVar] = None
        self.status_label: Optional[ModernLabel] = None

        # Form variables
        self.return_vars = {}
        self.beneficiary_vars = {}
        self.income_vars = {}
        self.deduction_vars = {}
        self.summary_vars = {}
        self.tax_summary_vars = {}

    def show(self):
        """Show the estate and trust tax returns window"""
        self.window = ctk.CTkToplevel(self.parent)
        self.window.title("📋 Estate & Trust Tax Returns - Form 1041")
        self.window.geometry("1300x850")
        self.window.resizable(True, True)

        # Configure grid
        self.window.grid_rowconfigure(2, weight=1)
        self.window.grid_columnconfigure(0, weight=1)

        # Initialize UI
        self._create_header()
        self._create_toolbar()
        self._create_tabview()
        self._load_data()
        self._bind_events()

        # Make modal
        self.window.transient(self.parent)
        self.window.grab_set()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self.window)
        header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))

        title_label = ModernLabel(
            header_frame,
            text="📋 Estate & Trust Tax Returns",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(anchor="w")

        subtitle_label = ModernLabel(
            header_frame,
            text="Form 1041 - Manage estates, trusts, and fiduciary income tax reporting",
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        )
        subtitle_label.pack(anchor="w", pady=(5, 0))

    def _create_toolbar(self):
        """Create the toolbar with action buttons"""
        toolbar_frame = ModernFrame(self.window)
        toolbar_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(5, 10))

        # Action buttons
        buttons_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        buttons_frame.pack(side="left")

        ModernButton(
            buttons_frame,
            text="➕ New Return",
            command=self._new_return,
            button_type="primary"
        ).pack(side="left", padx=(0, 8))

        ModernButton(
            buttons_frame,
            text="💾 Save Return",
            command=self._save_return,
            button_type="secondary"
        ).pack(side="left", padx=(0, 8))

        ModernButton(
            buttons_frame,
            text="🧮 Calculate Tax",
            command=self._calculate_tax,
            button_type="secondary"
        ).pack(side="left", padx=(0, 8))

        ModernButton(
            buttons_frame,
            text="📄 Form 1041",
            command=self._generate_form_1041,
            button_type="secondary"
        ).pack(side="left", padx=(0, 8))

        ModernButton(
            buttons_frame,
            text="📑 K-1 Forms",
            command=self._generate_k1_forms,
            button_type="secondary"
        ).pack(side="left")

        # Progress and status
        status_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        status_frame.pack(side="right", fill="x", expand=True, padx=(10, 0))

        self.progress_var = ctk.DoubleVar(value=0)
        progress_bar = ctk.CTkProgressBar(status_frame, variable=self.progress_var)
        progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.status_label = ModernLabel(
            status_frame,
            text="Ready",
            font=ctk.CTkFont(size=10)
        )
        self.status_label.pack(side="left")

    def _create_tabview(self):
        """Create the tabview with all tabs"""
        self.tabview = ctk.CTkTabview(self.window)
        self.tabview.grid(row=2, column=0, sticky="nsew", padx=15, pady=(0, 15))

        # Create tabs
        self._setup_returns_tab()
        self._setup_entity_tab()
        self._setup_income_deductions_tab()
        self._setup_beneficiaries_tab()
        self._setup_forms_tab()

    def _setup_returns_tab(self):
        """Setup the returns management tab"""
        returns_tab = ctk.CTkScrollableFrame(self.tabview)
        self.tabview.add("Returns", returns_tab)

        # Returns list
        list_label = ModernLabel(
            returns_tab,
            text="📊 Estate & Trust Returns",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        list_label.pack(anchor="w", padx=15, pady=(15, 10))

        list_frame = ModernFrame(returns_tab)
        list_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.returns_textbox = ctk.CTkTextbox(list_frame, height=200)
        self.returns_textbox.pack(fill="both", expand=True)
        self.returns_textbox.configure(state="disabled")

        # Control buttons
        btn_frame = ctk.CTkFrame(returns_tab, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(0, 15))

        ModernButton(btn_frame, text="Load Selected", command=self._load_selected_return, button_type="secondary").pack(side="left", padx=(0, 5))
        ModernButton(btn_frame, text="Delete Return", command=self._delete_return, button_type="danger").pack(side="left")

        # Summary section
        summary_label = ModernLabel(
            returns_tab,
            text="📈 Tax Year Summary",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        summary_label.pack(anchor="w", padx=15, pady=(10, 8))

        summary_frame = ModernFrame(returns_tab)
        summary_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.summary_vars = {}
        summary_items = [
            ("Total Returns:", "total_returns", "$0"),
            ("Total Taxable Income:", "total_taxable", "$0"),
            ("Total Tax Due:", "total_tax_due", "$0"),
            ("Total Balance Due:", "total_balance", "$0"),
        ]

        summary_grid = ctk.CTkFrame(summary_frame, fg_color="transparent")
        summary_grid.pack(fill="x")

        for i, (label, key, default) in enumerate(summary_items):
            row = i // 2
            col = i % 2

            item_frame = ctk.CTkFrame(summary_grid, fg_color="transparent")
            item_frame.grid(row=row, column=col, sticky="ew", padx=(0, 20), pady=(0, 10))

            ModernLabel(item_frame, text=label, font=ctk.CTkFont(size=10), text_color="gray60").pack(anchor="w")
            value_label = ModernLabel(item_frame, text=default, font=ctk.CTkFont(size=12, weight="bold"))
            value_label.pack(anchor="w")

            self.summary_vars[key] = value_label

        summary_grid.grid_columnconfigure((0, 1), weight=1)

    def _setup_entity_tab(self):
        """Setup the entity information tab"""
        entity_tab = ctk.CTkScrollableFrame(self.tabview)
        self.tabview.add("Entity Info", entity_tab)

        # Entity information form
        title_label = ModernLabel(
            entity_tab,
            text="🏛️ Entity Information",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        title_label.pack(anchor="w", padx=15, pady=(15, 10))

        form_frame = ModernFrame(entity_tab)
        form_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Create 2-column form
        self._create_form_fields(form_frame, [
            ("Tax Year:", "tax_year", str(date.today().year - 1)),
            ("Entity Type:", "entity_type", None),
            ("Entity Name:", "entity_name", ""),
            ("EIN:", "ein", ""),
            ("Fiduciary Name:", "fiduciary_name", ""),
            ("Fiduciary Address:", "fiduciary_address", ""),
            ("Fiduciary Phone:", "fiduciary_phone", ""),
            ("Trust Type:", "trust_type", None),
            ("Estate Type:", "estate_type", None),
        ])

    def _create_form_fields(self, parent, fields):
        """Create form fields in a 2-column layout"""
        for i, field_info in enumerate(fields):
            row = i // 2
            col = i % 2

            field_frame = ctk.CTkFrame(parent, fg_color="transparent")
            field_frame.grid(row=row, column=col, sticky="ew", padx=(0, 20 if col == 0 else 0), pady=(0, 15))

            label, key, default = field_info

            ModernLabel(field_frame, text=label, font=ctk.CTkFont(size=10), text_color="gray60").pack(anchor="w", pady=(0, 5))

            if key in ["entity_type", "trust_type", "estate_type"]:
                # Create combobox for enum values
                values = []
                if key == "entity_type":
                    values = ["Estate", "Trust"]
                elif key == "trust_type":
                    values = [t.value for t in TrustType]
                elif key == "estate_type":
                    values = [e.value for e in EstateType]

                self.return_vars[key] = ctk.StringVar(value=default or "")
                combo = ctk.CTkComboBox(
                    field_frame,
                    values=values,
                    variable=self.return_vars[key],
                    state="readonly",
                    font=ctk.CTkFont(size=11)
                )
                combo.pack(fill="x")
            else:
                # Create entry for text values
                self.return_vars[key] = ctk.StringVar(value=default or "")
                entry = ctk.CTkEntry(
                    field_frame,
                    textvariable=self.return_vars[key],
                    font=ctk.CTkFont(size=11)
                )
                entry.pack(fill="x")

        parent.grid_columnconfigure((0, 1), weight=1)

    def _setup_income_deductions_tab(self):
        """Setup the income and deductions tab"""
        tab = ctk.CTkScrollableFrame(self.tabview)
        self.tabview.add("Income & Deductions", tab)

        # Split into two columns
        main_frame = ctk.CTkFrame(tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Income column
        income_label = ModernLabel(
            main_frame,
            text="💰 Income",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        income_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        income_frame = ModernFrame(main_frame)
        income_frame.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 15))

        income_fields = [
            ("Interest Income:", "interest_income"),
            ("Dividend Income:", "dividend_income"),
            ("Business Income:", "business_income"),
            ("Capital Gains:", "capital_gains"),
            ("Rental Income:", "rental_income"),
            ("Royalty Income:", "royalty_income"),
            ("Other Income:", "other_income"),
            ("Total Income:", "total_income"),
        ]

        for i, (label, key) in enumerate(income_fields):
            label_widget = ModernLabel(income_frame, text=label, text_color="gray60" if key != "total_income" else "white")
            label_widget.grid(row=i, column=0, sticky="w", pady=(0, 8))

            self.income_vars[key] = ctk.StringVar(value="0.00")
            if key == "total_income":
                entry = ctk.CTkEntry(income_frame, textvariable=self.income_vars[key], state="disabled")
            else:
                entry = ctk.CTkEntry(income_frame, textvariable=self.income_vars[key])
            entry.grid(row=i, column=1, sticky="ew", pady=(0, 8), padx=(10, 0))

        # Deductions column
        deductions_label = ModernLabel(
            main_frame,
            text="📋 Deductions",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        deductions_label.grid(row=0, column=1, sticky="w", pady=(0, 10), padx=(10, 0))

        deductions_frame = ModernFrame(main_frame)
        deductions_frame.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(0, 15))

        deduction_fields = [
            ("Fiduciary Fees:", "fiduciary_fees"),
            ("Attorney Fees:", "attorney_fees"),
            ("Accounting Fees:", "accounting_fees"),
            ("Other Admin Expenses:", "other_administrative_expenses"),
            ("Charitable Contributions:", "charitable_contributions"),
            ("Net Operating Loss:", "net_operating_loss"),
            ("Total Deductions:", "total_deductions"),
        ]

        for i, (label, key) in enumerate(deduction_fields):
            label_widget = ModernLabel(deductions_frame, text=label, text_color="gray60" if key != "total_deductions" else "white")
            label_widget.grid(row=i, column=0, sticky="w", pady=(0, 8))

            self.deduction_vars[key] = ctk.StringVar(value="0.00")
            if key == "total_deductions":
                entry = ctk.CTkEntry(deductions_frame, textvariable=self.deduction_vars[key], state="disabled")
            else:
                entry = ctk.CTkEntry(deductions_frame, textvariable=self.deduction_vars[key])
            entry.grid(row=i, column=1, sticky="ew", pady=(0, 8), padx=(10, 0))

        income_frame.grid_columnconfigure(1, weight=1)
        deductions_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_columnconfigure((0, 1), weight=1)

        # Calculate button
        calc_button = ModernButton(
            tab,
            text="🧮 Calculate Totals",
            command=self._calculate_totals,
            button_type="secondary"
        )
        calc_button.pack(pady=(0, 15))

    def _setup_beneficiaries_tab(self):
        """Setup the beneficiaries management tab"""
        beneficiaries_tab = ctk.CTkScrollableFrame(self.tabview)
        self.tabview.add("Beneficiaries", beneficiaries_tab)

        # Beneficiaries list
        list_label = ModernLabel(
            beneficiaries_tab,
            text="👥 Trust Beneficiaries",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        list_label.pack(anchor="w", padx=15, pady=(15, 10))

        list_frame = ModernFrame(beneficiaries_tab)
        list_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.beneficiaries_textbox = ctk.CTkTextbox(list_frame, height=150)
        self.beneficiaries_textbox.pack(fill="both", expand=True)
        self.beneficiaries_textbox.configure(state="disabled")

        # Beneficiary form
        form_label = ModernLabel(
            beneficiaries_tab,
            text="➕ Add/Edit Beneficiary",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        form_label.pack(anchor="w", padx=15, pady=(10, 8))

        form_frame = ModernFrame(beneficiaries_tab)
        form_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self._create_beneficiary_form(form_frame)

        # Buttons
        btn_frame = ctk.CTkFrame(beneficiaries_tab, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(0, 15))

        ModernButton(btn_frame, text="Add Beneficiary", command=self._add_beneficiary, button_type="primary").pack(side="left", padx=(0, 5))
        ModernButton(btn_frame, text="Update", command=self._update_beneficiary, button_type="secondary").pack(side="left", padx=(0, 5))
        ModernButton(btn_frame, text="Delete", command=self._delete_beneficiary, button_type="danger").pack(side="left", padx=(0, 5))
        ModernButton(btn_frame, text="Clear", command=self._clear_beneficiary_form, button_type="secondary").pack(side="left")

    def _create_beneficiary_form(self, parent):
        """Create the beneficiary form fields"""
        form_grid = ctk.CTkFrame(parent, fg_color="transparent")
        form_grid.pack(fill="x")

        beneficiary_fields = [
            ("Name:", "name"),
            ("SSN:", "ssn"),
            ("Address:", "address"),
            ("Relationship:", "relationship"),
            ("Share Percentage:", "share_percentage"),
            ("Income Distributed:", "income_distributed"),
        ]

        for i, (label, key) in enumerate(beneficiary_fields):
            row = i // 2
            col = i % 2

            field_frame = ctk.CTkFrame(form_grid, fg_color="transparent")
            field_frame.grid(row=row, column=col, sticky="ew", padx=(0, 20 if col == 0 else 0), pady=(0, 12))

            ModernLabel(field_frame, text=label, font=ctk.CTkFont(size=10), text_color="gray60").pack(anchor="w", pady=(0, 5))

            self.beneficiary_vars[key] = ctk.StringVar(value="")
            entry = ctk.CTkEntry(field_frame, textvariable=self.beneficiary_vars[key])
            entry.pack(fill="x")

        # Distribution type field
        dist_field = ctk.CTkFrame(form_grid, fg_color="transparent")
        dist_field.grid(row=3, column=0, sticky="ew", padx=(0, 20))

        ModernLabel(dist_field, text="Distribution Type:", font=ctk.CTkFont(size=10), text_color="gray60").pack(anchor="w", pady=(0, 5))

        self.beneficiary_vars['distribution_type'] = ctk.StringVar(value="")
        dist_combo = ctk.CTkComboBox(
            dist_field,
            values=[dt.value for dt in IncomeDistributionType],
            variable=self.beneficiary_vars['distribution_type'],
            state="readonly"
        )
        dist_combo.pack(fill="x")

        form_grid.grid_columnconfigure((0, 1), weight=1)

    def _setup_forms_tab(self):
        """Setup the forms and reports tab"""
        forms_tab = ctk.CTkScrollableFrame(self.tabview)
        self.tabview.add("Forms & Reports", forms_tab)

        # Form 1041 section
        form_label = ModernLabel(
            forms_tab,
            text="📄 Form 1041 - U.S. Income Tax Return for Estates and Trusts",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        form_label.pack(anchor="w", padx=15, pady=(15, 8))

        form_desc = ModernLabel(
            forms_tab,
            text="Form 1041 is used to report income, deductions, and tax liability for estates and trusts.\nThis form is filed annually and is due on the 15th day of the 4th month after the end of the tax year.",
            font=ctk.CTkFont(size=10),
            text_color="gray70"
        )
        form_desc.pack(anchor="w", padx=15, pady=(0, 8))

        ModernButton(forms_tab, text="Generate Form 1041", command=self._generate_form_1041, button_type="primary").pack(anchor="w", padx=15, pady=(0, 15))

        # K-1 forms section
        k1_label = ModernLabel(
            forms_tab,
            text="📑 Schedule K-1 (Form 1041) - Beneficiary's Share of Income",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        k1_label.pack(anchor="w", padx=15, pady=(15, 8))

        k1_desc = ModernLabel(
            forms_tab,
            text="Schedule K-1 reports each beneficiary's share of income, deductions, and credits from the estate or trust.\nA separate K-1 must be provided to each beneficiary.",
            font=ctk.CTkFont(size=10),
            text_color="gray70"
        )
        k1_desc.pack(anchor="w", padx=15, pady=(0, 8))

        ModernButton(forms_tab, text="Generate K-1 Forms", command=self._generate_k1_forms, button_type="primary").pack(anchor="w", padx=15, pady=(0, 15))

        # Tax calculation summary
        tax_label = ModernLabel(
            forms_tab,
            text="🧮 Tax Calculation Summary",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        tax_label.pack(anchor="w", padx=15, pady=(15, 8))

        tax_frame = ModernFrame(forms_tab)
        tax_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.tax_summary_vars = {}
        tax_items = [
            ("Taxable Income:", "taxable_income", "$0.00"),
            ("Tax Due:", "tax_due", "$0.00"),
            ("Payments/Credits:", "payments_credits", "$0.00"),
            ("Balance Due/Refund:", "balance_due", "$0.00"),
        ]

        for i, (label, key, default) in enumerate(tax_items):
            row_frame = ctk.CTkFrame(tax_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=(0, 8))

            ModernLabel(row_frame, text=label).pack(side="left")
            self.tax_summary_vars[key] = ModernLabel(
                row_frame,
                text=default,
                font=ctk.CTkFont(weight="bold")
            )
            self.tax_summary_vars[key].pack(side="right")

    def _load_data(self):
        """Load existing estate/trust data"""
        try:
            if self.tax_data:
                self.returns = self.estate_service.load_estate_trust_returns(self.tax_data)

            self._refresh_returns_list()
            self._refresh_beneficiaries_list()
            self._update_summary()
            self.status_label.configure(text="Data loaded successfully")

        except Exception as e:
            self.error_tracker.log_error(e, "Estate/Trust Data Loading")
            messagebox.showerror("Load Error", f"Failed to load estate/trust data: {str(e)}")

    def _refresh_returns_list(self):
        """Refresh the returns display"""
        self.returns_textbox.configure(state="normal")
        self.returns_textbox.delete("0.0", "end")

        if not self.returns:
            self.returns_textbox.insert("0.0", "No returns found")
            self.returns_textbox.configure(state="disabled")
            return

        text = "TAX YEAR  │  ENTITY TYPE  │  ENTITY NAME  │  EIN  │  TAXABLE INCOME  │  TAX DUE\n"
        text += "─" * 110 + "\n"

        for i, ret in enumerate(self.returns):
            text += f"{ret.tax_year}  │  {ret.entity_type:12} │  {(ret.entity_name or '')[:12]:12} │  {ret.ein}  │  ${ret.taxable_income:>13,.2f}  │  ${ret.tax_due:>10,.2f}\n"

        self.returns_textbox.insert("0.0", text)
        self.returns_textbox.configure(state="disabled")

    def _refresh_beneficiaries_list(self):
        """Refresh the beneficiaries display"""
        self.beneficiaries_textbox.configure(state="normal")
        self.beneficiaries_textbox.delete("0.0", "end")

        if not self.current_return or not self.current_return.beneficiaries:
            self.beneficiaries_textbox.insert("0.0", "No beneficiaries found")
            self.beneficiaries_textbox.configure(state="disabled")
            return

        text = "NAME  │  SSN  │  RELATIONSHIP  │  SHARE %  │  INCOME DISTRIBUTED  │  TYPE\n"
        text += "─" * 110 + "\n"

        for ben in self.current_return.beneficiaries:
            text += f"{ben.name[:15]:15} │  {ben.ssn}  │  {ben.relationship[:12]:12} │  {ben.share_percentage:>6.2f}%  │  ${ben.income_distributed:>18,.2f}  │  {ben.distribution_type.value}\n"

        self.beneficiaries_textbox.insert("0.0", text)
        self.beneficiaries_textbox.configure(state="disabled")

    def _update_summary(self):
        """Update the tax year summary"""
        if not self.returns:
            return

        total_returns = len(self.returns)
        total_taxable = sum(r.taxable_income for r in self.returns)
        total_tax_due = sum(r.tax_due for r in self.returns)
        total_balance = sum(r.balance_due for r in self.returns)

        self.summary_vars['total_returns'].configure(text=str(total_returns))
        self.summary_vars['total_taxable'].configure(text=f"${total_taxable:,.2f}")
        self.summary_vars['total_tax_due'].configure(text=f"${total_tax_due:,.2f}")
        self.summary_vars['total_balance'].configure(text=f"${total_balance:,.2f}")

    def _new_return(self):
        """Create a new estate/trust return"""
        try:
            self.current_return = EstateTrustReturn(
                tax_year=int(self.return_vars['tax_year'].get()),
                entity_type=self.return_vars['entity_type'].get(),
                entity_name="",
                ein="",
                fiduciary_name="",
                fiduciary_address="",
                fiduciary_phone=""
            )

            self._clear_all_forms()
            self._refresh_beneficiaries_list()
            self.status_label.configure(text="New return created")

        except Exception as e:
            messagebox.showerror("New Return Error", f"Failed to create new return: {str(e)}")

    def _load_selected_return(self):
        """Load a return from the list (placeholder)"""
        if not self.returns:
            messagebox.showwarning("No Returns", "No returns available to load")
            return

        try:
            self.current_return = self.returns[0]
            self._populate_return_form()
            self._populate_income_form()
            self._populate_deductions_form()
            self._refresh_beneficiaries_list()
            self.status_label.configure(text=f"Loaded {self.current_return.entity_type} return")

        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load return: {str(e)}")

    def _populate_return_form(self):
        """Populate the return form"""
        if not self.current_return:
            return

        self.return_vars['tax_year'].set(str(self.current_return.tax_year))
        self.return_vars['entity_type'].set(self.current_return.entity_type)
        self.return_vars['entity_name'].set(self.current_return.entity_name or "")
        self.return_vars['ein'].set(self.current_return.ein)
        self.return_vars['fiduciary_name'].set(self.current_return.fiduciary_name)
        self.return_vars['fiduciary_address'].set(self.current_return.fiduciary_address)
        self.return_vars['fiduciary_phone'].set(self.current_return.fiduciary_phone)

    def _populate_income_form(self):
        """Populate the income form"""
        if not self.current_return:
            return

        income = self.current_return.income
        self.income_vars['interest_income'].set(f"{income.interest_income:.2f}")
        self.income_vars['dividend_income'].set(f"{income.dividend_income:.2f}")
        self.income_vars['business_income'].set(f"{income.business_income:.2f}")
        self.income_vars['capital_gains'].set(f"{income.capital_gains:.2f}")
        self.income_vars['rental_income'].set(f"{income.rental_income:.2f}")
        self.income_vars['royalty_income'].set(f"{income.royalty_income:.2f}")
        self.income_vars['other_income'].set(f"{income.other_income:.2f}")
        self.income_vars['total_income'].set(f"{income.total_income:.2f}")

    def _populate_deductions_form(self):
        """Populate the deductions form"""
        if not self.current_return:
            return

        deductions = self.current_return.deductions
        self.deduction_vars['fiduciary_fees'].set(f"{deductions.fiduciary_fees:.2f}")
        self.deduction_vars['attorney_fees'].set(f"{deductions.attorney_fees:.2f}")
        self.deduction_vars['accounting_fees'].set(f"{deductions.accounting_fees:.2f}")
        self.deduction_vars['other_administrative_expenses'].set(f"{deductions.other_administrative_expenses:.2f}")
        self.deduction_vars['charitable_contributions'].set(f"{deductions.charitable_contributions:.2f}")
        self.deduction_vars['net_operating_loss'].set(f"{deductions.net_operating_loss:.2f}")
        self.deduction_vars['total_deductions'].set(f"{deductions.total_deductions:.2f}")

    def _save_return(self):
        """Save the current return"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please create or load a return first.")
            return

        try:
            self._update_return_from_form()

            if self.tax_data:
                success = self.estate_service.save_estate_trust_return(self.tax_data, self.current_return)
                if success:
                    self.returns = self.estate_service.load_estate_trust_returns(self.tax_data)
                    self._refresh_returns_list()
                    self._update_summary()
                    self.status_label.configure(text="Return saved successfully")
                else:
                    messagebox.showerror("Save Error", "Failed to save return")
            else:
                messagebox.showwarning("No Tax Data", "No tax data available to save to")

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save return: {str(e)}")

    def _update_return_from_form(self):
        """Update the current return from form data"""
        if not self.current_return:
            return

        self.current_return.tax_year = int(self.return_vars['tax_year'].get())
        self.current_return.entity_type = self.return_vars['entity_type'].get()
        self.current_return.entity_name = self.return_vars['entity_name'].get()
        self.current_return.ein = self.return_vars['ein'].get()
        self.current_return.fiduciary_name = self.return_vars['fiduciary_name'].get()
        self.current_return.fiduciary_address = self.return_vars['fiduciary_address'].get()
        self.current_return.fiduciary_phone = self.return_vars['fiduciary_phone'].get()

        self.current_return.income.interest_income = Decimal(self.income_vars['interest_income'].get())
        self.current_return.income.dividend_income = Decimal(self.income_vars['dividend_income'].get())
        self.current_return.income.business_income = Decimal(self.income_vars['business_income'].get())
        self.current_return.income.capital_gains = Decimal(self.income_vars['capital_gains'].get())
        self.current_return.income.rental_income = Decimal(self.income_vars['rental_income'].get())
        self.current_return.income.royalty_income = Decimal(self.income_vars['royalty_income'].get())
        self.current_return.income.other_income = Decimal(self.income_vars['other_income'].get())
        self.current_return.income.calculate_total()

        self.current_return.deductions.fiduciary_fees = Decimal(self.deduction_vars['fiduciary_fees'].get())
        self.current_return.deductions.attorney_fees = Decimal(self.deduction_vars['attorney_fees'].get())
        self.current_return.deductions.accounting_fees = Decimal(self.deduction_vars['accounting_fees'].get())
        self.current_return.deductions.other_administrative_expenses = Decimal(self.deduction_vars['other_administrative_expenses'].get())
        self.current_return.deductions.charitable_contributions = Decimal(self.deduction_vars['charitable_contributions'].get())
        self.current_return.deductions.net_operating_loss = Decimal(self.deduction_vars['net_operating_loss'].get())
        self.current_return.deductions.calculate_total()

    def _calculate_totals(self):
        """Calculate income and deduction totals"""
        try:
            total_income = (
                Decimal(self.income_vars['interest_income'].get() or "0") +
                Decimal(self.income_vars['dividend_income'].get() or "0") +
                Decimal(self.income_vars['business_income'].get() or "0") +
                Decimal(self.income_vars['capital_gains'].get() or "0") +
                Decimal(self.income_vars['rental_income'].get() or "0") +
                Decimal(self.income_vars['royalty_income'].get() or "0") +
                Decimal(self.income_vars['other_income'].get() or "0")
            )
            self.income_vars['total_income'].set(f"{total_income:.2f}")

            total_deductions = (
                Decimal(self.deduction_vars['fiduciary_fees'].get() or "0") +
                Decimal(self.deduction_vars['attorney_fees'].get() or "0") +
                Decimal(self.deduction_vars['accounting_fees'].get() or "0") +
                Decimal(self.deduction_vars['other_administrative_expenses'].get() or "0") +
                Decimal(self.deduction_vars['charitable_contributions'].get() or "0") +
                Decimal(self.deduction_vars['net_operating_loss'].get() or "0")
            )
            self.deduction_vars['total_deductions'].set(f"{total_deductions:.2f}")

            self.status_label.configure(text="Totals calculated")

        except Exception as e:
            messagebox.showerror("Calculation Error", f"Failed to calculate totals: {str(e)}")

    def _calculate_tax(self):
        """Calculate tax for the current return"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please create or load a return first.")
            return

        try:
            self._update_return_from_form()
            result = self.estate_service.calculate_tax(self.current_return)

            if result.get('success'):
                self.tax_summary_vars['taxable_income'].configure(text=f"${result['taxable_income']:,.2f}")
                self.tax_summary_vars['tax_due'].configure(text=f"${result['tax_due']:,.2f}")
                self.tax_summary_vars['payments_credits'].configure(text=f"${self.current_return.payments_credits:,.2f}")
                balance = result.get('balance_due', 0)
                self.tax_summary_vars['balance_due'].configure(text=f"${balance:,.2f}")
                self.status_label.configure(text="Tax calculated successfully")
            else:
                messagebox.showerror("Tax Calculation Error", result.get('error', 'Unknown error'))

        except Exception as e:
            messagebox.showerror("Tax Calculation Error", f"Failed to calculate tax: {str(e)}")

    def _add_beneficiary(self):
        """Add a beneficiary to the current return"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please create or load a return first.")
            return

        try:
            name = self.beneficiary_vars['name'].get().strip()
            if not name:
                raise ValueError("Beneficiary name is required")

            beneficiary = TrustBeneficiary(
                name=name,
                ssn=self.beneficiary_vars['ssn'].get().strip(),
                address=self.beneficiary_vars['address'].get().strip(),
                relationship=self.beneficiary_vars['relationship'].get().strip(),
                share_percentage=Decimal(self.beneficiary_vars['share_percentage'].get() or "0"),
                income_distributed=Decimal(self.beneficiary_vars['income_distributed'].get() or "0"),
                distribution_type=IncomeDistributionType(self.beneficiary_vars['distribution_type'].get() or "ordinary_income")
            )

            self.current_return.beneficiaries.append(beneficiary)
            self._refresh_beneficiaries_list()
            self._clear_beneficiary_form()
            self.status_label.configure(text="Beneficiary added")

        except Exception as e:
            messagebox.showerror("Add Beneficiary Error", f"Failed to add beneficiary: {str(e)}")

    def _update_beneficiary(self):
        """Update the beneficiary (placeholder)"""
        self.status_label.configure(text="Update functionality available in full version")

    def _delete_beneficiary(self):
        """Delete a beneficiary"""
        if not self.current_return or not self.current_return.beneficiaries:
            messagebox.showwarning("No Beneficiaries", "No beneficiaries to delete")
            return

        try:
            name = self.beneficiary_vars['name'].get().strip()
            self.current_return.beneficiaries = [b for b in self.current_return.beneficiaries if b.name != name]
            self._refresh_beneficiaries_list()
            self._clear_beneficiary_form()
            self.status_label.configure(text="Beneficiary deleted")

        except Exception as e:
            messagebox.showerror("Delete Error", f"Failed to delete beneficiary: {str(e)}")

    def _clear_beneficiary_form(self):
        """Clear the beneficiary form"""
        for var in self.beneficiary_vars.values():
            if isinstance(var, ctk.StringVar):
                var.set("")

    def _clear_all_forms(self):
        """Clear all forms"""
        self._clear_beneficiary_form()
        for var in self.return_vars.values():
            if isinstance(var, ctk.StringVar):
                var.set("")

    def _delete_return(self):
        """Delete the selected return"""
        if not self.returns:
            messagebox.showwarning("No Returns", "No returns to delete")
            return

        if not messagebox.askyesno("Confirm Delete", "Delete this return? This action cannot be undone."):
            return

        try:
            self.returns.pop(0)
            self._refresh_returns_list()
            self._update_summary()
            self.status_label.configure(text="Return deleted")

        except Exception as e:
            messagebox.showerror("Delete Error", f"Failed to delete return: {str(e)}")

    def _generate_form_1041(self):
        """Generate Form 1041"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please create or load a return first.")
            return

        try:
            form_data = self.estate_service.generate_form_1041_data(self.current_return)
            messagebox.showinfo(
                "Form 1041 Generated",
                f"Form 1041 generated for {self.current_return.entity_name}\n\n"
                f"Tax Year: {self.current_return.tax_year}\n"
                f"Taxable Income: ${self.current_return.taxable_income:,.2f}\n"
                f"Tax Due: ${self.current_return.tax_due:,.2f}"
            )
            self.status_label.configure(text="Form 1041 generated")

        except Exception as e:
            messagebox.showerror("Form Generation Error", f"Failed to generate Form 1041: {str(e)}")

    def _generate_k1_forms(self):
        """Generate K-1 forms for beneficiaries"""
        if not self.current_return or not self.current_return.beneficiaries:
            messagebox.showwarning("No Beneficiaries", "Add beneficiaries before generating K-1 forms")
            return

        try:
            k1_data = self.estate_service.generate_k1_forms(self.current_return)
            messagebox.showinfo(
                "K-1 Forms Generated",
                f"K-1 forms generated for {len(self.current_return.beneficiaries)} beneficiaries"
            )
            self.status_label.configure(text="K-1 forms generated")

        except Exception as e:
            messagebox.showerror("K-1 Generation Error", f"Failed to generate K-1 forms: {str(e)}")

    def _bind_events(self):
        """Bind event handlers"""
        pass
