"""
Modern Payments Page - CustomTkinter-based payments collection

Provides a modern interface for entering tax payments including federal withholding,
estimated tax payments, and prior year overpayments with real-time calculations.
"""

import customtkinter as ctk
from typing import Optional, Dict, Any, Callable
import tkinter as tk
from datetime import datetime

from config.app_config import AppConfig
from models.tax_data import TaxData
from utils.w2_calculator import W2Calculator
from gui.modern_ui_components import (
    ModernFrame, ModernLabel, ModernButton, ModernEntry, ModernScrollableFrame,
    show_info_message, show_error_message, show_confirmation
)


class ModernPaymentsPage(ModernFrame):
    """
    Modern payments page using CustomTkinter.

    Features:
    - Federal withholding display (calculated from W-2s)
    - Estimated tax payments management
    - Prior year overpayment entry
    - Real-time total calculations
    - Modern expandable sections
    """

    def __init__(self, parent, config: AppConfig, on_complete: Optional[Callable] = None):
        """
        Initialize the modern payments page.

        Args:
            parent: Parent widget
            config: Application configuration
            on_complete: Callback for completion (tax_data, action)
        """
        super().__init__(parent, title="Tax Payments")
        self.config = config
        self.on_complete = on_complete
        self.tax_data: Optional[TaxData] = None

        # UI components
        self.estimated_payments_frame: Optional[ModernScrollableFrame] = None
        self.total_label: Optional[ModernLabel] = None
        self.prior_overpayment_entry: Optional[ModernEntry] = None

        # Build the UI
        self._build_ui()

    def _build_ui(self):
        """Build the user interface"""
        # Main scrollable content
        content_frame = ModernScrollableFrame(self)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Page header
        header_label = ModernLabel(
            content_frame,
            text="Tax Payments",
            font=ctk.CTkFont(size=24)
        )
        header_label.pack(pady=(0, 10))

        instruction_label = ModernLabel(
            content_frame,
            text="Enter any federal income tax payments you made during the year. Federal withholding from your W-2 forms is calculated automatically.",
            font=ctk.CTkFont(size=12),
            wraplength=700,
            text_color="gray60"
        )
        instruction_label.pack(pady=(0, 20), anchor="w")

        # Federal withholding section
        self._build_federal_withholding_section(content_frame)

        # Estimated payments section
        self._build_estimated_payments_section(content_frame)

        # Other payments section
        self._build_other_payments_section(content_frame)

        # Total payments display
        self._build_total_section(content_frame)

        # Navigation buttons
        self._build_navigation_buttons(content_frame)

    def _build_federal_withholding_section(self, parent):
        """Build federal withholding section"""
        # Section frame
        withholding_frame = ctk.CTkFrame(parent, fg_color="transparent")
        withholding_frame.pack(fill="x", pady=(0, 20))

        # Section header
        header_label = ModernLabel(
            withholding_frame,
            text="Federal Income Tax Withheld",
            font=ctk.CTkFont(size=16)
        )
        header_label.pack(anchor="w", pady=(0, 10))

        # Withholding info
        self.withholding_info_label = ModernLabel(
            withholding_frame,
            text="Total from W-2 forms: $0.00",
            font=ctk.CTkFont(size=14)
        )
        self.withholding_info_label.pack(anchor="w", pady=5)

    def _build_estimated_payments_section(self, parent):
        """Build estimated payments section"""
        # Section frame
        est_frame = ctk.CTkFrame(parent, fg_color="transparent")
        est_frame.pack(fill="x", pady=(0, 20))

        # Section header
        header_label = ModernLabel(
            est_frame,
            text="Estimated Tax Payments",
            font=ctk.CTkFont(size=16)
        )
        header_label.pack(anchor="w", pady=(0, 10))

        # Description
        desc_label = ModernLabel(
            est_frame,
            text="Enter any estimated tax payments you made during the year (Form 1040-ES).",
            font=ctk.CTkFont(size=11),
            text_color="gray60",
            wraplength=600
        )
        desc_label.pack(anchor="w", pady=(0, 10))

        # Payments list frame
        self.estimated_payments_frame = ModernScrollableFrame(est_frame, height=200)
        self.estimated_payments_frame.pack(fill="x", pady=(0, 10))

        # Add payment button
        add_button = ModernButton(
            est_frame,
            text="+ Add Estimated Payment",
            command=self._add_estimated_payment,
            button_type="secondary",
            height=35
        )
        add_button.pack(anchor="w", pady=(10, 0))

    def _build_other_payments_section(self, parent):
        """Build other payments section"""
        # Section frame
        other_frame = ctk.CTkFrame(parent, fg_color="transparent")
        other_frame.pack(fill="x", pady=(0, 20))

        # Section header
        header_label = ModernLabel(
            other_frame,
            text="Other Payments",
            font=ctk.CTkFont(size=16)
        )
        header_label.pack(anchor="w", pady=(0, 10))

        # Prior year overpayment
        overpayment_frame = ctk.CTkFrame(other_frame, fg_color="transparent")
        overpayment_frame.pack(fill="x", pady=5)

        overpayment_label = ModernLabel(
            overpayment_frame,
            text="Prior year overpayment applied to this year:",
            font=ctk.CTkFont(size=12)
        )
        overpayment_label.pack(anchor="w", pady=(0, 5))

        self.prior_overpayment_entry = ModernEntry(
            overpayment_frame,
            placeholder_text="0.00",
            width=200
        )
        self.prior_overpayment_entry.pack(anchor="w", pady=(0, 5))
        self.prior_overpayment_entry.bind("<KeyRelease>", lambda e: self._calculate_total())

    def _build_total_section(self, parent):
        """Build total payments section"""
        # Total frame
        total_frame = ctk.CTkFrame(parent, fg_color="transparent")
        total_frame.pack(fill="x", pady=(20, 0))

        # Total label
        self.total_label = ModernLabel(
            total_frame,
            text="Total Payments: $0.00",
            font=ctk.CTkFont(size=18),
            text_color="green"
        )
        self.total_label.pack(anchor="w")

    def _build_navigation_buttons(self, parent):
        """Build navigation buttons"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", pady=(30, 20))

        # Back button
        back_button = ModernButton(
            button_frame,
            text="← Back to Credits",
            command=self._go_back,
            button_type="secondary",
            width=150
        )
        back_button.pack(side="left")

        # Continue button
        continue_button = ModernButton(
            button_frame,
            text="Save and View Forms →",
            command=self._save_and_continue,
            button_type="primary",
            width=200
        )
        continue_button.pack(side="right")

    def _refresh_estimated_payments_list(self):
        """Refresh the estimated payments list"""
        # Clear existing payments
        for widget in self.estimated_payments_frame.winfo_children():
            widget.destroy()

        if not self.tax_data:
            return

        est_payments = self.tax_data.get("payments.estimated_payments", [])

        if not est_payments:
            empty_label = ModernLabel(
                self.estimated_payments_frame,
                text="No estimated payments entered yet.",
                font=ctk.CTkFont(size=11),
                text_color="gray50"
            )
            empty_label.pack(pady=20)
            return

        for idx, payment in enumerate(est_payments):
            self._create_payment_card(idx, payment)

    def _create_payment_card(self, index: int, payment: Dict[str, Any]):
        """Create a payment card for the list"""
        # Payment card frame
        card_frame = ctk.CTkFrame(self.estimated_payments_frame, fg_color="gray90")
        card_frame.pack(fill="x", pady=5, padx=5)

        # Payment info
        date = payment.get('date', 'N/A')
        amount = payment.get('amount', 0)

        info_text = f"Date: {date} | Amount: ${amount:,.2f}"

        info_label = ModernLabel(
            card_frame,
            text=info_text,
            font=ctk.CTkFont(size=12)
        )
        info_label.pack(side="left", padx=15, pady=10)

        # Delete button
        delete_button = ModernButton(
            card_frame,
            text="🗑️",
            command=lambda: self._delete_estimated_payment(index),
            button_type="secondary",
            width=40,
            height=30
        )
        delete_button.pack(side="right", padx=10, pady=10)

    def _add_estimated_payment(self):
        """Add a new estimated payment"""
        dialog = ModernEstimatedPaymentDialog(self, self._on_payment_added)
        dialog.grab_set()

    def _on_payment_added(self):
        """Handle payment added"""
        self._refresh_estimated_payments_list()
        self._calculate_total()

    def _delete_estimated_payment(self, index: int):
        """Delete an estimated payment"""
        if not self.tax_data:
            return

        if show_confirmation("Delete Payment", "Are you sure you want to delete this payment?"):
            self.tax_data.remove_from_list("payments.estimated_payments", index)
            self._refresh_estimated_payments_list()
            self._calculate_total()

    def _calculate_total(self):
        """Calculate and display total payments"""
        if not self.tax_data:
            return

        # Federal withholding from W-2s
        w2_forms = self.tax_data.get("income.w2_forms", [])
        total_withholding = W2Calculator.calculate_total_withholding(w2_forms)

        # Estimated payments
        est_payments = self.tax_data.get("payments.estimated_payments", [])
        total_estimated = sum(p.get("amount", 0) for p in est_payments)

        # Prior year overpayment
        try:
            prior_overpayment = float(self.prior_overpayment_entry.get() or 0)
        except ValueError:
            prior_overpayment = 0

        # Total
        total = total_withholding + total_estimated + prior_overpayment

        # Update displays
        self.withholding_info_label.configure(
            text=f"Total from W-2 forms: ${total_withholding:,.2f}"
        )

        self.total_label.configure(
            text=f"Total Payments: ${total:,.2f}"
        )

    def _go_back(self):
        """Go back to credits page"""
        if self.on_complete:
            self.on_complete(self.tax_data, "back")

    def _save_and_continue(self):
        """Save data and continue to form viewer"""
        if not self.tax_data:
            return

        try:
            # Save federal withholding from W-2s
            w2_forms = self.tax_data.get("income.w2_forms", [])
            total_withholding = W2Calculator.calculate_total_withholding(w2_forms)
            self.tax_data.set("payments.federal_withholding", total_withholding)

            # Save prior year overpayment
            try:
                prior_overpayment = float(self.prior_overpayment_entry.get() or 0)
                self.tax_data.set("payments.prior_year_overpayment", prior_overpayment)
            except ValueError:
                show_error_message("Invalid Input", "Please enter a valid number for prior year overpayment.")
                return

            # Call completion callback
            if self.on_complete:
                self.on_complete(self.tax_data, "continue")

        except Exception as e:
            show_error_message("Save Error", f"Failed to save payments data: {str(e)}")

    def load_data(self, tax_data: TaxData):
        """
        Load tax data into the page.

        Args:
            tax_data: Tax data to load
        """
        self.tax_data = tax_data

        # Load prior year overpayment
        prior_overpayment = self.tax_data.get("payments.prior_year_overpayment", 0)
        self.prior_overpayment_entry.delete(0, "end")
        self.prior_overpayment_entry.insert(0, str(prior_overpayment))

        # Refresh estimated payments list
        self._refresh_estimated_payments_list()

        # Calculate totals
        self._calculate_total()


class ModernEstimatedPaymentDialog(ctk.CTkToplevel):
    """
    Modern dialog for entering estimated tax payments.
    """

    def __init__(self, parent, on_complete: Callable):
        """
        Initialize the dialog.

        Args:
            parent: Parent window
            on_complete: Callback when payment is added
        """
        super().__init__(parent)

        self.on_complete = on_complete
        self.title("Add Estimated Tax Payment")
        self.geometry("450x300")

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Center dialog
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        """Build the dialog UI"""
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ModernLabel(
            main_frame,
            text="Add Estimated Tax Payment",
            font=ctk.CTkFont(size=18)
        )
        title_label.pack(pady=(0, 20))

        # Date field
        date_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        date_frame.pack(fill="x", pady=(0, 15))

        date_label = ModernLabel(
            date_frame,
            text="Payment Date:",
            font=ctk.CTkFont(size=12)
        )
        date_label.pack(anchor="w", pady=(0, 5))

        self.date_entry = ModernEntry(
            date_frame,
            placeholder_text="MM/DD/YYYY"
        )
        self.date_entry.pack(fill="x")

        # Amount field
        amount_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        amount_frame.pack(fill="x", pady=(0, 20))

        amount_label = ModernLabel(
            amount_frame,
            text="Amount Paid:",
            font=ctk.CTkFont(size=12)
        )
        amount_label.pack(anchor="w", pady=(0, 5))

        self.amount_entry = ModernEntry(
            amount_frame,
            placeholder_text="0.00"
        )
        self.amount_entry.pack(fill="x")

        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(20, 0))

        cancel_button = ModernButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            button_type="secondary",
            width=100
        )
        cancel_button.pack(side="left")

        add_button = ModernButton(
            button_frame,
            text="Add Payment",
            command=self._add_payment,
            button_type="primary",
            width=120
        )
        add_button.pack(side="right")

        # Bind Enter key to add payment
        self.bind("<Return>", lambda e: self._add_payment())
        self.bind("<Escape>", lambda e: self.destroy())

    def _add_payment(self):
        """Add the payment"""
        try:
            # Validate date
            date_str = self.date_entry.get().strip()
            if date_str:
                try:
                    datetime.strptime(date_str, "%m/%d/%Y")
                except ValueError:
                    show_error_message("Invalid Date", "Please enter date in MM/DD/YYYY format.")
                    return

            # Validate amount
            amount_str = self.amount_entry.get().strip()
            if not amount_str:
                show_error_message("Missing Amount", "Please enter the payment amount.")
                return

            try:
                amount = float(amount_str)
                if amount <= 0:
                    show_error_message("Invalid Amount", "Payment amount must be greater than zero.")
                    return
            except ValueError:
                show_error_message("Invalid Amount", "Please enter a valid number for the amount.")
                return

            # Get tax data from parent
            if hasattr(self.master, 'tax_data') and self.master.tax_data:
                payment_data = {
                    "date": date_str if date_str else "",
                    "amount": amount,
                }

                self.master.tax_data.add_to_list("payments.estimated_payments", payment_data)

                # Call completion callback
                if self.on_complete:
                    self.on_complete()

                self.destroy()
            else:
                show_error_message("Error", "Unable to access tax data.")

        except Exception as e:
            show_error_message("Error", f"Failed to add payment: {str(e)}")