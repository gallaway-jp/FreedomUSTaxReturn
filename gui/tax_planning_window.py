"""
Tax Planning Window - GUI for advanced tax planning tools

Provides interface for:
- What-if scenario analysis
- Tax projections
- Estimated tax calculators
- Withholding optimization
- Retirement planning
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
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


class TaxPlanningWindow:
    """
    Main window for tax planning tools and analysis.
    """

    def __init__(self, parent: tk.Tk, tax_data: Any):
        """
        Initialize tax planning window.

        Args:
            parent: Parent tkinter window
            tax_data: Current tax data object
        """
        self.parent = parent
        self.tax_data = tax_data
        self.planning_service = TaxPlanningService()

        # Create main window
        self.window = tk.Toplevel(parent)
        self.window.title("Tax Planning Tools - Freedom US Tax Return")
        self.window.geometry("1000x700")
        self.window.resizable(True, True)

        # Create notebook for different planning tools
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self._create_scenario_tab()
        self._create_projection_tab()
        self._create_estimated_tax_tab()
        self._create_withholding_tab()
        self._create_retirement_tab()

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.window, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _create_scenario_tab(self):
        """Create what-if scenario analysis tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="What-If Scenarios")

        # Title
        title_label = ttk.Label(frame, text="What-If Scenario Analysis",
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=10)

        # Description
        desc_text = ("Analyze how changes to your tax situation affect your tax liability.\n"
                    "Enter changes below and click 'Run Scenario' to see the impact.")
        desc_label = ttk.Label(frame, text=desc_text, justify=tk.CENTER)
        desc_label.pack(pady=5)

        # Scenario input frame
        input_frame = ttk.LabelFrame(frame, text="Scenario Changes", padding=10)
        input_frame.pack(fill=tk.X, padx=20, pady=10)

        # Create input fields for common changes
        self.scenario_vars = {}

        # Income changes
        income_frame = ttk.Frame(input_frame)
        income_frame.pack(fill=tk.X, pady=2)
        ttk.Label(income_frame, text="Additional W-2 Income:").pack(side=tk.LEFT)
        self.scenario_vars['income_w2'] = tk.DoubleVar()
        ttk.Entry(income_frame, textvariable=self.scenario_vars['income_w2'], width=15).pack(side=tk.RIGHT)

        # Business income changes
        business_frame = ttk.Frame(input_frame)
        business_frame.pack(fill=tk.X, pady=2)
        ttk.Label(business_frame, text="Additional Business Income:").pack(side=tk.LEFT)
        self.scenario_vars['income_business'] = tk.DoubleVar()
        ttk.Entry(business_frame, textvariable=self.scenario_vars['income_business'], width=15).pack(side=tk.RIGHT)

        # Deduction changes
        deduction_frame = ttk.Frame(input_frame)
        deduction_frame.pack(fill=tk.X, pady=2)
        ttk.Label(deduction_frame, text="Additional Itemized Deductions:").pack(side=tk.LEFT)
        self.scenario_vars['deductions_itemized'] = tk.DoubleVar()
        ttk.Entry(deduction_frame, textvariable=self.scenario_vars['deductions_itemized'], width=15).pack(side=tk.RIGHT)

        # Filing status change
        status_frame = ttk.Frame(input_frame)
        status_frame.pack(fill=tk.X, pady=2)
        ttk.Label(status_frame, text="Change Filing Status to:").pack(side=tk.LEFT)
        self.scenario_vars['filing_status'] = tk.StringVar()
        status_combo = ttk.Combobox(status_frame, textvariable=self.scenario_vars['filing_status'],
                                   values=["", "Single", "Married Filing Jointly", "Head of Household"],
                                   state="readonly", width=20)
        status_combo.pack(side=tk.RIGHT)

        # Run scenario button
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Run Scenario", command=self._run_scenario).pack()

        # Results display
        results_frame = ttk.LabelFrame(frame, text="Scenario Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.scenario_results_text = scrolledtext.ScrolledText(results_frame, height=15, wrap=tk.WORD)
        self.scenario_results_text.pack(fill=tk.BOTH, expand=True)

    def _create_projection_tab(self):
        """Create tax projection tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Tax Projections")

        # Title
        title_label = ttk.Label(frame, text="Tax Projections",
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=10)

        # Input frame
        input_frame = ttk.LabelFrame(frame, text="Projection Parameters", padding=10)
        input_frame.pack(fill=tk.X, padx=20, pady=10)

        # Projection year
        year_frame = ttk.Frame(input_frame)
        year_frame.pack(fill=tk.X, pady=2)
        ttk.Label(year_frame, text="Projection Year:").pack(side=tk.LEFT)
        self.projection_year_var = tk.IntVar(value=2026)
        ttk.Entry(year_frame, textvariable=self.projection_year_var, width=10).pack(side=tk.RIGHT)

        # Growth rates
        growth_frame = ttk.Frame(input_frame)
        growth_frame.pack(fill=tk.X, pady=2)
        ttk.Label(growth_frame, text="Expected Income Growth Rate (%):").pack(side=tk.LEFT)
        self.income_growth_var = tk.DoubleVar(value=3.0)
        ttk.Entry(growth_frame, textvariable=self.income_growth_var, width=10).pack(side=tk.RIGHT)

        inflation_frame = ttk.Frame(input_frame)
        inflation_frame.pack(fill=tk.X, pady=2)
        ttk.Label(inflation_frame, text="Expected Inflation Rate (%):").pack(side=tk.LEFT)
        self.inflation_var = tk.DoubleVar(value=2.5)
        ttk.Entry(inflation_frame, textvariable=self.inflation_var, width=10).pack(side=tk.RIGHT)

        # Run projection button
        ttk.Button(input_frame, text="Generate Projection", command=self._run_projection).pack(pady=10)

        # Results display
        results_frame = ttk.LabelFrame(frame, text="Projection Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.projection_results_text = scrolledtext.ScrolledText(results_frame, height=15, wrap=tk.WORD)
        self.projection_results_text.pack(fill=tk.BOTH, expand=True)

    def _create_estimated_tax_tab(self):
        """Create estimated tax payment calculator tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Estimated Tax Payments")

        # Title
        title_label = ttk.Label(frame, text="Quarterly Estimated Tax Calculator",
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=10)

        # Input frame
        input_frame = ttk.LabelFrame(frame, text="Income Projection", padding=10)
        input_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(input_frame, text="Expected Annual Income for 2025:").pack(anchor=tk.W)
        self.annual_income_var = tk.DoubleVar()
        ttk.Entry(input_frame, textvariable=self.annual_income_var, width=20).pack(pady=5)

        ttk.Button(input_frame, text="Calculate Payments", command=self._calculate_estimated_tax).pack(pady=10)

        # Results display
        results_frame = ttk.LabelFrame(frame, text="Quarterly Payment Schedule", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.estimated_tax_results_text = scrolledtext.ScrolledText(results_frame, height=15, wrap=tk.WORD)
        self.estimated_tax_results_text.pack(fill=tk.BOTH, expand=True)

    def _create_withholding_tab(self):
        """Create withholding calculator tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Withholding Calculator")

        # Title
        title_label = ttk.Label(frame, text="W-4 Withholding Calculator",
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=10)

        # Input frame
        input_frame = ttk.LabelFrame(frame, text="Income Information", padding=10)
        input_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(input_frame, text="Expected Annual Income:").pack(anchor=tk.W)
        self.withholding_income_var = tk.DoubleVar()
        ttk.Entry(input_frame, textvariable=self.withholding_income_var, width=20).pack(pady=5)

        ttk.Button(input_frame, text="Calculate Withholding", command=self._calculate_withholding).pack(pady=10)

        # Results display
        results_frame = ttk.LabelFrame(frame, text="Withholding Recommendations", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.withholding_results_text = scrolledtext.ScrolledText(results_frame, height=15, wrap=tk.WORD)
        self.withholding_results_text.pack(fill=tk.BOTH, expand=True)

    def _create_retirement_tab(self):
        """Create retirement planning tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Retirement Planning")

        # Title
        title_label = ttk.Label(frame, text="Retirement Contribution Optimizer",
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=10)

        # Input frame
        input_frame = ttk.LabelFrame(frame, text="Current Information", padding=10)
        input_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(input_frame, text="Current Annual Income:").pack(anchor=tk.W)
        self.retirement_income_var = tk.DoubleVar()
        ttk.Entry(input_frame, textvariable=self.retirement_income_var, width=20).pack(pady=5)

        ttk.Label(input_frame, text="Employer 401(k) Match (%):").pack(anchor=tk.W)
        self.employer_match_var = tk.DoubleVar(value=0.0)
        ttk.Entry(input_frame, textvariable=self.employer_match_var, width=20).pack(pady=5)

        ttk.Button(input_frame, text="Optimize Contributions", command=self._optimize_retirement).pack(pady=10)

        # Results display
        results_frame = ttk.LabelFrame(frame, text="Optimization Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.retirement_results_text = scrolledtext.ScrolledText(results_frame, height=15, wrap=tk.WORD)
        self.retirement_results_text.pack(fill=tk.BOTH, expand=True)

    def _run_scenario(self):
        """Run what-if scenario analysis."""
        try:
            # Build scenario changes
            changes = {}

            # Income changes
            if self.scenario_vars['income_w2'].get() != 0:
                changes.setdefault('income', {}).setdefault('w2_forms', [{}])
                if 'wages' not in changes['income']['w2_forms'][0]:
                    changes['income']['w2_forms'][0]['wages'] = 0
                changes['income']['w2_forms'][0]['wages'] += self.scenario_vars['income_w2'].get()

            if self.scenario_vars['income_business'].get() != 0:
                changes.setdefault('income', {}).setdefault('business_income', 0)
                changes['income']['business_income'] += self.scenario_vars['income_business'].get()

            # Deduction changes
            if self.scenario_vars['deductions_itemized'].get() != 0:
                changes.setdefault('deductions', {}).setdefault('itemized', 0)
                changes['deductions']['itemized'] += self.scenario_vars['deductions_itemized'].get()

            # Filing status change
            if self.scenario_vars['filing_status'].get():
                changes.setdefault('filing_status', {})
                changes['filing_status']['status'] = self.scenario_vars['filing_status'].get()

            if not changes:
                messagebox.showwarning("No Changes", "Please enter at least one scenario change.")
                return

            # Run scenario
            result = self.planning_service.analyze_scenario(self.tax_data, changes)

            # Display results
            self.scenario_results_text.delete(1.0, tk.END)
            self.scenario_results_text.insert(tk.END, f"Scenario Analysis Results\n")
            self.scenario_results_text.insert(tk.END, f"{'='*50}\n\n")
            self.scenario_results_text.insert(tk.END, f"Original Tax: ${result.original_tax:,.2f}\n")
            self.scenario_results_text.insert(tk.END, f"New Tax: ${result.new_tax:,.2f}\n")
            self.scenario_results_text.insert(tk.END, f"Tax Difference: ${result.tax_difference:,.2f}\n")
            self.scenario_results_text.insert(tk.END, f"Effective Rate Change: {result.effective_rate_change:.2%}\n\n")
            self.scenario_results_text.insert(tk.END, f"Key Changes Applied:\n")
            for key, value in result.key_changes.items():
                self.scenario_results_text.insert(tk.END, f"  {key}: {value}\n")

            self.status_var.set("Scenario analysis completed")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to run scenario: {str(e)}")
            self.status_var.set("Error running scenario")

    def _run_projection(self):
        """Generate tax projection."""
        try:
            projection_year = self.projection_year_var.get()
            income_growth = self.income_growth_var.get() / 100
            inflation_rate = self.inflation_var.get() / 100

            if projection_year <= 2025:
                messagebox.showwarning("Invalid Year", "Projection year must be greater than 2025.")
                return

            # Generate projection
            projection = self.planning_service.project_future_tax(
                self.tax_data, projection_year, income_growth, inflation_rate
            )

            # Display results
            self.projection_results_text.delete(1.0, tk.END)
            self.projection_results_text.insert(tk.END, f"Tax Projection for {projection.projection_year}\n")
            self.projection_results_text.insert(tk.END, f"{'='*50}\n\n")
            self.projection_results_text.insert(tk.END, f"Projected Income: ${projection.projected_income:,.2f}\n")
            self.projection_results_text.insert(tk.END, f"Projected Deductions: ${projection.projected_deductions:,.2f}\n")
            self.projection_results_text.insert(tk.END, f"Projected Taxable Income: ${projection.projected_taxable_income:,.2f}\n")
            self.projection_results_text.insert(tk.END, f"Projected Tax: ${projection.projected_tax:,.2f}\n")
            self.projection_results_text.insert(tk.END, f"Confidence Level: {projection.confidence_level.title()}\n\n")
            self.projection_results_text.insert(tk.END, f"Assumptions:\n")
            for key, value in projection.assumptions.items():
                if 'rate' in key:
                    self.projection_results_text.insert(tk.END, f"  {key}: {value:.1%}\n")
                else:
                    self.projection_results_text.insert(tk.END, f"  {key}: ${value:,.2f}\n")

            self.status_var.set("Tax projection completed")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate projection: {str(e)}")
            self.status_var.set("Error generating projection")

    def _calculate_estimated_tax(self):
        """Calculate estimated tax payments."""
        try:
            annual_income = self.annual_income_var.get()

            if annual_income <= 0:
                messagebox.showwarning("Invalid Income", "Please enter a valid annual income.")
                return

            # Calculate payments
            payments = self.planning_service.calculate_estimated_tax_payments(self.tax_data, annual_income)

            # Display results
            self.estimated_tax_results_text.delete(1.0, tk.END)
            self.estimated_tax_results_text.insert(tk.END, f"Quarterly Estimated Tax Payments for 2025\n")
            self.estimated_tax_results_text.insert(tk.END, f"{'='*60}\n\n")
            self.estimated_tax_results_text.insert(tk.END, f"Based on projected annual income: ${annual_income:,.2f}\n\n")

            total_payments = 0
            for payment in payments:
                self.estimated_tax_results_text.insert(tk.END, f"Quarter {payment.quarter} ({payment.due_date.strftime('%B %d')}):\n")
                self.estimated_tax_results_text.insert(tk.END, f"  Safe Harbor Amount: ${payment.safe_harbor_amount:,.2f}\n")
                self.estimated_tax_results_text.insert(tk.END, f"  Annualized Income Method: ${payment.annualized_income_method:,.2f}\n")
                self.estimated_tax_results_text.insert(tk.END, f"  Recommended Payment: ${payment.payment_amount:,.2f}\n")
                self.estimated_tax_results_text.insert(tk.END, f"  Reasoning: {payment.reasoning}\n\n")
                total_payments += payment.payment_amount

            self.estimated_tax_results_text.insert(tk.END, f"Total Annual Estimated Payments: ${total_payments:,.2f}\n")

            self.status_var.set("Estimated tax calculation completed")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate estimated tax: {str(e)}")
            self.status_var.set("Error calculating estimated tax")

    def _calculate_withholding(self):
        """Calculate withholding recommendations."""
        try:
            expected_income = self.withholding_income_var.get()

            if expected_income <= 0:
                messagebox.showwarning("Invalid Income", "Please enter a valid expected income.")
                return

            # Calculate withholding recommendation
            recommendation = self.planning_service.calculate_withholding_recommendation(self.tax_data, expected_income)

            # Display results
            self.withholding_results_text.delete(1.0, tk.END)
            self.withholding_results_text.insert(tk.END, f"W-4 Withholding Recommendation\n")
            self.withholding_results_text.insert(tk.END, f"{'='*40}\n\n")
            self.withholding_results_text.insert(tk.END, f"Current Annual Withholding: ${recommendation.current_withholding:,.2f}\n")
            self.withholding_results_text.insert(tk.END, f"Recommended Annual Withholding: ${recommendation.recommended_withholding:,.2f}\n")
            self.withholding_results_text.insert(tk.END, f"Adjustment Needed: ${recommendation.adjustment_needed:,.2f} per pay period\n")
            self.withholding_results_text.insert(tk.END, f"Expected Annual Tax: ${recommendation.expected_annual_tax:,.2f}\n")
            self.withholding_results_text.insert(tk.END, f"Expected Annual Refund/Owed: ${recommendation.expected_annual_refund:,.2f}\n\n")

            if recommendation.w4_adjustments:
                self.withholding_results_text.insert(tk.END, f"W-4 Adjustments Needed:\n")
                for key, value in recommendation.w4_adjustments.items():
                    self.withholding_results_text.insert(tk.END, f"  {key}: {value}\n")

            self.withholding_results_text.insert(tk.END, f"\nReasoning: {recommendation.reasoning}\n")

            self.status_var.set("Withholding calculation completed")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate withholding: {str(e)}")
            self.status_var.set("Error calculating withholding")

    def _optimize_retirement(self):
        """Optimize retirement contributions."""
        try:
            current_income = self.retirement_income_var.get()
            employer_match = self.employer_match_var.get() / 100

            if current_income <= 0:
                messagebox.showwarning("Invalid Income", "Please enter a valid current income.")
                return

            # Optimize retirement contributions
            optimization = self.planning_service.optimize_retirement_contributions(
                self.tax_data, current_income, employer_match
            )

            # Display results
            self.retirement_results_text.delete(1.0, tk.END)
            self.retirement_results_text.insert(tk.END, f"Retirement Contribution Optimization\n")
            self.retirement_results_text.insert(tk.END, f"{'='*45}\n\n")
            self.retirement_results_text.insert(tk.END, f"Contribution Limits:\n")
            self.retirement_results_text.insert(tk.END, f"  Traditional IRA: ${optimization.traditional_ira_limit:,.0f}\n")
            self.retirement_results_text.insert(tk.END, f"  Roth IRA: ${optimization.roth_ira_limit:,.0f}\n")
            self.retirement_results_text.insert(tk.END, f"  401(k): ${optimization.employer_401k_limit:,.0f}\n\n")
            self.retirement_results_text.insert(tk.END, f"Recommended Contributions:\n")
            self.retirement_results_text.insert(tk.END, f"  Traditional IRA: ${optimization.recommended_traditional:,.0f}\n")
            self.retirement_results_text.insert(tk.END, f"  Roth IRA: ${optimization.recommended_roth:,.0f}\n")
            self.retirement_results_text.insert(tk.END, f"  401(k): ${optimization.recommended_401k:,.0f}\n\n")
            self.retirement_results_text.insert(tk.END, f"Tax Savings: ${optimization.tax_savings:,.0f}\n")
            self.retirement_results_text.insert(tk.END, f"Net Benefit: ${optimization.net_benefit:,.0f}\n\n")
            self.retirement_results_text.insert(tk.END, f"Strategy: {optimization.strategy}\n\n")
            self.retirement_results_text.insert(tk.END, f"Reasoning:\n")
            for reason in optimization.reasoning:
                self.retirement_results_text.insert(tk.END, f"  • {reason}\n")

            self.status_var.set("Retirement optimization completed")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to optimize retirement: {str(e)}")
            self.status_var.set("Error optimizing retirement")


def open_tax_planning_window(parent: tk.Tk, tax_data: Any):
    """
    Open the tax planning window.

    Args:
        parent: Parent tkinter window
        tax_data: Current tax data
    """
    TaxPlanningWindow(parent, tax_data)