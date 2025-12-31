"""
Partnership and S-Corp Tax Return Page

Page for preparing Form 1065 (Partnership) and Form 1120-S (S-Corp) tax returns.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, List
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.partnership_s_corp_service import (
    PartnershipSCorpService,
    PartnershipSCorpReturn,
    EntityType,
    PartnershipType,
    SCorpShareholderType,
    PartnerShareholder,
    BusinessIncome,
    BusinessDeductions
)


class PartnershipSCorpPage(ttk.Frame):
    """
    Page for partnership and S-Corp tax return preparation.

    Allows users to:
    - Create new partnership/S-Corp returns
    - Enter income and deduction data
    - Manage partners/shareholders
    - Calculate business income/loss
    - Generate Form 1065/1120-S and K-1 forms
    """

    def __init__(self, parent, tax_data: TaxData, main_window, config: AppConfig):
        super().__init__(parent)
        self.tax_data = tax_data
        self.main_window = main_window
        self.config = config

        # Initialize service
        self.ps_service = PartnershipSCorpService(config)

        # UI components
        self.returns_tree = None
        self.current_return = None
        self.income_vars = {}
        self.deduction_vars = {}

        self.build_ui()
        self.load_returns()

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
            text="Partnership and S-Corp Tax Returns (Form 1065/1120-S)",
            font=("Arial", 16, "bold")
        )
        title_label.pack(anchor="w")

        description_label = ttk.Label(
            header_frame,
            text="Prepare U.S. Partnership (1065) and S-Corp (1120-S) tax returns. Supports pass-through entity taxation with K-1 generation.",
            wraplength=700,
            justify="left"
        )
        description_label.pack(anchor="w", pady=(5, 0))

        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True, pady=(10, 0))

        # Returns List tab
        list_frame = ttk.Frame(notebook)
        notebook.add(list_frame, text="Returns")

        self.build_returns_list_tab(list_frame)

        # Entity Info tab
        entity_frame = ttk.Frame(notebook)
        notebook.add(entity_frame, text="Entity Info")

        self.build_entity_tab(entity_frame)

        # Income tab
        income_frame = ttk.Frame(notebook)
        notebook.add(income_frame, text="Income")

        self.build_income_tab(income_frame)

        # Deductions tab
        deductions_frame = ttk.Frame(notebook)
        notebook.add(deductions_frame, text="Deductions")

        self.build_deductions_tab(deductions_frame)

        # Partners/Shareholders tab
        partners_frame = ttk.Frame(notebook)
        notebook.add(partners_frame, text="Partners/Shareholders")

        self.build_partners_tab(partners_frame)

        # Tax Calculation tab
        tax_frame = ttk.Frame(notebook)
        notebook.add(tax_frame, text="Tax Calculation")

        self.build_tax_tab(tax_frame)

    def build_returns_list_tab(self, parent):
        """Build the returns list tab"""
        # Toolbar
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill="x", pady=(0, 10))

        ttk.Button(
            toolbar,
            text="New Partnership Return",
            command=lambda: self.create_new_return("partnership")
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            toolbar,
            text="New S-Corp Return",
            command=lambda: self.create_new_return("s_corp")
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Edit Selected",
            command=self.edit_selected_return
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Delete Selected",
            command=self.delete_selected_return
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Generate Forms",
            command=self.generate_forms
        ).pack(side="right")

        # Returns treeview
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill="both", expand=True)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal")

        self.returns_tree = ttk.Treeview(
            tree_frame,
            columns=("entity_type", "entity_name", "ein", "tax_year", "net_income_loss", "partners_shareholders", "status"),
            show="headings",
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )

        # Configure columns
        self.returns_tree.heading("entity_type", text="Type")
        self.returns_tree.heading("entity_name", text="Entity Name")
        self.returns_tree.heading("ein", text="EIN")
        self.returns_tree.heading("tax_year", text="Tax Year")
        self.returns_tree.heading("net_income_loss", text="Net Income/Loss")
        self.returns_tree.heading("partners_shareholders", text="Partners/Shareholders")
        self.returns_tree.heading("status", text="Status")

        self.returns_tree.column("entity_type", width=100)
        self.returns_tree.column("entity_name", width=200)
        self.returns_tree.column("ein", width=100)
        self.returns_tree.column("tax_year", width=80)
        self.returns_tree.column("net_income_loss", width=120)
        self.returns_tree.column("partners_shareholders", width=120)
        self.returns_tree.column("status", width=80)

        # Pack tree and scrollbars
        self.returns_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        v_scrollbar.config(command=self.returns_tree.yview)
        h_scrollbar.config(command=self.returns_tree.xview)

        # Bind selection event
        self.returns_tree.bind('<<TreeviewSelect>>', self.on_return_selected)

    def build_entity_tab(self, parent):
        """Build the entity information tab"""
        # Entity Information section
        entity_frame = ttk.LabelFrame(parent, text="Entity Information", padding="10")
        entity_frame.pack(fill="x", pady=(0, 10))

        # Row 1: Entity Name and EIN
        ttk.Label(entity_frame, text="Entity Name:").grid(row=0, column=0, sticky="w", pady=5)
        self.entity_name_var = tk.StringVar()
        ttk.Entry(entity_frame, textvariable=self.entity_name_var, width=40).grid(row=0, column=1, sticky="ew", pady=5)

        ttk.Label(entity_frame, text="EIN:").grid(row=0, column=2, sticky="w", pady=5, padx=(20, 0))
        self.ein_var = tk.StringVar()
        ttk.Entry(entity_frame, textvariable=self.ein_var, width=15).grid(row=0, column=3, sticky="w", pady=5)

        # Row 2: Business Description
        ttk.Label(entity_frame, text="Business Description:").grid(row=1, column=0, sticky="w", pady=5)
        self.business_desc_var = tk.StringVar()
        ttk.Entry(entity_frame, textvariable=self.business_desc_var, width=60).grid(row=1, column=1, columnspan=3, sticky="ew", pady=5)

        # Row 3: Business Address
        ttk.Label(entity_frame, text="Business Address:").grid(row=2, column=0, sticky="w", pady=5)
        self.business_address_var = tk.StringVar()
        ttk.Entry(entity_frame, textvariable=self.business_address_var, width=60).grid(row=2, column=1, columnspan=3, sticky="ew", pady=5)

        # Configure grid
        entity_frame.columnconfigure(1, weight=1)

        # Entity Type section
        type_frame = ttk.LabelFrame(parent, text="Entity Type", padding="10")
        type_frame.pack(fill="x", pady=(10, 10))

        # Entity type selection
        ttk.Label(type_frame, text="Entity Type:").grid(row=0, column=0, sticky="w", pady=5)
        self.entity_type_var = tk.StringVar(value="partnership")
        entity_combo = ttk.Combobox(
            type_frame,
            textvariable=self.entity_type_var,
            values=["partnership", "s_corporation", "llc_partnership", "llc_s_corp"],
            state="readonly"
        )
        entity_combo.grid(row=0, column=1, sticky="w", pady=5)
        entity_combo.bind('<<ComboboxSelected>>', self.on_entity_type_changed)

        # Partnership type (shown when partnership is selected)
        ttk.Label(type_frame, text="Partnership Type:").grid(row=1, column=0, sticky="w", pady=5)
        self.partnership_type_var = tk.StringVar()
        self.partnership_combo = ttk.Combobox(
            type_frame,
            textvariable=self.partnership_type_var,
            values=[t.value.replace('_', ' ').title() for t in PartnershipType],
            state="readonly"
        )
        self.partnership_combo.grid(row=1, column=1, sticky="w", pady=5)

        # S-Corp shareholder type (shown when s_corp is selected)
        ttk.Label(type_frame, text="Shareholder Type:").grid(row=2, column=0, sticky="w", pady=5)
        self.shareholder_type_var = tk.StringVar()
        self.shareholder_combo = ttk.Combobox(
            type_frame,
            textvariable=self.shareholder_type_var,
            values=[s.value.replace('_', ' ').title() for s in SCorpShareholderType],
            state="readonly"
        )
        self.shareholder_combo.grid(row=2, column=1, sticky="w", pady=5)

        # Initially hide both
        self.partnership_combo.grid_remove()
        self.shareholder_combo.grid_remove()

        # Business Activity section
        activity_frame = ttk.LabelFrame(parent, text="Business Activity", padding="10")
        activity_frame.pack(fill="x", pady=(10, 10))

        ttk.Label(activity_frame, text="Principal Business Activity:").grid(row=0, column=0, sticky="w", pady=5)
        self.business_activity_var = tk.StringVar()
        ttk.Entry(activity_frame, textvariable=self.business_activity_var, width=40).grid(row=0, column=1, sticky="ew", pady=5)

        ttk.Label(activity_frame, text="Activity Code:").grid(row=0, column=2, sticky="w", pady=5, padx=(20, 0))
        self.activity_code_var = tk.StringVar()
        ttk.Entry(activity_frame, textvariable=self.activity_code_var, width=10).grid(row=0, column=3, sticky="w", pady=5)

        ttk.Label(activity_frame, text="Accounting Method:").grid(row=1, column=0, sticky="w", pady=5)
        self.accounting_method_var = tk.StringVar(value="cash")
        method_combo = ttk.Combobox(
            activity_frame,
            textvariable=self.accounting_method_var,
            values=["cash", "accrual"],
            state="readonly"
        )
        method_combo.grid(row=1, column=1, sticky="w", pady=5)

        activity_frame.columnconfigure(1, weight=1)

        # Save button
        ttk.Button(
            activity_frame,
            text="Save Entity Info",
            command=self.save_entity_info
        ).grid(row=2, column=0, columnspan=4, pady=(20, 0))

    def build_income_tab(self, parent):
        """Build the income tab"""
        # Income sources section
        income_frame = ttk.LabelFrame(parent, text="Business Income Sources", padding="10")
        income_frame.pack(fill="x", pady=(0, 10))

        income_fields = [
            ("Gross Receipts/Sales:", "gross_receipts"),
            ("Returns & Allowances:", "returns_allowances"),
            ("Cost of Goods Sold:", "cost_of_goods_sold"),
            ("Dividends:", "dividends"),
            ("Interest Income:", "interest_income"),
            ("Rents:", "rents"),
            ("Royalties:", "royalties"),
            ("Other Income:", "other_income"),
        ]

        for i, (label, field) in enumerate(income_fields):
            ttk.Label(income_frame, text=label).grid(row=i, column=0, sticky="w", pady=2)
            self.income_vars[field] = tk.StringVar(value="0.00")
            ttk.Entry(income_frame, textvariable=self.income_vars[field], width=20).grid(row=i, column=1, sticky="w", pady=2)

        # Gross Profit display
        ttk.Label(income_frame, text="Gross Profit:").grid(row=len(income_fields), column=0, sticky="w", pady=(10, 2))
        self.gross_profit_var = tk.StringVar(value="$0.00")
        ttk.Label(income_frame, textvariable=self.gross_profit_var, font=("Arial", 10, "bold")).grid(row=len(income_fields), column=1, sticky="w", pady=(10, 2))

        # Total income display
        ttk.Label(income_frame, text="Total Income:").grid(row=len(income_fields)+1, column=0, sticky="w", pady=(10, 2))
        self.total_income_var = tk.StringVar(value="$0.00")
        ttk.Label(income_frame, textvariable=self.total_income_var, font=("Arial", 10, "bold")).grid(row=len(income_fields)+1, column=1, sticky="w", pady=(10, 2))

        # Calculate button
        ttk.Button(
            income_frame,
            text="Calculate Totals",
            command=self.calculate_income_totals
        ).grid(row=len(income_fields)+2, column=0, columnspan=2, pady=(10, 0))

    def build_deductions_tab(self, parent):
        """Build the deductions tab"""
        # Deductions section
        deductions_frame = ttk.LabelFrame(parent, text="Business Deductions", padding="10")
        deductions_frame.pack(fill="x", pady=(0, 10))

        deduction_fields = [
            ("Compensation of Officers:", "compensation_officers"),
            ("Salaries & Wages:", "salaries_wages"),
            ("Repairs & Maintenance:", "repairs_maintenance"),
            ("Bad Debts:", "bad_debts"),
            ("Rents:", "rents"),
            ("Taxes & Licenses:", "taxes_licenses"),
            ("Charitable Contributions:", "charitable_contributions"),
            ("Advertising:", "advertising"),
            ("Pension Plans:", "pension_plans"),
            ("Employee Benefits:", "employee_benefits"),
            ("Utilities:", "utilities"),
            ("Supplies:", "supplies"),
            ("Other Expenses:", "other_expenses"),
        ]

        for i, (label, field) in enumerate(deduction_fields):
            ttk.Label(deductions_frame, text=label).grid(row=i, column=0, sticky="w", pady=2)
            self.deduction_vars[field] = tk.StringVar(value="0.00")
            ttk.Entry(deductions_frame, textvariable=self.deduction_vars[field], width=20).grid(row=i, column=1, sticky="w", pady=2)

        # Total deductions display
        ttk.Label(deductions_frame, text="Total Deductions:").grid(row=len(deduction_fields), column=0, sticky="w", pady=(10, 2))
        self.total_deductions_var = tk.StringVar(value="$0.00")
        ttk.Label(deductions_frame, textvariable=self.total_deductions_var, font=("Arial", 10, "bold")).grid(row=len(deduction_fields), column=1, sticky="w", pady=(10, 2))

        # Calculate button
        ttk.Button(
            deductions_frame,
            text="Calculate Total",
            command=self.calculate_deductions_total
        ).grid(row=len(deduction_fields)+1, column=0, columnspan=2, pady=(10, 0))

    def build_partners_tab(self, parent):
        """Build the partners/shareholders tab"""
        # Partners/Shareholders section
        partners_frame = ttk.LabelFrame(parent, text="Partners/Shareholders", padding="10")
        partners_frame.pack(fill="both", expand=True)

        # Toolbar
        toolbar = ttk.Frame(partners_frame)
        toolbar.pack(fill="x", pady=(0, 10))

        ttk.Button(
            toolbar,
            text="Add Partner/Shareholder",
            command=self.add_partner_shareholder
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Edit Selected",
            command=self.edit_selected_partner
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Delete Selected",
            command=self.delete_selected_partner
        ).pack(side="left")

        ttk.Button(
            toolbar,
            text="Allocate Income",
            command=self.allocate_income
        ).pack(side="right")

        # Partners/Shareholders treeview
        tree_frame = ttk.Frame(partners_frame)
        tree_frame.pack(fill="both", expand=True)

        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal")

        self.partners_tree = ttk.Treeview(
            tree_frame,
            columns=("name", "ssn_ein", "entity_type", "ownership_pct", "income_share", "loss_share", "distributions"),
            show="headings",
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )

        # Configure columns
        self.partners_tree.heading("name", text="Name")
        self.partners_tree.heading("ssn_ein", text="SSN/EIN")
        self.partners_tree.heading("entity_type", text="Type")
        self.partners_tree.heading("ownership_pct", text="Ownership %")
        self.partners_tree.heading("income_share", text="Income Share")
        self.partners_tree.heading("loss_share", text="Loss Share")
        self.partners_tree.heading("distributions", text="Distributions")

        self.partners_tree.column("name", width=150)
        self.partners_tree.column("ssn_ein", width=100)
        self.partners_tree.column("entity_type", width=80)
        self.partners_tree.column("ownership_pct", width=80)
        self.partners_tree.column("income_share", width=100)
        self.partners_tree.column("loss_share", width=100)
        self.partners_tree.column("distributions", width=100)

        # Pack tree and scrollbars
        self.partners_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        v_scrollbar.config(command=self.partners_tree.yview)
        h_scrollbar.config(command=self.partners_tree.xview)

    def build_tax_tab(self, parent):
        """Build the tax calculation tab"""
        # Tax Calculation section
        tax_frame = ttk.LabelFrame(parent, text="Business Income Calculation", padding="10")
        tax_frame.pack(fill="x", pady=(0, 10))

        # Tax calculation results
        tax_items = [
            ("Gross Profit:", "gross_profit"),
            ("Total Income:", "total_income"),
            ("Total Deductions:", "total_deductions"),
            ("Net Income/Loss:", "net_income_loss"),
        ]

        self.tax_vars = {}
        for i, (label, key) in enumerate(tax_items):
            ttk.Label(tax_frame, text=label).grid(row=i, column=0, sticky="w", pady=2)
            self.tax_vars[key] = tk.StringVar(value="$0.00")
            ttk.Label(tax_frame, textvariable=self.tax_vars[key], font=("Arial", 10, "bold")).grid(row=i, column=1, sticky="w", pady=2)

        # Calculate button
        ttk.Button(
            tax_frame,
            text="Calculate Business Income",
            command=self.calculate_business_income
        ).grid(row=len(tax_items), column=0, columnspan=2, pady=(20, 0))

        # Allocation Results section
        alloc_frame = ttk.LabelFrame(parent, text="Income Allocation to Partners/Shareholders", padding="10")
        alloc_frame.pack(fill="x", pady=(10, 10))

        # Allocation treeview
        alloc_tree_frame = ttk.Frame(alloc_frame)
        alloc_tree_frame.pack(fill="both", expand=True)

        v_scrollbar = ttk.Scrollbar(alloc_tree_frame, orient="vertical")

        self.allocation_tree = ttk.Treeview(
            alloc_tree_frame,
            columns=("partner_name", "ownership_pct", "share_pct", "income_share", "loss_share"),
            show="headings",
            yscrollcommand=v_scrollbar.set,
            height=8
        )

        # Configure columns
        self.allocation_tree.heading("partner_name", text="Partner/Shareholder")
        self.allocation_tree.heading("ownership_pct", text="Ownership %")
        self.allocation_tree.heading("share_pct", text="Share %")
        self.allocation_tree.heading("income_share", text="Income Share")
        self.allocation_tree.heading("loss_share", text="Loss Share")

        self.allocation_tree.column("partner_name", width=150)
        self.allocation_tree.column("ownership_pct", width=80)
        self.allocation_tree.column("share_pct", width=80)
        self.allocation_tree.column("income_share", width=100)
        self.allocation_tree.column("loss_share", width=100)

        # Pack tree and scrollbar
        self.allocation_tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        v_scrollbar.config(command=self.allocation_tree.yview)

        # Instructions
        instructions_frame = ttk.LabelFrame(parent, text="Form Instructions", padding="10")
        instructions_frame.pack(fill="x", pady=(10, 0))

        instructions_text = tk.Text(instructions_frame, height=6, wrap="word")
        instructions_text.insert("1.0", self.ps_service.get_filing_instructions())
        instructions_text.config(state="disabled")
        instructions_text.pack(fill="both", expand=True)

    def create_new_return(self, entity_type: str):
        """Create a new partnership or S-Corp return"""
        try:
            tax_year = self.tax_data.get_current_year()

            if entity_type == "partnership":
                entity_type_enum = EntityType.PARTNERSHIP
            elif entity_type == "s_corp":
                entity_type_enum = EntityType.S_CORPORATION
            else:
                raise ValueError(f"Unknown entity type: {entity_type}")

            new_return = self.ps_service.create_partnership_s_corp_return(
                tax_year=tax_year,
                entity_type=entity_type_enum,
                entity_name="",
                ein=""
            )

            # Set as current return
            self.current_return = new_return

            # Update UI
            self.update_entity_fields()
            self.update_income_fields()
            self.update_deduction_fields()
            self.load_partners()

            messagebox.showinfo("Success", f"Created new {entity_type.replace('_', ' ').title()} return for tax year {tax_year}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create new return: {str(e)}")

    def edit_selected_return(self):
        """Edit the selected return"""
        selection = self.returns_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a return to edit.")
            return

        # For now, show placeholder
        messagebox.showinfo("Edit Return", "Edit functionality coming soon!")

    def delete_selected_return(self):
        """Delete the selected return"""
        selection = self.returns_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a return to delete.")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this return?"):
            # This would need to be implemented
            messagebox.showinfo("Delete Return", "Delete functionality coming soon!")

    def generate_forms(self):
        """Generate Form 1065/1120-S and K-1 forms"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please select or create a return first.")
            return

        try:
            if self.current_return.entity_type in [EntityType.PARTNERSHIP, EntityType.LLC_TAXED_AS_PARTNERSHIP]:
                form_data = self.ps_service.generate_form_1065(self.current_return)
                form_type = "1065"
            else:
                form_data = self.ps_service.generate_form_1120s(self.current_return)
                form_type = "1120-S"

            k1_forms = self.ps_service.generate_k1_forms(self.current_return)

            messagebox.showinfo("Forms Generated",
                f"Form {form_type} generated for {self.current_return.entity_name}\n"
                f"EIN: {self.current_return.ein}\n"
                f"Tax Year: {self.current_return.tax_year}\n\n"
                f"Generated {len(k1_forms)} K-1 forms for partners/shareholders")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate forms: {str(e)}")

    def on_return_selected(self, event):
        """Handle return selection"""
        selection = self.returns_tree.selection()
        if selection:
            # Load the selected return data
            # This would need to be implemented to load from the tree item
            pass

    def on_entity_type_changed(self, event):
        """Handle entity type change"""
        entity_type = self.entity_type_var.get()

        if entity_type in ["partnership", "llc_partnership"]:
            self.partnership_combo.grid()
            self.shareholder_combo.grid_remove()
        elif entity_type in ["s_corporation", "llc_s_corp"]:
            self.partnership_combo.grid_remove()
            self.shareholder_combo.grid()
        else:
            self.partnership_combo.grid_remove()
            self.shareholder_combo.grid_remove()

    def save_entity_info(self):
        """Save entity information"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please create a return first.")
            return

        try:
            # Update return data
            self.current_return.entity_name = self.entity_name_var.get()
            self.current_return.ein = self.ein_var.get()
            self.current_return.business_description = self.business_desc_var.get()
            self.current_return.business_address = self.business_address_var.get()
            self.current_return.principal_business_activity = self.business_activity_var.get()
            self.current_return.business_activity_code = self.activity_code_var.get()
            self.current_return.accounting_method = self.accounting_method_var.get()

            # Entity type specific
            entity_type_str = self.entity_type_var.get()
            if entity_type_str == "partnership":
                self.current_return.entity_type = EntityType.PARTNERSHIP
                self.current_return.partnership_type = PartnershipType(self.partnership_type_var.get().lower().replace(' ', '_')) if self.partnership_type_var.get() else None
                self.current_return.s_corp_shareholder_type = None
            elif entity_type_str == "s_corporation":
                self.current_return.entity_type = EntityType.S_CORPORATION
                self.current_return.s_corp_shareholder_type = SCorpShareholderType(self.shareholder_type_var.get().lower().replace(' ', '_')) if self.shareholder_type_var.get() else None
                self.current_return.partnership_type = None
            elif entity_type_str == "llc_partnership":
                self.current_return.entity_type = EntityType.LLC_TAXED_AS_PARTNERSHIP
                self.current_return.partnership_type = PartnershipType(self.partnership_type_var.get().lower().replace(' ', '_')) if self.partnership_type_var.get() else None
                self.current_return.s_corp_shareholder_type = None
            elif entity_type_str == "llc_s_corp":
                self.current_return.entity_type = EntityType.LLC_TAXED_AS_S_CORP
                self.current_return.s_corp_shareholder_type = SCorpShareholderType(self.shareholder_type_var.get().lower().replace(' ', '_')) if self.shareholder_type_var.get() else None
                self.current_return.partnership_type = None

            # Validate
            errors = self.ps_service.validate_partnership_s_corp_data(self.current_return)
            if errors:
                messagebox.showerror("Validation Errors", "\n".join(errors))
                return

            # Save
            if self.ps_service.save_partnership_s_corp_return(self.tax_data, self.current_return):
                self.load_returns()
                messagebox.showinfo("Success", "Entity information saved successfully!")
            else:
                messagebox.showerror("Save Failed", "Failed to save entity information.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save entity info: {str(e)}")

    def calculate_income_totals(self):
        """Calculate income totals"""
        try:
            # Update income data
            if self.current_return:
                self.current_return.income.gross_receipts = Decimal(self.income_vars['gross_receipts'].get() or "0")
                self.current_return.income.returns_allowances = Decimal(self.income_vars['returns_allowances'].get() or "0")
                self.current_return.income.cost_of_goods_sold = Decimal(self.income_vars['cost_of_goods_sold'].get() or "0")
                self.current_return.income.dividends = Decimal(self.income_vars['dividends'].get() or "0")
                self.current_return.income.interest_income = Decimal(self.income_vars['interest_income'].get() or "0")
                self.current_return.income.rents = Decimal(self.income_vars['rents'].get() or "0")
                self.current_return.income.royalties = Decimal(self.income_vars['royalties'].get() or "0")
                self.current_return.income.other_income = Decimal(self.income_vars['other_income'].get() or "0")

            # Calculate gross profit
            gross_profit = (
                self.current_return.income.gross_receipts -
                self.current_return.income.returns_allowances -
                self.current_return.income.cost_of_goods_sold
            )
            self.gross_profit_var.set(f"${gross_profit:,.2f}")

            # Calculate total income
            total_income = (
                gross_profit +
                self.current_return.income.dividends +
                self.current_return.income.interest_income +
                self.current_return.income.rents +
                self.current_return.income.royalties +
                self.current_return.income.other_income
            )
            self.total_income_var.set(f"${total_income:,.2f}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate income totals: {str(e)}")

    def calculate_deductions_total(self):
        """Calculate total deductions"""
        try:
            # Update deduction data
            if self.current_return:
                self.current_return.deductions.compensation_officers = Decimal(self.deduction_vars['compensation_officers'].get() or "0")
                self.current_return.deductions.salaries_wages = Decimal(self.deduction_vars['salaries_wages'].get() or "0")
                self.current_return.deductions.repairs_maintenance = Decimal(self.deduction_vars['repairs_maintenance'].get() or "0")
                self.current_return.deductions.bad_debts = Decimal(self.deduction_vars['bad_debts'].get() or "0")
                self.current_return.deductions.rents = Decimal(self.deduction_vars['rents'].get() or "0")
                self.current_return.deductions.taxes_licenses = Decimal(self.deduction_vars['taxes_licenses'].get() or "0")
                self.current_return.deductions.charitable_contributions = Decimal(self.deduction_vars['charitable_contributions'].get() or "0")
                self.current_return.deductions.advertising = Decimal(self.deduction_vars['advertising'].get() or "0")
                self.current_return.deductions.pension_plans = Decimal(self.deduction_vars['pension_plans'].get() or "0")
                self.current_return.deductions.employee_benefits = Decimal(self.deduction_vars['employee_benefits'].get() or "0")
                self.current_return.deductions.utilities = Decimal(self.deduction_vars['utilities'].get() or "0")
                self.current_return.deductions.supplies = Decimal(self.deduction_vars['supplies'].get() or "0")
                self.current_return.deductions.other_expenses = Decimal(self.deduction_vars['other_expenses'].get() or "0")

            total = self.current_return.deductions.total_deductions()
            self.total_deductions_var.set(f"${total:,.2f}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate deductions total: {str(e)}")

    def add_partner_shareholder(self):
        """Add a new partner/shareholder"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please create a return first.")
            return

        dialog = PartnerShareholderDialog(self, self.ps_service, self.current_return)
        if dialog.result:
            self.load_partners()

    def edit_selected_partner(self):
        """Edit the selected partner/shareholder"""
        selection = self.partners_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a partner/shareholder to edit.")
            return

        # For now, show placeholder
        messagebox.showinfo("Edit Partner", "Edit functionality coming soon!")

    def delete_selected_partner(self):
        """Delete the selected partner/shareholder"""
        selection = self.partners_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a partner/shareholder to delete.")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this partner/shareholder?"):
            # This would need to be implemented
            messagebox.showinfo("Delete Partner", "Delete functionality coming soon!")

    def allocate_income(self):
        """Allocate income to partners/shareholders"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please create a return first.")
            return

        try:
            # First calculate business income
            self.calculate_business_income()

            # Then allocate to partners
            allocations = self.ps_service.allocate_income_to_partners(self.current_return)

            # Update the allocation display
            self.display_allocations(allocations)

            messagebox.showinfo("Income Allocated", f"Income allocated to {len(allocations)} partners/shareholders")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to allocate income: {str(e)}")

    def calculate_business_income(self):
        """Calculate business income"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please create a return first.")
            return

        try:
            # Update income and deductions first
            self.calculate_income_totals()
            self.calculate_deductions_total()

            # Calculate business income
            net_income = self.ps_service.calculate_business_income(self.current_return)

            # Update display
            self.tax_vars['gross_profit'].set(f"${self.current_return.income.gross_profit:,.2f}")
            self.tax_vars['total_income'].set(f"${self.current_return.income.total_ordinary_income():,.2f}")
            self.tax_vars['total_deductions'].set(f"${self.current_return.deductions.total_deductions():,.2f}")
            self.tax_vars['net_income_loss'].set(f"${self.current_return.net_income_loss:,.2f}")

            messagebox.showinfo("Business Income Calculated", "Business income calculation completed successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate business income: {str(e)}")

    def display_allocations(self, allocations):
        """Display income allocations in the treeview"""
        # Clear existing items
        for item in self.allocation_tree.get_children():
            self.allocation_tree.delete(item)

        # Add allocations
        for alloc in allocations:
            self.allocation_tree.insert("", "end", values=(
                alloc['partner_name'],
                f"{alloc['ownership_percentage']:.1f}%",
                f"{alloc['share_percentage']:.3f}",
                f"${alloc['income_share']:,.2f}",
                f"${alloc['loss_share']:,.2f}",
            ))

    def load_returns(self):
        """Load all returns into the treeview"""
        try:
            # Clear existing items
            for item in self.returns_tree.get_children():
                self.returns_tree.delete(item)

            # Load returns
            returns = self.ps_service.load_partnership_s_corp_returns(self.tax_data)

            # Add to treeview
            for return_data in returns:
                entity_type_display = return_data.entity_type.value.replace('_', ' ').title()
                status = "Complete" if return_data.partners_shareholders else "Incomplete"
                self.returns_tree.insert("", "end", values=(
                    entity_type_display,
                    return_data.entity_name,
                    return_data.ein,
                    return_data.tax_year,
                    f"${return_data.net_income_loss:,.2f}",
                    len(return_data.partners_shareholders),
                    status
                ))

        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load returns: {str(e)}")

    def update_entity_fields(self):
        """Update entity information fields from current return"""
        if self.current_return:
            self.entity_name_var.set(self.current_return.entity_name)
            self.ein_var.set(self.current_return.ein)
            self.business_desc_var.set(self.current_return.business_description)
            self.business_address_var.set(self.current_return.business_address)
            self.business_activity_var.set(self.current_return.principal_business_activity)
            self.activity_code_var.set(self.current_return.business_activity_code)
            self.accounting_method_var.set(self.current_return.accounting_method)

            # Entity type
            if self.current_return.entity_type == EntityType.PARTNERSHIP:
                self.entity_type_var.set("partnership")
                if self.current_return.partnership_type:
                    self.partnership_type_var.set(self.current_return.partnership_type.value.replace('_', ' ').title())
            elif self.current_return.entity_type == EntityType.S_CORPORATION:
                self.entity_type_var.set("s_corporation")
                if self.current_return.s_corp_shareholder_type:
                    self.shareholder_type_var.set(self.current_return.s_corp_shareholder_type.value.replace('_', ' ').title())
            elif self.current_return.entity_type == EntityType.LLC_TAXED_AS_PARTNERSHIP:
                self.entity_type_var.set("llc_partnership")
                if self.current_return.partnership_type:
                    self.partnership_type_var.set(self.current_return.partnership_type.value.replace('_', ' ').title())
            elif self.current_return.entity_type == EntityType.LLC_TAXED_AS_S_CORP:
                self.entity_type_var.set("llc_s_corp")
                if self.current_return.s_corp_shareholder_type:
                    self.shareholder_type_var.set(self.current_return.s_corp_shareholder_type.value.replace('_', ' ').title())

    def update_income_fields(self):
        """Update income fields from current return"""
        if self.current_return:
            self.income_vars['gross_receipts'].set(str(self.current_return.income.gross_receipts))
            self.income_vars['returns_allowances'].set(str(self.current_return.income.returns_allowances))
            self.income_vars['cost_of_goods_sold'].set(str(self.current_return.income.cost_of_goods_sold))
            self.income_vars['dividends'].set(str(self.current_return.income.dividends))
            self.income_vars['interest_income'].set(str(self.current_return.income.interest_income))
            self.income_vars['rents'].set(str(self.current_return.income.rents))
            self.income_vars['royalties'].set(str(self.current_return.income.royalties))
            self.income_vars['other_income'].set(str(self.current_return.income.other_income))

            self.calculate_income_totals()

    def update_deduction_fields(self):
        """Update deduction fields from current return"""
        if self.current_return:
            self.deduction_vars['compensation_officers'].set(str(self.current_return.deductions.compensation_officers))
            self.deduction_vars['salaries_wages'].set(str(self.current_return.deductions.salaries_wages))
            self.deduction_vars['repairs_maintenance'].set(str(self.current_return.deductions.repairs_maintenance))
            self.deduction_vars['bad_debts'].set(str(self.current_return.deductions.bad_debts))
            self.deduction_vars['rents'].set(str(self.current_return.deductions.rents))
            self.deduction_vars['taxes_licenses'].set(str(self.current_return.deductions.taxes_licenses))
            self.deduction_vars['charitable_contributions'].set(str(self.current_return.deductions.charitable_contributions))
            self.deduction_vars['advertising'].set(str(self.current_return.deductions.advertising))
            self.deduction_vars['pension_plans'].set(str(self.current_return.deductions.pension_plans))
            self.deduction_vars['employee_benefits'].set(str(self.current_return.deductions.employee_benefits))
            self.deduction_vars['utilities'].set(str(self.current_return.deductions.utilities))
            self.deduction_vars['supplies'].set(str(self.current_return.deductions.supplies))
            self.deduction_vars['other_expenses'].set(str(self.current_return.deductions.other_expenses))

            self.calculate_deductions_total()

    def load_partners(self):
        """Load partners/shareholders into the treeview"""
        try:
            # Clear existing items
            for item in self.partners_tree.get_children():
                self.partners_tree.delete(item)

            if self.current_return:
                # Add partners/shareholders to treeview
                for partner in self.current_return.partners_shareholders:
                    self.partners_tree.insert("", "end", values=(
                        partner.name,
                        partner.ssn_ein,
                        partner.entity_type.title(),
                        f"{partner.ownership_percentage:.1f}%",
                        f"${partner.share_of_income:,.2f}",
                        f"${partner.share_of_losses:,.2f}",
                        f"${partner.distributions:,.2f}",
                    ))

        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load partners/shareholders: {str(e)}")

    def on_show(self):
        """Called when this page is shown"""
        self.load_returns()

    def validate_page(self) -> bool:
        """Validate the page data"""
        return True

    def save_data(self):
        """Save page data to tax data model"""
        if self.current_return:
            self.ps_service.save_partnership_s_corp_return(self.tax_data, self.current_return)

    def load_data_from_model(self):
        """Load data from tax data model"""
        self.load_returns()


class PartnerShareholderDialog:
    """Dialog for adding/editing partners/shareholders"""

    def __init__(self, parent, ps_service, return_data, edit_partner=None):
        self.parent = parent
        self.ps_service = ps_service
        self.return_data = return_data
        self.edit_partner = edit_partner
        self.result = None

        self.build_dialog()

    def build_dialog(self):
        """Build the partner/shareholder dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Add Partner/Shareholder")
        self.dialog.geometry("500x450")
        self.dialog.resizable(False, False)

        # Make dialog modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Form fields
        form_frame = ttk.Frame(self.dialog, padding="20")
        form_frame.pack(fill="both", expand=True)

        # Name
        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky="w", pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.name_var).grid(row=0, column=1, sticky="ew", pady=5)

        # SSN/EIN
        ttk.Label(form_frame, text="SSN/EIN:").grid(row=1, column=0, sticky="w", pady=5)
        self.ssn_ein_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.ssn_ein_var).grid(row=1, column=1, sticky="ew", pady=5)

        # Entity Type
        ttk.Label(form_frame, text="Entity Type:").grid(row=2, column=0, sticky="w", pady=5)
        self.entity_type_var = tk.StringVar(value="individual")
        entity_combo = ttk.Combobox(
            form_frame,
            textvariable=self.entity_type_var,
            values=["individual", "partnership", "corporation", "estate", "trust"],
            state="readonly"
        )
        entity_combo.grid(row=2, column=1, sticky="ew", pady=5)

        # Address
        ttk.Label(form_frame, text="Address:").grid(row=3, column=0, sticky="w", pady=5)
        self.address_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.address_var).grid(row=3, column=1, sticky="ew", pady=5)

        # Ownership Percentage
        ttk.Label(form_frame, text="Ownership Percentage:").grid(row=4, column=0, sticky="w", pady=5)
        self.ownership_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.ownership_var).grid(row=4, column=1, sticky="ew", pady=5)

        # Beginning Capital Account
        ttk.Label(form_frame, text="Beginning Capital:").grid(row=5, column=0, sticky="w", pady=5)
        self.beginning_capital_var = tk.StringVar(value="0.00")
        ttk.Entry(form_frame, textvariable=self.beginning_capital_var).grid(row=5, column=1, sticky="ew", pady=5)

        # Ending Capital Account
        ttk.Label(form_frame, text="Ending Capital:").grid(row=6, column=0, sticky="w", pady=5)
        self.ending_capital_var = tk.StringVar(value="0.00")
        ttk.Entry(form_frame, textvariable=self.ending_capital_var).grid(row=6, column=1, sticky="ew", pady=5)

        # Distributions
        ttk.Label(form_frame, text="Distributions:").grid(row=7, column=0, sticky="w", pady=5)
        self.distributions_var = tk.StringVar(value="0.00")
        ttk.Entry(form_frame, textvariable=self.distributions_var).grid(row=7, column=1, sticky="ew", pady=5)

        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=(20, 0))

        ttk.Button(
            button_frame,
            text="Save",
            command=self.save_partner
        ).pack(side="left", padx=(0, 10))

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy
        ).pack(side="left")

        # Configure grid
        form_frame.columnconfigure(1, weight=1)

    def save_partner(self):
        """Save the partner/shareholder"""
        try:
            # Validate inputs
            if not self.name_var.get().strip():
                messagebox.showerror("Validation Error", "Name is required.")
                return

            if not self.ssn_ein_var.get().strip():
                messagebox.showerror("Validation Error", "SSN/EIN is required.")
                return

            # Create partner/shareholder
            partner = PartnerShareholder(
                name=self.name_var.get().strip(),
                ssn_ein=self.ssn_ein_var.get().strip(),
                address=self.address_var.get().strip(),
                entity_type=self.entity_type_var.get(),
                ownership_percentage=Decimal(self.ownership_var.get() or "0"),
                capital_account_beginning=Decimal(self.beginning_capital_var.get() or "0"),
                capital_account_ending=Decimal(self.ending_capital_var.get() or "0"),
                distributions=Decimal(self.distributions_var.get() or "0"),
            )

            # Add to return
            self.return_data.partners_shareholders.append(partner)

            self.result = partner
            self.dialog.destroy()
            messagebox.showinfo("Success", "Partner/Shareholder added successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save partner/shareholder: {str(e)}")