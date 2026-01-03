"""
Foreign Income and FBAR Reporting Page

A comprehensive page for managing foreign income, international tax obligations,
and FBAR (FinCEN Form 114) reporting requirements.

Features:
- Foreign income tracking and reporting
- FBAR filing requirements and tracking
- Foreign account information management
- Currency conversion and reporting
- Tax treaty and exclusion management
- IRS reporting form preparation
"""

import customtkinter as ctk
from typing import Optional, Any
from datetime import datetime

from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton, ModernScrollableFrame


class ForeignIncomeFBARPage(ModernFrame):
    """
    Foreign Income and FBAR Reporting Page
    
    Manages all aspects of foreign income reporting and FBAR filing requirements.
    """
    
    def __init__(
        self,
        master,
        config: Optional[Any] = None,
        tax_data: Optional[Any] = None,
        accessibility_service: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        self.config = config
        self.tax_data = tax_data
        self.accessibility_service = accessibility_service
        
        # Wrap content in scrollable frame for proper pack() compatibility
        scrollable = ModernScrollableFrame(self, fg_color="transparent")
        scrollable.pack(fill=ctk.BOTH, expand=True)
        
        # Create header
        self._create_header(scrollable)
        # Create toolbar
        self._create_toolbar(scrollable)
        # Create main content
        self._create_main_content(scrollable)
    
    def _create_header(self, parent):
        """Create page header."""
        header_frame = ModernFrame(parent, fg_color="transparent")
        header_frame.pack(fill=ctk.X, padx=20, pady=(20, 10))
        
        title_label = ModernLabel(
            header_frame,
            text="🌍 Foreign Income & FBAR Reporting",
            font=("Segoe UI", 24, "bold"),
            text_color="#FFFFFF"
        )
        title_label.pack(anchor=ctk.W)
        
        subtitle_label = ModernLabel(
            header_frame,
            text="Manage foreign income, international accounts, and FBAR filing requirements",
            font=("Segoe UI", 12),
            text_color="#A0A0A0"
        )
        subtitle_label.pack(anchor=ctk.W, pady=(5, 0))
    
    def _create_toolbar(self, parent):
        """Create toolbar with action buttons."""
        toolbar_frame = ModernFrame(parent, fg_color="transparent")
        toolbar_frame.pack(fill=ctk.X, padx=20, pady=(0, 10))
        
        button_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        button_frame.pack(side=ctk.LEFT, fill=ctk.X)
        
        add_income_btn = ModernButton(
            button_frame,
            text="+ Add Foreign Income",
            button_type="primary",
            width=180,
            height=36,
            command=self._action_add_foreign_income
        )
        add_income_btn.pack(side=ctk.LEFT, padx=(0, 10))
        
        add_account_btn = ModernButton(
            button_frame,
            text="+ Add Foreign Account",
            button_type="primary",
            width=180,
            height=36,
            command=self._action_add_foreign_account
        )
        add_account_btn.pack(side=ctk.LEFT, padx=5)
        
        check_fbar_btn = ModernButton(
            button_frame,
            text="📋 Check FBAR Status",
            button_type="secondary",
            width=160,
            height=36,
            command=self._action_check_fbar_status
        )
        check_fbar_btn.pack(side=ctk.LEFT, padx=5)
        
        # Progress bar
        progress_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        progress_frame.pack(side=ctk.RIGHT, fill=ctk.X, expand=True, padx=20)
        
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            width=200,
            height=8,
            progress_color="#28A745"
        )
        self.progress_bar.pack(side=ctk.LEFT, padx=(0, 10))
        self.progress_bar.set(0.70)
        
        self.status_label = ModernLabel(
            progress_frame,
            text="2 accounts, 1 income source",
            font=("Segoe UI", 10),
            text_color="#A0A0A0"
        )
        self.status_label.pack(side=ctk.RIGHT)
    
    def _create_main_content(self, parent):
        """Create tabbed interface."""
        content_frame = ctk.CTkFrame(parent, fg_color="#2B2B2B")
        content_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)
        
        self.tabview = ctk.CTkTabview(
            content_frame,
            text_color="#FFFFFF",
            segmented_button_fg_color="#1E1E1E",
            segmented_button_selected_color="#0066CC",
            fg_color="#2B2B2B"
        )
        self.tabview.pack(fill=ctk.BOTH, expand=True)
        
        self.tabview.add("Foreign Income")
        self.tabview.add("Foreign Accounts")
        self.tabview.add("FBAR Filing")
        self.tabview.add("Tax Treaties")
        self.tabview.add("Currency & Reporting")
        
        self._setup_foreign_income_tab()
        self._setup_foreign_accounts_tab()
        self._setup_fbar_filing_tab()
        self._setup_tax_treaties_tab()
        self._setup_currency_reporting_tab()
    
    def _setup_foreign_income_tab(self):
        """Setup Foreign Income tab."""
        tab = self.tabview.tab("Foreign Income")
        
        # Wrap tab content in scrollable frame
        scrollable = ModernScrollableFrame(tab, fg_color="transparent")
        scrollable.pack(fill=ctk.BOTH, expand=True)
        
        desc_label = ModernLabel(
            scrollable,
            text="Track and report all sources of foreign income",
            font=("Segoe UI", 11),
            text_color="#A0A0A0"
        )
        desc_label.pack(anchor=ctk.W, padx=15, pady=(15, 10))
        
        # Income sources frame
        income_frame = ctk.CTkFrame(scrollable, fg_color="#1E1E1E")
        income_frame.pack(fill=ctk.BOTH, expand=True, padx=15, pady=10)

        sources = [
            ("Consulting Services - Canada", "CAD 45,000", "Self-employment"),
            ("UK Investment Dividends", "GBP 8,500", "Portfolio income"),
            ("Singapore Employment", "SGD 120,000", "Wages/salary"),
        ]
        
        for source, amount, type_ in sources:
            source_frame = ctk.CTkFrame(income_frame, fg_color="#1E1E1E", height=60)
            source_frame.pack(fill=ctk.X, pady=5)
            
            left_frame = ctk.CTkFrame(source_frame, fg_color="transparent")
            left_frame.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True, padx=10, pady=5)
            
            source_label = ModernLabel(left_frame, text=source, font=("Segoe UI", 11, "bold"))
            source_label.pack(anchor=ctk.W)
            
            type_label = ModernLabel(left_frame, text=type_, font=("Segoe UI", 9), text_color="#A0A0A0")
            type_label.pack(anchor=ctk.W, pady=(0, 5))
            
            amount_label = ModernLabel(source_frame, text=amount, font=("Segoe UI", 12, "bold"), text_color="#2196F3")
            amount_label.pack(side=ctk.RIGHT, padx=10, pady=5)
    
    def _setup_foreign_accounts_tab(self):
        """Setup Foreign Accounts tab."""
        tab = self.tabview.tab("Foreign Accounts")
        
        # Wrap tab content in scrollable frame
        scrollable = ModernScrollableFrame(tab, fg_color="transparent")
        scrollable.pack(fill=ctk.BOTH, expand=True)
        
        desc_label = ModernLabel(
            scrollable,
            text="Track foreign financial accounts for FBAR and Form 8938",
            font=("Segoe UI", 11),
            text_color="#A0A0A0"
        )
        desc_label.pack(anchor=ctk.W, padx=15, pady=(15, 10))
        
        # Accounts frame
        accounts_frame = ctk.CTkFrame(scrollable, fg_color="#1E1E1E")
        accounts_frame.pack(fill=ctk.BOTH, expand=True, padx=15, pady=10)

        accounts = [
            ("Royal Bank of Canada - Savings", "Toronto, Canada", "CAD 125,000", "Yes"),
            ("Barclays Bank - Current Account", "London, UK", "GBP 45,000", "Yes"),
        ]
        
        for bank, location, balance, fbar in accounts:
            account_frame = ctk.CTkFrame(accounts_frame, fg_color="#1E1E1E", height=70)
            account_frame.pack(fill=ctk.X, pady=5)
            
            left_frame = ctk.CTkFrame(account_frame, fg_color="transparent")
            left_frame.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True, padx=10, pady=5)
            
            bank_label = ModernLabel(left_frame, text=bank, font=("Segoe UI", 11, "bold"))
            bank_label.pack(anchor=ctk.W)
            
            location_label = ModernLabel(left_frame, text=location, font=("Segoe UI", 9), text_color="#A0A0A0")
            location_label.pack(anchor=ctk.W, pady=(0, 5))
            
            right_frame = ctk.CTkFrame(account_frame, fg_color="transparent")
            right_frame.pack(side=ctk.RIGHT, fill=ctk.BOTH, padx=10, pady=5)
            
            balance_label = ModernLabel(right_frame, text=balance, font=("Segoe UI", 11, "bold"), text_color="#4CAF50")
            balance_label.pack(anchor=ctk.NE)
            
            fbar_label = ModernLabel(right_frame, text=f"FBAR Required: {fbar}", font=("Segoe UI", 9), text_color="#FF9800")
            fbar_label.pack(anchor=ctk.NE, pady=(0, 5))
    
    def _setup_fbar_filing_tab(self):
        """Setup FBAR Filing tab."""
        tab = self.tabview.tab("FBAR Filing")
        
        # Wrap tab content in scrollable frame
        scrollable = ModernScrollableFrame(tab, fg_color="transparent")
        scrollable.pack(fill=ctk.BOTH, expand=True)
        
        desc_label = ModernLabel(
            scrollable,
            text="Manage FBAR (Form 114) filing and compliance",
            font=("Segoe UI", 11),
            text_color="#A0A0A0"
        )
        desc_label.pack(anchor=ctk.W, padx=15, pady=(15, 10))
        
        # FBAR status frame
        fbar_frame = ctk.CTkFrame(scrollable, fg_color="#1E1E1E")
        fbar_frame.pack(fill=ctk.X, padx=15, pady=10)
        
        # Requirement check
        require_row = ctk.CTkFrame(fbar_frame, fg_color="transparent")
        require_row.pack(fill=ctk.X, padx=15, pady=10)
        
        require_label = ModernLabel(require_row, text="FBAR Filing Required:", font=("Segoe UI", 11))
        require_label.pack(side=ctk.LEFT)
        
        require_status = ModernLabel(
            require_row,
            text="✓ YES (Aggregate balance > $10,000)",
            font=("Segoe UI", 11),
            text_color="#FF9800"
        )
        require_status.pack(side=ctk.RIGHT)
        
        # Filing deadline
        deadline_row = ctk.CTkFrame(fbar_frame, fg_color="transparent")
        deadline_row.pack(fill=ctk.X, padx=15, pady=10)
        
        deadline_label = ModernLabel(deadline_row, text="Filing Deadline:", font=("Segoe UI", 11))
        deadline_label.pack(side=ctk.LEFT)
        
        deadline_status = ModernLabel(
            deadline_row,
            text="April 15, 2025 (Automatic 6-month extension available)",
            font=("Segoe UI", 11),
            text_color="#FF9800"
        )
        deadline_status.pack(side=ctk.RIGHT)
        
        # Filing status
        filed_row = ctk.CTkFrame(fbar_frame, fg_color="transparent")
        filed_row.pack(fill=ctk.X, padx=15, pady=10)
        
        filed_label = ModernLabel(filed_row, text="Filed Status:", font=("Segoe UI", 11))
        filed_label.pack(side=ctk.LEFT)
        
        filed_status = ModernLabel(
            filed_row,
            text="Not Filed (Due Date: 68 days remaining)",
            font=("Segoe UI", 11),
            text_color="#F44336"
        )
        filed_status.pack(side=ctk.RIGHT)
    
    def _setup_tax_treaties_tab(self):
        """Setup Tax Treaties tab."""
        tab = self.tabview.tab("Tax Treaties")
        
        # Wrap tab content in scrollable frame
        scrollable = ModernScrollableFrame(tab, fg_color="transparent")
        scrollable.pack(fill=ctk.BOTH, expand=True)
        
        desc_label = ModernLabel(
            scrollable,
            text="Apply applicable tax treaty benefits and exclusions",
            font=("Segoe UI", 11),
            text_color="#A0A0A0"
        )
        desc_label.pack(anchor=ctk.W, padx=15, pady=(15, 10))
        
        # Treaties frame
        treaties_frame = ctk.CTkFrame(scrollable, fg_color="#1E1E1E")
        treaties_frame.pack(fill=ctk.BOTH, expand=True, padx=15, pady=10)

        treaties = [
            ("US-Canada Tax Treaty", "Foreign Earned Income Exclusion", "Yes"),
            ("US-UK Tax Treaty", "Investment Credit", "Yes"),
            ("US-Singapore Tax Treaty", "Foreign Tax Credit", "Pending"),
        ]
        
        for treaty, benefit, status in treaties:
            treaty_frame = ctk.CTkFrame(treaties_frame, fg_color="#1E1E1E", height=60)
            treaty_frame.pack(fill=ctk.X, pady=5)
            
            left_frame = ctk.CTkFrame(treaty_frame, fg_color="transparent")
            left_frame.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True, padx=10, pady=5)
            
            treaty_label = ModernLabel(left_frame, text=treaty, font=("Segoe UI", 11, "bold"))
            treaty_label.pack(anchor=ctk.W)
            
            benefit_label = ModernLabel(left_frame, text=benefit, font=("Segoe UI", 10), text_color="#A0A0A0")
            benefit_label.pack(anchor=ctk.W, pady=(0, 5))
            
            status_label = ModernLabel(treaty_frame, text=status, font=("Segoe UI", 10, "bold"))
            status_label.pack(side=ctk.RIGHT, padx=10, pady=5)
    
    def _setup_currency_reporting_tab(self):
        """Setup Currency & Reporting tab."""
        tab = self.tabview.tab("Currency & Reporting")
        
        # Wrap tab content in scrollable frame
        scrollable = ModernScrollableFrame(tab, fg_color="transparent")
        scrollable.pack(fill=ctk.BOTH, expand=True)
        
        desc_label = ModernLabel(
            scrollable,
            text="Configure currency conversion and reporting preferences",
            font=("Segoe UI", 11),
            text_color="#A0A0A0"
        )
        desc_label.pack(anchor=ctk.W, padx=15, pady=(15, 10))
        
        # Settings frame
        settings_frame = ctk.CTkFrame(scrollable, fg_color="#1E1E1E")
        settings_frame.pack(fill=ctk.X, padx=15, pady=10)
        
        # Currency conversion method
        conv_row = ctk.CTkFrame(settings_frame, fg_color="transparent")
        conv_row.pack(fill=ctk.X, padx=15, pady=10)
        
        conv_label = ModernLabel(conv_row, text="Conversion Method:", font=("Segoe UI", 11))
        conv_label.pack(side=ctk.LEFT)
        
        conv_combo = ctk.CTkComboBox(
            conv_row,
            values=["Year-End Rate", "Average Rate", "Transaction Date Rate"],
            fg_color="#2B2B2B",
            button_color="#0066CC",
            text_color="#FFFFFF",
            state="readonly"
        )
        conv_combo.pack(side=ctk.RIGHT, fill=ctk.X, expand=True, padx=(10, 0))
        conv_combo.set("Year-End Rate")
        
        # Reporting currency
        report_row = ctk.CTkFrame(settings_frame, fg_color="transparent")
        report_row.pack(fill=ctk.X, padx=15, pady=10)
        
        report_label = ModernLabel(report_row, text="Reporting Currency:", font=("Segoe UI", 11))
        report_label.pack(side=ctk.LEFT)
        
        report_combo = ctk.CTkComboBox(
            report_row,
            values=["USD (US Dollar)", "EUR (Euro)", "GBP (British Pound)"],
            fg_color="#2B2B2B",
            button_color="#0066CC",
            text_color="#FFFFFF",
            state="readonly"
        )
        report_combo.pack(side=ctk.RIGHT, fill=ctk.X, expand=True, padx=(10, 0))
        report_combo.set("USD (US Dollar)")
    
    # Action Methods
    def _action_add_foreign_income(self):
        """Action: Add foreign income source."""
        print("[Foreign Income/FBAR] Add foreign income initiated")
    
    def _action_add_foreign_account(self):
        """Action: Add foreign account."""
        print("[Foreign Income/FBAR] Add foreign account initiated")
    
    def _action_check_fbar_status(self):
        """Action: Check FBAR filing status."""
        print("[Foreign Income/FBAR] Check FBAR status initiated")
