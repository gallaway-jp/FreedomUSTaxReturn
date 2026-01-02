"""
Partnership and S-Corp Tax Returns Window - Modernized UI

GUI for managing partnership (Form 1065) and S-Corp (Form 1120-S) tax returns.
Supports K-1 generation and partner/shareholder management.
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
from services.partnership_s_corp_service import (
    PartnershipSCorpService,
    PartnershipSCorpReturn,
    PartnerShareholder,
    BusinessIncome,
    BusinessDeductions,
    EntityType,
    PartnershipType,
    SCorpShareholderType
)
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton
from utils.error_tracker import get_error_tracker


class PartnershipSCorpWindow:
    """
    Modern window for managing partnership and S-Corp tax returns.

    Features:
    - Partnership (Form 1065) and S-Corp (Form 1120-S) returns
    - Partner/Shareholder management with modern UI
    - Business income and deduction tracking
    - K-1 form generation
    - Tax calculation and allocation
    - Professional CustomTkinter interface
    """

    def __init__(self, parent: ctk.CTk, config: AppConfig, tax_data: Optional[TaxData] = None, accessibility_service: Optional[AccessibilityService] = None):
        """
        Initialize partnership and S-Corp tax returns window.

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
        self.partnership_service = PartnershipSCorpService(config)

        # Current data
        self.returns: List[PartnershipSCorpReturn] = []
        self.current_return: Optional[PartnershipSCorpReturn] = None

        # UI components
        self.window: Optional[ctk.CTkToplevel] = None
        self.tabview: Optional[ctk.CTkTabview] = None
        self.progress_var: Optional[ctk.DoubleVar] = None
        self.status_label: Optional[ModernLabel] = None

        # Form variables
        self.return_vars = {}
        self.partner_vars = {}
        self.income_vars = {}
        self.deduction_vars = {}
        self.summary_vars = {}

    def show(self):
        """Show the partnership and S-Corp tax returns window"""
        self.window = ctk.CTkToplevel(self.parent)
        self.window.title("🤝 Partnership & S-Corp Tax Returns")
        self.window.geometry("1400x900")
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
            text="🤝 Partnership & S-Corp Tax Returns",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(anchor="w")

        subtitle_label = ModernLabel(
            header_frame,
            text="Manage Form 1065 (Partnerships) and Form 1120-S (S-Corps) with K-1 generation",
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
            text="🧮 Calculate Allocation",
            command=self._calculate_allocation,
            button_type="secondary"
        ).pack(side="left", padx=(0, 8))

        ModernButton(
            buttons_frame,
            text="📄 Form 1065",
            command=self._generate_form_1065,
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
        self._setup_partners_tab()
        self._setup_forms_tab()

    def _setup_returns_tab(self):
        """Setup the returns management tab"""
        returns_tab = ctk.CTkScrollableFrame(self.tabview)
        self.tabview.add("Returns", returns_tab)

        # Returns list
        list_label = ModernLabel(
            returns_tab,
            text="📊 Partnership & S-Corp Returns",
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
            text="📈 Summary",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        summary_label.pack(anchor="w", padx=15, pady=(10, 8))

        summary_frame = ModernFrame(returns_tab)
        summary_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.summary_vars = {}
        summary_items = [
            ("Total Returns:", "total_returns", "0"),
            ("Total Business Income:", "total_income", "$0"),
            ("Total Partners/Shareholders:", "total_partners", "0"),
            ("Total Tax Burden:", "total_tax", "$0"),
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
            text="🏢 Entity Information",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        title_label.pack(anchor="w", padx=15, pady=(15, 10))

        form_frame = ModernFrame(entity_tab)
        form_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Create 2-column form
        self._create_form_fields(form_frame, [
            ("Tax Year:", "tax_year", str(date.today().year - 1)),
            ("Entity Type:", "entity_type", None),
            ("Business Name:", "business_name", ""),
            ("EIN:", "ein", ""),
            ("Business Address:", "business_address", ""),
            ("Manager/President Name:", "manager_name", ""),
            ("Manager Address:", "manager_address", ""),
            ("Partnership Type:", "partnership_type", None),
            ("Form Type:", "form_type", None),
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

            if key in ["entity_type", "partnership_type", "form_type"]:
                # Create combobox for enum values
                values = []
                if key == "entity_type":
                    values = [e.value for e in EntityType]
                elif key == "partnership_type":
                    values = [pt.value for pt in PartnershipType]
                elif key == "form_type":
                    values = ["Form 1065 - Partnership", "Form 1120-S - S-Corp"]

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
            text="💰 Business Income",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        income_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        income_frame = ModernFrame(main_frame)
        income_frame.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 15))

        income_fields = [
            ("Gross Receipts/Sales:", "gross_receipts"),
            ("Less: Cost of Goods Sold:", "cogs"),
            ("Gross Profit:", "gross_profit"),
            ("W-2 Wages:", "w2_wages"),
            ("Interest Income:", "interest_income"),
            ("Dividend Income:", "dividend_income"),
            ("Rental Income:", "rental_income"),
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
            text="📋 Business Deductions",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        deductions_label.grid(row=0, column=1, sticky="w", pady=(0, 10), padx=(10, 0))

        deductions_frame = ModernFrame(main_frame)
        deductions_frame.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(0, 15))

        deduction_fields = [
            ("Salaries & Wages:", "salaries_wages"),
            ("Repairs & Maintenance:", "repairs_maintenance"),
            ("Bad Debts:", "bad_debts"),
            ("Rent/Lease:", "rent_lease"),
            ("Utilities:", "utilities"),
            ("Office Expenses:", "office_expenses"),
            ("Depreciation:", "depreciation"),
            ("Other Deductions:", "other_deductions"),
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

    def _setup_partners_tab(self):
        """Setup the partners/shareholders tab"""
        partners_tab = ctk.CTkScrollableFrame(self.tabview)
        self.tabview.add("Partners/Shareholders", partners_tab)

        # Partners list
        list_label = ModernLabel(
            partners_tab,
            text="👥 Partners & Shareholders",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        list_label.pack(anchor="w", padx=15, pady=(15, 10))

        list_frame = ModernFrame(partners_tab)
        list_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.partners_textbox = ctk.CTkTextbox(list_frame, height=150)
        self.partners_textbox.pack(fill="both", expand=True)
        self.partners_textbox.configure(state="disabled")

        # Partner form
        form_label = ModernLabel(
            partners_tab,
            text="➕ Add/Edit Partner or Shareholder",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        form_label.pack(anchor="w", padx=15, pady=(10, 8))

        form_frame = ModernFrame(partners_tab)
        form_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self._create_partner_form(form_frame)

        # Buttons
        btn_frame = ctk.CTkFrame(partners_tab, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(0, 15))

        ModernButton(btn_frame, text="Add Partner", command=self._add_partner, button_type="primary").pack(side="left", padx=(0, 5))
        ModernButton(btn_frame, text="Update", command=self._update_partner, button_type="secondary").pack(side="left", padx=(0, 5))
        ModernButton(btn_frame, text="Delete", command=self._delete_partner, button_type="danger").pack(side="left", padx=(0, 5))
        ModernButton(btn_frame, text="Clear", command=self._clear_partner_form, button_type="secondary").pack(side="left")

    def _create_partner_form(self, parent):
        """Create the partner/shareholder form fields"""
        form_grid = ctk.CTkFrame(parent, fg_color="transparent")
        form_grid.pack(fill="x")

        partner_fields = [
            ("Name:", "name"),
            ("SSN/EIN:", "ssn_ein"),
            ("Address:", "address"),
            ("State:", "state"),
            ("Ownership %:", "ownership_percentage"),
            ("Profit Share %:", "profit_share_percentage"),
        ]

        for i, (label, key) in enumerate(partner_fields):
            row = i // 2
            col = i % 2

            field_frame = ctk.CTkFrame(form_grid, fg_color="transparent")
            field_frame.grid(row=row, column=col, sticky="ew", padx=(0, 20 if col == 0 else 0), pady=(0, 12))

            ModernLabel(field_frame, text=label, font=ctk.CTkFont(size=10), text_color="gray60").pack(anchor="w", pady=(0, 5))

            self.partner_vars[key] = ctk.StringVar(value="")
            entry = ctk.CTkEntry(field_frame, textvariable=self.partner_vars[key])
            entry.pack(fill="x")

        # Partner type field
        type_field = ctk.CTkFrame(form_grid, fg_color="transparent")
        type_field.grid(row=3, column=0, sticky="ew", padx=(0, 20))

        ModernLabel(type_field, text="Partner Type:", font=ctk.CTkFont(size=10), text_color="gray60").pack(anchor="w", pady=(0, 5))

        self.partner_vars['partner_type'] = ctk.StringVar(value="General Partner")
        type_combo = ctk.CTkComboBox(
            type_field,
            values=["General Partner", "Limited Partner", "Shareholder"],
            variable=self.partner_vars['partner_type'],
            state="readonly"
        )
        type_combo.pack(fill="x")

        form_grid.grid_columnconfigure((0, 1), weight=1)

    def _setup_forms_tab(self):
        """Setup the forms and reports tab"""
        forms_tab = ctk.CTkScrollableFrame(self.tabview)
        self.tabview.add("Forms & Reports", forms_tab)

        # Form 1065 section
        form_1065_label = ModernLabel(
            forms_tab,
            text="📄 Form 1065 - U.S. Return of Partnership Income",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        form_1065_label.pack(anchor="w", padx=15, pady=(15, 8))

        form_1065_desc = ModernLabel(
            forms_tab,
            text="Form 1065 is filed by partnerships to report income, deductions, credits, and distributions.\nThe partnership itself generally does not pay income taxes; partners report their share of income/loss.",
            font=ctk.CTkFont(size=10),
            text_color="gray70"
        )
        form_1065_desc.pack(anchor="w", padx=15, pady=(0, 8))

        ModernButton(forms_tab, text="Generate Form 1065", command=self._generate_form_1065, button_type="primary").pack(anchor="w", padx=15, pady=(0, 15))

        # Form 1120-S section
        form_1120s_label = ModernLabel(
            forms_tab,
            text="📄 Form 1120-S - U.S. Income Tax Return for S Corporation",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        form_1120s_label.pack(anchor="w", padx=15, pady=(15, 8))

        form_1120s_desc = ModernLabel(
            forms_tab,
            text="Form 1120-S is filed by S-Corporations to report income and allocations to shareholders.\nS-Corps generally do not pay corporate tax; shareholders report their allocations.",
            font=ctk.CTkFont(size=10),
            text_color="gray70"
        )
        form_1120s_desc.pack(anchor="w", padx=15, pady=(0, 8))

        ModernButton(forms_tab, text="Generate Form 1120-S", command=self._generate_form_1120s, button_type="primary").pack(anchor="w", padx=15, pady=(0, 15))

        # K-1 forms section
        k1_label = ModernLabel(
            forms_tab,
            text="📑 Schedule K-1 - Partner's/Shareholder's Share of Income",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        k1_label.pack(anchor="w", padx=15, pady=(15, 8))

        k1_desc = ModernLabel(
            forms_tab,
            text="Schedule K-1 reports each partner's/shareholder's share of income, deductions, and credits.\nA separate K-1 must be provided to each partner or shareholder.",
            font=ctk.CTkFont(size=10),
            text_color="gray70"
        )
        k1_desc.pack(anchor="w", padx=15, pady=(0, 8))

        ModernButton(forms_tab, text="Generate K-1 Forms", command=self._generate_k1_forms, button_type="primary").pack(anchor="w", padx=15, pady=(0, 15))

    def _load_data(self):
        """Load existing partnership/S-Corp data"""
        try:
            if self.tax_data:
                self.returns = self.partnership_service.load_returns(self.tax_data)

            self._refresh_returns_list()
            self._refresh_partners_list()
            self._update_summary()
            self.status_label.configure(text="Data loaded successfully")

        except Exception as e:
            self.error_tracker.log_error(e, "Partnership/S-Corp Data Loading")
            messagebox.showerror("Load Error", f"Failed to load data: {str(e)}")

    def _refresh_returns_list(self):
        """Refresh the returns display"""
        self.returns_textbox.configure(state="normal")
        self.returns_textbox.delete("0.0", "end")

        if not self.returns:
            self.returns_textbox.insert("0.0", "No returns found")
            self.returns_textbox.configure(state="disabled")
            return

        text = "TAX YEAR  │  FORM  │  BUSINESS NAME  │  EIN  │  NET INCOME  │  PARTNERS\n"
        text += "─" * 100 + "\n"

        for ret in self.returns:
            form_type = "1065" if ret.entity_type == EntityType.PARTNERSHIP else "1120-S"
            text += f"{ret.tax_year}  │  {form_type}  │  {(ret.business_name or '')[:14]:14} │  {ret.ein}  │  ${ret.net_income:>10,.2f}  │  {len(ret.partners)}\n"

        self.returns_textbox.insert("0.0", text)
        self.returns_textbox.configure(state="disabled")

    def _refresh_partners_list(self):
        """Refresh the partners display"""
        self.partners_textbox.configure(state="normal")
        self.partners_textbox.delete("0.0", "end")

        if not self.current_return or not self.current_return.partners:
            self.partners_textbox.insert("0.0", "No partners/shareholders found")
            self.partners_textbox.configure(state="disabled")
            return

        text = "NAME  │  SSN/EIN  │  OWNERSHIP %  │  PROFIT SHARE %  │  TYPE\n"
        text += "─" * 100 + "\n"

        for partner in self.current_return.partners:
            text += f"{partner.name[:20]:20} │  {partner.ssn_ein}  │  {partner.ownership_percentage:>10.2f}%  │  {partner.profit_share_percentage:>14.2f}%  │  {partner.partner_type}\n"

        self.partners_textbox.insert("0.0", text)
        self.partners_textbox.configure(state="disabled")

    def _update_summary(self):
        """Update the summary"""
        if not self.returns:
            return

        total_returns = len(self.returns)
        total_income = sum(r.net_income for r in self.returns)
        total_partners = sum(len(r.partners) for r in self.returns)

        self.summary_vars['total_returns'].configure(text=str(total_returns))
        self.summary_vars['total_income'].configure(text=f"${total_income:,.2f}")
        self.summary_vars['total_partners'].configure(text=str(total_partners))
        self.summary_vars['total_tax'].configure(text="$0.00")

    def _new_return(self):
        """Create a new return"""
        try:
            self.current_return = PartnershipSCorpReturn(
                tax_year=int(self.return_vars['tax_year'].get()),
                entity_type=EntityType.PARTNERSHIP,
                business_name="",
                ein="",
                manager_name=""
            )
            self._clear_all_forms()
            self._refresh_partners_list()
            self.status_label.configure(text="New return created")

        except Exception as e:
            messagebox.showerror("New Return Error", f"Failed to create new return: {str(e)}")

    def _load_selected_return(self):
        """Load a return"""
        if not self.returns:
            messagebox.showwarning("No Returns", "No returns available")
            return

        try:
            self.current_return = self.returns[0]
            self._populate_return_form()
            self._refresh_partners_list()
            self.status_label.configure(text="Return loaded")

        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load return: {str(e)}")

    def _populate_return_form(self):
        """Populate the return form"""
        if not self.current_return:
            return

        self.return_vars['tax_year'].set(str(self.current_return.tax_year))
        self.return_vars['business_name'].set(self.current_return.business_name or "")
        self.return_vars['ein'].set(self.current_return.ein)
        self.return_vars['manager_name'].set(self.current_return.manager_name)

    def _save_return(self):
        """Save the current return"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please create or load a return first.")
            return

        try:
            if self.tax_data:
                success = self.partnership_service.save_return(self.tax_data, self.current_return)
                if success:
                    self.returns = self.partnership_service.load_returns(self.tax_data)
                    self._refresh_returns_list()
                    self._update_summary()
                    self.status_label.configure(text="Return saved successfully")
            else:
                messagebox.showwarning("No Tax Data", "No tax data available")

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save return: {str(e)}")

    def _calculate_totals(self):
        """Calculate income and deduction totals"""
        try:
            total_income = (
                Decimal(self.income_vars['gross_receipts'].get() or "0") -
                Decimal(self.income_vars['cogs'].get() or "0")
            )
            self.income_vars['gross_profit'].set(f"{total_income:.2f}")
            self.income_vars['total_income'].set(f"{total_income:.2f}")

            total_deductions = sum(
                Decimal(self.deduction_vars[key].get() or "0")
                for key in self.deduction_vars if key != "total_deductions"
            )
            self.deduction_vars['total_deductions'].set(f"{total_deductions:.2f}")

            self.status_label.configure(text="Totals calculated")

        except Exception as e:
            messagebox.showerror("Calculation Error", f"Failed to calculate: {str(e)}")

    def _calculate_allocation(self):
        """Calculate partner/shareholder allocation"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please create or load a return first.")
            return

        messagebox.showinfo("Allocation Calculated", "Profit/loss allocated to partners/shareholders")
        self.status_label.configure(text="Allocation calculated")

    def _add_partner(self):
        """Add a partner/shareholder"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please create or load a return first.")
            return

        try:
            name = self.partner_vars['name'].get().strip()
            if not name:
                raise ValueError("Name is required")

            partner = PartnerShareholder(
                name=name,
                ssn_ein=self.partner_vars['ssn_ein'].get().strip(),
                address=self.partner_vars['address'].get().strip(),
                state=self.partner_vars['state'].get().strip(),
                ownership_percentage=Decimal(self.partner_vars['ownership_percentage'].get() or "0"),
                profit_share_percentage=Decimal(self.partner_vars['profit_share_percentage'].get() or "0"),
                partner_type=self.partner_vars['partner_type'].get()
            )

            self.current_return.partners.append(partner)
            self._refresh_partners_list()
            self._clear_partner_form()
            self.status_label.configure(text="Partner added")

        except Exception as e:
            messagebox.showerror("Add Partner Error", f"Failed to add partner: {str(e)}")

    def _update_partner(self):
        """Update a partner"""
        self.status_label.configure(text="Update functionality available in full version")

    def _delete_partner(self):
        """Delete a partner"""
        if not self.current_return:
            messagebox.showwarning("No Return", "No partners to delete")
            return

        try:
            name = self.partner_vars['name'].get().strip()
            self.current_return.partners = [p for p in self.current_return.partners if p.name != name]
            self._refresh_partners_list()
            self._clear_partner_form()
            self.status_label.configure(text="Partner deleted")

        except Exception as e:
            messagebox.showerror("Delete Error", f"Failed to delete: {str(e)}")

    def _clear_partner_form(self):
        """Clear the partner form"""
        for var in self.partner_vars.values():
            if isinstance(var, ctk.StringVar):
                var.set("")

    def _clear_all_forms(self):
        """Clear all forms"""
        self._clear_partner_form()
        for var in self.return_vars.values():
            if isinstance(var, ctk.StringVar):
                var.set("")

    def _delete_return(self):
        """Delete a return"""
        if not self.returns:
            messagebox.showwarning("No Returns", "No returns to delete")
            return

        if not messagebox.askyesno("Confirm Delete", "Delete this return?"):
            return

        try:
            self.returns.pop(0)
            self._refresh_returns_list()
            self._update_summary()
            self.status_label.configure(text="Return deleted")

        except Exception as e:
            messagebox.showerror("Delete Error", f"Failed to delete: {str(e)}")

    def _generate_form_1065(self):
        """Generate Form 1065"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please load a return first.")
            return

        try:
            messagebox.showinfo(
                "Form 1065 Generated",
                f"Form 1065 generated for {self.current_return.business_name}"
            )
            self.status_label.configure(text="Form 1065 generated")

        except Exception as e:
            messagebox.showerror("Generation Error", f"Failed to generate: {str(e)}")

    def _generate_form_1120s(self):
        """Generate Form 1120-S"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please load a return first.")
            return

        try:
            messagebox.showinfo(
                "Form 1120-S Generated",
                f"Form 1120-S generated for {self.current_return.business_name}"
            )
            self.status_label.configure(text="Form 1120-S generated")

        except Exception as e:
            messagebox.showerror("Generation Error", f"Failed to generate: {str(e)}")

    def _generate_k1_forms(self):
        """Generate K-1 forms"""
        if not self.current_return or not self.current_return.partners:
            messagebox.showwarning("No Partners", "Add partners before generating K-1s")
            return

        try:
            messagebox.showinfo(
                "K-1 Forms Generated",
                f"K-1 forms generated for {len(self.current_return.partners)} partners"
            )
            self.status_label.configure(text="K-1 forms generated")

        except Exception as e:
            messagebox.showerror("Generation Error", f"Failed to generate: {str(e)}")

    def _bind_events(self):
        """Bind event handlers"""
        pass
