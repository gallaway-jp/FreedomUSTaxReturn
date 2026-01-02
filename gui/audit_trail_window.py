"""
Audit Trail Window - View and manage audit history

This window provides:
- Complete audit log viewing
- Filtering by date, entity type, action
- Calculation worksheets
- Export capabilities
- Session summaries
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from tkinter import scrolledtext
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from services.audit_trail_service import AuditTrailService, AuditEntry
from utils.event_bus import EventBus, Event, EventType
from gui.modern_ui_components import ModernFrame, ModernButton, ModernLabel
from services.accessibility_service import AccessibilityService


class AuditTrailWindow:
    """
    Window for viewing and managing audit trail history.
    """

    def __init__(self, parent: ctk.CTk, audit_service: AuditTrailService, accessibility_service: Optional[AccessibilityService] = None):
        """
        Initialize audit trail window.

        Args:
            parent: Parent window
            audit_service: Audit trail service instance
            accessibility_service: Accessibility service for enhanced usability
        """
        self.parent = parent
        self.audit_service = audit_service
        self.accessibility_service = accessibility_service
        self.current_entries: List[AuditEntry] = []

        # Create window
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Audit Trail")
        self.window.geometry("1200x800")
        self.window.resizable(True, True)

        # Initialize UI
        self._create_ui()
        self._load_audit_data()

        # Center window
        self.window.transient(parent)
        self.window.grab_set()

    def _create_ui(self) -> None:
        """Create the user interface"""
        # Main frame
        main_frame = ModernFrame(self.window)
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        # Title
        title_label = ModernLabel(main_frame, text="Audit Trail History",
                                 font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(pady=(0, 10))

        # Filter frame
        filter_frame = ctk.CTkFrame(main_frame)
        filter_frame.pack(fill=ctk.X, pady=(0, 10))

        filter_title = ModernLabel(filter_frame, text="Filters", font=ctk.CTkFont(size=14, weight="bold"))
        filter_title.pack(pady=(10, 5), padx=10, anchor="w")

        # Filter controls
        filter_controls = ctk.CTkFrame(filter_frame, fg_color="transparent")
        filter_controls.pack(fill=ctk.X, padx=10, pady=(0, 10))

        # Date range
        date_frame = ctk.CTkFrame(filter_controls, fg_color="transparent")
        date_frame.pack(fill=ctk.X, pady=(0, 5))

        ModernLabel(date_frame, text="Date Range:", accessibility_service=self.accessibility_service).pack(side=ctk.LEFT)

        ModernLabel(date_frame, text="From:", accessibility_service=self.accessibility_service).pack(side=ctk.LEFT, padx=(20, 5))
        self.from_date_var = ctk.StringVar()
        self.from_date_entry = ctk.CTkEntry(date_frame, textvariable=self.from_date_var, width=120)
        self.from_date_entry.pack(side=ctk.LEFT, padx=(0, 10))

        ModernLabel(date_frame, text="To:", accessibility_service=self.accessibility_service).pack(side=ctk.LEFT)
        self.to_date_var = ctk.StringVar()
        self.to_date_entry = ctk.CTkEntry(date_frame, textvariable=self.to_date_var, width=120)
        self.to_date_entry.pack(side=ctk.LEFT, padx=(5, 10))

        # Entity type and Action filters
        type_action_frame = ctk.CTkFrame(filter_controls, fg_color="transparent")
        type_action_frame.pack(fill=ctk.X, pady=(0, 5))

        # Entity type filter
        ModernLabel(type_action_frame, text="Entity Type:", accessibility_service=self.accessibility_service).pack(side=ctk.LEFT)
        self.entity_type_var = ctk.StringVar()
        self.entity_type_combo = ctk.CTkComboBox(
            type_action_frame,
            variable=self.entity_type_var,
            values=["All", "personal_info", "filing_status", "income", "deductions", "credits", "payments", "calculation"],
            width=150
        )
        self.entity_type_combo.pack(side=ctk.LEFT, padx=(5, 20))
        self.entity_type_combo.set("All")

        # Action filter
        ModernLabel(type_action_frame, text="Action:", accessibility_service=self.accessibility_service).pack(side=ctk.LEFT)
        self.action_var = ctk.StringVar()
        self.action_combo = ctk.CTkComboBox(
            type_action_frame,
            variable=self.action_var,
            values=["All", "CREATE", "UPDATE", "DELETE", "CALCULATE", "SESSION_START", "SESSION_END"],
            width=120
        )
        self.action_combo.pack(side=ctk.LEFT, padx=(5, 10))
        self.action_combo.set("All")

        # Buttons
        button_frame = ctk.CTkFrame(filter_controls, fg_color="transparent")
        button_frame.pack(fill=ctk.X, pady=(5, 0))

        ModernButton(button_frame, text="Apply Filters", command=self._apply_filters,
                    accessibility_service=self.accessibility_service).pack(side=ctk.LEFT, padx=(0, 5))
        ModernButton(button_frame, text="Clear Filters", command=self._clear_filters,
                    button_type="secondary", accessibility_service=self.accessibility_service).pack(side=ctk.LEFT, padx=(0, 5))
        ModernButton(button_frame, text="Export", command=self._export_audit,
                    button_type="secondary", accessibility_service=self.accessibility_service).pack(side=ctk.LEFT, padx=(0, 5))
        ModernButton(button_frame, text="Clear All Data", command=self._clear_all_audit_data,
                    button_type="danger", accessibility_service=self.accessibility_service).pack(side=ctk.RIGHT)

        # Audit entries display (using scrolled text instead of treeview for theming)
        entries_frame = ctk.CTkFrame(main_frame)
        entries_frame.pack(fill=ctk.BOTH, expand=True, pady=(0, 10))

        entries_title = ModernLabel(entries_frame, text="Audit Entries", font=ctk.CTkFont(size=14, weight="bold"))
        entries_title.pack(pady=(10, 5), padx=10, anchor="w")

        # Create scrolled text widget for audit entries
        self.audit_text = ctk.CTkTextbox(entries_frame, height=300, wrap="none")
        self.audit_text.pack(fill=ctk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Make it read-only
        self.audit_text.configure(state="disabled")

        # Detail view frame
        detail_frame = ctk.CTkFrame(main_frame)
        detail_frame.pack(fill=ctk.BOTH, expand=True)

        detail_title = ModernLabel(detail_frame, text="Entry Details", font=ctk.CTkFont(size=14, weight="bold"))
        detail_title.pack(pady=(10, 5), padx=10, anchor="w")

        # Detail text area
        self.detail_text = ctk.CTkTextbox(detail_frame, height=150, wrap="word")
        self.detail_text.pack(fill=ctk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Make detail text read-only
        self.detail_text.configure(state="disabled")

        # Bottom buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill=ctk.X, pady=(10, 0))

        ModernButton(button_frame, text="Refresh", command=self._load_audit_data,
                    accessibility_service=self.accessibility_service).pack(side=ctk.LEFT, padx=(10, 5))
        ModernButton(button_frame, text="View Calculation", command=self._view_calculation,
                    button_type="secondary", accessibility_service=self.accessibility_service).pack(side=ctk.LEFT, padx=(0, 5))
        ModernButton(button_frame, text="Close", command=self.window.destroy,
                    button_type="secondary", accessibility_service=self.accessibility_service).pack(side=ctk.RIGHT, padx=(0, 10))

    def _load_audit_data(self) -> None:
        """Load audit data into the text widget"""
        # Enable text widget for editing
        self.audit_text.configure(state="normal")
        self.audit_text.delete("0.0", "end")

        # Get audit entries (last 100 for performance)
        self.current_entries = self.audit_service.get_audit_history(limit=100)

        if not self.current_entries:
            self.audit_text.insert("0.0", "No audit entries found.")
            self.audit_text.configure(state="disabled")
            return

        # Add header
        header = f"{'Timestamp':<20} {'Action':<12} {'Entity Type':<15} {'Entity ID':<15} {'Field':<15} {'Old Value':<20} {'New Value':<20}\n"
        header += "=" * 120 + "\n"
        self.audit_text.insert("0.0", header)

        # Add entries to text widget
        for i, entry in enumerate(self.current_entries):
            # Format values for display
            old_val = str(entry.old_value) if entry.old_value is not None else ""
            new_val = str(entry.new_value) if entry.new_value is not None else ""

            # Truncate long values
            if len(old_val) > 17:
                old_val = old_val[:14] + "..."
            if len(new_val) > 17:
                new_val = new_val[:14] + "..."

            line = ("02d")

            self.audit_text.insert("end", line)

        # Make text widget read-only again
        self.audit_text.configure(state="disabled")

        # Clear detail view
        self.detail_text.configure(state="normal")
        self.detail_text.delete("0.0", "end")
        self.detail_text.configure(state="disabled")

    def _clear_filters(self) -> None:
        """Clear all filters"""
        self.entity_type_var.set("All")
        self.action_var.set("All")
        self.from_date_var.set("")
        self.to_date_var.set("")
        # Reload data with no filters
        self._load_audit_data()

    def _apply_filters(self) -> None:
        """Apply current filters to the audit data"""
        # Parse dates
        start_date = None
        end_date = None

        if self.from_date_var.get():
            try:
                start_date = datetime.strptime(self.from_date_var.get(), "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Invalid 'From' date format. Use YYYY-MM-DD")
                return

        if self.to_date_var.get():
            try:
                end_date = datetime.strptime(self.to_date_var.get(), "%Y-%m-%d")
                # Set to end of day
                end_date = end_date.replace(hour=23, minute=59, second=59)
            except ValueError:
                messagebox.showerror("Error", "Invalid 'To' date format. Use YYYY-MM-DD")
                return

        # Get entity type and action filters
        entity_type = None if self.entity_type_var.get() == "All" else self.entity_type_var.get()
        action = None if self.action_var.get() == "All" else self.action_var.get()

        # Filter entries
        filtered_entries = self.audit_service.get_audit_history(
            entity_type=entity_type,
            action=action,
            start_date=start_date,
            end_date=end_date,
            limit=500
        )

        # Update text widget
        self.audit_text.configure(state="normal")
        self.audit_text.delete("0.0", "end")

        if not filtered_entries:
            self.audit_text.insert("0.0", "No audit entries match the current filters.")
        else:
            # Add header
            header = f"{'Timestamp':<20} {'Action':<12} {'Entity Type':<15} {'Entity ID':<15} {'Field':<15} {'Old Value':<20} {'New Value':<20}\n"
            header += "=" * 120 + "\n"
            self.audit_text.insert("0.0", header)

            # Add filtered entries
            for i, entry in enumerate(filtered_entries):
                old_val = str(entry.old_value) if entry.old_value is not None else ""
                new_val = str(entry.new_value) if entry.new_value is not None else ""

                if len(old_val) > 17:
                    old_val = old_val[:14] + "..."
                if len(new_val) > 17:
                    new_val = new_val[:14] + "..."

                line = ("02d")

                self.audit_text.insert("end", line)

        self.audit_text.configure(state="disabled")
        self.current_entries = filtered_entries

        # Clear detail view
        self.detail_text.configure(state="normal")
        self.detail_text.delete("0.0", "end")
        self.detail_text.configure(state="disabled")

    def _clear_filters(self) -> None:
        """Clear all filters"""
        self.from_date_var.set("")
        self.to_date_var.set("")
        self.entity_type_var.set("All")
        self.action_var.set("All")
        self._load_audit_data()

    def _clear_all_audit_data(self) -> None:
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
                messagebox.showinfo(
                    "Audit Data Cleared",
                    f"Successfully cleared all audit data.\n\n"
                    f"Deleted {deleted_count} audit log files."
                )
                # Refresh the display
                self._load_audit_data()
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Failed to clear audit data: {str(e)}"
                )

    def _view_calculation(self) -> None:
        """View calculation details - simplified for text display"""
        messagebox.showinfo("Info", "Select a calculation entry by clicking on it in the audit entries list above, then use this button to view details.")

    def _export_selected(self) -> None:
        """Export selected entries - not available in text mode"""
        messagebox.showinfo("Info", "Export functionality is available via the Export button. Individual entry selection is not supported in the current view.")

    def _view_selected_details(self) -> None:
        """View selected entry details - not available in text mode"""
        messagebox.showinfo("Info", "Click on an audit entry in the list above to view its details.")

    def _show_context_menu(self, event) -> None:
        """Show context menu - not available in text mode"""
        pass

    def _refresh_data(self) -> None:
        """Refresh audit data"""
        self._load_audit_data()

    def _on_key_press(self, event) -> None:
        """Handle key press events"""
        pass

        text_area.insert(tk.END, calc_text)
        text_area.config(state=tk.DISABLED)

        # Close button
        ttk.Button(calc_window, text="Close", command=calc_window.destroy).pack(pady=10)

    def _export_audit(self) -> None:
        """Export audit data"""
        # Get date range from filters
        start_date = None
        end_date = None

        if self.from_date_var.get():
            try:
                start_date = datetime.strptime(self.from_date_var.get(), "%Y-%m-%d")
            except ValueError:
                start_date = None

        if self.to_date_var.get():
            try:
                end_date = datetime.strptime(self.to_date_var.get(), "%Y-%m-%d")
                end_date = end_date.replace(hour=23, minute=59, second=59)
            except ValueError:
                end_date = None

        # Ask for format
        format_choice = tk.StringVar(value="json")
        format_window = tk.Toplevel(self.window)
        format_window.title("Export Format")
        format_window.geometry("300x150")

        ttk.Label(format_window, text="Choose export format:").pack(pady=10)
        ttk.Radiobutton(format_window, text="JSON", variable=format_choice, value="json").pack()
        ttk.Radiobutton(format_window, text="CSV", variable=format_choice, value="csv").pack()

        def do_export():
            format_window.destroy()
            try:
                filepath = self.audit_service.export_audit_report(
                    start_date=start_date,
                    end_date=end_date,
                    format=format_choice.get()
                )
                messagebox.showinfo("Export Complete", f"Audit report exported to:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export audit report:\n{str(e)}")

        ttk.Button(format_window, text="Export", command=do_export).pack(pady=10)

    def _format_value(self, value: Any) -> str:
        """Format a value for display"""
        if value is None:
            return ""
        if isinstance(value, dict):
            # Truncate long dict representations
            str_val = json.dumps(value, default=str)
            if len(str_val) > 50:
                return str_val[:47] + "..."
            return str_val
        return str(value)

    def _format_timestamp(self, timestamp: datetime) -> str:
        """Format a timestamp for display"""
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")

    def _show_about(self) -> None:
        """Show about dialog"""
        messagebox.showinfo(
            "About Audit Trail",
            "Audit Trail Viewer\n\n"
            "View and manage audit entries for tax return activities.\n"
            "Tracks all changes, calculations, and user actions."
        )

    def _refresh_data(self) -> None:
        """Refresh audit data (alias for _load_audit_data)"""
        self._load_audit_data()

    def resizable(self) -> bool:
        """Check if window is resizable"""
        return True  # Window is resizable

    def minsize(self) -> tuple:
        """Get minimum window size"""
        return (800, 600)

    def _show_context_menu(self, event) -> None:
        """Show context menu on right-click"""
        if hasattr(self, 'context_menu'):
            self.context_menu.tk_popup(event.x_root, event.y_root)

    def _on_key_press(self, event) -> None:
        """Handle key press events"""
        if event.keysym == 'r' and event.state == 4:  # Ctrl+R
            self._refresh_data()

    def _sort_column(self, col: str) -> None:
        """Sort treeview by column"""
        # Simple sort implementation - reverse current order
        items = [(self.audit_tree.item(item, 'values'), item) for item in self.audit_tree.get_children('')]

        # Sort by the specified column (timestamp=0, action=1, etc.)
        col_index = {'timestamp': 0, 'action': 1, 'entity_type': 2, 'entity_id': 3, 'field_name': 4, 'old_value': 5, 'new_value': 6}.get(col, 0)

        items.sort(key=lambda x: x[0][col_index] if col_index < len(x[0]) else "")

        # Clear and re-insert sorted items
        for item in self.audit_tree.get_children():
            self.audit_tree.delete(item)

        for values, item_id in items:
            self.audit_tree.insert('', 'end', values=values, tags=(item_id,))

    def _view_selected_details(self) -> None:
        """View details for selected entry (context menu action)"""
        self._on_entry_selected(None)

    def _export_selected(self) -> None:
        """Export selected entries"""
        selection = self.audit_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select audit entries to export")
            return

        # Get selected entries
        selected_entries = []
        for item in selection:
            item_tags = self.audit_tree.item(item, "tags")
            if item_tags:
                entry_id = item_tags[0]
                entry = next((e for e in self.current_entries if e.id == entry_id), None)
                if entry:
                    selected_entries.append(entry)

        if not selected_entries:
            messagebox.showinfo("Info", "No valid entries selected")
            return

        # Export selected entries
        try:
            filepath = self.audit_service.export_audit_report(
                entries=selected_entries,
                format="json"
            )
            messagebox.showinfo("Export Complete", f"Selected entries exported to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export selected entries:\n{str(e)}")

    def show(self) -> None:
        """Show the audit trail window"""
        self.window.mainloop()

    def destroy(self) -> None:
        """Destroy the audit trail window"""
        if self.window:
            self.window.destroy()