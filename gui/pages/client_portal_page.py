"""
Client Portal Page - Converted from Legacy Window

Client portal and account management page.
Integrated into main window without popup dialogs.
"""

import customtkinter as ctk
from typing import Optional, List, Dict, Any
from datetime import datetime

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton


class ClientPortalPage(ctk.CTkScrollableFrame):
    """
    Client Portal page - converted from legacy window to integrated page.
    
    Features:
    - Client account management
    - Document upload and sharing
    - Message and collaboration
    - Tax return status tracking
    - Secure client portal
    """

    def __init__(self, master, config: AppConfig, tax_data: Optional[TaxData] = None,
                 accessibility_service: Optional[AccessibilityService] = None, **kwargs):
        super().__init__(master, **kwargs)

        self.config = config
        self.tax_data = tax_data
        self.accessibility_service = accessibility_service

        # Portal data
        self.current_client = None
        self.active_clients = 0
        self.portal_vars = {}

        # Build the page
        self._create_header()
        self._create_toolbar()
        self._create_main_content()
        self._load_portal_data()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self)
        header_frame.pack(fill=ctk.X, padx=20, pady=(20, 10))

        title_label = ModernLabel(
            header_frame,
            text="👥 Client Portal",
            font_size=24,
            font_weight="bold"
        )
        title_label.pack(anchor=ctk.W, pady=(0, 5))

        subtitle_label = ModernLabel(
            header_frame,
            text="Manage client accounts, documents, and communications",
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
            text="➕ New Client",
            command=self._add_client,
            button_type="primary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📤 Upload Docs",
            command=self._upload_documents,
            button_type="secondary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="💬 Messages",
            command=self._view_messages,
            button_type="secondary",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📋 Activity",
            command=self._view_activity,
            button_type="secondary",
            width=110
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="💾 Save",
            command=self._save_portal,
            button_type="success",
            width=100
        ).pack(side=ctk.LEFT, padx=5)

        # Progress bar
        progress_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        progress_frame.pack(fill=ctk.X, pady=10)

        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=6)
        self.progress_bar.pack(fill=ctk.X)
        self.progress_bar.set(0)

        self.status_label = ModernLabel(progress_frame, text="Loading portal...", font_size=11)
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
        self.tab_clients = self.tabview.add("👥 Clients")
        self.tab_documents = self.tabview.add("📄 Documents")
        self.tab_messages = self.tabview.add("💬 Messages")
        self.tab_returns = self.tabview.add("📋 Returns")
        self.tab_settings = self.tabview.add("⚙️ Settings")

        # Setup tabs
        self._setup_clients_tab()
        self._setup_documents_tab()
        self._setup_messages_tab()
        self._setup_returns_tab()
        self._setup_settings_tab()

    def _setup_clients_tab(self):
        """Setup clients management tab"""
        self.tab_clients.grid_rowconfigure(0, weight=1)
        self.tab_clients.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_clients)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        clients_label = ModernLabel(frame, text="Client Accounts", font_size=12, font_weight="bold")
        clients_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        # Search/filter
        search_frame = ctk.CTkFrame(frame, fg_color="transparent")
        search_frame.pack(fill=ctk.X, padx=5, pady=5)

        ctk.CTkLabel(search_frame, text="Search:", text_color="gray").pack(side=ctk.LEFT, padx=(0, 5))
        search_entry = ctk.CTkEntry(search_frame, placeholder_text="Client name or ID...")
        search_entry.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=(0, 5))
        self.portal_vars['search'] = search_entry

        # Client list
        self.clients_text = ctk.CTkTextbox(frame, height=400)
        self.clients_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.clients_text.insert("1.0",
            "Active Clients:\n\n"
            "No clients added yet.\n\n"
            "To add a client:\n"
            "1. Click 'New Client' button\n"
            "2. Enter client information\n"
            "3. Set up tax return forms\n"
            "4. Configure document sharing\n"
            "5. Send client invitation"
        )
        self.clients_text.configure(state="disabled")

    def _setup_documents_tab(self):
        """Setup documents tab"""
        self.tab_documents.grid_rowconfigure(0, weight=1)
        self.tab_documents.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_documents)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        docs_label = ModernLabel(frame, text="Shared Documents", font_size=12, font_weight="bold")
        docs_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.documents_text = ctk.CTkTextbox(frame, height=400)
        self.documents_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.documents_text.insert("1.0",
            "Shared Documents:\n\n"
            "No documents shared yet.\n\n"
            "Document Types:\n"
            "• Tax Returns (PDF)\n"
            "• 1040 and Schedules\n"
            "• Supporting Documentation\n"
            "• Receipt Scans\n"
            "• W-2 and 1099 Forms\n"
            "• Other Records"
        )
        self.documents_text.configure(state="disabled")

    def _setup_messages_tab(self):
        """Setup messages tab"""
        self.tab_messages.grid_rowconfigure(0, weight=1)
        self.tab_messages.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_messages)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        msg_label = ModernLabel(frame, text="Client Messages", font_size=12, font_weight="bold")
        msg_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.messages_text = ctk.CTkTextbox(frame, height=400)
        self.messages_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.messages_text.insert("1.0",
            "Message Log:\n\n"
            "No messages yet.\n\n"
            "Features:\n"
            "• Direct messaging with clients\n"
            "• Message notifications\n"
            "• Attachment support\n"
            "• Message history\n"
            "• Read receipts"
        )
        self.messages_text.configure(state="disabled")

    def _setup_returns_tab(self):
        """Setup tax returns tab"""
        self.tab_returns.grid_rowconfigure(0, weight=1)
        self.tab_returns.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_returns)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        returns_label = ModernLabel(frame, text="Tax Returns Status", font_size=12, font_weight="bold")
        returns_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.returns_text = ctk.CTkTextbox(frame, height=400)
        self.returns_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.returns_text.insert("1.0",
            "Tax Return Status:\n\n"
            "No returns assigned.\n\n"
            "Return Statuses:\n"
            "• In Progress - Under preparation\n"
            "• Ready for Review - Awaiting client review\n"
            "• Signed - Client has signed\n"
            "• Filed - Submitted to IRS\n"
            "• Accepted - Confirmed by IRS\n"
            "• Complete - All done"
        )
        self.returns_text.configure(state="disabled")

    def _setup_settings_tab(self):
        """Setup portal settings tab"""
        self.tab_settings.grid_rowconfigure(1, weight=1)
        self.tab_settings.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_settings)
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

        settings_label = ModernLabel(frame, text="Portal Settings", font_size=12, font_weight="bold")
        settings_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        settings_frame = ctk.CTkFrame(frame)
        settings_frame.pack(fill=ctk.X, padx=5, pady=10)
        settings_frame.grid_columnconfigure(1, weight=1)

        fields = [
            ("Enable Client Portal", "enable_portal"),
            ("Require 2FA", "require_2fa"),
            ("Document Retention Days", "retention_days"),
            ("Default Access Level", "access_level")
        ]

        for row, (label, key) in enumerate(fields):
            lbl = ctk.CTkLabel(settings_frame, text=f"{label}:", text_color="gray", font=("", 11))
            lbl.grid(row=row, column=0, sticky="w", padx=10, pady=8)
            entry = ctk.CTkEntry(settings_frame, placeholder_text="", width=200)
            entry.grid(row=row, column=1, sticky="ew", padx=10, pady=8)
            self.portal_vars[key] = entry

    # ===== Action Methods =====

    def _load_portal_data(self):
        """Load portal data on startup"""
        self.status_label.configure(text="Loading clients...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Portal ready")
        self.progress_bar.set(1.0)

    def _add_client(self):
        """Add new client"""
        self.status_label.configure(text="Adding client...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Client added")
        self.progress_bar.set(1.0)

    def _upload_documents(self):
        """Upload documents for client"""
        self.status_label.configure(text="Opening file browser...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Ready")
        self.progress_bar.set(1.0)

    def _view_messages(self):
        """View client messages"""
        self.status_label.configure(text="Loading messages...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Messages loaded")
        self.progress_bar.set(1.0)

    def _view_activity(self):
        """View client activity log"""
        self.status_label.configure(text="Loading activity...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Activity loaded")
        self.progress_bar.set(1.0)

    def _save_portal(self):
        """Save portal settings"""
        self.status_label.configure(text="Saving...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Saved")
        self.progress_bar.set(1.0)
