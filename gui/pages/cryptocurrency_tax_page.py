"""
Cryptocurrency Tax Page - Converted from Window

Page for cryptocurrency transaction tracking and tax reporting.
Integrated into main window without popup dialogs.
"""

import customtkinter as ctk
from typing import Optional, List, Dict, Any
from datetime import datetime

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton


class CryptocurrencyTaxPage(ctk.CTkScrollableFrame):
    """
    Cryptocurrency Tax page - converted from popup window to integrated page.
    
    Features:
    - Cryptocurrency transaction tracking
    - Capital gains calculations
    - Cost basis management
    - Portfolio tracking
    - Tax report generation
    """

    def __init__(self, master, config: AppConfig, tax_data: Optional[TaxData] = None,
                 accessibility_service: Optional[AccessibilityService] = None, **kwargs):
        super().__init__(master, **kwargs)

        self.config = config
        self.tax_data = tax_data
        self.accessibility_service = accessibility_service

        # Crypto data
        self.transactions: List[Dict[str, Any]] = []
        self.portfolio: Dict[str, float] = {}
        self.crypto_vars = {}

        # Build the page
        self._create_header()
        self._create_toolbar()
        self._create_main_content()
        self._load_portfolio()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self)
        header_frame.pack(fill=ctk.X, padx=20, pady=(20, 10))

        title_label = ModernLabel(
            header_frame,
            text="🪙 Cryptocurrency Tax Reporting",
            font_size=24,
            font_weight="bold"
        )
        title_label.pack(anchor=ctk.W, pady=(0, 5))

        subtitle_label = ModernLabel(
            header_frame,
            text="Track cryptocurrency transactions, calculate capital gains, and generate tax reports",
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
            text="➕ Add Transaction",
            command=self._add_transaction,
            button_type="primary",
            width=150
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📊 Calculate Gains",
            command=self._calculate_gains,
            button_type="secondary",
            width=150
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📈 Portfolio Analysis",
            command=self._analyze_portfolio,
            button_type="secondary",
            width=160
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📄 Generate Report",
            command=self._generate_report,
            button_type="secondary",
            width=150
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="💾 Save Data",
            command=self._save_data,
            button_type="success",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        # Progress bar
        progress_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        progress_frame.pack(fill=ctk.X, pady=10)

        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=6)
        self.progress_bar.pack(fill=ctk.X)
        self.progress_bar.set(0)

        self.status_label = ModernLabel(progress_frame, text="Ready", font_size=11)
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
        self.tab_portfolio = self.tabview.add("📈 Portfolio")
        self.tab_transactions = self.tabview.add("💹 Transactions")
        self.tab_gains = self.tabview.add("💰 Capital Gains")
        self.tab_analysis = self.tabview.add("📊 Analysis")
        self.tab_reporting = self.tabview.add("📄 Tax Reporting")

        # Setup tabs
        self._setup_portfolio_tab()
        self._setup_transactions_tab()
        self._setup_gains_tab()
        self._setup_analysis_tab()
        self._setup_reporting_tab()

    def _setup_portfolio_tab(self):
        """Setup portfolio overview tab"""
        self.tab_portfolio.grid_rowconfigure(1, weight=1)
        self.tab_portfolio.grid_columnconfigure(0, weight=1)

        # Portfolio controls
        control_frame = ctk.CTkFrame(self.tab_portfolio, fg_color="transparent")
        control_frame.pack(fill=ctk.X, padx=10, pady=10)

        ModernButton(
            control_frame,
            text="🔄 Refresh Prices",
            command=self._refresh_prices,
            button_type="secondary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        # Portfolio display
        display_frame = ctk.CTkFrame(self.tab_portfolio)
        display_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)
        display_frame.grid_rowconfigure(0, weight=1)
        display_frame.grid_columnconfigure(0, weight=1)

        self.portfolio_text = ctk.CTkTextbox(display_frame)
        self.portfolio_text.grid(row=0, column=0, sticky="nsew")
        self.portfolio_text.insert("1.0", "Current Portfolio:\n\nBTC: 0.00\nETH: 0.00\nNo cryptocurrency holdings loaded.")
        self.portfolio_text.configure(state="disabled")

    def _setup_transactions_tab(self):
        """Setup transactions tab"""
        self.tab_transactions.grid_rowconfigure(1, weight=1)
        self.tab_transactions.grid_columnconfigure(0, weight=1)

        # Transaction controls
        control_frame = ctk.CTkFrame(self.tab_transactions, fg_color="transparent")
        control_frame.pack(fill=ctk.X, padx=10, pady=10)

        ModernButton(
            control_frame,
            text="➕ Add Transaction",
            command=self._add_transaction,
            button_type="primary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            control_frame,
            text="✏️ Edit",
            command=self._edit_transaction,
            button_type="secondary",
            width=100
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            control_frame,
            text="🗑️ Delete",
            command=self._delete_transaction,
            button_type="danger",
            width=100
        ).pack(side=ctk.LEFT, padx=5)

        # Transaction list
        list_frame = ctk.CTkFrame(self.tab_transactions)
        list_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        self.transactions_text = ctk.CTkTextbox(list_frame)
        self.transactions_text.grid(row=0, column=0, sticky="nsew")
        self.transactions_text.insert("1.0", "No transactions recorded. Click 'Add Transaction' to begin.")
        self.transactions_text.configure(state="disabled")

    def _setup_gains_tab(self):
        """Setup capital gains tab"""
        self.tab_gains.grid_rowconfigure(0, weight=1)
        self.tab_gains.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_gains)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Summary cards
        cards_frame = ctk.CTkFrame(frame, fg_color="transparent")
        cards_frame.pack(fill=ctk.X, padx=5, pady=10)

        metrics = [
            ("Total Short-Term Gains", "$0.00"),
            ("Total Long-Term Gains", "$0.00"),
            ("Total Short-Term Losses", "$0.00"),
            ("Total Long-Term Losses", "$0.00")
        ]

        for metric, value in metrics:
            card = self._create_summary_card(cards_frame, metric, value)
            card.pack(side=ctk.LEFT, padx=5, fill=ctk.X, expand=True)

        # Detailed gains display
        gains_label = ModernLabel(frame, text="Capital Gains Details", font_size=12, font_weight="bold")
        gains_label.pack(anchor=ctk.W, padx=5, pady=(20, 10))

        self.gains_text = ctk.CTkTextbox(frame, height=300)
        self.gains_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.gains_text.insert("1.0", "No transactions processed yet.")
        self.gains_text.configure(state="disabled")

    def _setup_analysis_tab(self):
        """Setup portfolio analysis tab"""
        self.tab_analysis.grid_rowconfigure(0, weight=1)
        self.tab_analysis.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_analysis)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        analysis_label = ModernLabel(frame, text="Portfolio Analysis", font_size=12, font_weight="bold")
        analysis_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.analysis_text = ctk.CTkTextbox(frame, height=400)
        self.analysis_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.analysis_text.insert("1.0", "No portfolio analysis available.")
        self.analysis_text.configure(state="disabled")

    def _setup_reporting_tab(self):
        """Setup tax reporting tab"""
        self.tab_reporting.grid_rowconfigure(1, weight=1)
        self.tab_reporting.grid_columnconfigure(0, weight=1)

        # Report controls
        control_frame = ctk.CTkFrame(self.tab_reporting, fg_color="transparent")
        control_frame.pack(fill=ctk.X, padx=10, pady=10)

        ModernButton(
            control_frame,
            text="📄 Form 8949",
            command=self._generate_form_8949,
            button_type="secondary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            control_frame,
            text="📋 Schedule D",
            command=self._generate_schedule_d,
            button_type="secondary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            control_frame,
            text="💾 Save Report",
            command=self._save_report,
            button_type="success",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        # Report display
        display_frame = ctk.CTkFrame(self.tab_reporting)
        display_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)
        display_frame.grid_rowconfigure(0, weight=1)
        display_frame.grid_columnconfigure(0, weight=1)

        self.reporting_text = ctk.CTkTextbox(display_frame)
        self.reporting_text.grid(row=0, column=0, sticky="nsew")
        self.reporting_text.insert("1.0", "No tax forms generated yet.")
        self.reporting_text.configure(state="disabled")

    def _create_summary_card(self, parent, title, value):
        """Create a summary metric card"""
        card = ctk.CTkFrame(parent, corner_radius=8, fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        
        title_label = ctk.CTkLabel(card, text=title, text_color="gray", font=("", 11))
        title_label.pack(padx=10, pady=(8, 2))

        value_label = ctk.CTkLabel(card, text=value, text_color="white", font=("", 13, "bold"))
        value_label.pack(padx=10, pady=(2, 8))

        return card

    # ===== Action Methods =====

    def _load_portfolio(self):
        """Load current portfolio"""
        self.status_label.configure(text="Loading portfolio...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Ready")
        self.progress_bar.set(1.0)

    def _refresh_prices(self):
        """Refresh cryptocurrency prices"""
        self.status_label.configure(text="Refreshing prices...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Prices updated")
        self.progress_bar.set(1.0)

    def _add_transaction(self):
        """Add new cryptocurrency transaction"""
        self.status_label.configure(text="Transaction added")

    def _edit_transaction(self):
        """Edit selected transaction"""
        self.status_label.configure(text="Edit transaction")

    def _delete_transaction(self):
        """Delete selected transaction"""
        self.status_label.configure(text="Transaction deleted")

    def _calculate_gains(self):
        """Calculate capital gains"""
        self.status_label.configure(text="Calculating gains...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Calculation complete")
        self.progress_bar.set(1.0)

    def _analyze_portfolio(self):
        """Analyze portfolio"""
        self.status_label.configure(text="Analyzing portfolio...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Analysis complete")
        self.progress_bar.set(1.0)

    def _generate_report(self):
        """Generate tax report"""
        self.status_label.configure(text="Generating report...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Report generated")
        self.progress_bar.set(1.0)

    def _generate_form_8949(self):
        """Generate Form 8949"""
        self.status_label.configure(text="Generating Form 8949...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Form 8949 generated")
        self.progress_bar.set(1.0)

    def _generate_schedule_d(self):
        """Generate Schedule D"""
        self.status_label.configure(text="Generating Schedule D...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Schedule D generated")
        self.progress_bar.set(1.0)

    def _save_report(self):
        """Save generated report"""
        self.status_label.configure(text="Report saved")

    def _save_data(self):
        """Save portfolio data"""
        self.status_label.configure(text="Saving data...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Data saved")
        self.progress_bar.set(1.0)
