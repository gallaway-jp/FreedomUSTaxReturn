"""
Modern Tax Forms Page - Tax form selection and management

A page where users can view, select, and manage tax forms they want to file.
Can be accessed independently or after the tax interview.
"""

import customtkinter as ctk
from typing import Optional, Callable, Dict, Any, List
import tkinter as tk

from config.app_config import AppConfig
from services.tax_interview_service import TaxInterviewService, FormRecommendation
from services.form_recommendation_service import FormRecommendationService
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import (
    ModernFrame, ModernLabel, ModernButton, ModernCheckBox,
    show_info_message, show_error_message
)


class ModernTaxFormsPage(ctk.CTkScrollableFrame):
    """
    Modern tax forms selection and management page.

    Features:
    - View all available tax forms
    - Select forms to include in tax return
    - Search and filter forms
    - View form descriptions and estimated completion time
    - Add/remove forms dynamically
    - Integration with interview recommendations
    """

    def __init__(
        self,
        parent,
        config: AppConfig,
        accessibility_service: Optional[AccessibilityService] = None,
        initial_recommendations: Optional[List[Dict[str, Any]]] = None,
        on_forms_selected: Optional[Callable] = None,
        **kwargs
    ):
        """
        Initialize the tax forms page.

        Args:
            parent: Parent widget
            config: Application configuration
            accessibility_service: Accessibility service
            initial_recommendations: Forms from interview to pre-select
            on_forms_selected: Callback when forms are selected
        """
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.config = config
        self.accessibility_service = accessibility_service
        self.on_forms_selected = on_forms_selected
        self.initial_recommendations = initial_recommendations or []

        # Services
        self.interview_service = TaxInterviewService(config)
        self.form_rec_service = FormRecommendationService(config)

        # Data
        self.all_forms: List[Dict[str, Any]] = []
        self.selected_forms: Dict[str, Dict[str, Any]] = {}
        self.form_checkboxes: Dict[str, ctk.CTkCheckBox] = {}

        # UI components
        self.search_entry: Optional[ctk.CTkEntry] = None
        self.forms_container: Optional[ctk.CTkFrame] = None
        self.selected_count_label: Optional[ModernLabel] = None

        # Load available forms
        self._load_forms()

        # Pre-select recommended forms
        for rec in self.initial_recommendations:
            form_name = rec.get('form')
            if form_name:
                self.selected_forms[form_name] = rec

        self._setup_ui()

    def _load_forms(self):
        """Load all available forms"""
        try:
            # Get all available forms from the service
            self.all_forms = self._get_all_available_forms()
        except Exception as e:
            show_error_message("Error", f"Failed to load forms: {str(e)}")
            self.all_forms = []

    def _get_all_available_forms(self) -> List[Dict[str, Any]]:
        """Get all available tax forms"""
        forms = [
            {
                'form': '1040',
                'name': 'U.S. Individual Income Tax Return',
                'category': 'Core',
                'description': 'Main income tax return form',
                'estimated_time': 45,
                'required': True,
                'priority': 10
            },
            {
                'form': 'Schedule A',
                'name': 'Itemized Deductions',
                'category': 'Deductions',
                'description': 'Itemized deductions instead of standard deduction',
                'estimated_time': 30,
                'required': False,
                'priority': 8
            },
            {
                'form': 'Schedule B',
                'name': 'Interest and Ordinary Dividends',
                'category': 'Income',
                'description': 'Report interest and dividend income',
                'estimated_time': 20,
                'required': False,
                'priority': 7
            },
            {
                'form': 'Schedule C',
                'name': 'Profit or Loss From Business',
                'category': 'Business',
                'description': 'Self-employment income',
                'estimated_time': 60,
                'required': False,
                'priority': 8
            },
            {
                'form': 'Schedule D',
                'name': 'Capital Gains and Losses',
                'category': 'Investments',
                'description': 'Sale of stocks, bonds, or other assets',
                'estimated_time': 40,
                'required': False,
                'priority': 7
            },
            {
                'form': 'Schedule E',
                'name': 'Supplemental Income or Loss',
                'category': 'Rental/Investment',
                'description': 'Rental income or loss',
                'estimated_time': 35,
                'required': False,
                'priority': 6
            },
            {
                'form': 'Schedule EIC',
                'name': 'Earned Income Tax Credit',
                'category': 'Credits',
                'description': 'Earned Income Tax Credit (EITC)',
                'estimated_time': 25,
                'required': False,
                'priority': 8
            },
            {
                'form': 'Form 2441',
                'name': 'Child and Dependent Care Expenses',
                'category': 'Credits',
                'description': 'Dependent care credit',
                'estimated_time': 20,
                'required': False,
                'priority': 6
            },
            {
                'form': 'Form 3468',
                'name': 'Investment Credit',
                'category': 'Credits',
                'description': 'Investment tax credit',
                'estimated_time': 30,
                'required': False,
                'priority': 5
            },
            {
                'form': 'Form 5695',
                'name': 'Residential Energy Credits',
                'category': 'Credits',
                'description': 'Energy-efficient home improvements',
                'estimated_time': 20,
                'required': False,
                'priority': 5
            },
            {
                'form': 'Schedule H',
                'name': 'Household Employment Taxes',
                'category': 'Employment',
                'description': 'Nanny tax and household employee taxes',
                'estimated_time': 25,
                'required': False,
                'priority': 5
            },
            {
                'form': 'Form 8949',
                'name': 'Sales of Securities',
                'category': 'Investments',
                'description': 'Detailed securities transactions',
                'estimated_time': 30,
                'required': False,
                'priority': 6
            },
            {
                'form': 'Form 1116',
                'name': 'Foreign Tax Credit',
                'category': 'Foreign',
                'description': 'Credit for foreign taxes paid',
                'estimated_time': 40,
                'required': False,
                'priority': 5
            },
            {
                'form': 'Form 3520',
                'name': 'Gift Tax Return',
                'category': 'Gifts',
                'description': 'Gifts to U.S. persons',
                'estimated_time': 35,
                'required': False,
                'priority': 4
            },
            {
                'form': 'Form 8801',
                'name': 'Crypto and Digital Assets',
                'category': 'Crypto',
                'description': 'Cryptocurrency transactions',
                'estimated_time': 45,
                'required': False,
                'priority': 5
            },
        ]
        return forms

    def _setup_ui(self):
        """Setup the forms page UI"""
        # Main content frame
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        title_label = ModernLabel(
            header_frame,
            text="Tax Forms Selection",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left")

        self.selected_count_label = ModernLabel(
            header_frame,
            text=f"Selected: {len(self.selected_forms)} forms",
            font=ctk.CTkFont(size=12),
            text_color="gray60"
        )
        self.selected_count_label.pack(side="right")

        # Instructions
        instructions_label = ModernLabel(
            content_frame,
            text="Select the tax forms you want to include in your return. Required forms are marked with *.",
            font=ctk.CTkFont(size=11),
            text_color="gray60",
            wraplength=600
        )
        instructions_label.pack(fill="x", pady=(0, 20))

        # Search frame
        search_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 15))

        search_label = ModernLabel(
            search_frame,
            text="Search Forms:"
        )
        search_label.pack(side="left", padx=(0, 10))

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search by form name or number...",
            height=35
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", self._filter_forms)

        # Action buttons
        buttons_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(0, 20))

        select_all_btn = ModernButton(
            buttons_frame,
            text="Select All",
            command=self._select_all,
            button_type="secondary",
            width=100,
            accessibility_service=self.accessibility_service
        )
        select_all_btn.pack(side="left", padx=(0, 10))

        clear_all_btn = ModernButton(
            buttons_frame,
            text="Clear All",
            command=self._clear_all,
            button_type="secondary",
            width=100,
            accessibility_service=self.accessibility_service
        )
        clear_all_btn.pack(side="left", padx=(0, 10))

        # Forms container
        self.forms_container = ctk.CTkFrame(content_frame, fg_color="transparent")
        self.forms_container.pack(fill="both", expand=True)

        # Display forms
        self._display_forms()

        # Summary and action buttons at bottom
        summary_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        summary_frame.pack(fill="x", pady=(20, 0))

        summary_label = ModernLabel(
            summary_frame,
            text=self._get_summary_text(),
            font=ctk.CTkFont(size=11),
            text_color="gray60",
            wraplength=600,
            justify="left"
        )
        summary_label.pack(fill="x", pady=(0, 15))

        action_frame = ctk.CTkFrame(summary_frame, fg_color="transparent")
        action_frame.pack(fill="x")

        continue_btn = ModernButton(
            action_frame,
            text="Continue",
            command=self._continue,
            button_type="primary",
            width=100,
            accessibility_service=self.accessibility_service
        )
        continue_btn.pack(side="right")

    def _display_forms(self):
        """Display all available forms"""
        # Clear existing
        for widget in self.forms_container.winfo_children():
            widget.destroy()

        self.form_checkboxes.clear()

        # Group forms by category
        categories = {}
        for form in self.all_forms:
            category = form.get('category', 'Other')
            if category not in categories:
                categories[category] = []
            categories[category].append(form)

        # Display by category
        for category in sorted(categories.keys()):
            category_frame = ctk.CTkFrame(self.forms_container, fg_color="transparent")
            category_frame.pack(fill="x", pady=(0, 15))

            # Category header
            category_label = ModernLabel(
                category_frame,
                text=category,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="skyblue"
            )
            category_label.pack(anchor="w", pady=(0, 10))

            # Forms in category
            for form in categories[category]:
                self._create_form_item(category_frame, form)

    def _create_form_item(self, parent, form: Dict[str, Any]):
        """Create a form item with checkbox"""
        item_frame = ctk.CTkFrame(parent, fg_color="transparent")
        item_frame.pack(fill="x", pady=5, padx=20)

        # Checkbox
        form_name = form.get('form', '')
        is_selected = form_name in self.selected_forms
        is_required = form.get('required', False)

        var = ctk.StringVar(value="on" if is_selected else "off")
        checkbox = ctk.CTkCheckBox(
            item_frame,
            text="",
            variable=var,
            onvalue="on",
            offvalue="off",
            command=lambda: self._toggle_form(form_name, var),
            state="disabled" if is_required else "normal"
        )
        checkbox.pack(side="left", padx=(0, 10))
        self.form_checkboxes[form_name] = checkbox

        # Form details
        details_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        details_frame.pack(side="left", fill="both", expand=True)

        # Form name with required indicator
        name_text = f"{form_name}"
        if is_required:
            name_text += " *"
        name_label = ModernLabel(
            details_frame,
            text=name_text,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        name_label.pack(anchor="w")

        # Description and time
        description = form.get('description', '')
        time = form.get('estimated_time', 0)
        info_text = f"{description} (~{time} min)"
        info_label = ModernLabel(
            details_frame,
            text=info_text,
            font=ctk.CTkFont(size=10),
            text_color="gray60",
            wraplength=400,
            justify="left"
        )
        info_label.pack(anchor="w", pady=(2, 0))

    def _filter_forms(self, event=None):
        """Filter forms based on search text"""
        search_text = self.search_entry.get().lower()

        # Filter forms
        filtered = [
            form for form in self.all_forms
            if search_text in form.get('form', '').lower() or
               search_text in form.get('name', '').lower() or
               search_text in form.get('description', '').lower()
        ]

        # Update display
        for widget in self.forms_container.winfo_children():
            widget.destroy()

        self.form_checkboxes.clear()

        if not filtered:
            no_results = ModernLabel(
                self.forms_container,
                text="No forms match your search.",
                font=ctk.CTkFont(size=12),
                text_color="gray60"
            )
            no_results.pack(pady=20)
            return

        # Group filtered forms by category
        categories = {}
        for form in filtered:
            category = form.get('category', 'Other')
            if category not in categories:
                categories[category] = []
            categories[category].append(form)

        # Display by category
        for category in sorted(categories.keys()):
            category_frame = ctk.CTkFrame(self.forms_container, fg_color="transparent")
            category_frame.pack(fill="x", pady=(0, 15))

            category_label = ModernLabel(
                category_frame,
                text=category,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="skyblue"
            )
            category_label.pack(anchor="w", pady=(0, 10))

            for form in categories[category]:
                self._create_form_item(category_frame, form)

    def _toggle_form(self, form_name: str, var: ctk.StringVar):
        """Toggle form selection"""
        if var.get() == "on":
            # Find the form and add to selected
            for form in self.all_forms:
                if form.get('form') == form_name:
                    self.selected_forms[form_name] = form
                    break
        else:
            # Remove from selected (if not required)
            if form_name in self.selected_forms:
                form_data = self.selected_forms[form_name]
                if not form_data.get('required', False):
                    del self.selected_forms[form_name]
                    # Reset checkbox
                    var.set("off")
                else:
                    # Force it back on
                    var.set("on")

        # Update count
        self._update_count()

    def _update_count(self):
        """Update the selected forms count"""
        if self.selected_count_label:
            self.selected_count_label.configure(
                text=f"Selected: {len(self.selected_forms)} forms"
            )

    def _select_all(self):
        """Select all forms"""
        for form in self.all_forms:
            form_name = form.get('form', '')
            self.selected_forms[form_name] = form
            if form_name in self.form_checkboxes:
                self.form_checkboxes[form_name].select()

        self._update_count()

    def _clear_all(self):
        """Clear all non-required forms"""
        forms_to_remove = [
            name for name, form in self.selected_forms.items()
            if not form.get('required', False)
        ]

        for form_name in forms_to_remove:
            del self.selected_forms[form_name]
            if form_name in self.form_checkboxes:
                self.form_checkboxes[form_name].deselect()

        # Ensure required forms stay selected
        for form in self.all_forms:
            if form.get('required', False):
                form_name = form.get('form', '')
                self.selected_forms[form_name] = form
                if form_name in self.form_checkboxes:
                    self.form_checkboxes[form_name].select()

        self._update_count()

    def _get_summary_text(self) -> str:
        """Get summary text for selected forms"""
        if not self.selected_forms:
            return "Please select at least one form to continue."

        total_time = sum(f.get('estimated_time', 0) for f in self.selected_forms.values())
        return f"You have selected {len(self.selected_forms)} forms with an estimated completion time of {total_time} minutes."

    def _continue(self):
        """Continue with selected forms"""
        # Validate at least Form 1040 is selected
        if '1040' not in self.selected_forms:
            show_error_message("Required Form", "Form 1040 is required for all tax returns.")
            return

        if self.on_forms_selected:
            self.on_forms_selected(list(self.selected_forms.values()))
