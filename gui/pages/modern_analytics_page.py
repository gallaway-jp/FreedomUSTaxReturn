"""
Modern Analytics Page - Advanced tax analytics and insights

Provides comprehensive analytics views including:
- Tax burden and effective rate analysis
- Deduction optimization insights
- Income trend analysis
- Tax bracket visualization
- Year-over-year comparisons
"""

import customtkinter as ctk
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from decimal import Decimal
import json

from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton
from services.accessibility_service import AccessibilityService


class ModernAnalyticsPage(ctk.CTkScrollableFrame):
    """
    Modern analytics page showing detailed tax insights and visualizations.

    Features:
    - Tax burden analysis
    - Effective tax rate tracking
    - Deduction utilization reports
    - Income distribution analysis
    - Tax bracket visualization
    - Year-over-year trend analysis
    """

    def __init__(self, parent, accessibility_service: Optional[AccessibilityService] = None, **kwargs):
        """
        Initialize analytics page.

        Args:
            parent: Parent widget
            accessibility_service: Accessibility service instance
        """
        super().__init__(parent, **kwargs)

        self.accessibility_service = accessibility_service

        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Create UI
        self._create_header()
        self._create_analytics_sections()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        title_label = ModernLabel(
            header_frame,
            text="📊 Tax Analytics & Insights",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(anchor="w")

        subtitle_label = ModernLabel(
            header_frame,
            text="Detailed analysis of your tax situation, deductions, and planning opportunities",
            font=ctk.CTkFont(size=12),
            text_color="gray60"
        )
        subtitle_label.pack(anchor="w", pady=(5, 0))

    def _create_analytics_sections(self):
        """Create the main analytics sections"""
        # Tax Burden Analysis
        self._create_tax_burden_section()

        # Deduction Analysis
        self._create_deduction_analysis_section()

        # Income Analysis
        self._create_income_analysis_section()

        # Tax Bracket Info
        self._create_tax_bracket_section()

        # Year-over-Year Comparison
        self._create_year_comparison_section()

    def _create_tax_burden_section(self):
        """Create tax burden analysis section"""
        section = ModernFrame(self)
        section.pack(fill="x", padx=20, pady=(0, 20))

        title = ModernLabel(
            section,
            text="💰 Tax Burden Analysis",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title.pack(anchor="w", pady=(0, 15))

        # Create metrics grid
        metrics_frame = ctk.CTkFrame(section, fg_color="transparent")
        metrics_frame.pack(fill="x")

        self._create_metric_card(metrics_frame, "Total Income", "$125,000", "left")
        self._create_metric_card(metrics_frame, "Total Deductions", "$28,500", "left")
        self._create_metric_card(metrics_frame, "Taxable Income", "$96,500", "left")
        self._create_metric_card(metrics_frame, "Total Tax", "$18,240", "left")

        # Additional details
        details_frame = ctk.CTkFrame(section, fg_color="transparent")
        details_frame.pack(fill="x", pady=(15, 0))

        self._create_detail_row(details_frame, "Federal Income Tax", "$15,240", "secondary")
        self._create_detail_row(details_frame, "Self-Employment Tax", "$3,000", "secondary")
        self._create_detail_row(details_frame, "State Tax", "$2,100", "secondary")
        self._create_detail_row(details_frame, "Effective Tax Rate", "14.59%", "success")

    def _create_deduction_analysis_section(self):
        """Create deduction analysis section"""
        section = ModernFrame(self)
        section.pack(fill="x", padx=20, pady=(0, 20))

        title = ModernLabel(
            section,
            text="📋 Deduction Analysis",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title.pack(anchor="w", pady=(0, 15))

        # Deduction breakdown
        deductions = [
            ("Standard Deduction", "$13,850", "Using standard deduction"),
            ("Business Deductions", "$8,200", "Home office, supplies, equipment"),
            ("Charitable Contributions", "$3,500", "Donations to qualified charities"),
            ("Medical Expenses", "$5,100", "Exceeds 7.5% floor"),
            ("State/Local Taxes", "$10,000", "Limited by $10,000 cap"),
        ]

        for ded_name, amount, description in deductions:
            self._create_deduction_row(section, ded_name, amount, description)

        # Recommendations
        rec_frame = ctk.CTkFrame(section, fg_color="transparent")
        rec_frame.pack(fill="x", pady=(15, 0))

        rec_title = ModernLabel(rec_frame, text="💡 Recommendations:", font=ctk.CTkFont(weight="bold"))
        rec_title.pack(anchor="w", pady=(0, 10))

        self._create_recommendation(rec_frame, "Consider bunching charitable donations in alternating years for higher deductions")
        self._create_recommendation(rec_frame, "Track business expenses throughout the year for maximum deductions")
        self._create_recommendation(rec_frame, "Explore energy efficiency credits for home improvements")

    def _create_income_analysis_section(self):
        """Create income analysis section"""
        section = ModernFrame(self)
        section.pack(fill="x", padx=20, pady=(0, 20))

        title = ModernLabel(
            section,
            text="📈 Income Analysis",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title.pack(anchor="w", pady=(0, 15))

        # Income breakdown
        income_items = [
            ("W-2 Wages", "$95,000", "Primary employment"),
            ("Business Income", "$15,000", "1099 contracting"),
            ("Investment Income", "$8,000", "Dividends and capital gains"),
            ("Interest Income", "$2,500", "Savings accounts and bonds"),
            ("Other Income", "$4,500", "Rental and misc income"),
        ]

        for inc_name, amount, source in income_items:
            self._create_income_row(section, inc_name, amount, source)

        # Income distribution visualization
        viz_frame = ctk.CTkFrame(section, fg_color="transparent")
        viz_frame.pack(fill="x", pady=(15, 0))

        viz_title = ModernLabel(viz_frame, text="Income Distribution:", font=ctk.CTkFont(weight="bold"))
        viz_title.pack(anchor="w", pady=(0, 10))

        self._create_bar_chart(viz_frame, "W-2 Wages", 95000, 125000)
        self._create_bar_chart(viz_frame, "1099 Income", 15000, 125000)
        self._create_bar_chart(viz_frame, "Investment", 8000, 125000)
        self._create_bar_chart(viz_frame, "Other", 7000, 125000)

    def _create_tax_bracket_section(self):
        """Create tax bracket information section"""
        section = ModernFrame(self)
        section.pack(fill="x", padx=20, pady=(0, 20))

        title = ModernLabel(
            section,
            text="📊 Tax Bracket Information",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title.pack(anchor="w", pady=(0, 15))

        info_frame = ctk.CTkFrame(section, fg_color="transparent")
        info_frame.pack(fill="x")

        ModernLabel(info_frame, text="Filing Status:", width=150).pack(side="left", padx=(0, 10))
        ModernLabel(info_frame, text="Single", font=ctk.CTkFont(weight="bold")).pack(side="left")

        bracket_frame = ctk.CTkFrame(section, fg_color="transparent")
        bracket_frame.pack(fill="x", pady=(10, 0))

        ModernLabel(bracket_frame, text="Tax Bracket:", width=150).pack(side="left", padx=(0, 10))
        ModernLabel(bracket_frame, text="22% (Marginal)", font=ctk.CTkFont(weight="bold")).pack(side="left")

        rate_frame = ctk.CTkFrame(section, fg_color="transparent")
        rate_frame.pack(fill="x", pady=(5, 0))

        ModernLabel(rate_frame, text="Effective Rate:", width=150).pack(side="left", padx=(0, 10))
        ModernLabel(rate_frame, text="14.59%", font=ctk.CTkFont(weight="bold")).pack(side="left")

        # Bracket details
        details_frame = ctk.CTkFrame(section, fg_color="transparent")
        details_frame.pack(fill="x", pady=(15, 0))

        details_title = ModernLabel(details_frame, text="Tax Bracket Details:", font=ctk.CTkFont(weight="bold"))
        details_title.pack(anchor="w", pady=(0, 10))

        brackets = [
            ("10% bracket", "$0 - $11,600", "$1,160"),
            ("12% bracket", "$11,600 - $47,150", "$4,266"),
            ("22% bracket", "$47,150 - $100,525", "$12,814"),
        ]

        for bracket, range_text, tax_text in brackets:
            bracket_row = ctk.CTkFrame(details_frame, fg_color="transparent")
            bracket_row.pack(fill="x", pady=(0, 5))

            ModernLabel(bracket_row, text=f"{bracket}: {range_text}", width=300).pack(side="left")
            ModernLabel(bracket_row, text=tax_text, font=ctk.CTkFont(weight="bold")).pack(side="right")

    def _create_year_comparison_section(self):
        """Create year-over-year comparison section"""
        section = ModernFrame(self)
        section.pack(fill="x", padx=20, pady=(0, 20))

        title = ModernLabel(
            section,
            text="📅 Year-Over-Year Comparison",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title.pack(anchor="w", pady=(0, 15))

        # Comparison table
        comp_frame = ctk.CTkFrame(section, fg_color="transparent")
        comp_frame.pack(fill="x")

        # Header row
        header_row = ctk.CTkFrame(comp_frame, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 10))

        ModernLabel(header_row, text="Metric", width=200).pack(side="left", padx=(0, 20))
        ModernLabel(header_row, text="2024", width=150, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 20))
        ModernLabel(header_row, text="2025", width=150, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 20))
        ModernLabel(header_row, text="Change", width=100, font=ctk.CTkFont(weight="bold")).pack(side="left")

        # Data rows
        comparisons = [
            ("Total Income", "$120,000", "$125,000", "+$5,000"),
            ("Total Deductions", "$26,500", "$28,500", "+$2,000"),
            ("Taxable Income", "$93,500", "$96,500", "+$3,000"),
            ("Total Tax", "$16,840", "$18,240", "+$1,400"),
            ("Effective Rate", "14.02%", "14.59%", "+0.57%"),
        ]

        for metric, val_2024, val_2025, change in comparisons:
            row = ctk.CTkFrame(comp_frame, fg_color="transparent")
            row.pack(fill="x", pady=(0, 5))

            ModernLabel(row, text=metric, width=200).pack(side="left", padx=(0, 20))
            ModernLabel(row, text=val_2024, width=150).pack(side="left", padx=(0, 20))
            ModernLabel(row, text=val_2025, width=150, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 20))
            
            color = "gray70"
            if change.startswith("-"):
                color = "green"
            elif change.startswith("+"):
                color = "orange"
            
            ModernLabel(row, text=change, text_color=color, width=100).pack(side="left")

    def _create_metric_card(self, parent, title: str, value: str, side: str = "top"):
        """Create a metric card"""
        card = ctk.CTkFrame(parent)
        card.pack(side=side, padx=5, pady=5, fill="x" if side == "top" else "both", expand=False)

        title_label = ModernLabel(card, text=title, text_color="gray60", font=ctk.CTkFont(size=10))
        title_label.pack(anchor="w", padx=10, pady=(10, 0))

        value_label = ModernLabel(card, text=value, font=ctk.CTkFont(size=14, weight="bold"))
        value_label.pack(anchor="w", padx=10, pady=(0, 10))

    def _create_detail_row(self, parent, label: str, value: str, tag: str = "default"):
        """Create a detail row"""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 8))

        ModernLabel(row, text=label, width=300).pack(side="left")
        
        # Color based on tag
        color = "white"
        if tag == "secondary":
            color = "gray70"
        elif tag == "success":
            color = "green"
        elif tag == "danger":
            color = "red"
        
        ModernLabel(row, text=value, text_color=color, font=ctk.CTkFont(weight="bold")).pack(side="right")

    def _create_deduction_row(self, parent, name: str, amount: str, description: str):
        """Create a deduction row"""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 10))

        # Name and amount
        header = ctk.CTkFrame(row, fg_color="transparent")
        header.pack(fill="x")

        ModernLabel(header, text=name, font=ctk.CTkFont(weight="bold")).pack(side="left")
        ModernLabel(header, text=amount, font=ctk.CTkFont(weight="bold")).pack(side="right")

        # Description
        desc_label = ModernLabel(row, text=description, text_color="gray70", font=ctk.CTkFont(size=10))
        desc_label.pack(anchor="w")

    def _create_income_row(self, parent, name: str, amount: str, source: str):
        """Create an income row"""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 10))

        # Name and amount
        header = ctk.CTkFrame(row, fg_color="transparent")
        header.pack(fill="x")

        ModernLabel(header, text=name, font=ctk.CTkFont(weight="bold")).pack(side="left")
        ModernLabel(header, text=amount, font=ctk.CTkFont(weight="bold")).pack(side="right")

        # Source
        source_label = ModernLabel(row, text=source, text_color="gray70", font=ctk.CTkFont(size=10))
        source_label.pack(anchor="w")

    def _create_bar_chart(self, parent, label: str, value: int, max_value: int):
        """Create a simple bar chart"""
        chart_row = ctk.CTkFrame(parent, fg_color="transparent")
        chart_row.pack(fill="x", pady=(0, 8))

        # Label
        label_frame = ctk.CTkFrame(chart_row, fg_color="transparent", width=100)
        label_frame.pack(side="left", padx=(0, 15))

        ModernLabel(label_frame, text=label).pack(anchor="w")

        # Bar
        bar_frame = ctk.CTkFrame(chart_row, fg_color="gray30", height=20, width=300)
        bar_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))

        percentage = (value / max_value) * 100
        filled_frame = ctk.CTkFrame(bar_frame, fg_color="#1f84c6", height=20)
        filled_frame.pack(side="left", fill="y", expand=False)
        filled_frame.configure(width=int(percentage * 3))

        # Percentage
        ModernLabel(chart_row, text=f"{percentage:.0f}% (${value:,})", width=120).pack(side="left")

    def _create_recommendation(self, parent, text: str):
        """Create a recommendation item"""
        rec_frame = ctk.CTkFrame(parent, fg_color="transparent")
        rec_frame.pack(fill="x", pady=(0, 8))

        bullet = ModernLabel(rec_frame, text="•", font=ctk.CTkFont(size=12))
        bullet.pack(side="left", padx=(0, 10))

        text_label = ModernLabel(rec_frame, text=text, text_color="gray70")
        text_label.pack(side="left", fill="x", expand=True)
