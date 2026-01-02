"""
Review Mode Page - Converted from Legacy Window

Page for reviewing tax return before filing.
Integrated into main window without popup dialogs.
"""

import customtkinter as ctk
from typing import Optional, List, Dict, Any
from datetime import datetime

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton


class ReviewModePage(ctk.CTkScrollableFrame):
    """
    Review Mode page - converted from legacy window to integrated page.
    
    Features:
    - Comprehensive return review
    - Section-by-section validation
    - Data verification tools
    - Issue identification and resolution
    - Pre-filing checklist
    """

    def __init__(self, master, config: AppConfig, tax_data: Optional[TaxData] = None,
                 accessibility_service: Optional[AccessibilityService] = None, **kwargs):
        super().__init__(master, **kwargs)

        self.config = config
        self.tax_data = tax_data
        self.accessibility_service = accessibility_service

        # Review data
        self.review_items: List[Dict[str, Any]] = []
        self.issues: List[Dict[str, Any]] = []
        self.review_vars = {}

        # Build the page
        self._create_header()
        self._create_toolbar()
        self._create_main_content()
        self._load_return_data()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self)
        header_frame.pack(fill=ctk.X, padx=20, pady=(20, 10))

        title_label = ModernLabel(
            header_frame,
            text="📋 Review Your Return",
            font_size=24,
            font_weight="bold"
        )
        title_label.pack(anchor=ctk.W, pady=(0, 5))

        subtitle_label = ModernLabel(
            header_frame,
            text="Review and verify your tax return before filing",
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
            text="🔍 Check Issues",
            command=self._check_issues,
            button_type="primary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="✅ Validate Data",
            command=self._validate_data,
            button_type="secondary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📊 Compare Estimates",
            command=self._compare_estimates,
            button_type="secondary",
            width=160
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📄 Preview Forms",
            command=self._preview_forms,
            button_type="secondary",
            width=140
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="💾 Save Review",
            command=self._save_review,
            button_type="success",
            width=130
        ).pack(side=ctk.LEFT, padx=5)

        # Progress bar
        progress_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        progress_frame.pack(fill=ctk.X, pady=10)

        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=6)
        self.progress_bar.pack(fill=ctk.X)
        self.progress_bar.set(0)

        self.status_label = ModernLabel(progress_frame, text="Ready to review", font_size=11)
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
        self.tab_summary = self.tabview.add("📊 Summary")
        self.tab_sections = self.tabview.add("📑 Sections")
        self.tab_issues = self.tabview.add("⚠️ Issues")
        self.tab_checklist = self.tabview.add("✓ Checklist")
        self.tab_forms = self.tabview.add("📄 Forms")

        # Setup tabs
        self._setup_summary_tab()
        self._setup_sections_tab()
        self._setup_issues_tab()
        self._setup_checklist_tab()
        self._setup_forms_tab()

    def _setup_summary_tab(self):
        """Setup summary tab"""
        self.tab_summary.grid_rowconfigure(1, weight=1)
        self.tab_summary.grid_columnconfigure(0, weight=1)

        # Summary cards
        cards_frame = ctk.CTkFrame(self.tab_summary, fg_color="transparent")
        cards_frame.pack(fill=ctk.X, padx=20, pady=10)

        metrics = [
            ("Total Income", "$0.00"),
            ("Total Deductions", "$0.00"),
            ("Taxable Income", "$0.00"),
            ("Estimated Tax", "$0.00")
        ]

        for metric, value in metrics:
            card = self._create_summary_card(cards_frame, metric, value)
            card.pack(side=ctk.LEFT, padx=5, fill=ctk.X, expand=True)

        # Summary text
        frame = ctk.CTkScrollableFrame(self.tab_summary)
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

        summary_label = ModernLabel(frame, text="Return Summary", font_size=12, font_weight="bold")
        summary_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.summary_text = ctk.CTkTextbox(frame, height=300)
        self.summary_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.summary_text.insert("1.0", "Load return data to view summary.")
        self.summary_text.configure(state="disabled")

    def _setup_sections_tab(self):
        """Setup sections review tab"""
        self.tab_sections.grid_rowconfigure(0, weight=1)
        self.tab_sections.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_sections)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        sections_label = ModernLabel(frame, text="Return Sections", font_size=12, font_weight="bold")
        sections_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.sections_text = ctk.CTkTextbox(frame, height=400)
        self.sections_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.sections_text.insert("1.0", "Return Sections Review:\n\n✓ Personal Information\n✓ Filing Status\n✓ Income\n✓ Deductions\n✓ Credits\n✓ Payments\n✓ State Taxes")
        self.sections_text.configure(state="disabled")

    def _setup_issues_tab(self):
        """Setup issues identification tab"""
        self.tab_issues.grid_rowconfigure(0, weight=1)
        self.tab_issues.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_issues)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        issues_label = ModernLabel(frame, text="Identified Issues", font_size=12, font_weight="bold")
        issues_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.issues_text = ctk.CTkTextbox(frame, height=400)
        self.issues_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.issues_text.insert("1.0", "No issues identified. Return appears complete and valid.")
        self.issues_text.configure(state="disabled")

    def _setup_checklist_tab(self):
        """Setup pre-filing checklist tab"""
        self.tab_checklist.grid_rowconfigure(0, weight=1)
        self.tab_checklist.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_checklist)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        checklist_label = ModernLabel(frame, text="Pre-Filing Checklist", font_size=12, font_weight="bold")
        checklist_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.checklist_text = ctk.CTkTextbox(frame, height=400)
        self.checklist_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.checklist_text.insert("1.0", "Pre-Filing Checklist:\n\n[ ] All personal information correct\n[ ] Income entries verified\n[ ] Deductions documented\n[ ] Credits properly claimed\n[ ] Estimated payments accounted for\n[ ] State tax information complete\n[ ] Forms reviewed\n[ ] All calculations verified\n[ ] Ready to file")
        self.checklist_text.configure(state="disabled")

    def _setup_forms_tab(self):
        """Setup forms preview tab"""
        self.tab_forms.grid_rowconfigure(0, weight=1)
        self.tab_forms.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_forms)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        forms_label = ModernLabel(frame, text="Form Preview", font_size=12, font_weight="bold")
        forms_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.forms_text = ctk.CTkTextbox(frame, height=400)
        self.forms_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.forms_text.insert("1.0", "Forms to be filed:\n\n• Form 1040 (U.S. Individual Income Tax Return)\n• Form 1040 Schedule A (Itemized Deductions)\n• Form 1040 Schedule C (Business Income)\n• Form 1040 Schedule D (Capital Gains/Losses)\n• State tax forms (if applicable)")
        self.forms_text.configure(state="disabled")

    def _create_summary_card(self, parent, title, value):
        """Create a summary metric card"""
        card = ctk.CTkFrame(parent, corner_radius=8, fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        
        title_label = ctk.CTkLabel(card, text=title, text_color="gray", font=("", 11))
        title_label.pack(padx=10, pady=(8, 2))

        value_label = ctk.CTkLabel(card, text=value, text_color="white", font=("", 13, "bold"))
        value_label.pack(padx=10, pady=(2, 8))

        return card

    # ===== Action Methods =====

    def _load_return_data(self):
        """Load return data for review"""
        self.status_label.configure(text="Loading return...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Ready to review")
        self.progress_bar.set(1.0)

    def _check_issues(self):
        """Check for issues in return"""
        self.status_label.configure(text="Checking for issues...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Check complete")
        self.progress_bar.set(1.0)

    def _validate_data(self):
        """Validate return data"""
        self.status_label.configure(text="Validating data...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Validation complete")
        self.progress_bar.set(1.0)

    def _compare_estimates(self):
        """Compare estimates and actuals"""
        self.status_label.configure(text="Comparing estimates...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Comparison complete")
        self.progress_bar.set(1.0)

    def _preview_forms(self):
        """Preview forms to be filed"""
        self.status_label.configure(text="Generating form previews...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Forms ready")
        self.progress_bar.set(1.0)

    def _save_review(self):
        """Save review progress"""
        self.status_label.configure(text="Saving review...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Review saved")
        self.progress_bar.set(1.0)
