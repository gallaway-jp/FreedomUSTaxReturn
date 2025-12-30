#!/usr/bin/env python3
"""
Test script for FormField with date picker
"""

import tkinter as tk
from datetime import date
from gui.widgets.form_field import FormField
from gui.theme_manager import ThemeManager

def test_form_field_date():
    """Test FormField with date picker"""
    root = tk.Tk()
    root.title("FormField Date Test")
    root.geometry("400x300")

    # Create theme manager
    theme_manager = ThemeManager(root)

    # Create date field
    date_field = FormField(
        root,
        "Birth Date",
        field_type="date",
        required=True,
        theme_manager=theme_manager
    )
    date_field.pack(pady=20, padx=20, fill="x")

    # Label to show validation status
    status_label = tk.Label(root, text="Validation status will appear here")
    status_label.pack(pady=10)

    def update_status():
        is_valid = date_field.is_field_valid()
        status = "Valid" if is_valid else "Invalid"
        status_label.config(text=f"Status: {status}")

        # Get the date value
        date_value = date_field.get()
        if isinstance(date_value, date):
            print(f"Selected date: {date_value.strftime('%m/%d/%Y')}")
        else:
            print(f"Date value: {date_value}")

    # Set validation callback
    date_field.validation_callback = lambda valid, msg: update_status()

    # Test setting date programmatically
    test_date = date(1990, 5, 15)
    date_field.set(test_date)
    update_status()

    print("FormField date test window opened. Test the date picker functionality.")
    root.mainloop()

if __name__ == "__main__":
    test_form_field_date()