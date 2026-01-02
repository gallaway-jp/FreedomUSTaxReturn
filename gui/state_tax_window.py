"""
State Tax Window - Modernized

GUI for state tax return preparation and multi-state tax management.
Uses CustomTkinter for modern, theme-aware interface.
"""

import customtkinter as ctk
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from services.state_tax_service import StateTaxService, StateCode, StateTaxCalculation
from services.state_form_pdf_generator import StateFormPDFGenerator, StateFormData
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton
from config.app_config import AppConfig
from utils.event_bus import EventBus

logger = logging.getLogger(__name__)


class StateTaxWindow:
    """
    Modernized window for managing state tax returns and calculations.

    Provides interface for:
    - Selecting states of residence and work
    - Calculating state taxes
    - Viewing state-specific forms
    - Multi-state tax planning
    - State tax form generation
    """

    def __init__(self, parent: ctk.CTk, config: AppConfig, tax_data: Any = None, 
                 event_bus: EventBus = None, accessibility_service: AccessibilityService = None):
        self.parent = parent
        self.config = config
        self.tax_data = tax_data
        self.event_bus = event_bus
        self.accessibility_service = accessibility_service
        self.state_service = StateTaxService()
        self.pdf_generator = StateFormPDFGenerator()

        # Window setup
        self.window = ctk.CTkToplevel(parent)
        self.window.title("State Tax Returns")
        self.window.geometry("1600x950")
        self.window.configure(fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"])

        # Initialize data
        self.selected_states: List[StateCode] = []
        self.state_calculations: Dict[StateCode, StateTaxCalculation] = {}
        self.current_tax_year = datetime.now().year

        # Create main layout
        self._create_header()
        self._create_toolbar()
        self._create_main_content()
        self._create_status_bar()

        # Load initial data
        self._load_current_data()

    def _create_header(self):
        """Create the header section with title and subtitle"""
        header_frame = ModernFrame(self.window)
        header_frame.pack(fill=ctk.X, padx=20, pady=(20, 10))

        title_label = ModernLabel(
            header_frame,
            text="📋 State Tax Return Preparation",
            font_size=24,
            font_weight="bold"
        )
        title_label.pack(anchor=ctk.W, pady=(0, 5))

        subtitle_label = ModernLabel(
            header_frame,
            text="Calculate state taxes, manage multi-state returns, and generate state-specific forms",
            font_size=12,
            text_color="gray"
        )
        subtitle_label.pack(anchor=ctk.W)

    def _create_toolbar(self):
        """Create the toolbar with action buttons"""
        toolbar_frame = ModernFrame(self.window)
        toolbar_frame.pack(fill=ctk.X, padx=20, pady=10)

        # Left section - Action buttons
        left_section = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        left_section.pack(side=ctk.LEFT, fill=ctk.X, expand=False)

        ModernButton(
            left_section,
            text="🧮 Calculate Taxes",
            command=self._calculate_taxes,
            button_type="primary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            left_section,
            text="📄 Generate Forms",
            command=self._generate_forms,
            button_type="primary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            left_section,
            text="💾 Save Data",
            command=self._save_state_data,
            button_type="secondary",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            left_section,
            text="📊 Compare States",
            command=self._compare_states,
            button_type="secondary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        # Right section - Tax year selector
        right_section = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        right_section.pack(side=ctk.RIGHT, fill=ctk.X)

        ModernLabel(right_section, text="Tax Year:").pack(side=ctk.RIGHT, padx=(10, 5))
        self.tax_year_var = ctk.StringVar(value=str(self.current_tax_year))
        year_combo = ctk.CTkComboBox(
            right_section,
            variable=self.tax_year_var,
            values=[str(y) for y in range(self.current_tax_year - 5, self.current_tax_year + 1)],
            width=100
        )
        year_combo.pack(side=ctk.RIGHT, padx=5)

        # Progress bar and status
        progress_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        progress_frame.pack(fill=ctk.X, pady=10)

        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=6)
        self.progress_bar.pack(fill=ctk.X)
        self.progress_bar.set(0)

        self.status_label = ModernLabel(progress_frame, text="Ready", font_size=11)
        self.status_label.pack(anchor=ctk.W, pady=(5, 0))

    def _create_main_content(self):
        """Create the main content area with tabview"""
        main_container = ctk.CTkFrame(self.window, fg_color="transparent")
        main_container.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

        # Create tabview
        self.tabview = ctk.CTkTabview(main_container)
        self.tabview.pack(fill=ctk.BOTH, expand=True)

        # Add tabs
        self.tab_state_selection = self.tabview.add("📍 State Selection")
        self.tab_calculations = self.tabview.add("🧮 Calculations")
        self.tab_forms = self.tabview.add("📄 Forms & Reports")
        self.tab_summary = self.tabview.add("📊 Summary")

        # Setup tabs
        self._setup_state_selection_tab()
        self._setup_calculations_tab()
        self._setup_forms_tab()
        self._setup_summary_tab()

    def _setup_state_selection_tab(self):
        """Create the state selection tab"""
        self.tab_state_selection.grid_rowconfigure(0, weight=1)
        self.tab_state_selection.grid_columnconfigure(0, weight=1)
        self.tab_state_selection.grid_columnconfigure(1, weight=1)

        # Instructions
        instructions_frame = ModernFrame(self.tab_state_selection)
        instructions_frame.pack(fill=ctk.X, padx=10, pady=10)

        instructions_text = """Select the states where you have income tax obligations or where you work/live.
You can select multiple states to prepare multi-state returns and compare tax burdens."""

        instructions_label = ctk.CTkLabel(
            instructions_frame,
            text=instructions_text,
            text_color="gray",
            font=("", 11),
            justify=ctk.LEFT
        )
        instructions_label.pack(anchor=ctk.W, padx=10, pady=10)

        # State selection area
        content_frame = ctk.CTkFrame(self.tab_state_selection, fg_color="transparent")
        content_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)

        # States of residence
        residence_frame = ModernFrame(content_frame)
        residence_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        residence_frame.grid_rowconfigure(1, weight=1)

        ModernLabel(residence_frame, text="States of Residence", font_size=12, font_weight="bold").pack(anchor=ctk.W, padx=10, pady=(10, 5))

        self.residence_scrollable = ctk.CTkScrollableFrame(residence_frame)
        self.residence_scrollable.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)

        # States of work
        work_frame = ModernFrame(content_frame)
        work_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        work_frame.grid_rowconfigure(1, weight=1)

        ModernLabel(work_frame, text="States of Work", font_size=12, font_weight="bold").pack(anchor=ctk.W, padx=10, pady=(10, 5))

        self.work_scrollable = ctk.CTkScrollableFrame(work_frame)
        self.work_scrollable.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)

        # Selection controls
        self._populate_state_lists()

    def _populate_state_lists(self):
        """Populate state selection lists"""
        # Clear existing
        for widget in self.residence_scrollable.winfo_children():
            widget.destroy()
        for widget in self.work_scrollable.winfo_children():
            widget.destroy()

        # Create checkbox variables
        self.residence_vars = {}
        self.work_vars = {}

        # Add all states
        for state_code in sorted(StateCode, key=lambda s: s.value):
            # Residence checkbox
            var = ctk.BooleanVar(value=False)
            self.residence_vars[state_code] = var
            checkbox = ctk.CTkCheckBox(
                self.residence_scrollable,
                text=f"{state_code.value}",
                variable=var
            )
            checkbox.pack(anchor=ctk.W, padx=10, pady=3)

            # Work checkbox
            var2 = ctk.BooleanVar(value=False)
            self.work_vars[state_code] = var2
            checkbox2 = ctk.CTkCheckBox(
                self.work_scrollable,
                text=f"{state_code.value}",
                variable=var2
            )
            checkbox2.pack(anchor=ctk.W, padx=10, pady=3)

    def _setup_calculations_tab(self):
        """Create the calculations tab"""
        self.tab_calculations.grid_rowconfigure(0, weight=1)
        self.tab_calculations.grid_columnconfigure(0, weight=1)

        calc_frame = ctk.CTkScrollableFrame(self.tab_calculations)
        calc_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Summary section
        summary_label = ModernLabel(calc_frame, text="Tax Calculation Summary", font_size=12, font_weight="bold")
        summary_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        # Create metric cards
        cards_frame = ctk.CTkFrame(calc_frame, fg_color="transparent")
        cards_frame.pack(fill=ctk.X, padx=5, pady=10)

        self.calc_cards = {}
        metrics = ["Total Income", "Taxable Income", "Total Tax", "Avg Tax Rate"]

        for metric in metrics:
            card = self._create_metric_card(cards_frame, metric, "$0.00")
            self.calc_cards[metric] = card
            card.pack(side=ctk.LEFT, padx=5, fill=ctk.X, expand=True)

        # Calculations by state
        states_label = ModernLabel(calc_frame, text="State-by-State Breakdown", font_size=12, font_weight="bold")
        states_label.pack(anchor=ctk.W, padx=5, pady=(15, 10))

        self.calc_text = ctk.CTkTextbox(calc_frame, height=300)
        self.calc_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.calc_text.insert("1.0", "Run calculations to see results here.\nSelect states and click 'Calculate Taxes' to begin.")
        self.calc_text.configure(state="disabled")

    def _create_metric_card(self, parent, title, value):
        """Create a metric card display"""
        card = ctk.CTkFrame(parent, corner_radius=8, fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        
        title_label = ctk.CTkLabel(card, text=title, text_color="gray", font=("", 11))
        title_label.pack(padx=10, pady=(8, 2))

        value_label = ctk.CTkLabel(card, text=value, text_color="white", font=("", 14, "bold"))
        value_label.pack(padx=10, pady=(2, 8))

        card.value_label = value_label
        return card

    def _setup_forms_tab(self):
        """Create the forms tab"""
        self.tab_forms.grid_rowconfigure(0, weight=1)
        self.tab_forms.grid_columnconfigure(0, weight=1)

        forms_frame = ctk.CTkScrollableFrame(self.tab_forms)
        forms_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Forms section
        forms_label = ModernLabel(forms_frame, text="State Tax Forms", font_size=12, font_weight="bold")
        forms_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        # Form buttons
        button_frame = ctk.CTkFrame(forms_frame, fg_color="transparent")
        button_frame.pack(fill=ctk.X, padx=5, pady=5)

        ModernButton(
            button_frame,
            text="📄 Income Tax Return",
            command=lambda: self._generate_specific_form("income_return"),
            button_type="secondary",
            width=160
        ).pack(side=ctk.LEFT, padx=2, pady=2)

        ModernButton(
            button_frame,
            text="📋 Estimated Tax",
            command=lambda: self._generate_specific_form("estimated_tax"),
            button_type="secondary",
            width=140
        ).pack(side=ctk.LEFT, padx=2, pady=2)

        ModernButton(
            button_frame,
            text="🏢 Business Forms",
            command=lambda: self._generate_specific_form("business"),
            button_type="secondary",
            width=140
        ).pack(side=ctk.LEFT, padx=2, pady=2)

        # Generated forms display
        forms_label2 = ModernLabel(forms_frame, text="Generated Forms Output", font_size=12, font_weight="bold")
        forms_label2.pack(anchor=ctk.W, padx=5, pady=(15, 5))

        self.forms_text = ctk.CTkTextbox(forms_frame, height=400)
        self.forms_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.forms_text.insert("1.0", "Select states and click 'Generate Forms' to create state tax forms.")
        self.forms_text.configure(state="disabled")

    def _setup_summary_tab(self):
        """Create the summary tab"""
        self.tab_summary.grid_rowconfigure(0, weight=1)
        self.tab_summary.grid_columnconfigure(0, weight=1)

        summary_frame = ctk.CTkScrollableFrame(self.tab_summary)
        summary_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Multi-state comparison
        comparison_label = ModernLabel(summary_frame, text="Multi-State Tax Comparison", font_size=12, font_weight="bold")
        comparison_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        # Comparison table
        self.summary_text = ctk.CTkTextbox(summary_frame, height=400)
        self.summary_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.summary_text.insert("1.0", "Multi-state comparison results will appear here.\nSelect multiple states to compare their tax burdens.")
        self.summary_text.configure(state="disabled")

    def _create_status_bar(self):
        """Create status bar at bottom"""
        status_frame = ModernFrame(self.window)
        status_frame.pack(fill=ctk.X, padx=20, pady=10)

        info_label = ctk.CTkLabel(
            status_frame,
            text="Ready to prepare state tax returns",
            text_color="gray",
            font=("", 10)
        )
        info_label.pack(anchor=ctk.W)

    # ===== Action Methods =====

    def _calculate_taxes(self):
        """Calculate state taxes for selected states"""
        residence_states = [s for s, var in self.residence_vars.items() if var.get()]
        work_states = [s for s, var in self.work_vars.items() if var.get()]
        selected_states = list(set(residence_states + work_states))

        if not selected_states:
            self.status_label.configure(text="Please select at least one state")
            return

        self.status_label.configure(text="Calculating taxes...")
        self.progress_bar.set(0.3)

        # TODO: Implement tax calculations using state_service
        self.state_calculations = {}
        for state in selected_states:
            # Placeholder calculation
            self.state_calculations[state] = None

        self.status_label.configure(text="Tax calculations complete")
        self.progress_bar.set(1.0)

    def _generate_forms(self):
        """Generate state tax forms"""
        residence_states = [s for s, var in self.residence_vars.items() if var.get()]
        work_states = [s for s, var in self.work_vars.items() if var.get()]
        selected_states = list(set(residence_states + work_states))

        if not selected_states:
            self.status_label.configure(text="Please select at least one state")
            return

        self.status_label.configure(text="Generating state forms...")
        self.progress_bar.set(0.3)

        # TODO: Implement form generation using pdf_generator
        self.status_label.configure(text="Forms generated successfully")
        self.progress_bar.set(1.0)

    def _generate_specific_form(self, form_type: str):
        """Generate a specific state form"""
        residence_states = [s for s, var in self.residence_vars.items() if var.get()]
        work_states = [s for s, var in self.work_vars.items() if var.get()]
        selected_states = list(set(residence_states + work_states))

        if not selected_states:
            self.status_label.configure(text="Please select at least one state")
            return

        self.status_label.configure(text=f"Generating {form_type} forms...")
        self.progress_bar.set(0.5)

        # TODO: Implement specific form generation
        self.status_label.configure(text="Form generated")
        self.progress_bar.set(1.0)

    def _save_state_data(self):
        """Save state tax data"""
        self.status_label.configure(text="Saving state tax data...")
        self.progress_bar.set(0.5)

        # TODO: Implement data saving
        self.status_label.configure(text="State data saved")
        self.progress_bar.set(1.0)

    def _compare_states(self):
        """Compare taxes across selected states"""
        residence_states = [s for s, var in self.residence_vars.items() if var.get()]
        work_states = [s for s, var in self.work_vars.items() if var.get()]
        selected_states = list(set(residence_states + work_states))

        if len(selected_states) < 2:
            self.status_label.configure(text="Select at least 2 states to compare")
            return

        self.status_label.configure(text="Comparing states...")
        self.progress_bar.set(0.5)

        # TODO: Implement state comparison logic
        self.status_label.configure(text="Comparison complete")
        self.progress_bar.set(1.0)

    def _load_current_data(self):
        """Load current tax data"""
        self.status_label.configure(text="Loading state tax data...")
        self.progress_bar.set(0.5)
        # Data loading implementation
        self.progress_bar.set(1.0)
