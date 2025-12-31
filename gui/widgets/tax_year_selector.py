"""
Tax Year Selector Widget - GUI component for selecting tax years

This widget provides:
- Dropdown selection of supported tax years
- Visual indicators for filing status (open, approaching deadline, past deadline)
- Quick access to year-over-year comparisons
- Integration with the main application for year switching
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Optional, Callable, Dict, Any
from datetime import date
from services.tax_year_service import TaxYearService

logger = logging.getLogger(__name__)


class TaxYearSelector(ttk.Frame):
    """
    Widget for selecting and managing tax years in the application.

    Provides a dropdown for year selection with status indicators and
    quick access to year management features.
    """

    def __init__(self, parent, tax_year_service: TaxYearService, on_year_changed: Optional[Callable[[int], None]] = None):
        """
        Initialize the tax year selector.

        Args:
            parent: Parent tkinter widget
            tax_year_service: Service for tax year management
            on_year_changed: Callback when tax year is changed
        """
        super().__init__(parent)
        self.tax_year_service = tax_year_service
        self.on_year_changed = on_year_changed
        self.current_year = self.tax_year_service.get_current_tax_year()

        self._setup_ui()
        self._populate_years()
        self._update_status_display()

    def _setup_ui(self):
        """Set up the user interface components"""
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.X, expand=True, padx=5, pady=2)

        # Year selection label
        ttk.Label(main_frame, text="Tax Year:").pack(side=tk.LEFT, padx=(0, 5))

        # Year selection combobox
        self.year_var = tk.StringVar()
        self.year_combo = ttk.Combobox(
            main_frame,
            textvariable=self.year_var,
            state="readonly",
            width=6
        )
        self.year_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.year_combo.bind("<<ComboboxSelected>>", self._on_year_selected)

        # Status indicator frame
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(side=tk.LEFT, padx=(0, 10))

        # Status label
        self.status_var = tk.StringVar(value="Status: Unknown")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT)

        # Status indicator (colored dot)
        self.status_indicator = tk.Canvas(status_frame, width=12, height=12, bg=self.master.cget('bg'))
        self.status_indicator.pack(side=tk.LEFT, padx=(5, 0))
        self.status_indicator.create_oval(2, 2, 10, 10, fill="gray", tags="status_dot")

        # Deadline info
        self.deadline_var = tk.StringVar(value="")
        self.deadline_label = ttk.Label(main_frame, textvariable=self.deadline_var, font=("", 8))
        self.deadline_label.pack(side=tk.LEFT, padx=(10, 0))

        # Action buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.RIGHT)

        # New year button
        self.new_year_btn = ttk.Button(
            button_frame,
            text="New Year",
            command=self._create_new_year,
            width=8
        )
        self.new_year_btn.pack(side=tk.LEFT, padx=(0, 2))

        # Compare button
        self.compare_btn = ttk.Button(
            button_frame,
            text="Compare",
            command=self._show_year_comparison,
            width=8
        )
        self.compare_btn.pack(side=tk.LEFT)

    def _populate_years(self):
        """Populate the year selection dropdown"""
        supported_years = self.tax_year_service.get_supported_years()
        self.year_combo['values'] = [str(year) for year in supported_years]

        # Set current year as default
        self.year_var.set(str(self.current_year))

    def _on_year_selected(self, event=None):
        """Handle year selection change"""
        try:
            selected_year = int(self.year_var.get())
            self.current_year = selected_year
            self._update_status_display()

            if self.on_year_changed:
                self.on_year_changed(selected_year)

        except ValueError as e:
            logger.error(f"Invalid year selected: {e}")
            messagebox.showerror("Error", "Invalid tax year selected")

    def _update_status_display(self):
        """Update the status indicator and deadline display"""
        year = self.current_year
        days_until = self.tax_year_service.get_days_until_deadline(year)

        if days_until is None:
            self.status_var.set("Status: Unknown")
            self._set_status_color("gray")
            self.deadline_var.set("")
            return

        if days_until > 30:
            self.status_var.set("Status: Open")
            self._set_status_color("green")
        elif days_until > 0:
            self.status_var.set("Status: Approaching")
            self._set_status_color("yellow")
        elif days_until == 0:
            self.status_var.set("Status: Due Today")
            self._set_status_color("orange")
        else:
            self.status_var.set("Status: Past Due")
            self._set_status_color("red")

        # Update deadline display
        deadline = self.tax_year_service.get_filing_deadline(year)
        if deadline:
            if days_until > 0:
                self.deadline_var.set(f"Due: {deadline.strftime('%m/%d/%Y')} ({days_until} days)")
            elif days_until == 0:
                self.deadline_var.set(f"Due: {deadline.strftime('%m/%d/%Y')} (Today!)")
            else:
                self.deadline_var.set(f"Due: {deadline.strftime('%m/%d/%Y')} ({abs(days_until)} days past)")

    def _set_status_color(self, color: str):
        """Set the color of the status indicator dot"""
        color_map = {
            "green": "#28a745",
            "yellow": "#ffc107",
            "orange": "#fd7e14",
            "red": "#dc3545",
            "gray": "#6c757d"
        }
        actual_color = color_map.get(color, color)
        self.status_indicator.itemconfig("status_dot", fill=actual_color)

    def _create_new_year(self):
        """Create a new tax year return"""
        # Get available years (not already created)
        supported_years = set(self.tax_year_service.get_supported_years())
        # For now, just show a dialog - actual creation would be handled by the main app
        messagebox.showinfo(
            "New Tax Year",
            "To create a new tax year return, use 'File > New Return' and select the desired tax year."
        )

    def _show_year_comparison(self):
        """Show year-over-year comparison dialog"""
        # This would open a comparison window - for now just show info
        messagebox.showinfo(
            "Year Comparison",
            "Year-over-year comparison feature will be available in the next update.\n\n"
            "This will allow you to compare income, deductions, credits, and tax calculations "
            "between different tax years."
        )

    def get_current_year(self) -> int:
        """Get the currently selected tax year"""
        return self.current_year

    def set_current_year(self, year: int):
        """Set the current tax year"""
        if year in self.tax_year_service.get_supported_years():
            self.year_var.set(str(year))
            self.current_year = year
            self._update_status_display()

            if self.on_year_changed:
                self.on_year_changed(year)
        else:
            logger.warning(f"Attempted to set unsupported tax year: {year}")

    def refresh_status(self):
        """Refresh the status display (useful when date changes)"""
        self._update_status_display()