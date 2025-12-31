"""
Tax Analytics Window - GUI for displaying tax analytics and insights

Provides a comprehensive interface for viewing tax analytics including
effective tax rates, tax burden analysis, trends, and optimization insights.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import threading
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.tax_analytics_service import TaxAnalyticsService, TaxAnalyticsResult, TaxTrendAnalysis
from services.tax_calculation_service import TaxCalculationService
from utils.error_tracker import get_error_tracker


class TaxAnalyticsWindow:
    """
    Window for displaying comprehensive tax analytics and insights.

    Features:
    - Effective tax rate visualization
    - Tax burden breakdown
    - Multi-year trend analysis
    - Deduction and credit utilization
    - Optimization recommendations
    """

    def __init__(self, parent: tk.Tk, config: AppConfig, tax_data: Optional[TaxData] = None,
                 tax_returns: Optional[List[TaxData]] = None):
        """
        Initialize tax analytics window.

        Args:
            parent: Parent window
            config: Application configuration
            tax_data: Single tax return to analyze (optional)
            tax_returns: Multiple tax returns for trend analysis (optional)
        """
        self.parent = parent
        self.config = config
        self.tax_data = tax_data
        self.tax_returns = tax_returns or []
        self.error_tracker = get_error_tracker()

        # Initialize services
        self.tax_calculation = TaxCalculationService(config)
        self.analytics_service = TaxAnalyticsService(config, self.tax_calculation)

        # Current analysis results
        self.current_analysis: Optional[TaxAnalyticsResult] = None
        self.trend_analysis: Optional[TaxTrendAnalysis] = None

        # UI components
        self.window: Optional[tk.Toplevel] = None
        self.notebook: Optional[ttk.Notebook] = None
        self.progress_var: Optional[tk.DoubleVar] = None
        self.status_label: Optional[ttk.Label] = None

        # Matplotlib figures
        self.rate_chart: Optional[Figure] = None
        self.burden_chart: Optional[Figure] = None
        self.trend_chart: Optional[Figure] = None

        self._create_window()
        self._setup_ui()
        self._load_initial_data()

    def _create_window(self):
        """Create the main analytics window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Tax Analytics & Insights")
        self.window.geometry("1200x800")
        self.window.resizable(True, True)

        # Set window icon if available
        try:
            self.window.iconbitmap("assets/icon.ico")
        except:
            pass

        # Center window
        self.window.transient(self.parent)
        self.window.grab_set()

    def _setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        # Analysis buttons
        ttk.Button(toolbar, text="Run Analysis", command=self._run_analysis).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Export Report", command=self._export_report).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Save Charts", command=self._save_charts).pack(side=tk.LEFT, padx=(0, 10))

        # Progress bar
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(toolbar, variable=self.progress_var, maximum=100)
        progress_bar.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))

        # Status label
        self.status_label = ttk.Label(toolbar, text="Ready")
        self.status_label.pack(side=tk.RIGHT, padx=(10, 0))

        # Notebook for different analysis views
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs
        self._create_overview_tab()
        self._create_rates_tab()
        self._create_burden_tab()
        self._create_trends_tab()
        self._create_insights_tab()

    def _create_overview_tab(self):
        """Create the overview tab with key metrics"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Overview")

        # Key metrics frame
        metrics_frame = ttk.LabelFrame(tab, text="Key Tax Metrics", padding=10)
        metrics_frame.pack(fill=tk.X, pady=(0, 10))

        # Create metric labels (will be populated with data)
        self.overview_labels = {}
        metrics = [
            ("Effective Tax Rate", "effective_rate"),
            ("Marginal Tax Rate", "marginal_rate"),
            ("Tax Burden %", "burden_pct"),
            ("Deduction Utilization", "deduction_util"),
            ("Credit Utilization", "credit_util")
        ]

        for i, (label_text, key) in enumerate(metrics):
            row = i // 3
            col = i % 3

            frame = ttk.Frame(metrics_frame)
            frame.grid(row=row, column=col, padx=10, pady=5, sticky="ew")

            ttk.Label(frame, text=f"{label_text}:").pack(anchor="w")
            value_label = ttk.Label(frame, text="--", font=("Arial", 12, "bold"))
            value_label.pack(anchor="w")
            self.overview_labels[key] = value_label

        metrics_frame.columnconfigure(0, weight=1)
        metrics_frame.columnconfigure(1, weight=1)
        metrics_frame.columnconfigure(2, weight=1)

        # Summary text area
        summary_frame = ttk.LabelFrame(tab, text="Tax Summary", padding=10)
        summary_frame.pack(fill=tk.BOTH, expand=True)

        self.summary_text = tk.Text(summary_frame, wrap=tk.WORD, height=10)
        scrollbar = ttk.Scrollbar(summary_frame, command=self.summary_text.yview)
        self.summary_text.config(yscrollcommand=scrollbar.set)

        self.summary_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_rates_tab(self):
        """Create the tax rates visualization tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Tax Rates")

        # Chart frame
        chart_frame = ttk.LabelFrame(tab, text="Tax Rate Analysis", padding=10)
        chart_frame.pack(fill=tk.BOTH, expand=True)

        # Placeholder for matplotlib chart
        self.rate_canvas_frame = ttk.Frame(chart_frame)
        self.rate_canvas_frame.pack(fill=tk.BOTH, expand=True)

        # Rate details
        details_frame = ttk.LabelFrame(tab, text="Rate Details", padding=10)
        details_frame.pack(fill=tk.X, pady=(10, 0))

        self.rate_details_text = tk.Text(details_frame, wrap=tk.WORD, height=6)
        scrollbar = ttk.Scrollbar(details_frame, command=self.rate_details_text.yview)
        self.rate_details_text.config(yscrollcommand=scrollbar.set)

        self.rate_details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_burden_tab(self):
        """Create the tax burden analysis tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Tax Burden")

        # Chart frame
        chart_frame = ttk.LabelFrame(tab, text="Tax Burden Breakdown", padding=10)
        chart_frame.pack(fill=tk.BOTH, expand=True)

        self.burden_canvas_frame = ttk.Frame(chart_frame)
        self.burden_canvas_frame.pack(fill=tk.BOTH, expand=True)

        # Burden analysis
        analysis_frame = ttk.LabelFrame(tab, text="Burden Analysis", padding=10)
        analysis_frame.pack(fill=tk.X, pady=(10, 0))

        self.burden_analysis_text = tk.Text(analysis_frame, wrap=tk.WORD, height=8)
        scrollbar = ttk.Scrollbar(analysis_frame, command=self.burden_analysis_text.yview)
        self.burden_analysis_text.config(yscrollcommand=scrollbar.set)

        self.burden_analysis_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_trends_tab(self):
        """Create the multi-year trends tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Trends")

        # Chart frame
        chart_frame = ttk.LabelFrame(tab, text="Multi-Year Trends", padding=10)
        chart_frame.pack(fill=tk.BOTH, expand=True)

        self.trend_canvas_frame = ttk.Frame(chart_frame)
        self.trend_canvas_frame.pack(fill=tk.BOTH, expand=True)

        # Trend metrics
        metrics_frame = ttk.LabelFrame(tab, text="Trend Metrics", padding=10)
        metrics_frame.pack(fill=tk.X, pady=(10, 0))

        self.trend_labels = {}
        trend_metrics = [
            ("Income Growth Rate", "income_growth"),
            ("Tax Liability Growth Rate", "tax_growth"),
            ("Analysis Period", "period")
        ]

        for i, (label_text, key) in enumerate(trend_metrics):
            frame = ttk.Frame(metrics_frame)
            frame.pack(fill=tk.X, pady=2)

            ttk.Label(frame, text=f"{label_text}:").pack(side=tk.LEFT)
            value_label = ttk.Label(frame, text="--", font=("Arial", 10, "bold"))
            value_label.pack(side=tk.RIGHT)
            self.trend_labels[key] = value_label

    def _create_insights_tab(self):
        """Create the insights and recommendations tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Insights")

        # Insights text area
        insights_frame = ttk.LabelFrame(tab, text="Tax Optimization Insights", padding=10)
        insights_frame.pack(fill=tk.BOTH, expand=True)

        self.insights_text = tk.Text(insights_frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(insights_frame, command=self.insights_text.yview)
        self.insights_text.config(yscrollcommand=scrollbar.set)

        self.insights_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Action items
        actions_frame = ttk.LabelFrame(tab, text="Recommended Actions", padding=10)
        actions_frame.pack(fill=tk.X, pady=(10, 0))

        self.actions_text = tk.Text(actions_frame, wrap=tk.WORD, height=6)
        scrollbar2 = ttk.Scrollbar(actions_frame, command=self.actions_text.yview)
        self.actions_text.config(yscrollcommand=scrollbar2.set)

        self.actions_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)

    def _load_initial_data(self):
        """Load initial data and run analysis if tax data is available"""
        if self.tax_data:
            self._run_analysis()
        elif self.tax_returns:
            self._run_trend_analysis()

    def _run_analysis(self):
        """Run tax analysis in background thread"""
        if not self.tax_data:
            messagebox.showwarning("No Data", "No tax data available for analysis.")
            return

        def analysis_worker():
            try:
                self._update_status("Running tax analysis...")
                self.progress_var.set(25)

                # Generate comprehensive analysis
                self.current_analysis = self.analytics_service.generate_comprehensive_analysis(self.tax_data)

                self.progress_var.set(75)

                # Update UI
                self.window.after(0, self._update_analysis_display)

                self.progress_var.set(100)
                self._update_status("Analysis complete")

            except Exception as e:
                self.error_tracker.track_error(error=e, context={"operation": "_run_analysis"})
                self.window.after(0, lambda: messagebox.showerror("Analysis Error", f"Failed to run analysis: {str(e)}"))
                self._update_status("Analysis failed")

        # Run in background thread
        threading.Thread(target=analysis_worker, daemon=True).start()

    def _run_trend_analysis(self):
        """Run trend analysis for multiple years"""
        if not self.tax_returns:
            messagebox.showwarning("No Data", "No tax returns available for trend analysis.")
            return

        def trend_worker():
            try:
                self._update_status("Analyzing tax trends...")
                self.progress_var.set(25)

                # Generate trend analysis
                self.trend_analysis = self.analytics_service.analyze_tax_trends(self.tax_returns)

                self.progress_var.set(75)

                # Update UI
                self.window.after(0, self._update_trend_display)

                self.progress_var.set(100)
                self._update_status("Trend analysis complete")

            except Exception as e:
                self.error_tracker.track_error(error=e, context={"operation": "_run_trend_analysis"})
                self.window.after(0, lambda: messagebox.showerror("Trend Analysis Error", f"Failed to analyze trends: {str(e)}"))
                self._update_status("Trend analysis failed")

        # Run in background thread
        threading.Thread(target=trend_worker, daemon=True).start()

    def _update_analysis_display(self):
        """Update the UI with analysis results"""
        if not self.current_analysis:
            return

        # Update overview metrics
        self.overview_labels['effective_rate'].config(text=f"{self.current_analysis.effective_tax_rate:.1f}%")
        self.overview_labels['marginal_rate'].config(text=f"{self.current_analysis.marginal_tax_rate:.1f}%")
        self.overview_labels['burden_pct'].config(text=f"{self.current_analysis.tax_burden_percentage:.1f}%")
        self.overview_labels['deduction_util'].config(text=f"{self.current_analysis.deduction_utilization:.1f}%")
        self.overview_labels['credit_util'].config(text=f"{self.current_analysis.credit_utilization:.1f}%")

        # Update summary
        self._update_summary_text()

        # Create charts
        self._create_rate_chart()
        self._create_burden_chart()

        # Update insights
        self._update_insights()

    def _update_trend_display(self):
        """Update the UI with trend analysis results"""
        if not self.trend_analysis:
            return

        # Update trend metrics
        self.trend_labels['income_growth'].config(text=f"{self.trend_analysis.income_growth_rate:.1f}%")
        self.trend_labels['tax_growth'].config(text=f"{self.trend_analysis.tax_liability_growth_rate:.1f}%")
        self.trend_labels['period'].config(text=self.trend_analysis.analysis_period)

        # Create trend chart
        self._create_trend_chart()

    def _update_summary_text(self):
        """Update the summary text area"""
        if not self.current_analysis:
            return

        summary = f"""
Tax Year: {self.current_analysis.tax_year}

Effective Tax Rate: {self.current_analysis.effective_tax_rate:.1f}%
This represents the percentage of your total income that goes to taxes.

Marginal Tax Rate: {self.current_analysis.marginal_tax_rate:.1f}%
This is the tax rate on your last dollar of income.

Tax Burden: {self.current_analysis.tax_burden_percentage:.1f}%
This shows your overall tax burden as a percentage of income.

Analysis generated on: {self.current_analysis.calculated_at.strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, summary.strip())

    def _create_rate_chart(self):
        """Create the tax rates visualization chart"""
        if not self.current_analysis:
            return

        # Clear previous chart
        for widget in self.rate_canvas_frame.winfo_children():
            widget.destroy()

        # Create figure
        fig, ax = plt.subplots(figsize=(8, 6))
        fig.patch.set_facecolor('#f0f0f0')

        rates = [self.current_analysis.effective_tax_rate, self.current_analysis.marginal_tax_rate]
        labels = ['Effective Rate', 'Marginal Rate']
        colors = ['#4CAF50', '#FF9800']

        bars = ax.bar(labels, rates, color=colors, alpha=0.7)
        ax.set_ylabel('Tax Rate (%)')
        ax.set_title('Tax Rate Comparison')
        ax.grid(True, alpha=0.3)

        # Add value labels on bars
        for bar, rate in zip(bars, rates):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                   f'{rate:.1f}%', ha='center', va='bottom', fontweight='bold')

        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.rate_canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.rate_chart = fig

        # Update rate details
        details = f"""
Effective Tax Rate ({self.current_analysis.effective_tax_rate:.1f}%):
The actual percentage of your total income paid in taxes.

Marginal Tax Rate ({self.current_analysis.marginal_tax_rate:.1f}%):
The tax rate applied to your highest income bracket.

Difference: {abs(self.current_analysis.effective_tax_rate - self.current_analysis.marginal_tax_rate):.1f}%
This difference shows the benefit of progressive taxation.
"""
        self.rate_details_text.delete(1.0, tk.END)
        self.rate_details_text.insert(tk.END, details.strip())

    def _create_burden_chart(self):
        """Create the tax burden breakdown chart"""
        if not self.current_analysis:
            return

        # Clear previous chart
        for widget in self.burden_canvas_frame.winfo_children():
            widget.destroy()

        # Create pie chart
        fig, ax = plt.subplots(figsize=(8, 6))
        fig.patch.set_facecolor('#f0f0f0')

        breakdown = self.current_analysis.tax_liability_breakdown
        if breakdown:
            # Filter out zero values
            filtered_breakdown = {k: v for k, v in breakdown.items() if v > 0}

            if filtered_breakdown:
                labels = list(filtered_breakdown.keys())
                sizes = list(filtered_breakdown.values())
                colors = plt.cm.Set3(range(len(labels)))

                wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                                 startangle=90, wedgeprops={'edgecolor': 'white', 'linewidth': 2})
                ax.set_title('Tax Liability Breakdown')
                ax.axis('equal')

                # Improve label formatting
                for text in texts:
                    text.set_fontsize(9)
                for autotext in autotexts:
                    autotext.set_fontsize(8)
                    autotext.set_fontweight('bold')
            else:
                ax.text(0.5, 0.5, 'No tax liability breakdown available',
                       ha='center', va='center', transform=ax.transAxes, fontsize=12)
                ax.set_title('Tax Liability Breakdown')
        else:
            ax.text(0.5, 0.5, 'No tax liability data available',
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title('Tax Liability Breakdown')

        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.burden_canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.burden_chart = fig

        # Update burden analysis
        if breakdown:
            total_tax = sum(breakdown.values())
            analysis = f"""
Total Tax Liability: ${total_tax:,.2f}

Breakdown by Tax Type:
"""

            for tax_type, amount in breakdown.items():
                if amount > 0:
                    percentage = (amount / total_tax) * 100 if total_tax > 0 else 0
                    analysis += f"• {tax_type.replace('_', ' ').title()}: ${amount:,.2f} ({percentage:.1f}%)\n"

            analysis += f"\nTax Burden Percentage: {self.current_analysis.tax_burden_percentage:.1f}% of total income"
        else:
            analysis = "No tax burden data available for analysis."

        self.burden_analysis_text.delete(1.0, tk.END)
        self.burden_analysis_text.insert(tk.END, analysis.strip())

    def _create_trend_chart(self):
        """Create the multi-year trend chart"""
        if not self.trend_analysis:
            return

        # Clear previous chart
        for widget in self.trend_canvas_frame.winfo_children():
            widget.destroy()

        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        fig.patch.set_facecolor('#f0f0f0')

        years = self.trend_analysis.years_analyzed

        # Effective rate trend
        ax1.plot(years, self.trend_analysis.effective_rate_trend, 'o-', color='#4CAF50',
                linewidth=2, markersize=6, label='Effective Rate')
        ax1.set_ylabel('Effective Tax Rate (%)')
        ax1.set_title('Tax Rate Trends Over Time')
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        # Tax burden trend
        ax2.plot(years, self.trend_analysis.tax_burden_trend, 's-', color='#FF9800',
                linewidth=2, markersize=6, label='Tax Burden')
        ax2.set_xlabel('Tax Year')
        ax2.set_ylabel('Tax Burden (%)')
        ax2.set_title('Tax Burden Trends Over Time')
        ax2.grid(True, alpha=0.3)
        ax2.legend()

        plt.tight_layout()

        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.trend_canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.trend_chart = fig

    def _update_insights(self):
        """Update the insights and recommendations"""
        if not self.current_analysis:
            return

        insights = """
TAX OPTIMIZATION INSIGHTS

Based on your tax analysis, here are key insights and recommendations:

1. TAX RATE ANALYSIS:
"""

        # Rate insights
        if self.current_analysis.effective_tax_rate < 10:
            insights += "• Your effective tax rate is relatively low. Consider maximizing retirement contributions.\n"
        elif self.current_analysis.effective_tax_rate > 25:
            insights += "• Your effective tax rate is high. Review tax planning strategies to reduce future burden.\n"

        # Burden insights
        insights += "\n2. TAX BURDEN ANALYSIS:\n"
        if self.current_analysis.tax_burden_percentage < 15:
            insights += "• Your tax burden is moderate. Good job on tax efficiency.\n"
        elif self.current_analysis.tax_burden_percentage > 25:
            insights += "• Your tax burden is high. Consider tax-loss harvesting or increased deductions.\n"

        # Deduction insights
        insights += "\n3. DEDUCTION UTILIZATION:\n"
        if self.current_analysis.deduction_utilization < 50:
            insights += "• Low deduction utilization. Review eligibility for additional deductions.\n"
        elif self.current_analysis.deduction_utilization > 80:
            insights += "• High deduction utilization. Your deductions are working effectively.\n"

        # Credit insights
        insights += "\n4. CREDIT UTILIZATION:\n"
        if self.current_analysis.credit_utilization < 30:
            insights += "• Low credit utilization. Check eligibility for tax credits (EITC, education, energy).\n"
        elif self.current_analysis.credit_utilization > 70:
            insights += "• High credit utilization. You're maximizing available tax credits.\n"

        self.insights_text.delete(1.0, tk.END)
        self.insights_text.insert(tk.END, insights.strip())

        # Action items
        actions = """
RECOMMENDED ACTIONS:

1. Review your withholding to avoid large refunds or bills
2. Consider increasing retirement contributions for tax benefits
3. Keep detailed records of all deductible expenses
4. Review eligibility for tax credits annually
5. Consider consulting a tax professional for personalized advice
6. Plan major purchases around tax year boundaries
7. Review investment choices for tax efficiency
"""
        self.actions_text.delete(1.0, tk.END)
        self.actions_text.insert(tk.END, actions.strip())

    def _export_report(self):
        """Export analysis report to file"""
        if not self.current_analysis:
            messagebox.showwarning("No Data", "No analysis data available to export.")
            return

        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Export Tax Analysis Report"
            )

            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("TAX ANALYSIS REPORT\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"Tax Year: {self.current_analysis.tax_year}\n")
                    f.write(f"Analysis Date: {self.current_analysis.calculated_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                    f.write("KEY METRICS:\n")
                    f.write(f"Effective Tax Rate: {self.current_analysis.effective_tax_rate:.1f}%\n")
                    f.write(f"Marginal Tax Rate: {self.current_analysis.marginal_tax_rate:.1f}%\n")
                    f.write(f"Tax Burden: {self.current_analysis.tax_burden_percentage:.1f}%\n")
                    f.write(f"Deduction Utilization: {self.current_analysis.deduction_utilization:.1f}%\n")
                    f.write(f"Credit Utilization: {self.current_analysis.credit_utilization:.1f}%\n\n")

                    f.write("INCOME DISTRIBUTION:\n")
                    for source, pct in self.current_analysis.income_distribution.items():
                        f.write(f"• {source}: {pct:.1f}%\n")

                    f.write("\nTAX LIABILITY BREAKDOWN:\n")
                    for tax_type, amount in self.current_analysis.tax_liability_breakdown.items():
                        f.write(f"• {tax_type}: ${amount:,.2f}\n")

                messagebox.showinfo("Export Complete", f"Report exported to {filename}")

        except Exception as e:
            self.error_tracker.track_error(error=e, context={"operation": "_export_report"})
            messagebox.showerror("Export Error", f"Failed to export report: {str(e)}")

    def _save_charts(self):
        """Save charts to image files"""
        try:
            directory = filedialog.askdirectory(title="Select Directory to Save Charts")

            if directory:
                saved_files = []

                if self.rate_chart:
                    rate_file = Path(directory) / f"tax_rates_{self.current_analysis.tax_year}.png"
                    self.rate_chart.savefig(rate_file, dpi=300, bbox_inches='tight')
                    saved_files.append(str(rate_file))

                if self.burden_chart:
                    burden_file = Path(directory) / f"tax_burden_{self.current_analysis.tax_year}.png"
                    self.burden_chart.savefig(burden_file, dpi=300, bbox_inches='tight')
                    saved_files.append(str(burden_file))

                if self.trend_chart:
                    trend_file = Path(directory) / f"tax_trends_{self.trend_analysis.analysis_period if self.trend_analysis else 'multi_year'}.png"
                    self.trend_chart.savefig(trend_file, dpi=300, bbox_inches='tight')
                    saved_files.append(str(trend_file))

                if saved_files:
                    messagebox.showinfo("Charts Saved", f"Charts saved to:\n" + "\n".join(saved_files))
                else:
                    messagebox.showwarning("No Charts", "No charts available to save.")

        except Exception as e:
            self.error_tracker.track_error(error=e, context={"operation": "_save_charts"})
            messagebox.showerror("Save Error", f"Failed to save charts: {str(e)}")

    def _update_status(self, message: str):
        """Update the status label"""
        if self.status_label:
            self.status_label.config(text=message)
        self.window.update_idletasks()

    def show(self):
        """Show the analytics window"""
        self.window.mainloop()

    def destroy(self):
        """Destroy the analytics window"""
        if self.window:
            self.window.destroy()
