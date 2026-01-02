"""
Modern Main Window - CustomTkinter-based main application window

Provides a modern, intuitive interface for tax preparation with guided
interview, simplified navigation, and contextual help.

Features:
- Complete menu system (File, View, Tools, Security, E-File, Collaboration, Year)
- Tax interview wizard
- Intelligent form recommendations
- Accessibility integration
- Keyboard shortcuts for all major functions
- Authentication and session management
- Cloud backup and security features
- E-filing support
- Multi-year tax return management
"""

import customtkinter as ctk
from typing import Optional, Dict, Any
import tkinter as tk
import warnings
from unittest.mock import Mock
import subprocess
import webbrowser
import threading
import time
import sys
import os
import datetime

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.tax_interview_service import TaxInterviewService
from services.form_recommendation_service import FormRecommendationService
from services.accessibility_service import AccessibilityService
from services.authentication_service import AuthenticationService
from services.encryption_service import EncryptionService
from services.ptin_ero_service import PTINEROService
from gui.modern_ui_components import (
    ModernFrame, ModernLabel, ModernButton, ModernProgressBar,
    show_info_message, show_error_message, show_confirmation
)
from gui.tax_interview_wizard import TaxInterviewWizard
from gui.pages.modern_income_page import ModernIncomePage
from gui.pages.modern_deductions_page import ModernDeductionsPage
from gui.pages.modern_credits_page import ModernCreditsPage
from gui.pages.modern_payments_page import ModernPaymentsPage
from gui.pages.modern_foreign_income_page import ModernForeignIncomePage
from gui.pages.modern_form_viewer_page import ModernFormViewerPage
from gui.state_tax_window import open_state_tax_window
from gui.tax_analytics_window import TaxAnalyticsWindow
from gui.cryptocurrency_tax_window import CryptocurrencyTaxWindow
from gui.estate_trust_window import EstateTrustWindow
from gui.partnership_s_corp_window import PartnershipSCorpWindow
from gui.tax_planning_window import TaxPlanningWindow
from gui.receipt_scanning_window import ReceiptScanningWindow
from gui.foreign_income_fbar_window import ForeignIncomeFBARWindow
from gui.e_filing_window import EFilingWindow
from gui.amended_return_dialog import AmendedReturnDialog
from gui.audit_trail_window import AuditTrailWindow
from gui.plugin_management_window import open_plugin_management_window


class ModernMainWindow(ctk.CTk):
    """
    Modern main application window using CustomTkinter.

    Features:
    - Guided tax interview wizard
    - Simplified navigation based on recommendations
    - Progress tracking and contextual help
    - Modern UI design with accessibility support
    - Section 508 and WCAG 2.1 AA compliance
    - Keyboard shortcuts and screen reader support
    - Multi-page form navigation with lazy loading
    - Integrated authentication and session management
    - Web interface launcher for mobile access
    - Comprehensive error handling and user feedback
    """

    def __init__(self, config: AppConfig, accessibility_service: Optional[AccessibilityService] = None, demo_mode: bool = False):
        """
        Initialize the modern main window.

        Args:
            config: Application configuration
            accessibility_service: Optional accessibility service for feature support
            demo_mode: If True, skip authentication dialogs
        """
        super().__init__()

        self.config = config
        self.accessibility_service = accessibility_service
        self.demo_mode = demo_mode
        self.tax_data: Optional[TaxData] = None
        self.interview_completed = False
        self.form_recommendations = []  # Cache for form recommendations
        self._recommendations_cache = None  # Cache recommendations summary

        # Initialize services
        self.interview_service = TaxInterviewService(config)
        self.recommendation_service = FormRecommendationService(config)
        self.encryption_service = EncryptionService(config.key_file)
        self.ptin_ero_service = PTINEROService(config, self.encryption_service)
        self.auth_service = AuthenticationService(config, self.ptin_ero_service)
        self.session_token = None
        self.is_mocked = False

        # UI components
        self.sidebar_frame: Optional[ModernFrame] = None
        self.content_frame: Optional[ModernFrame] = None
        self.progress_bar: Optional[ModernProgressBar] = None
        self.status_label: Optional[ModernLabel] = None

        # Page instances (lazy-loaded)
        self.income_page: Optional[ModernIncomePage] = None
        self.deductions_page: Optional[ModernDeductionsPage] = None
        self.credits_page: Optional[ModernCreditsPage] = None
        self.payments_page: Optional[ModernPaymentsPage] = None
        self.foreign_income_page: Optional[ModernForeignIncomePage] = None
        self.form_viewer_page: Optional[ModernFormViewerPage] = None

        # Check authentication
        if not self._check_authentication():
            return

        self._setup_window()
        self._setup_ui()
        self._bind_keyboard_shortcuts()
        self._show_welcome_screen()

    def _setup_window(self):
        """Setup the main window properties"""
        self.title("Freedom US Tax Return - Modern Edition")
        self.geometry("1200x800")
        self.resizable(True, True)

        # Set theme
        ctk.set_appearance_mode("system")  # Modes: "System" (standard), "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

        # Apply accessibility to main window
        if self.accessibility_service:
            self.accessibility_service.make_accessible(
                self,
                label="Freedom US Tax Return - Modern Edition",
                role="application"
            )

        # Center window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _setup_ui(self):
        """Setup the main user interface"""
        # Create main container
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Sidebar (left)
        self.sidebar_frame = ModernFrame(
            main_container,
            width=250,
            title="Navigation"
        )
        self.sidebar_frame.pack(side="left", fill="y", padx=(0, 10))

        # Content area (right)
        self.content_frame = ModernFrame(main_container, title="")
        self.content_frame.pack(side="right", fill="both", expand=True)

        # Progress bar (bottom)
        self.progress_bar = ModernProgressBar(
            main_container,
            label_text="Tax Return Progress"
        )
        self.progress_bar.pack(side="bottom", fill="x", pady=(10, 0))

        # Status bar
        status_frame = ctk.CTkFrame(main_container, height=30)
        status_frame.pack(side="bottom", fill="x", pady=(5, 0))

        self.status_label = ModernLabel(
            status_frame,
            text="Ready to start your tax interview",
            font=ctk.CTkFont(size=10)
        )
        self.status_label.pack(side="left", padx=10)

        # Setup sidebar navigation
        self._setup_sidebar()

    def _setup_sidebar(self):
        """Setup the modern sidebar navigation with all features"""
        # Create a scrollable container for the sidebar
        sidebar_scroll = ctk.CTkScrollableFrame(self.sidebar_frame, fg_color="transparent")
        sidebar_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # ===== PRIMARY ACTION =====
        self.interview_button = ModernButton(
            sidebar_scroll,
            text="🚀 Start Tax Interview",
            command=self._start_interview,
            button_type="primary",
            height=40,
            accessibility_service=self.accessibility_service
        )
        self.interview_button.pack(fill="x", padx=5, pady=(5, 10))

        # Separator
        self._create_separator(sidebar_scroll)

        # ===== FORM SECTIONS (Hidden until interview complete) =====
        form_header = ModernLabel(
            sidebar_scroll,
            text="📄 TAX FORMS",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="gray60"
        )
        form_header.pack(fill="x", padx=10, pady=(10, 5), anchor="w")

        self.form_buttons_frame = ctk.CTkFrame(sidebar_scroll, fg_color="transparent")
        self.form_buttons_frame.pack(fill="x", padx=5, pady=5)
        self.form_buttons_frame.pack_forget()  # Initially hidden

        # Separator
        self._create_separator(sidebar_scroll)

        # ===== STATE TAX SECTION =====
        state_header = ModernLabel(
            sidebar_scroll,
            text="🏛️ STATE TAX",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="gray60"
        )
        state_header.pack(fill="x", padx=10, pady=(10, 5), anchor="w")

        ModernButton(
            sidebar_scroll,
            text="📋 State Tax Returns",
            command=self._open_state_tax_window,
            button_type="secondary",
            height=32,
            accessibility_service=self.accessibility_service
        ).pack(fill="x", padx=5, pady=2)

        # Separator
        self._create_separator(sidebar_scroll)

        # ===== VIEW & DISPLAY OPTIONS =====
        view_header = ModernLabel(
            sidebar_scroll,
            text="👁️ VIEW",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="gray60"
        )
        view_header.pack(fill="x", padx=10, pady=(10, 5), anchor="w")

        ModernButton(
            sidebar_scroll,
            text="📊 View Summary",
            command=self._show_summary,
            button_type="secondary",
            height=32,
            accessibility_service=self.accessibility_service
        ).pack(fill="x", padx=5, pady=2)

        ModernButton(
            sidebar_scroll,
            text="📈 Tax Analytics",
            command=self._show_tax_analytics,
            button_type="secondary",
            height=32,
            accessibility_service=self.accessibility_service
        ).pack(fill="x", padx=5, pady=2)

        ModernButton(
            sidebar_scroll,
            text="🌙 Toggle Theme",
            command=self._toggle_theme,
            button_type="secondary",
            height=32,
            accessibility_service=self.accessibility_service
        ).pack(fill="x", padx=5, pady=2)

        # Separator
        self._create_separator(sidebar_scroll)

        # ===== FILE OPERATIONS =====
        file_header = ModernLabel(
            sidebar_scroll,
            text="💾 FILE",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="gray60"
        )
        file_header.pack(fill="x", padx=10, pady=(10, 5), anchor="w")

        ModernButton(
            sidebar_scroll,
            text="💾 Save Progress",
            command=self._save_progress,
            button_type="secondary",
            height=32
        ).pack(fill="x", padx=5, pady=2)

        ModernButton(
            sidebar_scroll,
            text="📥 Import Data",
            command=self._show_import_menu,
            button_type="secondary",
            height=32
        ).pack(fill="x", padx=5, pady=2)

        ModernButton(
            sidebar_scroll,
            text="📝 Amended Return",
            command=self._create_amended_return,
            button_type="secondary",
            height=32
        ).pack(fill="x", padx=5, pady=2)

        # Separator
        self._create_separator(sidebar_scroll)

        # ===== SECURITY & SETTINGS =====
        security_header = ModernLabel(
            sidebar_scroll,
            text="🔒 SECURITY",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="gray60"
        )
        security_header.pack(fill="x", padx=10, pady=(10, 5), anchor="w")

        ModernButton(
            sidebar_scroll,
            text="🔑 Change Password",
            command=self._change_password,
            button_type="secondary",
            height=32,
            accessibility_service=self.accessibility_service
        ).pack(fill="x", padx=5, pady=2)

        ModernButton(
            sidebar_scroll,
            text="📋 Audit Trail",
            command=self._show_audit_trail,
            button_type="secondary",
            height=32,
            accessibility_service=self.accessibility_service
        ).pack(fill="x", padx=5, pady=2)

        ModernButton(
            sidebar_scroll,
            text="⚙️ Settings",
            command=self._show_settings,
            button_type="secondary",
            height=32,
            accessibility_service=self.accessibility_service
        ).pack(fill="x", padx=5, pady=2)

        # Separator
        self._create_separator(sidebar_scroll)

        # ===== ANALYTICS & REPORTING =====
        analytics_header = ModernLabel(
            sidebar_scroll,
            text="📊 ANALYTICS",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="gray60"
        )
        analytics_header.pack(fill="x", padx=10, pady=(10, 5), anchor="w")

        ModernButton(
            sidebar_scroll,
            text="📈 Tax Analytics",
            command=self._show_tax_analytics,
            button_type="secondary",
            height=32,
            accessibility_service=self.accessibility_service
        ).pack(fill="x", padx=5, pady=2)

        ModernButton(
            sidebar_scroll,
            text="🔮 Tax Projections",
            command=self._show_tax_projections,
            button_type="secondary",
            height=32,
            accessibility_service=self.accessibility_service
        ).pack(fill="x", padx=5, pady=2)

        ModernButton(
            sidebar_scroll,
            text="🤖 AI Deduction Finder",
            command=self._show_ai_deduction_finder,
            button_type="secondary",
            height=32,
            accessibility_service=self.accessibility_service
        ).pack(fill="x", padx=5, pady=2)

        ModernButton(
            sidebar_scroll,
            text="🔌 Plugin Management",
            command=self._show_plugin_management,
            button_type="secondary",
            height=32,
            accessibility_service=self.accessibility_service
        ).pack(fill="x", padx=5, pady=2)

        ModernButton(
            sidebar_scroll,
            text="₿ Cryptocurrency Tax",
            command=self._show_cryptocurrency_tax,
            button_type="secondary",
            height=32,
            accessibility_service=self.accessibility_service
        ).pack(fill="x", padx=5, pady=2)

        ModernButton(
            sidebar_scroll,
            text="🏛️ Estate & Trust Returns",
            command=self._show_estate_trust,
            button_type="secondary",
            height=32,
            accessibility_service=self.accessibility_service
        ).pack(fill="x", padx=5, pady=2)

        ModernButton(
            sidebar_scroll,
            text="🤝 Partnership & S-Corp Returns",
            command=self._show_partnership_s_corp,
            button_type="secondary",
            height=32,
            accessibility_service=self.accessibility_service
        ).pack(fill="x", padx=5, pady=2)

        ModernButton(
            sidebar_scroll,
            text="📊 Tax Planning Tools",
            command=self._show_tax_planning,
            button_type="secondary",
            height=32,
            accessibility_service=self.accessibility_service
        ).pack(fill="x", padx=5, pady=2)

        ModernButton(
            sidebar_scroll,
            text="📄 Receipt Scanning",
            command=self._show_receipt_scanning,
            button_type="secondary",
            height=32,
            accessibility_service=self.accessibility_service
        ).pack(fill="x", padx=5, pady=2)

        ModernButton(
            sidebar_scroll,
            text="🌍 Foreign Income & FBAR",
            command=self._show_foreign_income_fbar,
            button_type="secondary",
            height=32
        ).pack(fill="x", padx=5, pady=2)

        # Separator
        self._create_separator(sidebar_scroll)

        # ===== E-FILING =====
        efiling_header = ModernLabel(
            sidebar_scroll,
            text="📡 E-FILING",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="gray60"
        )
        efiling_header.pack(fill="x", padx=10, pady=(10, 5), anchor="w")

        ModernButton(
            sidebar_scroll,
            text="🚀 IRS E-Filing",
            command=self._show_e_filing,
            button_type="secondary",
            height=32,
            accessibility_service=self.accessibility_service
        ).pack(fill="x", padx=5, pady=2)

        # Separator
        self._create_separator(sidebar_scroll)

        # ===== HELP & INFO =====
        help_header = ModernLabel(
            sidebar_scroll,
            text="❓ HELP",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="gray60"
        )
        help_header.pack(fill="x", padx=10, pady=(10, 5), anchor="w")

        ModernButton(
            sidebar_scroll,
            text="ℹ️ About",
            command=self._show_about,
            button_type="secondary",
            height=32,
            accessibility_service=self.accessibility_service
        ).pack(fill="x", padx=5, pady=2)

        ModernButton(
            sidebar_scroll,
            text="� Mobile/Web Interface",
            command=self._launch_web_interface,
            button_type="secondary",
            height=32
        ).pack(fill="x", padx=5, pady=2)

        ModernButton(
            sidebar_scroll,
            text="�🚪 Logout",
            command=self._logout,
            button_type="secondary",
            height=32
        ).pack(fill="x", padx=5, pady=(2, 10))

    def _create_separator(self, parent):
        """Create a visual separator"""
        separator = ctk.CTkFrame(parent, height=1, fg_color="gray40")
        separator.pack(fill="x", padx=10, pady=8)

    def _show_welcome_screen(self):
        """Show the welcome screen"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Welcome content
        welcome_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        welcome_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ModernLabel(
            welcome_frame,
            text="Welcome to Freedom US Tax Return",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(50, 10))

        # Subtitle
        subtitle_label = ModernLabel(
            welcome_frame,
            text="Modern Edition - Guided Tax Preparation",
            font=ctk.CTkFont(size=16),
            text_color="gray60"
        )
        subtitle_label.pack(pady=(0, 30))

        # Description
        desc_text = """
        This modern tax preparation application will guide you through
        the process of filing your US federal income tax return.

        Features:
        • Intelligent tax interview to determine what you need to report
        • Step-by-step guidance with contextual help
        • Modern, intuitive interface
        • Automatic form recommendations
        • Progress tracking and validation

        To get started, click "Start Tax Interview" in the sidebar.
        """

        desc_label = ModernLabel(
            welcome_frame,
            text=desc_text,
            font=ctk.CTkFont(size=12),
            wraplength=600,
            justify="left"
        )
        desc_label.pack(pady=(0, 40))

        # Quick start button
        quick_start_button = ModernButton(
            welcome_frame,
            text="🚀 Quick Start - Begin Interview",
            command=self._start_interview,
            button_type="primary",
            height=50,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        quick_start_button.pack(pady=(0, 20))

        # Help text
        help_label = ModernLabel(
            welcome_frame,
            text="Need help? Hover over questions for guidance, or check our documentation.",
            font=ctk.CTkFont(size=10),
            text_color="gray50"
        )
        help_label.pack(pady=(20, 0))

    def _start_interview(self):
        """Start the tax interview wizard"""
        def on_interview_complete(summary: Dict[str, Any]):
            """Handle interview completion"""
            self.interview_completed = True
            self.form_recommendations = summary.get('recommendations', [])

            # Update UI
            self._update_sidebar_after_interview()
            self._show_recommendations_screen(summary)
            self._update_progress()

            show_info_message(
                "Interview Complete",
                f"Great! We've identified {len(self.form_recommendations)} forms you may need to complete."
            )

        # Show interview wizard
        TaxInterviewWizard(self, self.config, on_complete=on_interview_complete)

    def _update_sidebar_after_interview(self):
        """Update sidebar after interview completion"""
        # Hide interview button
        self.interview_button.pack_forget()

        # Show form buttons
        self.form_buttons_frame.pack(fill="x", padx=10, pady=5)

        # Add form section buttons based on recommendations
        for rec in self.form_recommendations[:8]:  # Show top 8
            button_text = f"{rec['form'][:20]}..." if len(rec['form']) > 20 else rec['form']

            ModernButton(
                self.form_buttons_frame,
                text=f"📄 {button_text}",
                command=lambda r=rec: self._navigate_to_form(r),
                button_type="secondary",
                height=35,
                anchor="w",
                accessibility_service=self.accessibility_service
            ).pack(fill="x", pady=(0, 2))

        # Update status
        self.status_label.configure(
            text=f"Interview complete - {len(self.form_recommendations)} forms recommended"
        )

    def _show_recommendations_screen(self, summary: Dict[str, Any]):
        """Show the form recommendations screen"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Recommendations content
        rec_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        rec_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ModernLabel(
            rec_frame,
            text="Your Recommended Tax Forms",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 10))

        # Summary
        summary_text = f"""
        Based on your answers, we recommend completing {len(self.form_recommendations)} tax forms.

        Estimated time: {summary.get('estimated_total_time', 0)} minutes
        Priority forms: {len([r for r in self.form_recommendations if r.get('priority', 0) >= 8])}
        """

        summary_label = ModernLabel(
            rec_frame,
            text=summary_text.strip(),
            font=ctk.CTkFont(size=12),
            wraplength=600,
            justify="left"
        )
        summary_label.pack(pady=(0, 20))

        # Recommendations list
        list_frame = ctk.CTkScrollableFrame(rec_frame, height=300)
        list_frame.pack(fill="both", expand=True, pady=(0, 20))

        for i, rec in enumerate(self.form_recommendations, 1):
            # Form card
            card_frame = ctk.CTkFrame(list_frame)
            card_frame.pack(fill="x", pady=(0, 10), padx=5)

            # Form title and priority
            priority_colors = {
                10: "red",    # Critical
                8: "orange",  # High
                6: "blue",    # Medium
                4: "green",   # Low
                2: "gray"     # Optional
            }

            priority_color = priority_colors.get(rec.get('priority', 2), "gray")

            title_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            title_frame.pack(fill="x", padx=10, pady=(10, 5))

            ModernLabel(
                title_frame,
                text=f"{i}. {rec['form']}",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(side="left")

            priority_label = ModernLabel(
                title_frame,
                text=f"Priority: {rec.get('priority', 2)}/10",
                font=ctk.CTkFont(size=10),
                text_color=priority_color
            )
            priority_label.pack(side="right")

            # Reason
            reason_label = ModernLabel(
                card_frame,
                text=f"Reason: {rec.get('reason', 'Recommended based on your situation')}",
                font=ctk.CTkFont(size=11),
                wraplength=500,
                justify="left"
            )
            reason_label.pack(padx=10, pady=(0, 10), anchor="w")

        # Continue button
        continue_button = ModernButton(
            rec_frame,
            text="Continue to Form Entry →",
            command=self._start_form_entry,
            button_type="primary",
            height=40
        )
        continue_button.pack(pady=(20, 0))

    def _navigate_to_form(self, recommendation: Dict[str, Any]):
        """Navigate to a specific form"""
        form_name = recommendation.get('form', '')

        # Route to specific form pages
        if 'income' in form_name.lower() or form_name in ['1040', 'W-2', '1099-INT', '1099-DIV', 'Schedule C', '1099-R', 'SSA-1099', 'Schedule D', 'Schedule E']:
            self._show_income_page()
        elif 'deduction' in form_name.lower() or form_name in ['Schedule A']:
            self._show_deductions_page()
        elif 'credit' in form_name.lower() or form_name in ['Schedule 3', 'Child Tax Credit', 'Earned Income Credit', 'Education Credits']:
            self._show_credits_page()
        elif 'payment' in form_name.lower() or form_name in ['1040-ES', 'Estimated Tax']:
            self._show_payments_page()
        elif 'foreign' in form_name.lower() or form_name in ['FBAR', '8938', '1116']:
            self._show_foreign_income_page()
        elif 'summary' in form_name.lower() or 'viewer' in form_name.lower() or form_name in ['Form 1040 Summary', 'Tax Return Summary']:
            self._show_form_viewer_page()
        else:
            show_info_message("Navigation", f"Navigation to {form_name} will be implemented in the next phase.")

    def _show_income_page(self):
        """Show the income page"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Initialize income page if not already done
        if self.income_page is None:
            self.income_page = ModernIncomePage(self.content_frame, self.config, on_complete=self._handle_income_complete)
            if self.tax_data:
                self.income_page.load_data(self.tax_data)

        # Show the income page
        self.income_page.pack(fill="both", expand=True)

        # Update status
        self.status_label.configure(text="Income Information - Enter all sources of income")

        # Update progress
        self._update_progress()

    def _show_deductions_page(self):
        """Show the deductions page"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Initialize deductions page if not already done
        if self.deductions_page is None:
            self.deductions_page = ModernDeductionsPage(self.content_frame, self.config, on_complete=self._handle_deductions_complete)
            if self.tax_data:
                self.deductions_page.load_data(self.tax_data)

        # Show the deductions page
        self.deductions_page.pack(fill="both", expand=True)

        # Update status
        self.status_label.configure(text="Deductions - Choose standard or itemized deductions")

        # Update progress
        self._update_progress()

    def _show_credits_page(self):
        """Show the credits page"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Initialize credits page if not already done
        if self.credits_page is None:
            self.credits_page = ModernCreditsPage(self.content_frame, self.config, on_complete=self._handle_credits_complete)
            if self.tax_data:
                self.credits_page.load_data(self.tax_data)

        # Show the credits page
        self.credits_page.pack(fill="both", expand=True)

        # Update status
        self.status_label.configure(text="Tax Credits - Enter eligible tax credits")

        # Update progress
        self._update_progress()

    def _show_payments_page(self):
        """Show the payments page"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Initialize payments page if not already done
        if self.payments_page is None:
            self.payments_page = ModernPaymentsPage(self.content_frame, self.config, on_complete=self._handle_payments_complete)
            if self.tax_data:
                self.payments_page.load_data(self.tax_data)

        # Show the payments page
        self.payments_page.pack(fill="both", expand=True)

        # Update status
        self.status_label.configure(text="Tax Payments - Enter federal tax payments made")

        # Update progress
        self._update_progress()

    def _show_foreign_income_page(self):
        """Show the foreign income page"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Initialize foreign income page if not already done
        if self.foreign_income_page is None:
            self.foreign_income_page = ModernForeignIncomePage(
                self.content_frame,
                self.tax_data,
                self.config,
                on_complete_callback=self._handle_foreign_income_complete
            )

        # Show the foreign income page
        self.foreign_income_page.pack(fill="both", expand=True)

        # Update status
        self.status_label.configure(text="Foreign Income & FBAR - Report foreign accounts and income")

        # Update progress
        self._update_progress()

    def _show_form_viewer_page(self):
        """Show the form viewer page"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Initialize form viewer page if not already done
        if self.form_viewer_page is None:
            self.form_viewer_page = ModernFormViewerPage(
                self.content_frame,
                self.tax_data,
                self.config,
                on_back_callback=self._handle_form_viewer_back
            )

        # Show the form viewer page
        self.form_viewer_page.pack(fill="both", expand=True)

        # Update status
        self.status_label.configure(text="Form Viewer - Review your tax return and export to PDF")

        # Update progress
        self._update_progress()

    def _handle_page_complete(self, page_name: str, tax_data, action="continue"):
        """Generic handler for page completion with navigation logic"""
        page_flow = {
            "income": {
                "continue": self._show_deductions_page,
                "back": lambda: show_info_message("Navigation", "Back navigation from income page.")
            },
            "deductions": {
                "continue": self._show_credits_page,
                "back": self._show_income_page
            },
            "credits": {
                "continue": self._show_payments_page,
                "back": self._show_deductions_page
            },
            "payments": {
                "continue": self._show_form_viewer_page,
                "back": self._show_credits_page
            }
        }

        if page_name in page_flow and action in page_flow[page_name]:
            page_flow[page_name][action]()
        else:
            show_info_message("Navigation", f"Unknown navigation action: {page_name} -> {action}")

    def _handle_income_complete(self, tax_data, action="continue"):
        """Handle completion of income page"""
        self._handle_page_complete("income", tax_data, action)

    def _handle_deductions_complete(self, tax_data, action="continue"):
        """Handle completion of deductions page"""
        self._handle_page_complete("deductions", tax_data, action)

    def _handle_credits_complete(self, tax_data, action="continue"):
        """Handle completion of credits page"""
        self._handle_page_complete("credits", tax_data, action)

    def _handle_payments_complete(self, tax_data, action="continue"):
        """Handle completion of payments page"""
        self._handle_page_complete("payments", tax_data, action)

    def _handle_foreign_income_complete(self, action="complete"):
        """Handle completion of foreign income page"""
        if action == "complete":
            show_info_message("Foreign Income Complete", "Foreign income and FBAR information has been saved.")
        elif action == "previous":
            # Could navigate back to previous page if needed
            show_info_message("Navigation", "Back navigation from foreign income page.")

    def _handle_form_viewer_back(self):
        """Handle back navigation from form viewer"""
        self._show_payments_page()

    def _start_form_entry(self):
        """Start the form entry process"""
        # Start with income page as it's typically the first major section
        self._show_income_page()

    def _save_progress(self):
        """Save current progress"""
        if not self.tax_data:
            show_error_message("No Data", "Please start the tax interview first before saving progress.")
            return

        try:
            # Generate progress filename with timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            tax_year = self.tax_data.get_current_year() if hasattr(self.tax_data, 'get_current_year') else 2026
            filename = f"progress_{tax_year}_{timestamp}.enc"

            # Save the tax data
            saved_path = self.tax_data.save_to_file(filename)

            show_info_message("Progress Saved",
                            f"Your tax return progress has been saved successfully!\n\n"
                            f"File: {os.path.basename(saved_path)}\n"
                            f"Location: {os.path.dirname(saved_path)}\n\n"
                            f"You can load this file later to continue where you left off.")

        except Exception as e:
            show_error_message("Save Failed",
                            f"Failed to save progress: {str(e)}\n\n"
                            f"Please check that you have write permissions and sufficient disk space.")

    def _show_summary(self):
        """Show tax return summary"""
        if not self.interview_completed:
            show_error_message("No Data", "Please complete the tax interview first.")
            return

        # Navigate to form viewer for summary
        self._show_form_viewer_page()

    def _show_settings(self):
        """Show settings dialog with accessibility options"""
        try:
            from gui.accessibility_dialogs import AccessibilitySettingsDialog
            from gui.theme_manager import ThemeManager
            
            # Create theme manager if not already available
            theme_manager = ThemeManager()
            
            # Create and show accessibility settings dialog
            dialog = AccessibilitySettingsDialog(
                self, 
                self.accessibility_service, 
                theme_manager
            )
            
            # The dialog handles its own lifecycle
            # Settings are automatically saved and applied
            
        except Exception as e:
            show_error_message("Settings Error", f"Failed to open settings: {str(e)}")

    def _check_authentication(self) -> bool:
        """Check if user is authenticated, prompt for login if needed"""
        if self.is_mocked or self.demo_mode:
            return True
        
        try:
            # Check if master password is set
            if not self.auth_service.is_master_password_set():
                from gui.password_dialogs import SetMasterPasswordDialog
                dialog = SetMasterPasswordDialog(self, self.auth_service)
                result = dialog.show()
                if not result:
                    self.destroy()
                    return False
            else:
                from gui.password_dialogs import AuthenticateDialog
                dialog = AuthenticateDialog(self, self.auth_service)
                self.session_token = dialog.show()
                if not self.session_token:
                    self.destroy()
                    return False
        except Exception as e:
            # If authentication services fail, continue anyway (for demo/testing)
            warnings.warn(f"Authentication service unavailable: {e}")
        
        return True

    def _bind_keyboard_shortcuts(self):
        """Bind keyboard shortcuts for common actions and accessibility"""
        # Theme toggle
        self.bind('<Control-t>', lambda e: self._toggle_theme())

        # Accessibility shortcuts
        if self.accessibility_service:
            # High contrast toggle
            self.bind('<Control-h>', lambda e: self._toggle_high_contrast())

            # Screen reader mode toggle
            self.bind('<Control-r>', lambda e: self._toggle_screen_reader())

            # Font size increase
            self.bind('<Control-plus>', lambda e: self._increase_font_size())
            self.bind('<Control-equal>', lambda e: self._increase_font_size())

            # Font size decrease
            self.bind('<Control-minus>', lambda e: self._decrease_font_size())

        # Navigation shortcuts
        self.bind('<Control-i>', lambda e: self._start_interview())  # Start interview
        self.bind('<Control-s>', lambda e: self._show_settings())    # Settings
        self.bind('<Control-a>', lambda e: self._show_tax_analytics())  # Analytics

        # Focus management for accessibility
        self.bind('<Tab>', self._handle_tab_navigation)
        self.bind('<Shift-Tab>', self._handle_shift_tab_navigation)

    # File menu - Simplified to show demo mode message
    # Additional file operations will be implemented in future releases

    def _toggle_theme(self):
        """Toggle between light and dark themes"""
        current_mode = ctk.get_appearance_mode()
        new_mode = "Light" if current_mode == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)
        show_info_message("Theme Changed", f"Theme changed to {new_mode} mode.")

    def _toggle_high_contrast(self):
        """Toggle high contrast mode for accessibility"""
        if self.accessibility_service:
            current_contrast = self.accessibility_service.get_high_contrast_mode()
            new_contrast = not current_contrast
            self.accessibility_service.set_high_contrast_mode(new_contrast)
            mode_text = "enabled" if new_contrast else "disabled"
            show_info_message("High Contrast Mode", f"High contrast mode {mode_text}.")
            # Refresh UI to apply changes
            self._refresh_ui_for_accessibility()

    def _toggle_screen_reader(self):
        """Toggle screen reader mode for accessibility"""
        if self.accessibility_service:
            current_reader = self.accessibility_service.get_screen_reader_mode()
            new_reader = not current_reader
            self.accessibility_service.set_screen_reader_mode(new_reader)
            mode_text = "enabled" if new_reader else "disabled"
            show_info_message("Screen Reader Mode", f"Screen reader mode {mode_text}.")
            # Announce change to screen reader
            if self.accessibility_service:
                self.accessibility_service.announce(f"Screen reader mode {mode_text}")

    def _increase_font_size(self):
        """Increase font size for accessibility"""
        if self.accessibility_service:
            current_size = self.accessibility_service.get_font_size()
            new_size = min(current_size + 2, 24)  # Max 24pt
            self.accessibility_service.set_font_size(new_size)
            show_info_message("Font Size", f"Font size increased to {new_size}pt.")
            # Refresh UI to apply changes
            self._refresh_ui_for_accessibility()

    def _decrease_font_size(self):
        """Decrease font size for accessibility"""
        if self.accessibility_service:
            current_size = self.accessibility_service.get_font_size()
            new_size = max(current_size - 2, 10)  # Min 10pt
            self.accessibility_service.set_font_size(new_size)
            show_info_message("Font Size", f"Font size decreased to {new_size}pt.")
            # Refresh UI to apply changes
            self._refresh_ui_for_accessibility()

    def _handle_tab_navigation(self, event):
        """Handle Tab key navigation for accessibility"""
        # Focus next widget in tab order
        current_focus = self.focus_get()
        if current_focus:
            # Find next focusable widget
            widgets = self.winfo_children()
            try:
                current_index = widgets.index(current_focus)
                next_index = (current_index + 1) % len(widgets)
                widgets[next_index].focus_set()
            except (ValueError, IndexError):
                # If current widget not found, focus first widget
                if widgets:
                    widgets[0].focus_set()
        else:
            # No current focus, focus first widget
            widgets = self.winfo_children()
            if widgets:
                widgets[0].focus_set()
        return "break"  # Prevent default tab behavior

    def _handle_shift_tab_navigation(self, event):
        """Handle Shift+Tab key navigation for accessibility"""
        # Focus previous widget in tab order
        current_focus = self.focus_get()
        if current_focus:
            widgets = self.winfo_children()
            try:
                current_index = widgets.index(current_focus)
                prev_index = (current_index - 1) % len(widgets)
                widgets[prev_index].focus_set()
            except (ValueError, IndexError):
                # If current widget not found, focus last widget
                if widgets:
                    widgets[-1].focus_set()
        else:
            # No current focus, focus last widget
            widgets = self.winfo_children()
            if widgets:
                widgets[-1].focus_set()
        return "break"  # Prevent default tab behavior

    def _refresh_ui_for_accessibility(self):
        """Refresh UI components to apply accessibility changes"""
        # Reapply themes and fonts to all components
        if hasattr(self, 'sidebar_frame') and self.sidebar_frame:
            self.sidebar_frame.configure(font=("Arial", self.accessibility_service.get_font_size() if self.accessibility_service else 12))

        if hasattr(self, 'content_frame') and self.content_frame:
            self.content_frame.configure(font=("Arial", self.accessibility_service.get_font_size() if self.accessibility_service else 12))

        # Update all child widgets recursively
        self._update_widget_fonts(self)

    def _update_widget_fonts(self, widget):
        """Recursively update font sizes for all widgets"""
        if self.accessibility_service:
            font_size = self.accessibility_service.get_font_size()
            try:
                # Update font for widgets that support it
                if hasattr(widget, 'configure'):
                    current_font = widget.cget('font') if 'font' in widget.configure() else None
                    if current_font:
                        # Parse current font and update size
                        if isinstance(current_font, str):
                            # Simple font string, replace size
                            widget.configure(font=("Arial", font_size))
                        elif isinstance(current_font, tuple):
                            # Font tuple, update size
                            new_font = (current_font[0], font_size, *current_font[2:])
                            widget.configure(font=new_font)
            except (AttributeError, TypeError, tk.TclError):
                pass  # Skip widgets that don't support font configuration

        # Recursively update children
        for child in widget.winfo_children():
            self._update_widget_fonts(child)

    def _show_tax_analytics(self):
        """Show tax analytics window"""
        if not self.tax_data:
            show_error_message("No Tax Data", "Please complete the tax interview first to view analytics.")
            return

        try:
            # Import required services
            from services.tax_calculation_service import TaxCalculationService
            
            # Create analytics window
            tax_year = self.tax_data.get_current_year() if self.tax_data else 2026
            tax_calc_service = TaxCalculationService(tax_year)
            analytics_window = TaxAnalyticsWindow(
                self,  # parent window
                self.config, 
                self.tax_data
            )
            analytics_window.show()
            
        except Exception as e:
            show_error_message("Analytics Error", f"Failed to open analytics: {str(e)}")

    def _show_tax_projections(self):
        """Show tax projections window"""
        if not self.tax_data:
            show_error_message("No Tax Data", "Please complete the tax interview first to view tax projections.")
            return

        try:
            # Import required services
            from services.tax_calculation_service import TaxCalculationService
            from gui.tax_projections_window import TaxProjectionsWindow
            
            # Create tax projections window
            tax_year = self.tax_data.get_current_year() if self.tax_data else 2026
            tax_calc_service = TaxCalculationService(tax_year)
            projections_window = TaxProjectionsWindow(
                self.config,
                tax_calc_service,
                self.tax_data
            )
            projections_window.show()
            
        except Exception as e:
            show_error_message("Tax Projections Error", f"Failed to open tax projections: {str(e)}")

    def _show_ai_deduction_finder(self):
        """Show AI deduction finder window"""
        if not self.tax_data:
            show_error_message("No Tax Data", "Please complete the tax interview first to use AI deduction finder.")
            return

        try:
            # Import AI deduction finder window
            from gui.ai_deduction_finder_window import AIDeductionFinderWindow
            
            # Create and show AI deduction finder window
            ai_window = AIDeductionFinderWindow(
                self,
                self.config,
                self.tax_data
            )
            ai_window.show()
            
        except Exception as e:
            show_error_message("AI Deduction Finder Error", f"Failed to open AI deduction finder: {str(e)}")

    def _show_plugin_management(self):
        """Show plugin management window"""
        try:
            # Open plugin management window
            open_plugin_management_window(self, self.config)

        except Exception as e:
            show_error_message("Plugin Management Error", f"Failed to open plugin management: {str(e)}")

    def _show_cryptocurrency_tax(self):
        """Show cryptocurrency tax reporting window"""
        try:
            # Create and show cryptocurrency tax window
            crypto_window = CryptocurrencyTaxWindow(
                self,
                self.config,
                self.tax_data
            )
            crypto_window.show()
            
        except Exception as e:
            show_error_message("Cryptocurrency Tax Error", f"Failed to open cryptocurrency tax window: {str(e)}")

    def _show_estate_trust(self):
        """Show estate and trust tax returns window"""
        try:
            # Create and show estate/trust tax window
            estate_window = EstateTrustWindow(
                self,
                self.config,
                self.tax_data
            )
            estate_window.show()
            
        except Exception as e:
            show_error_message("Estate & Trust Error", f"Failed to open estate & trust window: {str(e)}")

    def _show_partnership_s_corp(self):
        """Show partnership and S-Corp tax returns window"""
        try:
            # Create and show partnership/S-corp tax window
            partnership_window = PartnershipSCorpWindow(
                self,
                self.config,
                self.tax_data
            )
            partnership_window.show()
            
        except Exception as e:
            show_error_message("Partnership & S-Corp Error", f"Failed to open partnership & S-corp window: {str(e)}")

    def _show_tax_planning(self):
        """Show tax planning tools window"""
        try:
            # Create and show tax planning window
            planning_window = TaxPlanningWindow(
                self,
                self.tax_data
            )
            planning_window.show()
            
        except Exception as e:
            show_error_message("Tax Planning Error", f"Failed to open tax planning window: {str(e)}")

    def _show_receipt_scanning(self):
        """Show receipt scanning window"""
        try:
            # Create and show receipt scanning window
            scanning_window = ReceiptScanningWindow(
                self,
                self.config,
                self.tax_data
            )
            scanning_window.show()
            
        except Exception as e:
            show_error_message("Receipt Scanning Error", f"Failed to open receipt scanning window: {str(e)}")

    def _show_foreign_income_fbar(self):
        """Show foreign income and FBAR reporting window"""
        try:
            # Create and show foreign income FBAR window
            fbar_window = ForeignIncomeFBARWindow(
                self,
                self.config,
                self.tax_data
            )
            fbar_window.show()
            
        except Exception as e:
            show_error_message("Foreign Income & FBAR Error", f"Failed to open foreign income & FBAR window: {str(e)}")

    def _show_e_filing(self):
        """Show IRS e-filing window"""
        try:
            # Import e-filing service if not already imported
            from services.e_filing_service import EFilingService
            
            # Create e-filing service instance
            e_filing_service = EFilingService(self.config)
            
            # Create and show e-filing window
            e_filing_window = EFilingWindow(
                self,
                self.tax_data,
                self.config,
                e_filing_service
            )
            
        except Exception as e:
            show_error_message("E-Filing Error", f"Failed to open e-filing window: {str(e)}")

    def _create_amended_return(self):
        """Create an amended tax return"""
        if not self.tax_data:
            show_error_message("No Tax Data", "Please complete a tax return first before creating an amended return.")
            return

        try:
            # Create amended return dialog
            dialog = AmendedReturnDialog(self, self.tax_data)
            
            # If user created an amended return, refresh the interface
            if dialog.result:
                show_info_message("Amended Return Created", 
                                f"Amended return for tax year {dialog.result.get('tax_year')} has been created.\n\n" +
                                "You can now modify the return data and file the amended return.")
                
                # Update status to reflect amended return
                self.status_label.configure(text=f"Amended return created for tax year {dialog.result.get('tax_year')}")
                
        except Exception as e:
            show_error_message("Amended Return Error", f"Failed to create amended return: {str(e)}")

    def _show_audit_trail(self):
        """Show audit trail window"""
        try:
            from services.audit_trail_service import AuditTrailService
            
            # Create audit trail service
            audit_service = AuditTrailService(self.config)
            
            # Create and show audit trail window
            audit_window = AuditTrailWindow(
                self,
                audit_service,
                self.session_token
            )
            audit_window.show()
            
        except Exception as e:
            show_error_message("Audit Trail Error", f"Failed to open audit trail: {str(e)}")

    def _show_import_menu(self):
        """Show import options menu"""
        show_info_message("Import Data", "Import features for W-2, 1099, and other documents will be available in future releases.")

    # Accessibility, Tools, and other advanced features will be implemented in future releases

    def _change_password(self):
        """Change password"""
        show_info_message("Change Password", "Password change will be implemented in the next phase.")

    def _logout(self):
        """Logout current user"""
        if show_confirmation("Logout", "Are you sure you want to logout?"):
            self.destroy()

    def _show_about(self):
        """Show about dialog"""
        show_info_message("About Freedom US Tax Return", "Modern Edition - Guided Tax Preparation")

    def _launch_web_interface(self):
        """Launch the mobile/web interface"""
        try:
            import subprocess
            import webbrowser
            import threading
            import time
            
            def start_web_server():
                """Start the web server in a separate process"""
                try:
                    # Get absolute path to web_server.py for security
                    web_server_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'web_server.py'))

                    # Validate that the file exists and is a Python file
                    if not os.path.isfile(web_server_path) or not web_server_path.endswith('.py'):
                        raise FileNotFoundError(f"Web server script not found: {web_server_path}")

                    # Launch web server with validated path
                    subprocess.Popen([
                        sys.executable,
                        web_server_path
                    ],
                    cwd=os.path.dirname(web_server_path),
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    )
                    
                    # Wait a moment for server to start
                    time.sleep(2)
                    
                    # Open browser
                    webbrowser.open('http://localhost:5000')
                    
                except Exception as e:
                    print(f"Failed to start web server: {e}")
            
            # Start web server in background thread
            server_thread = threading.Thread(target=start_web_server, daemon=True)
            server_thread.start()
            
            show_info_message("Mobile/Web Interface", 
                           "Launching web interface...\n\nThe mobile-responsive web application will open in your default browser at http://localhost:5000")
            
        except Exception as e:
            show_error_message("Web Interface Error", f"Failed to launch web interface: {str(e)}")

    def _open_state_tax_window(self):
        """Open the state tax returns window"""
        if not self.tax_data:
            show_error_message("No Tax Data", "Please complete the tax interview first to access state tax features.")
            return

        try:
            open_state_tax_window(self, self.tax_data)
        except Exception as e:
            show_error_message("State Tax Error", f"Failed to open state tax window:\n\n{str(e)}")

    def _update_progress(self):
        """Update the progress bar"""
        if not self.progress_bar:
            return

        if not self.interview_completed:
            self.progress_bar.set(0.1)  # 10% for interview completion
            self.progress_bar.label.configure(text="Progress: Interview not completed")
        else:
            # Calculate progress based on recommendations
            completed_forms = 0  # This will be updated as forms are completed
            total_forms = len(self.form_recommendations)

            if total_forms > 0:
                progress = min(0.9, 0.1 + (completed_forms / total_forms) * 0.8)
                self.progress_bar.set(progress)
                self.progress_bar.label.configure(
                    text=f"Progress: {completed_forms}/{total_forms} forms completed"
                )
            else:
                self.progress_bar.set(0.1)
                self.progress_bar.label.configure(text="Progress: No forms recommended")

    def run(self):
        """Run the application"""
        self.mainloop()