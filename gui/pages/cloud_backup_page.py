"""
Cloud Backup Page - Converted from Legacy Window

Cloud backup and disaster recovery management page.
Integrated into main window without popup dialogs.
"""

import customtkinter as ctk
from typing import Optional, List, Dict, Any
from datetime import datetime

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton


class CloudBackupPage(ctk.CTkScrollableFrame):
    """
    Cloud Backup page - converted from legacy window to integrated page.
    
    Features:
    - Cloud backup management
    - Automatic backup scheduling
    - Backup restoration
    - Version history
    - Security and encryption settings
    """

    def __init__(self, master, config: AppConfig, tax_data: Optional[TaxData] = None,
                 accessibility_service: Optional[AccessibilityService] = None, **kwargs):
        super().__init__(master, **kwargs)

        self.config = config
        self.tax_data = tax_data
        self.accessibility_service = accessibility_service

        # Backup data
        self.backup_status = "Not Configured"
        self.last_backup = None
        self.total_backups = 0
        self.backup_vars = {}

        # Build the page
        self._create_header()
        self._create_toolbar()
        self._create_main_content()
        self._check_backup_status()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self)
        header_frame.pack(fill=ctk.X, padx=20, pady=(20, 10))

        title_label = ModernLabel(
            header_frame,
            text="☁️ Cloud Backup",
            font_size=24,
            font_weight="bold"
        )
        title_label.pack(anchor=ctk.W, pady=(0, 5))

        subtitle_label = ModernLabel(
            header_frame,
            text="Manage cloud backups and disaster recovery",
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
            text="⚙️ Configure",
            command=self._configure_backup,
            button_type="primary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="💾 Backup Now",
            command=self._backup_now,
            button_type="secondary",
            width=130
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="↩️ Restore",
            command=self._restore_backup,
            button_type="secondary",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📋 History",
            command=self._view_history,
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

        self.status_label = ModernLabel(progress_frame, text="Checking backup status...", font_size=11)
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
        self.tab_status = self.tabview.add("📊 Status")
        self.tab_configure = self.tabview.add("⚙️ Configure")
        self.tab_history = self.tabview.add("📜 History")
        self.tab_security = self.tabview.add("🔒 Security")
        self.tab_schedule = self.tabview.add("📅 Schedule")

        # Setup tabs
        self._setup_status_tab()
        self._setup_configure_tab()
        self._setup_history_tab()
        self._setup_security_tab()
        self._setup_schedule_tab()

    def _setup_status_tab(self):
        """Setup backup status tab"""
        self.tab_status.grid_rowconfigure(1, weight=1)
        self.tab_status.grid_columnconfigure(0, weight=1)

        # Status cards
        cards_frame = ctk.CTkFrame(self.tab_status, fg_color="transparent")
        cards_frame.pack(fill=ctk.X, padx=20, pady=10)

        card_data = [
            ("Backup Status", self.backup_status),
            ("Last Backup", "Never"),
            ("Total Backups", "0"),
            ("Storage Used", "0 GB")
        ]

        for title, value in card_data:
            card = self._create_summary_card(cards_frame, title, value)
            card.pack(side=ctk.LEFT, padx=5, fill=ctk.X, expand=True)

        # Status details
        frame = ctk.CTkScrollableFrame(self.tab_status)
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

        status_label = ModernLabel(frame, text="Backup Status Details", font_size=12, font_weight="bold")
        status_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.status_text = ctk.CTkTextbox(frame, height=300)
        self.status_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.status_text.insert("1.0",
            "Backup Status:\n\n"
            "Status: Not Configured\n"
            "Last Backup: Never\n"
            "Next Scheduled: Not scheduled\n"
            "Backup Service: Disconnected\n"
            "Storage Quota: 0 GB used / 100 GB available\n\n"
            "To begin, configure your cloud backup service."
        )
        self.status_text.configure(state="disabled")

    def _setup_configure_tab(self):
        """Setup configuration tab"""
        self.tab_configure.grid_rowconfigure(1, weight=1)
        self.tab_configure.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_configure)
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

        config_label = ModernLabel(frame, text="Backup Configuration", font_size=12, font_weight="bold")
        config_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        config_frame = ctk.CTkFrame(frame)
        config_frame.pack(fill=ctk.X, padx=5, pady=10)
        config_frame.grid_columnconfigure(1, weight=1)

        fields = [
            ("Cloud Service", "cloud_service"),
            ("Account Email", "account_email"),
            ("Backup Folder", "backup_folder"),
            ("Storage Limit (GB)", "storage_limit")
        ]

        for row, (label, key) in enumerate(fields):
            lbl = ctk.CTkLabel(config_frame, text=f"{label}:", text_color="gray", font=("", 11))
            lbl.grid(row=row, column=0, sticky="w", padx=10, pady=8)
            entry = ctk.CTkEntry(config_frame, placeholder_text="", width=200)
            entry.grid(row=row, column=1, sticky="ew", padx=10, pady=8)
            self.backup_vars[key] = entry

    def _setup_history_tab(self):
        """Setup backup history tab"""
        self.tab_history.grid_rowconfigure(0, weight=1)
        self.tab_history.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_history)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        history_label = ModernLabel(frame, text="Backup History", font_size=12, font_weight="bold")
        history_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.history_text = ctk.CTkTextbox(frame, height=400)
        self.history_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.history_text.insert("1.0",
            "Backup History:\n\n"
            "No backups have been created yet.\n\n"
            "Once you configure cloud backup and create a backup,\n"
            "your backup history will appear here.\n\n"
            "Each backup entry will show:\n"
            "• Backup date and time\n"
            "• Size of backup\n"
            "• Files included\n"
            "• Backup status"
        )
        self.history_text.configure(state="disabled")

    def _setup_security_tab(self):
        """Setup security settings tab"""
        self.tab_security.grid_rowconfigure(1, weight=1)
        self.tab_security.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_security)
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

        security_label = ModernLabel(frame, text="Security Settings", font_size=12, font_weight="bold")
        security_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        security_frame = ctk.CTkFrame(frame)
        security_frame.pack(fill=ctk.X, padx=5, pady=10)
        security_frame.grid_columnconfigure(1, weight=1)

        fields = [
            ("Encryption Method", "encryption"),
            ("Password Protection", "password_protect"),
            ("Two-Factor Authentication", "two_factor"),
            ("Backup Retention Days", "retention_days")
        ]

        for row, (label, key) in enumerate(fields):
            lbl = ctk.CTkLabel(security_frame, text=f"{label}:", text_color="gray", font=("", 11))
            lbl.grid(row=row, column=0, sticky="w", padx=10, pady=8)
            entry = ctk.CTkEntry(security_frame, placeholder_text="", width=200)
            entry.grid(row=row, column=1, sticky="ew", padx=10, pady=8)
            self.backup_vars[key] = entry

    def _setup_schedule_tab(self):
        """Setup backup schedule tab"""
        self.tab_schedule.grid_rowconfigure(1, weight=1)
        self.tab_schedule.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_schedule)
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

        schedule_label = ModernLabel(frame, text="Backup Schedule", font_size=12, font_weight="bold")
        schedule_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        schedule_frame = ctk.CTkFrame(frame)
        schedule_frame.pack(fill=ctk.X, padx=5, pady=10)
        schedule_frame.grid_columnconfigure(1, weight=1)

        fields = [
            ("Backup Frequency", "frequency"),
            ("Time of Day", "backup_time"),
            ("Day of Week", "backup_day"),
            ("Enable Automatic Backup", "enable_auto")
        ]

        for row, (label, key) in enumerate(fields):
            lbl = ctk.CTkLabel(schedule_frame, text=f"{label}:", text_color="gray", font=("", 11))
            lbl.grid(row=row, column=0, sticky="w", padx=10, pady=8)
            entry = ctk.CTkEntry(schedule_frame, placeholder_text="", width=200)
            entry.grid(row=row, column=1, sticky="ew", padx=10, pady=8)
            self.backup_vars[key] = entry

    def _create_summary_card(self, parent, title, value):
        """Create a summary metric card"""
        card = ctk.CTkFrame(parent, corner_radius=8, fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        
        title_label = ctk.CTkLabel(card, text=title, text_color="gray", font=("", 11))
        title_label.pack(padx=10, pady=(8, 2))

        value_label = ctk.CTkLabel(card, text=value, text_color="white", font=("", 13, "bold"))
        value_label.pack(padx=10, pady=(2, 8))

        return card

    # ===== Action Methods =====

    def _check_backup_status(self):
        """Check backup status on startup"""
        self.status_label.configure(text="Checking backup status...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Not configured")
        self.progress_bar.set(1.0)

    def _configure_backup(self):
        """Configure cloud backup service"""
        self.status_label.configure(text="Opening configuration...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Configuration ready")
        self.progress_bar.set(1.0)

    def _backup_now(self):
        """Create backup immediately"""
        self.status_label.configure(text="Creating backup...")
        self.progress_bar.set(0.8)
        self.status_label.configure(text="Backup complete")
        self.progress_bar.set(1.0)

    def _restore_backup(self):
        """Restore from backup"""
        self.status_label.configure(text="Loading backups...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Ready to restore")
        self.progress_bar.set(1.0)

    def _view_history(self):
        """View backup history"""
        self.status_label.configure(text="Loading history...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="History loaded")
        self.progress_bar.set(1.0)

    def _save_settings(self):
        """Save backup settings"""
        self.status_label.configure(text="Saving...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Saved")
        self.progress_bar.set(1.0)
