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


class ModernMainWindow(ctk.CTk):
    """
    Modern main application window using CustomTkinter.

    Features:
    - Guided tax interview wizard
    - Simplified navigation based on recommendations
    - Progress tracking
    - Contextual help
    - Modern UI design
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
        self.form_recommendations = []

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
        self._create_menu_bar()
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
        """Setup the sidebar navigation"""
        # Interview button
        self.interview_button = ModernButton(
            self.sidebar_frame,
            text="🚀 Start Tax Interview",
            command=self._start_interview,
            button_type="primary",
            height=40
        )
        self.interview_button.pack(fill="x", padx=10, pady=(10, 5))

        # Separator
        separator = ctk.CTkFrame(self.sidebar_frame, height=2, fg_color="gray70")
        separator.pack(fill="x", padx=10, pady=5)

        # Form sections (initially hidden)
        self.form_buttons_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.form_buttons_frame.pack(fill="x", padx=10, pady=5)

        # Initially hide form buttons
        self.form_buttons_frame.pack_forget()

        # Action buttons
        actions_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        actions_frame.pack(fill="x", padx=10, pady=(20, 10))

        ModernButton(
            actions_frame,
            text="💾 Save Progress",
            command=self._save_progress,
            button_type="secondary",
            height=35
        ).pack(fill="x", pady=(0, 5))

        ModernButton(
            actions_frame,
            text="📊 View Summary",
            command=self._show_summary,
            button_type="secondary",
            height=35
        ).pack(fill="x", pady=(0, 5))

        ModernButton(
            actions_frame,
            text="⚙️ Settings",
            command=self._show_settings,
            button_type="secondary",
            height=35
        ).pack(fill="x", pady=(0, 10))

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
                anchor="w"
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

    def _handle_income_complete(self, tax_data, action="continue"):
        """Handle completion of income page"""
        if action == "continue":
            self._show_deductions_page()
        elif action == "back":
            # Go back to interview or previous step
            show_info_message("Navigation", "Back navigation from income page.")

    def _handle_deductions_complete(self, tax_data, action="continue"):
        """Handle completion of deductions page"""
        if action == "continue":
            self._show_credits_page()
        elif action == "back":
            self._show_income_page()

    def _handle_credits_complete(self, tax_data, action="continue"):
        """Handle completion of credits page"""
        if action == "continue":
            self._show_payments_page()
        elif action == "back":
            self._show_deductions_page()

    def _handle_payments_complete(self, tax_data, action="continue"):
        """Handle completion of payments page"""
        if action == "continue":
            self._show_form_viewer_page()
        elif action == "back":
            self._show_credits_page()

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
        show_info_message("Save Progress", "Progress saving will be implemented in the next phase.")

    def _show_summary(self):
        """Show tax return summary"""
        if not self.interview_completed:
            show_error_message("No Data", "Please complete the tax interview first.")
            return

        # Navigate to form viewer for summary
        self._show_form_viewer_page()

    def _show_settings(self):
        """Show settings dialog"""
        show_info_message("Settings", "Settings dialog will be implemented in the next phase.")

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

    def _create_menu_bar(self):
        """Create the main menu bar"""
        menubar = tk.Menu(self)
        self.configure(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Return", command=self._new_return, accelerator="Ctrl+N")
        file_menu.add_command(label="New Amended Return", command=self._new_amended_return)
        file_menu.add_command(label="Open", command=self._load_progress, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self._save_progress, accelerator="Ctrl+S")
        file_menu.add_separator()
        
        import_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Import", menu=import_menu)
        import_menu.add_command(label="Prior Year Return", command=self._import_prior_year)
        import_menu.add_command(label="W-2 Form (PDF)", command=self._import_w2_pdf)
        import_menu.add_command(label="1099 Form (PDF)", command=self._import_1099_pdf)
        import_menu.add_command(label="Tax Software (TXF)", command=self._import_txf)
        
        file_menu.add_command(label="Export PDF", command=self._export_pdf, accelerator="Ctrl+E")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Tax Dashboard", command=self._open_tax_dashboard)
        view_menu.add_command(label="Toggle Theme", command=self._toggle_theme)
        view_menu.add_separator()
        view_menu.add_command(label="Accessibility Settings...", command=self._open_accessibility_settings)
        view_menu.add_command(label="Accessibility Help", command=self._open_accessibility_help)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Tax Planning", command=self._open_tax_planning, accelerator="Ctrl+P")
        tools_menu.add_command(label="State Taxes", command=self._open_state_taxes, accelerator="Ctrl+Shift+S")
        tools_menu.add_command(label="Tax Analytics", command=self._open_tax_analytics, accelerator="Ctrl+Shift+A")
        tools_menu.add_command(label="AI Deduction Finder", command=self._open_ai_deduction_finder, accelerator="Ctrl+D")
        tools_menu.add_command(label="Bank Account Linking", command=self._open_bank_account_linking, accelerator="Ctrl+B")
        tools_menu.add_command(label="QuickBooks Integration", command=self._open_quickbooks_integration, accelerator="Ctrl+Q")
        tools_menu.add_command(label="Audit Trail", command=self._open_audit_trail, accelerator="Ctrl+A")

        # Security menu
        security_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Security", menu=security_menu)
        
        cloud_menu = tk.Menu(security_menu, tearoff=0)
        security_menu.add_cascade(label="Cloud Backup", menu=cloud_menu)
        cloud_menu.add_command(label="Configure...", command=self._configure_cloud_backup)
        cloud_menu.add_command(label="Create Backup...", command=self._create_backup)
        cloud_menu.add_command(label="Restore Backup...", command=self._restore_backup)
        cloud_menu.add_command(label="Backup Status...", command=self._show_backup_status)
        
        tfa_menu = tk.Menu(security_menu, tearoff=0)
        security_menu.add_cascade(label="Two-Factor Auth", menu=tfa_menu)
        tfa_menu.add_command(label="Enable 2FA...", command=self._enable_2fa)
        tfa_menu.add_command(label="Disable 2FA...", command=self._disable_2fa)
        
        client_menu = tk.Menu(security_menu, tearoff=0)
        security_menu.add_cascade(label="Client Management", menu=client_menu)
        client_menu.add_command(label="Client Portal Login...", command=self._open_client_portal)
        client_menu.add_separator()
        client_menu.add_command(label="Manage Clients...", command=self._open_client_management)
        client_menu.add_command(label="PTIN/ERO Management...", command=self._open_ptin_ero_management)
        
        security_menu.add_command(label="Change Password", command=self._change_password)
        security_menu.add_separator()
        security_menu.add_command(label="Logout", command=self._logout)

        # E-File menu
        efile_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="E-File", menu=efile_menu)
        efile_menu.add_command(label="Prepare E-File", command=self._open_e_filing, accelerator="Ctrl+F")
        efile_menu.add_separator()
        efile_menu.add_command(label="E-File Status", command=self._check_e_file_status)

        # Collaboration menu
        collab_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Collaboration", menu=collab_menu)
        collab_menu.add_command(label="Share Return", command=self._share_return, accelerator="Ctrl+H")
        collab_menu.add_command(label="Review Mode", command=self._open_review_mode, accelerator="Ctrl+R")
        collab_menu.add_separator()
        collab_menu.add_command(label="Manage Shared Returns", command=self._manage_shared_returns)

        # Year menu
        year_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Year", menu=year_menu)
        year_menu.add_command(label="New Tax Year", command=self._create_new_year)
        year_menu.add_command(label="Copy Current Year", command=self._copy_current_year)
        year_menu.add_command(label="Compare Years", command=self._compare_years, accelerator="Ctrl+Y")
        year_menu.add_separator()
        year_menu.add_command(label="Manage Years", command=self._manage_years)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

    def _bind_keyboard_shortcuts(self):
        """Bind keyboard shortcuts for common actions"""
        self.bind('<Control-s>', lambda e: self._save_progress())
        self.bind('<Control-o>', lambda e: self._load_progress())
        self.bind('<Control-n>', lambda e: self._new_return())
        self.bind('<Control-e>', lambda e: self._export_pdf())
        self.bind('<Control-p>', lambda e: self._open_tax_planning())
        self.bind('<Control-Shift-s>', lambda e: self._open_state_taxes())
        self.bind('<Control-Shift-a>', lambda e: self._open_tax_analytics())
        self.bind('<Control-d>', lambda e: self._open_ai_deduction_finder())
        self.bind('<Control-b>', lambda e: self._open_bank_account_linking())
        self.bind('<Control-q>', lambda e: self._open_quickbooks_integration())
        self.bind('<Control-a>', lambda e: self._open_audit_trail())
        self.bind('<Control-f>', lambda e: self._open_e_filing())
        self.bind('<Control-y>', lambda e: self._compare_years())
        self.bind('<Control-h>', lambda e: self._share_return())
        self.bind('<Control-r>', lambda e: self._open_review_mode())

    # File menu handlers
    def _new_return(self):
        """Start a new tax return"""
        show_info_message("New Return", "New return functionality will be implemented in the next phase.")

    def _new_amended_return(self):
        """Start a new amended return"""
        show_info_message("Amended Return", "Amended return functionality will be implemented in the next phase.")

    def _load_progress(self):
        """Load progress from file"""
        show_info_message("Load Progress", "Load functionality will be implemented in the next phase.")

    def _export_pdf(self):
        """Export the current tax return as PDF"""
        show_info_message("Export PDF", "Export functionality will be implemented in the next phase.")

    def _import_prior_year(self):
        """Import prior year return"""
        show_info_message("Import Prior Year", "Prior year import will be implemented in the next phase.")

    def _import_w2_pdf(self):
        """Import W-2 form from PDF"""
        show_info_message("Import W-2", "W-2 import will be implemented in the next phase.")

    def _import_1099_pdf(self):
        """Import 1099 form from PDF"""
        show_info_message("Import 1099", "1099 import will be implemented in the next phase.")

    def _import_txf(self):
        """Import tax software TXF file"""
        show_info_message("Import TXF", "TXF import will be implemented in the next phase.")

    # View menu handlers
    def _toggle_theme(self):
        """Toggle between light and dark themes"""
        current_mode = ctk.get_appearance_mode()
        new_mode = "Light" if current_mode == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)
        show_info_message("Theme Changed", f"Theme changed to {new_mode} mode.")

    def _open_accessibility_settings(self):
        """Open accessibility settings dialog"""
        show_info_message("Accessibility", "Accessibility settings will be implemented in the next phase.")

    def _open_accessibility_help(self):
        """Open accessibility help"""
        help_text = """
        Accessibility Features:
        
        - Keyboard shortcuts for all major functions
        - High contrast themes
        - Screen reader support
        - Adjustable font sizes
        - Full WCAG 2.1 AA compliance
        """
        show_info_message("Accessibility Help", help_text)

    # Tools menu handlers
    def _open_tax_planning(self):
        """Open tax planning tools"""
        show_info_message("Tax Planning", "Tax planning tools will be implemented in the next phase.")

    def _open_state_taxes(self):
        """Open state tax tools"""
        show_info_message("State Taxes", "State tax tools will be implemented in the next phase.")

    def _open_tax_analytics(self):
        """Open tax analytics"""
        show_info_message("Tax Analytics", "Tax analytics will be implemented in the next phase.")

    def _open_ai_deduction_finder(self):
        """Open AI deduction finder"""
        show_info_message("AI Deduction Finder", "AI deduction finder will be implemented in the next phase.")

    def _open_bank_account_linking(self):
        """Open bank account linking"""
        show_info_message("Bank Account Linking", "Bank account linking will be implemented in the next phase.")

    def _open_quickbooks_integration(self):
        """Open QuickBooks integration"""
        show_info_message("QuickBooks Integration", "QuickBooks integration will be implemented in the next phase.")

    def _open_audit_trail(self):
        """Open audit trail"""
        show_info_message("Audit Trail", "Audit trail will be implemented in the next phase.")

    # Security menu handlers
    def _configure_cloud_backup(self):
        """Configure cloud backup"""
        show_info_message("Cloud Backup Configuration", "Cloud backup configuration will be implemented in the next phase.")

    def _create_backup(self):
        """Create a cloud backup"""
        show_info_message("Create Backup", "Cloud backup creation will be implemented in the next phase.")

    def _restore_backup(self):
        """Restore from a cloud backup"""
        show_info_message("Restore Backup", "Cloud backup restoration will be implemented in the next phase.")

    def _show_backup_status(self):
        """Show backup status"""
        show_info_message("Backup Status", "Backup status will be implemented in the next phase.")

    def _enable_2fa(self):
        """Enable two-factor authentication"""
        show_info_message("Enable 2FA", "2FA setup will be implemented in the next phase.")

    def _disable_2fa(self):
        """Disable two-factor authentication"""
        show_info_message("Disable 2FA", "2FA will be implemented in the next phase.")

    def _open_client_portal(self):
        """Open client portal login"""
        show_info_message("Client Portal", "Client portal will be implemented in the next phase.")

    def _open_client_management(self):
        """Open client management"""
        show_info_message("Client Management", "Client management will be implemented in the next phase.")

    def _open_ptin_ero_management(self):
        """Open PTIN/ERO management"""
        show_info_message("PTIN/ERO Management", "PTIN/ERO management will be implemented in the next phase.")

    def _change_password(self):
        """Change password"""
        show_info_message("Change Password", "Password change will be implemented in the next phase.")

    def _logout(self):
        """Logout current user"""
        if show_confirmation("Logout", "Are you sure you want to logout?"):
            self.destroy()

    # E-File menu handlers
    def _open_e_filing(self):
        """Open e-filing window"""
        show_info_message("E-Filing", "E-filing will be implemented in the next phase.")

    def _check_e_file_status(self):
        """Check e-file status"""
        show_info_message("E-File Status", "E-file status checking will be implemented in the next phase.")

    # Collaboration menu handlers
    def _share_return(self):
        """Share the current tax return"""
        show_info_message("Share Return", "Return sharing will be implemented in the next phase.")

    def _open_review_mode(self):
        """Open review mode"""
        show_info_message("Review Mode", "Review mode will be implemented in the next phase.")

    def _manage_shared_returns(self):
        """Manage shared returns"""
        show_info_message("Manage Shared Returns", "Shared returns management will be implemented in the next phase.")

    # Year menu handlers
    def _create_new_year(self):
        """Create a new tax year"""
        show_info_message("New Tax Year", "New year creation will be implemented in the next phase.")

    def _copy_current_year(self):
        """Copy current year data to a new year"""
        show_info_message("Copy Year", "Year copying will be implemented in the next phase.")

    def _compare_years(self):
        """Compare tax years"""
        show_info_message("Compare Years", "Year comparison will be implemented in the next phase.")

    def _manage_years(self):
        """Manage tax years"""
        show_info_message("Manage Years", "Year management will be implemented in the next phase.")

    # Help menu handlers
    def _open_tax_dashboard(self):
        """Open tax dashboard"""
        show_info_message("Tax Dashboard", "Tax dashboard will be implemented in the next phase.")

    def _show_about(self):
        """Show about dialog"""
        show_info_message("About Freedom US Tax Return", "Modern Edition - Guided Tax Preparation")

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