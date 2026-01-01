"""
Receipt Scanning Window - GUI for OCR receipt processing

Provides interface for:
- Receipt image upload and scanning
- OCR text extraction and data parsing
- Tax category classification
- Manual data correction
- Batch processing
- Integration with tax data
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
import threading
import os

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.receipt_scanning_service import (
    ReceiptScanningService,
    ReceiptData,
    ScanResult
)
from utils.error_tracker import get_error_tracker


class ReceiptScanningWindow:
    """
    Window for scanning receipts and extracting tax-relevant data using OCR.

    Features:
    - Image upload and preview
    - OCR processing with progress indication
    - Data extraction and validation
    - Tax category classification
    - Manual correction capabilities
    - Batch processing support
    - Integration with tax return data
    """

    def __init__(self, parent: tk.Tk, config: AppConfig, tax_data: Optional[TaxData] = None):
        """
        Initialize receipt scanning window.

        Args:
            parent: Parent window
            config: Application configuration
            tax_data: Tax return data to integrate with
        """
        self.parent = parent
        self.config = config
        self.tax_data = tax_data
        self.error_tracker = get_error_tracker()

        # Initialize service
        self.scanning_service = ReceiptScanningService(config)

        # Current data
        self.current_receipt: Optional[ReceiptData] = None
        self.scanned_receipts: List[ReceiptData] = []
        self.current_image_path: Optional[str] = None

        # UI components
        self.window: Optional[tk.Toplevel] = None
        self.notebook: Optional[ttk.Notebook] = None
        self.receipts_tree: Optional[ttk.Treeview] = None
        self.progress_var: Optional[tk.DoubleVar] = None
        self.status_label: Optional[ttk.Label] = None

        # Form variables
        self.receipt_vars = {}
        self.category_var = tk.StringVar(value="miscellaneous")

    def show(self):
        """Show the receipt scanning window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Receipt Scanning & OCR - Freedom US Tax Return")
        self.window.geometry("1200x900")
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
            text="Receipt Scanning & OCR Processing",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 10))

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, pady=(0, 10))

        # Create tabs
        self._create_scan_tab()
        self._create_review_tab()
        self._create_batch_tab()

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
            text="Scan Receipt",
            command=self._scan_receipt
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            button_frame,
            text="Save to Tax Data",
            command=self._save_to_tax_data
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            button_frame,
            text="Export CSV",
            command=self._export_csv
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            button_frame,
            text="Clear All",
            command=self._clear_all
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            button_frame,
            text="Close",
            command=self._close_window
        ).pack(side="right")

    def _create_scan_tab(self):
        """Create the single receipt scanning tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Scan Receipt")

        # Split into left (image) and right (data) panels
        left_frame = ttk.Frame(tab)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        right_frame = ttk.Frame(tab)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # Left panel - Image upload and preview
        image_frame = ttk.LabelFrame(left_frame, text="Receipt Image")
        image_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Image preview area
        self.image_label = ttk.Label(image_frame, text="No image selected", background="lightgray")
        self.image_label.pack(fill="both", expand=True, padx=10, pady=10)

        # Image controls
        img_ctrl_frame = ttk.Frame(image_frame)
        img_ctrl_frame.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Button(img_ctrl_frame, text="Select Image", command=self._select_image).pack(side="left", padx=(0, 5))
        ttk.Button(img_ctrl_frame, text="Preview Image", command=self._preview_image).pack(side="left", padx=(0, 5))

        # Right panel - Extracted data
        data_frame = ttk.LabelFrame(right_frame, text="Extracted Data")
        data_frame.pack(fill="both", expand=True)

        # Initialize receipt variables
        self.receipt_vars = {}

        # Vendor and amount
        ttk.Label(data_frame, text="Vendor Name:").grid(row=0, column=0, sticky="w", pady=5, padx=10)
        self.receipt_vars['vendor'] = tk.StringVar()
        ttk.Entry(data_frame, textvariable=self.receipt_vars['vendor']).grid(row=0, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(data_frame, text="Total Amount:").grid(row=1, column=0, sticky="w", pady=5, padx=10)
        self.receipt_vars['total'] = tk.StringVar()
        ttk.Entry(data_frame, textvariable=self.receipt_vars['total']).grid(row=1, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(data_frame, text="Tax Amount:").grid(row=2, column=0, sticky="w", pady=5, padx=10)
        self.receipt_vars['tax'] = tk.StringVar()
        ttk.Entry(data_frame, textvariable=self.receipt_vars['tax']).grid(row=2, column=1, sticky="ew", pady=5, padx=(0, 10))

        ttk.Label(data_frame, text="Date:").grid(row=3, column=0, sticky="w", pady=5, padx=10)
        self.receipt_vars['date'] = tk.StringVar()
        ttk.Entry(data_frame, textvariable=self.receipt_vars['date']).grid(row=3, column=1, sticky="ew", pady=5, padx=(0, 10))

        # Category selection
        ttk.Label(data_frame, text="Tax Category:").grid(row=4, column=0, sticky="w", pady=5, padx=10)
        category_combo = ttk.Combobox(
            data_frame,
            textvariable=self.category_var,
            values=[
                "medical", "charitable", "business", "education",
                "vehicle", "home_office", "retirement", "energy",
                "state_local", "miscellaneous"
            ],
            state="readonly"
        )
        category_combo.grid(row=4, column=1, sticky="ew", pady=5, padx=(0, 10))

        # Raw OCR text
        ttk.Label(data_frame, text="OCR Text:").grid(row=5, column=0, sticky="nw", pady=5, padx=10)
        self.ocr_text = scrolledtext.ScrolledText(data_frame, height=8, width=40)
        self.ocr_text.grid(row=5, column=1, sticky="ew", pady=5, padx=(0, 10))

        # Configure grid weights
        data_frame.columnconfigure(1, weight=1)

        # Action buttons
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(btn_frame, text="Process Image", command=self._process_image).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Save Receipt", command=self._save_receipt).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Clear Form", command=self._clear_form).pack(side="left", padx=(0, 5))

    def _create_review_tab(self):
        """Create the receipt review and management tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Review Receipts")

        # Receipts list
        list_frame = ttk.LabelFrame(tab, text="Scanned Receipts")
        list_frame.pack(fill="both", expand=True, pady=(0, 10))

        columns = ("Vendor", "Amount", "Tax", "Date", "Category", "Confidence")
        self.receipts_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.receipts_tree.heading(col, text=col)
            self.receipts_tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.receipts_tree.yview)
        self.receipts_tree.configure(yscrollcommand=scrollbar.set)

        self.receipts_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Receipt details
        details_frame = ttk.LabelFrame(tab, text="Receipt Details")
        details_frame.pack(fill="both", expand=True)

        self.details_text = scrolledtext.ScrolledText(details_frame, height=10)
        self.details_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Review buttons
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(btn_frame, text="Edit Selected", command=self._edit_selected_receipt).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Delete Selected", command=self._delete_selected_receipt).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Update Category", command=self._update_category).pack(side="left", padx=(0, 5))

    def _create_batch_tab(self):
        """Create the batch processing tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Batch Processing")

        # Batch controls
        controls_frame = ttk.LabelFrame(tab, text="Batch Operations")
        controls_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(controls_frame, text="Select multiple receipt images for batch processing:").pack(pady=10, padx=10, anchor="w")

        ttk.Button(
            controls_frame,
            text="Select Images",
            command=self._select_batch_images
        ).pack(pady=(0, 10), padx=10, anchor="w")

        # Batch results
        results_frame = ttk.LabelFrame(tab, text="Batch Results")
        results_frame.pack(fill="both", expand=True)

        self.batch_text = scrolledtext.ScrolledText(results_frame, height=15)
        self.batch_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Batch buttons
        batch_btn_frame = ttk.Frame(tab)
        batch_btn_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(batch_btn_frame, text="Process Batch", command=self._process_batch).pack(side="left", padx=(0, 5))
        ttk.Button(batch_btn_frame, text="Save All Valid", command=self._save_batch).pack(side="left", padx=(0, 5))
        ttk.Button(batch_btn_frame, text="Clear Results", command=self._clear_batch).pack(side="left", padx=(0, 5))

    def _load_data(self):
        """Load existing receipt data"""
        try:
            if self.tax_data:
                # Load receipts from tax data
                self.scanned_receipts = self._load_receipts_from_tax_data()

            self._refresh_receipts_list()
            self.status_label.config(text="Data loaded successfully")

        except Exception as e:
            self.error_tracker.track_error(e, {"operation": "_load_data"})
            messagebox.showerror("Load Error", f"Failed to load receipt data: {str(e)}")

    def _load_receipts_from_tax_data(self) -> List[ReceiptData]:
        """Load receipts from tax data"""
        receipts = []
        if self.tax_data and hasattr(self.tax_data, 'get'):
            # Try to load from various sections
            sections_to_check = ['receipts', 'scanned_receipts', 'ocr_receipts']
            for section in sections_to_check:
                try:
                    section_data = self.tax_data.get(section, [])
                    if section_data:
                        for receipt_dict in section_data:
                            try:
                                receipts.append(ReceiptData(
                                    vendor_name=receipt_dict.get('vendor_name', ''),
                                    total_amount=Decimal(str(receipt_dict.get('total_amount', 0))),
                                    tax_amount=Decimal(str(receipt_dict.get('tax_amount', 0))) if receipt_dict.get('tax_amount') else None,
                                    date=date.fromisoformat(receipt_dict['date']) if receipt_dict.get('date') else None,
                                    items=receipt_dict.get('items', []),
                                    category=receipt_dict.get('category', 'miscellaneous'),
                                    confidence_score=float(receipt_dict.get('confidence_score', 0)),
                                    raw_text=receipt_dict.get('raw_text', ''),
                                    extracted_at=datetime.fromisoformat(receipt_dict.get('extracted_at', datetime.now().isoformat()))
                                ))
                            except Exception as e:
                                self.error_tracker.track_error(e, {"receipt_dict": receipt_dict})
                                continue
                        break
                except Exception:
                    continue
        return receipts

    def _refresh_receipts_list(self):
        """Refresh the receipts treeview"""
        if not self.receipts_tree:
            return

        # Clear existing items
        for item in self.receipts_tree.get_children():
            self.receipts_tree.delete(item)

        # Add receipts
        for i, receipt in enumerate(self.scanned_receipts):
            self.receipts_tree.insert("", "end", values=(
                receipt.vendor_name,
                f"${receipt.total_amount:.2f}",
                f"${receipt.tax_amount:.2f}" if receipt.tax_amount else "$0.00",
                receipt.date.strftime("%Y-%m-%d") if receipt.date else "",
                receipt.category,
                f"{receipt.confidence_score:.1f}%"
            ), tags=(str(i),))

    def _select_image(self):
        """Select a receipt image file"""
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("PNG files", "*.png"),
            ("All files", "*.*")
        ]

        filename = filedialog.askopenfilename(
            title="Select Receipt Image",
            filetypes=filetypes
        )

        if filename:
            self.current_image_path = filename
            self.status_label.config(text=f"Selected: {os.path.basename(filename)}")
            self._preview_image()

    def _preview_image(self):
        """Preview the selected image"""
        if not self.current_image_path or not os.path.exists(self.current_image_path):
            messagebox.showwarning("No Image", "Please select an image file first.")
            return

        try:
            # For now, just show the filename since tkinter doesn't easily display images
            # In a full implementation, you'd use PIL to resize and display the image
            self.image_label.config(text=f"Image: {os.path.basename(self.current_image_path)}")
            self.status_label.config(text="Image ready for processing")

        except Exception as e:
            messagebox.showerror("Preview Error", f"Failed to preview image: {str(e)}")

    def _process_image(self):
        """Process the selected image with OCR"""
        if not self.current_image_path:
            messagebox.showwarning("No Image", "Please select an image file first.")
            return

        if not os.path.exists(self.current_image_path):
            messagebox.showerror("File Not Found", "The selected image file no longer exists.")
            return

        # Process in background thread
        self.progress_var.set(0)
        self.status_label.config(text="Processing image...")

        def process_thread():
            try:
                self.progress_var.set(25)
                result = self.scanning_service.scan_receipt(self.current_image_path)

                self.progress_var.set(75)

                if result.success and result.receipt_data:
                    self.current_receipt = result.receipt_data
                    self._populate_receipt_form()
                    self.status_label.config(text=f"OCR completed successfully (confidence: {result.receipt_data.confidence_score:.1f}%)")
                else:
                    self.status_label.config(text=f"OCR failed: {result.error_message}")
                    messagebox.showwarning("OCR Failed", f"Failed to extract data from receipt: {result.error_message}")

                self.progress_var.set(100)

            except Exception as e:
                self.error_tracker.track_error(e, {"image_path": self.current_image_path})
                self.status_label.config(text=f"Processing error: {str(e)}")
                messagebox.showerror("Processing Error", f"Failed to process image: {str(e)}")

        thread = threading.Thread(target=process_thread, daemon=True)
        thread.start()

    def _populate_receipt_form(self):
        """Populate the form with extracted receipt data"""
        if not self.current_receipt:
            return

        self.receipt_vars['vendor'].set(self.current_receipt.vendor_name)
        self.receipt_vars['total'].set(f"{self.current_receipt.total_amount:.2f}")
        if self.current_receipt.tax_amount:
            self.receipt_vars['tax'].set(f"{self.current_receipt.tax_amount:.2f}")
        if self.current_receipt.date:
            self.receipt_vars['date'].set(self.current_receipt.date.isoformat())
        self.category_var.set(self.current_receipt.category)
        self.ocr_text.delete(1.0, tk.END)
        self.ocr_text.insert(tk.END, self.current_receipt.raw_text)

    def _save_receipt(self):
        """Save the current receipt to the list"""
        if not self.current_receipt:
            messagebox.showwarning("No Receipt", "Please process an image first.")
            return

        try:
            # Update receipt with form data
            self.current_receipt.vendor_name = self.receipt_vars['vendor'].get()
            self.current_receipt.total_amount = Decimal(self.receipt_vars['total'].get())
            tax_str = self.receipt_vars['tax'].get()
            self.current_receipt.tax_amount = Decimal(tax_str) if tax_str else None
            date_str = self.receipt_vars['date'].get()
            self.current_receipt.date = date.fromisoformat(date_str) if date_str else None
            self.current_receipt.category = self.category_var.get()

            # Add to list if not already there
            if self.current_receipt not in self.scanned_receipts:
                self.scanned_receipts.append(self.current_receipt)

            self._refresh_receipts_list()
            self.status_label.config(text="Receipt saved successfully")

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save receipt: {str(e)}")

    def _save_to_tax_data(self):
        """Save all receipts to tax data"""
        if not self.tax_data:
            messagebox.showwarning("No Tax Data", "No tax data available to save to.")
            return

        if not self.scanned_receipts:
            messagebox.showwarning("No Receipts", "No receipts to save.")
            return

        try:
            # Convert receipts to dictionaries
            receipts_data = [receipt.to_dict() for receipt in self.scanned_receipts]

            # Save to tax data
            self.tax_data.set('receipts', receipts_data)

            self.status_label.config(text=f"Saved {len(self.scanned_receipts)} receipts to tax data")

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save receipts to tax data: {str(e)}")

    def _export_csv(self):
        """Export receipts to CSV file"""
        if not self.scanned_receipts:
            messagebox.showwarning("No Data", "No receipts to export.")
            return

        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Receipts to CSV"
            )

            if filename:
                with open(filename, 'w', newline='') as csvfile:
                    # Write header
                    csvfile.write("Vendor,Total Amount,Tax Amount,Date,Category,Confidence Score,Raw Text\n")

                    # Write data
                    for receipt in self.scanned_receipts:
                        csvfile.write(f'"{receipt.vendor_name}",')
                        csvfile.write(f'"{receipt.total_amount}",')
                        csvfile.write(f'"{receipt.tax_amount if receipt.tax_amount else 0}",')
                        csvfile.write(f'"{receipt.date.isoformat() if receipt.date else ""}",')
                        csvfile.write(f'"{receipt.category}",')
                        csvfile.write(f'"{receipt.confidence_score}",')
                        csvfile.write(f'"{receipt.raw_text.replace(chr(34), chr(39))}"\n')

                self.status_label.config(text=f"Exported {len(self.scanned_receipts)} receipts to CSV")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export CSV: {str(e)}")

    def _clear_form(self):
        """Clear the receipt form"""
        for var in self.receipt_vars.values():
            var.set("")
        self.category_var.set("miscellaneous")
        self.ocr_text.delete(1.0, tk.END)
        self.current_receipt = None
        self.current_image_path = None
        self.image_label.config(text="No image selected")

    def _clear_all(self):
        """Clear all data"""
        self.scanned_receipts.clear()
        self._clear_form()
        self._refresh_receipts_list()
        self.details_text.delete(1.0, tk.END)
        self.batch_text.delete(1.0, tk.END)
        self.status_label.config(text="All data cleared")

    def _edit_selected_receipt(self):
        """Edit the selected receipt"""
        selection = self.receipts_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a receipt to edit.")
            return

        try:
            item = selection[0]
            index = int(self.receipts_tree.item(item, "tags")[0])
            receipt = self.scanned_receipts[index]

            # Populate form
            self.current_receipt = receipt
            self._populate_receipt_form()

            # Switch to scan tab
            self.notebook.select(0)

            self.status_label.config(text="Receipt loaded for editing")

        except Exception as e:
            messagebox.showerror("Edit Error", f"Failed to load receipt: {str(e)}")

    def _delete_selected_receipt(self):
        """Delete the selected receipt"""
        selection = self.receipts_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a receipt to delete.")
            return

        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this receipt?"):
            return

        try:
            item = selection[0]
            index = int(self.receipts_tree.item(item, "tags")[0])
            del self.scanned_receipts[index]

            self._refresh_receipts_list()
            self.details_text.delete(1.0, tk.END)
            self.status_label.config(text="Receipt deleted")

        except Exception as e:
            messagebox.showerror("Delete Error", f"Failed to delete receipt: {str(e)}")

    def _update_category(self):
        """Update the category of selected receipts"""
        selection = self.receipts_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select receipts to update.")
            return

        try:
            new_category = self.category_var.get()

            for item in selection:
                index = int(self.receipts_tree.item(item, "tags")[0])
                self.scanned_receipts[index].category = new_category

            self._refresh_receipts_list()
            self.status_label.config(text=f"Updated category for {len(selection)} receipt(s)")

        except Exception as e:
            messagebox.showerror("Update Error", f"Failed to update categories: {str(e)}")

    def _select_batch_images(self):
        """Select multiple images for batch processing"""
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif"),
            ("All files", "*.*")
        ]

        filenames = filedialog.askopenfilenames(
            title="Select Receipt Images",
            filetypes=filetypes
        )

        if filenames:
            self.batch_images = list(filenames)
            self.batch_text.delete(1.0, tk.END)
            self.batch_text.insert(tk.END, f"Selected {len(filenames)} images for batch processing:\n\n")
            for filename in filenames:
                self.batch_text.insert(tk.END, f"• {os.path.basename(filename)}\n")
            self.status_label.config(text=f"Selected {len(filenames)} images for batch processing")

    def _process_batch(self):
        """Process batch of images"""
        if not hasattr(self, 'batch_images') or not self.batch_images:
            messagebox.showwarning("No Images", "Please select images for batch processing first.")
            return

        self.progress_var.set(0)
        self.status_label.config(text="Processing batch...")

        def batch_thread():
            try:
                total_images = len(self.batch_images)
                successful = 0
                failed = 0

                self.batch_text.delete(1.0, tk.END)
                self.batch_text.insert(tk.END, f"Processing {total_images} images...\n\n")

                for i, image_path in enumerate(self.batch_images):
                    try:
                        self.progress_var.set((i / total_images) * 100)
                        result = self.scanning_service.scan_receipt(image_path)

                        if result.success and result.receipt_data:
                            self.scanned_receipts.append(result.receipt_data)
                            successful += 1
                            self.batch_text.insert(tk.END, f"✓ {os.path.basename(image_path)} - Success\n")
                        else:
                            failed += 1
                            self.batch_text.insert(tk.END, f"✗ {os.path.basename(image_path)} - Failed: {result.error_message}\n")

                    except Exception as e:
                        failed += 1
                        self.batch_text.insert(tk.END, f"✗ {os.path.basename(image_path)} - Error: {str(e)}\n")

                self.progress_var.set(100)
                self._refresh_receipts_list()

                self.batch_text.insert(tk.END, f"\nBatch processing complete:\n")
                self.batch_text.insert(tk.END, f"Successful: {successful}\n")
                self.batch_text.insert(tk.END, f"Failed: {failed}\n")

                self.status_label.config(text=f"Batch processing complete: {successful} successful, {failed} failed")

            except Exception as e:
                self.status_label.config(text=f"Batch processing error: {str(e)}")
                messagebox.showerror("Batch Error", f"Failed to process batch: {str(e)}")

        thread = threading.Thread(target=batch_thread, daemon=True)
        thread.start()

    def _save_batch(self):
        """Save all valid receipts from batch"""
        if not self.scanned_receipts:
            messagebox.showwarning("No Receipts", "No receipts to save from batch processing.")
            return

        # Save to tax data
        self._save_to_tax_data()

    def _clear_batch(self):
        """Clear batch results"""
        if hasattr(self, 'batch_images'):
            self.batch_images.clear()
        self.batch_text.delete(1.0, tk.END)
        self.status_label.config(text="Batch results cleared")

    def _scan_receipt(self):
        """Alias for _process_image for button consistency"""
        self._process_image()

    def _bind_events(self):
        """Bind event handlers"""
        if self.receipts_tree:
            self.receipts_tree.bind("<Double-1>", lambda e: self._edit_selected_receipt())

    def _close_window(self):
        """Close the window"""
        if self.window:
            self.window.destroy()