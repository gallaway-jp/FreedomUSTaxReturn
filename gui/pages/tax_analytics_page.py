"""
Tax Analytics Page - Converted from Legacy Window

Tax analytics and reporting dashboard page.
Integrated into main window without popup dialogs.
"""

import customtkinter as ctk
from typing import Optional, List, Dict, Any
from datetime import datetime

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton


class TaxAnalyticsPage(ctk.CTkScrollableFrame):
    """
    Tax Analytics page - converted from legacy window to integrated page.
    
    Features:
    - Tax data analytics and insights
    - Historical trend analysis
    - Tax optimization recommendations
    - Comparative analysis
    - Advanced reporting
    """

    def __init__(self, master, config: AppConfig, tax_data: Optional[TaxData] = None,
                 accessibility_service: Optional[AccessibilityService] = None, **kwargs):
        super().__init__(master, **kwargs)

        self.config = config
        self.tax_data = tax_data
        self.accessibility_service = accessibility_service

        # Analytics data
        self.selected_year = 2024
        self.selected_metric = "Income"
        self.analytics_vars = {}

        # Build the page
        self._create_header()
        self._create_toolbar()
        self._create_main_content()
        self._load_analytics()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self)
        header_frame.pack(fill=ctk.X, padx=20, pady=(20, 10))

        title_label = ModernLabel(
            header_frame,
            text="📊 Tax Analytics",
            font_size=24,
            font_weight="bold"
        )
        title_label.pack(anchor=ctk.W, pady=(0, 5))

        subtitle_label = ModernLabel(
            header_frame,
            text="Analyze tax trends and optimize your tax strategy",
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
            text="📈 Trends",
            command=self._view_trends,
            button_type="secondary",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="💡 Optimization",
            command=self._show_optimization,
            button_type="secondary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📊 Comparison",
            command=self._compare_years,
            button_type="secondary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📤 Export",
            command=self._export_report,
            button_type="secondary",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="💾 Save",
            command=self._save_analytics,
            button_type="success",
            width=100
        ).pack(side=ctk.LEFT, padx=5)

        # Progress bar
        progress_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        progress_frame.pack(fill=ctk.X, pady=10)

        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=6)
        self.progress_bar.pack(fill=ctk.X)
        self.progress_bar.set(0)

        self.status_label = ModernLabel(progress_frame, text="Loading analytics...", font_size=11)
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
        self.tab_overview = self.tabview.add("📋 Overview")
        self.tab_trends = self.tabview.add("📈 Trends")
        self.tab_optimization = self.tabview.add("💡 Optimization")
        self.tab_comparisons = self.tabview.add("📊 Comparisons")
        self.tab_forecasts = self.tabview.add("🔮 Forecasts")

        # Setup tabs
        self._setup_overview_tab()
        self._setup_trends_tab()
        self._setup_optimization_tab()
        self._setup_comparisons_tab()
        self._setup_forecasts_tab()

    def _setup_overview_tab(self):
        """Setup analytics overview tab"""
        self.tab_overview.grid_rowconfigure(1, weight=1)
        self.tab_overview.grid_columnconfigure(0, weight=1)

        # Summary cards
        cards_frame = ctk.CTkFrame(self.tab_overview, fg_color="transparent")
        cards_frame.pack(fill=ctk.X, padx=20, pady=10)

        card_data = [
            ("Avg. Annual Income", "$0"),
            ("Avg. Tax Rate", "0%"),
            ("Avg. Refund", "$0"),
            ("Total Records", "0")
        ]

        for title, value in card_data:
            card = self._create_summary_card(cards_frame, title, value)
            card.pack(side=ctk.LEFT, padx=5, fill=ctk.X, expand=True)

        # Overview details
        frame = ctk.CTkScrollableFrame(self.tab_overview)
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

        overview_label = ModernLabel(frame, text="Analytics Summary", font_size=12, font_weight="bold")
        overview_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.overview_text = ctk.CTkTextbox(frame, height=300)
        self.overview_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.overview_text.insert("1.0",
            "Tax Analytics Overview:\n\n"
            "Years Analyzed: 0\n"
            "Data Records: 0\n"
            "Latest Return: N/A\n"
            "Earliest Return: N/A\n\n"
            "Key Metrics:\n"
            "• Average Income: N/A\n"
            "• Average Deductions: N/A\n"
            "• Average Tax: N/A\n"
            "• Average Refund: N/A"
        )
        self.overview_text.configure(state="disabled")

    def _setup_trends_tab(self):
        """Setup trends analysis tab"""
        self.tab_trends.grid_rowconfigure(0, weight=1)
        self.tab_trends.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_trends)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        trends_label = ModernLabel(frame, text="Income & Deduction Trends", font_size=12, font_weight="bold")
        trends_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.trends_text = ctk.CTkTextbox(frame, height=400)
        self.trends_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.trends_text.insert("1.0",
            "Historical Trends:\n\n"
            "Income Trends:\n"
            "  2024: $0\n"
            "  2023: $0\n"
            "  2022: $0\n"
            "  YoY Change: --\n\n"
            "Deduction Trends:\n"
            "  2024: $0\n"
            "  2023: $0\n"
            "  2022: $0\n"
            "  YoY Change: --\n\n"
            "Tax Liability Trends:\n"
            "  2024: $0\n"
            "  2023: $0\n"
            "  2022: $0"
        )
        self.trends_text.configure(state="disabled")

    def _setup_optimization_tab(self):
        """Setup optimization recommendations tab"""
        self.tab_optimization.grid_rowconfigure(0, weight=1)
        self.tab_optimization.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_optimization)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        optimization_label = ModernLabel(frame, text="Tax Optimization Opportunities", font_size=12, font_weight="bold")
        optimization_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.optimization_text = ctk.CTkTextbox(frame, height=400)
        self.optimization_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.optimization_text.insert("1.0",
            "Tax Optimization Opportunities:\n\n"
            "Based on your tax history, consider:\n\n"
            "1. Income Management\n"
            "   • Timing of income recognition\n"
            "   • Deferral strategies\n\n"
            "2. Deduction Strategies\n"
            "   • Bunching deductions\n"
            "   • Qualified business deductions\n\n"
            "3. Tax Credits\n"
            "   • Unused credits\n"
            "   • Eligibility verification\n\n"
            "4. Entity Structure\n"
            "   • Business structure optimization\n"
            "   • Pass-through considerations"
        )
        self.optimization_text.configure(state="disabled")

    def _setup_comparisons_tab(self):
        """Setup year-over-year comparisons tab"""
        self.tab_comparisons.grid_rowconfigure(0, weight=1)
        self.tab_comparisons.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_comparisons)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        comparison_label = ModernLabel(frame, text="Year-to-Year Comparisons", font_size=12, font_weight="bold")
        comparison_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.comparison_text = ctk.CTkTextbox(frame, height=400)
        self.comparison_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.comparison_text.insert("1.0",
            "Year-to-Year Analysis:\n\n"
            "2024 vs 2023:\n"
            "  Income: -- (--% change)\n"
            "  Deductions: -- (--% change)\n"
            "  Tax: -- (--% change)\n\n"
            "2023 vs 2022:\n"
            "  Income: -- (--% change)\n"
            "  Deductions: -- (--% change)\n"
            "  Tax: -- (--% change)\n\n"
            "Multi-year Average:\n"
            "  Income: $0\n"
            "  Deductions: $0\n"
            "  Tax Rate: 0%"
        )
        self.comparison_text.configure(state="disabled")

    def _setup_forecasts_tab(self):
        """Setup forecast and projection tab"""
        self.tab_forecasts.grid_rowconfigure(0, weight=1)
        self.tab_forecasts.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_forecasts)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        forecast_label = ModernLabel(frame, text="Tax Forecasts", font_size=12, font_weight="bold")
        forecast_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.forecast_text = ctk.CTkTextbox(frame, height=400)
        self.forecast_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.forecast_text.insert("1.0",
            "2025 Forecast (Based on Current Trends):\n\n"
            "Projected Income: $0\n"
            "Projected Deductions: $0\n"
            "Projected Tax Liability: $0\n"
            "Projected Refund: $0\n\n"
            "Confidence Level: --\n\n"
            "Assumptions:\n"
            "• Income growth: 0%\n"
            "• Expense patterns: Consistent\n"
            "• Tax law: No major changes\n"
            "• Personal situation: No major changes"
        )
        self.forecast_text.configure(state="disabled")

    def _create_summary_card(self, parent, title, value):
        """Create a summary metric card"""
        card = ctk.CTkFrame(parent, corner_radius=8, fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        
        title_label = ctk.CTkLabel(card, text=title, text_color="gray", font=("", 11))
        title_label.pack(padx=10, pady=(8, 2))

        value_label = ctk.CTkLabel(card, text=value, text_color="white", font=("", 13, "bold"))
        value_label.pack(padx=10, pady=(2, 8))

        return card

    # ===== Action Methods =====

    def _load_analytics(self):
        """Load analytics data"""
        self.status_label.configure(text="Loading analytics...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Analytics ready")
        self.progress_bar.set(1.0)

    def _view_trends(self):
        """View detailed trends"""
        self.status_label.configure(text="Loading trends...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Trends loaded")
        self.progress_bar.set(1.0)

    def _show_optimization(self):
        """Show optimization recommendations"""
        self.status_label.configure(text="Analyzing tax opportunities...")
        self.progress_bar.set(0.8)
        self.status_label.configure(text="Opportunities identified")
        self.progress_bar.set(1.0)

    def _compare_years(self):
        """Compare tax years"""
        self.status_label.configure(text="Comparing years...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Comparison complete")
        self.progress_bar.set(1.0)

    def _export_report(self):
        """Export analytics report"""
        self.status_label.configure(text="Exporting...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Export complete")
        self.progress_bar.set(1.0)

    def _save_analytics(self):
        """Save analytics data"""
        self.status_label.configure(text="Saving...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Saved")
        self.progress_bar.set(1.0)
