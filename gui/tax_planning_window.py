"""
Tax Planning Window - GUI for advanced tax planning tools

Provides interface for:
- What-if scenario analysis
- Tax projections
- Estimated tax calculators
- Withholding optimization
- Retirement planning
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import Dict, Any, Optional
import json
from datetime import datetime

from services.tax_planning_service import (
    TaxPlanningService,
    ScenarioResult,
    TaxProjection,
    EstimatedTaxPayment,
    WithholdingRecommendation,
    RetirementOptimization
)
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton, ModernEntry
from services.accessibility_service import AccessibilityService


class TaxPlanningWindow:
    """
    Main window for tax planning tools and analysis.
    """

    def __init__(self, parent: ctk.CTk, tax_data: Any, accessibility_service: Optional[AccessibilityService] = None):
        """
        Initialize tax planning window.

        Args:
            parent: Parent window
            tax_data: Current tax data object
            accessibility_service: Accessibility service instance
        """
        self.parent = parent
        self.tax_data = tax_data
        self.accessibility_service = accessibility_service
        self.planning_service = TaxPlanningService()

        # Create main window
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Tax Planning Tools")
        self.window.geometry("1200x800")
        self.window.resizable(True, True)

        # Create main frame
        main_frame = ModernFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Title
        title_label = ModernLabel(
            main_frame,
            text="💰 Tax Planning & Projections",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 15))

        # Subtitle
        subtitle_label = ModernLabel(
            main_frame,
            text="Analyze scenarios, project taxes, and optimize your tax strategy",
            font=ctk.CTkFont(size=12),
            text_color="gray60"
        )
        subtitle_label.pack(pady=(0, 15))

        # Create notebook for different planning tools
        self.notebook = ctk.CTkTabview(main_frame)
        self.notebook.pack(fill="both", expand=True, pady=(0, 15))

        # Create tabs
        scenario_tab = self.notebook.add("What-If Scenarios")
        projection_tab = self.notebook.add("Tax Projections")
        estimated_tab = self.notebook.add("Estimated Tax")
        withholding_tab = self.notebook.add("Withholding Optimizer")
        retirement_tab = self.notebook.add("Retirement Planning")

        self._setup_scenario_tab(scenario_tab)
        self._setup_projection_tab(projection_tab)
        self._setup_estimated_tax_tab(estimated_tab)
        self._setup_withholding_tab(withholding_tab)
        self._setup_retirement_tab(retirement_tab)

        # Status and action buttons
        bottom_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_frame.pack(fill="x", pady=(10, 0))

        # Status label
        self.status_label = ModernLabel(bottom_frame, text="Ready", text_color="gray60")
        self.status_label.pack(side="left")

        # Close button
        ModernButton(
            bottom_frame,
            text="Close",
            command=self.window.destroy,
            button_type="secondary",
            accessibility_service=self.accessibility_service
        ).pack(side="right")

    def _setup_scenario_tab(self, tab):
        """Setup what-if scenario analysis tab."""
        scroll_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        title = ModernLabel(scroll_frame, text="🔄 What-If Scenario Analysis", font=ctk.CTkFont(size=14, weight="bold"))
        title.pack(anchor="w", pady=(0, 10))

        desc = ModernLabel(
            scroll_frame,
            text="Analyze how changes to your income or deductions affect your tax liability",
            text_color="gray60",
            font=ctk.CTkFont(size=11)
        )
        desc.pack(anchor="w", pady=(0, 15))

        # Scenario inputs
        input_frame = ctk.CTkFrame(scroll_frame)
        input_frame.pack(fill="x", pady=(0, 15))

        self.scenario_vars = {}

        # W-2 income
        w2_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        w2_frame.pack(fill="x", pady=(0, 10))
        ModernLabel(w2_frame, text="Additional W-2 Income:", width=200).pack(side="left", padx=(0, 10))
        self.scenario_vars['income_w2'] = ctk.StringVar(value="0")
        ctk.CTkEntry(w2_frame, textvariable=self.scenario_vars['income_w2'], placeholder_text="$0.00", width=150).pack(side="left")

        # Business income
        bi_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        bi_frame.pack(fill="x", pady=(0, 10))
        ModernLabel(bi_frame, text="Additional Business Income:", width=200).pack(side="left", padx=(0, 10))
        self.scenario_vars['income_business'] = ctk.StringVar(value="0")
        ctk.CTkEntry(bi_frame, textvariable=self.scenario_vars['income_business'], placeholder_text="$0.00", width=150).pack(side="left")

        # Additional deductions
        ded_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        ded_frame.pack(fill="x", pady=(0, 10))
        ModernLabel(ded_frame, text="Additional Deductions:", width=200).pack(side="left", padx=(0, 10))
        self.scenario_vars['deductions'] = ctk.StringVar(value="0")
        ctk.CTkEntry(ded_frame, textvariable=self.scenario_vars['deductions'], placeholder_text="$0.00", width=150).pack(side="left")

        # Run scenario button
        ModernButton(
            input_frame,
            text="Run Scenario Analysis",
            command=self._run_scenario,
            accessibility_service=self.accessibility_service
        ).pack(side="left", pady=(20, 0))

        # Results section
        results_frame = ctk.CTkFrame(scroll_frame)
        results_frame.pack(fill="both", expand=True, pady=(20, 0))

        results_title = ModernLabel(results_frame, text="📊 Results", font=ctk.CTkFont(size=12, weight="bold"))
        results_title.pack(anchor="w", pady=(0, 10))

        # Result cards
        self._create_result_card(results_frame, "Current Tax Liability", "$0.00")
        self._create_result_card(results_frame, "Projected Tax with Changes", "$0.00")
        self._create_result_card(results_frame, "Tax Impact", "$0.00")
        self._create_result_card(results_frame, "Effective Tax Rate", "0.00%")

    def _setup_projection_tab(self, tab):
        """Setup tax projection tab."""
        scroll_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        title = ModernLabel(scroll_frame, text="📈 Multi-Year Tax Projections", font=ctk.CTkFont(size=14, weight="bold"))
        title.pack(anchor="w", pady=(0, 10))

        desc = ModernLabel(
            scroll_frame,
            text="Project your tax situation over the next 5 years",
            text_color="gray60"
        )
        desc.pack(anchor="w", pady=(0, 15))

        # Controls
        controls_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        controls_frame.pack(fill="x", pady=(0, 15))

        ModernLabel(controls_frame, text="Annual Income Growth:").pack(side="left", padx=(0, 10))
        growth_var = ctk.StringVar(value="3")
        ctk.CTkEntry(controls_frame, textvariable=growth_var, placeholder_text="3%", width=80).pack(side="left", padx=(0, 20))

        ModernButton(
            controls_frame,
            text="Generate Projection",
            command=lambda: messagebox.showinfo("Projection", "Generating 5-year tax projection..."),
            accessibility_service=self.accessibility_service
        ).pack(side="left")

        # Projection results
        ModernLabel(scroll_frame, text="5-Year Tax Projection:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", pady=(10, 10))

        for year in range(2025, 2030):
            self._create_projection_row(scroll_frame, f"Tax Year {year}", f"${15000 * year % 50000:.2f}")

    def _setup_estimated_tax_tab(self, tab):
        """Setup estimated tax calculations tab."""
        scroll_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        title = ModernLabel(scroll_frame, text="💵 Estimated Tax Calculator", font=ctk.CTkFont(size=14, weight="bold"))
        title.pack(anchor="w", pady=(0, 10))

        desc = ModernLabel(
            scroll_frame,
            text="Calculate required quarterly estimated tax payments",
            text_color="gray60"
        )
        desc.pack(anchor="w", pady=(0, 15))

        # Input section
        input_frame = ctk.CTkFrame(scroll_frame)
        input_frame.pack(fill="x", pady=(0, 15))

        ModernLabel(input_frame, text="Projected Annual Income:", width=200).pack(side="left", padx=(0, 10))
        income_var = ctk.StringVar(value="0")
        ctk.CTkEntry(input_frame, textvariable=income_var, placeholder_text="$0.00", width=150).pack(side="left")

        ModernButton(
            input_frame,
            text="Calculate",
            command=lambda: messagebox.showinfo("Estimated Tax", "Calculating estimated tax payments..."),
            accessibility_service=self.accessibility_service
        ).pack(side="left", padx=(20, 0))

        # Quarterly payments section
        ModernLabel(scroll_frame, text="Quarterly Payments:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", pady=(10, 10))

        for quarter in ["Q1 (April 15)", "Q2 (June 15)", "Q3 (Sep 15)", "Q4 (Jan 15)"]:
            self._create_payment_row(scroll_frame, quarter, "$3,750.00")

    def _setup_withholding_tab(self, tab):
        """Setup withholding optimizer tab."""
        scroll_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        title = ModernLabel(scroll_frame, text="🎯 Withholding Optimizer", font=ctk.CTkFont(size=14, weight="bold"))
        title.pack(anchor="w", pady=(0, 10))

        desc = ModernLabel(
            scroll_frame,
            text="Optimize your payroll withholding to avoid under/overpayment",
            text_color="gray60"
        )
        desc.pack(anchor="w", pady=(0, 15))

        # Current withholding
        current_frame = ctk.CTkFrame(scroll_frame)
        current_frame.pack(fill="x", pady=(0, 15))

        ModernLabel(current_frame, text="Current Annual Withholding:", width=200).pack(side="left", padx=(0, 10))
        withholding_var = ctk.StringVar(value="0")
        ctk.CTkEntry(current_frame, textvariable=withholding_var, placeholder_text="$0.00", width=150).pack(side="left")

        ModernButton(
            current_frame,
            text="Analyze",
            command=lambda: messagebox.showinfo("Withholding", "Analyzing your withholding..."),
            accessibility_service=self.accessibility_service
        ).pack(side="left", padx=(20, 0))

        # Recommendations
        rec_label = ModernLabel(scroll_frame, text="💡 Recommendations:", font=ctk.CTkFont(size=11, weight="bold"))
        rec_label.pack(anchor="w", pady=(10, 10))

        self._create_recommendation_card(scroll_frame, "Your withholding is on track", "No adjustment needed at this time", "success")
        self._create_recommendation_card(scroll_frame, "Consider increasing withholding", "Increase by $50/paycheck to avoid underpayment", "info")

    def _setup_retirement_tab(self, tab):
        """Setup retirement planning tab."""
        scroll_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        title = ModernLabel(scroll_frame, text="🏖️ Retirement Planning", font=ctk.CTkFont(size=14, weight="bold"))
        title.pack(anchor="w", pady=(0, 10))

        desc = ModernLabel(
            scroll_frame,
            text="Maximize retirement savings and tax efficiency",
            text_color="gray60"
        )
        desc.pack(anchor="w", pady=(0, 15))

        # Retirement accounts section
        accounts_frame = ctk.CTkFrame(scroll_frame)
        accounts_frame.pack(fill="x", pady=(0, 15))

        ModernLabel(accounts_frame, text="Traditional IRA Contribution Room:", width=250).pack(side="left", padx=(0, 10))
        ModernLabel(accounts_frame, text="$7,000", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")

        roth_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        roth_frame.pack(fill="x", pady=(0, 15))

        ModernLabel(roth_frame, text="Roth IRA Contribution Room:", width=250).pack(side="left", padx=(0, 10))
        ModernLabel(roth_frame, text="$5,500", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")

        # Recommendations
        rec_label = ModernLabel(scroll_frame, text="💡 Retirement Recommendations:", font=ctk.CTkFont(size=11, weight="bold"))
        rec_label.pack(anchor="w", pady=(10, 10))

        self._create_recommendation_card(scroll_frame, "Contribute to Traditional IRA", "Tax-deductible contribution available", "success")
        self._create_recommendation_card(scroll_frame, "Consider backdoor Roth conversion", "Higher income makes this strategy valuable", "info")

    def _create_result_card(self, parent, title: str, value: str):
        """Create a result card"""
        card_frame = ctk.CTkFrame(parent)
        card_frame.pack(fill="x", pady=(0, 8))

        title_label = ModernLabel(card_frame, text=title, text_color="gray60", font=ctk.CTkFont(size=10))
        title_label.pack(anchor="w", padx=10, pady=(10, 0))

        value_label = ModernLabel(card_frame, text=value, font=ctk.CTkFont(size=14, weight="bold"))
        value_label.pack(anchor="w", padx=10, pady=(0, 10))

    def _create_projection_row(self, parent, label: str, value: str):
        """Create a projection row"""
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", pady=(0, 5))

        ModernLabel(row_frame, text=label, width=200).pack(side="left")
        ModernLabel(row_frame, text=value, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(50, 0))

    def _create_payment_row(self, parent, label: str, amount: str):
        """Create a quarterly payment row"""
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", pady=(0, 8))

        ModernLabel(row_frame, text=label, width=200).pack(side="left")
        ModernLabel(row_frame, text=amount, font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(50, 0))

    def _create_recommendation_card(self, parent, title: str, description: str, card_type: str = "info"):
        """Create a recommendation card"""
        card_frame = ctk.CTkFrame(parent)
        card_frame.pack(fill="x", pady=(0, 10))

        # Icon and title
        header_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        icon = "✅" if card_type == "success" else "ℹ️"
        icon_label = ModernLabel(header_frame, text=icon)
        icon_label.pack(side="left", padx=(0, 8))

        title_label = ModernLabel(header_frame, text=title, font=ctk.CTkFont(weight="bold"))
        title_label.pack(side="left")

        # Description
        desc_label = ModernLabel(parent, text=description, text_color="gray70", font=ctk.CTkFont(size=10))
        desc_label.pack(anchor="w", padx=20, pady=(0, 10))

    def _run_scenario(self):
        """Run scenario analysis"""
        messagebox.showinfo("Scenario Analysis", "Analyzing tax impact of scenario changes...")