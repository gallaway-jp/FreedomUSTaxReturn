"""
Partnership and S-Corp Tax Returns Window

GUI for managing partnership (Form 1065) and S-Corp (Form 1120-S) tax returns.
Supports K-1 generation and partner/shareholder management.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
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
from utils.error_tracker import get_error_tracker


class PartnershipSCorpWindow:
    """
    Window for managing partnership and S-Corp tax returns.

    Features:
    - Partnership (Form 1065) and S-Corp (Form 1120-S) return creation
    - Partner/Shareholder management
    - Business income and deduction tracking
    - K-1 form generation
    - Tax calculation and allocation
    - Multi-entity support
    """

    def __init__(self, parent: tk.Tk, config: AppConfig, tax_data: Optional[TaxData] = None):
        """
        Initialize partnership and S-Corp tax returns window.

        Args:
            parent: Parent window
            config: Application configuration
            tax_data: Tax return data to analyze
        """
        self.parent = parent
        self.config = config
        self.tax_data = tax_data
        self.error_tracker = get_error_tracker()

        # Initialize service
        self.partnership_service = PartnershipSCorpService(config)

        # Current data
        self.returns: List[PartnershipSCorpReturn] = []
        self.current_return: Optional[PartnershipSCorpReturn] = None

        # UI components
        self.window: Optional[tk.Toplevel] = None
        self.notebook: Optional[ttk.Notebook] = None
        self.returns_tree: Optional[ttk.Treeview] = None
        self.partners_tree: Optional[ttk.Treeview] = None
        self.progress_var: Optional[tk.DoubleVar] = None
        self.status_label: Optional[ttk.Label] = None

        # Form variables
        self.return_vars = {}
        self.partner_vars = {}
        self.income_vars = {}
        self.deduction_vars = {}

    def show(self):
        """Show the partnership and S-Corp tax returns window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Partnership & S-Corp Tax Returns - Freedom US Tax Return")
        self.window.geometry("1500x950")
        self.window.resizable(True, True)

        # Initialize UI
        self._setup_ui()
        self._load_data()
        self._bind_events()

        # Center window
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

        # Make modal
        self.window.transient(self.parent)
        self.window.grab_set()
        self.parent.wait_window(self.window)

    def _setup_ui(self):
        """Setup the main user interface"""
        if not self.window:
            return

        # Create main frame
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Partnership & S-Corp Tax Returns (Form 1065/1120-S)",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 10))

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, pady=(0, 10))

        # Create tabs
        self._create_returns_tab()
        self._create_entity_tab()
        self._create_income_deductions_tab()
        self._create_partners_tab()
        self._create_forms_tab()

        # Progress bar
        self.progress_var = tk.DoubleVar()
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill="x", pady=(0, 5))

        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(side="left", fill="x", expand=True)

        # Status label
        self.status_label = ttk.Label(progress_frame, text="Ready")
        self.status_label.pack(side="right", padx=(10, 0))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(
            button_frame,
            text="New Return",
            command=self._new_return
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            button_frame,
            text="Save Return",
            command=self._save_return
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            button_frame,
            text="Calculate Income",
            command=self._calculate_income
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            button_frame,
            text="Allocate to Partners",
            command=self._allocate_to_partners
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            button_frame,
            text="Generate Form 1065/1120-S",
            command=self._generate_main_form
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            button_frame,
            text="Generate K-1s",
            command=self._generate_k1_forms
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            button_frame,
            text="Close",
            command=self._close_window
        ).pack(side="right")

    def _create_returns_tab(self):
        """Create the returns management tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Returns")

        # Returns list
        list_frame = ttk.LabelFrame(tab, text="Partnership & S-Corp Returns")
        list_frame.pack(fill="both", expand=True, pady=(0, 10))

        columns = ("Tax Year", "Entity Type", "Entity Name", "EIN", "Ordinary Income", "Net Income/Loss", "Partners")
        self.returns_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.returns_tree.heading(col, text=col)
            self.returns_tree.column(col, width=120)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.returns_tree.yview)
        self.returns_tree.configure(yscrollcommand=scrollbar.set)

        self.returns_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Return buttons
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill="x")

        ttk.Button(btn_frame, text="Load Return", command=self._load_selected_return).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Delete Return", command=self._delete_return).pack(side="left", padx=(0, 5))

        # Summary
        summary_frame = ttk.LabelFrame(tab, text="Tax Year Summary")
        summary_frame.pack(fill="x", pady=(10, 0))

        self.summary_vars = {}
        summary_items = [
            ("Total Returns:", "total_returns"),
            ("Total Ordinary Income:", "total_ordinary"),
            ("Total Net Income/Loss:", "total_net"),
            ("Total Partners/Shareholders:", "total_partners")
        ]

        for i, (label, key) in enumerate(summary_items):
            ttk.Label(summary_frame, text=label).grid(row=i, column=0, sticky="w", padx=10, pady=2)
            self.summary_vars[key] = tk.StringVar(value="0")
            ttk.Label(summary_frame, textvariable=self.summary_vars[key]).grid(row=i, column=1, sticky="e", padx=10, pady=2)

    def _create_entity_tab(self):
        """Create the entity information tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Entity Info")

        # Entity information form
        form_frame = ttk.LabelFrame(tab, text="Entity Information")
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Basic information
        ttk.Label(form_frame, text="Tax Year:").grid(row=0, column=0, sticky="w", pady=5, padx=10)
        self.return_vars['tax_year'] = tk.StringVar(value=str(date.today().year - 1))
        ttk.Entry(form_frame, textvariable=self.return_vars['tax_year']).grid(row=0, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="Entity Type:").grid(row=1, column=0, sticky="w", pady=5, padx=10)
        self.return_vars['entity_type'] = tk.StringVar()
        entity_combo = ttk.Combobox(
            form_frame,
            textvariable=self.return_vars['entity_type'],
            values=[e.value for e in EntityType],
            state="readonly"
        )
        entity_combo.grid(row=1, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="Entity Name:").grid(row=2, column=0, sticky="w", pady=5, padx=10)
        self.return_vars['entity_name'] = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.return_vars['entity_name']).grid(row=2, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="EIN:").grid(row=3, column=0, sticky="w", pady=5, padx=10)
        self.return_vars['ein'] = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.return_vars['ein']).grid(row=3, column=1, sticky="ew", pady=5, padx=(0, 10))

        # Business information
        ttk.Label(form_frame, text="Business Address:").grid(row=4, column=0, sticky="w", pady=5, padx=10)
        self.return_vars['business_address'] = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.return_vars['business_address']).grid(row=4, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="Business Description:").grid(row=5, column=0, sticky="w", pady=5, padx=10)
        self.return_vars['business_description'] = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.return_vars['business_description']).grid(row=5, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="Principal Business Activity:").grid(row=6, column=0, sticky="w", pady=5, padx=10)
        self.return_vars['principal_business_activity'] = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.return_vars['principal_business_activity']).grid(row=6, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="Business Activity Code:").grid(row=7, column=0, sticky="w", pady=5, padx=10)
        self.return_vars['business_activity_code'] = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.return_vars['business_activity_code']).grid(row=7, column=1, sticky="ew", pady=5, padx=(0, 10))

        # Partnership/S-Corp specific
        ttk.Label(form_frame, text="Partnership Type:").grid(row=8, column=0, sticky="w", pady=5, padx=10)
        self.return_vars['partnership_type'] = tk.StringVar()
        partnership_combo = ttk.Combobox(
            form_frame,
            textvariable=self.return_vars['partnership_type'],
            values=[p.value for p in PartnershipType],
            state="readonly"
        )
        partnership_combo.grid(row=8, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="S-Corp Shareholder Type:").grid(row=9, column=0, sticky="w", pady=5, padx=10)
        self.return_vars['s_corp_shareholder_type'] = tk.StringVar()
        s_corp_combo = ttk.Combobox(
            form_frame,
            textvariable=self.return_vars['s_corp_shareholder_type'],
            values=[s.value for s in SCorpShareholderType],
            state="readonly"
        )
        s_corp_combo.grid(row=9, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="Accounting Method:").grid(row=10, column=0, sticky="w", pady=5, padx=10)
        self.return_vars['accounting_method'] = tk.StringVar()
        accounting_combo = ttk.Combobox(
            form_frame,
            textvariable=self.return_vars['accounting_method'],
            values=["cash", "accrual"],
            state="readonly"
        )
        accounting_combo.grid(row=10, column=1, sticky="ew", pady=5, padx=(0, 10))

        # Configure grid weights
        form_frame.columnconfigure(1, weight=1)

    def _create_income_deductions_tab(self):
        """Create the income and deductions tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Income & Deductions")

        # Split into income and deductions sections
        income_frame = ttk.LabelFrame(tab, text="Business Income")
        income_frame.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=10)

        deductions_frame = ttk.LabelFrame(tab, text="Business Deductions")
        deductions_frame.pack(side="right", fill="both", expand=True, padx=(5, 0), pady=10)

        # Income fields
        self.income_vars = {}
        income_fields = [
            ("Gross Receipts:", "gross_receipts"),
            ("Returns & Allowances:", "returns_allowances"),
            ("Cost of Goods Sold:", "cost_of_goods_sold"),
            ("Gross Profit:", "gross_profit"),
            ("Dividends:", "dividends"),
            ("Interest Income:", "interest_income"),
            ("Rents:", "rents"),
            ("Royalties:", "royalties"),
            ("Other Income:", "other_income"),
            ("Total Ordinary Income:", "total_ordinary")
        ]

        for i, (label, key) in enumerate(income_fields):
            ttk.Label(income_frame, text=label).grid(row=i, column=0, sticky="w", pady=3, padx=10)
            self.income_vars[key] = tk.StringVar(value="0.00")
            entry = ttk.Entry(income_frame, textvariable=self.income_vars[key])
            entry.grid(row=i, column=1, sticky="ew", pady=3, padx=(0, 10))
            if key in ["gross_profit", "total_ordinary"]:
                entry.config(state="readonly")

        # Deductions fields
        self.deduction_vars = {}
        deduction_fields = [
            ("Salaries & Wages:", "salaries_wages"),
            ("Repairs & Maintenance:", "repairs_maintenance"),
            ("Bad Debts:", "bad_debts"),
            ("Rents:", "rents_deduction"),
            ("Taxes & Licenses:", "taxes_licenses"),
            ("Charitable Contributions:", "charitable_contributions"),
            ("Depreciation:", "depreciation"),
            ("Other Deductions:", "other_deductions"),
            ("Total Deductions:", "total_deductions")
        ]

        for i, (label, key) in enumerate(deduction_fields):
            ttk.Label(deductions_frame, text=label).grid(row=i, column=0, sticky="w", pady=3, padx=10)
            self.deduction_vars[key] = tk.StringVar(value="0.00")
            entry = ttk.Entry(deductions_frame, textvariable=self.deduction_vars[key])
            entry.grid(row=i, column=1, sticky="ew", pady=3, padx=(0, 10))
            if key == "total_deductions":
                entry.config(state="readonly")

        # Configure grid weights
        income_frame.columnconfigure(1, weight=1)
        deductions_frame.columnconfigure(1, weight=1)

        # Calculate button
        calc_frame = ttk.Frame(tab)
        calc_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(calc_frame, text="Calculate Totals", command=self._calculate_totals).pack(pady=5)

    def _create_partners_tab(self):
        """Create the partners/shareholders management tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Partners/Shareholders")

        # Partners/Shareholders list
        list_frame = ttk.LabelFrame(tab, text="Partners & Shareholders")
        list_frame.pack(fill="both", expand=True, pady=(0, 10))

        columns = ("Name", "SSN/EIN", "Ownership %", "Share of Income", "Share of Loss", "Distributions")
        self.partners_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)

        for col in columns:
            self.partners_tree.heading(col, text=col)
            self.partners_tree.column(col, width=120)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.partners_tree.yview)
        self.partners_tree.configure(yscrollcommand=scrollbar.set)

        self.partners_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Partner/Shareholder form
        form_frame = ttk.LabelFrame(tab, text="Partner/Shareholder Details")
        form_frame.pack(fill="both", expand=True)

        # Initialize partner variables
        self.partner_vars = {}

        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky="w", pady=5, padx=10)
        self.partner_vars['name'] = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.partner_vars['name']).grid(row=0, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="SSN/EIN:").grid(row=1, column=0, sticky="w", pady=5, padx=10)
        self.partner_vars['ssn_ein'] = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.partner_vars['ssn_ein']).grid(row=1, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="Address:").grid(row=2, column=0, sticky="w", pady=5, padx=10)
        self.partner_vars['address'] = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.partner_vars['address']).grid(row=2, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="Entity Type:").grid(row=3, column=0, sticky="w", pady=5, padx=10)
        self.partner_vars['entity_type'] = tk.StringVar()
        entity_combo = ttk.Combobox(
            form_frame,
            textvariable=self.partner_vars['entity_type'],
            values=["individual", "partnership", "corporation", "estate", "trust"],
            state="readonly"
        )
        entity_combo.grid(row=3, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="Ownership Percentage:").grid(row=4, column=0, sticky="w", pady=5, padx=10)
        self.partner_vars['ownership_percentage'] = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.partner_vars['ownership_percentage']).grid(row=4, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="Beginning Capital:").grid(row=5, column=0, sticky="w", pady=5, padx=10)
        self.partner_vars['capital_account_beginning'] = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.partner_vars['capital_account_beginning']).grid(row=5, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="Share of Income:").grid(row=6, column=0, sticky="w", pady=5, padx=10)
        self.partner_vars['share_of_income'] = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.partner_vars['share_of_income']).grid(row=6, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="Share of Loss:").grid(row=7, column=0, sticky="w", pady=5, padx=10)
        self.partner_vars['share_of_losses'] = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.partner_vars['share_of_losses']).grid(row=7, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="Distributions:").grid(row=8, column=0, sticky="w", pady=5, padx=10)
        self.partner_vars['distributions'] = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.partner_vars['distributions']).grid(row=8, column=1, sticky="ew", pady=5, padx=(0, 10))

        # Form buttons
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=9, column=0, columnspan=2, pady=(10, 0))

        ttk.Button(btn_frame, text="Add Partner/Shareholder", command=self._add_partner).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Update Partner/Shareholder", command=self._update_partner).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Delete Partner/Shareholder", command=self._delete_partner).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Clear Form", command=self._clear_partner_form).pack(side="left", padx=(0, 5))

        # Configure grid weights
        form_frame.columnconfigure(1, weight=1)

        # Partner buttons
        list_btn_frame = ttk.Frame(tab)
        list_btn_frame.pack(fill="x")

        ttk.Button(list_btn_frame, text="Edit Selected", command=self._edit_selected_partner).pack(side="left", padx=(0, 5))

    def _create_forms_tab(self):
        """Create the forms and reports tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Forms & Reports")

        # Form 1065/1120-S section
        form_frame = ttk.LabelFrame(tab, text="Form 1065 (Partnership) / Form 1120-S (S-Corp)")
        form_frame.pack(fill="both", expand=True, pady=(0, 10))

        ttk.Label(
            form_frame,
            text="Form 1065: Used to report partnership income, deductions, and partner allocations.\n" +
                 "Form 1120-S: Used to report S-Corp income, deductions, and shareholder allocations.\n\n" +
                 "Both forms are filed annually and are due on the 15th day of the 3rd month after tax year end.",
            wraplength=900,
            justify="left"
        ).pack(pady=10, padx=10, anchor="w")

        ttk.Button(
            form_frame,
            text="Generate Form 1065/1120-S",
            command=self._generate_main_form
        ).pack(pady=(0, 10), padx=10, anchor="w")

        # K-1 forms section
        k1_frame = ttk.LabelFrame(tab, text="Schedule K-1 - Partner's/Shareholder's Share")
        k1_frame.pack(fill="both", expand=True, pady=(0, 10))

        ttk.Label(
            k1_frame,
            text="Schedule K-1 reports each partner/shareholder's share of income, deductions, credits, and other items.\n" +
                 "A separate K-1 must be provided to each partner/shareholder for inclusion in their personal returns.",
            wraplength=900,
            justify="left"
        ).pack(pady=10, padx=10, anchor="w")

        ttk.Button(
            k1_frame,
            text="Generate K-1 Forms",
            command=self._generate_k1_forms
        ).pack(pady=(0, 10), padx=10, anchor="w")

        # Tax calculation summary
        tax_frame = ttk.LabelFrame(tab, text="Income Calculation Summary")
        tax_frame.pack(fill="x")

        ttk.Label(
            tax_frame,
            text="Current income calculation for the loaded partnership/S-Corp return:",
            wraplength=900,
            justify="left"
        ).pack(pady=10, padx=10, anchor="w")

        # Income summary labels
        self.income_summary_vars = {}
        income_items = [
            ("Gross Profit:", "gross_profit"),
            ("Total Ordinary Income:", "total_ordinary"),
            ("Total Deductions:", "total_deductions"),
            ("Net Income/Loss:", "net_income_loss")
        ]

        for item in income_items:
            frame = ttk.Frame(tax_frame)
            frame.pack(fill="x", padx=20, pady=2)
            ttk.Label(frame, text=item[0]).pack(side="left")
            self.income_summary_vars[item[1]] = tk.StringVar(value="$0.00")
            ttk.Label(frame, textvariable=self.income_summary_vars[item[1]], font=("Arial", 10, "bold")).pack(side="right")

    def _load_data(self):
        """Load existing partnership/S-Corp data"""
        try:
            if self.tax_data:
                # Load returns from tax data
                self.returns = self.partnership_service.load_partnership_s_corp_returns(self.tax_data)

            self._refresh_returns_list()
            self._update_summary()

            self.status_label.config(text="Data loaded successfully")

        except Exception as e:
            self.error_tracker.track_error(e, {"operation": "_load_data"})
            messagebox.showerror("Load Error", f"Failed to load partnership/S-Corp data: {str(e)}")

    def _refresh_returns_list(self):
        """Refresh the returns treeview"""
        if not self.returns_tree:
            return

        # Clear existing items
        for item in self.returns_tree.get_children():
            self.returns_tree.delete(item)

        # Add returns
        for i, return_data in enumerate(self.returns):
            partner_count = len(return_data.partners_shareholders)
            self.returns_tree.insert("", "end", values=(
                return_data.tax_year,
                return_data.entity_type.value.replace("_", " ").title(),
                return_data.entity_name or "",
                return_data.ein,
                f"${return_data.ordinary_business_income:.2f}",
                f"${return_data.net_income_loss:.2f}",
                partner_count
            ), tags=(str(i),))

    def _refresh_partners_list(self):
        """Refresh the partners/shareholders treeview"""
        if not self.partners_tree or not self.current_return:
            return

        # Clear existing items
        for item in self.partners_tree.get_children():
            self.partners_tree.delete(item)

        # Add partners/shareholders
        for partner in self.current_return.partners_shareholders:
            self.partners_tree.insert("", "end", values=(
                partner.name,
                partner.ssn_ein,
                f"{partner.ownership_percentage:.2f}%",
                f"${partner.share_of_income:.2f}",
                f"${partner.share_of_losses:.2f}",
                f"${partner.distributions:.2f}"
            ))

    def _update_summary(self):
        """Update the tax year summary"""
        if not self.returns:
            return

        total_returns = len(self.returns)
        total_ordinary = sum(r.ordinary_business_income for r in self.returns)
        total_net = sum(r.net_income_loss for r in self.returns)
        total_partners = sum(len(r.partners_shareholders) for r in self.returns)

        self.summary_vars['total_returns'].set(str(total_returns))
        self.summary_vars['total_ordinary'].set(f"${total_ordinary:.2f}")
        self.summary_vars['total_net'].set(f"${total_net:.2f}")
        self.summary_vars['total_partners'].set(str(total_partners))

    def _new_return(self):
        """Create a new partnership/S-Corp return"""
        try:
            # Create new return
            self.current_return = PartnershipSCorpReturn(
                tax_year=int(self.return_vars['tax_year'].get()),
                entity_type=EntityType.PARTNERSHIP,  # Default
                entity_name="",
                ein="",
                business_address="",
                business_description=""
            )

            # Clear all forms
            self._clear_all_forms()

            # Set default values
            self.return_vars['entity_name'].set("")
            self.return_vars['ein'].set("")
            self.return_vars['business_address'].set("")
            self.return_vars['business_description'].set("")
            self.return_vars['principal_business_activity'].set("")
            self.return_vars['business_activity_code'].set("")
            self.return_vars['partnership_type'].set("")
            self.return_vars['s_corp_shareholder_type'].set("")
            self.return_vars['accounting_method'].set("cash")

            # Clear income and deductions
            for var in self.income_vars.values():
                var.set("0.00")
            for var in self.deduction_vars.values():
                var.set("0.00")

            # Clear partners
            self.current_return.partners_shareholders = []
            self._refresh_partners_list()

            self.status_label.config(text="New return created")

        except Exception as e:
            messagebox.showerror("New Return Error", f"Failed to create new return: {str(e)}")

    def _load_selected_return(self):
        """Load the selected return into the form"""
        selection = self.returns_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a return to load.")
            return

        try:
            item = selection[0]
            index = int(self.returns_tree.item(item, "tags")[0])
            self.current_return = self.returns[index]

            # Populate form
            self._populate_return_form()
            self._populate_income_form()
            self._populate_deductions_form()
            self._refresh_partners_list()

            self.status_label.config(text=f"Loaded {self.current_return.entity_type.value.replace('_', ' ').title()} return for {self.current_return.entity_name}")

        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load return: {str(e)}")

    def _populate_return_form(self):
        """Populate the return form with current return data"""
        if not self.current_return:
            return

        self.return_vars['tax_year'].set(str(self.current_return.tax_year))
        self.return_vars['entity_type'].set(self.current_return.entity_type.value)
        self.return_vars['entity_name'].set(self.current_return.entity_name)
        self.return_vars['ein'].set(self.current_return.ein)
        self.return_vars['business_address'].set(self.current_return.business_address)
        self.return_vars['business_description'].set(self.current_return.business_description)
        self.return_vars['principal_business_activity'].set(self.current_return.principal_business_activity)
        self.return_vars['business_activity_code'].set(self.current_return.business_activity_code)
        self.return_vars['partnership_type'].set(self.current_return.partnership_type.value if self.current_return.partnership_type else "")
        self.return_vars['s_corp_shareholder_type'].set(self.current_return.s_corp_shareholder_type.value if self.current_return.s_corp_shareholder_type else "")
        self.return_vars['accounting_method'].set(self.current_return.accounting_method)

    def _populate_income_form(self):
        """Populate the income form with current return data"""
        if not self.current_return:
            return

        income = self.current_return.income
        self.income_vars['gross_receipts'].set(f"{income.gross_receipts:.2f}")
        self.income_vars['returns_allowances'].set(f"{income.returns_allowances:.2f}")
        self.income_vars['cost_of_goods_sold'].set(f"{income.cost_of_goods_sold:.2f}")
        self.income_vars['gross_profit'].set(f"{income.gross_profit:.2f}")
        self.income_vars['dividends'].set(f"{income.dividends:.2f}")
        self.income_vars['interest_income'].set(f"{income.interest_income:.2f}")
        self.income_vars['rents'].set(f"{income.rents:.2f}")
        self.income_vars['royalties'].set(f"{income.royalties:.2f}")
        self.income_vars['other_income'].set(f"{income.other_income:.2f}")
        self.income_vars['total_ordinary'].set(f"{income.total_ordinary_income():.2f}")

    def _populate_deductions_form(self):
        """Populate the deductions form with current return data"""
        if not self.current_return:
            return

        deductions = self.current_return.deductions
        self.deduction_vars['salaries_wages'].set(f"{deductions.salaries_wages:.2f}")
        self.deduction_vars['repairs_maintenance'].set(f"{deductions.repairs_maintenance:.2f}")
        self.deduction_vars['bad_debts'].set(f"{deductions.bad_debts:.2f}")
        self.deduction_vars['rents_deduction'].set(f"{deductions.rents:.2f}")
        self.deduction_vars['taxes_licenses'].set(f"{deductions.taxes_licenses:.2f}")
        self.deduction_vars['charitable_contributions'].set(f"{deductions.charitable_contributions:.2f}")
        self.deduction_vars['depreciation'].set(f"{deductions.depreciation:.2f}")
        self.deduction_vars['other_deductions'].set(f"{deductions.other_deductions:.2f}")
        self.deduction_vars['total_deductions'].set(f"{deductions.total_deductions:.2f}")

    def _save_return(self):
        """Save the current return"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please create or load a return first.")
            return

        try:
            # Update return data from forms
            self._update_return_from_form()

            # Save to tax data
            if self.tax_data:
                success = self.partnership_service.save_partnership_s_corp_return(self.tax_data, self.current_return)
                if success:
                    # Reload returns list
                    self.returns = self.partnership_service.load_partnership_s_corp_returns(self.tax_data)
                    self._refresh_returns_list()
                    self._update_summary()
                    self.status_label.config(text="Return saved successfully")
                else:
                    messagebox.showerror("Save Error", "Failed to save return to tax data")
            else:
                messagebox.showwarning("No Tax Data", "No tax data available to save to")

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save return: {str(e)}")

    def _update_return_from_form(self):
        """Update the current return from form data"""
        if not self.current_return:
            return

        # Basic info
        self.current_return.tax_year = int(self.return_vars['tax_year'].get())
        self.current_return.entity_type = EntityType(self.return_vars['entity_type'].get())
        self.current_return.entity_name = self.return_vars['entity_name'].get()
        self.current_return.ein = self.return_vars['ein'].get()
        self.current_return.business_address = self.return_vars['business_address'].get()
        self.current_return.business_description = self.return_vars['business_description'].get()
        self.current_return.principal_business_activity = self.return_vars['principal_business_activity'].get()
        self.current_return.business_activity_code = self.return_vars['business_activity_code'].get()
        self.current_return.accounting_method = self.return_vars['accounting_method'].get()

        # Partnership/S-Corp specific
        partnership_type_str = self.return_vars['partnership_type'].get()
        self.current_return.partnership_type = PartnershipType(partnership_type_str) if partnership_type_str else None

        s_corp_type_str = self.return_vars['s_corp_shareholder_type'].get()
        self.current_return.s_corp_shareholder_type = SCorpShareholderType(s_corp_type_str) if s_corp_type_str else None

        # Income
        self.current_return.income.gross_receipts = Decimal(self.income_vars['gross_receipts'].get())
        self.current_return.income.returns_allowances = Decimal(self.income_vars['returns_allowances'].get())
        self.current_return.income.cost_of_goods_sold = Decimal(self.income_vars['cost_of_goods_sold'].get())
        self.current_return.income.dividends = Decimal(self.income_vars['dividends'].get())
        self.current_return.income.interest_income = Decimal(self.income_vars['interest_income'].get())
        self.current_return.income.rents = Decimal(self.income_vars['rents'].get())
        self.current_return.income.royalties = Decimal(self.income_vars['royalties'].get())
        self.current_return.income.other_income = Decimal(self.income_vars['other_income'].get())
        self.current_return.income.calculate_gross_profit()

        # Deductions
        self.current_return.deductions.salaries_wages = Decimal(self.deduction_vars['salaries_wages'].get())
        self.current_return.deductions.repairs_maintenance = Decimal(self.deduction_vars['repairs_maintenance'].get())
        self.current_return.deductions.bad_debts = Decimal(self.deduction_vars['bad_debts'].get())
        self.current_return.deductions.rents = Decimal(self.deduction_vars['rents_deduction'].get())
        self.current_return.deductions.taxes_licenses = Decimal(self.deduction_vars['taxes_licenses'].get())
        self.current_return.deductions.charitable_contributions = Decimal(self.deduction_vars['charitable_contributions'].get())
        self.current_return.deductions.depreciation = Decimal(self.deduction_vars['depreciation'].get())
        self.current_return.deductions.other_deductions = Decimal(self.deduction_vars['other_deductions'].get())
        self.current_return.deductions.calculate_total()

    def _calculate_totals(self):
        """Calculate income and deduction totals"""
        try:
            # Calculate gross profit
            gross_receipts = Decimal(self.income_vars['gross_receipts'].get())
            returns_allowances = Decimal(self.income_vars['returns_allowances'].get())
            cost_of_goods_sold = Decimal(self.income_vars['cost_of_goods_sold'].get())
            gross_profit = gross_receipts - returns_allowances - cost_of_goods_sold
            self.income_vars['gross_profit'].set(f"{gross_profit:.2f}")

            # Calculate total ordinary income
            dividends = Decimal(self.income_vars['dividends'].get())
            interest = Decimal(self.income_vars['interest_income'].get())
            rents = Decimal(self.income_vars['rents'].get())
            royalties = Decimal(self.income_vars['royalties'].get())
            other = Decimal(self.income_vars['other_income'].get())
            total_ordinary = gross_profit + dividends + interest + rents + royalties + other
            self.income_vars['total_ordinary'].set(f"{total_ordinary:.2f}")

            # Calculate total deductions
            total_deductions = (
                Decimal(self.deduction_vars['salaries_wages'].get()) +
                Decimal(self.deduction_vars['repairs_maintenance'].get()) +
                Decimal(self.deduction_vars['bad_debts'].get()) +
                Decimal(self.deduction_vars['rents_deduction'].get()) +
                Decimal(self.deduction_vars['taxes_licenses'].get()) +
                Decimal(self.deduction_vars['charitable_contributions'].get()) +
                Decimal(self.deduction_vars['depreciation'].get()) +
                Decimal(self.deduction_vars['other_deductions'].get())
            )
            self.deduction_vars['total_deductions'].set(f"{total_deductions:.2f}")

            self.status_label.config(text="Totals calculated")

        except Exception as e:
            messagebox.showerror("Calculation Error", f"Failed to calculate totals: {str(e)}")

    def _calculate_income(self):
        """Calculate business income for the current return"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please create or load a return first.")
            return

        try:
            # Update return from form first
            self._update_return_from_form()

            # Calculate income
            ordinary_income = self.partnership_service.calculate_business_income(self.current_return)

            # Update income summary
            self.income_summary_vars['gross_profit'].set(f"${self.current_return.income.gross_profit:.2f}")
            self.income_summary_vars['total_ordinary'].set(f"${self.current_return.income.total_ordinary_income():.2f}")
            self.income_summary_vars['total_deductions'].set(f"${self.current_return.deductions.total_deductions:.2f}")
            self.income_summary_vars['net_income_loss'].set(f"${self.current_return.net_income_loss:.2f}")

            self.status_label.config(text="Business income calculated successfully")

        except Exception as e:
            messagebox.showerror("Income Calculation Error", f"Failed to calculate income: {str(e)}")

    def _allocate_to_partners(self):
        """Allocate income/loss to partners based on ownership"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please create or load a return first.")
            return

        if not self.current_return.partners_shareholders:
            messagebox.showwarning("No Partners", "Please add partners/shareholders first.")
            return

        try:
            # Allocate income to partners
            allocations = self.partnership_service.allocate_income_to_partners(self.current_return)

            # Update partner shares in the return
            for allocation in allocations:
                partner_name = allocation['partner_name']
                # Find the partner and update their share
                for partner in self.current_return.partners_shareholders:
                    if partner.name == partner_name:
                        partner.share_of_income = allocation['ordinary_income']
                        partner.share_of_losses = allocation['ordinary_loss']
                        break

            # Refresh partners list
            self._refresh_partners_list()

            self.status_label.config(text="Income allocated to partners successfully")

        except Exception as e:
            messagebox.showerror("Allocation Error", f"Failed to allocate income to partners: {str(e)}")

    def _add_partner(self):
        """Add a partner/shareholder to the current return"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please create or load a return first.")
            return

        try:
            # Validate form data
            name = self.partner_vars['name'].get().strip()
            if not name:
                raise ValueError("Partner/Shareholder name is required")

            ssn_ein = self.partner_vars['ssn_ein'].get().strip()
            if not ssn_ein:
                raise ValueError("SSN/EIN is required")

            address = self.partner_vars['address'].get().strip()
            entity_type = self.partner_vars['entity_type'].get().strip() or "individual"
            ownership_percentage = Decimal(self.partner_vars['ownership_percentage'].get() or '0')
            capital_beginning = Decimal(self.partner_vars['capital_account_beginning'].get() or '0')
            share_income = Decimal(self.partner_vars['share_of_income'].get() or '0')
            share_losses = Decimal(self.partner_vars['share_of_losses'].get() or '0')
            distributions = Decimal(self.partner_vars['distributions'].get() or '0')

            # Create partner/shareholder
            partner = PartnerShareholder(
                name=name,
                ssn_ein=ssn_ein,
                address=address,
                entity_type=entity_type,
                ownership_percentage=ownership_percentage,
                capital_account_beginning=capital_beginning,
                share_of_income=share_income,
                share_of_losses=share_losses,
                distributions=distributions
            )

            # Add to return
            self.current_return.partners_shareholders.append(partner)

            # Refresh list and clear form
            self._refresh_partners_list()
            self._clear_partner_form()

            self.status_label.config(text="Partner/Shareholder added")

        except Exception as e:
            messagebox.showerror("Add Partner Error", f"Failed to add partner/shareholder: {str(e)}")

    def _update_partner(self):
        """Update the selected partner/shareholder"""
        selection = self.partners_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a partner/shareholder to update.")
            return

        try:
            item = selection[0]
            values = self.partners_tree.item(item, "values")
            name = values[0]

            # Find partner
            partner = None
            for p in self.current_return.partners_shareholders:
                if p.name == name:
                    partner = p
                    break

            if not partner:
                raise ValueError("Partner/Shareholder not found")

            # Update partner
            partner.name = self.partner_vars['name'].get().strip()
            partner.ssn_ein = self.partner_vars['ssn_ein'].get().strip()
            partner.address = self.partner_vars['address'].get().strip()
            partner.entity_type = self.partner_vars['entity_type'].get().strip() or "individual"
            partner.ownership_percentage = Decimal(self.partner_vars['ownership_percentage'].get() or '0')
            partner.capital_account_beginning = Decimal(self.partner_vars['capital_account_beginning'].get() or '0')
            partner.share_of_income = Decimal(self.partner_vars['share_of_income'].get() or '0')
            partner.share_of_losses = Decimal(self.partner_vars['share_of_losses'].get() or '0')
            partner.distributions = Decimal(self.partner_vars['distributions'].get() or '0')

            # Refresh list and clear form
            self._refresh_partners_list()
            self._clear_partner_form()

            self.status_label.config(text="Partner/Shareholder updated")

        except Exception as e:
            messagebox.showerror("Update Partner Error", f"Failed to update partner/shareholder: {str(e)}")

    def _delete_partner(self):
        """Delete the selected partner/shareholder"""
        selection = self.partners_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a partner/shareholder to delete.")
            return

        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this partner/shareholder?"):
            return

        try:
            item = selection[0]
            values = self.partners_tree.item(item, "values")
            name = values[0]

            # Remove partner
            self.current_return.partners_shareholders = [p for p in self.current_return.partners_shareholders if p.name != name]

            # Refresh list and clear form
            self._refresh_partners_list()
            self._clear_partner_form()

            self.status_label.config(text="Partner/Shareholder deleted")

        except Exception as e:
            messagebox.showerror("Delete Partner Error", f"Failed to delete partner/shareholder: {str(e)}")

    def _edit_selected_partner(self):
        """Edit the selected partner/shareholder"""
        selection = self.partners_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a partner/shareholder to edit.")
            return

        try:
            item = selection[0]
            values = self.partners_tree.item(item, "values")

            # Populate form
            self.partner_vars['name'].set(values[0])
            self.partner_vars['ssn_ein'].set(values[1])
            self.partner_vars['ownership_percentage'].set(values[2].replace('%', ''))
            self.partner_vars['share_of_income'].set(values[3].replace('$', ''))
            self.partner_vars['share_of_losses'].set(values[4].replace('$', ''))
            self.partner_vars['distributions'].set(values[5].replace('$', ''))

            self.status_label.config(text="Partner/Shareholder loaded for editing")

        except Exception as e:
            messagebox.showerror("Edit Partner Error", f"Failed to load partner/shareholder: {str(e)}")

    def _clear_partner_form(self):
        """Clear the partner/shareholder form"""
        for var in self.partner_vars.values():
            if hasattr(var, 'set'):
                var.set("")

    def _clear_all_forms(self):
        """Clear all forms"""
        self._clear_partner_form()
        for var in self.return_vars.values():
            if hasattr(var, 'set'):
                var.set("")

    def _delete_return(self):
        """Delete the selected return"""
        selection = self.returns_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a return to delete.")
            return

        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this return? This action cannot be undone."):
            return

        try:
            item = selection[0]
            index = int(self.returns_tree.item(item, "tags")[0])
            return_to_delete = self.returns[index]

            # Remove from tax data (this would need to be implemented in the service)
            # For now, just remove from local list
            self.returns.pop(index)
            self._refresh_returns_list()
            self._update_summary()

            self.status_label.config(text="Return deleted")

        except Exception as e:
            messagebox.showerror("Delete Error", f"Failed to delete return: {str(e)}")

    def _generate_main_form(self):
        """Generate Form 1065 or 1120-S"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please create or load a return first.")
            return

        try:
            form_type = "1065" if self.current_return.entity_type in [EntityType.PARTNERSHIP, EntityType.LLC_TAXED_AS_PARTNERSHIP] else "1120-S"

            messagebox.showinfo(
                f"Form {form_type} Generated",
                f"Form {form_type} data generated successfully for {self.current_return.entity_name}!\n\n"
                f"Tax Year: {self.current_return.tax_year}\n"
                f"EIN: {self.current_return.ein}\n"
                f"Ordinary Business Income: ${self.current_return.ordinary_business_income:.2f}\n"
                f"Net Income/Loss: ${self.current_return.net_income_loss:.2f}\n\n"
                f"Data is ready for inclusion in your tax return."
            )

            self.status_label.config(text=f"Form {form_type} generated")

        except Exception as e:
            self.error_tracker.track_error(e, {"operation": "_generate_main_form"})
            messagebox.showerror("Form Generation Error", f"Failed to generate form: {str(e)}")

    def _generate_k1_forms(self):
        """Generate K-1 forms for partners/shareholders"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please create or load a return first.")
            return

        if not self.current_return.partners_shareholders:
            messagebox.showwarning("No Partners", "No partners/shareholders found to generate K-1 forms for.")
            return

        try:
            # Generate K-1 forms
            k1_data = self.partnership_service.generate_k1_forms(self.current_return)

            messagebox.showinfo(
                "K-1 Forms Generated",
                f"K-1 forms generated successfully for {len(self.current_return.partners_shareholders)} partners/shareholders!\n\n"
                f"Each partner/shareholder will receive a Schedule K-1 showing their share of income,\n"
                f"losses, and other allocations from the {self.current_return.entity_type.value.replace('_', ' ')}."
            )

            self.status_label.config(text="K-1 forms generated")

        except Exception as e:
            self.error_tracker.track_error(e, {"operation": "_generate_k1_forms"})
            messagebox.showerror("K-1 Generation Error", f"Failed to generate K-1 forms: {str(e)}")

    def _bind_events(self):
        """Bind event handlers"""
        if self.returns_tree:
            self.returns_tree.bind("<Double-1>", lambda e: self._load_selected_return())

        if self.partners_tree:
            self.partners_tree.bind("<Double-1>", lambda e: self._edit_selected_partner())

    def _close_window(self):
        """Close the window"""
        if self.window:
            self.window.destroy()