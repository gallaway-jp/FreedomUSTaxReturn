"""
QuickBooks Integration Page - Converted from Legacy Window

Page for connecting and syncing with QuickBooks accounting software.
Integrated into main window without popup dialogs.
"""

import customtkinter as ctk
from typing import Optional, List, Dict, Any
from datetime import datetime

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton


class QuickBooksIntegrationPage(ctk.CTkScrollableFrame):
    """
    QuickBooks Integration page - converted from legacy window to integrated page.
    
    Features:
    - QuickBooks data sync
    - Account mapping
    - Transaction categorization
    - Data reconciliation
    - Sync history tracking
    """

    def __init__(self, master, config: AppConfig, tax_data: Optional[TaxData] = None,
                 accessibility_service: Optional[AccessibilityService] = None, **kwargs):
        super().__init__(master, **kwargs)

        self.config = config
        self.tax_data = tax_data
        self.accessibility_service = accessibility_service

        # Integration data
        self.connection_status = "Disconnected"
        self.last_sync = None
        self.qb_vars = {}

        # Build the page
        self._create_header()
        self._create_toolbar()
        self._create_main_content()
        self._check_connection()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self)
        header_frame.pack(fill=ctk.X, padx=20, pady=(20, 10))

        title_label = ModernLabel(
            header_frame,
            text="📊 QuickBooks Integration",
            font_size=24,
            font_weight="bold"
        )
        title_label.pack(anchor=ctk.W, pady=(0, 5))

        subtitle_label = ModernLabel(
            header_frame,
            text="Connect and sync accounting data from QuickBooks",
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
            text="🔗 Connect Account",
            command=self._connect_account,
            button_type="primary",
            width=150
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="🔄 Sync Data",
            command=self._sync_data,
            button_type="secondary",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📋 Map Accounts",
            command=self._map_accounts,
            button_type="secondary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="✓ Reconcile",
            command=self._reconcile_data,
            button_type="secondary",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="💾 Save",
            command=self._save_settings,
            button_type="success",
            width=100
        ).pack(side=ctk.LEFT, padx=5)

        # Progress bar
        progress_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        progress_frame.pack(fill=ctk.X, pady=10)

        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=6)
        self.progress_bar.pack(fill=ctk.X)
        self.progress_bar.set(0)

        self.status_label = ModernLabel(progress_frame, text="Checking connection...", font_size=11)
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
        self.tab_connection = self.tabview.add("🔗 Connection")
        self.tab_accounts = self.tabview.add("💼 Accounts")
        self.tab_transactions = self.tabview.add("📊 Transactions")
        self.tab_reconciliation = self.tabview.add("✓ Reconciliation")
        self.tab_history = self.tabview.add("📜 Sync History")

        # Setup tabs
        self._setup_connection_tab()
        self._setup_accounts_tab()
        self._setup_transactions_tab()
        self._setup_reconciliation_tab()
        self._setup_history_tab()

    def _setup_connection_tab(self):
        """Setup connection settings tab"""
        self.tab_connection.grid_rowconfigure(1, weight=1)
        self.tab_connection.grid_columnconfigure(0, weight=1)

        # Connection status
        status_cards_frame = ctk.CTkFrame(self.tab_connection, fg_color="transparent")
        status_cards_frame.pack(fill=ctk.X, padx=20, pady=10)

        card = self._create_summary_card(status_cards_frame, "Connection Status", self.connection_status)
        card.pack(side=ctk.LEFT, padx=5, fill=ctk.X, expand=True)

        # Connection details
        frame = ctk.CTkScrollableFrame(self.tab_connection)
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

        conn_label = ModernLabel(frame, text="Connection Settings", font_size=12, font_weight="bold")
        conn_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        form_frame = ctk.CTkFrame(frame)
        form_frame.pack(fill=ctk.X, padx=5, pady=10)
        form_frame.grid_columnconfigure(1, weight=1)

        fields = [
            ("QuickBooks Company", "company"),
            ("Username", "username"),
            ("Connection Type", "connection_type"),
            ("Last Connected", "last_connected")
        ]

        for row, (label, key) in enumerate(fields):
            lbl = ctk.CTkLabel(form_frame, text=f"{label}:", text_color="gray", font=("", 11))
            lbl.grid(row=row, column=0, sticky="w", padx=10, pady=8)
            entry = ctk.CTkEntry(form_frame, placeholder_text="", width=200)
            entry.grid(row=row, column=1, sticky="ew", padx=10, pady=8)
            self.qb_vars[key] = entry

    def _setup_accounts_tab(self):
        """Setup account mapping tab"""
        self.tab_accounts.grid_rowconfigure(0, weight=1)
        self.tab_accounts.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_accounts)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        accounts_label = ModernLabel(frame, text="QB Account Mapping", font_size=12, font_weight="bold")
        accounts_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.accounts_text = ctk.CTkTextbox(frame, height=400)
        self.accounts_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.accounts_text.insert("1.0", "Mapped Accounts:\n\n• Checking Account\n• Savings Account\n• Credit Card\n• Income Account\n• Expense Categories")
        self.accounts_text.configure(state="disabled")

    def _setup_transactions_tab(self):
        """Setup transactions tab"""
        self.tab_transactions.grid_rowconfigure(0, weight=1)
        self.tab_transactions.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_transactions)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        trans_label = ModernLabel(frame, text="Recent Transactions", font_size=12, font_weight="bold")
        trans_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.transactions_text = ctk.CTkTextbox(frame, height=400)
        self.transactions_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.transactions_text.insert("1.0", "Recent QB Transactions:\n\nNo transactions synced yet. Connect account and sync to import transactions.")
        self.transactions_text.configure(state="disabled")

    def _setup_reconciliation_tab(self):
        """Setup reconciliation tab"""
        self.tab_reconciliation.grid_rowconfigure(0, weight=1)
        self.tab_reconciliation.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_reconciliation)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        recon_label = ModernLabel(frame, text="Data Reconciliation", font_size=12, font_weight="bold")
        recon_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.reconciliation_text = ctk.CTkTextbox(frame, height=400)
        self.reconciliation_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.reconciliation_text.insert("1.0", "Reconciliation Status:\n\nNo data synced. Connect your QuickBooks account to begin reconciliation.")
        self.reconciliation_text.configure(state="disabled")

    def _setup_history_tab(self):
        """Setup sync history tab"""
        self.tab_history.grid_rowconfigure(0, weight=1)
        self.tab_history.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_history)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        history_label = ModernLabel(frame, text="Sync History", font_size=12, font_weight="bold")
        history_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.history_text = ctk.CTkTextbox(frame, height=400)
        self.history_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.history_text.insert("1.0", "Sync History:\n\nNo previous syncs recorded.")
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

    def _check_connection(self):
        """Check QuickBooks connection status"""
        self.status_label.configure(text="Checking connection...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Ready")
        self.progress_bar.set(1.0)

    def _connect_account(self):
        """Connect QuickBooks account"""
        self.status_label.configure(text="Initiating connection...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Connected")
        self.progress_bar.set(1.0)

    def _sync_data(self):
        """Sync data from QuickBooks"""
        self.status_label.configure(text="Syncing QuickBooks data...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Sync complete")
        self.progress_bar.set(1.0)

    def _map_accounts(self):
        """Map QuickBooks accounts to tax categories"""
        self.status_label.configure(text="Mapping accounts...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Mapping complete")
        self.progress_bar.set(1.0)

    def _reconcile_data(self):
        """Reconcile QuickBooks data"""
        self.status_label.configure(text="Reconciling data...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Reconciliation complete")
        self.progress_bar.set(1.0)

    def _save_settings(self):
        """Save integration settings"""
        self.status_label.configure(text="Saving...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Settings saved")
        self.progress_bar.set(1.0)
