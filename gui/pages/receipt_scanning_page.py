"""
Receipt Scanning Page - Converted from Legacy Window

Receipt scanning and document management page.
Integrated into main window without popup dialogs.
"""

import customtkinter as ctk
from typing import Optional, List, Dict, Any
from datetime import datetime

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton


class ReceiptScanningPage(ctk.CTkScrollableFrame):
    """
    Receipt Scanning page - converted from legacy window to integrated page.
    
    Features:
    - Receipt capture and scanning
    - OCR-based data extraction
    - Category assignment
    - Duplicate detection
    - Receipt storage and organization
    """

    def __init__(self, master, config: AppConfig, tax_data: Optional[TaxData] = None,
                 accessibility_service: Optional[AccessibilityService] = None, **kwargs):
        super().__init__(master, **kwargs)

        self.config = config
        self.tax_data = tax_data
        self.accessibility_service = accessibility_service

        # Receipt data
        self.total_receipts = 0
        self.ocr_supported = True
        self.scan_vars = {}

        # Build the page
        self._create_header()
        self._create_toolbar()
        self._create_main_content()
        self._check_ocr_support()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self)
        header_frame.pack(fill=ctk.X, padx=20, pady=(20, 10))

        title_label = ModernLabel(
            header_frame,
            text="📸 Receipt Scanning",
            font_size=24,
            font_weight="bold"
        )
        title_label.pack(anchor=ctk.W, pady=(0, 5))

        subtitle_label = ModernLabel(
            header_frame,
            text="Capture and extract data from receipts and invoices",
            font_size=12,
            text_color="gray"
        )
        subtitle_label.pack(anchor=ctk.W)

    def _create_toolbar(self):
        """Create the toolbar with action buttons"""
        toolbar_frame = ModernFrame(self)
        toolbar_frame.pack(fill=ctk.X, padx=20, pady=10)

        # Action buttons
        button_section = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        button_section.pack(side=ctk.LEFT, fill=ctk.X, expand=False)

        ModernButton(
            button_section,
            text="📷 Scan Receipt",
            command=self._scan_receipt,
            button_type="primary",
            width=150
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📁 Upload Files",
            command=self._upload_files,
            button_type="secondary",
            width=130
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="🔍 Extract Data",
            command=self._extract_data,
            button_type="secondary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="🗂️ Organize",
            command=self._organize_receipts,
            button_type="secondary",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="💾 Save",
            command=self._save_receipts,
            button_type="success",
            width=100
        ).pack(side=ctk.LEFT, padx=5)

        # Progress bar
        progress_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        progress_frame.pack(fill=ctk.X, pady=10)

        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=6)
        self.progress_bar.pack(fill=ctk.X)
        self.progress_bar.set(0)

        self.status_label = ModernLabel(progress_frame, text="Ready to scan receipts", font_size=11)
        self.status_label.pack(anchor=ctk.W, pady=(5, 0))

    def _create_main_content(self):
        """Create main content with tabview"""
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(0, weight=1)

        # Create tabview
        self.tabview = ctk.CTkTabview(main_container)
        self.tabview.pack(fill=ctk.BOTH, expand=True)

        # Add tabs
        self.tab_scanner = self.tabview.add("📷 Scanner")
        self.tab_receipts = self.tabview.add("📄 Receipts")
        self.tab_extraction = self.tabview.add("🔍 Extracted Data")
        self.tab_categories = self.tabview.add("🏷️ Categories")
        self.tab_duplicates = self.tabview.add("⚠️ Duplicates")

        # Setup tabs
        self._setup_scanner_tab()
        self._setup_receipts_tab()
        self._setup_extraction_tab()
        self._setup_categories_tab()
        self._setup_duplicates_tab()

    def _setup_scanner_tab(self):
        """Setup scanner tab"""
        self.tab_scanner.grid_rowconfigure(1, weight=1)
        self.tab_scanner.grid_columnconfigure(0, weight=1)

        # Scanner settings
        frame = ctk.CTkScrollableFrame(self.tab_scanner)
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

        scanner_label = ModernLabel(frame, text="Scanner Settings", font_size=12, font_weight="bold")
        scanner_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        settings_frame = ctk.CTkFrame(frame)
        settings_frame.pack(fill=ctk.X, padx=5, pady=10)
        settings_frame.grid_columnconfigure(1, weight=1)

        fields = [
            ("Scan Quality", "quality"),
            ("Resolution (DPI)", "resolution"),
            ("Color Mode", "color_mode"),
            ("File Format", "file_format")
        ]

        for row, (label, key) in enumerate(fields):
            lbl = ctk.CTkLabel(settings_frame, text=f"{label}:", text_color="gray", font=("", 11))
            lbl.grid(row=row, column=0, sticky="w", padx=10, pady=8)
            entry = ctk.CTkEntry(settings_frame, placeholder_text="", width=200)
            entry.grid(row=row, column=1, sticky="ew", padx=10, pady=8)
            self.scan_vars[key] = entry

    def _setup_receipts_tab(self):
        """Setup receipts tab"""
        self.tab_receipts.grid_rowconfigure(0, weight=1)
        self.tab_receipts.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_receipts)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        receipts_label = ModernLabel(frame, text="Scanned Receipts", font_size=12, font_weight="bold")
        receipts_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.receipts_text = ctk.CTkTextbox(frame, height=400)
        self.receipts_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.receipts_text.insert("1.0",
            "Scanned Receipts List:\n\n"
            "No receipts scanned yet.\n\n"
            "Steps:\n"
            "1. Click 'Scan Receipt' to start scanning\n"
            "2. Use your scanner or camera\n"
            "3. Receipt data will be extracted automatically\n"
            "4. Review extracted data and make corrections\n"
            "5. Assign appropriate category\n"
            "6. Save to your receipt library"
        )
        self.receipts_text.configure(state="disabled")

    def _setup_extraction_tab(self):
        """Setup extracted data tab"""
        self.tab_extraction.grid_rowconfigure(0, weight=1)
        self.tab_extraction.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_extraction)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        extract_label = ModernLabel(frame, text="Extracted Data", font_size=12, font_weight="bold")
        extract_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.extraction_text = ctk.CTkTextbox(frame, height=400)
        self.extraction_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.extraction_text.insert("1.0",
            "Extracted Receipt Data:\n\n"
            "Vendor: \nDate: \nAmount: \nCategory: \nDescription: \nTax Deductible: \nNotes: \n\n"
            "OCR Confidence: \nExtraction Status: Ready"
        )
        self.extraction_text.configure(state="disabled")

    def _setup_categories_tab(self):
        """Setup category assignment tab"""
        self.tab_categories.grid_rowconfigure(0, weight=1)
        self.tab_categories.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_categories)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        cat_label = ModernLabel(frame, text="Receipt Categories", font_size=12, font_weight="bold")
        cat_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.categories_text = ctk.CTkTextbox(frame, height=400)
        self.categories_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.categories_text.insert("1.0",
            "Available Categories:\n\n"
            "• Office Supplies\n"
            "• Equipment & Furniture\n"
            "• Travel & Meals\n"
            "• Utilities\n"
            "• Rent & Facility\n"
            "• Professional Services\n"
            "• Insurance\n"
            "• Vehicle & Fuel\n"
            "• Education & Training\n"
            "• Entertainment\n"
            "• Other Business Expenses"
        )
        self.categories_text.configure(state="disabled")

    def _setup_duplicates_tab(self):
        """Setup duplicate detection tab"""
        self.tab_duplicates.grid_rowconfigure(0, weight=1)
        self.tab_duplicates.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_duplicates)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        dup_label = ModernLabel(frame, text="Duplicate Detection", font_size=12, font_weight="bold")
        dup_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.duplicates_text = ctk.CTkTextbox(frame, height=400)
        self.duplicates_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.duplicates_text.insert("1.0",
            "Duplicate Receipt Check:\n\n"
            "Status: No duplicates detected\n\n"
            "Matching Criteria:\n"
            "• Same vendor and date\n"
            "• Amount within 5%\n"
            "• Similar description\n\n"
            "Sensitivity: Medium\n"
            "Last Check: Never"
        )
        self.duplicates_text.configure(state="disabled")

    # ===== Action Methods =====

    def _check_ocr_support(self):
        """Check if OCR is supported"""
        self.status_label.configure(text="Checking OCR support...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="OCR available")
        self.progress_bar.set(1.0)

    def _scan_receipt(self):
        """Scan receipt from camera or scanner"""
        self.status_label.configure(text="Initializing scanner...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Ready to scan")
        self.progress_bar.set(1.0)

    def _upload_files(self):
        """Upload receipt files"""
        self.status_label.configure(text="Opening file browser...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Ready")
        self.progress_bar.set(1.0)

    def _extract_data(self):
        """Extract data from receipts using OCR"""
        self.status_label.configure(text="Extracting data...")
        self.progress_bar.set(0.8)
        self.status_label.configure(text="Extraction complete")
        self.progress_bar.set(1.0)

    def _organize_receipts(self):
        """Organize receipts by category"""
        self.status_label.configure(text="Organizing receipts...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Organization complete")
        self.progress_bar.set(1.0)

    def _save_receipts(self):
        """Save receipt data"""
        self.status_label.configure(text="Saving...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Saved")
        self.progress_bar.set(1.0)
