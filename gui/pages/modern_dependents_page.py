"""
Modern Dependents Page - CustomTkinter Implementation

A comprehensive dependents management interface with modern UI,
intelligent validation, and detailed dependent information tracking.
"""

import customtkinter as ctk
from typing import Optional, Dict, Any, List
from datetime import datetime
import re


class ModernDependentsPage(ctk.CTkScrollableFrame):
    """
    Modern dependents management page using CustomTkinter.

    Features:
    - Interactive dependents list with detailed information
    - Modern dialog for adding/editing dependents
    - Real-time validation and age calculation
    - Tax credit eligibility indicators
    - Relationship-based guidance
    """

    def __init__(self, master, config, tax_data: Optional[Dict[str, Any]] = None,
                 on_complete=None, **kwargs):
        """
        Initialize the modern dependents page.

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

        # Build the form
        self._build_form()

        # Load existing data
        self._load_existing_data()

    def _build_form(self):
        """Build the modern dependents form"""
        # Main content frame
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header section
        header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        title_label = ctk.CTkLabel(
            header_frame,
            text="Dependents Information",
            font=ctk.CTkFont(size=24)
        )
        title_label.pack(anchor="w", pady=(0, 5))

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Add information for all qualifying children and other dependents you plan to claim on your tax return. This affects your eligibility for tax credits like the Child Tax Credit and Child and Dependent Care Credit.",
            font=ctk.CTkFont(size=12),
            text_color="gray60",
            wraplength=600
        )
        subtitle_label.pack(anchor="w")

        # Quick info section
        self._build_quick_info(content_frame)

        # Dependents management section
        self._build_dependents_section(content_frame)

        # Action buttons
        self._build_action_buttons(content_frame)

    def _build_quick_info(self, parent):
        """Build the quick information section"""
        info_frame = ctk.CTkFrame(parent, fg_color="#f0f8ff", border_width=1)
        info_frame.pack(fill="x", pady=(0, 20))

        info_title = ctk.CTkLabel(
            info_frame,
            text="💡 Qualifying Child Requirements (2024)",
            font=ctk.CTkFont(size=14)
        )
        info_title.pack(anchor="w", padx=15, pady=(15, 10))

        requirements_text = """• Under age 19 (or 24 if full-time student)
• Lived with you for more than half the year
• Didn't provide more than half their own support
• Related to you (child, stepchild, sibling, etc.)"""

        requirements_label = ctk.CTkLabel(
            info_frame,
            text=requirements_text,
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        requirements_label.pack(anchor="w", padx=15, pady=(0, 15))

    def _build_dependents_section(self, parent):
        """Build the dependents management section"""
        section_frame = ctk.CTkFrame(parent)
        section_frame.pack(fill="both", expand=True, pady=(0, 20))

        # Section header
        header_label = ctk.CTkLabel(
            section_frame,
            text="Your Dependents",
            font=ctk.CTkFont(size=18)
        )
        header_label.pack(anchor="w", padx=15, pady=(15, 10))

        # Dependents list container
        list_container = ctk.CTkFrame(section_frame, fg_color="transparent")
        list_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Empty state
        self.empty_state_frame = ctk.CTkFrame(list_container, fg_color="transparent")
        self.empty_state_frame.pack(fill="both", expand=True)

        empty_icon = ctk.CTkLabel(
            self.empty_state_frame,
            text="👨‍👩‍👧‍👦",
            font=ctk.CTkFont(size=48)
        )
        empty_icon.pack(pady=(20, 10))

        empty_title = ctk.CTkLabel(
            self.empty_state_frame,
            text="No Dependents Added Yet",
            font=ctk.CTkFont(size=16)
        )
        empty_title.pack(pady=(0, 5))

        empty_desc = ctk.CTkLabel(
            self.empty_state_frame,
            text="Click 'Add Dependent' to start adding family members who qualify as dependents.",
            font=ctk.CTkFont(size=12),
            text_color="gray60",
            wraplength=400
        )
        empty_desc.pack(pady=(0, 20))

        # Dependents list (initially hidden)
        self.dependents_frame = ctk.CTkScrollableFrame(list_container, height=300)
        # Initially hide the dependents frame

        # Add dependent button
        from gui.modern_ui_components import ModernButton

        button_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=(0, 15))

        ModernButton(
            button_frame,
            text="+ Add Dependent",
            command=self._add_dependent,
            button_type="primary"
        ).pack(anchor="w")

    def _build_action_buttons(self, parent):
        """Build action buttons"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", pady=(30, 20))

        # Progress indicator
        progress_label = ctk.CTkLabel(
            button_frame,
            text="Step 3 of 7: Dependents",
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
            text="← Back to Filing Status",
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
        """Load existing dependents data"""
        dependents = self.tax_data.get("dependents", [])
        self._refresh_dependents_display(dependents)

    def _refresh_dependents_display(self, dependents: List[Dict[str, Any]]):
        """Refresh the dependents display"""
        # Clear existing dependents frame
        for widget in self.dependents_frame.winfo_children():
            widget.destroy()

        if not dependents:
            # Show empty state
            self.empty_state_frame.pack(fill="both", expand=True)
            self.dependents_frame.pack_forget()
            return

        # Hide empty state and show dependents
        self.empty_state_frame.pack_forget()
        self.dependents_frame.pack(fill="both", expand=True, pady=(10, 0))

        # Add each dependent
        for i, dependent in enumerate(dependents):
            self._create_dependent_card(dependent, i)

    def _create_dependent_card(self, dependent: Dict[str, Any], index: int):
        """Create a dependent information card"""
        card_frame = ctk.CTkFrame(self.dependents_frame, border_width=1)
        card_frame.pack(fill="x", pady=(0, 10), padx=(0, 10))

        # Header with name and relationship
        header_frame = ctk.CTkFrame(card_frame, fg_color="transparent", height=35)
        header_frame.pack(fill="x", padx=15, pady=(10, 5))
        header_frame.pack_propagate(False)

        name = f"{dependent.get('first_name', '')} {dependent.get('last_name', '')}".strip()
        relationship = dependent.get('relationship', 'Unknown')

        name_label = ctk.CTkLabel(
            header_frame,
            text=name,
            font=ctk.CTkFont(size=14)
        )
        name_label.pack(side="left")

        relationship_label = ctk.CTkLabel(
            header_frame,
            text=relationship,
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        )
        relationship_label.pack(side="left", padx=(10, 0))

        # Action buttons
        actions_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        actions_frame.pack(side="right")

        from gui.modern_ui_components import ModernButton

        ModernButton(
            actions_frame,
            text="Edit",
            command=lambda: self._edit_dependent(index),
            button_type="secondary",
            width=60,
            height=25
        ).pack(side="left", padx=(0, 5))

        ModernButton(
            actions_frame,
            text="Delete",
            command=lambda: self._delete_dependent(index),
            button_type="danger",
            width=60,
            height=25
        ).pack(side="left")

        # Details section
        details_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        details_frame.pack(fill="x", padx=15, pady=(0, 10))

        # SSN (masked)
        ssn = dependent.get('ssn', '')
        masked_ssn = f"XXX-XX-{ssn[-4:]}" if len(ssn) >= 4 else ssn

        ssn_label = ctk.CTkLabel(
            details_frame,
            text=f"SSN: {masked_ssn}",
            font=ctk.CTkFont(size=11)
        )
        ssn_label.pack(anchor="w", pady=(0, 3))

        # Age and birth date
        birth_date_str = dependent.get('birth_date', '')
        age = self._calculate_age(birth_date_str)

        age_text = f"Age: {age}" if age else "Birth date not available"
        if birth_date_str:
            age_text += f" (DOB: {birth_date_str})"

        age_label = ctk.CTkLabel(
            details_frame,
            text=age_text,
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        )
        age_label.pack(anchor="w", pady=(0, 3))

        # Months lived in home
        months = dependent.get('months_lived_in_home', 0)
        months_label = ctk.CTkLabel(
            details_frame,
            text=f"Lived in home: {months} months",
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        )
        months_label.pack(anchor="w", pady=(0, 3))

        # Eligibility indicators
        self._add_eligibility_indicators(details_frame, dependent)

    def _add_eligibility_indicators(self, parent, dependent: Dict[str, Any]):
        """Add tax credit eligibility indicators"""
        indicators_frame = ctk.CTkFrame(parent, fg_color="transparent")
        indicators_frame.pack(fill="x", pady=(5, 0))

        age = self._calculate_age(dependent.get('birth_date', ''))
        relationship = dependent.get('relationship', '').lower()
        months = dependent.get('months_lived_in_home', 0)

        indicators = []

        # Child Tax Credit eligibility (under 17)
        if age is not None and age < 17 and relationship in ['son', 'daughter', 'step-son', 'step-daughter']:
            indicators.append(("✅ Child Tax Credit Eligible", "green"))
        elif age is not None and age >= 17:
            indicators.append(("❌ Child Tax Credit (17+)", "red"))

        # Qualifying child for other credits
        if (age is not None and age < 19) or (age is not None and age < 24 and self._is_full_time_student(dependent)):
            if months >= 7:  # More than half the year
                indicators.append(("✅ Qualifying Child", "green"))
            else:
                indicators.append(("⚠️ Qualifying Child (lived < 7 months)", "orange"))

        # Add indicators
        for indicator_text, color in indicators:
            indicator_label = ctk.CTkLabel(
                indicators_frame,
                text=indicator_text,
                font=ctk.CTkFont(size=10),
                text_color=color
            )
            indicator_label.pack(anchor="w", pady=(1, 0))

    def _is_full_time_student(self, dependent: Dict[str, Any]) -> bool:
        """Check if dependent is a full-time student (simplified check)"""
        # This would need more detailed information in a real implementation
        # For now, we'll assume based on age and relationship
        return False  # Placeholder

    def _calculate_age(self, birth_date_str: str) -> Optional[int]:
        """Calculate age from birth date string"""
        if not birth_date_str:
            return None
        try:
            birth_date = datetime.strptime(birth_date_str, '%m/%d/%Y')
            today = datetime.now()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            return age
        except:
            return None

    def _add_dependent(self):
        """Add a new dependent"""
        dialog = ModernDependentDialog(self, self.config, on_save=self._on_dependent_saved)
        dialog.grab_set()

    def _edit_dependent(self, index: int):
        """Edit an existing dependent"""
        dependents = self.tax_data.get("dependents", [])
        if index < len(dependents):
            dependent = dependents[index]
            dialog = ModernDependentDialog(
                self,
                self.config,
                dependent_data=dependent,
                edit_index=index,
                on_save=self._on_dependent_saved
            )
            dialog.grab_set()

    def _delete_dependent(self, index: int):
        """Delete a dependent"""
        dependents = self.tax_data.get("dependents", [])
        if index < len(dependents):
            dependent = dependents[index]
            name = f"{dependent.get('first_name', '')} {dependent.get('last_name', '')}".strip()

            # Show confirmation dialog
            from gui.modern_ui_components import show_confirmation_dialog
            show_confirmation_dialog(
                self,
                f"Delete Dependent",
                f"Are you sure you want to delete '{name}' from your dependents?",
                lambda: self._confirm_delete(index)
            )

    def _confirm_delete(self, index: int):
        """Confirm deletion of dependent"""
        dependents = self.tax_data.get("dependents", [])
        if index < len(dependents):
            dependent = dependents[index]
            name = f"{dependent.get('first_name', '')} {dependent.get('last_name', '')}".strip()

            dependents.pop(index)
            self.tax_data["dependents"] = dependents
            self._refresh_dependents_display(dependents)

            # Show success message
            from gui.modern_ui_components import show_success_message
            show_success_message(f"Dependent '{name}' has been deleted.")

    def _on_dependent_saved(self, dependent_data: Dict[str, Any], edit_index: Optional[int] = None):
        """Handle dependent saved event"""
        dependents = self.tax_data.get("dependents", [])

        if edit_index is not None:
            # Update existing
            dependents[edit_index] = dependent_data
            message = "Dependent updated successfully!"
        else:
            # Add new
            dependents.append(dependent_data)
            message = "Dependent added successfully!"

        self.tax_data["dependents"] = dependents
        self._refresh_dependents_display(dependents)

        # Show success message
        from gui.modern_ui_components import show_success_message
        show_success_message(message)

    def _save_and_continue(self):
        """Save form data and continue to next step"""
        # Mark dependents section as completed
        if "dependents" not in self.tax_data:
            self.tax_data["dependents"] = []

        dependents_data = {
            "completed": True,
            "count": len(self.tax_data["dependents"])
        }

        if "dependents_section" not in self.tax_data:
            self.tax_data["dependents_section"] = {}
        self.tax_data["dependents_section"].update(dependents_data)

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
        """Check if the dependents section is complete"""
        dependents_section = self.tax_data.get("dependents_section", {})
        return dependents_section.get("completed", False)

    def get_progress_percentage(self) -> float:
        """Get completion percentage for this section"""
        if self.is_complete():
            return 100.0

        dependents = self.tax_data.get("dependents", [])
        if dependents:
            return 100.0  # Complete if any dependents are added

        return 0.0


class ModernDependentDialog(ctk.CTkToplevel):
    """
    Modern dialog for entering dependent information
    """

    def __init__(self, parent, config, dependent_data: Optional[Dict[str, Any]] = None,
                 edit_index: Optional[int] = None, on_save=None):
        """
        Initialize the dependent dialog.

        Args:
            parent: Parent window
            config: Application configuration
            dependent_data: Existing dependent data for editing
            edit_index: Index of dependent being edited
            on_save: Callback when dependent is saved
        """
        super().__init__(parent)

        self.config = config
        self.dependent_data = dependent_data or {}
        self.edit_index = edit_index
        self.on_save = on_save

        self.title("Add Dependent" if edit_index is None else "Edit Dependent")
        self.geometry("600x700")

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Build the dialog
        self._build_dialog()

        # Load existing data if editing
        if dependent_data:
            self._load_dependent_data()

    def _build_dialog(self):
        """Build the dialog interface"""
        # Main container
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header_label = ctk.CTkLabel(
            main_frame,
            text="Dependent Information",
            font=ctk.CTkFont(size=18)
        )
        header_label.pack(pady=(0, 20))

        # Personal Information Section
        self._build_personal_info_section(main_frame)

        # Relationship Section
        self._build_relationship_section(main_frame)

        # Living Arrangement Section
        self._build_living_arrangement_section(main_frame)

        # Action buttons
        self._build_dialog_buttons(main_frame)

    def _build_personal_info_section(self, parent):
        """Build the personal information section"""
        section_frame = ctk.CTkFrame(parent)
        section_frame.pack(fill="x", pady=(0, 20))

        section_title = ctk.CTkLabel(
            section_frame,
            text="Personal Information",
            font=ctk.CTkFont(size=14)
        )
        section_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Name fields
        name_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        name_frame.pack(fill="x", padx=15, pady=(0, 10))

        from gui.modern_ui_components import ModernEntry

        self.first_name_entry = ModernEntry(
            name_frame,
            placeholder_text="First Name",
            required=True
        )
        self.first_name_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.last_name_entry = ModernEntry(
            name_frame,
            placeholder_text="Last Name",
            required=True
        )
        self.last_name_entry.pack(side="left", fill="x", expand=True)

        # SSN
        self.ssn_entry = ModernEntry(
            section_frame,
            placeholder_text="Social Security Number (XXX-XX-XXXX)",
            field_type="ssn",
            required=True
        )
        self.ssn_entry.pack(fill="x", padx=15, pady=(0, 10))

        # Birth date
        self.birth_date_entry = ModernEntry(
            section_frame,
            placeholder_text="Birth Date (MM/DD/YYYY)",
            field_type="date",
            required=True
        )
        self.birth_date_entry.pack(fill="x", padx=15, pady=(0, 15))

    def _build_relationship_section(self, parent):
        """Build the relationship selection section"""
        section_frame = ctk.CTkFrame(parent)
        section_frame.pack(fill="x", pady=(0, 20))

        section_title = ctk.CTkLabel(
            section_frame,
            text="Relationship to You",
            font=ctk.CTkFont(size=14)
        )
        section_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Relationship radio buttons
        relationships = [
            ("Son", "son"), ("Daughter", "daughter"),
            ("Step-son", "step-son"), ("Step-daughter", "step-daughter"),
            ("Brother", "brother"), ("Sister", "sister"),
            ("Step-brother", "step-brother"), ("Step-sister", "step-sister"),
            ("Father", "father"), ("Mother", "mother"),
            ("Grandfather", "grandfather"), ("Grandmother", "grandmother"),
            ("Grandson", "grandson"), ("Granddaughter", "granddaughter"),
            ("Uncle", "uncle"), ("Aunt", "aunt"),
            ("Nephew", "nephew"), ("Niece", "niece"),
            ("Other", "other")
        ]

        self.relationship_var = ctk.StringVar()

        # Create grid layout for relationships
        rel_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        rel_frame.pack(fill="x", padx=15, pady=(0, 15))

        for i, (display_name, value) in enumerate(relationships):
            row = i // 3
            col = i % 3

            rb = ctk.CTkRadioButton(
                rel_frame,
                text=display_name,
                variable=self.relationship_var,
                value=value,
                font=ctk.CTkFont(size=11)
            )
            rb.grid(row=row, column=col, sticky="w", padx=(0, 20), pady=3)

    def _build_living_arrangement_section(self, parent):
        """Build the living arrangement section"""
        section_frame = ctk.CTkFrame(parent)
        section_frame.pack(fill="x", pady=(0, 20))

        section_title = ctk.CTkLabel(
            section_frame,
            text="Living Arrangement",
            font=ctk.CTkFont(size=14)
        )
        section_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Months lived in home
        months_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        months_frame.pack(fill="x", padx=15, pady=(0, 15))

        months_label = ctk.CTkLabel(
            months_frame,
            text="Months lived in your home during the tax year:",
            font=ctk.CTkFont(size=12)
        )
        months_label.pack(anchor="w", pady=(0, 5))

        from gui.modern_ui_components import ModernEntry

        self.months_entry = ModernEntry(
            months_frame,
            placeholder_text="Months (0-12)",
            field_type="number",
            required=True
        )
        self.months_entry.pack(fill="x", pady=(0, 5))

        help_text = ctk.CTkLabel(
            months_frame,
            text="For a child to qualify as a dependent, they must have lived with you for more than half the year (generally 7+ months).",
            font=ctk.CTkFont(size=10),
            text_color="gray60",
            wraplength=400
        )
        help_text.pack(anchor="w")

    def _build_dialog_buttons(self, parent):
        """Build dialog action buttons"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", pady=(20, 0))

        from gui.modern_ui_components import ModernButton

        ModernButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            button_type="secondary"
        ).pack(side="left")

        ModernButton(
            button_frame,
            text="Save Dependent",
            command=self._save_dependent,
            button_type="primary"
        ).pack(side="right")

    def _load_dependent_data(self):
        """Load existing dependent data for editing"""
        self.first_name_entry.set(self.dependent_data.get('first_name', ''))
        self.last_name_entry.set(self.dependent_data.get('last_name', ''))
        self.ssn_entry.set(self.dependent_data.get('ssn', ''))
        self.birth_date_entry.set(self.dependent_data.get('birth_date', ''))
        self.relationship_var.set(self.dependent_data.get('relationship', ''))
        self.months_entry.set(str(self.dependent_data.get('months_lived_in_home', '')))

    def _save_dependent(self):
        """Save the dependent information"""
        # Validate required fields
        if not self._validate_form():
            return

        # Create dependent data
        dependent_data = {
            'first_name': self.first_name_entry.get().strip(),
            'last_name': self.last_name_entry.get().strip(),
            'ssn': self.ssn_entry.get().strip(),
            'birth_date': self.birth_date_entry.get().strip(),
            'relationship': self.relationship_var.get(),
            'months_lived_in_home': int(self.months_entry.get().strip())
        }

        # Call save callback
        if self.on_save:
            self.on_save(dependent_data, self.edit_index)

        # Close dialog
        self.destroy()

    def _validate_form(self) -> bool:
        """Validate the form data"""
        from gui.modern_ui_components import show_error_message

        # First name
        if not self.first_name_entry.get().strip():
            show_error_message("Validation Error", "First name is required.")
            return False

        # Last name
        if not self.last_name_entry.get().strip():
            show_error_message("Validation Error", "Last name is required.")
            return False

        # SSN
        ssn = self.ssn_entry.get().strip()
        if not ssn:
            show_error_message("Validation Error", "Social Security Number is required.")
            return False

        # Basic SSN format validation
        ssn_pattern = r'^\d{3}-?\d{2}-?\d{4}$'
        if not re.match(ssn_pattern, ssn.replace('-', '')):
            show_error_message("Validation Error", "Please enter a valid Social Security Number (XXX-XX-XXXX).")
            return False

        # Birth date
        birth_date = self.birth_date_entry.get().strip()
        if not birth_date:
            show_error_message("Validation Error", "Birth date is required.")
            return False

        # Validate date format
        try:
            datetime.strptime(birth_date, '%m/%d/%Y')
        except ValueError:
            show_error_message("Validation Error", "Please enter birth date in MM/DD/YYYY format.")
            return False

        # Relationship
        if not self.relationship_var.get():
            show_error_message("Validation Error", "Please select a relationship.")
            return False

        # Months
        try:
            months = int(self.months_entry.get().strip())
            if months < 0 or months > 12:
                raise ValueError()
        except ValueError:
            show_error_message("Validation Error", "Months lived in home must be a number between 0 and 12.")
            return False

        return True