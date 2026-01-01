"""
Modern Credits Page - CustomTkinter-based tax credits form

Provides a modern interface for claiming various tax credits with
expandable sections, real-time calculations, and contextual help.
"""

import customtkinter as ctk
from typing import Optional, Dict, Any, List
import tkinter as tk

from config.app_config import AppConfig
from models.tax_data import TaxData
from gui.modern_ui_components import (
    ModernFrame, ModernLabel, ModernButton, ModernEntry,
    show_info_message, show_error_message, show_confirmation
)


class ModernCreditsPage(ModernFrame):
    """
    Modern tax credits page using CustomTkinter.

    Features:
    - Expandable credit sections with detailed information
    - Real-time validation and calculations
    - Contextual help for each credit type
    - Automatic eligibility checking
    - Modern UI with progressive disclosure
    """

    def __init__(self, master, config: AppConfig, tax_data: Optional[TaxData] = None,
                 on_complete=None, **kwargs):
        """
        Initialize the modern credits page.

        Args:
            master: Parent widget
            config: Application configuration
            tax_data: Tax data object (optional, can be loaded later)
            on_complete: Callback when form is completed
        """
        super().__init__(master, title="Tax Credits")
        self.config = config
        self.tax_data = tax_data
        self.on_complete = on_complete

        # UI components for credits
        self.num_children_entry: Optional[ModernEntry] = None
        self.claim_eic_var: Optional[tk.BooleanVar] = None
        self.claim_edu_var: Optional[tk.BooleanVar] = None
        self.retirement_entry: Optional[ModernEntry] = None
        self.care_expenses_entry: Optional[ModernEntry] = None
        self.energy_credit_entry: Optional[ModernEntry] = None
        self.premium_credit_entry: Optional[ModernEntry] = None

        # Build the form
        self._build_form()

        # Load data if available
        if self.tax_data:
            self.load_data(self.tax_data)

    def _build_form(self):
        """Build the credits form with modern UI components"""
        # Main scrollable frame
        scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Page header with description
        header_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        title_label = ModernLabel(
            header_frame,
            text="Claim Your Tax Credits",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(anchor="w", pady=(0, 5))

        desc_label = ModernLabel(
            header_frame,
            text="Tax credits reduce your tax liability dollar-for-dollar. Check all credits you may qualify for and enter the required information. Credits are more valuable than deductions!",
            font=ctk.CTkFont(size=11),
            wraplength=700,
            text_color="gray70"
        )
        desc_label.pack(anchor="w")

        # Credits sections
        self._build_child_tax_credit_section(scrollable_frame)
        self._build_earned_income_credit_section(scrollable_frame)
        self._build_education_credits_section(scrollable_frame)
        self._build_retirement_savings_section(scrollable_frame)
        self._build_child_care_credit_section(scrollable_frame)
        self._build_energy_credit_section(scrollable_frame)
        self._build_premium_tax_credit_section(scrollable_frame)

        # Navigation buttons
        self._build_navigation_buttons(scrollable_frame)

    def _build_child_tax_credit_section(self, parent):
        """Build the Child Tax Credit section"""
        credit_frame = ModernFrame(parent, title="Child Tax Credit")
        credit_frame.pack(fill="x", pady=(0, 15))

        # Description
        desc_label = ModernLabel(
            credit_frame,
            text="The Child Tax Credit provides up to $2,000 per qualifying child under age 17. This credit is partially refundable.",
            font=ctk.CTkFont(size=10),
            text_color="gray60",
            wraplength=600
        )
        desc_label.pack(anchor="w", pady=(10, 15))

        # Number of children input
        children_frame = ctk.CTkFrame(credit_frame, fg_color="transparent")
        children_frame.pack(fill="x", pady=(0, 10))

        ModernLabel(
            children_frame,
            text="Number of qualifying children:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(0, 15))

        self.num_children_entry = ModernEntry(
            children_frame,
            placeholder_text="Enter number (0-10)",
            width=120
        )
        self.num_children_entry.pack(side="left")

        # Credit amount display
        amount_frame = ctk.CTkFrame(credit_frame, fg_color="transparent")
        amount_frame.pack(fill="x", pady=(10, 0))

        ModernLabel(
            amount_frame,
            text="Estimated credit amount:",
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(0, 10))

        self.child_credit_label = ModernLabel(
            amount_frame,
            text="$0",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#2E8B57"
        )
        self.child_credit_label.pack(side="left")

        # Bind calculation
        if self.num_children_entry:
            self.num_children_entry.bind("<KeyRelease>", lambda e: self._calculate_child_credit())

    def _build_earned_income_credit_section(self, parent):
        """Build the Earned Income Credit section"""
        credit_frame = ModernFrame(parent, title="Earned Income Credit (EIC)")
        credit_frame.pack(fill="x", pady=(0, 15))

        # Description
        desc_label = ModernLabel(
            credit_frame,
            text="The Earned Income Credit is a refundable credit for low to moderate income workers. It can be worth up to $7,430 for families with 3 or more children in 2025.",
            font=ctk.CTkFont(size=10),
            text_color="gray60",
            wraplength=600
        )
        desc_label.pack(anchor="w", pady=(10, 15))

        # Checkbox for claiming
        self.claim_eic_var = tk.BooleanVar()

        eic_checkbox = ctk.CTkCheckBox(
            credit_frame,
            text="I want to claim the Earned Income Credit",
            variable=self.claim_eic_var,
            font=ctk.CTkFont(size=12)
        )
        eic_checkbox.pack(anchor="w", pady=(0, 10))

        # Additional info
        info_label = ModernLabel(
            credit_frame,
            text="Note: EIC eligibility depends on income, number of children, and filing status. The IRS will verify eligibility when processing your return.",
            font=ctk.CTkFont(size=9),
            text_color="gray50",
            wraplength=600
        )
        info_label.pack(anchor="w")

    def _build_education_credits_section(self, parent):
        """Build the Education Credits section"""
        credit_frame = ModernFrame(parent, title="Education Credits")
        credit_frame.pack(fill="x", pady=(0, 15))

        # Description
        desc_label = ModernLabel(
            credit_frame,
            text="American Opportunity Tax Credit (AOTC): Up to $2,500 per student for the first 4 years of higher education\nLifetime Learning Credit (LLC): Up to $2,000 per return for any level of higher education",
            font=ctk.CTkFont(size=10),
            text_color="gray60",
            wraplength=600
        )
        desc_label.pack(anchor="w", pady=(10, 15))

        # Checkbox for claiming
        self.claim_edu_var = tk.BooleanVar()

        edu_checkbox = ctk.CTkCheckBox(
            credit_frame,
            text="I paid qualified education expenses in 2025",
            variable=self.claim_edu_var,
            font=ctk.CTkFont(size=12)
        )
        edu_checkbox.pack(anchor="w", pady=(0, 10))

        # Additional info
        info_label = ModernLabel(
            credit_frame,
            text="Qualifying expenses include tuition, fees, books, and supplies. AOTC phases out for modified AGI over $80,000 (single) or $160,000 (joint).",
            font=ctk.CTkFont(size=9),
            text_color="gray50",
            wraplength=600
        )
        info_label.pack(anchor="w")

    def _build_retirement_savings_section(self, parent):
        """Build the Retirement Savings Credit section"""
        credit_frame = ModernFrame(parent, title="Retirement Savings Contributions Credit")
        credit_frame.pack(fill="x", pady=(0, 15))

        # Description
        desc_label = ModernLabel(
            credit_frame,
            text="Saver's Credit for contributions to IRAs, 401(k)s, and other retirement plans. Credit rate is 50%, 20%, or 10% depending on your income.",
            font=ctk.CTkFont(size=10),
            text_color="gray60",
            wraplength=600
        )
        desc_label.pack(anchor="w", pady=(10, 15))

        # Contribution amount input
        contrib_frame = ctk.CTkFrame(credit_frame, fg_color="transparent")
        contrib_frame.pack(fill="x", pady=(0, 10))

        ModernLabel(
            contrib_frame,
            text="Retirement plan contributions:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(0, 15))

        self.retirement_entry = ModernEntry(
            contrib_frame,
            placeholder_text="Enter amount (e.g., 2000.00)",
            width=150
        )
        self.retirement_entry.pack(side="left")

        # Credit amount display
        amount_frame = ctk.CTkFrame(credit_frame, fg_color="transparent")
        amount_frame.pack(fill="x", pady=(10, 0))

        ModernLabel(
            amount_frame,
            text="Estimated credit (20% rate):",
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(0, 10))

        self.retirement_credit_label = ModernLabel(
            amount_frame,
            text="$0",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#2E8B57"
        )
        self.retirement_credit_label.pack(side="left")

        # Bind calculation
        if self.retirement_entry:
            self.retirement_entry.bind("<KeyRelease>", lambda e: self._calculate_retirement_credit())

    def _build_child_care_credit_section(self, parent):
        """Build the Child and Dependent Care Credit section"""
        credit_frame = ModernFrame(parent, title="Child and Dependent Care Credit")
        credit_frame.pack(fill="x", pady=(0, 15))

        # Description
        desc_label = ModernLabel(
            credit_frame,
            text="Credit for expenses paid for care of children under 13 or dependents who are physically or mentally unable to care for themselves. Up to $3,000 for one child or $6,000 for two or more.",
            font=ctk.CTkFont(size=10),
            text_color="gray60",
            wraplength=600
        )
        desc_label.pack(anchor="w", pady=(10, 15))

        # Expenses input
        expense_frame = ctk.CTkFrame(credit_frame, fg_color="transparent")
        expense_frame.pack(fill="x", pady=(0, 10))

        ModernLabel(
            expense_frame,
            text="Qualified care expenses paid:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(0, 15))

        self.care_expenses_entry = ModernEntry(
            expense_frame,
            placeholder_text="Enter amount (max $6,000)",
            width=150
        )
        self.care_expenses_entry.pack(side="left")

        # Credit amount display
        amount_frame = ctk.CTkFrame(credit_frame, fg_color="transparent")
        amount_frame.pack(fill="x", pady=(10, 0))

        ModernLabel(
            amount_frame,
            text="Estimated credit (20% rate):",
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(0, 10))

        self.care_credit_label = ModernLabel(
            amount_frame,
            text="$0",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#2E8B57"
        )
        self.care_credit_label.pack(side="left")

        # Bind calculation
        if self.care_expenses_entry:
            self.care_expenses_entry.bind("<KeyRelease>", lambda e: self._calculate_care_credit())

    def _build_energy_credit_section(self, parent):
        """Build the Residential Energy Credit section"""
        credit_frame = ModernFrame(parent, title="Residential Energy Credit")
        credit_frame.pack(fill="x", pady=(0, 15))

        # Description
        desc_label = ModernLabel(
            credit_frame,
            text="Credit for energy-efficient improvements to your home including solar panels, energy-efficient windows, electrical panel upgrades, electrical wiring, and electrical outlets.",
            font=ctk.CTkFont(size=10),
            text_color="gray60",
            wraplength=600
        )
        desc_label.pack(anchor="w", pady=(10, 15))

        # Credit amount input
        credit_frame_inner = ctk.CTkFrame(credit_frame, fg_color="transparent")
        credit_frame_inner.pack(fill="x")

        ModernLabel(
            credit_frame_inner,
            text="Energy credit amount:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(0, 15))

        self.energy_credit_entry = ModernEntry(
            credit_frame_inner,
            placeholder_text="Enter credit amount",
            width=150
        )
        self.energy_credit_entry.pack(side="left")

    def _build_premium_tax_credit_section(self, parent):
        """Build the Premium Tax Credit section"""
        credit_frame = ModernFrame(parent, title="Premium Tax Credit (ACA)")
        credit_frame.pack(fill="x", pady=(0, 15))

        # Description
        desc_label = ModernLabel(
            credit_frame,
            text="Credit for health insurance premiums purchased through the Health Insurance Marketplace. This credit helps make health insurance more affordable.",
            font=ctk.CTkFont(size=10),
            text_color="gray60",
            wraplength=600
        )
        desc_label.pack(anchor="w", pady=(10, 15))

        # Credit amount input
        credit_frame_inner = ctk.CTkFrame(credit_frame, fg_color="transparent")
        credit_frame_inner.pack(fill="x")

        ModernLabel(
            credit_frame_inner,
            text="Premium tax credit amount:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(0, 15))

        self.premium_credit_entry = ModernEntry(
            credit_frame_inner,
            placeholder_text="Enter credit amount",
            width=150
        )
        self.premium_credit_entry.pack(side="left")

    def _build_navigation_buttons(self, parent):
        """Build navigation buttons"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent", height=50)
        button_frame.pack(fill="x", pady=(30, 10))

        # Back button
        back_button = ModernButton(
            button_frame,
            text="← Back to Deductions",
            command=self._go_back,
            button_type="secondary",
            width=180
        )
        back_button.pack(side="left")

        # Save and continue button
        continue_button = ModernButton(
            button_frame,
            text="Save and Continue →",
            command=self._save_and_continue,
            button_type="primary",
            width=180
        )
        continue_button.pack(side="right")

    def _calculate_child_credit(self):
        """Calculate Child Tax Credit amount"""
        if not self.num_children_entry or not self.child_credit_label:
            return

        try:
            num_children = int(self.num_children_entry.get().strip() or 0)
            credit_amount = min(num_children, 10) * 2000  # Max 10 children for display
            self.child_credit_label.configure(text=f"${credit_amount:,}")
        except ValueError:
            self.child_credit_label.configure(text="$0")

    def _calculate_retirement_credit(self):
        """Calculate Retirement Savings Credit amount"""
        if not self.retirement_entry or not self.retirement_credit_label:
            return

        try:
            contribution = float(self.retirement_entry.get().replace(",", "").replace("$", "") or 0)
            # Using 20% rate as default estimate
            credit_amount = contribution * 0.20
            self.retirement_credit_label.configure(text=f"${credit_amount:,.0f}")
        except ValueError:
            self.retirement_credit_label.configure(text="$0")

    def _calculate_care_credit(self):
        """Calculate Child and Dependent Care Credit amount"""
        if not self.care_expenses_entry or not self.care_credit_label:
            return

        try:
            expenses = float(self.care_expenses_entry.get().replace(",", "").replace("$", "") or 0)
            # Using 20% rate as default estimate, max $3,000 for one child
            credit_amount = min(expenses * 0.20, 3000)
            self.care_credit_label.configure(text=f"${credit_amount:,.0f}")
        except ValueError:
            self.care_credit_label.configure(text="$0")

    def _go_back(self):
        """Go back to the previous page"""
        if self.on_complete:
            self.on_complete(self.tax_data, action="back")
        else:
            # This will be handled by the parent window
            if hasattr(self.master, 'show_deductions_page'):
                self.master.show_deductions_page()
            else:
                show_info_message("Navigation", "Back navigation will be implemented by the parent window.")

    def _save_and_continue(self):
        """Save data and continue to next page"""
        if not self._validate_and_save():
            return

        if self.on_complete:
            self.on_complete(self.tax_data, action="continue")
        else:
            # This will be handled by the parent window
            show_info_message("Navigation", "Credits completed. Payments page will be implemented next.")

    def _validate_and_save(self) -> bool:
        """Validate input and save data to tax_data"""
        if not self.tax_data:
            show_error_message("Error", "No tax data available to save.")
            return False

        try:
            # Save Child Tax Credit
            if self.num_children_entry:
                num_children = int(self.num_children_entry.get().strip() or 0)
                children_list = []
                for i in range(num_children):
                    children_list.append({"name": f"Child {i+1}", "qualifying": True})
                self.tax_data.set("credits.child_tax_credit.qualifying_children", children_list)

            # Save Earned Income Credit
            if self.claim_eic_var:
                if self.claim_eic_var.get():
                    # Use the same children list for EIC
                    children_list = self.tax_data.get("credits.child_tax_credit.qualifying_children", [])
                    self.tax_data.set("credits.earned_income_credit.qualifying_children", children_list)
                else:
                    self.tax_data.set("credits.earned_income_credit.qualifying_children", [])

            # Save Education Credits
            if self.claim_edu_var:
                if self.claim_edu_var.get():
                    # Set a placeholder - actual calculation will be done later
                    self.tax_data.set("credits.education_credits.claiming", True)
                else:
                    self.tax_data.set("credits.education_credits.claiming", False)

            # Save Retirement Savings Credit
            if self.retirement_entry:
                value = self.retirement_entry.get().strip()
                amount = float(value.replace(",", "").replace("$", "")) if value else 0.0
                self.tax_data.set("credits.retirement_savings_credit", amount)

            # Save Child and Dependent Care Credit
            if self.care_expenses_entry:
                value = self.care_expenses_entry.get().strip()
                amount = float(value.replace(",", "").replace("$", "")) if value else 0.0
                self.tax_data.set("credits.child_dependent_care.expenses", amount)

            # Save Residential Energy Credit
            if self.energy_credit_entry:
                value = self.energy_credit_entry.get().strip()
                amount = float(value.replace(",", "").replace("$", "")) if value else 0.0
                self.tax_data.set("credits.residential_energy.amount", amount)

            # Save Premium Tax Credit
            if self.premium_credit_entry:
                value = self.premium_credit_entry.get().strip()
                amount = float(value.replace(",", "").replace("$", "")) if value else 0.0
                self.tax_data.set("credits.premium_tax_credit.amount", amount)

            show_info_message("Success", "Tax credits saved successfully!")
            return True

        except ValueError as e:
            show_error_message("Validation Error", f"Please enter valid numbers for all credit amounts.\n\nError: {str(e)}")
            return False

    def load_data(self, tax_data: TaxData):
        """Load data from tax_data object"""
        self.tax_data = tax_data

        # Load Child Tax Credit
        if self.num_children_entry:
            children_list = tax_data.get("credits.child_tax_credit.qualifying_children", [])
            self.num_children_entry.delete(0, "end")
            self.num_children_entry.insert(0, str(len(children_list)))

        # Load Earned Income Credit
        if self.claim_eic_var:
            eic_children = tax_data.get("credits.earned_income_credit.qualifying_children", [])
            self.claim_eic_var.set(len(eic_children) > 0)

        # Load Education Credits
        if self.claim_edu_var:
            claiming_edu = tax_data.get("credits.education_credits.claiming", False)
            self.claim_edu_var.set(claiming_edu)

        # Load Retirement Savings Credit
        if self.retirement_entry:
            amount = tax_data.get("credits.retirement_savings_credit", 0)
            self.retirement_entry.delete(0, "end")
            self.retirement_entry.insert(0, str(amount))

        # Load Child and Dependent Care Credit
        if self.care_expenses_entry:
            amount = tax_data.get("credits.child_dependent_care.expenses", 0)
            self.care_expenses_entry.delete(0, "end")
            self.care_expenses_entry.insert(0, str(amount))

        # Load Residential Energy Credit
        if self.energy_credit_entry:
            amount = tax_data.get("credits.residential_energy.amount", 0)
            self.energy_credit_entry.delete(0, "end")
            self.energy_credit_entry.insert(0, str(amount))

        # Load Premium Tax Credit
        if self.premium_credit_entry:
            amount = tax_data.get("credits.premium_tax_credit.amount", 0)
            self.premium_credit_entry.delete(0, "end")
            self.premium_credit_entry.insert(0, str(amount))

        # Update calculations
        self._calculate_child_credit()
        self._calculate_retirement_credit()
        self._calculate_care_credit()

    def get_data(self) -> Dict[str, Any]:
        """Get current form data"""
        data = {
            "child_tax_credit": {
                "qualifying_children": int(self.num_children_entry.get() or 0) if self.num_children_entry else 0
            },
            "earned_income_credit": {
                "claiming": self.claim_eic_var.get() if self.claim_eic_var else False
            },
            "education_credits": {
                "claiming": self.claim_edu_var.get() if self.claim_edu_var else False
            },
            "retirement_savings_credit": float(self.retirement_entry.get().replace(",", "").replace("$", "") or 0) if self.retirement_entry else 0,
            "child_dependent_care": {
                "expenses": float(self.care_expenses_entry.get().replace(",", "").replace("$", "") or 0) if self.care_expenses_entry else 0
            },
            "residential_energy": {
                "amount": float(self.energy_credit_entry.get().replace(",", "").replace("$", "") or 0) if self.energy_credit_entry else 0
            },
            "premium_tax_credit": {
                "amount": float(self.premium_credit_entry.get().replace(",", "").replace("$", "") or 0) if self.premium_credit_entry else 0
            }
        }
        return data