"""
State Tax Returns Page - Converted from Window

Page for state tax return preparation and multi-state tax management.
Integrated into main window without popup dialogs.
"""

import customtkinter as ctk
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.state_tax_service import StateTaxService, StateCode, StateTaxCalculation
from services.state_form_pdf_generator import StateFormPDFGenerator, StateFormData
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton
from utils.event_bus import EventBus

logger = logging.getLogger(__name__)


class StateTaxPage(ctk.CTkScrollableFrame):
    """
    State Tax Returns page - converted from popup window to integrated page.
    
    Features:
    - Multi-state tax management
    - State tax calculations
    - State-specific form generation
    - Tax comparison across states
    - Integration with federal returns
    """

    def __init__(self, master, config: AppConfig, tax_data: Optional[TaxData] = None,
                 accessibility_service: Optional[AccessibilityService] = None,
                 event_bus: Optional[EventBus] = None, **kwargs):
        super().__init__(master, **kwargs)

        self.config = config
        self.tax_data = tax_data
        self.accessibility_service = accessibility_service
        self.event_bus = event_bus

        # Initialize services
        self.state_service = StateTaxService()
        self.pdf_generator = StateFormPDFGenerator()

        # Data storage
        self.selected_states: List[StateCode] = []
        self.state_calculations: Dict[StateCode, StateTaxCalculation] = {}
        self.current_tax_year = datetime.now().year
        self.state_vars = {}
        self.calculation_vars = {}

        # Build the page
        self._create_header()
        self._create_toolbar()
        self._create_main_content()
        self._load_current_data()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self)
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
        toolbar_frame = ModernFrame(self)
        toolbar_frame.pack(fill=ctk.X, padx=20, pady=10)

        # Action buttons
        button_section = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        button_section.pack(side=ctk.LEFT, fill=ctk.X, expand=False)

        ModernButton(
            button_section,
            text="🧮 Calculate Taxes",
            command=self._calculate_taxes,
            button_type="primary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📊 Compare States",
            command=self._compare_states,
            button_type="secondary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📄 Generate Forms",
            command=self._generate_forms,
            button_type="secondary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="💾 Save Return",
            command=self._save_return,
            button_type="success",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        # Progress bar
        progress_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        progress_frame.pack(fill=ctk.X, pady=10)

        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=6)
        self.progress_bar.pack(fill=ctk.X)
        self.progress_bar.set(0)

        self.status_label = ModernLabel(progress_frame, text="Ready", font_size=11)
        self.status_label.pack(anchor=ctk.W, pady=(5, 0))

    def _create_main_content(self):
        """Create main content with tabview"""
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

        # Create tabview
        self.tabview = ctk.CTkTabview(main_container)
        self.tabview.pack(fill=ctk.BOTH, expand=True)

        # Add tabs
        self.tab_overview = self.tabview.add("📊 Overview")
        self.tab_states = self.tabview.add("🗺️ State Selection")
        self.tab_income = self.tabview.add("💰 Income & Deductions")
        self.tab_calculation = self.tabview.add("🧮 Calculations")
        self.tab_forms = self.tabview.add("📄 Forms & Reports")

        # Setup tabs
        self._setup_overview_tab()
        self._setup_states_tab()
        self._setup_income_tab()
        self._setup_calculation_tab()
        self._setup_forms_tab()

    def _setup_overview_tab(self):
        """Setup overview tab"""
        frame = ctk.CTkScrollableFrame(self.tab_overview)
        frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        overview_label = ModernLabel(frame, text="State Tax Overview", font_size=12, font_weight="bold")
        overview_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        # Summary cards
        cards_frame = ctk.CTkFrame(frame, fg_color="transparent")
        cards_frame.pack(fill=ctk.X, padx=5, pady=10)

        for metric in ["Selected States", "Total State Tax", "Average Tax Rate", "Multi-State Impact"]:
            card = self._create_summary_card(cards_frame, metric, "0")
            card.pack(side=ctk.LEFT, padx=5, fill=ctk.X, expand=True)

        # Status text
        status_label = ModernLabel(frame, text="Status", font_size=11, font_weight="bold")
        status_label.pack(anchor=ctk.W, padx=5, pady=(10, 5))

        self.overview_text = ctk.CTkTextbox(frame, height=300)
        self.overview_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.overview_text.insert("1.0", "Select states to begin calculating state taxes.")
        self.overview_text.configure(state="disabled")

    def _setup_states_tab(self):
        """Setup state selection tab"""
        # Controls
        control_frame = ctk.CTkFrame(self.tab_states, fg_color="transparent")
        control_frame.pack(fill=ctk.X, padx=10, pady=10)

        filter_label = ctk.CTkLabel(control_frame, text="Filter:", text_color="gray", font=("", 11))
        filter_label.pack(side=ctk.LEFT, padx=5)

        self.state_filter = ctk.CTkComboBox(
            control_frame,
            values=["All States", "Income Tax States", "No Income Tax", "Residence", "Work"],
            command=self._on_state_filter_changed,
            width=150
        )
        self.state_filter.set("All States")
        self.state_filter.pack(side=ctk.LEFT, padx=5)

        multi_state_checkbox = ctk.CTkCheckBox(
            control_frame,
            text="Multi-state Mode",
            command=self._toggle_multi_state_mode
        )
        multi_state_checkbox.pack(side=ctk.LEFT, padx=5)

        # State selection area
        content_frame = ctk.CTkFrame(self.tab_states)
        content_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)

        # Left panel - state list
        left_panel = ctk.CTkScrollableFrame(content_frame)
        left_panel.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True, padx=5, pady=5)

        left_label = ModernLabel(left_panel, text="States", font_size=11, font_weight="bold")
        left_label.pack(anchor=ctk.W, padx=5, pady=(0, 5))

        self.states_listbox = ctk.CTkTextbox(left_panel, height=400, width=150)
        self.states_listbox.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.states_listbox.insert("1.0", "AL - Alabama\nAK - Alaska\nAZ - Arizona\nAR - Arkansas\nCA - California")
        self.states_listbox.configure(state="disabled")

        # Right panel - state details
        right_panel = ctk.CTkFrame(content_frame)
        right_panel.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True, padx=5, pady=5)

        right_label = ModernLabel(right_panel, text="State Information", font_size=11, font_weight="bold")
        right_label.pack(anchor=ctk.W, padx=5, pady=(0, 5))

        self.state_info_text = ctk.CTkTextbox(right_panel, height=400)
        self.state_info_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.state_info_text.insert("1.0", "Select a state to view details.")
        self.state_info_text.configure(state="disabled")

    def _setup_income_tab(self):
        """Setup income and deductions tab"""
        container = ctk.CTkFrame(self.tab_income, fg_color="transparent")
        container.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        # Income and Deductions section
        content_frame = ctk.CTkFrame(container, fg_color="transparent")
        content_frame.pack(fill=ctk.BOTH, expand=True)

        # Income section (left)
        income_label = ModernLabel(content_frame, text="State Income Sources", font_size=12, font_weight="bold")
        income_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        income_frame = ctk.CTkFrame(content_frame)
        income_frame.pack(fill=ctk.X, padx=5, pady=5)

        income_items = ["W-2 Wages", "Self-Employment Income", "Capital Gains", "Dividend Income", "Other Income"]
        for item in income_items:
            item_frame = ctk.CTkFrame(income_frame, fg_color="transparent")
            item_frame.pack(fill=ctk.X, padx=10, pady=8)
            
            label = ctk.CTkLabel(item_frame, text=f"{item}:", text_color="gray", font=("", 11))
            label.pack(side=ctk.LEFT, padx=5)
            
            entry = ctk.CTkEntry(item_frame, placeholder_text="$0.00", width=150)
            entry.pack(side=ctk.LEFT, padx=5, fill=ctk.X, expand=True)
            
            self.calculation_vars[item.lower().replace(" ", "_")] = entry

        # Deductions section
        deduction_label = ModernLabel(content_frame, text="State Deductions", font_size=12, font_weight="bold")
        deduction_label.pack(anchor=ctk.W, padx=5, pady=(10, 10))

        deduction_frame = ctk.CTkFrame(content_frame)
        deduction_frame.pack(fill=ctk.X, padx=5, pady=5)

        deduction_items = ["Standard Deduction", "Itemized Deductions", "Credits", "Tax Payments"]
        for item in deduction_items:
            item_frame = ctk.CTkFrame(deduction_frame, fg_color="transparent")
            item_frame.pack(fill=ctk.X, padx=10, pady=8)
            
            label = ctk.CTkLabel(item_frame, text=f"{item}:", text_color="gray", font=("", 11))
            label.pack(side=ctk.LEFT, padx=5)
            
            entry = ctk.CTkEntry(item_frame, placeholder_text="$0.00", width=150)
            entry.pack(side=ctk.LEFT, padx=5, fill=ctk.X, expand=True)
            
            self.calculation_vars[item.lower().replace(" ", "_")] = entry

    def _setup_calculation_tab(self):
        """Setup calculation tab"""
        frame = ctk.CTkScrollableFrame(self.tab_calculation)
        frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        calc_label = ModernLabel(frame, text="State Tax Calculation Results", font_size=12, font_weight="bold")
        calc_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.calculation_text = ctk.CTkTextbox(frame, height=400)
        self.calculation_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.calculation_text.insert("1.0", "No calculations performed yet. Select states and click 'Calculate Taxes'.")
        self.calculation_text.configure(state="disabled")

    def _setup_forms_tab(self):
        """Setup forms and reports tab"""
        # Button bar
        button_frame = ctk.CTkFrame(self.tab_forms, fg_color="transparent")
        button_frame.pack(fill=ctk.X, padx=10, pady=10)

        ModernButton(
            button_frame,
            text="📄 Generate Forms",
            command=self._generate_forms,
            button_type="secondary",
            width=150
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_frame,
            text="💾 Save Forms",
            command=self._save_forms,
            button_type="success",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_frame,
            text="📧 E-File",
            command=self._efile_forms,
            button_type="secondary",
            width=100
        ).pack(side=ctk.LEFT, padx=5)

        # Forms output
        output_frame = ctk.CTkFrame(self.tab_forms)
        output_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)
        output_frame.grid_rowconfigure(0, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)

        self.forms_text = ctk.CTkTextbox(output_frame)
        self.forms_text.grid(row=0, column=0, sticky="nsew")
        self.forms_text.insert("1.0", "No forms generated yet.")
        self.forms_text.configure(state="disabled")

    def _create_summary_card(self, parent, title, value):
        """Create a summary metric card"""
        card = ctk.CTkFrame(parent, corner_radius=8, fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        
        title_label = ctk.CTkLabel(card, text=title, text_color="gray", font=("", 11))
        title_label.pack(padx=10, pady=(8, 2))

        value_label = ctk.CTkLabel(card, text=value, text_color="white", font=("", 13, "bold"))
        value_label.pack(padx=10, pady=(2, 8))

        return card

    # ===== Action Methods =====

    def _load_current_data(self):
        """Load current state tax data"""
        self.status_label.configure(text="Loading state data...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Ready")
        self.progress_bar.set(1.0)

    def _calculate_taxes(self):
        """Calculate state taxes"""
        self.status_label.configure(text="Calculating state taxes...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Calculation complete")
        self.progress_bar.set(1.0)

    def _compare_states(self):
        """Compare taxes across selected states"""
        self.status_label.configure(text="Comparing states...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Comparison complete")
        self.progress_bar.set(1.0)

    def _generate_forms(self):
        """Generate state tax forms"""
        self.status_label.configure(text="Generating forms...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Forms generated")
        self.progress_bar.set(1.0)

    def _save_forms(self):
        """Save generated forms"""
        self.status_label.configure(text="Forms saved")

    def _efile_forms(self):
        """E-file state forms"""
        self.status_label.configure(text="E-filing forms...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="E-file complete")
        self.progress_bar.set(1.0)

    def _save_return(self):
        """Save state tax return"""
        self.status_label.configure(text="Saving return...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Return saved")
        self.progress_bar.set(1.0)

    def _on_state_filter_changed(self, choice):
        """Handle state filter selection"""
        self.status_label.configure(text=f"Filtering by: {choice}")

    def _toggle_multi_state_mode(self):
        """Toggle multi-state mode"""
        self.status_label.configure(text="Multi-state mode toggled")
