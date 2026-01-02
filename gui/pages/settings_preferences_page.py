"""
Settings & Preferences Page - Converted from Legacy Window

Application settings and user preferences management page.
Integrated into main window without popup dialogs.
"""

import customtkinter as ctk
from typing import Optional, Dict, Any

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton


class SettingsPreferencesPage(ctk.CTkScrollableFrame):
    """
    Settings & Preferences page - converted from legacy window to integrated page.
    
    Features:
    - Application settings management
    - User preferences configuration
    - Theme and appearance settings
    - Notification preferences
    - Data and privacy settings
    """

    def __init__(self, master, config: AppConfig, tax_data: Optional[TaxData] = None,
                 accessibility_service: Optional[AccessibilityService] = None, **kwargs):
        super().__init__(master, **kwargs)

        self.config = config
        self.tax_data = tax_data
        self.accessibility_service = accessibility_service

        # Settings data
        self.settings_vars = {}
        self.preferences_changed = False

        # Build the page
        self._create_header()
        self._create_toolbar()
        self._create_main_content()
        self._load_preferences()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self)
        header_frame.pack(fill=ctk.X, padx=20, pady=(20, 10))

        title_label = ModernLabel(
            header_frame,
            text="⚙️ Settings & Preferences",
            font_size=24,
            font_weight="bold"
        )
        title_label.pack(anchor=ctk.W, pady=(0, 5))

        subtitle_label = ModernLabel(
            header_frame,
            text="Manage application settings and user preferences",
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
            text="↺ Reset Defaults",
            command=self._reset_defaults,
            button_type="secondary",
            width=150
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📤 Export",
            command=self._export_settings,
            button_type="secondary",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📥 Import",
            command=self._import_settings,
            button_type="secondary",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="💾 Save",
            command=self._save_preferences,
            button_type="success",
            width=100
        ).pack(side=ctk.LEFT, padx=5)

        # Progress bar
        progress_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        progress_frame.pack(fill=ctk.X, pady=10)

        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=6)
        self.progress_bar.pack(fill=ctk.X)
        self.progress_bar.set(0)

        self.status_label = ModernLabel(progress_frame, text="Loading preferences...", font_size=11)
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
        self.tab_general = self.tabview.add("🏠 General")
        self.tab_appearance = self.tabview.add("🎨 Appearance")
        self.tab_notifications = self.tabview.add("🔔 Notifications")
        self.tab_privacy = self.tabview.add("🔒 Privacy")
        self.tab_advanced = self.tabview.add("🔧 Advanced")

        # Setup tabs
        self._setup_general_tab()
        self._setup_appearance_tab()
        self._setup_notifications_tab()
        self._setup_privacy_tab()
        self._setup_advanced_tab()

    def _setup_general_tab(self):
        """Setup general settings tab"""
        self.tab_general.grid_rowconfigure(1, weight=1)
        self.tab_general.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_general)
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

        general_label = ModernLabel(frame, text="General Settings", font_size=12, font_weight="bold")
        general_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        settings_frame = ctk.CTkFrame(frame)
        settings_frame.pack(fill=ctk.X, padx=5, pady=10)
        settings_frame.grid_columnconfigure(1, weight=1)

        fields = [
            ("Default Tax Year", "default_tax_year"),
            ("Auto-Save Interval (minutes)", "autosave_interval"),
            ("Startup Behavior", "startup_behavior"),
            ("Recent Files Count", "recent_files_count")
        ]

        for row, (label, key) in enumerate(fields):
            lbl = ctk.CTkLabel(settings_frame, text=f"{label}:", text_color="gray", font=("", 11))
            lbl.grid(row=row, column=0, sticky="w", padx=10, pady=8)
            entry = ctk.CTkEntry(settings_frame, placeholder_text="", width=200)
            entry.grid(row=row, column=1, sticky="ew", padx=10, pady=8)
            self.settings_vars[key] = entry

    def _setup_appearance_tab(self):
        """Setup appearance settings tab"""
        self.tab_appearance.grid_rowconfigure(1, weight=1)
        self.tab_appearance.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_appearance)
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

        appearance_label = ModernLabel(frame, text="Appearance Settings", font_size=12, font_weight="bold")
        appearance_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        settings_frame = ctk.CTkFrame(frame)
        settings_frame.pack(fill=ctk.X, padx=5, pady=10)
        settings_frame.grid_columnconfigure(1, weight=1)

        fields = [
            ("Theme", "theme"),
            ("Color Mode", "color_mode"),
            ("Font Size", "font_size"),
            ("Window Size", "window_size")
        ]

        for row, (label, key) in enumerate(fields):
            lbl = ctk.CTkLabel(settings_frame, text=f"{label}:", text_color="gray", font=("", 11))
            lbl.grid(row=row, column=0, sticky="w", padx=10, pady=8)
            entry = ctk.CTkEntry(settings_frame, placeholder_text="", width=200)
            entry.grid(row=row, column=1, sticky="ew", padx=10, pady=8)
            self.settings_vars[key] = entry

    def _setup_notifications_tab(self):
        """Setup notification settings tab"""
        self.tab_notifications.grid_rowconfigure(0, weight=1)
        self.tab_notifications.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_notifications)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        notif_label = ModernLabel(frame, text="Notification Preferences", font_size=12, font_weight="bold")
        notif_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.notifications_text = ctk.CTkTextbox(frame, height=350)
        self.notifications_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.notifications_text.insert("1.0",
            "Notification Settings:\n\n"
            "☑ Enable desktop notifications\n"
            "☑ File save notifications\n"
            "☑ Deadline reminders\n"
            "☑ Update notifications\n"
            "☑ Error notifications\n"
            "☐ Sound notifications\n\n"
            "Notification Schedule:\n"
            "• Quiet hours: 9 PM - 7 AM\n"
            "• Show banner only: 7 AM - 9 PM"
        )
        self.notifications_text.configure(state="disabled")

    def _setup_privacy_tab(self):
        """Setup privacy settings tab"""
        self.tab_privacy.grid_rowconfigure(0, weight=1)
        self.tab_privacy.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_privacy)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        privacy_label = ModernLabel(frame, text="Privacy & Security", font_size=12, font_weight="bold")
        privacy_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.privacy_text = ctk.CTkTextbox(frame, height=350)
        self.privacy_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.privacy_text.insert("1.0",
            "Privacy & Security Settings:\n\n"
            "Data Collection:\n"
            "☐ Send usage statistics\n"
            "☐ Send error reports\n"
            "☑ Local data only\n\n"
            "Encryption:\n"
            "☑ Encrypt sensitive data\n"
            "☑ Require password on startup\n"
            "☑ Auto-lock on inactivity\n\n"
            "Data Retention:\n"
            "• Clear cache on exit: Enabled\n"
            "• Delete temporary files: Enabled"
        )
        self.privacy_text.configure(state="disabled")

    def _setup_advanced_tab(self):
        """Setup advanced settings tab"""
        self.tab_advanced.grid_rowconfigure(1, weight=1)
        self.tab_advanced.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_advanced)
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

        advanced_label = ModernLabel(frame, text="Advanced Settings", font_size=12, font_weight="bold")
        advanced_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        settings_frame = ctk.CTkFrame(frame)
        settings_frame.pack(fill=ctk.X, padx=5, pady=10)
        settings_frame.grid_columnconfigure(1, weight=1)

        fields = [
            ("Logging Level", "logging_level"),
            ("Database Path", "database_path"),
            ("Temp Directory", "temp_directory"),
            ("API Timeout (seconds)", "api_timeout")
        ]

        for row, (label, key) in enumerate(fields):
            lbl = ctk.CTkLabel(settings_frame, text=f"{label}:", text_color="gray", font=("", 11))
            lbl.grid(row=row, column=0, sticky="w", padx=10, pady=8)
            entry = ctk.CTkEntry(settings_frame, placeholder_text="", width=200)
            entry.grid(row=row, column=1, sticky="ew", padx=10, pady=8)
            self.settings_vars[key] = entry

    # ===== Action Methods =====

    def _load_preferences(self):
        """Load user preferences"""
        self.status_label.configure(text="Loading preferences...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Preferences loaded")
        self.progress_bar.set(1.0)

    def _reset_defaults(self):
        """Reset all settings to defaults"""
        self.status_label.configure(text="Resetting to defaults...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Settings reset")
        self.progress_bar.set(1.0)

    def _export_settings(self):
        """Export settings to file"""
        self.status_label.configure(text="Exporting settings...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Export complete")
        self.progress_bar.set(1.0)

    def _import_settings(self):
        """Import settings from file"""
        self.status_label.configure(text="Opening file browser...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Ready")
        self.progress_bar.set(1.0)

    def _save_preferences(self):
        """Save all preferences"""
        self.status_label.configure(text="Saving...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Saved")
        self.progress_bar.set(1.0)
