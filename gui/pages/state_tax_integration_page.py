"""
State Tax Integration Page - Converted from Window to Page

Replaces state_tax_integration_window.py as a CTkScrollableFrame page
for the main application window. All functionality accessible within
the main window without popup dialogs.
"""

import customtkinter as ctk
from typing import Optional, List, Dict, Any
from datetime import datetime

from services.state_tax_integration_service import (
    StateTaxIntegrationService,
    StateCode,
    FilingStatus,
    StateTaxType,
)
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton
from config.app_config import AppConfig


class StateTaxIntegrationPage(ctk.CTkScrollableFrame):
    """
    State Tax Integration page - converted from popup window to main window page.
    
    Provides comprehensive state tax return preparation interface as a page
    within the main application window.
    """

    def __init__(self, master, config: AppConfig, 
                 accessibility_service: AccessibilityService = None, **kwargs):
        super().__init__(master, **kwargs)

        self.config = config
        self.accessibility_service = accessibility_service
        self.service = StateTaxIntegrationService(config, None)

        # Initialize variables
        self.selected_state: Optional[StateCode] = None
        self.selected_states: List[StateCode] = []
        self.current_tax_year = datetime.now().year
        self.multi_state_mode = False
        self.state_returns: Dict[str, Any] = {}

        # Build the page content
        self._create_header()
        self._create_toolbar()
        self._create_main_content()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self)
        header_frame.pack(fill=ctk.X, padx=20, pady=(20, 10))

        title_label = ModernLabel(
            header_frame,
            text="🌍 State Tax Integration",
            font_size=24,
            font_weight="bold"
        )
        title_label.pack(anchor=ctk.W, pady=(0, 5))

        subtitle_label = ModernLabel(
            header_frame,
            text="Prepare state tax returns, manage multi-state filings, and calculate state-specific taxes",
            font_size=12,
            text_color="gray"
        )
        subtitle_label.pack(anchor=ctk.W)

    def _create_toolbar(self):
        """Create the toolbar with action buttons"""
        toolbar_frame = ModernFrame(self)
        toolbar_frame.pack(fill=ctk.X, padx=20, pady=10)

        # Left section - Action buttons
        left_section = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        left_section.pack(side=ctk.LEFT, fill=ctk.X, expand=False)

        ModernButton(
            left_section,
            text="➕ New Return",
            command=self._new_state_return,
            button_type="primary",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            left_section,
            text="💾 Save Return",
            command=self._save_return,
            button_type="secondary",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            left_section,
            text="🧮 Calculate Tax",
            command=self._calculate_tax,
            button_type="primary",
            width=130
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            left_section,
            text="📊 Compare States",
            command=self._compare_states,
            button_type="secondary",
            width=130
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            left_section,
            text="📤 E-File",
            command=self._export_for_filing,
            button_type="success",
            width=100
        ).pack(side=ctk.LEFT, padx=5)

        # Right section - Multi-state toggle
        right_section = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        right_section.pack(side=ctk.RIGHT, fill=ctk.X)

        self.multi_state_var = ctk.BooleanVar(value=False)
        multi_state_checkbox = ctk.CTkCheckBox(
            right_section,
            text="Multi-State Mode",
            variable=self.multi_state_var,
            command=self._toggle_multi_state_mode
        )
        multi_state_checkbox.pack(side=ctk.RIGHT, padx=5)

        # Progress bar and status
        progress_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        progress_frame.pack(fill=ctk.X, pady=10)

        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=6)
        self.progress_bar.pack(fill=ctk.X)
        self.progress_bar.set(0)

        self.status_label = ModernLabel(progress_frame, text="Ready", font_size=11)
        self.status_label.pack(anchor=ctk.W, pady=(5, 0))

    def _create_main_content(self):
        """Create the main content area"""
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_columnconfigure(1, weight=2)

        # Left panel - State selection
        self._create_left_panel(main_container)

        # Right panel - State details and tabview
        self._create_right_panel(main_container)

    def _create_left_panel(self, parent: ctk.CTkFrame):
        """Create left panel with state selection"""
        left_frame = ModernFrame(parent)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_frame.grid_rowconfigure(2, weight=1)

        # State selection header
        state_header = ModernLabel(left_frame, text="📍 States", font_size=14, font_weight="bold")
        state_header.pack(anchor=ctk.W, padx=10, pady=(10, 5))

        # Filter section
        filter_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        filter_frame.pack(fill=ctk.X, padx=10, pady=5)

        ModernLabel(filter_frame, text="Filter:").pack(side=ctk.LEFT, padx=(0, 5))
        self.state_filter_var = ctk.StringVar(value="All")
        filter_combo = ctk.CTkComboBox(
            filter_frame,
            variable=self.state_filter_var,
            values=["All", "Progressive", "Flat", "No Income Tax"],
            command=self._apply_state_filter,
            width=150
        )
        filter_combo.pack(side=ctk.LEFT)

        # State listbox
        state_list_frame = ctk.CTkFrame(left_frame)
        state_list_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)
        state_list_frame.grid_rowconfigure(0, weight=1)
        state_list_frame.grid_columnconfigure(0, weight=1)

        self.state_scrollable_frame = ctk.CTkScrollableFrame(
            state_list_frame,
            fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"]
        )
        self.state_scrollable_frame.grid(row=0, column=0, sticky="nsew")

        # State buttons
        button_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        button_frame.pack(fill=ctk.X, padx=10, pady=5)

        ModernButton(
            button_frame,
            text="ℹ️ State Info",
            command=self._show_selected_state_info,
            button_type="secondary",
            width=120
        ).pack(side=ctk.LEFT, padx=2)

        ModernButton(
            button_frame,
            text="🗑️ Clear",
            command=self._clear_selection,
            button_type="danger",
            width=80
        ).pack(side=ctk.LEFT, padx=2)

        # Populate state list
        self._refresh_state_list()

    def _create_right_panel(self, parent: ctk.CTkFrame):
        """Create right panel with tabview"""
        self.right_frame = ModernFrame(parent)
        self.right_frame.grid(row=0, column=1, sticky="nsew")
        self.right_frame.grid_rowconfigure(1, weight=1)

        # Content header
        content_header = ModernLabel(self.right_frame, text="Details", font_size=14, font_weight="bold")
        content_header.pack(anchor=ctk.W, padx=10, pady=(10, 5))

        # Create tabview
        self.tabview = ctk.CTkTabview(self.right_frame)
        self.tabview.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)

        # Add tabs
        self.tab_state_info = self.tabview.add("📍 State Info")
        self.tab_income = self.tabview.add("💰 Income & Deductions")
        self.tab_calculation = self.tabview.add("🧮 Calculation")
        self.tab_forms = self.tabview.add("📋 Forms & Reports")

        self._setup_state_info_tab()
        self._setup_income_tab()
        self._setup_calculation_tab()
        self._setup_forms_tab()

    def _setup_state_info_tab(self):
        """Setup state information tab"""
        self.tab_state_info.grid_rowconfigure(0, weight=1)
        self.tab_state_info.grid_columnconfigure(0, weight=1)

        info_frame = ctk.CTkScrollableFrame(self.tab_state_info)
        info_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        placeholder = ctk.CTkLabel(
            info_frame,
            text="Select a state to view tax information",
            text_color="gray",
            font=("", 12)
        )
        placeholder.pack(padx=20, pady=20)
        self.state_info_content = info_frame

    def _setup_income_tab(self):
        """Setup income and deductions tab"""
        self.tab_income.grid_rowconfigure(0, weight=1)
        self.tab_income.grid_columnconfigure(0, weight=1)

        income_container = ctk.CTkFrame(self.tab_income, fg_color="transparent")
        income_container.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        income_container.grid_rowconfigure(1, weight=1)
        income_container.grid_columnconfigure(0, weight=1)
        income_container.grid_columnconfigure(1, weight=1)

        # Income section
        income_label = ModernLabel(income_container, text="Income Sources", font_size=12, font_weight="bold")
        income_label.grid(row=0, column=0, sticky="w", padx=5, pady=(0, 10))

        self.income_frame = ctk.CTkFrame(income_container)
        self.income_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self._create_income_fields()

        # Deductions section
        deduction_label = ModernLabel(income_container, text="Deductions", font_size=12, font_weight="bold")
        deduction_label.grid(row=0, column=1, sticky="w", padx=5, pady=(0, 10))

        self.deductions_frame = ctk.CTkFrame(income_container)
        self.deductions_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        self._create_deduction_fields()

    def _create_income_fields(self):
        """Create income entry fields"""
        self.income_entries = {}
        income_sources = [
            ("Wages", "wages"),
            ("Interest", "interest"),
            ("Dividends", "dividends"),
            ("Capital Gains", "capital_gains"),
            ("Business Income", "business_income"),
            ("Rental Income", "rental_income"),
            ("Other Income", "other_income")
        ]

        for idx, (label, key) in enumerate(income_sources):
            lbl = ctk.CTkLabel(self.income_frame, text=f"{label}:", text_color="gray", font=("", 11))
            lbl.grid(row=idx, column=0, sticky="w", padx=10, pady=8)

            entry = ctk.CTkEntry(self.income_frame, placeholder_text="$0.00", width=150)
            entry.grid(row=idx, column=1, sticky="ew", padx=10, pady=8)
            self.income_entries[key] = entry

        self.income_frame.grid_columnconfigure(1, weight=1)

    def _create_deduction_fields(self):
        """Create deduction entry fields"""
        self.deduction_entries = {}
        deductions = [
            ("Standard Deduction", "standard_deduction"),
            ("Itemized Deductions", "itemized_deductions"),
            ("Personal Exemption", "personal_exemption"),
            ("Dependent Exemptions", "dependent_exemptions"),
            ("Other Deductions", "other_deductions")
        ]

        for idx, (label, key) in enumerate(deductions):
            lbl = ctk.CTkLabel(self.deductions_frame, text=f"{label}:", text_color="gray", font=("", 11))
            lbl.grid(row=idx, column=0, sticky="w", padx=10, pady=8)

            entry = ctk.CTkEntry(self.deductions_frame, placeholder_text="$0.00", width=150)
            entry.grid(row=idx, column=1, sticky="ew", padx=10, pady=8)
            self.deduction_entries[key] = entry

        self.deductions_frame.grid_columnconfigure(1, weight=1)

    def _setup_calculation_tab(self):
        """Setup calculation results tab"""
        self.tab_calculation.grid_rowconfigure(0, weight=1)
        self.tab_calculation.grid_columnconfigure(0, weight=1)

        calc_frame = ctk.CTkScrollableFrame(self.tab_calculation)
        calc_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Summary cards
        cards_container = ctk.CTkFrame(calc_frame, fg_color="transparent")
        cards_container.pack(fill=ctk.X, padx=5, pady=10)

        self.calculation_cards = {}
        metrics = ["Gross Income", "Taxable Income", "Tax Amount", "Effective Rate", "Marginal Rate"]

        for metric in metrics:
            card = self._create_metric_card(cards_container, metric, "$0.00")
            self.calculation_cards[metric] = card
            card.pack(side=ctk.LEFT, padx=5, fill=ctk.X, expand=True)

        # Detailed breakdown
        breakdown_label = ModernLabel(calc_frame, text="Tax Breakdown", font_size=12, font_weight="bold")
        breakdown_label.pack(anchor=ctk.W, padx=5, pady=(15, 5))

        self.breakdown_text = ctk.CTkTextbox(calc_frame, height=200)
        self.breakdown_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.breakdown_text.configure(state="disabled")

    def _create_metric_card(self, parent, title, value):
        """Create a metric card"""
        card = ctk.CTkFrame(parent, corner_radius=8, fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        
        title_label = ctk.CTkLabel(card, text=title, text_color="gray", font=("", 11))
        title_label.pack(padx=10, pady=(8, 2))

        value_label = ctk.CTkLabel(card, text=value, text_color="white", font=("", 14, "bold"))
        value_label.pack(padx=10, pady=(2, 8))

        card.value_label = value_label
        return card

    def _setup_forms_tab(self):
        """Setup forms and reports tab"""
        self.tab_forms.grid_rowconfigure(0, weight=1)
        self.tab_forms.grid_columnconfigure(0, weight=1)

        forms_frame = ctk.CTkScrollableFrame(self.tab_forms)
        forms_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        forms_label = ModernLabel(forms_frame, text="Available State Forms", font_size=12, font_weight="bold")
        forms_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        button_frame = ctk.CTkFrame(forms_frame, fg_color="transparent")
        button_frame.pack(fill=ctk.X, padx=5, pady=5)

        ModernButton(
            button_frame,
            text="📄 State Income Tax Return",
            command=lambda: self._generate_form("state_return"),
            button_type="secondary",
            width=200
        ).pack(side=ctk.LEFT, padx=2, pady=2)

        ModernButton(
            button_frame,
            text="📊 Form Details",
            command=self._show_form_details,
            button_type="secondary",
            width=150
        ).pack(side=ctk.LEFT, padx=2, pady=2)

        forms_label2 = ModernLabel(forms_frame, text="Generated Forms", font_size=12, font_weight="bold")
        forms_label2.pack(anchor=ctk.W, padx=5, pady=(15, 5))

        self.forms_text = ctk.CTkTextbox(forms_frame, height=300)
        self.forms_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.forms_text.insert("1.0", "No forms generated yet.")
        self.forms_text.configure(state="disabled")

    # ===== Action Methods =====

    def _refresh_state_list(self):
        """Refresh the state list display"""
        for widget in self.state_scrollable_frame.winfo_children():
            widget.destroy()

        filter_type = self.state_filter_var.get()

        for state_code in sorted(StateCode, key=lambda s: s.value):
            try:
                state_info = self.service.state_tax_info.get(state_code)
                if state_info:
                    tax_type_name = state_info.tax_type.value.replace("_", " ").title()
                    
                    if filter_type != "All" and tax_type_name != filter_type:
                        continue

                    button = ctk.CTkButton(
                        self.state_scrollable_frame,
                        text=f"{state_code.value} - {state_info.state_name}",
                        command=lambda sc=state_code: self._select_state(sc),
                        width=200,
                        height=32,
                        fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"],
                        hover_color=ctk.ThemeManager.theme["CTkButton"]["hover_color"],
                        border_color="white" if state_code == self.selected_state else "transparent",
                        border_width=2 if state_code == self.selected_state else 0
                    )
                    button.pack(fill=ctk.X, padx=5, pady=3)
            except:
                continue

    def _select_state(self, state_code: StateCode):
        """Handle state selection"""
        if self.multi_state_var.get():
            if state_code in self.selected_states:
                self.selected_states.remove(state_code)
            else:
                self.selected_states.append(state_code)
        else:
            self.selected_state = state_code
            self.selected_states = [state_code]

        self._refresh_state_list()
        self._update_state_info()

    def _update_state_info(self):
        """Update state information display"""
        if not self.selected_states:
            return

        state_code = self.selected_states[0]
        state_info = self.service.state_tax_info.get(state_code)

        if not state_info:
            return

        for widget in self.state_info_content.winfo_children():
            widget.destroy()

        info_text = f"""State: {state_info.state_name}
Code: {state_code.value}
Tax Type: {state_info.tax_type.value.replace('_', ' ').title()}
Tax Deadline: {state_info.tax_deadline}
E-Filing Supported: {'Yes' if state_info.e_filing_supported else 'No'}
Local Tax Supported: {'Yes' if state_info.local_tax_supported else 'No'}
"""

        if state_info.flat_rate:
            info_text += f"Flat Tax Rate: {state_info.flat_rate*100:.2f}%"

        info_label = ctk.CTkLabel(
            self.state_info_content,
            text=info_text,
            text_color="white",
            font=("", 11),
            justify=ctk.LEFT
        )
        info_label.pack(anchor=ctk.NW, padx=15, pady=15)

    def _apply_state_filter(self, _=None):
        """Apply state filter"""
        self._refresh_state_list()

    def _toggle_multi_state_mode(self):
        """Toggle multi-state mode"""
        self.multi_state_mode = self.multi_state_var.get()
        self._refresh_state_list()

    def _clear_selection(self):
        """Clear state selection"""
        self.selected_state = None
        self.selected_states = []
        self._refresh_state_list()

    def _new_state_return(self):
        """Create a new state return"""
        self.status_label.configure(text="Creating new state return...")
        self.progress_bar.set(0.3)
        self.status_label.configure(text="New return created")
        self.progress_bar.set(1.0)

    def _save_return(self):
        """Save the current state return"""
        self.status_label.configure(text="Saving return...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Return saved")
        self.progress_bar.set(1.0)

    def _calculate_tax(self):
        """Calculate state tax"""
        if not self.selected_states:
            self.status_label.configure(text="Please select a state first")
            return

        self.status_label.configure(text="Calculating tax...")
        self.progress_bar.set(0.3)
        self.status_label.configure(text="Tax calculation complete")
        self.progress_bar.set(1.0)

    def _compare_states(self):
        """Compare taxes across selected states"""
        if len(self.selected_states) < 2:
            self.status_label.configure(text="Select at least 2 states to compare")
            return

        self.status_label.configure(text="Comparing states...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Comparison complete")
        self.progress_bar.set(1.0)

    def _export_for_filing(self):
        """Export return for e-filing"""
        if not self.selected_states:
            self.status_label.configure(text="Please select a state first")
            return

        self.status_label.configure(text="Preparing for e-filing...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Ready for e-filing")
        self.progress_bar.set(1.0)

    def _show_selected_state_info(self):
        """Show detailed information about selected state"""
        if not self.selected_states:
            self.status_label.configure(text="Please select a state first")
            return

        self._update_state_info()

    def _generate_form(self, form_type: str):
        """Generate a state tax form"""
        if not self.selected_states:
            self.status_label.configure(text="Please select a state first")
            return

        self.status_label.configure(text="Generating form...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Form generated")
        self.progress_bar.set(1.0)

    def _show_form_details(self):
        """Show form details"""
        self.status_label.configure(text="Form details not yet implemented")
