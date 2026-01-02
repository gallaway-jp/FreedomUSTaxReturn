"""
Modern Audit Trail Page - CustomTkinter-based audit trail viewer

Provides a comprehensive view of system activities with filtering and export capabilities.
"""

import customtkinter as ctk
from typing import Optional, Callable, List, Dict, Any
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import csv

from services.audit_trail_service import AuditTrailService, AuditEntry
from gui.modern_ui_components import (
    ModernFrame, ModernLabel, ModernButton, ModernEntry,
    show_info_message, show_error_message
)


class ModernAuditTrailPage(ctk.CTkScrollableFrame):
    """
    Modern audit trail page showing system activity history.

    Features:
    - View audit trail entries with timestamp, action, and entity information
    - Filter by date range, entity type, and action
    - Export audit data to CSV
    - Search functionality
    - Real-time updates
    """

    def __init__(
        self,
        parent,
        audit_service: AuditTrailService,
        **kwargs
    ):
        """
        Initialize the audit trail page.

        Args:
            parent: Parent widget
            audit_service: Audit trail service instance
        """
        super().__init__(parent, **kwargs)

        self.audit_service = audit_service
        self.current_entries: List[AuditEntry] = []
        self.filtered_entries: List[AuditEntry] = []

        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Create UI
        self._create_header()
        self._create_filters()
        self._create_tree_view()

        # Load data
        self._load_audit_data()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        title_label = ModernLabel(
            header_frame,
            text="Audit Trail - System Activity Log",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(anchor="w")

        subtitle_label = ModernLabel(
            header_frame,
            text="View all system activities and changes to your tax return",
            font=ctk.CTkFont(size=12),
            text_color="gray60"
        )
        subtitle_label.pack(anchor="w", pady=(5, 0))

    def _create_filters(self):
        """Create the filters section"""
        filter_frame = ModernFrame(self)
        filter_frame.pack(fill="x", padx=20, pady=10)

        filter_title = ModernLabel(
            filter_frame,
            text="🔍 Filters",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        filter_title.pack(anchor="w", pady=(0, 10))

        # Filter controls frame
        controls_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        controls_frame.pack(fill="x")

        # Date range filters
        date_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        date_frame.pack(fill="x", pady=(0, 10))

        ModernLabel(date_frame, text="From Date:").pack(side="left", padx=(0, 5))
        self.from_date_entry = ctk.CTkEntry(date_frame, placeholder_text="YYYY-MM-DD", width=120)
        self.from_date_entry.pack(side="left", padx=(0, 15))

        ModernLabel(date_frame, text="To Date:").pack(side="left", padx=(0, 5))
        self.to_date_entry = ctk.CTkEntry(date_frame, placeholder_text="YYYY-MM-DD", width=120)
        self.to_date_entry.pack(side="left", padx=(0, 15))

        # Entity type and action filters
        filter_row2 = ctk.CTkFrame(controls_frame, fg_color="transparent")
        filter_row2.pack(fill="x", pady=(0, 10))

        ModernLabel(filter_row2, text="Entity Type:").pack(side="left", padx=(0, 5))
        self.entity_type_combo = ctk.CTkComboBox(
            filter_row2,
            values=["All", "personal_info", "filing_status", "income", "deductions", "credits", "payments", "calculation"],
            width=130
        )
        self.entity_type_combo.set("All")
        self.entity_type_combo.pack(side="left", padx=(0, 15))

        ModernLabel(filter_row2, text="Action:").pack(side="left", padx=(0, 5))
        self.action_combo = ctk.CTkComboBox(
            filter_row2,
            values=["All", "CREATE", "UPDATE", "DELETE", "CALCULATE", "SESSION_START", "SESSION_END"],
            width=120
        )
        self.action_combo.set("All")
        self.action_combo.pack(side="left", padx=(0, 15))

        # Buttons
        button_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        ModernButton(
            button_frame,
            text="Apply Filters",
            command=self._apply_filters,
            height=32,
            width=100
        ).pack(side="left", padx=(0, 5))

        ModernButton(
            button_frame,
            text="Clear Filters",
            command=self._clear_filters,
            height=32,
            width=100
        ).pack(side="left", padx=(0, 5))

        ModernButton(
            button_frame,
            text="Export to CSV",
            command=self._export_audit,
            height=32,
            width=100
        ).pack(side="left", padx=(0, 5))

        ModernButton(
            button_frame,
            text="Clear All Data",
            command=self._clear_all_audit_data,
            button_type="danger",
            height=32,
            width=120
        ).pack(side="left")

    def _create_tree_view(self):
        """Create the audit entries display using CustomTkinter textbox"""
        tree_frame = ModernFrame(self)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        tree_title = ModernLabel(
            tree_frame,
            text="📋 Audit Entries",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        tree_title.pack(anchor="w", pady=(0, 10))

        # Use CustomTkinter textbox instead of ttk.Treeview for proper theming
        self.audit_textbox = ctk.CTkTextbox(tree_frame, height=400, wrap="none")
        self.audit_textbox.pack(fill="both", expand=True)

        # Make it read-only
        self.audit_textbox.configure(state="disabled")

    def _load_audit_data(self):
        """Load audit trail data from service"""
        try:
            # Get all audit entries (limit to last 1000 entries)
            self.current_entries = self.audit_service.get_audit_history(limit=1000)
            self._refresh_tree_view()
        except Exception as e:
            show_error_message("Audit Trail Error", f"Failed to load audit data: {str(e)}")

    def _refresh_tree_view(self):
        """Refresh the textbox display with current entries"""
        # Enable textbox for editing
        self.audit_textbox.configure(state="normal")
        self.audit_textbox.delete("0.0", "end")

        # Add entries from filtered list or all entries if no filter applied
        entries_to_display = self.filtered_entries if self.filtered_entries else self.current_entries

        if not entries_to_display:
            self.audit_textbox.insert("0.0", "No audit entries found.")
            self.audit_textbox.configure(state="disabled")
            return

        # Add header
        header = f"{'Timestamp':<20} {'Action':<12} {'Entity Type':<15} {'Entity ID':<15} {'Field':<15} {'Old Value':<20} {'New Value':<20}\n"
        header += "=" * 120 + "\n"
        self.audit_textbox.insert("0.0", header)

        # Add entries
        for i, entry in enumerate(entries_to_display):
            timestamp_str = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S") if hasattr(entry.timestamp, 'strftime') else str(entry.timestamp)
            old_val = self._truncate_value(entry.old_value, 17)
            new_val = self._truncate_value(entry.new_value, 17)

            line = ("02d")

            self.audit_textbox.insert("end", line)

        # Make textbox read-only again
        self.audit_textbox.configure(state="disabled")

    def _truncate_value(self, value: Any, max_length: int = 50) -> str:
        """Truncate long values for display"""
        if value is None:
            return ""
        str_value = str(value)
        if len(str_value) > max_length:
            return str_value[:max_length] + "..."
        return str_value

    def _apply_filters(self):
        """Apply filters to the audit entries"""
        try:
            self.filtered_entries = self.current_entries.copy()

            # Filter by date range
            from_date_str = self.from_date_entry.get().strip()
            to_date_str = self.to_date_entry.get().strip()

            if from_date_str:
                from_date = datetime.strptime(from_date_str, "%Y-%m-%d")
                self.filtered_entries = [
                    e for e in self.filtered_entries
                    if (hasattr(e.timestamp, 'date') and e.timestamp.date() >= from_date.date())
                       or (isinstance(e.timestamp, str) and e.timestamp[:10] >= from_date_str)
                ]

            if to_date_str:
                to_date = datetime.strptime(to_date_str, "%Y-%m-%d")
                self.filtered_entries = [
                    e for e in self.filtered_entries
                    if (hasattr(e.timestamp, 'date') and e.timestamp.date() <= to_date.date())
                       or (isinstance(e.timestamp, str) and e.timestamp[:10] <= to_date_str)
                ]

            # Filter by entity type
            entity_type = self.entity_type_combo.get()
            if entity_type != "All":
                self.filtered_entries = [e for e in self.filtered_entries if e.entity_type == entity_type]

            # Filter by action
            action = self.action_combo.get()
            if action != "All":
                self.filtered_entries = [e for e in self.filtered_entries if e.action == action]

            self._refresh_tree_view()
            show_info_message("Filters Applied", f"Found {len(self.filtered_entries)} matching entries")

        except ValueError as e:
            show_error_message("Filter Error", f"Invalid date format. Use YYYY-MM-DD: {str(e)}")

    def _clear_filters(self):
        """Clear all filters"""
        self.from_date_entry.delete(0, "end")
        self.to_date_entry.delete(0, "end")
        self.entity_type_combo.set("All")
        self.action_combo.set("All")
        self.filtered_entries = []
        self._refresh_tree_view()
        show_info_message("Filters Cleared", "Showing all audit entries")

    def _export_audit(self):
        """Export audit data to CSV"""
        try:
            entries_to_export = self.filtered_entries if self.filtered_entries else self.current_entries

            if not entries_to_export:
                show_info_message("Export", "No entries to export")
                return

            # Ask user for file location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
                initialfile=f"audit_trail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )

            if not file_path:
                return

            # Write to CSV
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Action", "Entity Type", "Entity ID", "Field", "Old Value", "New Value"])

                for entry in entries_to_export:
                    writer.writerow([
                        entry.timestamp.strftime("%Y-%m-%d %H:%M:%S") if hasattr(entry.timestamp, 'strftime') else str(entry.timestamp),
                        entry.action,
                        entry.entity_type,
                        entry.entity_id or "",
                        entry.field_name or "",
                        entry.old_value or "",
                        entry.new_value or ""
                    ])

            show_info_message("Export Successful", f"Audit data exported to:\n{file_path}")

        except Exception as e:
            show_error_message("Export Error", f"Failed to export audit data: {str(e)}")

    def _clear_all_audit_data(self):
        """Clear all audit trail data"""
        result = messagebox.askyesno(
            "Confirm Clear Audit Data",
            "Are you sure you want to clear ALL audit trail data?\n\n"
            "This will permanently delete all audit log files and cannot be undone.",
            icon="warning"
        )

        if result:
            try:
                deleted_count = self.audit_service.clear_all_audit_data()
                show_info_message(
                    "Audit Data Cleared",
                    f"Successfully cleared all audit data.\n\n"
                    f"Deleted {deleted_count} audit log files."
                )
                # Refresh the display
                self._load_audit_data()
            except Exception as e:
                show_error_message(
                    "Error",
                    f"Failed to clear audit data: {str(e)}"
                )
