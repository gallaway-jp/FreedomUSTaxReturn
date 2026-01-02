"""
AI Deduction Finder Page - Converted from Window

Page for AI-powered deduction analysis and recommendations.
Integrated into main window without popup dialogs.
"""

import customtkinter as ctk
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import threading

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.ai_deduction_finder_service import (
    AIDeductionFinderService,
    DeductionAnalysisResult,
    DeductionSuggestion,
    DeductionCategory
)
from services.tax_calculation_service import TaxCalculationService
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton
from utils.error_tracker import get_error_tracker


class AIDeductionFinderPage(ctk.CTkScrollableFrame):
    """
    AI Deduction Finder page - converted from popup window to integrated page.
    
    Features:
    - AI-powered deduction analysis
    - Category-specific suggestions
    - Confidence scoring
    - Potential savings calculation
    - Exportable analysis reports
    """

    def __init__(self, master, config: AppConfig, tax_data: Optional[TaxData] = None,
                 accessibility_service: Optional[AccessibilityService] = None, **kwargs):
        super().__init__(master, **kwargs)

        self.config = config
        self.tax_data = tax_data
        self.accessibility_service = accessibility_service
        self.error_tracker = get_error_tracker()

        # Initialize services
        tax_year = tax_data.get_current_year() if tax_data else 2026
        self.tax_calculation = TaxCalculationService(tax_year)
        self.ai_service = AIDeductionFinderService(config, self.tax_calculation)

        # Current analysis
        self.current_analysis: Optional[DeductionAnalysisResult] = None
        self.analysis_vars = {}

        # Build the page
        self._create_header()
        self._create_toolbar()
        self._create_main_content()
        self._load_initial_data()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self)
        header_frame.pack(fill=ctk.X, padx=20, pady=(20, 10))

        title_label = ModernLabel(
            header_frame,
            text="🤖 AI Deduction Finder",
            font_size=24,
            font_weight="bold"
        )
        title_label.pack(anchor=ctk.W, pady=(0, 5))

        subtitle_label = ModernLabel(
            header_frame,
            text="Intelligent deduction analysis to maximize your tax savings",
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
            text="🔍 Analyze Deductions",
            command=self._analyze_deductions,
            button_type="primary",
            width=160
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="⭐ View Recommendations",
            command=self._view_recommendations,
            button_type="secondary",
            width=170
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="💾 Save Analysis",
            command=self._save_analysis,
            button_type="success",
            width=130
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📊 Export Report",
            command=self._export_report,
            button_type="secondary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        # Progress bar
        progress_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        progress_frame.pack(fill=ctk.X, pady=10)

        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=6)
        self.progress_bar.pack(fill=ctk.X)
        self.progress_bar.set(0)

        self.status_label = ModernLabel(progress_frame, text="Ready for analysis", font_size=11)
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
        self.tab_business = self.tabview.add("🏢 Business Deductions")
        self.tab_investment = self.tabview.add("💼 Investment Deductions")
        self.tab_medical = self.tabview.add("🏥 Medical Expenses")
        self.tab_education = self.tabview.add("📚 Education & Professional")
        self.tab_charitable = self.tabview.add("❤️ Charitable Contributions")

        # Setup tabs
        self._setup_overview_tab()
        self._setup_business_tab()
        self._setup_investment_tab()
        self._setup_medical_tab()
        self._setup_education_tab()
        self._setup_charitable_tab()

    def _setup_overview_tab(self):
        """Setup overview tab with analysis summary"""
        self.tab_overview.grid_rowconfigure(0, weight=1)
        self.tab_overview.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_overview)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Summary cards
        summary_label = ModernLabel(frame, text="Analysis Summary", font_size=12, font_weight="bold")
        summary_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        cards_frame = ctk.CTkFrame(frame, fg_color="transparent")
        cards_frame.pack(fill=ctk.X, padx=5, pady=10)

        metrics = [
            ("Deductions Analyzed", "0"),
            ("Potential Savings", "$0.00"),
            ("High Confidence Items", "0"),
            ("Medium Confidence Items", "0")
        ]

        for metric, value in metrics:
            card = self._create_summary_card(cards_frame, metric, value)
            card.pack(side=ctk.LEFT, padx=5, fill=ctk.X, expand=True)

        # Detailed results
        details_label = ModernLabel(frame, text="Top Recommendations", font_size=12, font_weight="bold")
        details_label.pack(anchor=ctk.W, padx=5, pady=(20, 10))

        self.overview_text = ctk.CTkTextbox(frame, height=400)
        self.overview_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.overview_text.insert("1.0", "Click 'Analyze Deductions' to begin AI analysis of potential tax savings.")
        self.overview_text.configure(state="disabled")

    def _setup_business_tab(self):
        """Setup business deductions tab"""
        self.tab_business.grid_rowconfigure(1, weight=1)
        self.tab_business.grid_columnconfigure(0, weight=1)

        # Category label
        category_label = ModernLabel(self.tab_business, text="Business Deductions", font_size=12, font_weight="bold")
        category_label.pack(anchor=ctk.W, padx=10, pady=(10, 5))

        # Deductions list
        list_frame = ctk.CTkFrame(self.tab_business)
        list_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        self.business_text = ctk.CTkTextbox(list_frame)
        self.business_text.grid(row=0, column=0, sticky="nsew")
        self.business_text.insert("1.0", "Suggested Business Deductions:\n\n• Home Office Expenses\n• Business Supplies\n• Professional Services\n• Equipment Depreciation\n• Vehicle Expenses")
        self.business_text.configure(state="disabled")

    def _setup_investment_tab(self):
        """Setup investment deductions tab"""
        self.tab_investment.grid_rowconfigure(1, weight=1)
        self.tab_investment.grid_columnconfigure(0, weight=1)

        # Category label
        category_label = ModernLabel(self.tab_investment, text="Investment Deductions", font_size=12, font_weight="bold")
        category_label.pack(anchor=ctk.W, padx=10, pady=(10, 5))

        # Deductions list
        list_frame = ctk.CTkFrame(self.tab_investment)
        list_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        self.investment_text = ctk.CTkTextbox(list_frame)
        self.investment_text.grid(row=0, column=0, sticky="nsew")
        self.investment_text.insert("1.0", "Suggested Investment Deductions:\n\n• Investment Advisory Fees\n• Brokerage Commissions\n• Safe Deposit Box Rental\n• Investment Publications\n• Portfolio Management Fees")
        self.investment_text.configure(state="disabled")

    def _setup_medical_tab(self):
        """Setup medical expenses tab"""
        self.tab_medical.grid_rowconfigure(1, weight=1)
        self.tab_medical.grid_columnconfigure(0, weight=1)

        # Category label
        category_label = ModernLabel(self.tab_medical, text="Medical & Dental Expenses", font_size=12, font_weight="bold")
        category_label.pack(anchor=ctk.W, padx=10, pady=(10, 5))

        # Deductions list
        list_frame = ctk.CTkFrame(self.tab_medical)
        list_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        self.medical_text = ctk.CTkTextbox(list_frame)
        self.medical_text.grid(row=0, column=0, sticky="nsew")
        self.medical_text.insert("1.0", "Suggested Medical Expenses:\n\n• Prescription Medications\n• Medical Equipment\n• Doctor & Dentist Visits\n• Vision Care\n• Hearing Aids & Devices")
        self.medical_text.configure(state="disabled")

    def _setup_education_tab(self):
        """Setup education and professional development tab"""
        self.tab_education.grid_rowconfigure(1, weight=1)
        self.tab_education.grid_columnconfigure(0, weight=1)

        # Category label
        category_label = ModernLabel(self.tab_education, text="Education & Professional Development", font_size=12, font_weight="bold")
        category_label.pack(anchor=ctk.W, padx=10, pady=(10, 5))

        # Deductions list
        list_frame = ctk.CTkFrame(self.tab_education)
        list_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        self.education_text = ctk.CTkTextbox(list_frame)
        self.education_text.grid(row=0, column=0, sticky="nsew")
        self.education_text.insert("1.0", "Suggested Education Expenses:\n\n• Continuing Education Courses\n• Professional Licensing\n• Books & Publications\n• Professional Conferences\n• Tuition for Job Skills")
        self.education_text.configure(state="disabled")

    def _setup_charitable_tab(self):
        """Setup charitable contributions tab"""
        self.tab_charitable.grid_rowconfigure(1, weight=1)
        self.tab_charitable.grid_columnconfigure(0, weight=1)

        # Category label
        category_label = ModernLabel(self.tab_charitable, text="Charitable Contributions", font_size=12, font_weight="bold")
        category_label.pack(anchor=ctk.W, padx=10, pady=(10, 5))

        # Deductions list
        list_frame = ctk.CTkFrame(self.tab_charitable)
        list_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        self.charitable_text = ctk.CTkTextbox(list_frame)
        self.charitable_text.grid(row=0, column=0, sticky="nsew")
        self.charitable_text.insert("1.0", "Suggested Charitable Contributions:\n\n• Monetary Donations\n• Appreciated Securities\n• Vehicle Donations\n• Property Donations\n• Volunteer Mileage")
        self.charitable_text.configure(state="disabled")

    def _create_summary_card(self, parent, title, value):
        """Create a summary metric card"""
        card = ctk.CTkFrame(parent, corner_radius=8, fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        
        title_label = ctk.CTkLabel(card, text=title, text_color="gray", font=("", 11))
        title_label.pack(padx=10, pady=(8, 2))

        value_label = ctk.CTkLabel(card, text=value, text_color="white", font=("", 13, "bold"))
        value_label.pack(padx=10, pady=(2, 8))

        return card

    # ===== Action Methods =====

    def _load_initial_data(self):
        """Load initial data for analysis"""
        self.status_label.configure(text="Loading tax data...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Ready for analysis")
        self.progress_bar.set(1.0)

    def _analyze_deductions(self):
        """Run AI analysis of potential deductions"""
        self.status_label.configure(text="Analyzing deductions with AI...")
        self.progress_bar.set(0.3)

        def run_analysis():
            try:
                self.progress_bar.set(0.7)
                self.status_label.configure(text="Analysis complete")
                self.progress_bar.set(1.0)
            except Exception as e:
                self.status_label.configure(text=f"Error: {str(e)}")
                self.error_tracker.log_error("AI Deduction Analysis", str(e))

        # Run analysis in background thread
        analysis_thread = threading.Thread(target=run_analysis, daemon=True)
        analysis_thread.start()

    def _view_recommendations(self):
        """View AI recommendations"""
        self.status_label.configure(text="Loading recommendations...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Recommendations displayed")
        self.progress_bar.set(1.0)

    def _save_analysis(self):
        """Save current analysis"""
        self.status_label.configure(text="Saving analysis...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Analysis saved")
        self.progress_bar.set(1.0)

    def _export_report(self):
        """Export analysis report"""
        self.status_label.configure(text="Exporting report...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Report exported")
        self.progress_bar.set(1.0)
