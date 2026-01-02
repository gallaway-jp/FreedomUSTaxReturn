"""
Modern Personal Information Page - CustomTkinter Implementation

A modern, user-friendly personal information collection page with
intelligent validation, contextual help, and guided data entry.
"""

import customtkinter as ctk
from typing import Optional, Dict, Any
import re

from gui.modern_ui_components import (
    ModernFrame, ModernLabel, ModernEntry, ModernButton,
    ModernScrollableFrame, validate_ssn, validate_zip_code
)
from services.form_recommendation_service import FormRecommendationService


class ModernPersonalInfoPage(ModernScrollableFrame):
    """
    Modern personal information collection page using CustomTkinter.

    Features:
    - Clean, modern interface with contextual help
    - Real-time validation with helpful error messages
    - Progressive disclosure of fields
    - Integration with form recommendation service
    """

    def __init__(self, master, config, tax_data: Optional[Dict[str, Any]] = None,
                 on_complete=None, **kwargs):
        """
        Initialize the modern personal info page.

        Args:
            master: Parent widget
            config: Application configuration
            tax_data: Current tax data dictionary
            on_complete: Callback when form is completed
        """
        super().__init__(master, title="Personal Information", **kwargs)

        self.config = config
        self.tax_data = tax_data or {}
        self.on_complete = on_complete
        self.recommendation_service = FormRecommendationService(config)

        # Form field references
        self.fields = {}

        # Build the form
        self._build_form()

        # Load existing data if available
        self._load_existing_data()

    def _build_form(self):
        """Build the modern personal information form"""
        # Main content frame
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header section
        header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        title_label = ModernLabel(
            header_frame,
            text="Tell us about yourself",
            font=ctk.CTkFont(size=24)
        )
        title_label.pack(anchor="w", pady=(0, 5))

        subtitle_label = ModernLabel(
            header_frame,
            text="We'll use this information to prepare your tax return. All fields marked with * are required.",
            font=ctk.CTkFont(size=12),
            text_color="gray60",
            wraplength=600
        )
        subtitle_label.pack(anchor="w")

        # Taxpayer Information Section
        taxpayer_section = self._create_section(
            content_frame,
            "Taxpayer Information",
            "Enter your full name and basic information as it appears on your Social Security card."
        )

        # Name fields
        name_frame = ctk.CTkFrame(taxpayer_section, fg_color="transparent")
        name_frame.pack(fill="x", pady=(10, 0))

        # First name and middle initial
        name_row1 = ctk.CTkFrame(name_frame, fg_color="transparent")
        name_row1.pack(fill="x", pady=(0, 10))

        self.fields['first_name'] = ModernEntry(
            name_row1,
            label_text="First Name",
            help_text="Your legal first name as shown on your Social Security card",
            required=True
        )
        self.fields['first_name'].pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.fields['middle_initial'] = ModernEntry(
            name_row1,
            label_text="Middle Initial",
            help_text="Your middle initial (optional)",
            required=False
        )
        self.fields['middle_initial'].pack(side="left", padx=(0, 10))
        self.fields['middle_initial'].configure(width=80)

        # Last name
        self.fields['last_name'] = ModernEntry(
            name_frame,
            label_text="Last Name",
            help_text="Your legal last name as shown on your Social Security card",
            required=True
        )
        self.fields['last_name'].pack(fill="x", pady=(10, 0))

        # SSN and Date of Birth
        identity_frame = ctk.CTkFrame(taxpayer_section, fg_color="transparent")
        identity_frame.pack(fill="x", pady=(20, 0))

        identity_row = ctk.CTkFrame(identity_frame, fg_color="transparent")
        identity_row.pack(fill="x", pady=(0, 10))

        self.fields['ssn'] = ModernEntry(
            identity_row,
            label_text="Social Security Number",
            help_text="Enter your 9-digit SSN in XXX-XX-XXXX format. Required for tax filing.",
            validator=validate_ssn,
            required=True
        )
        self.fields['ssn'].pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.fields['date_of_birth'] = ModernEntry(
            identity_row,
            label_text="Date of Birth",
            help_text="Enter in MM/DD/YYYY format. Used to determine filing requirements.",
            required=True
        )
        self.fields['date_of_birth'].pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Occupation
        self.fields['occupation'] = ModernEntry(
            taxpayer_section,
            label_text="Occupation",
            help_text="Your current job title or profession (optional but recommended)",
            required=False
        )
        self.fields['occupation'].pack(fill="x", pady=(20, 0))

        # Mailing Address Section
        address_section = self._create_section(
            content_frame,
            "Mailing Address",
            "Enter your current mailing address. This is where the IRS will send any correspondence."
        )

        # Street address
        self.fields['address'] = ModernEntry(
            address_section,
            label_text="Street Address",
            help_text="Your complete street address including apartment/unit number",
            required=True
        )
        self.fields['address'].pack(fill="x", pady=(10, 0))

        # City, State, ZIP
        location_frame = ctk.CTkFrame(address_section, fg_color="transparent")
        location_frame.pack(fill="x", pady=(20, 0))

        location_row = ctk.CTkFrame(location_frame, fg_color="transparent")
        location_row.pack(fill="x", pady=(0, 10))

        self.fields['city'] = ModernEntry(
            location_row,
            label_text="City",
            help_text="Your city of residence",
            required=True
        )
        self.fields['city'].pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.fields['state'] = ModernEntry(
            location_row,
            label_text="State",
            help_text="Your state (use 2-letter abbreviation)",
            required=True
        )
        self.fields['state'].pack(side="left", padx=(0, 10))
        self.fields['state'].configure(width=100)

        self.fields['zip_code'] = ModernEntry(
            location_row,
            label_text="ZIP Code",
            help_text="Your 5-digit ZIP code (or ZIP+4)",
            validator=validate_zip_code,
            required=True
        )
        self.fields['zip_code'].pack(side="left")
        self.fields['zip_code'].configure(width=120)

        # Contact Information Section
        contact_section = self._create_section(
            content_frame,
            "Contact Information",
            "Optional contact information for IRS communications and tax preparation."
        )

        contact_row = ctk.CTkFrame(contact_section, fg_color="transparent")
        contact_row.pack(fill="x", pady=(10, 0))

        self.fields['email'] = ModernEntry(
            contact_row,
            label_text="Email Address",
            help_text="Your email address for electronic communications",
            required=False
        )
        self.fields['email'].pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.fields['phone'] = ModernEntry(
            contact_row,
            label_text="Phone Number",
            help_text="Your phone number including area code",
            required=False
        )
        self.fields['phone'].pack(side="left", fill="x", expand=True)

        # Action buttons
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(30, 20))

        # Progress indicator
        progress_label = ModernLabel(
            button_frame,
            text="Step 1 of 7: Personal Information",
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        )
        progress_label.pack(anchor="w", pady=(0, 10))

        # Buttons
        button_row = ctk.CTkFrame(button_frame, fg_color="transparent")
        button_row.pack(fill="x")

        ModernButton(
            button_row,
            text="← Back to Interview",
            command=self._go_back,
            button_type="secondary"
        ).pack(side="left")

        ModernButton(
            button_row,
            text="Save and Continue →",
            command=self._save_and_continue,
            button_type="primary"
        ).pack(side="right")

    def _create_section(self, parent, title: str, description: str) -> ctk.CTkFrame:
        """Create a form section with title and description"""
        section_frame = ctk.CTkFrame(parent)
        section_frame.pack(fill="x", pady=(20, 0))

        # Section title
        title_label = ModernLabel(
            section_frame,
            text=title,
            font=ctk.CTkFont(size=18)
        )
        title_label.pack(anchor="w", pady=(15, 5), padx=15)

        # Section description
        if description:
            desc_label = ModernLabel(
                section_frame,
                text=description,
                font=ctk.CTkFont(size=11),
                text_color="gray60",
                wraplength=550
            )
            desc_label.pack(anchor="w", pady=(0, 10), padx=15)

        # Content container
        content_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=15, pady=(0, 15))

        return content_frame

    def _load_existing_data(self):
        """Load existing personal information data"""
        personal_info = self.tax_data.get("personal_info", {})

        field_mappings = {
            'first_name': 'first_name',
            'middle_initial': 'middle_initial',
            'last_name': 'last_name',
            'ssn': 'ssn',
            'date_of_birth': 'date_of_birth',
            'occupation': 'occupation',
            'address': 'address',
            'city': 'city',
            'state': 'state',
            'zip_code': 'zip_code',
            'email': 'email',
            'phone': 'phone'
        }

        for field_name, data_key in field_mappings.items():
            if field_name in self.fields:
                value = personal_info.get(data_key, "")
                self.fields[field_name].insert(0, str(value))

    def _validate_form(self) -> bool:
        """Validate all form fields"""
        all_valid = True
        first_invalid_field = None

        # Check required fields
        required_fields = ['first_name', 'last_name', 'ssn', 'date_of_birth', 'address', 'city', 'state', 'zip_code']

        for field_name in required_fields:
            if field_name in self.fields:
                field = self.fields[field_name]
                value = field.get().strip()

                if not value:
                    field.configure(border_color="red")
                    if not first_invalid_field:
                        first_invalid_field = field
                    all_valid = False
                else:
                    field.configure(border_color=["#979DA2", "#565B5E"])

        # Validate specific field formats
        if 'ssn' in self.fields:
            ssn_field = self.fields['ssn']
            valid, formatted_ssn = validate_ssn(ssn_field.get())
            if not valid:
                ssn_field.configure(border_color="red")
                all_valid = False
                if not first_invalid_field:
                    first_invalid_field = ssn_field

        if 'zip_code' in self.fields:
            zip_field = self.fields['zip_code']
            valid, formatted_zip = validate_zip_code(zip_field.get())
            if not valid:
                zip_field.configure(border_color="red")
                all_valid = False
                if not first_invalid_field:
                    first_invalid_field = zip_field

        # Focus on first invalid field
        if first_invalid_field:
            first_invalid_field.focus()

        return all_valid

    def _save_and_continue(self):
        """Save form data and continue to next step"""
        if not self._validate_form():
            from gui.modern_ui_components import show_error_message
            show_error_message(
                "Validation Error",
                "Please correct the highlighted fields before continuing."
            )
            return

        # Collect form data
        personal_info = {}

        field_mappings = {
            'first_name': 'first_name',
            'middle_initial': 'middle_initial',
            'last_name': 'last_name',
            'ssn': 'ssn',
            'date_of_birth': 'date_of_birth',
            'occupation': 'occupation',
            'address': 'address',
            'city': 'city',
            'state': 'state',
            'zip_code': 'zip_code',
            'email': 'email',
            'phone': 'phone'
        }

        for field_name, data_key in field_mappings.items():
            if field_name in self.fields:
                value = self.fields[field_name].get().strip()
                if value:  # Only save non-empty values
                    personal_info[data_key] = value

        # Update tax data
        if "personal_info" not in self.tax_data:
            self.tax_data["personal_info"] = {}
        self.tax_data["personal_info"].update(personal_info)

        # Mark personal info as complete
        self.tax_data["personal_info"]["completed"] = True

        # Generate form recommendations based on completed data
        try:
            from models.tax_data import TaxData
            temp_tax_data = TaxData()
            temp_tax_data.personal_info = personal_info

            recommendations = self.recommendation_service.analyze_tax_data(temp_tax_data)

            # Store recommendations
            self.tax_data["_recommendations"] = [
                {
                    "form": rec.form_name,
                    "category": rec.form_type.value,
                    "priority": rec.priority.value,
                    "reason": rec.reason,
                    "estimated_time": rec.estimated_time
                }
                for rec in recommendations
            ]

        except Exception as e:
            print(f"Warning: Could not generate recommendations: {e}")

        # Call completion callback
        if self.on_complete:
            self.on_complete(self.tax_data)

    def _go_back(self):
        """Go back to the interview or previous step"""
        if self.on_complete:
            self.on_complete(self.tax_data, action="back")

    def get_data(self) -> Dict[str, Any]:
        """Get the current form data"""
        return self.tax_data

    def is_complete(self) -> bool:
        """Check if the personal info section is complete"""
        personal_info = self.tax_data.get("personal_info", {})
        return personal_info.get("completed", False)

    def get_progress_percentage(self) -> float:
        """Get completion percentage for this section"""
        if self.is_complete():
            return 100.0

        # Calculate based on filled required fields
        required_fields = ['first_name', 'last_name', 'ssn', 'date_of_birth', 'address', 'city', 'state', 'zip_code']
        filled_count = 0

        for field_name in required_fields:
            if field_name in self.fields:
                value = self.fields[field_name].get().strip()
                if value:
                    filled_count += 1

        return (filled_count / len(required_fields)) * 100.0