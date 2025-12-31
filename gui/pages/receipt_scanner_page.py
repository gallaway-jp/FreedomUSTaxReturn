"""
Receipt Scanner Page

Page for scanning receipts and extracting tax-relevant data.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any
from datetime import datetime

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
            # Integrate with tax data model based on category
            category = receipt_data.get('category', '').lower()
            amount = receipt_data.get('total_amount', 0)
            vendor = receipt_data.get('vendor_name', 'Unknown')
            
            # Map receipt categories to tax deduction categories
            # Note: Only map to categories currently supported in the deductions UI
            deduction_mapping = {
                'medical': 'medical_expenses',
                'charitable': 'charitable_contributions',
                # Future categories that could be added to UI:
                # 'business': 'business_expenses',
                # 'office': 'home_office',
                # 'vehicle': 'vehicle_expenses', 
                # 'education': 'education_expenses',
            }
            
            deduction_key = deduction_mapping.get(category)
            
            if deduction_key:
                # Add to existing deduction amount
                current_amount = self.tax_data.get(f"deductions.{deduction_key}", 0)
                new_amount = current_amount + amount
                
                # Save to tax data
                self.tax_data.set(f"deductions.{deduction_key}", new_amount)
                
                # Also store the receipt details for audit trail
                receipts = self.tax_data.get("receipts", [])
                receipt_record = {
                    'vendor_name': vendor,
                    'amount': amount,
                    'category': category,
                    'date_scanned': datetime.now().isoformat(),
                    'deduction_category': deduction_key,
                    'confidence_score': receipt_data.get('confidence_score', 0)
                }
                receipts.append(receipt_record)
                self.tax_data.set("receipts", receipts)
                
                messagebox.showinfo(
                    "Receipt Scanned & Saved",
                    f"Receipt from {vendor} for ${amount:.2f} has been processed and added to {deduction_key.replace('_', ' ').title()}.\n\n"
                    f"Total {deduction_key.replace('_', ' ').title()}: ${new_amount:.2f}\n"
                    f"Confidence: {receipt_data.get('confidence_score', 0):.1f}%"
                )
                
                # Refresh the deductions page if it's currently visible
                if hasattr(self.main_window, 'current_page') and self.main_window.current_page:
                    # Check if deductions page is current
                    if hasattr(self.main_window.current_page, 'calculate_itemized_total'):
                        self.main_window.current_page.calculate_itemized_total()
                        
            else:
                # Category not recognized for deductions, just show info
                messagebox.showinfo(
                    "Receipt Scanned",
                    f"Receipt from {vendor} for ${amount:.2f} has been processed.\n\n"
                    f"Category: {category.title()}\n"
                    f"Confidence: {receipt_data.get('confidence_score', 0):.1f}%\n\n"
                    f"This category doesn't map to a tax deduction. You may need to add it manually to the appropriate section."
                )
                
                # Still store the receipt for record keeping
                receipts = self.tax_data.get("receipts", [])
                receipt_record = {
                    'vendor_name': vendor,
                    'amount': amount,
                    'category': category,
                    'date_scanned': datetime.now().isoformat(),
                    'deduction_category': None,
                    'confidence_score': receipt_data.get('confidence_score', 0)
                }
                receipts.append(receipt_record)
                self.tax_data.set("receipts", receipts)

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