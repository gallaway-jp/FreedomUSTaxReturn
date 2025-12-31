"""
Year Comparison Window - GUI for comparing tax returns between years

This window provides:
- Side-by-side comparison of tax returns from different years
- Visual charts showing year-over-year changes
- Detailed breakdown of income, deductions, credits, and tax calculations
- Export functionality for comparison reports
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from typing import Dict, Any, Optional, List, Tuple
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from datetime import datetime
import json
import os

from services.tax_year_service import TaxYearService

logger = logging.getLogger(__name__)


class YearComparisonWindow(tk.Toplevel):
    """
    Window for comparing tax returns between different years.

    Shows detailed comparisons with charts and allows export of comparison data.
    """

    def __init__(self, parent, tax_year_service: TaxYearService, tax_data_dict: Dict[int, Dict[str, Any]]):
        """
        Initialize the year comparison window.

        Args:
            parent: Parent window
            tax_year_service: Service for tax year operations
            tax_data_dict: Dictionary mapping years to their tax data
        """
        super().__init__(parent)
        self.tax_year_service = tax_year_service
        self.tax_data_dict = tax_data_dict
        self.title("Year-over-Year Tax Comparison")
        self.geometry("1200x800")
        self.resizable(True, True)

        # Available years for comparison
        self.available_years = sorted(tax_data_dict.keys(), reverse=True)

        self._setup_ui()
        self._populate_year_selections()
        self._perform_comparison()

    def _setup_ui(self):
        """Set up the user interface"""
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top control panel
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # Year selection
        ttk.Label(control_frame, text="Compare:").pack(side=tk.LEFT, padx=(0, 5))

        self.year1_var = tk.StringVar()
        self.year1_combo = ttk.Combobox(
            control_frame,
            textvariable=self.year1_var,
            state="readonly",
            width=6
        )
        self.year1_combo.pack(side=tk.LEFT, padx=(0, 5))
        self.year1_combo.bind("<<ComboboxSelected>>", self._on_year_changed)

        ttk.Label(control_frame, text="vs").pack(side=tk.LEFT, padx=(0, 5))

        self.year2_var = tk.StringVar()
        self.year2_combo = ttk.Combobox(
            control_frame,
            textvariable=self.year2_var,
            state="readonly",
            width=6
        )
        self.year2_combo.pack(side=tk.LEFT, padx=(0, 5))
        self.year2_combo.bind("<<ComboboxSelected>>", self._on_year_changed)

        # Export button
        ttk.Button(
            control_frame,
            text="Export Comparison",
            command=self._export_comparison
        ).pack(side=tk.RIGHT, padx=(10, 0))

        # Refresh button
        ttk.Button(
            control_frame,
            text="Refresh",
            command=self._perform_comparison
        ).pack(side=tk.RIGHT)

        # Main content area with paned window
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left panel - Summary comparison
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        # Summary title
        ttk.Label(left_frame, text="Summary Comparison", font=("", 12, "bold")).pack(pady=(0, 10))

        # Summary treeview
        columns = ("Metric", "Year1", "Year2", "Difference", "% Change")
        self.summary_tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.summary_tree.heading(col, text=col)
            self.summary_tree.column(col, width=120, anchor="center")

        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.summary_tree.yview)
        self.summary_tree.configure(yscrollcommand=scrollbar.set)

        self.summary_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Right panel - Charts and details
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)

        # Chart notebook
        self.chart_notebook = ttk.Notebook(right_frame)
        self.chart_notebook.pack(fill=tk.BOTH, expand=True)

        # Income chart tab
        income_frame = ttk.Frame(self.chart_notebook)
        self.chart_notebook.add(income_frame, text="Income Sources")

        # Tax calculation chart tab
        tax_frame = ttk.Frame(self.chart_notebook)
        self.chart_notebook.add(tax_frame, text="Tax Calculations")

        # Trend chart tab
        trend_frame = ttk.Frame(self.chart_notebook)
        self.chart_notebook.add(trend_frame, text="Year Trends")

        # Chart canvases (will be populated when comparison is performed)
        self.income_canvas = None
        self.tax_canvas = None
        self.trend_canvas = None

    def _populate_year_selections(self):
        """Populate the year selection dropdowns"""
        years = [str(year) for year in self.available_years]

        self.year1_combo['values'] = years
        self.year2_combo['values'] = years

        # Set defaults (most recent two years if available)
        if len(self.available_years) >= 2:
            self.year1_var.set(str(self.available_years[0]))
            self.year2_var.set(str(self.available_years[1]))
        elif len(self.available_years) == 1:
            self.year1_var.set(str(self.available_years[0]))
            self.year2_var.set("")  # No second year available

    def _on_year_changed(self, event=None):
        """Handle year selection change"""
        self._perform_comparison()

    def _perform_comparison(self):
        """Perform the year-over-year comparison"""
        try:
            year1_str = self.year1_var.get()
            year2_str = self.year2_var.get()

            if not year1_str:
                return

            year1 = int(year1_str)
            year2 = int(year2_str) if year2_str else None

            if year2 is None:
                # Single year view - show details for that year
                self._show_single_year_details(year1)
            else:
                # Two year comparison
                self._show_year_comparison(year1, year2)

        except ValueError as e:
            logger.error(f"Error in year comparison: {e}")
            messagebox.showerror("Error", "Invalid year selection")

    def _show_single_year_details(self, year: int):
        """Show details for a single tax year"""
        tax_data = self.tax_data_dict.get(year, {})

        # Clear existing data
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)

        # Show key metrics for the single year
        metrics = [
            ("Total Income", "income", "total_income"),
            ("Total Deductions", "deductions", "total_deductions"),
            ("Taxable Income", "calculations", "taxable_income"),
            ("Total Tax", "calculations", "total_tax"),
            ("Total Credits", "credits", "total_credits"),
            ("Refund/Owed", "calculations", "refund_owed")
        ]

        for display_name, section, key in metrics:
            value = self._extract_value(tax_data, section, key)
            self.summary_tree.insert("", "end", values=(display_name, f"${value:,.2f}", "-", "-", "-"))

        # Update chart title
        self._update_single_year_chart(year, tax_data)

    def _show_year_comparison(self, year1: int, year2: int):
        """Show comparison between two tax years"""
        data1 = self.tax_data_dict.get(year1, {})
        data2 = self.tax_data_dict.get(year2, {})

        # Get comparison data from service
        comparison = self.tax_year_service.get_year_comparison_data(year1, year2, data1, data2)

        # Clear existing data
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)

        # Populate summary table
        for metric_key, metric_data in comparison.get("summary", {}).items():
            display_name = self._get_metric_display_name(metric_key)
            val1 = metric_data.get("year1", 0)
            val2 = metric_data.get("year2", 0)
            diff = metric_data.get("difference", 0)
            pct_change = metric_data.get("percent_change", 0)

            self.summary_tree.insert("", "end", values=(
                display_name,
                f"${val1:,.2f}",
                f"${val2:,.2f}",
                f"${diff:+,.2f}",
                f"{pct_change:+.1f}%"
            ))

        # Update charts
        self._update_comparison_charts(year1, year2, comparison)

    def _get_metric_display_name(self, metric_key: str) -> str:
        """Get display name for a metric key"""
        name_map = {
            "total_income": "Total Income",
            "total_deductions": "Total Deductions",
            "taxable_income": "Taxable Income",
            "total_tax": "Total Tax",
            "total_credits": "Total Credits",
            "refund_owed": "Refund/Owed"
        }
        return name_map.get(metric_key, metric_key.replace("_", " ").title())

    def _extract_value(self, tax_data: Dict[str, Any], section: str, key: str) -> float:
        """Extract a value from tax data"""
        try:
            if section == "calculations":
                # These might be computed values
                return tax_data.get("calculations", {}).get(key, 0)
            else:
                return tax_data.get(section, {}).get(key, 0)
        except (KeyError, TypeError):
            return 0

    def _update_single_year_chart(self, year: int, tax_data: Dict[str, Any]):
        """Update charts for single year view"""
        # Clear existing charts
        self._clear_charts()

        # Create income breakdown chart
        income_data = tax_data.get("income", {})
        if income_data:
            self._create_income_pie_chart(year, income_data)

    def _update_comparison_charts(self, year1: int, year2: int, comparison: Dict[str, Any]):
        """Update charts for year comparison"""
        # Clear existing charts
        self._clear_charts()

        # Create comparison charts
        self._create_income_comparison_chart(year1, year2, comparison)
        self._create_tax_comparison_chart(year1, year2, comparison)
        self._create_trend_chart(year1, year2, comparison)

    def _clear_charts(self):
        """Clear existing chart canvases"""
        for canvas in [self.income_canvas, self.tax_canvas, self.trend_canvas]:
            if canvas:
                canvas.get_tk_widget().destroy()
                canvas = None

        self.income_canvas = None
        self.tax_canvas = None
        self.trend_canvas = None

    def _create_income_pie_chart(self, year: int, income_data: Dict[str, Any]):
        """Create a pie chart showing income sources"""
        # Get income breakdown tabs
        income_frame = self.chart_notebook.nametowidget(self.chart_notebook.tabs()[0])

        # Clear existing content
        for widget in income_frame.winfo_children():
            widget.destroy()

        # Extract income sources
        sources = []
        amounts = []

        for key, value in income_data.items():
            if isinstance(value, (int, float)) and value > 0:
                sources.append(key.replace("_", " ").title())
                amounts.append(value)

        if not sources:
            ttk.Label(income_frame, text="No income data available").pack()
            return

        # Create pie chart
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.pie(amounts, labels=sources, autopct='%1.1f%%', startangle=90)
        ax.set_title(f"Income Sources - {year}")
        ax.axis('equal')

        # Embed in tkinter
        self.income_canvas = FigureCanvasTkAgg(fig, master=income_frame)
        self.income_canvas.draw()
        self.income_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _create_income_comparison_chart(self, year1: int, year2: int, comparison: Dict[str, Any]):
        """Create bar chart comparing income between years"""
        # Get income frame
        income_frame = self.chart_notebook.nametowidget(self.chart_notebook.tabs()[0])

        # Clear existing content
        for widget in income_frame.winfo_children():
            widget.destroy()

        # Get income data for both years
        data1 = self.tax_data_dict.get(year1, {}).get("income", {})
        data2 = self.tax_data_dict.get(year2, {}).get("income", {})

        # Extract common income sources
        all_sources = set(data1.keys()) | set(data2.keys())
        sources = []
        amounts1 = []
        amounts2 = []

        for source in sorted(all_sources):
            if isinstance(data1.get(source, 0), (int, float)) or isinstance(data2.get(source, 0), (int, float)):
                sources.append(source.replace("_", " ").title())
                amounts1.append(float(data1.get(source, 0)))
                amounts2.append(float(data2.get(source, 0)))

        if not sources:
            ttk.Label(income_frame, text="No income data available for comparison").pack()
            return

        # Create bar chart
        fig, ax = plt.subplots(figsize=(8, 5))
        x = range(len(sources))
        width = 0.35

        ax.bar([i - width/2 for i in x], amounts1, width, label=str(year1), alpha=0.8)
        ax.bar([i + width/2 for i in x], amounts2, width, label=str(year2), alpha=0.8)

        ax.set_xlabel('Income Source')
        ax.set_ylabel('Amount ($)')
        ax.set_title(f'Income Comparison: {year1} vs {year2}')
        ax.set_xticks(x)
        ax.set_xticklabels(sources, rotation=45, ha='right')
        ax.legend()
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

        plt.tight_layout()

        # Embed in tkinter
        self.income_canvas = FigureCanvasTkAgg(fig, master=income_frame)
        self.income_canvas.draw()
        self.income_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _create_tax_comparison_chart(self, year1: int, year2: int, comparison: Dict[str, Any]):
        """Create chart comparing tax calculations"""
        # Get tax frame
        tax_frame = self.chart_notebook.nametowidget(self.chart_notebook.tabs()[1])

        # Clear existing content
        for widget in tax_frame.winfo_children():
            widget.destroy()

        # Get tax calculation data
        summary = comparison.get("summary", {})

        categories = ["Total Income", "Total Deductions", "Taxable Income", "Total Tax", "Total Credits"]
        keys = ["total_income", "total_deductions", "taxable_income", "total_tax", "total_credits"]

        amounts1 = [summary.get(key, {}).get("year1", 0) for key in keys]
        amounts2 = [summary.get(key, {}).get("year2", 0) for key in keys]

        # Create bar chart
        fig, ax = plt.subplots(figsize=(8, 5))
        x = range(len(categories))
        width = 0.35

        ax.bar([i - width/2 for i in x], amounts1, width, label=str(year1), alpha=0.8)
        ax.bar([i + width/2 for i in x], amounts2, width, label=str(year2), alpha=0.8)

        ax.set_xlabel('Tax Category')
        ax.set_ylabel('Amount ($)')
        ax.set_title(f'Tax Calculation Comparison: {year1} vs {year2}')
        ax.set_xticks(x)
        ax.set_xticklabels(categories, rotation=45, ha='right')
        ax.legend()
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

        plt.tight_layout()

        # Embed in tkinter
        self.tax_canvas = FigureCanvasTkAgg(fig, master=tax_frame)
        self.tax_canvas.draw()
        self.tax_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _create_trend_chart(self, year1: int, year2: int, comparison: Dict[str, Any]):
        """Create trend chart showing changes"""
        # Get trend frame
        trend_frame = self.chart_notebook.nametowidget(self.chart_notebook.tabs()[2])

        # Clear existing content
        for widget in trend_frame.winfo_children():
            widget.destroy()

        # Get summary data
        summary = comparison.get("summary", {})

        # Create a simple trend visualization
        fig, ax = plt.subplots(figsize=(8, 5))

        metrics = ["total_income", "total_tax", "refund_owed"]
        metric_names = ["Total Income", "Total Tax", "Refund/Owed"]

        for i, (metric, name) in enumerate(zip(metrics, metric_names)):
            val1 = summary.get(metric, {}).get("year1", 0)
            val2 = summary.get(metric, {}).get("year2", 0)

            ax.plot([year1, year2], [val1, val2], marker='o', label=name, linewidth=2)

        ax.set_xlabel('Tax Year')
        ax.set_ylabel('Amount ($)')
        ax.set_title(f'Key Metrics Trend: {year1} to {year2}')
        ax.legend()
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        # Embed in tkinter
        self.trend_canvas = FigureCanvasTkAgg(fig, master=trend_frame)
        self.trend_canvas.draw()
        self.trend_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _export_comparison(self):
        """Export the comparison data to a file"""
        try:
            year1 = int(self.year1_var.get())
            year2 = int(self.year2_var.get()) if self.year2_var.get() else None

            if year2 is None:
                messagebox.showwarning("Export", "Please select two years to compare for export.")
                return

            # Get comparison data
            data1 = self.tax_data_dict.get(year1, {})
            data2 = self.tax_data_dict.get(year2, {})
            comparison = self.tax_year_service.get_year_comparison_data(year1, year2, data1, data2)

            # Ask for file location
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")],
                title="Export Comparison Data"
            )

            if filename:
                with open(filename, 'w') as f:
                    json.dump({
                        "comparison_years": [year1, year2],
                        "generated_date": datetime.now().isoformat(),
                        "comparison_data": comparison
                    }, f, indent=2)

                messagebox.showinfo("Export Complete", f"Comparison data exported to {filename}")

        except Exception as e:
            logger.error(f"Error exporting comparison: {e}")
            messagebox.showerror("Export Error", f"Failed to export comparison: {str(e)}")