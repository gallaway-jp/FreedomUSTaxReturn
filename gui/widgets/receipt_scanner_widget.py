"""
Receipt Scanning Widget for tkinter

GUI component for scanning receipts and extracting tax-relevant data.
"""

import os
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Optional, Callable, Dict, Any
from PIL import Image, ImageTk
import threading
import queue

from services.receipt_scanning_service import ReceiptScanningService, ScanResult
from utils.image_processing import ReceiptImageProcessor
from config.app_config import AppConfig
from utils.error_tracker import get_error_tracker

logger = logging.getLogger(__name__)


class ReceiptScanWorker(threading.Thread):
    """Worker thread for receipt scanning to avoid blocking the UI"""

    def __init__(self, service: ReceiptScanningService, image_path: str, result_queue: queue.Queue):
        super().__init__()
        self.service = service
        self.image_path = image_path
        self.result_queue = result_queue

    def run(self):
        """Execute the scanning operation"""
        try:
            result = self.service.scan_receipt(self.image_path)
            self.result_queue.put(result)
        except Exception as e:
            logger.error(f"Scanning failed: {e}")
            error_result = ScanResult(
                success=False,
                receipt_data=None,
                error_message=str(e),
                processing_time=0.0,
                image_quality_score=0.0
            )
            self.result_queue.put(error_result)


class ReceiptScanningWidget(ttk.Frame):
    """
    Widget for scanning receipts and displaying extracted data.

    Features:
    - Image selection and preview
    - Receipt scanning with progress indication
    - Display of extracted data
    - Quality assessment
    - Error handling
    """

    def __init__(self, parent, config: AppConfig, on_receipt_scanned: Optional[Callable[[Dict[str, Any]], None]] = None):
        super().__init__(parent, relief="raised", borderwidth=1)
        self.config = config
        self.scanning_service = ReceiptScanningService(config)
        self.error_tracker = get_error_tracker()
        self.on_receipt_scanned = on_receipt_scanned

        self.current_image_path = None
        self.current_receipt_data = None
        self.scan_worker = None
        self.result_queue = queue.Queue()

        self.build_ui()
        self.setup_bindings()

    def build_ui(self):
        """Build the user interface"""
        # Main container with padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Receipt Scanner",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 10))

        # Create paned window for split layout
        paned = ttk.PanedWindow(main_frame, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # Left panel - Image selection and preview
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        self.build_image_panel(left_frame)

        # Right panel - Results and data
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)

        self.build_results_panel(right_frame)

        # Progress bar (initially hidden)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            mode='indeterminate'
        )
        self.progress_bar.pack(fill="x", pady=(5, 0))
        self.progress_bar.pack_forget()  # Hide initially

        # Status label
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            foreground="blue"
        )
        self.status_label.pack(anchor="w", pady=(5, 0))

    def build_image_panel(self, parent):
        """Build the image selection and preview panel"""
        # Image selection group
        image_frame = ttk.LabelFrame(parent, text="Receipt Image", padding="5")
        image_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Buttons
        button_frame = ttk.Frame(image_frame)
        button_frame.pack(fill="x", pady=(0, 10))

        self.select_button = ttk.Button(
            button_frame,
            text="Select Image",
            command=self.select_image
        )
        self.select_button.pack(side="left", padx=(0, 5))

        self.scan_button = ttk.Button(
            button_frame,
            text="Scan Receipt",
            command=self.scan_receipt,
            state="disabled"
        )
        self.scan_button.pack(side="left")

        # Image preview
        self.image_label = ttk.Label(
            image_frame,
            text="No image selected",
            background="lightgray"
        )
        self.image_label.pack(fill="both", expand=True, padx=5, pady=5)

        # Image info
        self.image_info_var = tk.StringVar()
        self.image_info_label = ttk.Label(
            image_frame,
            textvariable=self.image_info_var,
            justify="left"
        )
        self.image_info_label.pack(anchor="w", pady=(5, 0))

    def build_results_panel(self, parent):
        """Build the results display panel"""
        results_frame = ttk.LabelFrame(parent, text="Extracted Data", padding="5")
        results_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Create scrollable frame for results
        canvas = tk.Canvas(results_frame)
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Extracted data fields
        self.vendor_var = tk.StringVar()
        self.total_var = tk.StringVar()
        self.tax_var = tk.StringVar()
        self.date_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.confidence_var = tk.StringVar()

        self.create_data_field(scrollable_frame, "Vendor:", self.vendor_var)
        self.create_data_field(scrollable_frame, "Total Amount:", self.total_var)
        self.create_data_field(scrollable_frame, "Tax Amount:", self.tax_var)
        self.create_data_field(scrollable_frame, "Date:", self.date_var)
        self.create_data_field(scrollable_frame, "Category:", self.category_var)
        self.create_data_field(scrollable_frame, "Confidence:", self.confidence_var)

        # Raw text display
        ttk.Label(scrollable_frame, text="Raw OCR Text:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 5))

        self.raw_text = scrolledtext.ScrolledText(scrollable_frame, height=8, wrap=tk.WORD)
        self.raw_text.pack(fill="x", pady=(0, 10))
        self.raw_text.config(state="disabled")

        # Items section
        ttk.Label(scrollable_frame, text="Items:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 5))

        self.items_text = scrolledtext.ScrolledText(scrollable_frame, height=6, wrap=tk.WORD)
        self.items_text.pack(fill="x", pady=(0, 10))
        self.items_text.config(state="disabled")

        # Action buttons
        actions_frame = ttk.Frame(scrollable_frame)
        actions_frame.pack(fill="x", pady=(10, 0))

        self.save_button = ttk.Button(
            actions_frame,
            text="Save Data",
            command=self.save_receipt_data,
            state="disabled"
        )
        self.save_button.pack(side="left", padx=(0, 5))

        self.clear_button = ttk.Button(
            actions_frame,
            text="Clear",
            command=self.clear_data
        )
        self.clear_button.pack(side="left")

    def create_data_field(self, parent, label_text: str, text_var: tk.StringVar):
        """Create a labeled data field"""
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=2)

        label = ttk.Label(frame, text=label_text, width=15, anchor="w", font=("Arial", 10, "bold"))
        label.pack(side="left")

        value_label = ttk.Label(frame, textvariable=text_var, anchor="w")
        value_label.pack(side="left", fill="x", expand=True)

    def setup_bindings(self):
        """Setup event bindings and polling"""
        # Poll for scan results
        self.after(100, self.check_scan_results)

    def select_image(self):
        """Handle image selection"""
        filetypes = [
            ('Image files', '*.png *.jpg *.jpeg *.bmp *.tiff'),
            ('All files', '*.*')
        ]

        filename = filedialog.askopenfilename(
            title="Select Receipt Image",
            filetypes=filetypes
        )

        if filename:
            self.load_image(filename)

    def load_image(self, image_path: str):
        """Load and display the selected image"""
        try:
            self.current_image_path = image_path

            # Load image for display
            image = Image.open(image_path)

            # Resize to fit the label (max 300x400)
            image.thumbnail((300, 400), Image.Resampling.LANCZOS)

            # Convert to PhotoImage
            self.photo_image = ImageTk.PhotoImage(image)
            self.image_label.config(image=self.photo_image, text="")

            # Update image info
            file_size = os.path.getsize(image_path) / 1024  # KB
            self.image_info_var.set(
                f"File: {os.path.basename(image_path)}\n"
                f"Size: {file_size:.1f} KB"
            )

            # Enable scan button
            self.scan_button.config(state="normal")
            self.status_var.set("Image loaded. Ready to scan.")

        except Exception as e:
            self.error_tracker.track_error(e, "Image Loading")
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")

    def scan_receipt(self):
        """Start the receipt scanning process"""
        if not self.current_image_path:
            messagebox.showwarning("No Image", "Please select an image first.")
            return

        # Disable buttons during scanning
        self.scan_button.config(state="disabled")
        self.select_button.config(state="disabled")

        # Show progress
        self.progress_bar.pack(fill="x", pady=(5, 0))
        self.progress_bar.start()
        self.status_var.set("Scanning receipt...")

        # Start scanning in background thread
        self.result_queue = queue.Queue()
        self.scan_worker = ReceiptScanWorker(
            self.scanning_service,
            self.current_image_path,
            self.result_queue
        )
        self.scan_worker.start()

    def check_scan_results(self):
        """Check for completed scan results"""
        try:
            # Non-blocking check for results
            result = self.result_queue.get_nowait()
            self.on_scan_finished(result)
        except queue.Empty:
            pass

        # Continue polling
        self.after(100, self.check_scan_results)

    def on_scan_finished(self, result: ScanResult):
        """Handle scan completion"""
        # Hide progress
        self.progress_bar.stop()
        self.progress_bar.pack_forget()

        # Re-enable buttons
        self.scan_button.config(state="normal")
        self.select_button.config(state="normal")

        if result.success and result.receipt_data:
            self.display_receipt_data(result.receipt_data)
            self.save_button.config(state="normal")
            self.status_var.set(
                f"Scan completed successfully in {result.processing_time:.2f}s. "
                f"Quality: {result.image_quality_score:.1f}%"
            )
        else:
            self.status_var.set(f"Scan failed: {result.error_message}")
            messagebox.showwarning("Scan Failed", result.error_message or "Unknown error occurred")

        # Clean up worker
        self.scan_worker = None

    def display_receipt_data(self, receipt_data):
        """Display the extracted receipt data"""
        self.current_receipt_data = receipt_data

        # Update data fields
        self.vendor_var.set(receipt_data.vendor_name)
        self.total_var.set(f"${receipt_data.total_amount:.2f}")
        self.tax_var.set(f"${receipt_data.tax_amount:.2f}" if receipt_data.tax_amount else "Not found")
        self.date_var.set(receipt_data.date.strftime("%Y-%m-%d") if receipt_data.date else "Not found")
        self.category_var.set(receipt_data.category.title())
        self.confidence_var.set(f"{receipt_data.confidence_score:.1f}%")

        # Raw text
        self.raw_text.config(state="normal")
        self.raw_text.delete(1.0, tk.END)
        self.raw_text.insert(tk.END, receipt_data.raw_text)
        self.raw_text.config(state="disabled")

        # Items
        self.items_text.config(state="normal")
        self.items_text.delete(1.0, tk.END)
        if receipt_data.items:
            items_text = "\n".join([
                f"{item['description']}: ${item['price']:.2f}"
                for item in receipt_data.items
            ])
        else:
            items_text = "No items extracted"
        self.items_text.insert(tk.END, items_text)
        self.items_text.config(state="disabled")

    def save_receipt_data(self):
        """Save the extracted receipt data"""
        if self.current_receipt_data and self.on_receipt_scanned:
            self.on_receipt_scanned(self.current_receipt_data.to_dict())
            messagebox.showinfo("Saved", "Receipt data saved successfully!")

    def clear_data(self):
        """Clear all data and reset the widget"""
        self.current_image_path = None
        self.current_receipt_data = None

        # Clear image
        self.image_label.config(image="", text="No image selected")
        self.image_info_var.set("")

        # Clear data fields
        self.vendor_var.set("")
        self.total_var.set("")
        self.tax_var.set("")
        self.date_var.set("")
        self.category_var.set("")
        self.confidence_var.set("")

        # Clear text areas
        self.raw_text.config(state="normal")
        self.raw_text.delete(1.0, tk.END)
        self.raw_text.config(state="disabled")

        self.items_text.config(state="normal")
        self.items_text.delete(1.0, tk.END)
        self.items_text.config(state="disabled")

        # Reset buttons
        self.scan_button.config(state="disabled")
        self.save_button.config(state="disabled")
        self.status_var.set("")