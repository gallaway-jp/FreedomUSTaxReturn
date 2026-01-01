"""
Tax Projections Window - GUI for tax liability projections

Provides interactive tax projection modeling with multiple scenarios
and visual charts for future tax planning.
"""

import customtkinter as ctk
from typing import Optional, Dict, Any, List
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from datetime import datetime, date
from decimal import Decimal

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.tax_calculation_service import TaxCalculationService
from services.tax_analytics_service import TaxAnalyticsService, TaxProjectionResult, TaxProjectionScenario
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton, show_info_message, show_error_message


class TaxProjectionsWindow:
    """
    Window for displaying and interacting with tax projections.

    Features:
    - Multiple projection scenarios (Base, Conservative, Aggressive, Retirement)
    - Interactive charts and graphs
    - Scenario comparison tools
    - Export capabilities
    - Assumption customization
    """

    def __init__(self, config: AppConfig, tax_calc_service: TaxCalculationService, tax_data: TaxData):
        """
        Initialize tax projections window.

        Args:
            config: Application configuration
            tax_calc_service: Tax calculation service
            tax_data: Current tax data
        """
        self.config = config
        self.tax_calc_service = tax_calc_service
        self.tax_data = tax_data

        # Initialize analytics service
        self.analytics_service = TaxAnalyticsService(config, tax_calc_service)

        # Projection data
        self.projection_result: Optional[TaxProjectionResult] = None
        self.selected_scenario: Optional[TaxProjectionScenario] = None

        # UI components
        self.window: Optional[ctk.CTkToplevel] = None
        self.main_frame: Optional[ModernFrame] = None
        self.chart_frame: Optional[ctk.CTkFrame] = None
        self.scenarios_frame: Optional[ctk.CTkFrame] = None
        self.details_frame: Optional[ctk.CTkFrame] = None

        # Chart components
        self.canvas: Optional[FigureCanvasTkAgg] = None
        self.figure: Optional[plt.Figure] = None

        self._create_window()
        self._load_projections()

    def _create_window(self):
        """Create the main window"""
        self.window = ctk.CTkToplevel()
        self.window.title("Tax Projections - Future Tax Planning")
        self.window.geometry("1200x800")
        self.window.resizable(True, True)

        # Configure grid
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(0, weight=1)

        # Main container
        main_container = ctk.CTkFrame(self.window, fg_color="transparent")
        main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(1, weight=1)

        # Title
        title_label = ModernLabel(
            main_container,
            text="🔮 Tax Projections",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 10), sticky="w")

        # Content area with splitter
        content_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # Create paned window for resizable panels
        paned = tk.PanedWindow(content_frame, orient=tk.HORIZONTAL, sashwidth=5)
        paned.grid(row=0, column=0, sticky="nsew")

        # Left panel - Scenarios and controls
        left_panel = ctk.CTkFrame(paned, width=300)
        paned.add(left_panel, minsize=250)

        # Right panel - Charts and details
        right_panel = ctk.CTkFrame(paned)
        paned.add(right_panel, minsize=400)

        # Setup left panel
        self._setup_scenarios_panel(left_panel)

        # Setup right panel
        self._setup_charts_panel(right_panel)

        # Bottom buttons
        self._setup_bottom_buttons(main_container)

    def _setup_scenarios_panel(self, parent: ctk.CTkFrame):
        """Setup the scenarios selection panel"""
        parent.grid_columnconfigure(0, weight=1)

        # Scenarios title
        scenarios_title = ModernLabel(
            parent,
            text="Projection Scenarios",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        scenarios_title.grid(row=0, column=0, pady=(10, 5), sticky="w")

        # Scenarios listbox frame
        list_frame = ctk.CTkFrame(parent)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)

        # Scenarios listbox
        self.scenarios_listbox = tk.Listbox(
            list_frame,
            selectmode=tk.SINGLE,
            font=("Arial", 10),
            bg="#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#ffffff",
            fg="#ffffff" if ctk.get_appearance_mode() == "Dark" else "#000000",
            selectbackground="#1f6aa5",
            relief=tk.FLAT,
            borderwidth=0
        )
        self.scenarios_listbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Bind selection event
        self.scenarios_listbox.bind('<<ListboxSelect>>', self._on_scenario_selected)

        # Scrollbar for listbox
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.scenarios_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.scenarios_listbox.config(yscrollcommand=scrollbar.set)

        # Configure parent grid weights
        parent.grid_rowconfigure(1, weight=1)

    def _setup_charts_panel(self, parent: ctk.CTkFrame):
        """Setup the charts and details panel"""
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        # Chart frame
        self.chart_frame = ctk.CTkFrame(parent)
        self.chart_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.chart_frame.grid_columnconfigure(0, weight=1)
        self.chart_frame.grid_rowconfigure(0, weight=1)

        # Details frame
        self.details_frame = ctk.CTkFrame(parent, height=200)
        self.details_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        self.details_frame.grid_columnconfigure(0, weight=1)

        # Details text area
        self.details_text = ctk.CTkTextbox(self.details_frame, wrap="word")
        self.details_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Configure weights
        parent.grid_rowconfigure(0, weight=3)  # Chart gets more space
        parent.grid_rowconfigure(1, weight=1)  # Details get less space

    def _setup_bottom_buttons(self, parent: ctk.CTkFrame):
        """Setup bottom action buttons"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.grid(row=2, column=0, pady=(10, 0), sticky="ew")

        # Export button
        export_btn = ModernButton(
            button_frame,
            text="📊 Export Report",
            command=self._export_report,
            button_type="secondary"
        )
        export_btn.pack(side="left", padx=(0, 10))

        # Refresh button
        refresh_btn = ModernButton(
            button_frame,
            text="🔄 Recalculate",
            command=self._recalculate_projections,
            button_type="secondary"
        )
        refresh_btn.pack(side="left", padx=(0, 10))

        # Close button
        close_btn = ModernButton(
            button_frame,
            text="❌ Close",
            command=self._close_window,
            button_type="primary"
        )
        close_btn.pack(side="right")

    def _load_projections(self):
        """Load and display tax projections"""
        try:
            # Calculate projections
            self.projection_result = self.analytics_service.project_future_tax_liability(
                self.tax_data,
                projection_years=5,  # 5-year projection
                income_growth_rate=0.03,  # 3% annual growth
                inflation_rate=0.025  # 2.5% inflation
            )

            # Populate scenarios list
            self._populate_scenarios_list()

            # Show initial chart
            if self.projection_result.scenarios:
                self.selected_scenario = self.projection_result.scenarios[0]
                self._update_chart()
                self._update_details()

        except Exception as e:
            show_error_message("Projection Error", f"Failed to calculate projections: {str(e)}")
            self._close_window()

    def _populate_scenarios_list(self):
        """Populate the scenarios listbox"""
        if not self.projection_result:
            return

        self.scenarios_listbox.delete(0, tk.END)

        for scenario in self.projection_result.scenarios:
            display_text = f"{scenario.scenario_name}\n"
            display_text += f"Year: {scenario.projection_year}\n"
            display_text += f"Income: ${scenario.projected_income:,.0f}\n"
            display_text += f"Tax: ${scenario.projected_tax_liability:,.0f}\n"
            display_text += f"Rate: {scenario.projected_effective_rate:.1f}%"

            self.scenarios_listbox.insert(tk.END, display_text)

        # Select first scenario
        if self.projection_result.scenarios:
            self.scenarios_listbox.selection_set(0)

    def _on_scenario_selected(self, event):
        """Handle scenario selection"""
        selection = self.scenarios_listbox.curselection()
        if selection and self.projection_result:
            index = selection[0]
            if 0 <= index < len(self.projection_result.scenarios):
                self.selected_scenario = self.projection_result.scenarios[index]
                self._update_chart()
                self._update_details()

    def _update_chart(self):
        """Update the projection chart"""
        if not self.selected_scenario or not self.chart_frame:
            return

        # Clear previous chart
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        # Create matplotlib figure
        self.figure, ax = plt.subplots(figsize=(8, 6), dpi=100)

        # Create comparison data
        if self.projection_result:
            scenarios = self.projection_result.scenarios
            scenario_names = [s.scenario_name for s in scenarios]
            tax_liabilities = [s.projected_tax_liability for s in scenarios]
            incomes = [s.projected_income for s in scenarios]

            # Create bar chart
            x = range(len(scenarios))
            bars1 = ax.bar([i - 0.2 for i in x], tax_liabilities, 0.4, label='Tax Liability', color='red', alpha=0.7)
            bars2 = ax.bar([i + 0.2 for i in x], incomes, 0.4, label='Income', color='blue', alpha=0.7)

            ax.set_xlabel('Projection Scenarios')
            ax.set_ylabel('Amount ($)')
            ax.set_title(f'Tax Projections for {self.selected_scenario.projection_year}')
            ax.set_xticks(x)
            ax.set_xticklabels(scenario_names, rotation=45, ha='right')
            ax.legend()
            ax.grid(True, alpha=0.3)

            # Add value labels on bars
            for bar in bars1:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'${height:,.0f}', ha='center', va='bottom', fontsize=8)

            for bar in bars2:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'${height:,.0f}', ha='center', va='bottom', fontsize=8)

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    def _update_details(self):
        """Update the details text area"""
        if not self.selected_scenario or not self.details_frame:
            return

        # Clear previous content
        self.details_text.delete("0.0", tk.END)

        # Add scenario details
        details = f"""
PROJECTION DETAILS - {self.selected_scenario.scenario_name}
{'='*50}

Base Year: {self.selected_scenario.base_year}
Projection Year: {self.selected_scenario.projection_year}

FINANCIAL PROJECTIONS:
• Projected Income: ${self.selected_scenario.projected_income:,.2f}
• Projected Tax Liability: ${self.selected_scenario.projected_tax_liability:,.2f}
• Effective Tax Rate: {self.selected_scenario.projected_effective_rate:.1f}%

ASSUMPTIONS:
• Income Growth Rate: {self.selected_scenario.assumptions.get('income_growth_rate', 0)*100:.1f}%
• Inflation Rate: {self.selected_scenario.assumptions.get('inflation_rate', 0)*100:.1f}%
• Projection Period: {self.selected_scenario.assumptions.get('projection_years', 0)} years

CONFIDENCE LEVEL: {self.selected_scenario.confidence_level}

"""

        if self.selected_scenario.risk_factors:
            details += "RISK FACTORS:\n"
            for factor in self.selected_scenario.risk_factors:
                details += f"• {factor}\n"
            details += "\n"

        # Add insights if available
        if self.projection_result and self.projection_result.summary_insights:
            details += "KEY INSIGHTS:\n"
            for insight in self.projection_result.summary_insights:
                details += f"• {insight}\n"
            details += "\n"

        if self.projection_result and self.projection_result.recommended_actions:
            details += "RECOMMENDED ACTIONS:\n"
            for action in self.projection_result.recommended_actions:
                details += f"• {action}\n"

        self.details_text.insert("0.0", details.strip())

    def _export_report(self):
        """Export projection report"""
        if not self.projection_result:
            show_error_message("Export Error", "No projection data to export.")
            return

        try:
            from tkinter import filedialog
            import json

            # Ask for file location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Export Tax Projections Report"
            )

            if file_path:
                # Export to JSON
                with open(file_path, 'w') as f:
                    json.dump(self.projection_result.to_dict(), f, indent=2)

                show_info_message("Export Complete", f"Tax projections exported to {file_path}")

        except Exception as e:
            show_error_message("Export Error", f"Failed to export report: {str(e)}")

    def _recalculate_projections(self):
        """Recalculate projections with updated assumptions"""
        # For now, just reload with same parameters
        # Future enhancement: Allow user to modify assumptions
        self._load_projections()
        show_info_message("Recalculated", "Tax projections have been recalculated.")

    def _close_window(self):
        """Close the projections window"""
        if self.window:
            self.window.destroy()

    def show(self):
        """Show the projections window"""
        if self.window:
            self.window.mainloop()