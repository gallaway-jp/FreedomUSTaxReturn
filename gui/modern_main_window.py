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
import queue

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.tax_interview_service import TaxInterviewService
from services.form_recommendation_service import FormRecommendationService
from services.accessibility_service import AccessibilityService
from services.authentication_service import AuthenticationService
from services.encryption_service import EncryptionService
from services.translation_service import TranslationService
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
from gui.pages.modern_settings_page import ModernSettingsPage
from gui.pages.modern_audit_trail_page import ModernAuditTrailPage
from gui.pages.modern_save_progress_page import ModernSaveProgressPage
from gui.pages.modern_amended_return_page import ModernAmendedReturnPage
from gui.pages.modern_tax_interview_page import ModernTaxInterviewPage
from gui.pages.modern_tax_forms_page import ModernTaxFormsPage
from gui.state_tax_window import open_state_tax_window
from gui.tax_analytics_window import TaxAnalyticsWindow
from gui.cryptocurrency_tax_window import CryptocurrencyTaxWindow
from gui.estate_trust_window import EstateTrustWindow
from gui.partnership_s_corp_window import PartnershipSCorpWindow
from gui.tax_planning_window import TaxPlanningWindow
from gui.receipt_scanning_window import ReceiptScanningWindow
from gui.foreign_income_fbar_window import ForeignIncomeFBARWindow
from gui.e_filing_window import EFilingWindow
from gui.translation_management_window import TranslationManagementWindow
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
        self.translation_service = TranslationService(config)
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
        self.settings_page: Optional[ModernSettingsPage] = None
        self.tax_interview_page: Optional[ModernTaxInterviewPage] = None
        self.tax_forms_page: Optional[ModernTaxFormsPage] = None

        # Background calculation system
        self.calculation_thread: Optional[threading.Thread] = None
        self.calculation_queue = queue.Queue()
        self.calculation_lock = threading.Lock()
        self.calculation_results = {}
        self.calculation_callbacks = {}
        self.calculation_running = False

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

        # Set theme from config
        ctk.set_appearance_mode(self.config.theme)  # Use saved theme: "System", "Dark", "Light"
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
        self.interview_button.pack(fill="x", padx=5, pady=(5, 5))

        # Skip interview button
        skip_interview_button = ModernButton(
            sidebar_scroll,
            text="📋 Skip to Tax Forms",
            command=lambda: self._show_tax_forms_page([]),
            button_type="secondary",
            height=35,
            accessibility_service=self.accessibility_service
        )
        skip_interview_button.pack(fill="x", padx=5, pady=(0, 10))

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
            text="� Audit Trail",
            command=self._show_audit_trail,
            button_type="secondary",
            height=32,
            accessibility_service=self.accessibility_service
        ).pack(fill="x", padx=5, pady=2)

        ModernButton(
            sidebar_scroll,
            text="⚙️ Settings",
            command=self._show_settings_page,
            button_type="secondary",
            height=32,
            accessibility_service=self.accessibility_service
        ).pack(fill="x", padx=5, pady=2)

        # Separator
        self._create_separator(sidebar_scroll)

        # ===== SESSION =====
        session_header = ModernLabel(
            sidebar_scroll,
            text="🔐 SESSION",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="gray60"
        )
        session_header.pack(fill="x", padx=10, pady=(10, 5), anchor="w")

        ModernButton(
            sidebar_scroll,
            text="🚪 Logout",
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
        """Start the page-based tax interview"""
        def on_interview_complete(recommendations: list):
            """Handle interview completion with form recommendations"""
            self.interview_completed = True
            self.form_recommendations = recommendations

            # Create initial tax data if not exists
            if not self.tax_data:
                from models.tax_data import TaxData
                self.tax_data = TaxData(self.config)

            # Show the tax forms selection page with recommendations
            self._show_tax_forms_page(recommendations)

            show_info_message(
                "Interview Complete",
                f"Great! We've identified {len(recommendations)} forms you may need. Select the forms you want to file."
            )

        def on_interview_skip():
            """Handle interview skip - go directly to forms selection"""
            # Show the tax forms selection page without recommendations
            self._show_tax_forms_page([])

        # Clear content and show interview page
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self.tax_interview_page = ModernTaxInterviewPage(
            self.content_frame,
            self.config,
            accessibility_service=self.accessibility_service,
            on_complete=on_interview_complete,
            on_skip=on_interview_skip
        )
        self.tax_interview_page.pack(fill="both", expand=True)

    def _show_tax_forms_page(self, initial_recommendations: list):
        """Show the tax forms selection page"""
        def on_forms_selected(selected_forms: list):
            """Handle forms selection"""
            self.form_recommendations = selected_forms

            # Create initial tax data if not exists
            if not self.tax_data:
                from models.tax_data import TaxData
                self.tax_data = TaxData(self.config)

            # Update sidebar
            self._update_sidebar_after_interview()

            # Show the form viewer or first form page
            if selected_forms:
                first_form = selected_forms[0]
                self._navigate_to_form(first_form)

            show_info_message(
                "Forms Selected",
                f"You've selected {len(selected_forms)} forms. Let's get started!"
            )

        # Clear content and show forms page
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self.tax_forms_page = ModernTaxFormsPage(
            self.content_frame,
            self.config,
            accessibility_service=self.accessibility_service,
            initial_recommendations=initial_recommendations,
            on_forms_selected=on_forms_selected
        )
        self.tax_forms_page.pack(fill="both", expand=True)

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

        # Always recreate income page to avoid widget path errors
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

        # Always recreate deductions page to avoid widget path errors
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

        # Always recreate credits page to avoid widget path errors
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

        # Always recreate payments page to avoid widget path errors
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

        # Always recreate foreign income page to avoid widget path errors
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

        # Always recreate form viewer page to avoid widget path errors
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

    def _show_settings_page(self):
        """Show the settings page"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Always recreate settings page to avoid widget path errors
        self.settings_page = ModernSettingsPage(
            self.content_frame,
            self.config,
            self.translation_service,
            self.auth_service,
            on_theme_changed=self._handle_theme_changed,
            on_language_changed=self._handle_language_changed
        )

        # Show the settings page
        self.settings_page.pack(fill="both", expand=True)

        # Update status
        self.status_label.configure(text="Settings - Customize your application preferences")

        # Update progress
        self._update_progress()

    def _handle_theme_changed(self, new_theme: str):
        """Handle theme change from settings page"""
        try:
            # Set the appearance mode using CustomTkinter
            ctk.set_appearance_mode(new_theme)

            # Save theme setting to config
            self.config.theme = new_theme
            self.config.save_user_settings()

            # Refresh the UI to apply theme changes
            self._refresh_ui_theme()
        except Exception as e:
            show_error_message("Theme Error", f"Failed to change theme: {str(e)}")

    def _handle_language_changed(self, new_language: str):
        """Handle language change from settings page"""
        # Save language setting to config
        self.config.default_language = new_language
        self.config.save_user_settings()

        # Refresh translations in the UI
        self._refresh_translations()

    def _refresh_ui_theme(self):
        """Refresh UI elements to apply theme changes"""
        # This would refresh any theme-dependent UI elements
        # For now, CustomTkinter handles most theme changes automatically
        pass

    def _refresh_translations(self):
        """Refresh UI text with new language settings"""
        # This would update all UI text elements with new translations
        # For now, the translation service handles most updates
        pass

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
        """Show save progress page"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Create and show save progress page
        self.save_progress_page = ModernSaveProgressPage(
            self.content_frame,
            tax_data=self.tax_data,
            on_progress_saved=self._handle_progress_saved
        )

        # Show the save progress page
        self.save_progress_page.pack(fill="both", expand=True)

        # Update status
        self.status_label.configure(text="Save Progress - Back up your tax return")

        # Update progress
        self._update_progress()

    def _handle_progress_saved(self):
        """Handle progress saved callback"""
        # Could refresh UI or update status here if needed
        pass

    def _show_summary(self):
        """Show tax return summary"""
        # Check if tax data exists and has basic personal info
        if not self.tax_data or not self.tax_data.get('personal_info.first_name', '').strip():
            self._show_summary_placeholder()
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

        # Save theme setting to config
        self.config.theme = new_mode
        self.config.save_user_settings()

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
        """Show tax analytics page with grid of analytics features"""
        # Check if tax data exists and has basic personal info
        if not self.tax_data or not self.tax_data.get('personal_info.first_name', '').strip():
            self._show_analytics_placeholder()
            return

        # Show analytics page
        self._show_analytics_page()

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

    def _show_translation_management(self):
        """Show translation management window"""
        try:
            # Create and show translation management window
            translation_window = TranslationManagementWindow(
                self,
                self.config,
                self.translation_service
            )
            translation_window.show()
            
        except Exception as e:
            show_error_message("Translation Management Error", f"Failed to open translation management window: {str(e)}")

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

    def _open_state_tax_window(self):
        """Open state tax returns page or show placeholder"""
        if not self.tax_data:
            # Show placeholder page instead of dialog
            self._show_state_tax_placeholder()
            return

        try:
            # Open state tax window
            open_state_tax_window(self, self.tax_data)
            
        except Exception as e:
            show_error_message("State Tax Error", f"Failed to open state tax tools: {str(e)}")

    def _show_state_tax_placeholder(self):
        """Show placeholder page for state tax returns when no data exists"""
        # Clear content area
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Create placeholder content
        placeholder_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        placeholder_frame.pack(fill="both", expand=True, padx=40, pady=40)

        # Title
        title_label = ModernLabel(
            placeholder_frame,
            text="🏛️ State Tax Returns",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 20))

        # Icon
        icon_label = ModernLabel(
            placeholder_frame,
            text="📋",
            font=ctk.CTkFont(size=48)
        )
        icon_label.pack(pady=(20, 30))

        # Message
        message_label = ModernLabel(
            placeholder_frame,
            text="Complete your federal tax interview first to access state tax preparation tools.",
            font=ctk.CTkFont(size=14),
            text_color="gray70",
            wraplength=500,
            justify="center"
        )
        message_label.pack(pady=(0, 30))

        # Instructions
        instructions_frame = ctk.CTkFrame(placeholder_frame, fg_color="transparent")
        instructions_frame.pack(pady=(0, 30))

        instructions_title = ModernLabel(
            instructions_frame,
            text="To get started:",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        instructions_title.pack(anchor="w", pady=(0, 10))

        steps = [
            "1. Complete the tax interview using the 'Start Tax Interview' button",
            "2. Enter your personal information and income details",
            "3. Review your tax calculations and form recommendations",
            "4. Return here to prepare your state tax returns"
        ]

        for step in steps:
            step_label = ModernLabel(
                instructions_frame,
                text=step,
                font=ctk.CTkFont(size=12),
                text_color="gray60",
                anchor="w"
            )
            step_label.pack(anchor="w", pady=2)

        # Action button
        action_button = ModernButton(
            placeholder_frame,
            text="🚀 Start Tax Interview",
            command=self._start_interview,
            button_type="primary",
            height=40
        )
        action_button.pack(pady=(20, 0))

        # Update status
        self.status_label.configure(text="State tax preparation requires completed federal tax interview")

    def _show_summary_placeholder(self):
        """Show placeholder page for tax summary when no data exists"""
        # Clear content area
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Create placeholder content
        placeholder_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        placeholder_frame.pack(fill="both", expand=True, padx=40, pady=40)

        # Title
        title_label = ModernLabel(
            placeholder_frame,
            text="📊 Tax Return Summary",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 20))

        # Icon
        icon_label = ModernLabel(
            placeholder_frame,
            text="📈",
            font=ctk.CTkFont(size=48)
        )
        icon_label.pack(pady=(20, 30))

        # Message
        message_label = ModernLabel(
            placeholder_frame,
            text="Complete your federal tax interview first to view your tax return summary.",
            font=ctk.CTkFont(size=14),
            text_color="gray70",
            wraplength=500,
            justify="center"
        )
        message_label.pack(pady=(0, 30))

        # Instructions
        instructions_frame = ctk.CTkFrame(placeholder_frame, fg_color="transparent")
        instructions_frame.pack(pady=(0, 30))

        instructions_title = ModernLabel(
            instructions_frame,
            text="To get started:",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        instructions_title.pack(anchor="w", pady=(0, 10))

        steps = [
            "1. Complete the tax interview using the 'Start Tax Interview' button",
            "2. Enter your personal information and income details",
            "3. Review your tax calculations and form recommendations",
            "4. Return here to view your complete tax return summary"
        ]

        for step in steps:
            step_label = ModernLabel(
                instructions_frame,
                text=step,
                font=ctk.CTkFont(size=12),
                text_color="gray60",
                anchor="w"
            )
            step_label.pack(anchor="w", pady=2)

        # Action button
        action_button = ModernButton(
            placeholder_frame,
            text="🚀 Start Tax Interview",
            command=self._start_interview,
            button_type="primary",
            height=40
        )
        action_button.pack(pady=(20, 0))

        # Update status
        self.status_label.configure(text="Tax summary requires completed federal tax interview")

    def _show_analytics_placeholder(self):
        """Show placeholder page for analytics when no data exists"""
        # Clear content area
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Create placeholder content
        placeholder_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        placeholder_frame.pack(fill="both", expand=True, padx=40, pady=40)

        # Title
        title_label = ModernLabel(
            placeholder_frame,
            text="📊 Tax Analytics & Tools",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 20))

        # Icon
        icon_label = ModernLabel(
            placeholder_frame,
            text="📈",
            font=ctk.CTkFont(size=48)
        )
        icon_label.pack(pady=(20, 30))

        # Message
        message_label = ModernLabel(
            placeholder_frame,
            text="Complete your federal tax interview first to access advanced analytics and tax planning tools.",
            font=ctk.CTkFont(size=14),
            text_color="gray70",
            wraplength=500,
            justify="center"
        )
        message_label.pack(pady=(0, 30))

        # Instructions
        instructions_frame = ctk.CTkFrame(placeholder_frame, fg_color="transparent")
        instructions_frame.pack(pady=(0, 30))

        instructions_title = ModernLabel(
            instructions_frame,
            text="To get started:",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        instructions_title.pack(anchor="w", pady=(0, 10))

        steps = [
            "1. Complete the tax interview using the 'Start Tax Interview' button",
            "2. Enter your personal information and income details",
            "3. Review your tax calculations and form recommendations",
            "4. Return here to access powerful tax analytics and planning tools"
        ]

        for step in steps:
            step_label = ModernLabel(
                instructions_frame,
                text=step,
                font=ctk.CTkFont(size=12),
                text_color="gray60",
                anchor="w"
            )
            step_label.pack(anchor="w", pady=2)

        # Action button
        action_button = ModernButton(
            placeholder_frame,
            text="🚀 Start Tax Interview",
            command=self._start_interview,
            button_type="primary",
            height=40
        )
        action_button.pack(pady=(20, 0))

        # Update status
        self.status_label.configure(text="Tax analytics requires completed federal tax interview")

    def _show_e_filing_placeholder(self):
        """Show placeholder page for IRS e-filing when no data exists"""
        # Clear content area
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Create placeholder content
        placeholder_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        placeholder_frame.pack(fill="both", expand=True, padx=40, pady=40)

        # Title
        title_label = ModernLabel(
            placeholder_frame,
            text="🚀 IRS E-Filing",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 20))

        # Icon
        icon_label = ModernLabel(
            placeholder_frame,
            text="📄",
            font=ctk.CTkFont(size=48)
        )
        icon_label.pack(pady=(20, 30))

        # Message
        message_label = ModernLabel(
            placeholder_frame,
            text="Complete your federal tax interview first to access IRS e-filing capabilities.",
            font=ctk.CTkFont(size=14),
            text_color="gray70",
            wraplength=500,
            justify="center"
        )
        message_label.pack(pady=(0, 30))

        # Instructions
        instructions_frame = ctk.CTkFrame(placeholder_frame, fg_color="transparent")
        instructions_frame.pack(pady=(0, 30))

        instructions_title = ModernLabel(
            instructions_frame,
            text="To get started:",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        instructions_title.pack(anchor="w", pady=(0, 10))

        steps = [
            "1. Complete the tax interview using the 'Start Tax Interview' button",
            "2. Enter your personal information and income details",
            "3. Review your tax calculations and form recommendations",
            "4. Return here to electronically file your tax return with the IRS"
        ]

        for step in steps:
            step_label = ModernLabel(
                instructions_frame,
                text=step,
                font=ctk.CTkFont(size=12),
                text_color="gray60",
                anchor="w"
            )
            step_label.pack(anchor="w", pady=2)

        # Action button
        action_button = ModernButton(
            placeholder_frame,
            text="🚀 Start Tax Interview",
            command=self._start_interview,
            button_type="primary",
            height=40
        )
        action_button.pack(pady=(20, 0))

        # Update status
        self.status_label.configure(text="IRS e-filing requires completed federal tax interview")

    def _show_e_filing_page(self):
        """Show IRS e-filing page"""
        # Clear content area
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Create main content frame
        main_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ModernLabel(
            main_frame,
            text="🚀 IRS E-Filing Center",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 10))

        # Subtitle
        subtitle_label = ModernLabel(
            main_frame,
            text="Electronically file your tax return with the IRS",
            font=ctk.CTkFont(size=14),
            text_color="gray70"
        )
        subtitle_label.pack(pady=(0, 30))

        # Create scrollable frame for content
        scrollable_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scrollable_frame.pack(fill="both", expand=True)

        # Status section
        status_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent", border_width=1, border_color="gray75")
        status_frame.pack(fill="x", padx=10, pady=10)

        status_title = ModernLabel(
            status_frame,
            text="📋 Filing Status",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        status_title.pack(pady=(15, 10))

        # Check if return is ready for filing
        tax_year = self.tax_data.get_current_year() if self.tax_data else 2026
        year_data = self.tax_data.get_year_data(tax_year) if self.tax_data else None

        if year_data and year_data.get('personal_info', {}).get('first_name'):
            status_text = "✅ Your tax return is ready for e-filing"
            status_color = "green"
        else:
            status_text = "⏳ Complete your tax interview to prepare for e-filing"
            status_color = "orange"

        status_label = ModernLabel(
            status_frame,
            text=status_text,
            font=ctk.CTkFont(size=12),
            text_color=status_color
        )
        status_label.pack(pady=(0, 15))

        # Federal e-filing section
        federal_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent", border_width=1, border_color="gray75")
        federal_frame.pack(fill="x", padx=10, pady=10)

        federal_title = ModernLabel(
            federal_frame,
            text="🇺🇸 Federal Tax Return E-Filing",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        federal_title.pack(pady=(15, 10))

        federal_desc = ModernLabel(
            federal_frame,
            text="Prepare and electronically submit your federal tax return to the IRS",
            font=ctk.CTkFont(size=12),
            text_color="gray70",
            wraplength=400
        )
        federal_desc.pack(pady=(0, 15))

        # Federal e-filing buttons
        federal_buttons_frame = ctk.CTkFrame(federal_frame, fg_color="transparent")
        federal_buttons_frame.pack(pady=(0, 15))

        prepare_button = ModernButton(
            federal_buttons_frame,
            text="📝 Prepare Federal Return",
            command=self._prepare_federal_e_filing,
            button_type="secondary",
            height=35,
            width=180
        )
        prepare_button.pack(side="left", padx=5)

        submit_button = ModernButton(
            federal_buttons_frame,
            text="📤 Submit to IRS",
            command=self._submit_federal_e_filing,
            button_type="primary",
            height=35,
            width=180
        )
        submit_button.pack(side="left", padx=5)

        # State e-filing section
        state_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent", border_width=1, border_color="gray75")
        state_frame.pack(fill="x", padx=10, pady=10)

        state_title = ModernLabel(
            state_frame,
            text="🏛️ State Tax Return E-Filing",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        state_title.pack(pady=(15, 10))

        state_desc = ModernLabel(
            state_frame,
            text="File your state tax returns electronically with state tax authorities",
            font=ctk.CTkFont(size=12),
            text_color="gray70",
            wraplength=400
        )
        state_desc.pack(pady=(0, 15))

        # State e-filing buttons
        state_buttons_frame = ctk.CTkFrame(state_frame, fg_color="transparent")
        state_buttons_frame.pack(pady=(0, 15))

        state_prepare_button = ModernButton(
            state_buttons_frame,
            text="📋 Prepare State Returns",
            command=self._prepare_state_e_filing,
            button_type="secondary",
            height=35,
            width=180
        )
        state_prepare_button.pack(side="left", padx=5)

        state_submit_button = ModernButton(
            state_buttons_frame,
            text="📤 Submit to States",
            command=self._submit_state_e_filing,
            button_type="primary",
            height=35,
            width=180
        )
        state_submit_button.pack(side="left", padx=5)

        # Filing history section
        history_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent", border_width=1, border_color="gray75")
        history_frame.pack(fill="x", padx=10, pady=10)

        history_title = ModernLabel(
            history_frame,
            text="📚 Filing History",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        history_title.pack(pady=(15, 10))

        history_desc = ModernLabel(
            history_frame,
            text="View your previous e-filing submissions and status updates",
            font=ctk.CTkFont(size=12),
            text_color="gray70",
            wraplength=400
        )
        history_desc.pack(pady=(0, 15))

        view_history_button = ModernButton(
            history_frame,
            text="📖 View Filing History",
            command=self._view_e_filing_history,
            button_type="secondary",
            height=35
        )
        view_history_button.pack(pady=(0, 15))

        # Update status
        self.status_label.configure(text="IRS E-Filing Center")

    def _prepare_federal_e_filing(self):
        """Prepare federal tax return for e-filing"""
        try:
            # Import e-filing service
            from services.e_filing_service import EFilingService

            # Create e-filing service instance
            e_filing_service = EFilingService(self.config)

            # Generate XML for federal return
            tax_year = self.tax_data.get_current_year() if self.tax_data else 2026
            xml_content = e_filing_service.generate_efile_xml(self.tax_data, tax_year)

            if xml_content:
                # Show success message and update page
                show_info_message("Preparation Complete", "Your federal tax return has been prepared for e-filing. You can now submit it to the IRS.")
                # Update the page to show prepared status
                self._show_e_filing_page()
            else:
                show_error_message("Preparation Failed", "Failed to prepare your tax return for e-filing. Please check your data and try again.")

        except Exception as e:
            show_error_message("E-Filing Error", f"Failed to prepare federal e-filing: {str(e)}")

    def _submit_federal_e_filing(self):
        """Submit federal tax return via e-filing"""
        try:
            # Import e-filing service
            from services.e_filing_service import EFilingService

            # Create e-filing service instance
            e_filing_service = EFilingService(self.config)

            # First generate the XML
            tax_year = self.tax_data.get_current_year() if self.tax_data else 2026
            xml_content = e_filing_service.generate_efile_xml(self.tax_data, tax_year)

            if xml_content:
                # Submit the return
                result = e_filing_service.submit_efile(xml_content, test_mode=True)

                if result.get('success'):
                    show_info_message("Submission Successful", f"Your tax return has been submitted to the IRS.\nConfirmation: {result.get('confirmation_number', 'N/A')}")
                    # Update the page to show submitted status
                    self._show_e_filing_page()
                else:
                    show_error_message("Submission Failed", f"Failed to submit your tax return: {result.get('error', 'Unknown error')}")
            else:
                show_error_message("Preparation Failed", "Failed to prepare your tax return for submission.")

        except Exception as e:
            show_error_message("E-Filing Error", f"Failed to submit federal e-filing: {str(e)}")

    def _prepare_state_e_filing(self):
        """Prepare state tax returns for e-filing"""
        show_error_message("Coming Soon", "State e-filing preparation will be available in a future update.")

    def _submit_state_e_filing(self):
        """Submit state tax returns via e-filing"""
        show_error_message("Coming Soon", "State e-filing submission will be available in a future update.")

    def _view_e_filing_history(self):
        """View e-filing history"""
        show_error_message("Coming Soon", "E-filing history will be available in a future update.")

    def _show_analytics_page(self):
        """Show analytics page with grid of analytics features"""
        # Clear content area
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Create main content frame
        main_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ModernLabel(
            main_frame,
            text="📊 Tax Analytics & Advanced Tools",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 10))

        # Subtitle
        subtitle_label = ModernLabel(
            main_frame,
            text="Powerful tools to analyze, optimize, and plan your tax strategy",
            font=ctk.CTkFont(size=14),
            text_color="gray70"
        )
        subtitle_label.pack(pady=(0, 30))

        # Create scrollable frame for the grid
        scrollable_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scrollable_frame.pack(fill="both", expand=True)

        # Define analytics features
        analytics_features = [
            {
                "icon": "📈",
                "title": "Tax Analytics Dashboard",
                "description": "Comprehensive tax analysis including effective rates, deductions breakdown, and tax optimization insights",
                "command": self._show_tax_analytics_dashboard
            },
            {
                "icon": "🔮",
                "title": "Tax Projections",
                "description": "Future tax planning with scenario analysis and year-over-year comparisons",
                "command": self._show_tax_projections
            },
            {
                "icon": "🤖",
                "title": "AI Deduction Finder",
                "description": "Artificial intelligence powered deduction discovery and tax saving opportunities",
                "command": self._show_ai_deduction_finder
            },
            {
                "icon": "🔌",
                "title": "Plugin Management",
                "description": "Manage tax calculation plugins and third-party integrations",
                "command": self._show_plugin_management
            },
            {
                "icon": "₿",
                "title": "Cryptocurrency Tax",
                "description": "Specialized cryptocurrency transaction tracking and tax reporting",
                "command": self._show_cryptocurrency_tax
            },
            {
                "icon": "🏛️",
                "title": "Estate & Trust Returns",
                "description": "Estate tax planning and trust return preparation tools",
                "command": self._show_estate_trust
            },
            {
                "icon": "🤝",
                "title": "Partnership & S-Corp Returns",
                "description": "Business entity tax returns and partnership income reporting",
                "command": self._show_partnership_s_corp
            },
            {
                "icon": "📊",
                "title": "Tax Planning Tools",
                "description": "Strategic tax planning calculators and optimization tools",
                "command": self._show_tax_planning
            },
            {
                "icon": "📄",
                "title": "Receipt Scanning",
                "description": "AI-powered receipt scanning and expense categorization",
                "command": self._show_receipt_scanning
            },
            {
                "icon": "🌍",
                "title": "Foreign Income & FBAR",
                "description": "International income reporting and FBAR filing assistance",
                "command": self._show_foreign_income_fbar
            }
        ]

        # Create grid layout
        # Calculate columns based on available width (aim for 3-4 columns)
        columns = 3
        current_row = 0
        current_col = 0

        for feature in analytics_features:
            # Create feature card
            card_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent", border_width=1, border_color="gray75")
            card_frame.grid(row=current_row, column=current_col, padx=10, pady=10, sticky="nsew")

            # Configure grid weights
            scrollable_frame.grid_rowconfigure(current_row, weight=1)
            scrollable_frame.grid_columnconfigure(current_col, weight=1)

            # Icon
            icon_label = ModernLabel(
                card_frame,
                text=feature["icon"],
                font=ctk.CTkFont(size=32)
            )
            icon_label.pack(pady=(15, 5))

            # Title
            title_label = ModernLabel(
                card_frame,
                text=feature["title"],
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="white"
            )
            title_label.pack(pady=(0, 8))

            # Description
            desc_label = ModernLabel(
                card_frame,
                text=feature["description"],
                font=ctk.CTkFont(size=11),
                text_color="gray70",
                wraplength=200,
                justify="center"
            )
            desc_label.pack(pady=(0, 15))

            # Button
            action_button = ModernButton(
                card_frame,
                text="Open Tool",
                command=feature["command"],
                button_type="secondary",
                height=30,
                width=120
            )
            action_button.pack(pady=(0, 15))

            # Move to next position
            current_col += 1
            if current_col >= columns:
                current_col = 0
                current_row += 1

        # Update status
        self.status_label.configure(text="Tax Analytics & Advanced Tools")

    def _show_tax_analytics_dashboard(self):
        """Show the main tax analytics dashboard window"""
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
            show_error_message("Analytics Error", f"Failed to open analytics dashboard: {str(e)}")

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
        """Show IRS e-filing page"""
        # Check if tax data exists and has basic personal info
        if not self.tax_data or not self.tax_data.get('personal_info.first_name', '').strip():
            self._show_e_filing_placeholder()
            return

        # Show e-filing page
        self._show_e_filing_page()

    def _create_amended_return(self):
        """Show amended return page"""
        if not self.tax_data:
            show_error_message("No Tax Data", "Please complete a tax return first before creating an amended return.")
            return

        try:
            # Clear content frame
            for widget in self.content_frame.winfo_children():
                widget.destroy()

            # Create and show amended return page
            self.amended_return_page = ModernAmendedReturnPage(
                self.content_frame,
                tax_data=self.tax_data,
                on_amended_created=self._handle_amended_created
            )

            # Show the amended return page
            self.amended_return_page.pack(fill="both", expand=True)

            # Update status
            self.status_label.configure(text="Amended Return - Create Form 1040-X")

            # Update progress
            self._update_progress()

        except Exception as e:
            show_error_message("Amended Return Error", f"Failed to open amended return page: {str(e)}")

    def _handle_amended_created(self, amended_result):
        """Handle amended return created callback"""
        if amended_result:
            show_info_message(
                "Amended Return Created",
                f"Amended return for tax year {amended_result.get('tax_year')} has been created.\n\n"
                "You can now modify the return data and file the amended return."
            )
            # Update status to reflect amended return
            self.status_label.configure(text=f"Amended return created for tax year {amended_result.get('tax_year')}")

    def _show_audit_trail(self):
        """Show audit trail as a page"""
        try:
            from services.audit_trail_service import AuditTrailService

            # Clear content frame
            for widget in self.content_frame.winfo_children():
                widget.destroy()

            # Create audit trail service
            audit_service = AuditTrailService(self.config)

            # Create and show audit trail page
            self.audit_trail_page = ModernAuditTrailPage(
                self.content_frame,
                audit_service
            )

            # Show the audit trail page
            self.audit_trail_page.pack(fill="both", expand=True)

            # Update status
            self.status_label.configure(text="Audit Trail - System activity log")

            # Update progress
            self._update_progress()

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

    def _open_state_tax_window(self):
        """Open the state tax returns window"""
        # Check if tax data exists and has basic personal info
        if not self.tax_data or not self.tax_data.get('personal_info.first_name', '').strip():
            self._show_state_tax_placeholder()
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

    def _start_background_calculations(self):
        """Start the background calculation thread"""
        if self.calculation_thread and self.calculation_thread.is_alive():
            return  # Already running

        self.calculation_running = True
        self.calculation_thread = threading.Thread(
            target=self._background_calculation_worker,
            daemon=True,
            name="TaxCalculationWorker"
        )
        self.calculation_thread.start()

    def _stop_background_calculations(self):
        """Stop the background calculation thread"""
        self.calculation_running = False
        if self.calculation_thread:
            self.calculation_thread.join(timeout=1.0)

    def _queue_calculation(self, calculation_id: str, calculation_func, callback=None):
        """
        Queue a calculation to run in the background

        Args:
            calculation_id: Unique identifier for this calculation
            calculation_func: Function to execute (should return result)
            callback: Function to call with result when complete
        """
        with self.calculation_lock:
            # Remove any existing calculation with same ID
            if calculation_id in self.calculation_callbacks:
                # Cancel existing callback
                pass

            self.calculation_callbacks[calculation_id] = callback
            self.calculation_queue.put((calculation_id, calculation_func))

        # Start worker if not running
        self._start_background_calculations()

    def _get_calculation_result(self, calculation_id: str):
        """Get result of a background calculation if available"""
        with self.calculation_lock:
            return self.calculation_results.pop(calculation_id, None)

    def _background_calculation_worker(self):
        """Background worker thread for calculations"""
        while self.calculation_running:
            try:
                # Get next calculation (with timeout to allow shutdown)
                calculation_item = self.calculation_queue.get(timeout=0.1)
                calculation_id, calculation_func = calculation_item

                try:
                    # Execute calculation
                    result = calculation_func()

                    # Store result
                    with self.calculation_lock:
                        self.calculation_results[calculation_id] = result
                        callback = self.calculation_callbacks.pop(calculation_id, None)

                    # Execute callback on main thread
                    if callback:
                        self.after(0, lambda: callback(calculation_id, result))

                except Exception as e:
                    # Store error result
                    with self.calculation_lock:
                        self.calculation_results[calculation_id] = e
                        callback = self.calculation_callbacks.pop(calculation_id, None)

                    # Execute error callback on main thread
                    if callback:
                        self.after(0, lambda: callback(calculation_id, e))

                finally:
                    self.calculation_queue.task_done()

            except queue.Empty:
                continue  # No work, check again
            except Exception as e:
                # Log unexpected errors but keep thread running
                print(f"Background calculation error: {e}")
                continue

    def _calculate_tax_totals_background(self, callback=None):
        """Calculate tax totals in background"""
        if not self.tax_data:
            if callback:
                self.after(0, lambda: callback("tax_totals", None))
            return

        def calculation():
            return self.tax_data.calculate_totals()

        self._queue_calculation("tax_totals", calculation, callback)

    def _calculate_form_recommendations_background(self, callback=None):
        """Calculate form recommendations in background"""
        if not self.tax_data:
            if callback:
                self.after(0, lambda: callback("form_recommendations", []))
            return

        def calculation():
            return self.recommendation_service.get_recommendations(self.tax_data)

        self._queue_calculation("form_recommendations", calculation, callback)

    def _on_tax_totals_calculated(self, calculation_id, result):
        """Handle completion of tax totals calculation"""
        if isinstance(result, Exception):
            print(f"Tax totals calculation failed: {result}")
            return

        # Update cached totals
        self._cached_totals = result

        # Update UI if currently showing relevant page
        if hasattr(self, '_update_current_page_totals'):
            self._update_current_page_totals()

    def _on_form_recommendations_calculated(self, calculation_id, result):
        """Handle completion of form recommendations calculation"""
        if isinstance(result, Exception):
            print(f"Form recommendations calculation failed: {result}")
            return

        # Update cached recommendations
        self.form_recommendations = result
        self._recommendations_cache = None  # Invalidate summary cache

        # Update progress bar
        self._update_progress()

    def _trigger_tax_calculations(self):
        """Trigger background tax calculations when data changes"""
        if self.tax_data:
            self._calculate_tax_totals_background(self._on_tax_totals_calculated)

    def _is_calculation_ready(self, calculation_id: str) -> bool:
        """Check if a background calculation result is ready"""
        with self.calculation_lock:
            return calculation_id in self.calculation_results

    def _get_cached_calculation(self, calculation_id: str):
        """Get cached calculation result if available"""
        if self._is_calculation_ready(calculation_id):
            return self._get_calculation_result(calculation_id)
        return None

    def get_tax_totals(self):
        """Get tax totals, using cached result if available"""
        cached = self._get_cached_calculation("tax_totals")
        if cached is not None:
            return cached

        # Fallback to direct calculation if no cache
        if self.tax_data:
            return self.tax_data.calculate_totals()
        return {}

    def destroy(self):
        """Clean up resources before destroying window"""
        # Stop background calculations
        self._stop_background_calculations()

        # Call parent destroy
        super().destroy()

    def run(self):
        """Run the application"""
        self.mainloop()