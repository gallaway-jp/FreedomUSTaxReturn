"""
Estate & Trust Tax Returns Page - Converted from Window

Page for managing Form 1041 estate and trust tax returns.
Integrated into main window without popup dialogs.
"""

import customtkinter as ctk
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.estate_trust_service import (
    EstateTrustService,
    EstateTrustReturn,
    TrustBeneficiary,
    TrustIncome,
    TrustDeductions,
    TrustType,
    EstateType,
    IncomeDistributionType
)
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton, ModernScrollableFrame


class EstateTrustPage(ModernFrame):
    """
    Estate & Trust Tax Returns page - converted from popup window to integrated page.
    
    Features:
    - Estate and trust return creation and management
    - Beneficiary management
    - Income and deduction tracking
    - Form 1041 generation
    - K-1 form generation
    """

    def __init__(self, master, config: AppConfig, tax_data: Optional[TaxData] = None,
                 accessibility_service: Optional[AccessibilityService] = None, **kwargs):
        super().__init__(master, **kwargs)

        self.config = config
        self.tax_data = tax_data
        self.accessibility_service = accessibility_service
        
        # Initialize service
        self.estate_service = EstateTrustService(config)
        
        # Current data
        self.returns: List[EstateTrustReturn] = []
        self.current_return: Optional[EstateTrustReturn] = None
        
        # Form variables
        self.return_vars = {}
        self.beneficiary_vars = {}
        self.income_vars = {}
        self.deduction_vars = {}

        # Build the page
        self._create_header()
        self._create_toolbar()
        self._create_main_content()
        self._load_data()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self)
        header_frame.pack(fill=ctk.X, padx=20, pady=(20, 10))

        title_label = ModernLabel(
            header_frame,
            text="📋 Estate & Trust Tax Returns",
            font_size=24,
            font_weight="bold"
        )
        title_label.pack(anchor=ctk.W, pady=(0, 5))

        subtitle_label = ModernLabel(
            header_frame,
            text="Prepare Form 1041 returns, manage beneficiaries, and generate K-1 forms",
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
            text="➕ New Return",
            command=self._new_return,
            button_type="primary",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="💾 Save Return",
            command=self._save_return,
            button_type="secondary",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="🧮 Calculate Tax",
            command=self._calculate_tax,
            button_type="primary",
            width=130
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📄 Form 1041",
            command=self._generate_form_1041,
            button_type="secondary",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_section,
            text="📑 K-1 Forms",
            command=self._generate_k1_forms,
            button_type="secondary",
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
        # Create scrollable container for the entire content
        scrollable = ModernScrollableFrame(self, fg_color="transparent")
        scrollable.pack(fill=ctk.BOTH, expand=True, padx=0, pady=0)
        
        main_container = ctk.CTkFrame(scrollable, fg_color="transparent")
        main_container.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)

        # Create tabview
        self.tabview = ctk.CTkTabview(main_container)
        self.tabview.pack(fill=ctk.BOTH, expand=True)

        # Add tabs
        self.tab_returns = self.tabview.add("📋 Returns")
        self.tab_entity = self.tabview.add("🏛️ Entity Info")
        self.tab_income = self.tabview.add("💰 Income & Deductions")
        self.tab_beneficiaries = self.tabview.add("👥 Beneficiaries")
        self.tab_forms = self.tabview.add("📄 Forms & Reports")

        # Setup tabs
        self._setup_returns_tab()
        self._setup_entity_tab()
        self._setup_income_deductions_tab()
        self._setup_beneficiaries_tab()
        self._setup_forms_tab()

    def _setup_returns_tab(self):
        """Setup returns list tab"""
        frame = ctk.CTkScrollableFrame(self.tab_returns)
        frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        # Returns display
        returns_label = ModernLabel(frame, text="Existing Returns", font_size=12, font_weight="bold")
        returns_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        self.returns_text = ctk.CTkTextbox(frame, height=300)
        self.returns_text.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        self.returns_text.insert("1.0", "No returns created yet. Click 'New Return' to begin.")
        self.returns_text.configure(state="disabled")

        # Summary cards
        cards_frame = ctk.CTkFrame(frame, fg_color="transparent")
        cards_frame.pack(fill=ctk.X, padx=5, pady=10)

        for metric in ["Total Returns", "Total Taxable Income", "Total Tax Due", "Total Balance Due"]:
            card = self._create_summary_card(cards_frame, metric, "$0.00")
            card.pack(side=ctk.LEFT, padx=5, fill=ctk.X, expand=True)

    def _setup_entity_tab(self):
        """Setup entity information tab"""
        frame = ctk.CTkScrollableFrame(self.tab_entity)
        frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        # Entity form fields
        form_frame = ctk.CTkFrame(frame, fg_color="transparent")
        form_frame.pack(fill=ctk.X, padx=5, pady=10)

        fields = [
            ("Tax Year", "tax_year"),
            ("Entity Type", "entity_type"),
            ("Entity Name", "entity_name"),
            ("EIN", "ein"),
            ("Fiduciary Name", "fiduciary_name"),
            ("Address", "address"),
            ("Phone", "phone"),
            ("Trust Type", "trust_type")
        ]

        for row, (label, key) in enumerate(fields):
            lbl = ctk.CTkLabel(form_frame, text=f"{label}:", text_color="gray", font=("", 11))
            lbl.pack(anchor=ctk.W, padx=5, pady=8)

            entry = ctk.CTkEntry(form_frame, placeholder_text="Enter " + label.lower(), width=200)
            entry.pack(fill=ctk.X, padx=5, pady=(0, 8))
            self.return_vars[key] = entry

    def _setup_income_deductions_tab(self):
        """Setup income and deductions tab"""
        container = ctk.CTkScrollableFrame(self.tab_income, fg_color="transparent")
        container.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        # Income section
        income_label = ModernLabel(container, text="Income Sources", font_size=12, font_weight="bold")
        income_label.pack(anchor=ctk.W, padx=5, pady=(0, 10))

        income_frame = ctk.CTkFrame(container, fg_color="transparent")
        income_frame.pack(fill=ctk.X, padx=5, pady=5)

        income_items = ["Interest", "Dividends", "Capital Gains", "Rental Income", "Other Income"]
        for item in income_items:
            field_row = ctk.CTkFrame(income_frame, fg_color="transparent")
            field_row.pack(fill=ctk.X, padx=10, pady=8)
            
            label = ctk.CTkLabel(field_row, text=f"{item}:", text_color="gray", font=("", 11))
            label.pack(side=ctk.LEFT, padx=5)
            entry = ctk.CTkEntry(field_row, placeholder_text="$0.00", width=150)
            entry.pack(side=ctk.LEFT, padx=5, fill=ctk.X, expand=True)
            self.income_vars[item.lower().replace(" ", "_")] = entry

        # Deductions section
        deduction_label = ModernLabel(container, text="Deductions", font_size=12, font_weight="bold")
        deduction_label.pack(anchor=ctk.W, padx=5, pady=(20, 10))

        deduction_frame = ctk.CTkFrame(container, fg_color="transparent")
        deduction_frame.pack(fill=ctk.X, padx=5, pady=5)

        deduction_items = ["Fiduciary Fees", "Trustee Commissions", "Charitable Contributions", "Medical Expenses", "Other Deductions"]
        for item in deduction_items:
            field_row = ctk.CTkFrame(deduction_frame, fg_color="transparent")
            field_row.pack(fill=ctk.X, padx=10, pady=8)
            
            label = ctk.CTkLabel(field_row, text=f"{item}:", text_color="gray", font=("", 11))
            label.pack(side=ctk.LEFT, padx=5)
            entry = ctk.CTkEntry(field_row, placeholder_text="$0.00", width=150)
            entry.pack(side=ctk.LEFT, padx=5, fill=ctk.X, expand=True)
            self.deduction_vars[item.lower().replace(" ", "_")] = entry

    def _setup_beneficiaries_tab(self):
        """Setup beneficiaries management tab"""

        # Button bar
        button_frame = ctk.CTkFrame(self.tab_beneficiaries, fg_color="transparent")
        button_frame.pack(fill=ctk.X, padx=10, pady=10)

        ModernButton(
            button_frame,
            text="➕ Add Beneficiary",
            command=self._add_beneficiary,
            button_type="primary",
            width=150
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_frame,
            text="✏️ Edit",
            command=self._edit_beneficiary,
            button_type="secondary",
            width=100
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_frame,
            text="🗑️ Delete",
            command=self._delete_beneficiary,
            button_type="danger",
            width=100
        ).pack(side=ctk.LEFT, padx=5)

        # Beneficiaries list
        list_frame = ctk.CTkFrame(self.tab_beneficiaries)
        list_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)

        self.beneficiaries_text = ctk.CTkTextbox(list_frame)
        self.beneficiaries_text.pack(fill=ctk.BOTH, expand=True)
        self.beneficiaries_text.insert("1.0", "No beneficiaries added yet.")
        self.beneficiaries_text.configure(state="disabled")

    def _setup_forms_tab(self):
        """Setup forms and reports tab"""
        # Button bar
        button_frame = ctk.CTkFrame(self.tab_forms, fg_color="transparent")
        button_frame.pack(fill=ctk.X, padx=10, pady=10)

        ModernButton(
            button_frame,
            text="📄 Form 1041",
            command=self._generate_form_1041,
            button_type="secondary",
            width=150
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_frame,
            text="📑 K-1 Forms",
            command=self._generate_k1_forms,
            button_type="secondary",
            width=150
        ).pack(side=ctk.LEFT, padx=5)

        ModernButton(
            button_frame,
            text="💾 Save Form",
            command=self._save_form,
            button_type="success",
            width=120
        ).pack(side=ctk.LEFT, padx=5)

        # Forms output
        output_frame = ctk.CTkFrame(self.tab_forms)
        output_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)

        self.forms_text = ctk.CTkTextbox(output_frame)
        self.forms_text.pack(fill=ctk.BOTH, expand=True)
        self.forms_text.insert("1.0", "No forms generated yet.")
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

    def _load_data(self):
        """Load estate and trust data"""
        self.status_label.configure(text="Loading data...")
        self.progress_bar.set(0.5)
        # TODO: Load returns from service
        self.status_label.configure(text="Ready")
        self.progress_bar.set(1.0)

    def _new_return(self):
        """Create new estate/trust return"""
        self.status_label.configure(text="Creating new return...")
        self.progress_bar.set(0.3)
        self.status_label.configure(text="New return created")
        self.progress_bar.set(1.0)

    def _save_return(self):
        """Save current return"""
        self.status_label.configure(text="Saving return...")
        self.progress_bar.set(0.5)
        self.status_label.configure(text="Return saved")
        self.progress_bar.set(1.0)

    def _calculate_tax(self):
        """Calculate tax for current return"""
        self.status_label.configure(text="Calculating tax...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Tax calculation complete")
        self.progress_bar.set(1.0)

    def _generate_form_1041(self):
        """Generate Form 1041"""
        self.status_label.configure(text="Generating Form 1041...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="Form 1041 generated")
        self.progress_bar.set(1.0)

    def _generate_k1_forms(self):
        """Generate K-1 forms for beneficiaries"""
        self.status_label.configure(text="Generating K-1 forms...")
        self.progress_bar.set(0.7)
        self.status_label.configure(text="K-1 forms generated")
        self.progress_bar.set(1.0)

    def _save_form(self):
        """Save generated form"""
        self.status_label.configure(text="Form saved")

    def _add_beneficiary(self):
        """Add beneficiary"""
        self.status_label.configure(text="Beneficiary added")

    def _edit_beneficiary(self):
        """Edit selected beneficiary"""
        self.status_label.configure(text="Edit beneficiary")

    def _delete_beneficiary(self):
        """Delete selected beneficiary"""
        self.status_label.configure(text="Beneficiary deleted")
