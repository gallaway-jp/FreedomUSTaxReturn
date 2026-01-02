"""
Estate and Trust Tax Return Page

Page for preparing Form 1041 (U.S. Income Tax Return for Estates and Trusts).
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, List
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.estate_trust_service import (
    EstateTrustService,
    EstateTrustReturn,
    TrustType,
    EstateType,
    TrustBeneficiary,
    TrustIncome,
    TrustDeductions,
    IncomeDistributionType
)


class EstateTrustPage(ttk.Frame):
    """
    Page for estate and trust tax return preparation.

    Allows users to:
    - Create new estate/trust returns
    - Enter income and deduction data
    - Manage beneficiaries
    - Calculate taxes
    - Generate Form 1041
    """

    def __init__(self, parent, tax_data, main_window, theme_manager=None):
        super().__init__(parent)
        self.tax_data = tax_data
        self.main_window = main_window
        self.theme_manager = theme_manager
        self.config = main_window.config

        # Initialize service
        self.et_service = EstateTrustService(config)

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
            text="Estate and Trust Tax Returns (Form 1041)",
            font=("Arial", 16, "bold")
        )
        title_label.pack(anchor="w")

        description_label = ttk.Label(
            header_frame,
            text="Prepare U.S. Income Tax Returns for Estates and Trusts. Supports simple/complex trusts and estates.",
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

        # Beneficiaries tab
        beneficiaries_frame = ttk.Frame(notebook)
        notebook.add(beneficiaries_frame, text="Beneficiaries")

        self.build_beneficiaries_tab(beneficiaries_frame)

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
            text="New Estate Return",
            command=lambda: self.create_new_return("estate")
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            toolbar,
            text="New Trust Return",
            command=lambda: self.create_new_return("trust")
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
            text="Generate Form 1041",
            command=self.generate_form_1041
        ).pack(side="right")

        # Returns treeview
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill="both", expand=True)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal")

        self.returns_tree = ttk.Treeview(
            tree_frame,
            columns=("entity_type", "entity_name", "ein", "tax_year", "taxable_income", "tax_due", "status"),
            show="headings",
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )

        # Configure columns
        self.returns_tree.heading("entity_type", text="Type")
        self.returns_tree.heading("entity_name", text="Entity Name")
        self.returns_tree.heading("ein", text="EIN")
        self.returns_tree.heading("tax_year", text="Tax Year")
        self.returns_tree.heading("taxable_income", text="Taxable Income")
        self.returns_tree.heading("tax_due", text="Tax Due")
        self.returns_tree.heading("status", text="Status")

        self.returns_tree.column("entity_type", width=80)
        self.returns_tree.column("entity_name", width=200)
        self.returns_tree.column("ein", width=100)
        self.returns_tree.column("tax_year", width=80)
        self.returns_tree.column("taxable_income", width=120)
        self.returns_tree.column("tax_due", width=100)
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

        # Row 2: Fiduciary Information
        ttk.Label(entity_frame, text="Fiduciary Name:").grid(row=1, column=0, sticky="w", pady=5)
        self.fiduciary_name_var = tk.StringVar()
        ttk.Entry(entity_frame, textvariable=self.fiduciary_name_var, width=40).grid(row=1, column=1, sticky="ew", pady=5)

        ttk.Label(entity_frame, text="Phone:").grid(row=1, column=2, sticky="w", pady=5, padx=(20, 0))
        self.fiduciary_phone_var = tk.StringVar()
        ttk.Entry(entity_frame, textvariable=self.fiduciary_phone_var, width=15).grid(row=1, column=3, sticky="w", pady=5)

        # Row 3: Fiduciary Address
        ttk.Label(entity_frame, text="Fiduciary Address:").grid(row=2, column=0, sticky="w", pady=5)
        self.fiduciary_address_var = tk.StringVar()
        ttk.Entry(entity_frame, textvariable=self.fiduciary_address_var, width=60).grid(row=2, column=1, columnspan=3, sticky="ew", pady=5)

        # Configure grid
        entity_frame.columnconfigure(1, weight=1)

        # Entity Type section
        type_frame = ttk.LabelFrame(parent, text="Entity Type", padding="10")
        type_frame.pack(fill="x", pady=(10, 10))

        # Entity type selection
        ttk.Label(type_frame, text="Entity Type:").grid(row=0, column=0, sticky="w", pady=5)
        self.entity_type_var = tk.StringVar(value="trust")
        entity_combo = ttk.Combobox(
            type_frame,
            textvariable=self.entity_type_var,
            values=["trust", "estate"],
            state="readonly"
        )
        entity_combo.grid(row=0, column=1, sticky="w", pady=5)
        entity_combo.bind('<<ComboboxSelected>>', self.on_entity_type_changed)

        # Trust type (shown when trust is selected)
        ttk.Label(type_frame, text="Trust Type:").grid(row=1, column=0, sticky="w", pady=5)
        self.trust_type_var = tk.StringVar()
        self.trust_combo = ttk.Combobox(
            type_frame,
            textvariable=self.trust_type_var,
            values=[t.value.replace('_', ' ').title() for t in TrustType],
            state="readonly"
        )
        self.trust_combo.grid(row=1, column=1, sticky="w", pady=5)

        # Estate type (shown when estate is selected)
        ttk.Label(type_frame, text="Estate Type:").grid(row=2, column=0, sticky="w", pady=5)
        self.estate_type_var = tk.StringVar()
        self.estate_combo = ttk.Combobox(
            type_frame,
            textvariable=self.estate_type_var,
            values=[e.value.replace('_', ' ').title() for e in EstateType],
            state="readonly"
        )
        self.estate_combo.grid(row=2, column=1, sticky="w", pady=5)

        # Initially hide estate type
        self.estate_combo.grid_remove()

        # Save button
        ttk.Button(
            type_frame,
            text="Save Entity Info",
            command=self.save_entity_info
        ).grid(row=3, column=0, columnspan=2, pady=(20, 0))

    def build_income_tab(self, parent):
        """Build the income tab"""
        # Income sources section
        income_frame = ttk.LabelFrame(parent, text="Income Sources", padding="10")
        income_frame.pack(fill="x", pady=(0, 10))

        income_fields = [
            ("Interest Income:", "interest_income"),
            ("Dividend Income:", "dividend_income"),
            ("Business Income:", "business_income"),
            ("Capital Gains:", "capital_gains"),
            ("Rental Income:", "rental_income"),
            ("Royalty Income:", "royalty_income"),
            ("Other Income:", "other_income"),
        ]

        for i, (label, field) in enumerate(income_fields):
            ttk.Label(income_frame, text=label).grid(row=i, column=0, sticky="w", pady=2)
            self.income_vars[field] = tk.StringVar(value="0.00")
            ttk.Entry(income_frame, textvariable=self.income_vars[field], width=20).grid(row=i, column=1, sticky="w", pady=2)

        # Total income display
        ttk.Label(income_frame, text="Total Income:").grid(row=len(income_fields), column=0, sticky="w", pady=(10, 2))
        self.total_income_var = tk.StringVar(value="$0.00")
        ttk.Label(income_frame, textvariable=self.total_income_var, font=("Arial", 10, "bold")).grid(row=len(income_fields), column=1, sticky="w", pady=(10, 2))

        # Calculate button
        ttk.Button(
            income_frame,
            text="Calculate Total",
            command=self.calculate_income_total
        ).grid(row=len(income_fields)+1, column=0, columnspan=2, pady=(10, 0))

    def build_deductions_tab(self, parent):
        """Build the deductions tab"""
        # Deductions section
        deductions_frame = ttk.LabelFrame(parent, text="Deductions", padding="10")
        deductions_frame.pack(fill="x", pady=(0, 10))

        deduction_fields = [
            ("Fiduciary Fees:", "fiduciary_fees"),
            ("Attorney Fees:", "attorney_fees"),
            ("Accounting Fees:", "accounting_fees"),
            ("Other Administrative Expenses:", "other_administrative_expenses"),
            ("Charitable Contributions:", "charitable_contributions"),
            ("Net Operating Loss:", "net_operating_loss"),
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

    def build_beneficiaries_tab(self, parent):
        """Build the beneficiaries tab"""
        # Beneficiaries section
        beneficiaries_frame = ttk.LabelFrame(parent, text="Beneficiaries", padding="10")
        beneficiaries_frame.pack(fill="both", expand=True)

        # Toolbar
        toolbar = ttk.Frame(beneficiaries_frame)
        toolbar.pack(fill="x", pady=(0, 10))

        ttk.Button(
            toolbar,
            text="Add Beneficiary",
            command=self.add_beneficiary
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Edit Selected",
            command=self.edit_selected_beneficiary
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Delete Selected",
            command=self.delete_selected_beneficiary
        ).pack(side="left")

        # Beneficiaries treeview
        tree_frame = ttk.Frame(beneficiaries_frame)
        tree_frame.pack(fill="both", expand=True)

        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal")

        self.beneficiaries_tree = ttk.Treeview(
            tree_frame,
            columns=("name", "ssn", "relationship", "share_percentage", "income_distributed", "distribution_type"),
            show="headings",
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )

        # Configure columns
        self.beneficiaries_tree.heading("name", text="Name")
        self.beneficiaries_tree.heading("ssn", text="SSN")
        self.beneficiaries_tree.heading("relationship", text="Relationship")
        self.beneficiaries_tree.heading("share_percentage", text="Share %")
        self.beneficiaries_tree.heading("income_distributed", text="Income Distributed")
        self.beneficiaries_tree.heading("distribution_type", text="Distribution Type")

        self.beneficiaries_tree.column("name", width=150)
        self.beneficiaries_tree.column("ssn", width=100)
        self.beneficiaries_tree.column("relationship", width=100)
        self.beneficiaries_tree.column("share_percentage", width=80)
        self.beneficiaries_tree.column("income_distributed", width=120)
        self.beneficiaries_tree.column("distribution_type", width=120)

        # Pack tree and scrollbars
        self.beneficiaries_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        v_scrollbar.config(command=self.beneficiaries_tree.yview)
        h_scrollbar.config(command=self.beneficiaries_tree.xview)

    def build_tax_tab(self, parent):
        """Build the tax calculation tab"""
        # Tax Calculation section
        tax_frame = ttk.LabelFrame(parent, text="Tax Calculation", padding="10")
        tax_frame.pack(fill="x", pady=(0, 10))

        # Tax calculation results
        tax_items = [
            ("Total Income:", "total_income"),
            ("Total Deductions:", "total_deductions"),
            ("Taxable Income:", "taxable_income"),
            ("Tax Due:", "tax_due"),
            ("Payments & Credits:", "payments_credits"),
            ("Balance Due:", "balance_due"),
        ]

        self.tax_vars = {}
        for i, (label, key) in enumerate(tax_items):
            ttk.Label(tax_frame, text=label).grid(row=i, column=0, sticky="w", pady=2)
            self.tax_vars[key] = tk.StringVar(value="$0.00")
            ttk.Label(tax_frame, textvariable=self.tax_vars[key], font=("Arial", 10, "bold")).grid(row=i, column=1, sticky="w", pady=2)

        # Calculate tax button
        ttk.Button(
            tax_frame,
            text="Calculate Tax",
            command=self.calculate_tax
        ).grid(row=len(tax_items), column=0, columnspan=2, pady=(20, 0))

        # Instructions
        instructions_frame = ttk.LabelFrame(parent, text="Form 1041 Instructions", padding="10")
        instructions_frame.pack(fill="x", pady=(10, 0))

        instructions_text = tk.Text(instructions_frame, height=8, wrap="word")
        instructions_text.insert("1.0", self.et_service.get_filing_instructions())
        instructions_text.config(state="disabled")
        instructions_text.pack(fill="both", expand=True)

    def create_new_return(self, entity_type: str):
        """Create a new estate or trust return"""
        try:
            tax_year = self.tax_data.get_current_year()
            new_return = self.et_service.create_estate_trust_return(self.tax_data, entity_type, tax_year)

            # Set as current return
            self.current_return = new_return

            # Update UI
            self.update_entity_fields()
            self.update_income_fields()
            self.update_deduction_fields()
            self.load_beneficiaries()

            messagebox.showinfo("Success", f"Created new {entity_type} return for tax year {tax_year}")

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

    def generate_form_1041(self):
        """Generate Form 1041"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please select or create a return first.")
            return

        try:
            form_data = self.et_service.generate_form_1041(self.current_return)

            if form_data:
                messagebox.showinfo("Form 1041 Generated",
                    f"Form 1041 generated for {self.current_return.entity_name}\n"
                    f"EIN: {self.current_return.ein}\n"
                    f"Tax Year: {self.current_return.tax_year}")
            else:
                messagebox.showerror("Generation Failed", "Failed to generate Form 1041.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate form: {str(e)}")

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

        if entity_type == "trust":
            self.trust_combo.grid()
            self.estate_combo.grid_remove()
        else:  # estate
            self.trust_combo.grid_remove()
            self.estate_combo.grid()

    def save_entity_info(self):
        """Save entity information"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please create a return first.")
            return

        try:
            # Update return data
            self.current_return.entity_name = self.entity_name_var.get()
            self.current_return.ein = self.ein_var.get()
            self.current_return.fiduciary_name = self.fiduciary_name_var.get()
            self.current_return.fiduciary_address = self.fiduciary_address_var.get()
            self.current_return.fiduciary_phone = self.fiduciary_phone_var.get()

            # Entity type specific
            entity_type = self.entity_type_var.get()
            self.current_return.entity_type = entity_type

            if entity_type == "trust":
                trust_type_str = self.trust_type_var.get().lower().replace(' ', '_')
                self.current_return.trust_type = TrustType(trust_type_str) if trust_type_str else None
                self.current_return.estate_type = None
            else:
                estate_type_str = self.estate_type_var.get().lower().replace(' ', '_')
                self.current_return.estate_type = EstateType(estate_type_str) if estate_type_str else None
                self.current_return.trust_type = None

            # Validate
            errors = self.et_service.validate_estate_trust_data(self.current_return)
            if errors:
                messagebox.showerror("Validation Errors", "\n".join(errors))
                return

            # Save
            if self.et_service.save_estate_trust_return(self.tax_data, self.current_return):
                self.load_returns()
                messagebox.showinfo("Success", "Entity information saved successfully!")
            else:
                messagebox.showerror("Save Failed", "Failed to save entity information.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save entity info: {str(e)}")

    def calculate_income_total(self):
        """Calculate total income"""
        try:
            total = sum(Decimal(self.income_vars[field].get() or "0") for field in self.income_vars.keys())
            self.total_income_var.set(f"${total:,.2f}")

            if self.current_return:
                self.current_return.income.interest_income = Decimal(self.income_vars['interest_income'].get() or "0")
                self.current_return.income.dividend_income = Decimal(self.income_vars['dividend_income'].get() or "0")
                self.current_return.income.business_income = Decimal(self.income_vars['business_income'].get() or "0")
                self.current_return.income.capital_gains = Decimal(self.income_vars['capital_gains'].get() or "0")
                self.current_return.income.rental_income = Decimal(self.income_vars['rental_income'].get() or "0")
                self.current_return.income.royalty_income = Decimal(self.income_vars['royalty_income'].get() or "0")
                self.current_return.income.other_income = Decimal(self.income_vars['other_income'].get() or "0")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate income total: {str(e)}")

    def calculate_deductions_total(self):
        """Calculate total deductions"""
        try:
            total = sum(Decimal(self.deduction_vars[field].get() or "0") for field in self.deduction_vars.keys())
            self.total_deductions_var.set(f"${total:,.2f}")

            if self.current_return:
                self.current_return.deductions.fiduciary_fees = Decimal(self.deduction_vars['fiduciary_fees'].get() or "0")
                self.current_return.deductions.attorney_fees = Decimal(self.deduction_vars['attorney_fees'].get() or "0")
                self.current_return.deductions.accounting_fees = Decimal(self.deduction_vars['accounting_fees'].get() or "0")
                self.current_return.deductions.other_administrative_expenses = Decimal(self.deduction_vars['other_administrative_expenses'].get() or "0")
                self.current_return.deductions.charitable_contributions = Decimal(self.deduction_vars['charitable_contributions'].get() or "0")
                self.current_return.deductions.net_operating_loss = Decimal(self.deduction_vars['net_operating_loss'].get() or "0")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate deductions total: {str(e)}")

    def add_beneficiary(self):
        """Add a new beneficiary"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please create a return first.")
            return

        dialog = BeneficiaryDialog(self, self.et_service, self.current_return)
        if dialog.result:
            self.load_beneficiaries()

    def edit_selected_beneficiary(self):
        """Edit the selected beneficiary"""
        selection = self.beneficiaries_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a beneficiary to edit.")
            return

        # For now, show placeholder
        messagebox.showinfo("Edit Beneficiary", "Edit functionality coming soon!")

    def delete_selected_beneficiary(self):
        """Delete the selected beneficiary"""
        selection = self.beneficiaries_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a beneficiary to delete.")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this beneficiary?"):
            # This would need to be implemented
            messagebox.showinfo("Delete Beneficiary", "Delete functionality coming soon!")

    def calculate_tax(self):
        """Calculate tax for the current return"""
        if not self.current_return:
            messagebox.showwarning("No Return", "Please create a return first.")
            return

        try:
            # Update income and deductions first
            self.calculate_income_total()
            self.calculate_deductions_total()

            # Calculate tax
            result = self.et_service.calculate_tax(self.current_return)

            if result.get('success'):
                # Update display
                self.tax_vars['total_income'].set(f"${result['total_income']:,.2f}")
                self.tax_vars['total_deductions'].set(f"${result['total_deductions']:,.2f}")
                self.tax_vars['taxable_income'].set(f"${result['taxable_income']:,.2f}")
                self.tax_vars['tax_due'].set(f"${result['tax_due']:,.2f}")
                self.tax_vars['payments_credits'].set(f"${self.current_return.payments_credits:,.2f}")
                self.tax_vars['balance_due'].set(f"${result['balance_due']:,.2f}")

                messagebox.showinfo("Tax Calculated", "Tax calculation completed successfully!")
            else:
                messagebox.showerror("Calculation Failed", result.get('error', 'Unknown error'))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate tax: {str(e)}")

    def load_returns(self):
        """Load all returns into the treeview"""
        try:
            # Clear existing items
            for item in self.returns_tree.get_children():
                self.returns_tree.delete(item)

            # Load returns
            returns = self.et_service.load_estate_trust_returns(self.tax_data)

            # Add to treeview
            for return_data in returns:
                status = "Complete" if return_data.balance_due >= 0 else "Incomplete"
                self.returns_tree.insert("", "end", values=(
                    return_data.entity_type.title(),
                    return_data.entity_name,
                    return_data.ein,
                    return_data.tax_year,
                    f"${return_data.taxable_income:,.2f}",
                    f"${return_data.tax_due:,.2f}",
                    status
                ))

        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load returns: {str(e)}")

    def update_entity_fields(self):
        """Update entity information fields from current return"""
        if self.current_return:
            self.entity_name_var.set(self.current_return.entity_name)
            self.ein_var.set(self.current_return.ein)
            self.fiduciary_name_var.set(self.current_return.fiduciary_name)
            self.fiduciary_address_var.set(self.current_return.fiduciary_address)
            self.fiduciary_phone_var.set(self.current_return.fiduciary_phone)
            self.entity_type_var.set(self.current_return.entity_type)

            if self.current_return.trust_type:
                self.trust_type_var.set(self.current_return.trust_type.value.replace('_', ' ').title())
            if self.current_return.estate_type:
                self.estate_type_var.set(self.current_return.estate_type.value.replace('_', ' ').title())

    def update_income_fields(self):
        """Update income fields from current return"""
        if self.current_return:
            self.income_vars['interest_income'].set(str(self.current_return.income.interest_income))
            self.income_vars['dividend_income'].set(str(self.current_return.income.dividend_income))
            self.income_vars['business_income'].set(str(self.current_return.income.business_income))
            self.income_vars['capital_gains'].set(str(self.current_return.income.capital_gains))
            self.income_vars['rental_income'].set(str(self.current_return.income.rental_income))
            self.income_vars['royalty_income'].set(str(self.current_return.income.royalty_income))
            self.income_vars['other_income'].set(str(self.current_return.income.other_income))

            self.calculate_income_total()

    def update_deduction_fields(self):
        """Update deduction fields from current return"""
        if self.current_return:
            self.deduction_vars['fiduciary_fees'].set(str(self.current_return.deductions.fiduciary_fees))
            self.deduction_vars['attorney_fees'].set(str(self.current_return.deductions.attorney_fees))
            self.deduction_vars['accounting_fees'].set(str(self.current_return.deductions.accounting_fees))
            self.deduction_vars['other_administrative_expenses'].set(str(self.current_return.deductions.other_administrative_expenses))
            self.deduction_vars['charitable_contributions'].set(str(self.current_return.deductions.charitable_contributions))
            self.deduction_vars['net_operating_loss'].set(str(self.current_return.deductions.net_operating_loss))

            self.calculate_deductions_total()

    def load_beneficiaries(self):
        """Load beneficiaries into the treeview"""
        try:
            # Clear existing items
            for item in self.beneficiaries_tree.get_children():
                self.beneficiaries_tree.delete(item)

            if self.current_return:
                # Add beneficiaries to treeview
                for beneficiary in self.current_return.beneficiaries:
                    self.beneficiaries_tree.insert("", "end", values=(
                        beneficiary.name,
                        beneficiary.ssn,
                        beneficiary.relationship,
                        f"{beneficiary.share_percentage:.1f}%",
                        f"${beneficiary.income_distributed:,.2f}",
                        beneficiary.distribution_type.value.replace('_', ' ').title()
                    ))

        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load beneficiaries: {str(e)}")

    def on_show(self):
        """Called when this page is shown"""
        self.load_returns()

    def validate_page(self) -> bool:
        """Validate the page data"""
        return True

    def save_data(self):
        """Save page data to tax data model"""
        if self.current_return:
            self.et_service.save_estate_trust_return(self.tax_data, self.current_return)

    def load_data_from_model(self):
        """Load data from tax data model"""
        self.load_returns()


class BeneficiaryDialog:
    """Dialog for adding/editing beneficiaries"""

    def __init__(self, parent, et_service: EstateTrustService, return_data: EstateTrustReturn, edit_beneficiary=None):
        self.parent = parent
        self.et_service = et_service
        self.return_data = return_data
        self.edit_beneficiary = edit_beneficiary
        self.result = None

        self.build_dialog()

    def build_dialog(self):
        """Build the beneficiary dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Add Beneficiary")
        self.dialog.geometry("500x400")
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

        # SSN
        ttk.Label(form_frame, text="SSN:").grid(row=1, column=0, sticky="w", pady=5)
        self.ssn_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.ssn_var).grid(row=1, column=1, sticky="ew", pady=5)

        # Relationship
        ttk.Label(form_frame, text="Relationship:").grid(row=2, column=0, sticky="w", pady=5)
        self.relationship_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.relationship_var).grid(row=2, column=1, sticky="ew", pady=5)

        # Address
        ttk.Label(form_frame, text="Address:").grid(row=3, column=0, sticky="w", pady=5)
        self.address_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.address_var).grid(row=3, column=1, sticky="ew", pady=5)

        # Share Percentage
        ttk.Label(form_frame, text="Share Percentage:").grid(row=4, column=0, sticky="w", pady=5)
        self.share_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.share_var).grid(row=4, column=1, sticky="ew", pady=5)

        # Income Distributed
        ttk.Label(form_frame, text="Income Distributed:").grid(row=5, column=0, sticky="w", pady=5)
        self.income_var = tk.StringVar(value="0.00")
        ttk.Entry(form_frame, textvariable=self.income_var).grid(row=5, column=1, sticky="ew", pady=5)

        # Distribution Type
        ttk.Label(form_frame, text="Distribution Type:").grid(row=6, column=0, sticky="w", pady=5)
        self.distribution_var = tk.StringVar(value="ordinary_income")
        dist_combo = ttk.Combobox(
            form_frame,
            textvariable=self.distribution_var,
            values=[dt.value.replace('_', ' ').title() for dt in IncomeDistributionType],
            state="readonly"
        )
        dist_combo.grid(row=6, column=1, sticky="ew", pady=5)

        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=(20, 0))

        ttk.Button(
            button_frame,
            text="Save",
            command=self.save_beneficiary
        ).pack(side="left", padx=(0, 10))

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy
        ).pack(side="left")

        # Configure grid
        form_frame.columnconfigure(1, weight=1)

    def save_beneficiary(self):
        """Save the beneficiary"""
        try:
            # Validate inputs
            if not self.name_var.get().strip():
                messagebox.showerror("Validation Error", "Name is required.")
                return

            if not self.ssn_var.get().strip():
                messagebox.showerror("Validation Error", "SSN is required.")
                return

            # Create beneficiary
            beneficiary = TrustBeneficiary(
                name=self.name_var.get().strip(),
                ssn=self.ssn_var.get().strip(),
                address=self.address_var.get().strip(),
                relationship=self.relationship_var.get().strip(),
                share_percentage=Decimal(self.share_var.get() or "0"),
                income_distributed=Decimal(self.income_var.get() or "0"),
                distribution_type=IncomeDistributionType(self.distribution_var.get().lower().replace(' ', '_'))
            )

            # Add to return
            self.return_data.beneficiaries.append(beneficiary)

            self.result = beneficiary
            self.dialog.destroy()
            messagebox.showinfo("Success", "Beneficiary added successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save beneficiary: {str(e)}")