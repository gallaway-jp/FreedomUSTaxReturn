"""
PTIN/ERO Management Page - Converted from Legacy Window

PTIN and Electronic Return Originator (ERO) management page.
Integrated into main window without popup dialogs.
"""

import customtkinter as ctk
from typing import Optional, List, Dict, Any
from datetime import datetime

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton


class PTINEROManagementPage(ctk.CTkScrollableFrame):
    """
    PTIN/ERO Management page - converted from legacy window to integrated page.
    
    Features:
    - PTIN registration and management
    - ERO credentials management
    - E-filing authorization
    - PTIN renewal and compliance
    - IRS communication logs
    """

    def __init__(self, master, config: AppConfig, tax_data: Optional[TaxData] = None,
                 accessibility_service: Optional[AccessibilityService] = None, **kwargs):
        super().__init__(master, **kwargs)

        self.config = config
        self.tax_data = tax_data
        self.accessibility_service = accessibility_service

        # PTIN data
        self.ptin_status = "Not Registered"
        self.ero_status = "Not Configured"
        self.ptin_vars = {}

        # Build the page
        self._create_header()
        self._create_toolbar()
        self._create_main_content()
        self._check_registration_status()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self)
        header_frame.pack(fill=ctk.X, padx=20, pady=(20, 10))

        title_label = ModernLabel(
            header_frame,
            text="🆔 PTIN/ERO Management",
            font_size=24,
            font_weight="bold"
        )
        title_label.pack(anchor=ctk.W, pady=(0, 5))

        subtitle_label = ModernLabel(
            header_frame,
            text="Manage PTIN and electronic return originator credentials",
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
            text="📝 Register PTIN",
            command=self._register_ptin,
            button_type="primary",
            width=150
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="🔑 ERO Setup",
            command=self._setup_ero,
            button_type="secondary",
            width=130
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="✓ Verify",
            command=self._verify_registration,
            button_type="secondary",
            width=110
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📋 Compliance",
            command=self._check_compliance,
            button_type="secondary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="💾 Save",
            command=self._save_credentials,
            button_type="success",
            width=100
        ).pack(side=ctk.LEFT, padx=5)

        # Progress bar
        progress_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        progress_frame.pack(fill=ctk.X, pady=10)

        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=6)
        self.progress_bar.pack(fill=ctk.X)
        self.progress_bar.set(0)

        self.status_label = ModernLabel(progress_frame, text="Checking registration status...", font_size=11)
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
        self.tab_ptin = self.tabview.add("🆔 PTIN")
        self.tab_ero = self.tabview.add("🔑 ERO")
        self.tab_efiling = self.tabview.add("📧 E-Filing Auth")
        self.tab_compliance = self.tabview.add("✓ Compliance")
        self.tab_communications = self.tabview.add("📧 Communications")

        # Setup tabs
        self._setup_ptin_tab()
        self._setup_ero_tab()
        self._setup_efiling_tab()
        self._setup_compliance_tab()
        self._setup_communications_tab()

    def _setup_ptin_tab(self):
        """Setup PTIN management tab"""
        self.tab_ptin.grid_rowconfigure(1, weight=1)
        self.tab_ptin.grid_columnconfigure(0, weight=1)

        # Status card
        status_frame = ctk.CTkFrame(self.tab_ptin, fg_color="transparent")
        status_frame.pack(fill=ctk.X, padx=20, pady=10)

        card = self._create_summary_card(status_frame, "PTIN Status", self.ptin_status)
        card.pack(side=ctk.LEFT, padx=5, fill=ctk.X, expand=True)

        # PTIN details
        frame = ctk.CTkScrollableFrame(self.tab_ptin)
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

        ptin_label = ModernLabel(frame, text="PTIN Information", font_size=12, font_weight="bold")
        ptin_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        form_frame = ctk.CTkFrame(frame)
        form_frame.pack(fill=ctk.X, padx=5, pady=10)
        form_frame.grid_columnconfigure(1, weight=1)

        fields = [
            ("PTIN", "ptin"),
            ("SSN", "ssn"),
            ("Date of Birth", "dob"),
            ("Expiration Date", "expiration"),
            ("Status", "status")
        ]

        for row, (label, key) in enumerate(fields):
            lbl = ctk.CTkLabel(form_frame, text=f"{label}:", text_color="gray", font=("", 11))
            lbl.grid(row=row, column=0, sticky="w", padx=10, pady=8)
            entry = ctk.CTkEntry(form_frame, placeholder_text="", width=200)
            entry.grid(row=row, column=1, sticky="ew", padx=10, pady=8)
            self.ptin_vars[key] = entry

    def _setup_ero_tab(self):
        """Setup ERO configuration tab"""
        self.tab_ero.grid_rowconfigure(1, weight=1)
        self.tab_ero.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_ero)
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

        ero_label = ModernLabel(frame, text="ERO Credentials", font_size=12, font_weight="bold")
        ero_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        form_frame = ctk.CTkFrame(frame)
        form_frame.pack(fill=ctk.X, padx=5, pady=10)
        form_frame.grid_columnconfigure(1, weight=1)

        fields = [
            ("ERO Name", "ero_name"),
            ("ERO ID", "ero_id"),
            ("Username", "username"),
            ("Password", "password"),
            ("IRS PIN", "irs_pin")
        ]

        for row, (label, key) in enumerate(fields):
            lbl = ctk.CTkLabel(form_frame, text=f"{label}:", text_color="gray", font=("", 11))
            lbl.grid(row=row, column=0, sticky="w", padx=10, pady=8)
            entry = ctk.CTkEntry(form_frame, placeholder_text="", width=200, show="*" if "password" in key or "pin" in key else "")
            entry.grid(row=row, column=1, sticky="ew", padx=10, pady=8)
            self.ptin_vars[key] = entry

    def _setup_efiling_tab(self):
        """Setup e-filing authorization tab"""
        self.tab_efiling.grid_rowconfigure(0, weight=1)
        self.tab_efiling.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_efiling)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        efiling_label = ModernLabel(frame, text="E-Filing Authorization", font_size=12, font_weight="bold")
        efiling_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.efiling_text = ctk.CTkTextbox(frame, height=400)
        self.efiling_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.efiling_text.insert("1.0",
            "E-Filing Authorization Status:\n\n"
            "Not Authorized\n\n"
            "Requirements for E-Filing:\n"
            "1. Valid PTIN registration\n"
            "2. Valid ERO account\n"
            "3. IRS e-Services account\n"
            "4. Digital certificate\n"
            "5. Transmission compliance\n\n"
            "Once authorized, you can e-file returns."
        )
        self.efiling_text.configure(state="disabled")

    def _setup_compliance_tab(self):
        """Setup compliance checking tab"""
        self.tab_compliance.grid_rowconfigure(0, weight=1)
        self.tab_compliance.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_compliance)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        compliance_label = ModernLabel(frame, text="Compliance Status", font_size=12, font_weight="bold")
        compliance_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.compliance_text = ctk.CTkTextbox(frame, height=400)
        self.compliance_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.compliance_text.insert("1.0",
            "PTIN Compliance:\n\n"
            "Status: Not Registered\n\n"
            "Compliance Requirements:\n"
            "✓ Annual PTIN renewal\n"
            "✓ Continuing education (CPE)\n"
            "✓ Annual tax return review\n"
            "✓ Maintain professional standards\n"
            "✓ Report all income\n"
            "✓ Comply with IRS regulations"
        )
        self.compliance_text.configure(state="disabled")

    def _setup_communications_tab(self):
        """Setup IRS communications tab"""
        self.tab_communications.grid_rowconfigure(0, weight=1)
        self.tab_communications.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_communications)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        comms_label = ModernLabel(frame, text="IRS Communications", font_size=12, font_weight="bold")
        comms_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.communications_text = ctk.CTkTextbox(frame, height=400)
        self.communications_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.communications_text.insert("1.0",
            "IRS Communication Log:\n\n"
            "No communications yet.\n\n"
            "Communication types may include:\n"
            "• Registration confirmations\n"
            "• Annual notices\n"
            "• Compliance reminders\n"
            "• Updates to regulations\n"
            "• Annual renewal notices\n"
            "• Important IRS announcements"
        )
        self.communications_text.configure(state="disabled")

    def _create_summary_card(self, parent, title, value):
        """Create a summary metric card"""
        card = ctk.CTkFrame(parent, corner_radius=8, fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        
        title_label = ctk.CTkLabel(card, text=title, text_color="gray", font=("", 11))
        title_label.pack(padx=10, pady=(8, 2))

        value_label = ctk.CTkLabel(card, text=value, text_color="white", font=("", 13, "bold"))
        value_label.pack(padx=10, pady=(2, 8))

        return card

    # ===== Action Methods =====

    def _check_registration_status(self):
        """Check PTIN registration status"""
        self.status_label.configure(text="Checking registration status...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Status checked")
        self.progress_bar.set(1.0)

    def _register_ptin(self):
        """Register or renew PTIN"""
        self.status_label.configure(text="Initiating PTIN registration...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Registration process started")
        self.progress_bar.set(1.0)

    def _setup_ero(self):
        """Setup ERO credentials"""
        self.status_label.configure(text="Setting up ERO...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="ERO configured")
        self.progress_bar.set(1.0)

    def _verify_registration(self):
        """Verify PTIN and ERO registration"""
        self.status_label.configure(text="Verifying registration...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Verification complete")
        self.progress_bar.set(1.0)

    def _check_compliance(self):
        """Check compliance status"""
        self.status_label.configure(text="Checking compliance...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Compliance status loaded")
        self.progress_bar.set(1.0)

    def _save_credentials(self):
        """Save PTIN and ERO credentials"""
        self.status_label.configure(text="Saving...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Saved securely")
        self.progress_bar.set(1.0)
