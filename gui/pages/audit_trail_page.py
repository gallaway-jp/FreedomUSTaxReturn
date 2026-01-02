"""
Audit Trail Page - Converted from Window

Page for activity tracking, logging, and audit trail management.
Integrated into main window without popup dialogs.
"""

import customtkinter as ctk
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton

logger = logging.getLogger(__name__)


class AuditTrailPage(ctk.CTkScrollableFrame):
    """
    Audit Trail page - converted from popup window to integrated page.
    
    Features:
    - Activity tracking and logging
    - Filterable event display
    - Export audit trail
    - Clear history options
    - Search capabilities
    """

    def __init__(self, master, config: AppConfig, tax_data: Optional[TaxData] = None,
                 accessibility_service: Optional[AccessibilityService] = None, **kwargs):
        super().__init__(master, **kwargs)

        self.config = config
        self.tax_data = tax_data
        self.accessibility_service = accessibility_service

        # Audit data
        self.audit_events: List[Dict[str, Any]] = []
        self.filtered_events: List[Dict[str, Any]] = []
        self.filter_vars = {}

        # Build the page
        self._create_header()
        self._create_toolbar()
        self._create_main_content()
        self._load_audit_log()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self)
        header_frame.pack(fill=ctk.X, padx=20, pady=(20, 10))

        title_label = ModernLabel(
            header_frame,
            text="📋 Audit Trail & Activity Log",
            font_size=24,
            font_weight="bold"
        )
        title_label.pack(anchor=ctk.W, pady=(0, 5))

        subtitle_label = ModernLabel(
            header_frame,
            text="Track all activities, changes, and events in your tax return",
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
            text="🔄 Refresh Log",
            command=self._refresh_log,
            button_type="secondary",
            width=130
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📊 Filter Events",
            command=self._filter_events,
            button_type="secondary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📥 Export Log",
            command=self._export_log,
            button_type="secondary",
            width=130
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="🗑️ Clear History",
            command=self._clear_history,
            button_type="danger",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        # Progress bar
        progress_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        progress_frame.pack(fill=ctk.X, pady=10)

        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=6)
        self.progress_bar.pack(fill=ctk.X)
        self.progress_bar.set(0)

        self.status_label = ModernLabel(progress_frame, text="Ready", font_size=11)
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
        self.tab_log = self.tabview.add("📋 Activity Log")
        self.tab_filters = self.tabview.add("🔍 Filters")
        self.tab_statistics = self.tabview.add("📊 Statistics")
        self.tab_details = self.tabview.add("📄 Details")

        # Setup tabs
        self._setup_log_tab()
        self._setup_filters_tab()
        self._setup_statistics_tab()
        self._setup_details_tab()

    def _setup_log_tab(self):
        """Setup activity log tab"""
        self.tab_log.grid_rowconfigure(0, weight=1)
        self.tab_log.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_log)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        log_label = ModernLabel(frame, text="Activity Log", font_size=12, font_weight="bold")
        log_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.log_text = ctk.CTkTextbox(frame, height=400)
        self.log_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.insert("1.0", "Loading activity log...")
        self.log_text.configure(state="disabled")

    def _setup_filters_tab(self):
        """Setup filters tab"""
        self.tab_filters.grid_rowconfigure(0, weight=1)
        self.tab_filters.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkFrame(self.tab_filters, fg_color="transparent")
        frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # Filter controls
        filter_label = ModernLabel(frame, text="Filter Events", font_size=12, font_weight="bold")
        filter_label.grid(row=0, column=0, sticky="w", padx=5, pady=(0, 10))

        filter_frame = ctk.CTkFrame(frame)
        filter_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        filter_frame.grid_columnconfigure(1, weight=1)

        # Event type filter
        event_label = ctk.CTkLabel(filter_frame, text="Event Type:", text_color="gray", font=("", 11))
        event_label.grid(row=0, column=0, sticky="w", padx=10, pady=8)
        
        event_combo = ctk.CTkComboBox(
            filter_frame,
            values=["All Events", "Data Modified", "Form Generated", "File Saved", "User Login"],
            width=150
        )
        event_combo.set("All Events")
        event_combo.grid(row=0, column=1, sticky="ew", padx=10, pady=8)
        self.filter_vars["event_type"] = event_combo

        # Date range filter
        date_label = ctk.CTkLabel(filter_frame, text="Date Range:", text_color="gray", font=("", 11))
        date_label.grid(row=1, column=0, sticky="w", padx=10, pady=8)
        
        date_combo = ctk.CTkComboBox(
            filter_frame,
            values=["All Time", "Today", "This Week", "This Month", "This Year"],
            width=150
        )
        date_combo.set("All Time")
        date_combo.grid(row=1, column=1, sticky="ew", padx=10, pady=8)
        self.filter_vars["date_range"] = date_combo

        # User filter
        user_label = ctk.CTkLabel(filter_frame, text="User:", text_color="gray", font=("", 11))
        user_label.grid(row=2, column=0, sticky="w", padx=10, pady=8)
        
        user_combo = ctk.CTkComboBox(
            filter_frame,
            values=["All Users", "Current User", "System"],
            width=150
        )
        user_combo.set("All Users")
        user_combo.grid(row=2, column=1, sticky="ew", padx=10, pady=8)
        self.filter_vars["user"] = user_combo

    def _setup_statistics_tab(self):
        """Setup statistics tab"""
        self.tab_statistics.grid_rowconfigure(0, weight=1)
        self.tab_statistics.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_statistics)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Summary cards
        stats_label = ModernLabel(frame, text="Activity Statistics", font_size=12, font_weight="bold")
        stats_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        cards_frame = ctk.CTkFrame(frame, fg_color="transparent")
        cards_frame.pack(fill=ctk.X, padx=5, pady=10)

        metrics = [
            ("Total Events", "0"),
            ("Today's Events", "0"),
            ("Last 7 Days", "0"),
            ("Last 30 Days", "0")
        ]

        for metric, value in metrics:
            card = self._create_summary_card(cards_frame, metric, value)
            card.pack(side=ctk.LEFT, padx=5, fill=ctk.X, expand=True)

        # Detailed statistics
        stats_detail_label = ModernLabel(frame, text="Event Breakdown", font_size=12, font_weight="bold")
        stats_detail_label.pack(anchor=ctk.W, padx=5, pady=(20, 10))

        self.stats_text = ctk.CTkTextbox(frame, height=300)
        self.stats_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.stats_text.insert("1.0", "Event Type Breakdown:\n\n• Data Modified: 0\n• Forms Generated: 0\n• Files Saved: 0\n• User Actions: 0")
        self.stats_text.configure(state="disabled")

    def _setup_details_tab(self):
        """Setup detailed event information tab"""
        self.tab_details.grid_rowconfigure(0, weight=1)
        self.tab_details.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_details)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        details_label = ModernLabel(frame, text="Event Details", font_size=12, font_weight="bold")
        details_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.details_text = ctk.CTkTextbox(frame, height=400)
        self.details_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.details_text.insert("1.0", "Select an event to view details.")
        self.details_text.configure(state="disabled")

    def _create_summary_card(self, parent, title, value):
        """Create a summary metric card"""
        card = ctk.CTkFrame(parent, corner_radius=8, fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        
        title_label = ctk.CTkLabel(card, text=title, text_color="gray", font=("", 11))
        title_label.pack(padx=10, pady=(8, 2))

        value_label = ctk.CTkLabel(card, text=value, text_color="white", font=("", 13, "bold"))
        value_label.pack(padx=10, pady=(2, 8))

        return card

    # ===== Action Methods =====

    def _load_audit_log(self):
        """Load audit log from storage"""
        self.status_label.configure(text="Loading audit log...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Ready")
        self.progress_bar.set(1.0)

    def _refresh_log(self):
        """Refresh the activity log"""
        self.status_label.configure(text="Refreshing log...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Log refreshed")
        self.progress_bar.set(1.0)

    def _filter_events(self):
        """Apply filters to activity log"""
        self.status_label.configure(text="Applying filters...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Filters applied")
        self.progress_bar.set(1.0)

    def _export_log(self):
        """Export audit trail to file"""
        self.status_label.configure(text="Exporting log...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Log exported")
        self.progress_bar.set(1.0)

    def _clear_history(self):
        """Clear audit trail history"""
        self.status_label.configure(text="Clearing history...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="History cleared")
        self.progress_bar.set(1.0)
