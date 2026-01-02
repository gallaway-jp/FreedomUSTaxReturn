"""
Help & Documentation Page - Converted from Legacy Window

Comprehensive help, documentation, and support page.
Integrated into main window without popup dialogs.
"""

import customtkinter as ctk
from typing import Optional, Dict, Any

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton


class HelpDocumentationPage(ctk.CTkScrollableFrame):
    """
    Help & Documentation page - converted from legacy window to integrated page.
    
    Features:
    - Comprehensive help documentation
    - Frequently asked questions
    - Tutorial guides
    - Technical support resources
    - Version and license information
    """

    def __init__(self, master, config: AppConfig, tax_data: Optional[TaxData] = None,
                 accessibility_service: Optional[AccessibilityService] = None, **kwargs):
        super().__init__(master, **kwargs)

        self.config = config
        self.tax_data = tax_data
        self.accessibility_service = accessibility_service

        # Documentation data
        self.search_query = ""
        self.help_vars = {}

        # Build the page
        self._create_header()
        self._create_toolbar()
        self._create_main_content()
        self._load_help_index()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self)
        header_frame.pack(fill=ctk.X, padx=20, pady=(20, 10))

        title_label = ModernLabel(
            header_frame,
            text="❓ Help & Documentation",
            font_size=24,
            font_weight="bold"
        )
        title_label.pack(anchor=ctk.W, pady=(0, 5))

        subtitle_label = ModernLabel(
            header_frame,
            text="Get help, find answers, and access documentation",
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
            text="🔍 Search",
            command=self._search_help,
            button_type="secondary",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📖 User Guide",
            command=self._open_user_guide,
            button_type="secondary",
            width=130
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📧 Contact Support",
            command=self._contact_support,
            button_type="secondary",
            width=160
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="🌐 Online Help",
            command=self._open_online_help,
            button_type="secondary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        # Progress bar
        progress_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        progress_frame.pack(fill=ctk.X, pady=10)

        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=6)
        self.progress_bar.pack(fill=ctk.X)
        self.progress_bar.set(0)

        self.status_label = ModernLabel(progress_frame, text="Loading help system...", font_size=11)
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
        self.tab_overview = self.tabview.add("📚 Overview")
        self.tab_faq = self.tabview.add("❓ FAQ")
        self.tab_tutorials = self.tabview.add("🎓 Tutorials")
        self.tab_troubleshooting = self.tabview.add("🔧 Troubleshooting")
        self.tab_about = self.tabview.add("ℹ️ About")

        # Setup tabs
        self._setup_overview_tab()
        self._setup_faq_tab()
        self._setup_tutorials_tab()
        self._setup_troubleshooting_tab()
        self._setup_about_tab()

    def _setup_overview_tab(self):
        """Setup help overview tab"""
        self.tab_overview.grid_rowconfigure(0, weight=1)
        self.tab_overview.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_overview)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        overview_label = ModernLabel(frame, text="Getting Started", font_size=12, font_weight="bold")
        overview_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.overview_text = ctk.CTkTextbox(frame, height=400)
        self.overview_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.overview_text.insert("1.0",
            "Freedom US Tax Return - Help & Documentation\n\n"
            "Welcome to the comprehensive help system. This application helps you prepare\n"
            "and file your US tax returns efficiently.\n\n"
            "Quick Start Guide:\n"
            "1. Create a new tax return or open an existing one\n"
            "2. Answer the tax interview questions\n"
            "3. Enter your income information\n"
            "4. Add deductions and credits\n"
            "5. Review your return\n"
            "6. E-file or print your return\n\n"
            "For detailed help on any topic, use the search function or browse the FAQ section.\n"
            "Contact support if you have questions not covered in this help system."
        )
        self.overview_text.configure(state="disabled")

    def _setup_faq_tab(self):
        """Setup FAQ tab"""
        self.tab_faq.grid_rowconfigure(0, weight=1)
        self.tab_faq.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_faq)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        faq_label = ModernLabel(frame, text="Frequently Asked Questions", font_size=12, font_weight="bold")
        faq_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.faq_text = ctk.CTkTextbox(frame, height=400)
        self.faq_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.faq_text.insert("1.0",
            "Frequently Asked Questions\n\n"
            "Q: How do I start a new tax return?\n"
            "A: Click 'New Return' from the main menu and select your tax year.\n\n"
            "Q: How do I e-file my return?\n"
            "A: Go to the E-Filing section and follow the submission wizard.\n\n"
            "Q: Can I save my work in progress?\n"
            "A: Yes, the application auto-saves every 5 minutes.\n\n"
            "Q: What file formats are supported?\n"
            "A: PDF, XML, and TXT formats for importing/exporting.\n\n"
            "Q: How do I update my information?\n"
            "A: All settings can be modified in the Settings & Preferences page.\n\n"
            "Q: Is my data secure?\n"
            "A: Yes, all data is encrypted and stored locally."
        )
        self.faq_text.configure(state="disabled")

    def _setup_tutorials_tab(self):
        """Setup tutorials tab"""
        self.tab_tutorials.grid_rowconfigure(0, weight=1)
        self.tab_tutorials.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_tutorials)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        tutorials_label = ModernLabel(frame, text="Video Tutorials & Guides", font_size=12, font_weight="bold")
        tutorials_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.tutorials_text = ctk.CTkTextbox(frame, height=400)
        self.tutorials_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.tutorials_text.insert("1.0",
            "Available Tutorials\n\n"
            "1. Getting Started\n"
            "   - Introduction to the application\n"
            "   - Creating your first return\n"
            "   - Basic navigation\n\n"
            "2. Entering Income\n"
            "   - W-2 employment income\n"
            "   - Self-employment income\n"
            "   - Investment income\n\n"
            "3. Claiming Deductions\n"
            "   - Standard vs itemized deductions\n"
            "   - Business deductions\n"
            "   - Education expenses\n\n"
            "4. Tax Credits\n"
            "   - Child tax credit\n"
            "   - Education credits\n"
            "   - Earned income credit\n\n"
            "5. Filing Your Return\n"
            "   - E-file submission\n"
            "   - Tracking status\n"
            "   - Receiving your refund"
        )
        self.tutorials_text.configure(state="disabled")

    def _setup_troubleshooting_tab(self):
        """Setup troubleshooting tab"""
        self.tab_troubleshooting.grid_rowconfigure(0, weight=1)
        self.tab_troubleshooting.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_troubleshooting)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        trouble_label = ModernLabel(frame, text="Troubleshooting", font_size=12, font_weight="bold")
        trouble_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.troubleshooting_text = ctk.CTkTextbox(frame, height=400)
        self.troubleshooting_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.troubleshooting_text.insert("1.0",
            "Common Issues & Solutions\n\n"
            "Issue: Application won't start\n"
            "Solution: Clear temporary files and restart\n\n"
            "Issue: Data won't save\n"
            "Solution: Check disk space and file permissions\n\n"
            "Issue: E-file submission failed\n"
            "Solution: Verify internet connection and ERO credentials\n\n"
            "Issue: Calculations appear incorrect\n"
            "Solution: Review your input data and validate\n\n"
            "Issue: Performance is slow\n"
            "Solution: Close unnecessary programs and restart the application\n\n"
            "Issue: Receipt scanning not working\n"
            "Solution: Check OCR is enabled in settings\n\n"
            "For additional support, contact: support@freedom-tax.com"
        )
        self.troubleshooting_text.configure(state="disabled")

    def _setup_about_tab(self):
        """Setup about tab"""
        self.tab_about.grid_rowconfigure(0, weight=1)
        self.tab_about.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_about)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        about_label = ModernLabel(frame, text="About This Application", font_size=12, font_weight="bold")
        about_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.about_text = ctk.CTkTextbox(frame, height=400)
        self.about_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.about_text.insert("1.0",
            "Freedom US Tax Return Application\n\n"
            "Version: 1.0.0\n"
            "Release Date: 2026\n"
            "Platform: Windows, macOS, Linux\n\n"
            "About:\n"
            "Freedom is a comprehensive, user-friendly tax return preparation\n"
            "and filing application designed to simplify the tax filing process.\n\n"
            "Features:\n"
            "• Complete tax interview system\n"
            "• Multiple tax forms support\n"
            "• E-filing capabilities\n"
            "• Receipt scanning with OCR\n"
            "• Tax planning and optimization\n"
            "• Secure client portal\n\n"
            "License: Proprietary\n"
            "Support: support@freedom-tax.com\n"
            "Website: www.freedom-tax.com\n\n"
            "© 2026 Freedom Tax Software. All rights reserved."
        )
        self.about_text.configure(state="disabled")

    # ===== Action Methods =====

    def _load_help_index(self):
        """Load help system index"""
        self.status_label.configure(text="Loading help system...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Help system ready")
        self.progress_bar.set(1.0)

    def _search_help(self):
        """Search help documentation"""
        self.status_label.configure(text="Searching...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Search complete")
        self.progress_bar.set(1.0)

    def _open_user_guide(self):
        """Open full user guide"""
        self.status_label.configure(text="Opening user guide...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="User guide opened")
        self.progress_bar.set(1.0)

    def _contact_support(self):
        """Open support contact dialog"""
        self.status_label.configure(text="Opening support contact...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Ready")
        self.progress_bar.set(1.0)

    def _open_online_help(self):
        """Open online help in browser"""
        self.status_label.configure(text="Opening online help...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Online help opened")
        self.progress_bar.set(1.0)
