"""
Date picker widget for selecting dates
"""

import tkinter as tk
from tkinter import ttk
import calendar
from datetime import datetime, date
from typing import Callable, Optional


class DatePicker(ttk.Frame):
    """A date picker widget with calendar popup"""

    def __init__(self, parent, initial_date=None, date_format="%m/%d/%Y",
                 command=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.date_format = date_format
        self.command = command
        self.selected_date = initial_date or date.today()
        self.popup = None

        # Create the entry and button
        self.entry = ttk.Entry(self, width=12)
        self.entry.pack(side="left", fill="x", expand=True)

        self.button = ttk.Button(self, text="📅", width=3, command=self._show_calendar)
        self.button.pack(side="right")

        # Set initial value
        self._update_entry()

        # Bind events
        self.entry.bind('<FocusOut>', self._on_entry_focus_out)
        self.entry.bind('<Return>', self._on_entry_return)

    def _show_calendar(self):
        """Show the calendar popup"""
        if self.popup:
            self.popup.destroy()

        # Create popup window
        self.popup = tk.Toplevel(self)
        self.popup.title("Select Date")
        self.popup.geometry("250x220")
        self.popup.resizable(False, False)
        self.popup.transient(self.winfo_toplevel())
        self.popup.grab_set()

        # Center the popup
        self.popup.geometry("+{}+{}".format(
            self.winfo_rootx() + 50,
            self.winfo_rooty() + 30
        ))

        # Current date info
        current_year = self.selected_date.year
        current_month = self.selected_date.month

        # Month/Year selector
        header_frame = ttk.Frame(self.popup)
        header_frame.pack(fill="x", padx=10, pady=5)

        self.month_var = tk.StringVar(value=calendar.month_name[current_month])
        self.year_var = tk.IntVar(value=current_year)

        month_combo = ttk.Combobox(header_frame, textvariable=self.month_var,
                                  values=list(calendar.month_name)[1:], width=10)
        month_combo.pack(side="left", padx=(0, 5))
        month_combo.bind('<<ComboboxSelected>>', self._on_month_year_change)

        year_combo = ttk.Combobox(header_frame, textvariable=self.year_var,
                                 values=list(range(current_year - 10, current_year + 11)), width=6)
        year_combo.pack(side="left")
        year_combo.bind('<<ComboboxSelected>>', self._on_month_year_change)

        # Calendar grid
        self._create_calendar_grid(current_year, current_month)

        # Buttons
        button_frame = ttk.Frame(self.popup)
        button_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(button_frame, text="Today", command=self._set_today).pack(side="left")
        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side="right", padx=(5, 0))
        ttk.Button(button_frame, text="OK", command=self._accept).pack(side="right")

    def _create_calendar_grid(self, year, month):
        """Create the calendar grid for the given month/year"""
        # Remove existing calendar if any
        if hasattr(self, 'calendar_frame'):
            self.calendar_frame.destroy()

        self.calendar_frame = ttk.Frame(self.popup)
        self.calendar_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Day headers
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for i, day in enumerate(days):
            ttk.Label(self.calendar_frame, text=day, font=("Arial", 9, "bold")).grid(
                row=0, column=i, padx=2, pady=2)

        # Get calendar data
        cal = calendar.monthcalendar(year, month)
        today = date.today()

        # Create day buttons
        for week_num, week in enumerate(cal):
            for day_num, day in enumerate(week):
                if day == 0:
                    # Empty cell
                    ttk.Label(self.calendar_frame, text="").grid(
                        row=week_num + 1, column=day_num, padx=2, pady=2)
                else:
                    # Day button
                    day_date = date(year, month, day)
                    is_today = (day_date == today)
                    is_selected = (day_date == self.selected_date)

                    if is_selected:
                        style = "Selected.TButton"
                    elif is_today:
                        style = "Today.TButton"
                    else:
                        style = "Calendar.TButton"

                    btn = ttk.Button(self.calendar_frame, text=str(day),
                                   width=3, style=style,
                                   command=lambda d=day_date: self._select_date(d))
                    btn.grid(row=week_num + 1, column=day_num, padx=1, pady=1)

    def _on_month_year_change(self, event=None):
        """Handle month/year change"""
        month_name = self.month_var.get()
        year = self.year_var.get()

        # Convert month name to number
        month_names = list(calendar.month_name)
        if month_name in month_names:
            month = month_names.index(month_name)
            self._create_calendar_grid(year, month)

    def _select_date(self, selected_date):
        """Select a date from the calendar"""
        self.selected_date = selected_date
        self._update_entry()

        # Highlight selected date
        self._create_calendar_grid(selected_date.year, selected_date.month)

    def _set_today(self):
        """Set date to today"""
        self.selected_date = date.today()
        self._update_entry()
        self._create_calendar_grid(self.selected_date.year, self.selected_date.month)

    def _accept(self):
        """Accept the selected date"""
        if self.popup:
            self.popup.destroy()
            self.popup = None
        if self.command:
            self.command()

    def _cancel(self):
        """Cancel date selection"""
        if self.popup:
            self.popup.destroy()
            self.popup = None

    def _on_entry_focus_out(self, event):
        """Handle entry focus out - try to parse date"""
        self._parse_entry_date()

    def _on_entry_return(self, event):
        """Handle enter key in entry"""
        self._parse_entry_date()

    def _parse_entry_date(self):
        """Parse date from entry field"""
        text = self.entry.get().strip()
        if not text:
            return

        try:
            parsed_date = datetime.strptime(text, self.date_format).date()
            self.selected_date = parsed_date
            self._update_entry()
            if self.command:
                self.command()
        except ValueError:
            # Invalid date format - revert to previous date
            self._update_entry()

    def _update_entry(self):
        """Update the entry field with the selected date"""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, self.selected_date.strftime(self.date_format))

    def get_date(self) -> date:
        """Get the selected date"""
        return self.selected_date

    def set_date(self, new_date: date):
        """Set the selected date"""
        self.selected_date = new_date
        self._update_entry()