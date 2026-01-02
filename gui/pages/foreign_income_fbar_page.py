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


class ModernButton(ctk.CTkButton):
    """Custom button with type variants."""
    
    def __init__(self, *args, button_type: str = "primary", **kwargs):
        colors = {
            "primary": ("#0066CC", "#0052A3"),
            "secondary": ("#666666", "#4D4D4D"),
            "success": ("#28A745", "#1E8449"),
            "danger": ("#DC3545", "#C82333"),
        }
        
        fg_color, hover_color = colors.get(button_type, colors["primary"])
        kwargs.update({"fg_color": fg_color, "hover_color": hover_color, "text_color": "white"})
        super().__init__(*args, **kwargs)


class ModernFrame(ctk.CTkFrame):
    """Custom frame with consistent styling."""
    pass


class ModernLabel(ctk.CTkLabel):
    """Custom label with consistent styling."""
    pass


class ForeignIncomeFBARPage(ctk.CTkScrollableFrame):
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
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._create_header()
        self._create_toolbar()
        self._create_main_content()
    
    def _create_header(self):
        """Create page header."""
        header_frame = ModernFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ModernLabel(
            header_frame,
            text="🌍 Foreign Income & FBAR Reporting",
            font=("Segoe UI", 24, "bold"),
            text_color="#FFFFFF"
        )
        title_label.grid(row=0, column=0, sticky="w")
        
        subtitle_label = ModernLabel(
            header_frame,
            text="Manage foreign income, international accounts, and FBAR filing requirements",
            font=("Segoe UI", 12),
            text_color="#A0A0A0"
        )
        subtitle_label.grid(row=1, column=0, sticky="w", pady=(5, 0))
    
    def _create_toolbar(self):
        """Create toolbar with action buttons."""
        toolbar_frame = ModernFrame(self, fg_color="transparent")
        toolbar_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(0, 10))
        toolbar_frame.grid_columnconfigure(1, weight=1)
        
        button_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        button_frame.grid(row=0, column=0, sticky="w")
        
        add_income_btn = ModernButton(
            button_frame,
            text="+ Add Foreign Income",
            button_type="primary",
            width=180,
            height=36,
            command=self._action_add_foreign_income
        )
        add_income_btn.grid(row=0, column=0, padx=(0, 10))
        
        add_account_btn = ModernButton(
            button_frame,
            text="+ Add Foreign Account",
            button_type="primary",
            width=180,
            height=36,
            command=self._action_add_foreign_account
        )
        add_account_btn.grid(row=0, column=1, padx=5)
        
        check_fbar_btn = ModernButton(
            button_frame,
            text="📋 Check FBAR Status",
            button_type="secondary",
            width=160,
            height=36,
            command=self._action_check_fbar_status
        )
        check_fbar_btn.grid(row=0, column=2, padx=5)
        
        # Progress bar
        progress_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        progress_frame.grid(row=0, column=1, sticky="e")
        
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            width=200,
            height=8,
            progress_color="#28A745"
        )
        self.progress_bar.grid(row=0, column=0, sticky="e")
        self.progress_bar.set(0.70)
        
        self.status_label = ModernLabel(
            progress_frame,
            text="2 accounts, 1 income source",
            font=("Segoe UI", 10),
            text_color="#A0A0A0"
        )
        self.status_label.grid(row=1, column=0, sticky="e", pady=(5, 0))
    
    def _create_main_content(self):
        """Create tabbed interface."""
        content_frame = ModernFrame(self, fg_color="#2B2B2B")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        self.tabview = ctk.CTkTabview(
            content_frame,
            text_color="#FFFFFF",
            segmented_button_fg_color="#1E1E1E",
            segmented_button_selected_color="#0066CC",
            fg_color="#2B2B2B"
        )
        self.tabview.grid(row=0, column=0, sticky="nsew")
        self.tabview.grid_columnconfigure(0, weight=1)
        self.tabview.grid_rowconfigure(0, weight=1)
        
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
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        
        desc_label = ModernLabel(
            tab,
            text="Track and report all sources of foreign income",
            font=("Segoe UI", 11),
            text_color="#A0A0A0"
        )
        desc_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
        
        # Income sources frame
        income_frame = ctk.CTkFrame(tab, fg_color="#1E1E1E")
        income_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        income_frame.grid_columnconfigure(0, weight=1)
        income_frame.grid_rowconfigure(0, weight=1)
        
        income_scroll = ctk.CTkScrollableFrame(income_frame, fg_color="#2B2B2B")
        income_scroll.grid(row=0, column=0, sticky="nsew")
        income_scroll.grid_columnconfigure(0, weight=1)
        
        sources = [
            ("Consulting Services - Canada", "CAD 45,000", "Self-employment"),
            ("UK Investment Dividends", "GBP 8,500", "Portfolio income"),
            ("Singapore Employment", "SGD 120,000", "Wages/salary"),
        ]
        
        for source, amount, type_ in sources:
            source_frame = ctk.CTkFrame(income_scroll, fg_color="#1E1E1E", height=60)
            source_frame.pack(fill="x", pady=5)
            source_frame.grid_columnconfigure(1, weight=1)
            
            source_label = ModernLabel(source_frame, text=source, font=("Segoe UI", 11, "bold"))
            source_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
            
            type_label = ModernLabel(source_frame, text=type_, font=("Segoe UI", 9), text_color="#A0A0A0")
            type_label.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 5))
            
            amount_label = ModernLabel(source_frame, text=amount, font=("Segoe UI", 12, "bold"), text_color="#2196F3")
            amount_label.grid(row=0, column=1, sticky="e", padx=10, pady=5)
    
    def _setup_foreign_accounts_tab(self):
        """Setup Foreign Accounts tab."""
        tab = self.tabview.tab("Foreign Accounts")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        
        desc_label = ModernLabel(
            tab,
            text="Track foreign financial accounts for FBAR and Form 8938",
            font=("Segoe UI", 11),
            text_color="#A0A0A0"
        )
        desc_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
        
        # Accounts frame
        accounts_frame = ctk.CTkFrame(tab, fg_color="#1E1E1E")
        accounts_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        accounts_frame.grid_columnconfigure(0, weight=1)
        accounts_frame.grid_rowconfigure(0, weight=1)
        
        accounts_scroll = ctk.CTkScrollableFrame(accounts_frame, fg_color="#2B2B2B")
        accounts_scroll.grid(row=0, column=0, sticky="nsew")
        accounts_scroll.grid_columnconfigure(0, weight=1)
        
        accounts = [
            ("Royal Bank of Canada - Savings", "Toronto, Canada", "CAD 125,000", "Yes"),
            ("Barclays Bank - Current Account", "London, UK", "GBP 45,000", "Yes"),
        ]
        
        for bank, location, balance, fbar in accounts:
            account_frame = ctk.CTkFrame(accounts_scroll, fg_color="#1E1E1E", height=70)
            account_frame.pack(fill="x", pady=5)
            account_frame.grid_columnconfigure(1, weight=1)
            
            bank_label = ModernLabel(account_frame, text=bank, font=("Segoe UI", 11, "bold"))
            bank_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
            
            location_label = ModernLabel(account_frame, text=location, font=("Segoe UI", 9), text_color="#A0A0A0")
            location_label.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 5))
            
            balance_label = ModernLabel(account_frame, text=balance, font=("Segoe UI", 11, "bold"), text_color="#4CAF50")
            balance_label.grid(row=0, column=1, sticky="e", padx=10, pady=5)
            
            fbar_label = ModernLabel(account_frame, text=f"FBAR Required: {fbar}", font=("Segoe UI", 9), text_color="#FF9800")
            fbar_label.grid(row=1, column=1, sticky="e", padx=10, pady=(0, 5))
    
    def _setup_fbar_filing_tab(self):
        """Setup FBAR Filing tab."""
        tab = self.tabview.tab("FBAR Filing")
        tab.grid_columnconfigure(0, weight=1)
        
        desc_label = ModernLabel(
            tab,
            text="Manage FBAR (Form 114) filing and compliance",
            font=("Segoe UI", 11),
            text_color="#A0A0A0"
        )
        desc_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
        
        # FBAR status frame
        fbar_frame = ctk.CTkFrame(tab, fg_color="#1E1E1E")
        fbar_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=10)
        fbar_frame.grid_columnconfigure(1, weight=1)
        
        # Requirement check
        require_label = ModernLabel(fbar_frame, text="FBAR Filing Required:", font=("Segoe UI", 11))
        require_label.grid(row=0, column=0, sticky="w", padx=15, pady=10)
        
        require_status = ModernLabel(
            fbar_frame,
            text="✓ YES (Aggregate balance > $10,000)",
            font=("Segoe UI", 11),
            text_color="#FF9800"
        )
        require_status.grid(row=0, column=1, sticky="e", padx=15, pady=10)
        
        # Filing deadline
        deadline_label = ModernLabel(fbar_frame, text="Filing Deadline:", font=("Segoe UI", 11))
        deadline_label.grid(row=1, column=0, sticky="w", padx=15, pady=10)
        
        deadline_status = ModernLabel(
            fbar_frame,
            text="April 15, 2025 (Automatic 6-month extension available)",
            font=("Segoe UI", 11),
            text_color="#FF9800"
        )
        deadline_status.grid(row=1, column=1, sticky="e", padx=15, pady=10)
        
        # Filing status
        filed_label = ModernLabel(fbar_frame, text="Filed Status:", font=("Segoe UI", 11))
        filed_label.grid(row=2, column=0, sticky="w", padx=15, pady=10)
        
        filed_status = ModernLabel(
            fbar_frame,
            text="Not Filed (Due Date: 68 days remaining)",
            font=("Segoe UI", 11),
            text_color="#F44336"
        )
        filed_status.grid(row=2, column=1, sticky="e", padx=15, pady=10)
    
    def _setup_tax_treaties_tab(self):
        """Setup Tax Treaties tab."""
        tab = self.tabview.tab("Tax Treaties")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        
        desc_label = ModernLabel(
            tab,
            text="Apply applicable tax treaty benefits and exclusions",
            font=("Segoe UI", 11),
            text_color="#A0A0A0"
        )
        desc_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
        
        # Treaties frame
        treaties_frame = ctk.CTkFrame(tab, fg_color="#1E1E1E")
        treaties_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        treaties_frame.grid_columnconfigure(0, weight=1)
        treaties_frame.grid_rowconfigure(0, weight=1)
        
        treaties_scroll = ctk.CTkScrollableFrame(treaties_frame, fg_color="#2B2B2B")
        treaties_scroll.grid(row=0, column=0, sticky="nsew")
        treaties_scroll.grid_columnconfigure(0, weight=1)
        
        treaties = [
            ("US-Canada Tax Treaty", "Foreign Earned Income Exclusion", "Yes"),
            ("US-UK Tax Treaty", "Investment Credit", "Yes"),
            ("US-Singapore Tax Treaty", "Foreign Tax Credit", "Pending"),
        ]
        
        for treaty, benefit, status in treaties:
            treaty_frame = ctk.CTkFrame(treaties_scroll, fg_color="#1E1E1E", height=60)
            treaty_frame.pack(fill="x", pady=5)
            treaty_frame.grid_columnconfigure(1, weight=1)
            
            treaty_label = ModernLabel(treaty_frame, text=treaty, font=("Segoe UI", 11, "bold"))
            treaty_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
            
            benefit_label = ModernLabel(treaty_frame, text=benefit, font=("Segoe UI", 10), text_color="#A0A0A0")
            benefit_label.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 5))
            
            status_label = ModernLabel(treaty_frame, text=status, font=("Segoe UI", 10, "bold"))
            status_label.grid(row=0, column=1, sticky="e", padx=10, pady=5)
    
    def _setup_currency_reporting_tab(self):
        """Setup Currency & Reporting tab."""
        tab = self.tabview.tab("Currency & Reporting")
        tab.grid_columnconfigure(0, weight=1)
        
        desc_label = ModernLabel(
            tab,
            text="Configure currency conversion and reporting preferences",
            font=("Segoe UI", 11),
            text_color="#A0A0A0"
        )
        desc_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
        
        # Settings frame
        settings_frame = ctk.CTkFrame(tab, fg_color="#1E1E1E")
        settings_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=10)
        settings_frame.grid_columnconfigure(1, weight=1)
        
        # Currency conversion method
        conv_label = ModernLabel(settings_frame, text="Conversion Method:", font=("Segoe UI", 11))
        conv_label.grid(row=0, column=0, sticky="w", padx=15, pady=10)
        
        conv_combo = ctk.CTkComboBox(
            settings_frame,
            values=["Year-End Rate", "Average Rate", "Transaction Date Rate"],
            fg_color="#2B2B2B",
            button_color="#0066CC",
            text_color="#FFFFFF",
            state="readonly"
        )
        conv_combo.grid(row=0, column=1, sticky="ew", padx=15, pady=10)
        conv_combo.set("Year-End Rate")
        
        # Reporting currency
        report_label = ModernLabel(settings_frame, text="Reporting Currency:", font=("Segoe UI", 11))
        report_label.grid(row=1, column=0, sticky="w", padx=15, pady=10)
        
        report_combo = ctk.CTkComboBox(
            settings_frame,
            values=["USD (US Dollar)", "EUR (Euro)", "GBP (British Pound)"],
            fg_color="#2B2B2B",
            button_color="#0066CC",
            text_color="#FFFFFF",
            state="readonly"
        )
        report_combo.grid(row=1, column=1, sticky="ew", padx=15, pady=10)
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
