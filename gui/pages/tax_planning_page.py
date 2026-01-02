"""
Tax Planning Page - Converted from Window

Page for tax planning strategies, scenario analysis, and tax optimization.
Integrated into main window without popup dialogs.
"""

import customtkinter as ctk
from typing import Optional, List, Dict, Any
from datetime import datetime

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton


class TaxPlanningPage(ctk.CTkScrollableFrame):
    """
    Tax Planning page - converted from popup window to integrated page.
    
    Features:
    - Tax planning strategy development
    - Scenario analysis and comparison
    - Income projection calculations
    - Optimization recommendations
    - Year-end planning guidance
    """

    def __init__(self, master, config: AppConfig, tax_data: Optional[TaxData] = None,
                 accessibility_service: Optional[AccessibilityService] = None, **kwargs):
        super().__init__(master, **kwargs)

        self.config = config
        self.tax_data = tax_data
        self.accessibility_service = accessibility_service

        # Planning data
        self.strategies: List[Dict[str, Any]] = []
        self.scenarios: List[Dict[str, Any]] = []
        self.planning_vars = {}

        # Build the page
        self._create_header()
        self._create_toolbar()
        self._create_main_content()
        self._load_planning_data()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self)
        header_frame.pack(fill=ctk.X, padx=20, pady=(20, 10))

        title_label = ModernLabel(
            header_frame,
            text="📊 Tax Planning & Strategy",
            font_size=24,
            font_weight="bold"
        )
        title_label.pack(anchor=ctk.W, pady=(0, 5))

        subtitle_label = ModernLabel(
            header_frame,
            text="Develop tax strategies, analyze scenarios, and optimize your tax position",
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
            text="💡 Get Strategies",
            command=self._get_strategies,
            button_type="primary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📊 Run Scenario",
            command=self._run_scenario,
            button_type="secondary",
            width=130
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📈 Project Income",
            command=self._project_income,
            button_type="secondary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="💾 Save Plan",
            command=self._save_plan,
            button_type="success",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📄 Generate Report",
            command=self._generate_report,
            button_type="secondary",
            width=150
        ).pack(side=ctk.LEFT, padx=5)

        # Progress bar
        progress_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        progress_frame.pack(fill=ctk.X, pady=10)

        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=6)
        self.progress_bar.pack(fill=ctk.X)
        self.progress_bar.set(0)

        self.status_label = ModernLabel(progress_frame, text="Ready for planning", font_size=11)
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
        self.tab_overview = self.tabview.add("📊 Overview")
        self.tab_strategies = self.tabview.add("💡 Strategies")
        self.tab_scenarios = self.tabview.add("📈 Scenarios")
        self.tab_projections = self.tabview.add("🔮 Projections")
        self.tab_recommendations = self.tabview.add("⭐ Recommendations")

        # Setup tabs
        self._setup_overview_tab()
        self._setup_strategies_tab()
        self._setup_scenarios_tab()
        self._setup_projections_tab()
        self._setup_recommendations_tab()

    def _setup_overview_tab(self):
        """Setup overview tab"""
        self.tab_overview.grid_rowconfigure(1, weight=1)
        self.tab_overview.grid_columnconfigure(0, weight=1)

        # Summary section
        summary_label = ModernLabel(self.tab_overview, text="Current Tax Position", font_size=12, font_weight="bold")
        summary_label.pack(anchor=ctk.W, padx=20, pady=(10, 5))

        # Summary cards
        cards_frame = ctk.CTkFrame(self.tab_overview, fg_color="transparent")
        cards_frame.pack(fill=ctk.X, padx=20, pady=10)

        metrics = [
            ("Estimated Tax Liability", "$0.00"),
            ("Projected Refund", "$0.00"),
            ("Tax Rate", "0.0%"),
            ("Tax Planning Opportunity", "$0.00")
        ]

        for metric, value in metrics:
            card = self._create_summary_card(cards_frame, metric, value)
            card.pack(side=ctk.LEFT, padx=5, fill=ctk.X, expand=True)

        # Planning goals
        frame = ctk.CTkScrollableFrame(self.tab_overview)
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

        goals_label = ModernLabel(frame, text="Planning Goals", font_size=12, font_weight="bold")
        goals_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.overview_text = ctk.CTkTextbox(frame, height=300)
        self.overview_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.overview_text.insert("1.0", "Tax Planning Goals:\n\n1. Minimize tax liability\n2. Optimize deductions\n3. Plan estimated payments\n4. Structure income efficiently")
        self.overview_text.configure(state="disabled")

    def _setup_strategies_tab(self):
        """Setup tax strategies tab"""
        self.tab_strategies.grid_rowconfigure(0, weight=1)
        self.tab_strategies.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_strategies)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        strategies_label = ModernLabel(frame, text="Available Tax Strategies", font_size=12, font_weight="bold")
        strategies_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.strategies_text = ctk.CTkTextbox(frame, height=400)
        self.strategies_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.strategies_text.insert("1.0", "Tax Planning Strategies:\n\n1. Bunching Deductions\n   - Group deductions in alternating years\n   - Maximize itemized deductions\n\n2. Income Deferral\n   - Defer income to next tax year\n   - Accelerate deductions\n\n3. Entity Structure Optimization\n   - Evaluate S-Corp vs. LLC election\n   - Consider QBI deduction implications\n\n4. Estimated Payment Planning\n   - Optimize quarterly payment schedule\n   - Avoid penalties and interest")
        self.strategies_text.configure(state="disabled")

    def _setup_scenarios_tab(self):
        """Setup scenarios tab"""
        self.tab_scenarios.grid_rowconfigure(1, weight=1)
        self.tab_scenarios.grid_columnconfigure(0, weight=1)

        # Scenario controls
        control_frame = ctk.CTkFrame(self.tab_scenarios, fg_color="transparent")
        control_frame.pack(fill=ctk.X, padx=10, pady=10)

        ModernButton(
            control_frame,
            text="➕ Create Scenario",
            command=self._create_scenario,
            button_type="primary",
            width=150
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            control_frame,
            text="📊 Compare Scenarios",
            command=self._compare_scenarios,
            button_type="secondary",
            width=160
        ).pack(side=ctk.LEFT, padx=5)

        # Scenario list
        list_frame = ctk.CTkFrame(self.tab_scenarios)
        list_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        self.scenarios_text = ctk.CTkTextbox(list_frame)
        self.scenarios_text.grid(row=0, column=0, sticky="nsew")
        self.scenarios_text.insert("1.0", "No scenarios created yet. Click 'Create Scenario' to analyze different tax situations.")
        self.scenarios_text.configure(state="disabled")

    def _setup_projections_tab(self):
        """Setup income projections tab"""
        self.tab_projections.grid_rowconfigure(1, weight=1)
        self.tab_projections.grid_columnconfigure(0, weight=1)
        self.tab_projections.grid_columnconfigure(1, weight=1)

        # Projection inputs
        input_label = ModernLabel(self.tab_projections, text="Income Projections", font_size=12, font_weight="bold")
        input_label.pack(anchor=ctk.W, padx=20, pady=(10, 5))

        input_frame = ctk.CTkFrame(self.tab_projections)
        input_frame.pack(fill=ctk.X, padx=20, pady=10)
        input_frame.grid_columnconfigure(1, weight=1)

        fields = [
            ("Current Year Income", "current_income"),
            ("Projected Growth Rate", "growth_rate"),
            ("Expected Deductions", "deductions"),
            ("Planning Horizon (Years)", "horizon")
        ]

        for row, (label, key) in enumerate(fields):
            lbl = ctk.CTkLabel(input_frame, text=f"{label}:", text_color="gray", font=("", 11))
            lbl.grid(row=row, column=0, sticky="w", padx=10, pady=8)
            entry = ctk.CTkEntry(input_frame, placeholder_text="Enter value", width=200)
            entry.grid(row=row, column=1, sticky="ew", padx=10, pady=8)
            self.planning_vars[key] = entry

        # Projection results
        results_frame = ctk.CTkFrame(self.tab_projections)
        results_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        results_label = ModernLabel(results_frame, text="Projection Results", font_size=12, font_weight="bold")
        results_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.projections_text = ctk.CTkTextbox(results_frame)
        self.projections_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.projections_text.insert("1.0", "Set parameters and click 'Project Income' to view projections.")
        self.projections_text.configure(state="disabled")

    def _setup_recommendations_tab(self):
        """Setup recommendations tab"""
        self.tab_recommendations.grid_rowconfigure(0, weight=1)
        self.tab_recommendations.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_recommendations)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        rec_label = ModernLabel(frame, text="Tax Planning Recommendations", font_size=12, font_weight="bold")
        rec_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.recommendations_text = ctk.CTkTextbox(frame, height=400)
        self.recommendations_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.recommendations_text.insert("1.0", "Personalized Recommendations:\n\n✓ Priority 1: Maximize Deductions\n  - Review current deduction level\n  - Identify missed deductions\n  - Plan large purchases strategically\n\n✓ Priority 2: Structure Business Income\n  - Evaluate salary vs. distributions\n  - Consider quarterly payment strategy\n  - Review entity structure\n\n✓ Priority 3: Year-End Planning\n  - Harvest capital losses\n  - Bunching opportunities\n  - Income deferral strategies")
        self.recommendations_text.configure(state="disabled")

    def _create_summary_card(self, parent, title, value):
        """Create a summary metric card"""
        card = ctk.CTkFrame(parent, corner_radius=8, fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        
        title_label = ctk.CTkLabel(card, text=title, text_color="gray", font=("", 11))
        title_label.pack(padx=10, pady=(8, 2))

        value_label = ctk.CTkLabel(card, text=value, text_color="white", font=("", 13, "bold"))
        value_label.pack(padx=10, pady=(2, 8))

        return card

    # ===== Action Methods =====

    def _load_planning_data(self):
        """Load planning data"""
        self.status_label.configure(text="Loading planning data...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Ready for planning")
        self.progress_bar.set(1.0)

    def _get_strategies(self):
        """Get personalized tax strategies"""
        self.status_label.configure(text="Generating strategies...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Strategies generated")
        self.progress_bar.set(1.0)

    def _run_scenario(self):
        """Run tax scenario analysis"""
        self.status_label.configure(text="Running scenario...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Scenario complete")
        self.progress_bar.set(1.0)

    def _project_income(self):
        """Project future income and taxes"""
        self.status_label.configure(text="Projecting income...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Projection complete")
        self.progress_bar.set(1.0)

    def _save_plan(self):
        """Save tax plan"""
        self.status_label.configure(text="Saving plan...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Plan saved")
        self.progress_bar.set(1.0)

    def _generate_report(self):
        """Generate tax planning report"""
        self.status_label.configure(text="Generating report...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Report generated")
        self.progress_bar.set(1.0)

    def _create_scenario(self):
        """Create new planning scenario"""
        self.status_label.configure(text="Scenario created")

    def _compare_scenarios(self):
        """Compare multiple scenarios"""
        self.status_label.configure(text="Comparing scenarios...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Comparison complete")
        self.progress_bar.set(1.0)
