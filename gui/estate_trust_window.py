"""
Estate and Trust Tax Returns Window

GUI for managing estate and trust tax returns (Form 1041).
Supports estates, trusts, and fiduciary income tax reporting.
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
from utils.error_tracker import get_error_tracker


class EstateTrustWindow:
    """
    Window for managing estate and trust tax returns.

    Features:
    - Estate and trust return creation and management
    - Beneficiary management
    - Income and deduction tracking
    - Form 1041 generation
    - K-1 form generation for beneficiaries
    - Tax calculation and liability estimation
    """

    def __init__(self, parent: tk.Tk, config: AppConfig, tax_data: Optional[TaxData] = None):
        """
        Initialize estate and trust tax returns window.

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
        self.estate_service = EstateTrustService(config)

        # Current data
        self.returns: List[EstateTrustReturn] = []
        self.current_return: Optional[EstateTrustReturn] = None

        # UI components
        self.window: Optional[tk.Toplevel] = None
        self.notebook: Optional[ttk.Notebook] = None
        self.returns_tree: Optional[ttk.Treeview] = None
        self.beneficiaries_tree: Optional[ttk.Treeview] = None
        self.progress_var: Optional[tk.DoubleVar] = None
        self.status_label: Optional[ttk.Label] = None

        # Form variables
        self.return_vars = {}
        self.beneficiary_vars = {}
        self.income_vars = {}
        self.deduction_vars = {}

    def show(self):
        """Show the estate and trust tax returns window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Estate & Trust Tax Returns - Freedom US Tax Return")
        self.window.geometry("1400x900")
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
            text="Estate & Trust Tax Returns (Form 1041)",
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
        self._create_beneficiaries_tab()
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
            text="Calculate Tax",
            command=self._calculate_tax
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            button_frame,
            text="Generate Form 1041",
            command=self._generate_form_1041
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
        list_frame = ttk.LabelFrame(tab, text="Estate & Trust Returns")
        list_frame.pack(fill="both", expand=True, pady=(0, 10))

        columns = ("Tax Year", "Entity Type", "Entity Name", "EIN", "Taxable Income", "Tax Due", "Balance Due")
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
            ("Total Taxable Income:", "total_taxable"),
            ("Total Tax Due:", "total_tax_due"),
            ("Total Balance Due:", "total_balance")
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
            values=["Estate", "Trust"],
            state="readonly"
        )
        entity_combo.grid(row=1, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="Entity Name:").grid(row=2, column=0, sticky="w", pady=5, padx=10)
        self.return_vars['entity_name'] = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.return_vars['entity_name']).grid(row=2, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="EIN:").grid(row=3, column=0, sticky="w", pady=5, padx=10)
        self.return_vars['ein'] = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.return_vars['ein']).grid(row=3, column=1, sticky="ew", pady=5, padx=(0, 10))

        # Fiduciary information
        ttk.Label(form_frame, text="Fiduciary Name:").grid(row=4, column=0, sticky="w", pady=5, padx=10)
        self.return_vars['fiduciary_name'] = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.return_vars['fiduciary_name']).grid(row=4, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="Fiduciary Address:").grid(row=5, column=0, sticky="w", pady=5, padx=10)
        self.return_vars['fiduciary_address'] = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.return_vars['fiduciary_address']).grid(row=5, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="Fiduciary Phone:").grid(row=6, column=0, sticky="w", pady=5, padx=10)
        self.return_vars['fiduciary_phone'] = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.return_vars['fiduciary_phone']).grid(row=6, column=1, sticky="ew", pady=5, padx=(0, 10))

        # Trust/Estate specific
        ttk.Label(form_frame, text="Trust Type:").grid(row=7, column=0, sticky="w", pady=5, padx=10)
        self.return_vars['trust_type'] = tk.StringVar()
        trust_combo = ttk.Combobox(
            form_frame,
            textvariable=self.return_vars['trust_type'],
            values=[t.value for t in TrustType],
            state="readonly"
        )
        trust_combo.grid(row=7, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="Estate Type:").grid(row=8, column=0, sticky="w", pady=5, padx=10)
        self.return_vars['estate_type'] = tk.StringVar()
        estate_combo = ttk.Combobox(
            form_frame,
            textvariable=self.return_vars['estate_type'],
            values=[e.value for e in EstateType],
            state="readonly"
        )
        estate_combo.grid(row=8, column=1, sticky="ew", pady=5, padx=(0, 10))

        # Configure grid weights
        form_frame.columnconfigure(1, weight=1)

    def _create_income_deductions_tab(self):
        """Create the income and deductions tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Income & Deductions")

        # Split into income and deductions sections
        income_frame = ttk.LabelFrame(tab, text="Income")
        income_frame.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=10)

        deductions_frame = ttk.LabelFrame(tab, text="Deductions")
        deductions_frame.pack(side="right", fill="both", expand=True, padx=(5, 0), pady=10)

        # Income fields
        self.income_vars = {}
        income_fields = [
            ("Interest Income:", "interest_income"),
            ("Dividend Income:", "dividend_income"),
            ("Business Income:", "business_income"),
            ("Capital Gains:", "capital_gains"),
            ("Rental Income:", "rental_income"),
            ("Royalty Income:", "royalty_income"),
            ("Other Income:", "other_income"),
            ("Total Income:", "total_income")
        ]

        for i, (label, key) in enumerate(income_fields):
            ttk.Label(income_frame, text=label).grid(row=i, column=0, sticky="w", pady=3, padx=10)
            self.income_vars[key] = tk.StringVar(value="0.00")
            entry = ttk.Entry(income_frame, textvariable=self.income_vars[key])
            entry.grid(row=i, column=1, sticky="ew", pady=3, padx=(0, 10))
            if key == "total_income":
                entry.config(state="readonly")

        # Deductions fields
        self.deduction_vars = {}
        deduction_fields = [
            ("Fiduciary Fees:", "fiduciary_fees"),
            ("Attorney Fees:", "attorney_fees"),
            ("Accounting Fees:", "accounting_fees"),
            ("Other Admin Expenses:", "other_administrative_expenses"),
            ("Charitable Contributions:", "charitable_contributions"),
            ("Net Operating Loss:", "net_operating_loss"),
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

    def _create_beneficiaries_tab(self):
        """Create the beneficiaries management tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Beneficiaries")

        # Beneficiaries list
        list_frame = ttk.LabelFrame(tab, text="Trust Beneficiaries")
        list_frame.pack(fill="both", expand=True, pady=(0, 10))

        columns = ("Name", "SSN", "Relationship", "Share %", "Income Distributed", "Distribution Type")
        self.beneficiaries_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)

        for col in columns:
            self.beneficiaries_tree.heading(col, text=col)
            self.beneficiaries_tree.column(col, width=120)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.beneficiaries_tree.yview)
        self.beneficiaries_tree.configure(yscrollcommand=scrollbar.set)

        self.beneficiaries_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Beneficiary form
        form_frame = ttk.LabelFrame(tab, text="Beneficiary Details")
        form_frame.pack(fill="both", expand=True)

        # Initialize beneficiary variables
        self.beneficiary_vars = {}

        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky="w", pady=5, padx=10)
        self.beneficiary_vars['name'] = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.beneficiary_vars['name']).grid(row=0, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="SSN:").grid(row=1, column=0, sticky="w", pady=5, padx=10)
        self.beneficiary_vars['ssn'] = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.beneficiary_vars['ssn']).grid(row=1, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="Address:").grid(row=2, column=0, sticky="w", pady=5, padx=10)
        self.beneficiary_vars['address'] = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.beneficiary_vars['address']).grid(row=2, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="Relationship:").grid(row=3, column=0, sticky="w", pady=5, padx=10)
        self.beneficiary_vars['relationship'] = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.beneficiary_vars['relationship']).grid(row=3, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="Share Percentage:").grid(row=4, column=0, sticky="w", pady=5, padx=10)
        self.beneficiary_vars['share_percentage'] = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.beneficiary_vars['share_percentage']).grid(row=4, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="Income Distributed:").grid(row=5, column=0, sticky="w", pady=5, padx=10)
        self.beneficiary_vars['income_distributed'] = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.beneficiary_vars['income_distributed']).grid(row=5, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(form_frame, text="Distribution Type:").grid(row=6, column=0, sticky="w", pady=5, padx=10)
        self.beneficiary_vars['distribution_type'] = tk.StringVar()
        dist_combo = ttk.Combobox(
            form_frame,
            textvariable=self.beneficiary_vars['distribution_type'],
            values=[dt.value for dt in IncomeDistributionType],
            state="readonly"
        )
        dist_combo.grid(row=6, column=1, sticky="ew", pady=5, padx=(0, 10))

        # Form buttons
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=(10, 0))

        ttk.Button(btn_frame, text="Add Beneficiary", command=self._add_beneficiary).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Update Beneficiary", command=self._update_beneficiary).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Delete Beneficiary", command=self._delete_beneficiary).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Clear Form", command=self._clear_beneficiary_form).pack(side="left", padx=(0, 5))

        # Configure grid weights
        form_frame.columnconfigure(1, weight=1)

        # Beneficiary buttons
        list_btn_frame = ttk.Frame(tab)
        list_btn_frame.pack(fill="x")

        ttk.Button(list_btn_frame, text="Edit Selected", command=self._edit_selected_beneficiary).pack(side="left", padx=(0, 5))

    def _create_forms_tab(self):
        """Create the forms and reports tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Forms & Reports")

        # Form 1041 section
        form_frame = ttk.LabelFrame(tab, text="Form 1041 - U.S. Income Tax Return for Estates and Trusts")
        form_frame.pack(fill="both", expand=True, pady=(0, 10))

        ttk.Label(
            form_frame,
            text="Form 1041 is used to report income, deductions, and tax liability for estates and trusts.\n" +
                 "This form is filed annually and is due on the 15th day of the 4th month after the end of the tax year.",
            wraplength=800,
            justify="left"
        ).pack(pady=10, padx=10, anchor="w")

        ttk.Button(
            form_frame,
            text="Generate Form 1041",
            command=self._generate_form_1041
        ).pack(pady=(0, 10), padx=10, anchor="w")

        # K-1 forms section
        k1_frame = ttk.LabelFrame(tab, text="Schedule K-1 (Form 1041) - Beneficiary's Share of Income, Deductions, Credits")
        k1_frame.pack(fill="both", expand=True, pady=(0, 10))

        ttk.Label(
            k1_frame,
            text="Schedule K-1 reports each beneficiary's share of income, deductions, and credits from the estate or trust.\n" +
                 "A separate K-1 must be provided to each beneficiary.",
            wraplength=800,
            justify="left"
        ).pack(pady=10, padx=10, anchor="w")

        ttk.Button(
            k1_frame,
            text="Generate K-1 Forms",
            command=self._generate_k1_forms
        ).pack(pady=(0, 10), padx=10, anchor="w")

        # Tax calculation summary
        tax_frame = ttk.LabelFrame(tab, text="Tax Calculation Summary")
        tax_frame.pack(fill="x")

        ttk.Label(
            tax_frame,
            text="Current tax calculation for the loaded estate/trust return:",
            wraplength=800,
            justify="left"
        ).pack(pady=10, padx=10, anchor="w")

        # Tax summary labels
        self.tax_summary_vars = {}
        tax_items = [
            ("Taxable Income:", "taxable_income"),
            ("Tax Due:", "tax_due"),
            ("Payments/Credits:", "payments_credits"),
            ("Balance Due/Refund:", "balance_due")
        ]

        for item in tax_items:
            frame = ttk.Frame(tax_frame)
            frame.pack(fill="x", padx=20, pady=2)
            ttk.Label(frame, text=item[0]).pack(side="left")
            self.tax_summary_vars[item[1]] = tk.StringVar(value="$0.00")
            ttk.Label(frame, textvariable=self.tax_summary_vars[item[1]], font=("Arial", 10, "bold")).pack(side="right")

    def _load_data(self):
        """Load existing estate/trust data"""
        try:
            if self.tax_data:
                # Load returns from tax data
                self.returns = self.estate_service.load_estate_trust_returns(self.tax_data)

            self._refresh_returns_list()
            self._update_summary()

            self.status_label.config(text="Data loaded successfully")

        except Exception as e:
            self.error_tracker.track_error(e, {"operation": "_load_data"})
            messagebox.showerror("Load Error", f"Failed to load estate/trust data: {str(e)}")

    def _refresh_returns_list(self):
        """Refresh the returns treeview"""
        if not self.returns_tree:
            return

        # Clear existing items
        for item in self.returns_tree.get_children():
            self.returns_tree.delete(item)

        # Add returns
        for i, return_data in enumerate(self.returns):
            self.returns_tree.insert("", "end", values=(
                return_data.tax_year,
                return_data.entity_type,
                return_data.entity_name or "",
                return_data.ein,
                f"${return_data.taxable_income:.2f}",
                f"${return_data.tax_due:.2f}",
                f"${return_data.balance_due:.2f}"
            ), tags=(str(i),))

    def _refresh_beneficiaries_list(self):
        """Refresh the beneficiaries treeview"""
        if not self.beneficiaries_tree or not self.current_return:
            return

        # Clear existing items
        for item in self.beneficiaries_tree.get_children():
            self.beneficiaries_tree.delete(item)

        # Add beneficiaries
        for beneficiary in self.current_return.beneficiaries:
            self.beneficiaries_tree.insert("", "end", values=(
                beneficiary.name,
                beneficiary.ssn,
                beneficiary.relationship,
                f"{beneficiary.share_percentage:.2f}%",
                f"${beneficiary.income_distributed:.2f}",
                beneficiary.distribution_type.value
            ))

    def _update_summary(self):
        """Update the tax year summary"""
        if not self.returns:
            return

        total_returns = len(self.returns)
        total_taxable = sum(r.taxable_income for r in self.returns)
        total_tax_due = sum(r.tax_due for r in self.returns)
        total_balance = sum(r.balance_due for r in self.returns)

        self.summary_vars['total_returns'].set(str(total_returns))
        self.summary_vars['total_taxable'].set(f"${total_taxable:.2f}")
        self.summary_vars['total_tax_due'].set(f"${total_tax_due:.2f}")
        self.summary_vars['total_balance'].set(f"${total_balance:.2f}")

    def _new_return(self):
        """Create a new estate/trust return"""
        try:
            # Create new return
            self.current_return = EstateTrustReturn(
                tax_year=int(self.return_vars['tax_year'].get()),
                entity_type=self.return_vars['entity_type'].get(),
                entity_name="",
                ein="",
                fiduciary_name="",
                fiduciary_address="",
                fiduciary_phone=""
            )

            # Clear all forms
            self._clear_all_forms()

            # Set default values
            self.return_vars['entity_name'].set("")
            self.return_vars['ein'].set("")
            self.return_vars['fiduciary_name'].set("")
            self.return_vars['fiduciary_address'].set("")
            self.return_vars['fiduciary_phone'].set("")
            self.return_vars['trust_type'].set("")
            self.return_vars['estate_type'].set("")

            # Clear income and deductions
            for var in self.income_vars.values():
                var.set("0.00")
            for var in self.deduction_vars.values():
                var.set("0.00")

            # Clear beneficiaries
            self.current_return.beneficiaries = []
            self._refresh_beneficiaries_list()

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
            self._refresh_beneficiaries_list()

            self.status_label.config(text=f"Loaded {self.current_return.entity_type} return for {self.current_return.entity_name}")

        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load return: {str(e)}")

    def _populate_return_form(self):
        """Populate the return form with current return data"""
        if not self.current_return:
            return

        self.return_vars['tax_year'].set(str(self.current_return.tax_year))
        self.return_vars['entity_type'].set(self.current_return.entity_type)
        self.return_vars['entity_name'].set(self.current_return.entity_name or "")
        self.return_vars['ein'].set(self.current_return.ein)
        self.return_vars['fiduciary_name'].set(self.current_return.fiduciary_name)
        self.return_vars['fiduciary_address'].set(self.current_return.fiduciary_address)
        self.return_vars['fiduciary_phone'].set(self.current_return.fiduciary_phone)
        self.return_vars['trust_type'].set(self.current_return.trust_type.value if self.current_return.trust_type else "")
        self.return_vars['estate_type'].set(self.current_return.estate_type.value if self.current_return.estate_type else "")

    def _populate_income_form(self):
        """Populate the income form with current return data"""
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
        """Populate the deductions form with current return data"""
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
            # Update return data from forms
            self._update_return_from_form()

            # Save to tax data
            if self.tax_data:
                success = self.estate_service.save_estate_trust_return(self.tax_data, self.current_return)
                if success:
                    # Reload returns list
                    self.returns = self.estate_service.load_estate_trust_returns(self.tax_data)
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
        self.current_return.entity_type = self.return_vars['entity_type'].get()
        self.current_return.entity_name = self.return_vars['entity_name'].get()
        self.current_return.ein = self.return_vars['ein'].get()
        self.current_return.fiduciary_name = self.return_vars['fiduciary_name'].get()
        self.current_return.fiduciary_address = self.return_vars['fiduciary_address'].get()
        self.current_return.fiduciary_phone = self.return_vars['fiduciary_phone'].get()

        # Trust/Estate type
        trust_type_str = self.return_vars['trust_type'].get()
        self.current_return.trust_type = TrustType(trust_type_str) if trust_type_str else None

        estate_type_str = self.return_vars['estate_type'].get()
        self.current_return.estate_type = EstateType(estate_type_str) if estate_type_str else None

        # Income
        self.current_return.income.interest_income = Decimal(self.income_vars['interest_income'].get())
        self.current_return.income.dividend_income = Decimal(self.income_vars['dividend_income'].get())
        self.current_return.income.business_income = Decimal(self.income_vars['business_income'].get())
        self.current_return.income.capital_gains = Decimal(self.income_vars['capital_gains'].get())
        self.current_return.income.rental_income = Decimal(self.income_vars['rental_income'].get())
        self.current_return.income.royalty_income = Decimal(self.income_vars['royalty_income'].get())
        self.current_return.income.other_income = Decimal(self.income_vars['other_income'].get())
        self.current_return.income.calculate_total()

        # Deductions
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
            # Calculate income total
            total_income = (
                Decimal(self.income_vars['interest_income'].get()) +
                Decimal(self.income_vars['dividend_income'].get()) +
                Decimal(self.income_vars['business_income'].get()) +
                Decimal(self.income_vars['capital_gains'].get()) +
                Decimal(self.income_vars['rental_income'].get()) +
                Decimal(self.income_vars['royalty_income'].get()) +
                Decimal(self.income_vars['other_income'].get())
            )
            self.income_vars['total_income'].set(f"{total_income:.2f}")

            # Calculate deductions total
            total_deductions = (
                Decimal(self.deduction_vars['fiduciary_fees'].get()) +
                Decimal(self.deduction_vars['attorney_fees'].get()) +
                Decimal(self.deduction_vars['accounting_fees'].get()) +
                Decimal(self.deduction_vars['other_administrative_expenses'].get()) +
                Decimal(self.deduction_vars['charitable_contributions'].get()) +
                Decimal(self.deduction_vars['net_operating_loss'].get())
            )
            self.deduction_vars['total_deductions'].set(f"{total_deductions:.2f}")

            self.status_label.config(text="Totals calculated")

        except Exception as e:
            messagebox.showerror("Calculation Error", f"Failed to calculate totals: {str(e)}")

    def _calculate_tax(self):
        """Calculate tax for the current return"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please create or load a return first.")
            return

        try:
            # Update return from form first
            self._update_return_from_form()

            # Calculate tax
            result = self.estate_service.calculate_tax(self.current_return)

            if result.get('success'):
                # Update tax summary
                self.tax_summary_vars['taxable_income'].set(f"${result['taxable_income']:.2f}")
                self.tax_summary_vars['tax_due'].set(f"${result['tax_due']:.2f}")
                self.tax_summary_vars['payments_credits'].set(f"${self.current_return.payments_credits:.2f}")
                balance = result['balance_due']
                balance_text = f"${balance:.2f}" if balance >= 0 else f"(${abs(balance):.2f})"
                self.tax_summary_vars['balance_due'].set(balance_text)

                self.status_label.config(text="Tax calculated successfully")
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
            # Validate form data
            name = self.beneficiary_vars['name'].get().strip()
            if not name:
                raise ValueError("Beneficiary name is required")

            ssn = self.beneficiary_vars['ssn'].get().strip()
            if not ssn:
                raise ValueError("SSN is required")

            address = self.beneficiary_vars['address'].get().strip()
            relationship = self.beneficiary_vars['relationship'].get().strip()
            share_percentage = Decimal(self.beneficiary_vars['share_percentage'].get() or '0')
            income_distributed = Decimal(self.beneficiary_vars['income_distributed'].get() or '0')
            distribution_type = IncomeDistributionType(self.beneficiary_vars['distribution_type'].get() or 'ordinary_income')

            # Create beneficiary
            beneficiary = TrustBeneficiary(
                name=name,
                ssn=ssn,
                address=address,
                relationship=relationship,
                share_percentage=share_percentage,
                income_distributed=income_distributed,
                distribution_type=distribution_type
            )

            # Add to return
            self.current_return.beneficiaries.append(beneficiary)

            # Refresh list and clear form
            self._refresh_beneficiaries_list()
            self._clear_beneficiary_form()

            self.status_label.config(text="Beneficiary added")

        except Exception as e:
            messagebox.showerror("Add Beneficiary Error", f"Failed to add beneficiary: {str(e)}")

    def _update_beneficiary(self):
        """Update the selected beneficiary"""
        selection = self.beneficiaries_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a beneficiary to update.")
            return

        try:
            item = selection[0]
            values = self.beneficiaries_tree.item(item, "values")
            name = values[0]

            # Find beneficiary
            beneficiary = None
            for b in self.current_return.beneficiaries:
                if b.name == name:
                    beneficiary = b
                    break

            if not beneficiary:
                raise ValueError("Beneficiary not found")

            # Update beneficiary
            beneficiary.name = self.beneficiary_vars['name'].get().strip()
            beneficiary.ssn = self.beneficiary_vars['ssn'].get().strip()
            beneficiary.address = self.beneficiary_vars['address'].get().strip()
            beneficiary.relationship = self.beneficiary_vars['relationship'].get().strip()
            beneficiary.share_percentage = Decimal(self.beneficiary_vars['share_percentage'].get() or '0')
            beneficiary.income_distributed = Decimal(self.beneficiary_vars['income_distributed'].get() or '0')
            beneficiary.distribution_type = IncomeDistributionType(self.beneficiary_vars['distribution_type'].get() or 'ordinary_income')

            # Refresh list and clear form
            self._refresh_beneficiaries_list()
            self._clear_beneficiary_form()

            self.status_label.config(text="Beneficiary updated")

        except Exception as e:
            messagebox.showerror("Update Beneficiary Error", f"Failed to update beneficiary: {str(e)}")

    def _delete_beneficiary(self):
        """Delete the selected beneficiary"""
        selection = self.beneficiaries_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a beneficiary to delete.")
            return

        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this beneficiary?"):
            return

        try:
            item = selection[0]
            values = self.beneficiaries_tree.item(item, "values")
            name = values[0]

            # Remove beneficiary
            self.current_return.beneficiaries = [b for b in self.current_return.beneficiaries if b.name != name]

            # Refresh list and clear form
            self._refresh_beneficiaries_list()
            self._clear_beneficiary_form()

            self.status_label.config(text="Beneficiary deleted")

        except Exception as e:
            messagebox.showerror("Delete Beneficiary Error", f"Failed to delete beneficiary: {str(e)}")

    def _edit_selected_beneficiary(self):
        """Edit the selected beneficiary"""
        selection = self.beneficiaries_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a beneficiary to edit.")
            return

        try:
            item = selection[0]
            values = self.beneficiaries_tree.item(item, "values")

            # Populate form
            self.beneficiary_vars['name'].set(values[0])
            self.beneficiary_vars['ssn'].set(values[1])
            self.beneficiary_vars['relationship'].set(values[2])
            self.beneficiary_vars['share_percentage'].set(values[3].replace('%', ''))
            self.beneficiary_vars['income_distributed'].set(values[4].replace('$', ''))
            self.beneficiary_vars['distribution_type'].set(values[5])

            self.status_label.config(text="Beneficiary loaded for editing")

        except Exception as e:
            messagebox.showerror("Edit Beneficiary Error", f"Failed to load beneficiary: {str(e)}")

    def _clear_beneficiary_form(self):
        """Clear the beneficiary form"""
        for var in self.beneficiary_vars.values():
            if hasattr(var, 'set'):
                var.set("")

    def _clear_all_forms(self):
        """Clear all forms"""
        self._clear_beneficiary_form()
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

            # Remove from tax data
            if self.tax_data:
                existing_returns = self.tax_data.get("estate_trust_returns", [])
                existing_returns = [r for r in existing_returns if not (
                    r.get('tax_year') == return_to_delete.tax_year and
                    r.get('entity_type') == return_to_delete.entity_type and
                    r.get('ein') == return_to_delete.ein
                )]
                self.tax_data.set("estate_trust_returns", existing_returns)

                # Reload returns
                self.returns = self.estate_service.load_estate_trust_returns(self.tax_data)
                self._refresh_returns_list()
                self._update_summary()

            self.status_label.config(text="Return deleted")

        except Exception as e:
            messagebox.showerror("Delete Error", f"Failed to delete return: {str(e)}")

    def _generate_form_1041(self):
        """Generate Form 1041"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please create or load a return first.")
            return

        try:
            # Generate Form 1041 data
            form_data = self.estate_service.generate_form_1041_data(self.current_return)

            messagebox.showinfo(
                "Form 1041 Generated",
                f"Form 1041 data generated successfully for {self.current_return.entity_name}!\n\n"
                f"Tax Year: {self.current_return.tax_year}\n"
                f"EIN: {self.current_return.ein}\n"
                f"Taxable Income: ${self.current_return.taxable_income:.2f}\n"
                f"Tax Due: ${self.current_return.tax_due:.2f}\n\n"
                f"Data is ready for inclusion in your tax return."
            )

            self.status_label.config(text="Form 1041 generated")

        except Exception as e:
            self.error_tracker.track_error(e, {"operation": "_generate_form_1041"})
            messagebox.showerror("Form Generation Error", f"Failed to generate Form 1041: {str(e)}")

    def _generate_k1_forms(self):
        """Generate K-1 forms for beneficiaries"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please create or load a return first.")
            return

        if not self.current_return.beneficiaries:
            messagebox.showwarning("No Beneficiaries", "No beneficiaries found to generate K-1 forms for.")
            return

        try:
            # Generate K-1 forms
            k1_data = self.estate_service.generate_k1_forms(self.current_return)

            messagebox.showinfo(
                "K-1 Forms Generated",
                f"K-1 forms generated successfully for {len(self.current_return.beneficiaries)} beneficiaries!\n\n"
                f"Each beneficiary will receive a Schedule K-1 showing their share of income,\n"
                f"deductions, and credits from the {self.current_return.entity_type.lower()}."
            )

            self.status_label.config(text="K-1 forms generated")

        except Exception as e:
            self.error_tracker.track_error(e, {"operation": "_generate_k1_forms"})
            messagebox.showerror("K-1 Generation Error", f"Failed to generate K-1 forms: {str(e)}")

    def _bind_events(self):
        """Bind event handlers"""
        if self.returns_tree:
            self.returns_tree.bind("<Double-1>", lambda e: self._load_selected_return())

        if self.beneficiaries_tree:
            self.beneficiaries_tree.bind("<Double-1>", lambda e: self._edit_selected_beneficiary())

    def _close_window(self):
        """Close the window"""
        if self.window:
            self.window.destroy()