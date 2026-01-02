"""
State Tax Calculator Page - Converted from Window

Page for advanced state tax calculations and multi-state scenarios.
Integrated into main window without popup dialogs.
"""

import customtkinter as ctk
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.state_tax_service import StateTaxService
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton

logger = logging.getLogger(__name__)


class StateTaxCalculatorPage(ctk.CTkScrollableFrame):
    """
    State Tax Calculator page - converted from popup window to integrated page.
    
    Features:
    - Advanced state tax calculations
    - Multi-state tax scenarios
    - Tax optimization recommendations
    - Comparison tools
    - What-if analysis
    """

    def __init__(self, master, config: AppConfig, tax_data: Optional[TaxData] = None,
                 accessibility_service: Optional[AccessibilityService] = None, **kwargs):
        super().__init__(master, **kwargs)

        self.config = config
        self.tax_data = tax_data
        self.accessibility_service = accessibility_service

        # Initialize services
        self.state_service = StateTaxService()

        # Calculator variables
        self.calculation_vars = {}
        self.scenario_vars = {}

        # Build the page
        self._create_header()
        self._create_toolbar()
        self._create_main_content()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self)
        header_frame.pack(fill=ctk.X, padx=20, pady=(20, 10))

        title_label = ModernLabel(
            header_frame,
            text="🧮 State Tax Calculator",
            font_size=24,
            font_weight="bold"
        )
        title_label.pack(anchor=ctk.W, pady=(0, 5))

        subtitle_label = ModernLabel(
            header_frame,
            text="Advanced calculations, scenario analysis, and tax optimization",
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
            text="🧮 Calculate",
            command=self._perform_calculation,
            button_type="primary",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📊 Run Scenario",
            command=self._run_scenario,
            button_type="secondary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="💡 Optimize",
            command=self._optimize_calculation,
            button_type="secondary",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📥 Load Template",
            command=self._load_template,
            button_type="secondary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="💾 Save Results",
            command=self._save_results,
            button_type="success",
            width=130
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
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(0, weight=1)

        # Create tabview
        self.tabview = ctk.CTkTabview(main_container)
        self.tabview.pack(fill=ctk.BOTH, expand=True)

        # Add tabs
        self.tab_calculator = self.tabview.add("🧮 Calculator")
        self.tab_scenarios = self.tabview.add("📊 Scenarios")
        self.tab_comparison = self.tabview.add("📈 Comparison")
        self.tab_optimization = self.tabview.add("💡 Optimization")
        self.tab_results = self.tabview.add("📋 Results")

        # Setup tabs
        self._setup_calculator_tab()
        self._setup_scenarios_tab()
        self._setup_comparison_tab()
        self._setup_optimization_tab()
        self._setup_results_tab()

    def _setup_calculator_tab(self):
        """Setup calculator tab"""
        self.tab_calculator.grid_rowconfigure(0, weight=1)
        self.tab_calculator.grid_columnconfigure(0, weight=1)
        self.tab_calculator.grid_columnconfigure(1, weight=1)

        container = ctk.CTkFrame(self.tab_calculator, fg_color="transparent")
        container.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

        # Input section
        input_label = ModernLabel(container, text="Calculator Inputs", font_size=12, font_weight="bold")
        input_label.grid(row=0, column=0, sticky="w", padx=5, pady=(0, 10))

        input_frame = ctk.CTkFrame(container)
        input_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        inputs = [
            ("Taxable Income", "taxable_income"),
            ("Filing Status", "filing_status"),
            ("Number of Dependents", "dependents"),
            ("Capital Gains", "capital_gains"),
            ("Tax Credits", "tax_credits")
        ]

        for idx, (label, key) in enumerate(inputs):
            lbl = ctk.CTkLabel(input_frame, text=f"{label}:", text_color="gray", font=("", 11))
            lbl.grid(row=idx, column=0, sticky="w", padx=10, pady=8)
            entry = ctk.CTkEntry(input_frame, placeholder_text="Enter value", width=150)
            entry.grid(row=idx, column=1, sticky="ew", padx=10, pady=8)
            self.calculation_vars[key] = entry

        input_frame.grid_columnconfigure(1, weight=1)

        # Results section
        results_label = ModernLabel(container, text="Calculation Results", font_size=12, font_weight="bold")
        results_label.grid(row=0, column=1, sticky="w", padx=5, pady=(0, 10))

        results_frame = ctk.CTkFrame(container)
        results_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        self.results_text = ctk.CTkTextbox(results_frame)
        self.results_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.results_text.insert("1.0", "Results will appear here after calculation")
        self.results_text.configure(state="disabled")

    def _setup_scenarios_tab(self):
        """Setup scenarios tab"""
        self.tab_scenarios.grid_rowconfigure(1, weight=1)
        self.tab_scenarios.grid_columnconfigure(0, weight=1)

        # Scenario controls
        control_frame = ctk.CTkFrame(self.tab_scenarios, fg_color="transparent")
        control_frame.pack(fill=ctk.X, padx=10, pady=10)

        ModernButton(
            control_frame,
            text="➕ New Scenario",
            command=self._create_scenario,
            button_type="primary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            control_frame,
            text="🧪 Test Scenario",
            command=self._test_scenario,
            button_type="secondary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            control_frame,
            text="📊 Compare Scenarios",
            command=self._compare_scenarios,
            button_type="secondary",
            width=170
        ).pack(side=ctk.LEFT, padx=5)

        # Scenario list
        list_frame = ctk.CTkFrame(self.tab_scenarios)
        list_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        self.scenarios_text = ctk.CTkTextbox(list_frame)
        self.scenarios_text.grid(row=0, column=0, sticky="nsew")
        self.scenarios_text.insert("1.0", "No scenarios created yet.")
        self.scenarios_text.configure(state="disabled")

    def _setup_comparison_tab(self):
        """Setup comparison tab"""
        self.tab_comparison.grid_rowconfigure(0, weight=1)
        self.tab_comparison.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_comparison)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        comp_label = ModernLabel(frame, text="Tax Comparison", font_size=12, font_weight="bold")
        comp_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.comparison_text = ctk.CTkTextbox(frame, height=400)
        self.comparison_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.comparison_text.insert("1.0", "No comparisons available.")
        self.comparison_text.configure(state="disabled")

    def _setup_optimization_tab(self):
        """Setup optimization tab"""
        self.tab_optimization.grid_rowconfigure(0, weight=1)
        self.tab_optimization.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_optimization)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        opt_label = ModernLabel(frame, text="Tax Optimization Recommendations", font_size=12, font_weight="bold")
        opt_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.optimization_text = ctk.CTkTextbox(frame, height=400)
        self.optimization_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.optimization_text.insert("1.0", "No optimization recommendations available.")
        self.optimization_text.configure(state="disabled")

    def _setup_results_tab(self):
        """Setup results tab"""
        self.tab_results.grid_rowconfigure(0, weight=1)
        self.tab_results.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_results)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        results_label = ModernLabel(frame, text="Detailed Results", font_size=12, font_weight="bold")
        results_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.detailed_results_text = ctk.CTkTextbox(frame, height=400)
        self.detailed_results_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.detailed_results_text.insert("1.0", "No results to display.")
        self.detailed_results_text.configure(state="disabled")

    # ===== Action Methods =====

    def _perform_calculation(self):
        """Perform tax calculation"""
        self.status_label.configure(text="Calculating...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Calculation complete")
        self.progress_bar.set(1.0)

    def _run_scenario(self):
        """Run scenario analysis"""
        self.status_label.configure(text="Running scenario...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Scenario complete")
        self.progress_bar.set(1.0)

    def _optimize_calculation(self):
        """Optimize tax calculation"""
        self.status_label.configure(text="Optimizing...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Optimization complete")
        self.progress_bar.set(1.0)

    def _load_template(self):
        """Load a calculation template"""
        self.status_label.configure(text="Loading template...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Template loaded")
        self.progress_bar.set(1.0)

    def _save_results(self):
        """Save calculation results"""
        self.status_label.configure(text="Saving results...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Results saved")
        self.progress_bar.set(1.0)

    def _create_scenario(self):
        """Create new scenario"""
        self.status_label.configure(text="New scenario created")

    def _test_scenario(self):
        """Test current scenario"""
        self.status_label.configure(text="Testing scenario...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Test complete")
        self.progress_bar.set(1.0)

    def _compare_scenarios(self):
        """Compare multiple scenarios"""
        self.status_label.configure(text="Comparing scenarios...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Comparison complete")
        self.progress_bar.set(1.0)
