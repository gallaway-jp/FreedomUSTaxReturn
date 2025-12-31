"""
Audit Trail Window - View and manage audit history

This window provides:
- Complete audit log viewing
- Filtering by date, entity type, action
- Calculation worksheets
- Export capabilities
- Session summaries
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import scrolledtext
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from services.audit_trail_service import AuditTrailService, AuditEntry
from utils.event_bus import EventBus, Event, EventType


class AuditTrailWindow:
    """
    Window for viewing and managing audit trail history.
    """

    def __init__(self, parent: tk.Tk, audit_service: AuditTrailService):
        """
        Initialize audit trail window.

        Args:
            parent: Parent window
            audit_service: Audit trail service instance
        """
        self.parent = parent
        self.audit_service = audit_service
        self.current_entries: List[AuditEntry] = []

        # Create window
        self.window = tk.Toplevel(parent)
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
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Audit Trail History",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))

        # Filter frame
        filter_frame = ttk.LabelFrame(main_frame, text="Filters", padding="5")
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        # Filter controls
        filter_controls = ttk.Frame(filter_frame)
        filter_controls.pack(fill=tk.X)

        # Date range
        ttk.Label(filter_controls, text="Date Range:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        date_frame = ttk.Frame(filter_controls)
        date_frame.grid(row=0, column=1, sticky=tk.W)

        ttk.Label(date_frame, text="From:").pack(side=tk.LEFT)
        self.from_date_var = tk.StringVar()
        self.from_date_entry = ttk.Entry(date_frame, textvariable=self.from_date_var, width=12)
        self.from_date_entry.pack(side=tk.LEFT, padx=(5, 10))

        ttk.Label(date_frame, text="To:").pack(side=tk.LEFT)
        self.to_date_var = tk.StringVar()
        self.to_date_entry = ttk.Entry(date_frame, textvariable=self.to_date_var, width=12)
        self.to_date_entry.pack(side=tk.LEFT, padx=(5, 10))

        # Entity type filter
        ttk.Label(filter_controls, text="Entity Type:").grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        self.entity_type_var = tk.StringVar()
        self.entity_type_combo = ttk.Combobox(filter_controls, textvariable=self.entity_type_var,
                                             values=["All", "personal_info", "filing_status", "income",
                                                   "deductions", "credits", "payments", "calculation"],
                                             state="readonly", width=15)
        self.entity_type_combo.grid(row=0, column=3, sticky=tk.W, padx=(0, 10))
        self.entity_type_combo.set("All")

        # Action filter
        ttk.Label(filter_controls, text="Action:").grid(row=0, column=4, sticky=tk.W, padx=(10, 5))
        self.action_var = tk.StringVar()
        self.action_combo = ttk.Combobox(filter_controls, textvariable=self.action_var,
                                        values=["All", "CREATE", "UPDATE", "DELETE", "CALCULATE",
                                              "SESSION_START", "SESSION_END"],
                                        state="readonly", width=12)
        self.action_combo.grid(row=0, column=5, sticky=tk.W, padx=(0, 10))
        self.action_combo.set("All")

        # Buttons
        button_frame = ttk.Frame(filter_controls)
        button_frame.grid(row=0, column=6, sticky=tk.E)

        ttk.Button(button_frame, text="Apply Filters", command=self._apply_filters).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Clear Filters", command=self._clear_filters).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Export", command=self._export_audit).pack(side=tk.LEFT)

        # Treeview for audit entries
        tree_frame = ttk.LabelFrame(main_frame, text="Audit Entries", padding="5")
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create treeview with scrollbar
        tree_container = ttk.Frame(tree_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)

        # Treeview columns
        columns = ("timestamp", "action", "entity_type", "entity_id", "field_name", "old_value", "new_value")
        self.audit_tree = ttk.Treeview(tree_container, columns=columns, show="headings", height=15)

        # Configure columns
        self.audit_tree.heading("timestamp", text="Timestamp")
        self.audit_tree.heading("action", text="Action")
        self.audit_tree.heading("entity_type", text="Entity Type")
        self.audit_tree.heading("entity_id", text="Entity ID")
        self.audit_tree.heading("field_name", text="Field")
        self.audit_tree.heading("old_value", text="Old Value")
        self.audit_tree.heading("new_value", text="New Value")

        self.audit_tree.column("timestamp", width=150, minwidth=150)
        self.audit_tree.column("action", width=80, minwidth=80)
        self.audit_tree.column("entity_type", width=100, minwidth=100)
        self.audit_tree.column("entity_id", width=100, minwidth=100)
        self.audit_tree.column("field_name", width=100, minwidth=100)
        self.audit_tree.column("old_value", width=120, minwidth=120)
        self.audit_tree.column("new_value", width=120, minwidth=120)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.audit_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, command=self.audit_tree.xview)
        self.audit_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Pack treeview and scrollbars
        self.audit_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Bind selection event
        self.audit_tree.bind("<<TreeviewSelect>>", self._on_entry_selected)

        # Create context menu
        self.context_menu = tk.Menu(self.window, tearoff=0)
        self.context_menu.add_command(label="View Details", command=self._view_selected_details)
        self.context_menu.add_command(label="Export Selected", command=self._export_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Refresh", command=self._refresh_data)

        # Bind right-click to context menu
        self.audit_tree.bind("<Button-3>", self._show_context_menu)

        # Bind keyboard shortcuts
        self.window.bind('<Control-r>', lambda e: self._refresh_data())
        self.window.bind('<Key>', self._on_key_press)

        # Detail view frame
        detail_frame = ttk.LabelFrame(main_frame, text="Entry Details", padding="5")
        detail_frame.pack(fill=tk.BOTH, expand=True)

        # Detail text area
        self.detail_text = scrolledtext.ScrolledText(detail_frame, height=8, wrap=tk.WORD)
        self.detail_text.pack(fill=tk.BOTH, expand=True)

        # Bottom buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="Refresh", command=self._load_audit_data).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="View Calculation", command=self._view_calculation).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Close", command=self.window.destroy).pack(side=tk.RIGHT)

    def _load_audit_data(self) -> None:
        """Load audit data into the treeview"""
        # Clear existing items
        for item in self.audit_tree.get_children():
            self.audit_tree.delete(item)

        # Get audit entries (last 100 for performance)
        self.current_entries = self.audit_service.get_audit_history(limit=100)

        # Add entries to treeview
        for entry in self.current_entries:
            # Format values for display
            old_val = str(entry.old_value) if entry.old_value is not None else ""
            new_val = str(entry.new_value) if entry.new_value is not None else ""

            # Truncate long values
            if len(old_val) > 50:
                old_val = old_val[:47] + "..."
            if len(new_val) > 50:
                new_val = new_val[:47] + "..."

            self.audit_tree.insert("", tk.END, values=(
                entry.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                entry.action,
                entry.entity_type,
                entry.entity_id or "",
                entry.field_name or "",
                old_val,
                new_val
            ), tags=(entry.id,))

        # Clear detail view
        self.detail_text.delete(1.0, tk.END)

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

        # Update treeview
        for item in self.audit_tree.get_children():
            self.audit_tree.delete(item)

        self.current_entries = filtered_entries

        for entry in filtered_entries:
            old_val = str(entry.old_value) if entry.old_value is not None else ""
            new_val = str(entry.new_value) if entry.new_value is not None else ""

            if len(old_val) > 50:
                old_val = old_val[:47] + "..."
            if len(new_val) > 50:
                new_val = new_val[:47] + "..."

            self.audit_tree.insert("", tk.END, values=(
                entry.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                entry.action,
                entry.entity_type,
                entry.entity_id or "",
                entry.field_name or "",
                old_val,
                new_val
            ), tags=(entry.id,))

    def _clear_filters(self) -> None:
        """Clear all filters"""
        self.from_date_var.set("")
        self.to_date_var.set("")
        self.entity_type_var.set("All")
        self.action_var.set("All")
        self._load_audit_data()

    def _on_entry_selected(self, event) -> None:
        """Handle audit entry selection"""
        selection = self.audit_tree.selection()
        if not selection:
            return

        # Get the entry ID from tags
        item_tags = self.audit_tree.item(selection[0], "tags")
        if not item_tags:
            return

        entry_id = item_tags[0]

        # Find the entry
        entry = next((e for e in self.current_entries if e.id == entry_id), None)
        if not entry:
            return

        # Display detailed information
        detail_text = f"""Audit Entry Details
==================

ID: {entry.id}
Timestamp: {entry.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
User ID: {entry.user_id}
Session ID: {entry.session_id}

Action: {entry.action}
Entity Type: {entry.entity_type}
Entity ID: {entry.entity_id or 'N/A'}
Field Name: {entry.field_name or 'N/A'}

Old Value: {entry.old_value}
New Value: {entry.new_value}

Metadata:
{json.dumps(entry.metadata, indent=2, default=str) if entry.metadata else 'None'}
"""

        if entry.calculation_worksheet:
            detail_text += f"""

Calculation Worksheet:
{json.dumps(entry.calculation_worksheet, indent=2, default=str)}
"""

        self.detail_text.delete(1.0, tk.END)
        self.detail_text.insert(tk.END, detail_text)

    def _view_calculation(self) -> None:
        """View calculation details for selected entry"""
        selection = self.audit_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select an audit entry first")
            return

        item_tags = self.audit_tree.item(selection[0], "tags")
        if not item_tags:
            return

        entry_id = item_tags[0]
        entry = next((e for e in self.current_entries if e.id == entry_id), None)

        if not entry or entry.action != "CALCULATE":
            messagebox.showinfo("Info", "Selected entry is not a calculation")
            return

        # Create calculation detail window
        calc_window = tk.Toplevel(self.window)
        calc_window.title("Calculation Details")
        calc_window.geometry("800x600")

        # Title
        ttk.Label(calc_window, text=f"Calculation: {entry.entity_id}",
                 font=("Arial", 14, "bold")).pack(pady=10)

        # Calculation details
        text_area = scrolledtext.ScrolledText(calc_window, wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Format calculation details
        calc_text = f"""Calculation Type: {entry.metadata.get('calculation_type', 'Unknown')}

Inputs:
{json.dumps(entry.metadata.get('inputs', {}), indent=2, default=str)}

Results:
{json.dumps(entry.metadata.get('results', {}), indent=2, default=str)}
"""

        if entry.calculation_worksheet:
            calc_text += f"""

Detailed Worksheet:
{json.dumps(entry.calculation_worksheet, indent=2, default=str)}
"""

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