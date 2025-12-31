"""
Receipt Scanner Page

Page for scanning receipts and extracting tax-relevant data.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any

from config.app_config import AppConfig
from gui.widgets.receipt_scanner_widget import ReceiptScanningWidget
from models.tax_data import TaxData


class ReceiptScannerPage(ttk.Frame):
    """
    Page for receipt scanning functionality.

    Allows users to scan receipts and extract tax-relevant information
    that can be used for deductions and expense tracking.
    """

    def __init__(self, parent, main_window, config: AppConfig):
        super().__init__(parent)
        self.main_window = main_window
        self.config = config
        self.tax_data = main_window.tax_data

        self.build_ui()

    def build_ui(self):
        """Build the page UI"""
        # Create main container with padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Header with description
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 10))

        title_label = ttk.Label(
            header_frame,
            text="Receipt Scanner",
            font=("Arial", 16, "bold")
        )
        title_label.pack(anchor="w")

        description_label = ttk.Label(
            header_frame,
            text="Scan receipts to automatically extract tax-relevant information including amounts, dates, and vendors. "
                 "This helps identify potential deductions and organize expense records.",
            wraplength=600,
            justify="left"
        )
        description_label.pack(anchor="w", pady=(5, 0))

        # Create the receipt scanner widget
        self.scanner_widget = ReceiptScanningWidget(
            main_frame,
            self.config,
            on_receipt_scanned=self.on_receipt_scanned
        )
        self.scanner_widget.pack(fill="both", expand=True, pady=(10, 0))

        # Footer with tips
        tips_frame = ttk.LabelFrame(main_frame, text="Tips for Better Scanning", padding="5")
        tips_frame.pack(fill="x", pady=(10, 0))

        tips_text = (
            "• Ensure good lighting and focus on the receipt\n"
            "• Hold the camera steady and avoid blurry images\n"
            "• Make sure the entire receipt is visible in the frame\n"
            "• Clean receipts work better than crumpled or stained ones\n"
            "• For best results, receipts should be well-lit and flat"
        )

        tips_label = ttk.Label(
            tips_frame,
            text=tips_text,
            justify="left",
            font=("Arial", 9)
        )
        tips_label.pack(anchor="w")

    def on_receipt_scanned(self, receipt_data: Dict[str, Any]):
        """
        Handle successful receipt scanning.

        Args:
            receipt_data: Dictionary containing extracted receipt data
        """
        try:
            # Here we could integrate with the tax data model
            # For now, just show a success message
            messagebox.showinfo(
                "Receipt Scanned",
                f"Receipt from {receipt_data.get('vendor_name', 'Unknown')} "
                f"for ${receipt_data.get('total_amount', 0):.2f} has been processed.\n\n"
                f"Category: {receipt_data.get('category', 'Unknown')}\n"
                f"Confidence: {receipt_data.get('confidence_score', 0):.1f}%"
            )

            # TODO: Integrate with deductions/expenses tracking
            # This could automatically add to business expenses or charitable contributions
            # based on the category and amount

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to process receipt data: {str(e)}"
            )

    def on_show(self):
        """Called when this page is shown"""
        # Reset the scanner widget when the page is shown
        if hasattr(self.scanner_widget, 'clear_data'):
            self.scanner_widget.clear_data()

    def validate_page(self) -> bool:
        """Validate the page data"""
        # Receipt scanner doesn't require validation
        return True

    def save_data(self):
        """Save page data to tax data model"""
        # Receipt scanner saves data through the callback
        pass

    def load_data(self):
        """Load data from tax data model"""
        # No persistent data to load for receipt scanner
        pass