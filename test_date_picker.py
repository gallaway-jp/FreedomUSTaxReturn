#!/usr/bin/env python3
"""
Test script for date picker widget
"""

import tkinter as tk
from datetime import date
from gui.widgets.date_picker import DatePicker

def test_date_picker():
    """Test the date picker widget"""
    root = tk.Tk()
    root.title("Date Picker Test")
    root.geometry("300x200")

    # Create date picker
    date_picker = DatePicker(root, initial_date=date.today())
    date_picker.pack(pady=20, padx=20)

    # Label to show selected date
    result_label = tk.Label(root, text="Selected date will appear here")
    result_label.pack(pady=10)

    def on_date_change():
        selected_date = date_picker.get_date()
        result_label.config(text=f"Selected: {selected_date.strftime('%m/%d/%Y')}")

    # Set callback
    date_picker.command = on_date_change

    # Test setting date programmatically
    test_date = date(2024, 12, 25)
    date_picker.set_date(test_date)
    on_date_change()

    print("Date picker test window opened. Click the calendar button to test.")
    root.mainloop()

if __name__ == "__main__":
    test_date_picker()