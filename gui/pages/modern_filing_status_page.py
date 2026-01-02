"""
Modern Filing Status Page - CustomTkinter Implementation

An interactive filing status selection page with detailed explanations,
visual indicators, and intelligent guidance based on user situation.
"""

import customtkinter as ctk
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class FilingStatusOption:
    """Represents a filing status option with details"""
    name: str
    code: str
    description: str
    requirements: str
    benefits: str
    common_situations: List[str]
    standard_deduction_2024: int


class ModernFilingStatusPage(ctk.CTkScrollableFrame):
    """
    Modern filing status selection page using CustomTkinter.

    Features:
    - Interactive status cards with detailed information
    - Visual selection indicators
    - Contextual help and requirements
    - Intelligent recommendations based on user profile
    """

    def __init__(self, master, config, tax_data: Optional[Dict[str, Any]] = None,
                 on_complete=None, **kwargs):
        """
        Initialize the modern filing status page.

        Args:
            master: Parent widget
            config: Application configuration
            tax_data: Current tax data dictionary
            on_complete: Callback when form is completed
        """
        super().__init__(master, **kwargs)

        self.config = config
        self.tax_data = tax_data or {}
        self.on_complete = on_complete

        # Selected filing status
        self.selected_status = ctk.StringVar()

        # Filing status options
        self.status_options = self._get_filing_status_options()

        # Build the form
        self._build_form()

        # Load existing data
        self._load_existing_data()

    def _get_filing_status_options(self) -> Dict[str, FilingStatusOption]:
        """Get all filing status options with detailed information"""
        return {
            "single": FilingStatusOption(
                name="Single",
                code="single",
                description="For unmarried individuals or those legally separated from their spouse.",
                requirements="You must be unmarried or legally separated on December 31.",
                benefits="Lower tax rates than married filing jointly. Eligible for earned income credit.",
                common_situations=[
                    "Never married",
                    "Divorced or legally separated",
                    "Widowed (if not qualifying widow(er))"
                ],
                standard_deduction_2024=14600
            ),
            "mfj": FilingStatusOption(
                name="Married Filing Jointly",
                code="mfj",
                description="For married couples who want to combine their incomes and deductions.",
                requirements="You must be married and both spouses must agree to file jointly.",
                benefits="Highest standard deduction, lower tax rates, more tax credits available.",
                common_situations=[
                    "Married couples with similar incomes",
                    "One spouse has little or no income",
                    "Want to maximize deductions and credits"
                ],
                standard_deduction_2024=29200
            ),
            "mfs": FilingStatusOption(
                name="Married Filing Separately",
                code="mfs",
                description="For married couples who choose to file separate returns.",
                requirements="You can be married, unmarried, or legally separated on December 31.",
                benefits="May be beneficial if one spouse has high medical expenses or other itemized deductions.",
                common_situations=[
                    "One spouse has high medical expenses",
                    "Spouses have very different incomes",
                    "Want to avoid community property rules"
                ],
                standard_deduction_2024=14600
            ),
            "hoh": FilingStatusOption(
                name="Head of Household",
                code="hoh",
                description="For unmarried individuals who provide a home for qualifying dependents.",
                requirements="You must be unmarried, pay more than half the cost of keeping up a home, and have a qualifying dependent.",
                benefits="Higher standard deduction than single, lower tax rates than married filing jointly.",
                common_situations=[
                    "Single parent with children",
                    "Supporting aging parents",
                    "Unmarried with dependent relatives"
                ],
                standard_deduction_2024=21900
            ),
            "qw": FilingStatusOption(
                name="Qualifying Widow(er)",
                code="qw",
                description="For widows and widowers who haven't remarried within 2 years.",
                requirements="Spouse died within the past 2 years, you haven't remarried, and you have a dependent child.",
                benefits="Same benefits as married filing jointly for 2 years after spouse's death.",
                common_situations=[
                    "Widowed within last 2 years",
                    "Have dependent children",
                    "Haven't remarried"
                ],
                standard_deduction_2024=29200
            )
        }

    def _build_form(self):
        """Build the modern filing status form"""
        # Main content frame
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header section
        header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        title_label = ctk.CTkLabel(
            header_frame,
            text="Choose Your Filing Status",
            font=ctk.CTkFont(size=24)
        )
        title_label.pack(anchor="w", pady=(0, 5))

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Your filing status determines your tax rates, standard deduction, and eligibility for credits. Choose the option that best describes your situation.",
            font=ctk.CTkFont(size=12),
            text_color="gray60",
            wraplength=600
        )
        subtitle_label.pack(anchor="w")

        # Status selection cards
        self._build_status_cards(content_frame)

        # Additional information section
        self._build_additional_info(content_frame)

        # Action buttons
        self._build_action_buttons(content_frame)

    def _build_status_cards(self, parent):
        """Build interactive filing status selection cards"""
        cards_frame = ctk.CTkFrame(parent, fg_color="transparent")
        cards_frame.pack(fill="x", pady=(20, 0))

        # Instructions
        instruction_label = ctk.CTkLabel(
            cards_frame,
            text="Select the filing status that applies to you:",
            font=ctk.CTkFont(size=14)
        )
        instruction_label.pack(anchor="w", pady=(0, 15))

        # Status cards container
        self.status_cards = {}

        for status_key, status_info in self.status_options.items():
            card = self._create_status_card(cards_frame, status_key, status_info)
            self.status_cards[status_key] = card
            card.pack(fill="x", pady=(0, 10))

    def _create_status_card(self, parent, status_key: str, status_info: FilingStatusOption):
        """Create an interactive status selection card"""
        # Card frame
        card_frame = ctk.CTkFrame(parent, border_width=2)
        card_frame.configure(border_color="transparent")  # Default no border

        # Header with radio button and title
        header_frame = ctk.CTkFrame(card_frame, fg_color="transparent", height=40)
        header_frame.pack(fill="x", padx=15, pady=(15, 10))
        header_frame.pack_propagate(False)

        # Radio button
        radio = ctk.CTkRadioButton(
            header_frame,
            text=status_info.name,
            variable=self.selected_status,
            value=status_key,
            command=lambda: self._on_status_selected(status_key),
            font=ctk.CTkFont(size=14)
        )
        radio.pack(side="left")

        # Standard deduction badge
        deduction_label = ctk.CTkLabel(
            header_frame,
            text=f"${status_info.standard_deduction_2024:,} deduction",
            font=ctk.CTkFont(size=10),
            text_color="gray60"
        )
        deduction_label.pack(side="right")

        # Description
        desc_label = ctk.CTkLabel(
            card_frame,
            text=status_info.description,
            font=ctk.CTkFont(size=11),
            wraplength=500
        )
        desc_label.pack(anchor="w", padx=15, pady=(0, 10))

        # Requirements (collapsible)
        req_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        req_frame.pack(fill="x", padx=15, pady=(0, 15))

        req_title = ctk.CTkLabel(
            req_frame,
            text="📋 Requirements",
            font=ctk.CTkFont(size=11),
            cursor="hand2"
        )
        req_title.pack(anchor="w")
        req_title.bind("<Button-1>", lambda e: self._toggle_requirements(status_key))

        self.requirements_labels = {}
        req_details = ctk.CTkLabel(
            req_frame,
            text=status_info.requirements,
            font=ctk.CTkFont(size=10),
            text_color="gray60",
            wraplength=480
        )
        req_details.pack(anchor="w", pady=(5, 0))
        req_details.pack_forget()  # Initially hidden
        self.requirements_labels[status_key] = req_details

        # Common situations
        situations_text = "Common situations: " + ", ".join(status_info.common_situations[:2])
        if len(status_info.common_situations) > 2:
            situations_text += f", +{len(status_info.common_situations) - 2} more"

        situations_label = ctk.CTkLabel(
            card_frame,
            text=situations_text,
            font=ctk.CTkFont(size=10),
            text_color="gray50",
            wraplength=500
        )
        situations_label.pack(anchor="w", padx=15, pady=(0, 15))

        # Store card reference for selection highlighting
        card_frame.status_key = status_key

        return card_frame

    def _toggle_requirements(self, status_key: str):
        """Toggle the visibility of requirements details"""
        if status_key in self.requirements_labels:
            label = self.requirements_labels[status_key]
            if label.winfo_viewable():
                label.pack_forget()
            else:
                label.pack(anchor="w", pady=(5, 0))

    def _on_status_selected(self, status_key: str):
        """Handle filing status selection"""
        # Update card borders to show selection
        for key, card in self.status_cards.items():
            if key == status_key:
                card.configure(border_color="#1f538d")  # Primary color
            else:
                card.configure(border_color="transparent")

        # Show additional information based on selection
        self._update_additional_info(status_key)

    def _build_additional_info(self, parent):
        """Build the additional information section"""
        additional_frame = ctk.CTkFrame(parent)
        additional_frame.pack(fill="x", pady=(20, 0))

        # Section title
        title_label = ctk.CTkLabel(
            additional_frame,
            text="Additional Information",
            font=ctk.CTkFont(size=18)
        )
        title_label.pack(anchor="w", padx=15, pady=(15, 10))

        # Dependent question
        dependent_frame = ctk.CTkFrame(additional_frame, fg_color="transparent")
        dependent_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.is_dependent_var = ctk.BooleanVar()

        dependent_cb = ctk.CTkCheckBox(
            dependent_frame,
            text="Someone can claim you as a dependent on their tax return",
            variable=self.is_dependent_var,
            font=ctk.CTkFont(size=12)
        )
        dependent_cb.pack(anchor="w", pady=(0, 5))

        dependent_help = ctk.CTkLabel(
            dependent_frame,
            text="Check this if your parents, another relative, or someone else can claim you as a dependent. This may affect your eligibility for certain credits.",
            font=ctk.CTkFont(size=10),
            text_color="gray60",
            wraplength=500
        )
        dependent_help.pack(anchor="w")

        # Status-specific information (initially hidden)
        self.status_info_frame = ctk.CTkFrame(additional_frame, fg_color="transparent")
        self.status_info_frame.pack(fill="x", padx=15, pady=(10, 15))

    def _update_additional_info(self, status_key: str):
        """Update additional information based on selected status"""
        # Clear existing content
        for widget in self.status_info_frame.winfo_children():
            widget.destroy()

        if not status_key or status_key not in self.status_options:
            return

        status_info = self.status_options[status_key]

        # Benefits section
        benefits_title = ctk.CTkLabel(
            self.status_info_frame,
            text="💡 Benefits of this filing status:",
            font=ctk.CTkFont(size=12)
        )
        benefits_title.pack(anchor="w", pady=(0, 5))

        benefits_label = ctk.CTkLabel(
            self.status_info_frame,
            text=status_info.benefits,
            font=ctk.CTkFont(size=11),
            wraplength=500
        )
        benefits_label.pack(anchor="w", pady=(0, 10))

        # Tax implications
        tax_title = ctk.CTkLabel(
            self.status_info_frame,
            text="📊 Tax Implications:",
            font=ctk.CTkFont(size=12)
        )
        tax_title.pack(anchor="w", pady=(0, 5))

        tax_info = ctk.CTkLabel(
            self.status_info_frame,
            text=f"• Standard deduction: ${status_info.standard_deduction_2024:,}\n"
                 f"• May affect eligibility for certain credits and deductions\n"
                 f"• Determines tax bracket thresholds",
            font=ctk.CTkFont(size=11),
            wraplength=500
        )
        tax_info.pack(anchor="w")

    def _build_action_buttons(self, parent):
        """Build action buttons"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", pady=(30, 20))

        # Progress indicator
        progress_label = ctk.CTkLabel(
            button_frame,
            text="Step 2 of 7: Filing Status",
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        )
        progress_label.pack(anchor="w", pady=(0, 10))

        # Buttons
        button_row = ctk.CTkFrame(button_frame, fg_color="transparent")
        button_row.pack(fill="x")

        from gui.modern_ui_components import ModernButton

        ModernButton(
            button_row,
            text="← Back to Personal Info",
            command=self._go_back,
            button_type="secondary"
        ).pack(side="left")

        ModernButton(
            button_row,
            text="Save and Continue →",
            command=self._save_and_continue,
            button_type="primary"
        ).pack(side="right")

    def _load_existing_data(self):
        """Load existing filing status data"""
        filing_status = self.tax_data.get("filing_status", {})

        # Set selected status
        status = filing_status.get("status", "")
        if status:
            self.selected_status.set(status)
            self._on_status_selected(status)

        # Set dependent status
        is_dependent = filing_status.get("is_dependent", False)
        self.is_dependent_var.set(is_dependent)

    def _save_and_continue(self):
        """Save form data and continue to next step"""
        selected_status = self.selected_status.get()

        if not selected_status:
            from gui.modern_ui_components import show_error_message
            show_error_message(
                "Selection Required",
                "Please select a filing status before continuing."
            )
            return

        # Save data
        filing_status_data = {
            "status": selected_status,
            "is_dependent": self.is_dependent_var.get(),
            "status_name": self.status_options[selected_status].name,
            "standard_deduction": self.status_options[selected_status].standard_deduction_2024,
            "completed": True
        }

        if "filing_status" not in self.tax_data:
            self.tax_data["filing_status"] = {}
        self.tax_data["filing_status"].update(filing_status_data)

        # Call completion callback
        if self.on_complete:
            self.on_complete(self.tax_data)

    def _go_back(self):
        """Go back to the previous step"""
        if self.on_complete:
            self.on_complete(self.tax_data, action="back")

    def get_data(self) -> Dict[str, Any]:
        """Get the current form data"""
        return self.tax_data

    def is_complete(self) -> bool:
        """Check if the filing status section is complete"""
        filing_status = self.tax_data.get("filing_status", {})
        return filing_status.get("completed", False)

    def get_progress_percentage(self) -> float:
        """Get completion percentage for this section"""
        if self.is_complete():
            return 100.0

        # Check if status is selected
        if self.selected_status.get():
            return 100.0  # Complete once status is selected

        return 0.0