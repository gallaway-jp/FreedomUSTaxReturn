"""
Modern Amended Return Page - Create and manage amended tax returns

Provides an interface to create Form 1040-X amended returns.
"""

import customtkinter as ctk
from typing import Optional, Callable, Dict, Any
import tkinter as tk
from datetime import datetime

from models.tax_data import TaxData
from gui.modern_ui_components import (
    ModernFrame, ModernLabel, ModernButton, ModernEntry,
    show_info_message, show_error_message
)


class ModernAmendedReturnPage(ctk.CTkScrollableFrame):
    """
    Modern amended return page for creating Form 1040-X.

    Features:
    - Select tax year to amend
    - Specify reason for amendment
    - Document explanation of changes
    - Create amended return record
    """

    def __init__(
        self,
        parent,
        tax_data: Optional[TaxData] = None,
        on_amended_created: Optional[Callable] = None,
        **kwargs
    ):
        """
        Initialize the amended return page.

        Args:
            parent: Parent widget
            tax_data: Current tax data
            on_amended_created: Callback when amended return is created
        """
        super().__init__(parent, **kwargs)

        self.tax_data = tax_data
        self.on_amended_created = on_amended_created
        self.amended_result: Optional[Dict[str, Any]] = None

        # Configure grid
        self.grid_columnconfigure(0, weight=1)

        # Create UI
        self._create_header()
        self._create_original_return_section()
        self._create_reason_section()
        self._create_explanation_section()
        self._create_action_section()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        title_label = ModernLabel(
            header_frame,
            text="📝 Create Amended Return",
            font=ctk.CTkFont(size=18)
        )
        title_label.pack(anchor="w")

        instructions = (
            "An amended return (Form 1040-X) is used to correct errors or make changes "
            "to a previously filed tax return. Select the tax year you want to amend "
            "and provide the required information."
        )
        subtitle_label = ModernLabel(
            header_frame,
            text=instructions,
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        )
        subtitle_label.pack(anchor="w", pady=(5, 0))

    def _create_original_return_section(self):
        """Create the original return information section"""
        orig_frame = ModernFrame(self)
        orig_frame.pack(fill="x", padx=20, pady=15)

        orig_title = ModernLabel(
            orig_frame,
            text="🗂️ Original Return Information",
            font=ctk.CTkFont(size=12)
        )
        orig_title.pack(anchor="w", pady=(0, 10))

        # Tax year selection
        year_row = ctk.CTkFrame(orig_frame, fg_color="transparent")
        year_row.pack(fill="x", pady=8)

        year_label = ModernLabel(year_row, text="Tax Year to Amend:", width=200)
        year_label.pack(side="left", padx=(0, 10))

        self.year_var = ctk.StringVar()
        year_combo = ctk.CTkComboBox(
            year_row,
            values=["2025", "2024", "2023", "2022", "2021", "2020"],
            variable=self.year_var,
            width=150
        )
        year_combo.set(str(datetime.now().year - 1))
        year_combo.pack(side="left")

        # Filing date
        date_row = ctk.CTkFrame(orig_frame, fg_color="transparent")
        date_row.pack(fill="x", pady=8)

        date_label = ModernLabel(date_row, text="Original Filing Date (MM/DD/YYYY):", width=200)
        date_label.pack(side="left", padx=(0, 10))

        self.filing_date_entry = ctk.CTkEntry(date_row, placeholder_text="MM/DD/YYYY", width=150)
        self.filing_date_entry.pack(side="left")

    def _create_reason_section(self):
        """Create the reason for amendment section"""
        reason_frame = ModernFrame(self)
        reason_frame.pack(fill="x", padx=20, pady=15)

        reason_title = ModernLabel(
            reason_frame,
            text="⚠️ Reason for Amendment",
            font=ctk.CTkFont(size=12)
        )
        reason_title.pack(anchor="w", pady=(0, 10))

        info_label = ModernLabel(
            reason_frame,
            text="Select all applicable reason codes:",
            font=ctk.CTkFont(size=11),
            text_color="gray70"
        )
        info_label.pack(anchor="w", pady=(0, 10))

        # Reason code checkboxes
        self.reason_vars: Dict[str, ctk.BooleanVar] = {}
        reasons = [
            ('A', 'Income (wages, interest, etc.)'),
            ('B', 'Deductions (standard/itemized)'),
            ('C', 'Credits'),
            ('D', 'Filing status change'),
            ('E', 'Payments (withholding, estimated)'),
            ('F', 'Other'),
        ]

        for code, description in reasons:
            var = ctk.BooleanVar(value=False)
            self.reason_vars[code] = var

            checkbox_frame = ctk.CTkFrame(reason_frame, fg_color="transparent")
            checkbox_frame.pack(fill="x", pady=5)

            checkbox = ctk.CTkCheckBox(
                checkbox_frame,
                text=f"{code} - {description}",
                variable=var,
                onvalue=True,
                offvalue=False
            )
            checkbox.pack(anchor="w")

    def _create_explanation_section(self):
        """Create the explanation section"""
        expl_frame = ModernFrame(self)
        expl_frame.pack(fill="both", expand=True, padx=20, pady=15)

        expl_title = ModernLabel(
            expl_frame,
            text="📄 Explanation of Changes",
            font=ctk.CTkFont(size=12)
        )
        expl_title.pack(anchor="w", pady=(0, 10))

        info_label = ModernLabel(
            expl_frame,
            text="Describe what changes you're making and why:",
            font=ctk.CTkFont(size=11),
            text_color="gray70"
        )
        info_label.pack(anchor="w", pady=(0, 10))

        # Create text widget with CustomTkinter styling
        text_frame = ctk.CTkFrame(expl_frame)
        text_frame.pack(fill="both", expand=True)

        self.explanation_text = tk.Text(
            text_frame,
            height=8,
            width=70,
            wrap=tk.WORD,
            font=("Arial", 10),
            bg="gray17",
            fg="gray90",
            insertbackground="gray90"
        )
        self.explanation_text.pack(fill="both", expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(text_frame, command=self.explanation_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.explanation_text.config(yscrollcommand=scrollbar.set)

    def _create_action_section(self):
        """Create the action buttons section"""
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=20)

        ModernButton(
            action_frame,
            text="✓ Create Amended Return",
            command=self._create_amended,
            height=40,
            width=200
        ).pack(side="left", padx=(0, 10))

        ModernButton(
            action_frame,
            text="Cancel",
            command=self._cancel,
            height=40,
            width=100,
            button_type="secondary"
        ).pack(side="left")

    def _create_amended(self):
        """Create the amended return"""
        try:
            # Validate input
            if not self.year_var.get():
                show_error_message("Missing Information", "Please select a tax year to amend.")
                return

            # Check if at least one reason is selected
            selected_reasons = [code for code, var in self.reason_vars.items() if var.get()]
            if not selected_reasons:
                show_error_message("Missing Information", "Please select at least one reason for the amendment.")
                return

            explanation = self.explanation_text.get("1.0", "end-1c").strip()
            if not explanation:
                show_error_message("Missing Information", "Please provide an explanation of the changes.")
                return

            # Create amended return result
            self.amended_result = {
                'tax_year': int(self.year_var.get()),
                'filing_date': self.filing_date_entry.get(),
                'reasons': selected_reasons,
                'explanation': explanation,
                'created_date': datetime.now().isoformat()
            }

            # Show success message
            show_info_message(
                "Amended Return Created",
                f"Amended return for tax year {self.amended_result['tax_year']} has been created.\n\n"
                "You can now modify the return data and file the amended return."
            )

            # Trigger callback if provided
            if self.on_amended_created:
                self.on_amended_created(self.amended_result)

        except Exception as e:
            show_error_message("Error", f"Failed to create amended return: {str(e)}")

    def _cancel(self):
        """Cancel the amended return creation"""
        self.amended_result = None
        show_info_message("Cancelled", "Amended return creation cancelled.")


# Import ttk for Scrollbar styling
from tkinter import ttk
