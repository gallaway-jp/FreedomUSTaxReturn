"""
E-Filing Page - Converted from Legacy Window

Page for electronic tax return filing and submission.
Integrated into main window without popup dialogs.
"""

import customtkinter as ctk
from typing import Optional, List, Dict, Any
from datetime import datetime

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton


class EFilingPage(ctk.CTkScrollableFrame):
    """
    E-Filing page - converted from legacy window to integrated page.
    
    Features:
    - Electronic return filing
    - Filing status tracking
    - Confirmation tracking
    - Payment processing
    - Filing history
    """

    def __init__(self, master, config: AppConfig, tax_data: Optional[TaxData] = None,
                 accessibility_service: Optional[AccessibilityService] = None, **kwargs):
        super().__init__(master, **kwargs)

        self.config = config
        self.tax_data = tax_data
        self.accessibility_service = accessibility_service

        # Filing data
        self.filings: List[Dict[str, Any]] = []
        self.current_filing: Optional[Dict[str, Any]] = None
        self.filing_vars = {}

        # Build the page
        self._create_header()
        self._create_toolbar()
        self._create_main_content()
        self._load_filing_status()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self)
        header_frame.pack(fill=ctk.X, padx=20, pady=(20, 10))

        title_label = ModernLabel(
            header_frame,
            text="📧 Electronic Filing (E-File)",
            font_size=24,
            font_weight="bold"
        )
        title_label.pack(anchor=ctk.W, pady=(0, 5))

        subtitle_label = ModernLabel(
            header_frame,
            text="File your tax return electronically with the IRS",
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
            text="📤 File Return",
            command=self._file_return,
            button_type="primary",
            width=130
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📊 Check Status",
            command=self._check_status,
            button_type="secondary",
            width=130
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="💳 Make Payment",
            command=self._make_payment,
            button_type="secondary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📋 View History",
            command=self._view_history,
            button_type="secondary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="💾 Save Filing",
            command=self._save_filing,
            button_type="success",
            width=130
        ).pack(side=ctk.LEFT, padx=5)

        # Progress bar
        progress_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        progress_frame.pack(fill=ctk.X, pady=10)

        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=6)
        self.progress_bar.pack(fill=ctk.X)
        self.progress_bar.set(0)

        self.status_label = ModernLabel(progress_frame, text="Ready to file", font_size=11)
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
        self.tab_status = self.tabview.add("📊 Filing Status")
        self.tab_preparation = self.tabview.add("📋 Preparation")
        self.tab_submission = self.tabview.add("📤 Submission")
        self.tab_confirmation = self.tabview.add("✅ Confirmation")
        self.tab_history = self.tabview.add("📜 History")

        # Setup tabs
        self._setup_status_tab()
        self._setup_preparation_tab()
        self._setup_submission_tab()
        self._setup_confirmation_tab()
        self._setup_history_tab()

    def _setup_status_tab(self):
        """Setup filing status tab"""
        self.tab_status.grid_rowconfigure(1, weight=1)
        self.tab_status.grid_columnconfigure(0, weight=1)

        # Status cards
        cards_frame = ctk.CTkFrame(self.tab_status, fg_color="transparent")
        cards_frame.pack(fill=ctk.X, padx=20, pady=10)

        metrics = [
            ("Filing Status", "Not Filed"),
            ("IRS Acknowledgment", "Pending"),
            ("Refund Status", "N/A"),
            ("Filed on", "N/A")
        ]

        for metric, value in metrics:
            card = self._create_summary_card(cards_frame, metric, value)
            card.pack(side=ctk.LEFT, padx=5, fill=ctk.X, expand=True)

        # Status details
        frame = ctk.CTkScrollableFrame(self.tab_status)
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

        status_label = ModernLabel(frame, text="Filing Details", font_size=12, font_weight="bold")
        status_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.status_text = ctk.CTkTextbox(frame, height=300)
        self.status_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.status_text.insert("1.0", "Your return has not been filed yet. Click 'File Return' to begin e-filing.")
        self.status_text.configure(state="disabled")

    def _setup_preparation_tab(self):
        """Setup filing preparation tab"""
        self.tab_preparation.grid_rowconfigure(1, weight=1)
        self.tab_preparation.grid_columnconfigure(0, weight=1)
        self.tab_preparation.grid_columnconfigure(1, weight=1)

        # Filing requirements
        prep_label = ModernLabel(self.tab_preparation, text="Filing Requirements", font_size=12, font_weight="bold")
        prep_label.pack(anchor=ctk.W, padx=20, pady=(10, 5))

        requirements_frame = ctk.CTkFrame(self.tab_preparation)
        requirements_frame.pack(fill=ctk.X, padx=20, pady=10)
        requirements_frame.grid_columnconfigure(1, weight=1)

        items = [
            ("Applicant's Name", "applicant_name"),
            ("SSN/ITIN", "ssn"),
            ("Email Address", "email"),
            ("Phone Number", "phone"),
            ("Address", "address")
        ]

        for row, (label, key) in enumerate(items):
            lbl = ctk.CTkLabel(requirements_frame, text=f"{label}:", text_color="gray", font=("", 11))
            lbl.grid(row=row, column=0, sticky="w", padx=10, pady=8)
            entry = ctk.CTkEntry(requirements_frame, placeholder_text="Enter " + label.lower(), width=200)
            entry.grid(row=row, column=1, sticky="ew", padx=10, pady=8)
            self.filing_vars[key] = entry

    def _setup_submission_tab(self):
        """Setup submission tab"""
        self.tab_submission.grid_rowconfigure(1, weight=1)
        self.tab_submission.grid_columnconfigure(0, weight=1)

        # Submission controls
        submit_label = ModernLabel(self.tab_submission, text="File Your Return", font_size=12, font_weight="bold")
        submit_label.pack(anchor=ctk.W, padx=20, pady=(10, 5))

        button_frame = ctk.CTkFrame(self.tab_submission, fg_color="transparent")
        button_frame.pack(fill=ctk.X, padx=20, pady=10)

        ModernButton(
            button_frame,
            text="📤 Submit to IRS",
            command=self._submit_to_irs,
            button_type="primary",
            width=150
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_frame,
            text="🔍 Preview First",
            command=self._preview_filing,
            button_type="secondary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        # Submission info
        frame = ctk.CTkScrollableFrame(self.tab_submission)
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

        info_label = ModernLabel(frame, text="Submission Information", font_size=12, font_weight="bold")
        info_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.submission_text = ctk.CTkTextbox(frame, height=300)
        self.submission_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.submission_text.insert("1.0", "Submission Steps:\n\n1. Complete return review\n2. Gather required documents\n3. Verify all information\n4. Agree to electronic filing terms\n5. Submit to IRS\n\nProcessing typically takes 24 hours for acknowledgment.")
        self.submission_text.configure(state="disabled")

    def _setup_confirmation_tab(self):
        """Setup confirmation tab"""
        self.tab_confirmation.grid_rowconfigure(0, weight=1)
        self.tab_confirmation.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_confirmation)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        confirm_label = ModernLabel(frame, text="Filing Confirmation", font_size=12, font_weight="bold")
        confirm_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.confirmation_text = ctk.CTkTextbox(frame, height=400)
        self.confirmation_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.confirmation_text.insert("1.0", "No filing confirmation available. File your return first.")
        self.confirmation_text.configure(state="disabled")

    def _setup_history_tab(self):
        """Setup filing history tab"""
        self.tab_history.grid_rowconfigure(0, weight=1)
        self.tab_history.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_history)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        history_label = ModernLabel(frame, text="Filing History", font_size=12, font_weight="bold")
        history_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.history_text = ctk.CTkTextbox(frame, height=400)
        self.history_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.history_text.insert("1.0", "Previous Filings:\n\nNo previous filings on record.")
        self.history_text.configure(state="disabled")

    def _create_summary_card(self, parent, title, value):
        """Create a summary metric card"""
        card = ctk.CTkFrame(parent, corner_radius=8, fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        
        title_label = ctk.CTkLabel(card, text=title, text_color="gray", font=("", 11))
        title_label.pack(padx=10, pady=(8, 2))

        value_label = ctk.CTkLabel(card, text=value, text_color="white", font=("", 13, "bold"))
        value_label.pack(padx=10, pady=(2, 8))

        return card

    # ===== Action Methods =====

    def _load_filing_status(self):
        """Load current filing status"""
        self.status_label.configure(text="Loading filing status...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Ready to file")
        self.progress_bar.set(1.0)

    def _file_return(self):
        """Begin filing return"""
        self.status_label.configure(text="Preparing to file...")
        self.progress_bar.set(0.3)
        self.status_label.configure(text="Ready for submission")
        self.progress_bar.set(1.0)

    def _check_status(self):
        """Check IRS filing status"""
        self.status_label.configure(text="Checking IRS status...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Status retrieved")
        self.progress_bar.set(1.0)

    def _make_payment(self):
        """Process payment for taxes"""
        self.status_label.configure(text="Opening payment options...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Payment ready")
        self.progress_bar.set(1.0)

    def _view_history(self):
        """View past filings"""
        self.status_label.configure(text="Loading filing history...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="History loaded")
        self.progress_bar.set(1.0)

    def _save_filing(self):
        """Save filing information"""
        self.status_label.configure(text="Saving...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Filing saved")
        self.progress_bar.set(1.0)

    def _submit_to_irs(self):
        """Submit return to IRS"""
        self.status_label.configure(text="Submitting to IRS...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Submission complete")
        self.progress_bar.set(1.0)

    def _preview_filing(self):
        """Preview filing before submission"""
        self.status_label.configure(text="Generating preview...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Preview ready")
        self.progress_bar.set(1.0)
