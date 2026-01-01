"""
Modern Deductions Page - CustomTkinter-based deductions form

Provides a modern interface for selecting between standard and itemized deductions
with real-time calculations and contextual help.
"""

import customtkinter as ctk
from typing import Optional, Dict, Any
import tkinter as tk

from config.app_config import AppConfig
from models.tax_data import TaxData
from gui.modern_ui_components import (
    ModernFrame, ModernLabel, ModernButton, ModernEntry,
    show_info_message, show_error_message, show_confirmation
)


class ModernDeductionsPage(ModernFrame):
    """
    Modern deductions page using CustomTkinter.

    Features:
    - Clean deduction method selection (standard vs itemized)
    - Real-time standard deduction calculation based on filing status
    - Expandable itemized deductions section
    - Automatic total calculations
    - Contextual help and validation
    - Modern UI with progressive disclosure
    """

    def __init__(self, master, config: AppConfig, tax_data: Optional[TaxData] = None,
                 on_complete=None, **kwargs):
        """
        Initialize the modern deductions page.

        Args:
            master: Parent widget
            config: Application configuration
            tax_data: Tax data object (optional, can be loaded later)
            on_complete: Callback when form is completed
        """
        super().__init__(master, **kwargs)
        self.config = config
        self.tax_data = tax_data
        self.on_complete = on_complete

        # UI components
        self.method_var: Optional[tk.StringVar] = None
        self.itemized_frame: Optional[ModernFrame] = None

        # Form fields for itemized deductions
        self.medical_entry: Optional[ModernEntry] = None
        self.taxes_entry: Optional[ModernEntry] = None
        self.mortgage_entry: Optional[ModernEntry] = None
        self.charitable_entry: Optional[ModernEntry] = None

        # Display labels
        self.standard_amount_label: Optional[ModernLabel] = None
        self.total_label: Optional[ModernLabel] = None

        # Build the form
        self._build_form()

        # Load data if available
        if self.tax_data:
            self.load_data(self.tax_data)

    def _build_form(self):
        """Build the deductions form with modern UI components"""
        # Main scrollable frame
        scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Page header with description
        header_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        title_label = ModernLabel(
            header_frame,
            text="Choose Your Deduction Method",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(anchor="w", pady=(0, 5))

        desc_label = ModernLabel(
            header_frame,
            text="Select whether to use the standard deduction (recommended for most taxpayers) or itemize your deductions. The standard deduction is a fixed amount that reduces your taxable income.",
            font=ctk.CTkFont(size=11),
            wraplength=700,
            text_color="gray70"
        )
        desc_label.pack(anchor="w")

        # Deduction method selection
        self._build_deduction_method_section(scrollable_frame)

        # Itemized deductions section (initially hidden)
        self._build_itemized_deductions_section(scrollable_frame)

        # Navigation buttons
        self._build_navigation_buttons(scrollable_frame)

    def _build_deduction_method_section(self, parent):
        """Build the deduction method selection section"""
        method_frame = ModernFrame(parent, title="Deduction Method")
        method_frame.pack(fill="x", pady=(0, 20))

        # Radio button selection
        self.method_var = tk.StringVar(value="standard")

        # Standard deduction option
        std_frame = ctk.CTkFrame(method_frame, fg_color="transparent")
        std_frame.pack(fill="x", pady=(10, 5))

        std_radio = ctk.CTkRadioButton(
            std_frame,
            text="Standard Deduction",
            variable=self.method_var,
            value="standard",
            command=self._on_method_change,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        std_radio.pack(anchor="w", pady=(0, 5))

        # Standard deduction description
        std_desc = ModernLabel(
            std_frame,
            text="Use the standard deduction amount set by the IRS. This is the recommended choice for most taxpayers as it's simple and often provides the best deduction.",
            font=ctk.CTkFont(size=10),
            text_color="gray60",
            wraplength=600
        )
        std_desc.pack(anchor="w", padx=25, pady=(0, 5))

        # Standard deduction amount display
        amount_frame = ctk.CTkFrame(std_frame, fg_color="transparent")
        amount_frame.pack(anchor="w", padx=25)

        ModernLabel(
            amount_frame,
            text="Your standard deduction amount:",
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(0, 10))

        self.standard_amount_label = ModernLabel(
            amount_frame,
            text="$14,600",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#2E8B57"  # Sea green
        )
        self.standard_amount_label.pack(side="left")

        # Itemized deduction option
        itemized_frame = ctk.CTkFrame(method_frame, fg_color="transparent")
        itemized_frame.pack(fill="x", pady=(15, 10))

        itemized_radio = ctk.CTkRadioButton(
            itemized_frame,
            text="Itemized Deductions",
            variable=self.method_var,
            value="itemized",
            command=self._on_method_change,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        itemized_radio.pack(anchor="w", pady=(0, 5))

        # Itemized deduction description
        itemized_desc = ModernLabel(
            itemized_frame,
            text="List and total your actual deductions. Choose this option if your itemized deductions exceed the standard deduction amount.",
            font=ctk.CTkFont(size=10),
            text_color="gray60",
            wraplength=600
        )
        itemized_desc.pack(anchor="w", padx=25)

    def _build_itemized_deductions_section(self, parent):
        """Build the itemized deductions section"""
        self.itemized_frame = ModernFrame(parent, title="Itemized Deductions")
        # Initially hidden - will be shown when itemized is selected

        # Medical expenses
        medical_frame = ctk.CTkFrame(self.itemized_frame, fg_color="transparent")
        medical_frame.pack(fill="x", pady=(10, 5))

        ModernLabel(
            medical_frame,
            text="Medical and Dental Expenses",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w", pady=(0, 2))

        ModernLabel(
            medical_frame,
            text="Expenses that exceed 7.5% of your adjusted gross income (AGI)",
            font=ctk.CTkFont(size=9),
            text_color="gray60"
        ).pack(anchor="w", pady=(0, 5))

        self.medical_entry = ModernEntry(
            medical_frame,
            placeholder_text="Enter amount (e.g., 5000.00)",
            width=200
        )
        self.medical_entry.pack(anchor="w")

        # State and local taxes
        taxes_frame = ctk.CTkFrame(self.itemized_frame, fg_color="transparent")
        taxes_frame.pack(fill="x", pady=(15, 5))

        ModernLabel(
            taxes_frame,
            text="State and Local Taxes",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w", pady=(0, 2))

        ModernLabel(
            taxes_frame,
            text="State income tax, property tax, and general sales tax (maximum $10,000)",
            font=ctk.CTkFont(size=9),
            text_color="gray60"
        ).pack(anchor="w", pady=(0, 5))

        self.taxes_entry = ModernEntry(
            taxes_frame,
            placeholder_text="Enter amount (max $10,000)",
            width=200
        )
        self.taxes_entry.pack(anchor="w")

        # Mortgage interest
        mortgage_frame = ctk.CTkFrame(self.itemized_frame, fg_color="transparent")
        mortgage_frame.pack(fill="x", pady=(15, 5))

        ModernLabel(
            mortgage_frame,
            text="Mortgage Interest",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w", pady=(0, 2))

        ModernLabel(
            mortgage_frame,
            text="Interest paid on qualified home mortgages",
            font=ctk.CTkFont(size=9),
            text_color="gray60"
        ).pack(anchor="w", pady=(0, 5))

        self.mortgage_entry = ModernEntry(
            mortgage_frame,
            placeholder_text="Enter amount",
            width=200
        )
        self.mortgage_entry.pack(anchor="w")

        # Charitable contributions
        charitable_frame = ctk.CTkFrame(self.itemized_frame, fg_color="transparent")
        charitable_frame.pack(fill="x", pady=(15, 5))

        ModernLabel(
            charitable_frame,
            text="Charitable Contributions",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w", pady=(0, 2))

        ModernLabel(
            charitable_frame,
            text="Cash and non-cash donations to qualified organizations",
            font=ctk.CTkFont(size=9),
            text_color="gray60"
        ).pack(anchor="w", pady=(0, 5))

        self.charitable_entry = ModernEntry(
            charitable_frame,
            placeholder_text="Enter amount",
            width=200
        )
        self.charitable_entry.pack(anchor="w")

        # Total calculation section
        total_frame = ctk.CTkFrame(self.itemized_frame, fg_color="transparent")
        total_frame.pack(fill="x", pady=(20, 10))

        # Total display
        total_display_frame = ctk.CTkFrame(total_frame, fg_color="transparent")
        total_display_frame.pack(fill="x", pady=(0, 10))

        ModernLabel(
            total_display_frame,
            text="Total Itemized Deductions:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")

        self.total_label = ModernLabel(
            total_display_frame,
            text="$0.00",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#2E8B57"
        )
        self.total_label.pack(side="right")

        # Calculate button
        calc_button = ModernButton(
            total_frame,
            text="Calculate Total",
            command=self._calculate_itemized_total,
            button_type="secondary",
            height=35
        )
        calc_button.pack(fill="x", pady=(10, 0))

        # Bind real-time calculation to entry changes
        for entry in [self.medical_entry, self.taxes_entry, self.mortgage_entry, self.charitable_entry]:
            if entry:
                entry.bind("<KeyRelease>", lambda e: self._calculate_itemized_total())

    def _build_navigation_buttons(self, parent):
        """Build navigation buttons"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent", height=50)
        button_frame.pack(fill="x", pady=(30, 10))

        # Back button
        back_button = ModernButton(
            button_frame,
            text="← Back to Income",
            command=self._go_back,
            button_type="secondary",
            width=150
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

    def _on_method_change(self):
        """Handle deduction method change"""
        if self.method_var and self.method_var.get() == "standard":
            if self.itemized_frame:
                self.itemized_frame.pack_forget()
        else:
            if self.itemized_frame:
                self.itemized_frame.pack(fill="x", pady=(0, 20))

        self._update_standard_deduction_display()

    def _update_standard_deduction_display(self):
        """Update the standard deduction amount display"""
        if not self.tax_data or not self.standard_amount_label:
            return

        filing_status = self.tax_data.get("filing_status.status", "Single")

        # 2025 standard deduction amounts
        standard_amounts = {
            "Single": 14600,
            "MFJ": 29200,
            "MFS": 14600,
            "HOH": 21900,
            "QW": 29200,
        }

        amount = standard_amounts.get(filing_status, 14600)
        self.standard_amount_label.configure(text=f"${amount:,}")

    def _calculate_itemized_total(self, event=None):
        """Calculate total itemized deductions"""
        if not self.total_label:
            return

        try:
            total = 0.0

            # Get values from entries
            entries = [self.medical_entry, self.taxes_entry, self.mortgage_entry, self.charitable_entry]
            for entry in entries:
                if entry:
                    value = entry.get().strip()
                    if value:
                        # Remove commas and dollar signs for parsing
                        clean_value = value.replace(",", "").replace("$", "")
                        total += float(clean_value)

            self.total_label.configure(text=f"${total:,.2f}")

        except ValueError:
            self.total_label.configure(text="Error: Invalid input")

    def _go_back(self):
        """Go back to the previous page"""
        if self.on_complete:
            self.on_complete(self.tax_data, action="back")
        else:
            # This will be handled by the parent window
            if hasattr(self.master, 'show_income_page'):
                self.master.show_income_page()
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
            if hasattr(self.master, 'show_credits_page'):
                self.master.show_credits_page()
            else:
                show_info_message("Navigation", "Continue navigation will be implemented by the parent window.")

    def _validate_and_save(self) -> bool:
        """Validate input and save data to tax_data"""
        if not self.tax_data:
            show_error_message("Error", "No tax data available to save.")
            return False

        try:
            # Save deduction method
            if self.method_var:
                self.tax_data.set("deductions.method", self.method_var.get())

            # Save itemized deductions if selected
            if self.method_var and self.method_var.get() == "itemized":
                itemized_data = {}

                # Medical expenses
                if self.medical_entry:
                    value = self.medical_entry.get().strip()
                    itemized_data["medical_expenses"] = float(value.replace(",", "").replace("$", "")) if value else 0.0

                # State and local taxes
                if self.taxes_entry:
                    value = self.taxes_entry.get().strip()
                    tax_amount = float(value.replace(",", "").replace("$", "")) if value else 0.0
                    if tax_amount > 10000:
                        show_error_message("Validation Error", "State and local taxes cannot exceed $10,000.")
                        return False
                    itemized_data["state_local_taxes"] = tax_amount

                # Mortgage interest
                if self.mortgage_entry:
                    value = self.mortgage_entry.get().strip()
                    itemized_data["mortgage_interest"] = float(value.replace(",", "").replace("$", "")) if value else 0.0

                # Charitable contributions
                if self.charitable_entry:
                    value = self.charitable_entry.get().strip()
                    itemized_data["charitable_contributions"] = float(value.replace(",", "").replace("$", "")) if value else 0.0

                # Save all itemized data
                for key, value in itemized_data.items():
                    self.tax_data.set(f"deductions.{key}", value)

            show_info_message("Success", "Deductions saved successfully!")
            return True

        except ValueError as e:
            show_error_message("Validation Error", f"Please enter valid numbers for all deduction amounts.\n\nError: {str(e)}")
            return False

    def load_data(self, tax_data: TaxData):
        """Load data from tax_data object"""
        self.tax_data = tax_data

        if not self.method_var:
            return

        # Load deduction method
        method = tax_data.get("deductions.method", "standard")
        self.method_var.set(method)

        # Load itemized deduction values
        if self.medical_entry:
            self.medical_entry.delete(0, "end")
            self.medical_entry.insert(0, str(tax_data.get("deductions.medical_expenses", 0)))

        if self.taxes_entry:
            self.taxes_entry.delete(0, "end")
            self.taxes_entry.insert(0, str(tax_data.get("deductions.state_local_taxes", 0)))

        if self.mortgage_entry:
            self.mortgage_entry.delete(0, "end")
            self.mortgage_entry.insert(0, str(tax_data.get("deductions.mortgage_interest", 0)))

        if self.charitable_entry:
            self.charitable_entry.delete(0, "end")
            self.charitable_entry.insert(0, str(tax_data.get("deductions.charitable_contributions", 0)))

        # Update display
        self._update_standard_deduction_display()
        self._on_method_change()
        self._calculate_itemized_total()

    def get_data(self) -> Dict[str, Any]:
        """Get current form data"""
        data = {
            "method": self.method_var.get() if self.method_var else "standard"
        }

        if data["method"] == "itemized":
            data.update({
                "medical_expenses": float(self.medical_entry.get().replace(",", "").replace("$", "") or 0) if self.medical_entry else 0,
                "state_local_taxes": float(self.taxes_entry.get().replace(",", "").replace("$", "") or 0) if self.taxes_entry else 0,
                "mortgage_interest": float(self.mortgage_entry.get().replace(",", "").replace("$", "") or 0) if self.mortgage_entry else 0,
                "charitable_contributions": float(self.charitable_entry.get().replace(",", "").replace("$", "") or 0) if self.charitable_entry else 0,
            })

        return data