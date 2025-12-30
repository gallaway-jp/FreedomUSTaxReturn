"""
Validation summary widget - shows form validation errors across all pages
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Callable


class ValidationSummary(ttk.Frame):
    """Widget that displays validation errors from all form pages"""

    def __init__(self, parent, main_window):
        super().__init__(parent, relief="raised", borderwidth=1)
        self.main_window = main_window
        self.errors = {}  # page_id -> list of error messages

        self.build_ui()

    def build_ui(self):
        """Build the validation summary UI"""
        # Header
        header = ttk.Label(
            self,
            text="⚠️ Form Validation Summary",
            font=("Arial", 12, "bold"),
            foreground="red"
        )
        header.pack(pady=(10, 5), padx=10, anchor="w")

        # Error list frame
        self.error_frame = ttk.Frame(self)
        self.error_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Initially hide if no errors
        self.pack_forget()

    def update_errors(self, errors: Dict[str, List[str]]):
        """Update the validation errors display"""
        self.errors = errors

        # Clear existing error widgets
        for widget in self.error_frame.winfo_children():
            widget.destroy()

        total_errors = sum(len(error_list) for error_list in errors.values())

        if total_errors == 0:
            # No errors - hide the summary
            self.pack_forget()
            return

        # Show the summary
        self.pack(fill="x", pady=(10, 0))

        # Add error summary
        summary_text = f"Found {total_errors} validation error{'s' if total_errors != 1 else ''} across {len([e for e in errors.values() if e])} page{'s' if len([e for e in errors.values() if e]) != 1 else ''}"
        summary_label = ttk.Label(
            self.error_frame,
            text=summary_text,
            font=("Arial", 10, "bold"),
            foreground="red"
        )
        summary_label.pack(anchor="w", pady=(0, 10))

        # Add errors by page
        page_names = {
            "personal_info": "Personal Information",
            "filing_status": "Filing Status",
            "income": "Income",
            "deductions": "Deductions",
            "credits": "Credits & Taxes",
            "payments": "Payments"
        }

        for page_id, error_list in errors.items():
            if not error_list:
                continue

            # Page header
            page_name = page_names.get(page_id, page_id.title())
            page_label = ttk.Label(
                self.error_frame,
                text=f"• {page_name}:",
                font=("Arial", 10, "bold")
            )
            page_label.pack(anchor="w", pady=(5, 2))

            # Error list
            for error in error_list:
                error_label = ttk.Label(
                    self.error_frame,
                    text=f"  - {error}",
                    font=("Arial", 9),
                    foreground="red"
                )
                error_label.pack(anchor="w", pady=(1, 0))

                # Make error clickable to navigate to page
                error_label.bind("<Button-1>", lambda e, p=page_id: self._navigate_to_page(p))
                error_label.config(cursor="hand2")

    def _navigate_to_page(self, page_id: str):
        """Navigate to the page with validation errors"""
        self.main_window.show_page(page_id)

    def get_error_count(self) -> int:
        """Get total number of validation errors"""
        return sum(len(error_list) for error_list in self.errors.values())