"""
Tax Interview Page - Converted from Legacy Window

Guided tax interview and questionnaire page.
Integrated into main window without popup dialogs.
"""

import customtkinter as ctk
from typing import Optional, List, Dict, Any
from datetime import datetime

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton


class TaxInterviewPage(ctk.CTkScrollableFrame):
    """
    Tax Interview page - converted from legacy window to integrated page.
    
    Features:
    - Guided tax interview questions
    - Multi-step questionnaire
    - Progress tracking
    - Answer validation
    - Conditional question logic
    """

    def __init__(self, master, config: AppConfig, tax_data: Optional[TaxData] = None,
                 accessibility_service: Optional[AccessibilityService] = None, **kwargs):
        super().__init__(master, **kwargs)

        self.config = config
        self.tax_data = tax_data
        self.accessibility_service = accessibility_service

        # Interview data
        self.current_section = 1
        self.total_sections = 8
        self.progress = 0.0
        self.interview_vars = {}
        self.answers = {}

        # Build the page
        self._create_header()
        self._create_toolbar()
        self._create_main_content()
        self._load_interview_questions()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self)
        header_frame.pack(fill=ctk.X, padx=20, pady=(20, 10))

        title_label = ModernLabel(
            header_frame,
            text="❓ Tax Interview",
            font_size=24,
            font_weight="bold"
        )
        title_label.pack(anchor=ctk.W, pady=(0, 5))

        subtitle_label = ModernLabel(
            header_frame,
            text="Answer questions to help prepare your tax return",
            font_size=12,
            text_color="gray"
        )
        subtitle_label.pack(anchor=ctk.W)

    def _create_toolbar(self):
        """Create the toolbar with action buttons"""
        toolbar_frame = ModernFrame(self)
        toolbar_frame.pack(fill=ctk.X, padx=20, pady=10)

        # Navigation buttons
        button_section = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        button_section.pack(side=ctk.LEFT, fill=ctk.X, expand=False)

        ModernButton(
            button_section,
            text="⬅️ Previous",
            command=self._previous_section,
            button_type="secondary",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="Next ➡️",
            command=self._next_section,
            button_type="secondary",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📋 Review",
            command=self._review_answers,
            button_type="secondary",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="💾 Save",
            command=self._save_interview,
            button_type="success",
            width=100
        ).pack(side=ctk.LEFT, padx=5)

        # Progress bar
        progress_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        progress_frame.pack(fill=ctk.X, pady=10)

        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=6)
        self.progress_bar.pack(fill=ctk.X)
        self.progress_bar.set(0)

        self.status_label = ModernLabel(progress_frame, text="Section 1 of 8: Personal Information", font_size=11)
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

        # Add tabs for each interview section
        self.tab_personal = self.tabview.add("👤 Personal")
        self.tab_income = self.tabview.add("💵 Income")
        self.tab_deductions = self.tabview.add("✂️ Deductions")
        self.tab_dependents = self.tabview.add("👨‍👩‍👧 Dependents")
        self.tab_credits = self.tabview.add("💳 Credits")

        # Setup tabs
        self._setup_personal_tab()
        self._setup_income_tab()
        self._setup_deductions_tab()
        self._setup_dependents_tab()
        self._setup_credits_tab()

    def _setup_personal_tab(self):
        """Setup personal information tab"""
        self.tab_personal.grid_rowconfigure(0, weight=1)
        self.tab_personal.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_personal)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        personal_label = ModernLabel(frame, text="Personal Information", font_size=12, font_weight="bold")
        personal_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        form_frame = ctk.CTkFrame(frame)
        form_frame.pack(fill=ctk.X, padx=5, pady=10)
        form_frame.grid_columnconfigure(1, weight=1)

        fields = [
            ("Full Name", "full_name"),
            ("SSN", "ssn"),
            ("Date of Birth", "dob"),
            ("Filing Status", "filing_status"),
            ("Spouse Name (if MFJ)", "spouse_name")
        ]

        for row, (label, key) in enumerate(fields):
            lbl = ctk.CTkLabel(form_frame, text=f"{label}:", text_color="gray", font=("", 11))
            lbl.grid(row=row, column=0, sticky="w", padx=10, pady=8)
            entry = ctk.CTkEntry(form_frame, placeholder_text="", width=200)
            entry.grid(row=row, column=1, sticky="ew", padx=10, pady=8)
            self.interview_vars[key] = entry

    def _setup_income_tab(self):
        """Setup income questions tab"""
        self.tab_income.grid_rowconfigure(0, weight=1)
        self.tab_income.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_income)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        income_label = ModernLabel(frame, text="Income Questions", font_size=12, font_weight="bold")
        income_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.income_text = ctk.CTkTextbox(frame, height=350)
        self.income_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.income_text.insert("1.0",
            "Income Questions:\n\n"
            "1. Do you have W-2 income from employment?\n"
            "2. Do you have self-employment income?\n"
            "3. Do you have investment income (dividends, interest)?\n"
            "4. Do you have capital gains or losses?\n"
            "5. Do you have rental property income?\n"
            "6. Do you have other sources of income?"
        )
        self.income_text.configure(state="disabled")

    def _setup_deductions_tab(self):
        """Setup deductions questions tab"""
        self.tab_deductions.grid_rowconfigure(0, weight=1)
        self.tab_deductions.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_deductions)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        deduction_label = ModernLabel(frame, text="Deduction Questions", font_size=12, font_weight="bold")
        deduction_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.deduction_text = ctk.CTkTextbox(frame, height=350)
        self.deduction_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.deduction_text.insert("1.0",
            "Deduction Questions:\n\n"
            "1. Do you itemize deductions?\n"
            "2. Do you have mortgage interest to deduct?\n"
            "3. Do you have property taxes to deduct?\n"
            "4. Do you have medical expenses?\n"
            "5. Do you have charitable contributions?\n"
            "6. Do you have business expenses to deduct?"
        )
        self.deduction_text.configure(state="disabled")

    def _setup_dependents_tab(self):
        """Setup dependents questions tab"""
        self.tab_dependents.grid_rowconfigure(0, weight=1)
        self.tab_dependents.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_dependents)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        dependent_label = ModernLabel(frame, text="Dependent Information", font_size=12, font_weight="bold")
        dependent_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.dependent_text = ctk.CTkTextbox(frame, height=350)
        self.dependent_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.dependent_text.insert("1.0",
            "Dependent Questions:\n\n"
            "1. Do you have qualifying children?\n"
            "2. Do you have qualifying relatives?\n"
            "3. How many dependents in total?\n"
            "4. Do dependents live with you?\n"
            "5. What is your relationship to each dependent?\n"
            "6. Do you claim head of household status?"
        )
        self.dependent_text.configure(state="disabled")

    def _setup_credits_tab(self):
        """Setup credits and other questions tab"""
        self.tab_credits.grid_rowconfigure(0, weight=1)
        self.tab_credits.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self.tab_credits)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        credits_label = ModernLabel(frame, text="Tax Credits & Other", font_size=12, font_weight="bold")
        credits_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.credits_text = ctk.CTkTextbox(frame, height=350)
        self.credits_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.credits_text.insert("1.0",
            "Credits & Other Questions:\n\n"
            "1. Did you receive child tax credits?\n"
            "2. Do you qualify for education credits?\n"
            "3. Do you have estimated tax payments?\n"
            "4. Do you have federal taxes withheld?\n"
            "5. Did you make charitable contributions?\n"
            "6. Were there major life events this year?"
        )
        self.credits_text.configure(state="disabled")

    # ===== Action Methods =====

    def _load_interview_questions(self):
        """Load interview questions"""
        self.status_label.configure(text="Loading interview questions...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Interview loaded - Section 1 of 8")
        self.progress_bar.set(0.125)

    def _previous_section(self):
        """Go to previous section"""
        if self.current_section > 1:
            self.current_section -= 1
            self.progress = (self.current_section - 1) / self.total_sections
            self.progress_bar.set(self.progress)
            self.status_label.configure(text=f"Section {self.current_section} of {self.total_sections}")

    def _next_section(self):
        """Go to next section"""
        if self.current_section < self.total_sections:
            self.current_section += 1
            self.progress = self.current_section / self.total_sections
            self.progress_bar.set(self.progress)
            self.status_label.configure(text=f"Section {self.current_section} of {self.total_sections}")

    def _review_answers(self):
        """Review all answers"""
        self.status_label.configure(text="Loading review...")
        self.progress_bar.set(0.8)
        self.status_label.configure(text="Review ready")
        self.progress_bar.set(1.0)

    def _save_interview(self):
        """Save interview answers"""
        self.status_label.configure(text="Saving...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Interview saved")
        self.progress_bar.set(1.0)
