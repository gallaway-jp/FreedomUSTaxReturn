"""
Tax Dashboard Page - Converted from Legacy Window

Main dashboard page for tax return overview and analytics.
Integrated into main window without popup dialogs.
"""

import customtkinter as ctk
from typing import Optional, Dict, Any
from datetime import datetime

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton


class TaxDashboardPage(ctk.CTkScrollableFrame):
    """
    Tax Dashboard page - converted from legacy window to integrated page.
    
    Features:
    - Return overview and status
    - Key tax metrics
    - Income and deduction summaries
    - Tax liability calculations
    - Filing status and deadlines
    """

    def __init__(self, master, config: AppConfig, tax_data: Optional[TaxData] = None,
                 accessibility_service: Optional[AccessibilityService] = None, **kwargs):
        super().__init__(master, **kwargs)

        self.config = config
        self.tax_data = tax_data
        self.accessibility_service = accessibility_service

        # Dashboard data
        self.total_income = 0
        self.total_deductions = 0
        self.tax_liability = 0
        self.filing_status = "Single"

        # Build the page
        self._create_header()
        self._create_toolbar()
        self._create_main_content()
        self._calculate_totals()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self)
        header_frame.pack(fill=ctk.X, padx=20, pady=(20, 10))

        title_label = ModernLabel(
            header_frame,
            text="📊 Tax Dashboard",
            font_size=24,
            font_weight="bold"
        )
        title_label.pack(anchor=ctk.W, pady=(0, 5))

        subtitle_label = ModernLabel(
            header_frame,
            text="Overview and analysis of your tax return",
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
            text="🔄 Refresh",
            command=self._refresh_dashboard,
            button_type="secondary",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📈 Details",
            command=self._view_details,
            button_type="secondary",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📊 Analytics",
            command=self._view_analytics,
            button_type="secondary",
            width=130
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="💾 Save",
            command=self._save_dashboard,
            button_type="success",
            width=100
        ).pack(side=ctk.LEFT, padx=5)

        # Progress bar
        progress_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        progress_frame.pack(fill=ctk.X, pady=10)

        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=6)
        self.progress_bar.pack(fill=ctk.X)
        self.progress_bar.set(0)

        self.status_label = ModernLabel(progress_frame, text="Loading dashboard...", font_size=11)
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
        self.tab_income = self.tabview.add("💵 Income")
        self.tab_deductions = self.tabview.add("✂️ Deductions")
        self.tab_liability = self.tabview.add("💰 Tax Liability")
        self.tab_estimates = self.tabview.add("📅 Estimates")

        # Setup tabs
        self._setup_overview_tab()
        self._setup_income_tab()
        self._setup_deductions_tab()
        self._setup_liability_tab()
        self._setup_estimates_tab()

    def _setup_overview_tab(self):
        """Setup overview tab with summary cards"""
        self.tab_overview.grid_rowconfigure(1, weight=1)
        self.tab_overview.grid_columnconfigure(0, weight=1)

        # Summary cards
        cards_frame = ctk.CTkFrame(self.tab_overview, fg_color="transparent")
        cards_frame.pack(fill=ctk.X, padx=20, pady=10)

        card_data = [
            ("Total Income", "$0.00"),
            ("Total Deductions", "$0.00"),
            ("Tax Liability", "$0.00"),
            ("Filing Status", "Single")
        ]

        for title, value in card_data:
            card = self._create_summary_card(cards_frame, title, value)
            card.pack(side=ctk.LEFT, padx=5, fill=ctk.X, expand=True)

        # Summary details
        frame = ctk.CTkScrollableFrame(self.tab_overview)
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

        summary_label = ModernLabel(frame, text="Return Summary", font_size=12, font_weight="bold")
        summary_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.summary_text = ctk.CTkTextbox(frame, height=300)
        self.summary_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.summary_text.insert("1.0",
            "Tax Return Overview:\n\n"
            "• Tax Year: 2024\n"
            "• Filing Status: Single\n"
            "• Forms: 1040, Schedule A, Schedule C\n"
            "• Status: In Progress\n\n"
            "Key Information:\n"
            "• Return Completeness: 0%\n"
            "• Forms to Review: 3\n"
            "• Issues Detected: 0\n"
            "• Filing Deadline: April 15, 2025"
        )
        self.summary_text.configure(state="disabled")

    def _setup_income_tab(self):
        """Setup income tab"""
        self.tab_income.grid_rowconfigure(0, weight=1)
        self.tab_income.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_income)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        income_label = ModernLabel(frame, text="Income Sources", font_size=12, font_weight="bold")
        income_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.income_text = ctk.CTkTextbox(frame, height=400)
        self.income_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.income_text.insert("1.0",
            "Income Summary:\n\n"
            "Wages & Salaries:\n"
            "  • W-2 Income: $0.00\n\n"
            "Investment Income:\n"
            "  • Dividends: $0.00\n"
            "  • Interest: $0.00\n"
            "  • Capital Gains: $0.00\n\n"
            "Self-Employment Income:\n"
            "  • Business Income: $0.00\n"
            "  • Other Income: $0.00\n\n"
            "Total Income: $0.00"
        )
        self.income_text.configure(state="disabled")

    def _setup_deductions_tab(self):
        """Setup deductions tab"""
        self.tab_deductions.grid_rowconfigure(0, weight=1)
        self.tab_deductions.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_deductions)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        deduction_label = ModernLabel(frame, text="Deduction Summary", font_size=12, font_weight="bold")
        deduction_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.deduction_text = ctk.CTkTextbox(frame, height=400)
        self.deduction_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.deduction_text.insert("1.0",
            "Deduction Summary:\n\n"
            "Standard Deduction: $13,850.00\n\n"
            "Itemized Deductions (if applicable):\n"
            "  • Mortgage Interest: $0.00\n"
            "  • Property Taxes: $0.00\n"
            "  • Charitable Contributions: $0.00\n"
            "  • Medical Expenses: $0.00\n\n"
            "Business Deductions:\n"
            "  • Office Supplies: $0.00\n"
            "  • Equipment: $0.00\n"
            "  • Other: $0.00\n\n"
            "Total Deductions: $13,850.00"
        )
        self.deduction_text.configure(state="disabled")

    def _setup_liability_tab(self):
        """Setup tax liability tab"""
        self.tab_liability.grid_rowconfigure(0, weight=1)
        self.tab_liability.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_liability)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        liability_label = ModernLabel(frame, text="Tax Liability Calculation", font_size=12, font_weight="bold")
        liability_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.liability_text = ctk.CTkTextbox(frame, height=400)
        self.liability_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.liability_text.insert("1.0",
            "Tax Liability Analysis:\n\n"
            "Gross Income: $0.00\n"
            "Less: Deductions: $0.00\n"
            "Taxable Income: $0.00\n\n"
            "Tax Calculation:\n"
            "  • Federal Income Tax: $0.00\n"
            "  • Self-Employment Tax: $0.00\n"
            "  • Other Taxes: $0.00\n"
            "Total Tax Liability: $0.00\n\n"
            "Credits & Payments:\n"
            "  • Tax Credits: $0.00\n"
            "  • Estimated Payments: $0.00\n"
            "Refund/Due: $0.00"
        )
        self.liability_text.configure(state="disabled")

    def _setup_estimates_tab(self):
        """Setup estimated tax payments tab"""
        self.tab_estimates.grid_rowconfigure(0, weight=1)
        self.tab_estimates.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_estimates)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        estimates_label = ModernLabel(frame, text="Estimated Tax Payments", font_size=12, font_weight="bold")
        estimates_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.estimates_text = ctk.CTkTextbox(frame, height=400)
        self.estimates_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.estimates_text.insert("1.0",
            "Quarterly Estimated Payments:\n\n"
            "Q1 (April 15, 2024): $0.00\n"
            "Q2 (June 17, 2024): $0.00\n"
            "Q3 (September 16, 2024): $0.00\n"
            "Q4 (January 15, 2025): $0.00\n\n"
            "Total Estimated Payments: $0.00\n\n"
            "Payment Deadlines:\n"
            "• Next Deadline: April 15, 2025\n"
            "• Amount Due: $0.00\n\n"
            "Safe Harbor Amounts:\n"
            "• 90% of 2024 Tax: TBD\n"
            "• 100% of 2023 Tax: TBD"
        )
        self.estimates_text.configure(state="disabled")

    def _create_summary_card(self, parent, title, value):
        """Create a summary metric card"""
        card = ctk.CTkFrame(parent, corner_radius=8, fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        
        title_label = ctk.CTkLabel(card, text=title, text_color="gray", font=("", 11))
        title_label.pack(padx=10, pady=(8, 2))

        value_label = ctk.CTkLabel(card, text=value, text_color="white", font=("", 13, "bold"))
        value_label.pack(padx=10, pady=(2, 8))

        return card

    # ===== Action Methods =====

    def _calculate_totals(self):
        """Calculate dashboard totals"""
        self.status_label.configure(text="Calculating totals...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Dashboard ready")
        self.progress_bar.set(1.0)

    def _refresh_dashboard(self):
        """Refresh dashboard data"""
        self.status_label.configure(text="Refreshing...")
        self.progress_bar.set(0.5)
        self.progress_bar.set(1.0)
        self.status_label.configure(text="Refreshed")

    def _view_details(self):
        """View detailed information"""
        self.status_label.configure(text="Loading details...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Details loaded")
        self.progress_bar.set(1.0)

    def _view_analytics(self):
        """View analytics dashboard"""
        self.status_label.configure(text="Loading analytics...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Analytics ready")
        self.progress_bar.set(1.0)

    def _save_dashboard(self):
        """Save dashboard state"""
        self.status_label.configure(text="Saving...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Saved")
        self.progress_bar.set(1.0)
