"""
Modern Income Page - CustomTkinter Implementation

A comprehensive income collection interface with modern UI,
organized by income type with intelligent validation and guidance.
"""

import customtkinter as ctk
from typing import Optional, Dict, Any, List
from datetime import datetime
import re

# Import dialog classes
from .modern_income_dialogs import (
    ModernW2Dialog,
    ModernInterestDialog,
    ModernDividendDialog,
    ModernSelfEmploymentDialog,
    ModernRetirementDialog,
    ModernSocialSecurityDialog,
    ModernCapitalGainDialog,
    ModernRentalDialog
)


class ModernIncomePage(ctk.CTkScrollableFrame):
    """
    Modern income collection page using CustomTkinter.

    Features:
    - Organized income sections with modern cards
    - Interactive income type selection
    - Real-time validation and calculations
    - Form 8949 generation and wash sale detection
    - Progress tracking and contextual help
    """

    def __init__(self, master, config, tax_data: Optional[Dict[str, Any]] = None,
                 on_complete=None, **kwargs):
        """
        Initialize the modern income page.

        Args:
            master: Parent widget
            config: Application configuration
            tax_data: Current tax data dictionary
            on_complete: Callback when form is completed
        """
        super().__init__(master, **kwargs)

        self.config = config
        self.tax_data = tax_data or {}
        self.on_complete = on_complete

        # Build the form
        self._build_form()

        # Load existing data
        self._load_existing_data()

    def _build_form(self):
        """Build the modern income form"""
        # Main content frame
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header section
        header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        title_label = ctk.CTkLabel(
            header_frame,
            text="Income Information",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(anchor="w", pady=(0, 5))

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Report all sources of income you received during the tax year. We'll help you organize and validate your income entries.",
            font=ctk.CTkFont(size=12),
            text_color="gray60",
            wraplength=600
        )
        subtitle_label.pack(anchor="w")

        # Income summary section
        self._build_income_summary(content_frame)

        # Income sections
        self._build_income_sections(content_frame)

        # Special tools section
        self._build_special_tools(content_frame)

        # Action buttons
        self._build_action_buttons(content_frame)

    def _build_income_summary(self, parent):
        """Build the income summary section"""
        summary_frame = ctk.CTkFrame(parent)
        summary_frame.pack(fill="x", pady=(0, 20))

        summary_title = ctk.CTkLabel(
            summary_frame,
            text="💰 Income Summary",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        summary_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Summary grid
        summary_grid = ctk.CTkFrame(summary_frame, fg_color="transparent")
        summary_grid.pack(fill="x", padx=15, pady=(0, 15))

        # Initialize summary labels
        self.summary_labels = {}

        summary_items = [
            ("W-2 Wages", "w2_wages", "$0.00"),
            ("Interest Income", "interest", "$0.00"),
            ("Dividend Income", "dividends", "$0.00"),
            ("Self-Employment", "self_employment", "$0.00"),
            ("Retirement", "retirement", "$0.00"),
            ("Social Security", "ss_benefits", "$0.00"),
            ("Capital Gains", "capital_gains", "$0.00"),
            ("Rental Income", "rental", "$0.00"),
            ("Total Income", "total", "$0.00")
        ]

        for i, (label_text, key, default_value) in enumerate(summary_items):
            row = i // 3
            col = i % 3

            item_frame = ctk.CTkFrame(summary_grid, fg_color="transparent")
            item_frame.grid(row=row, column=col, padx=10, pady=5, sticky="w")

            label = ctk.CTkLabel(
                item_frame,
                text=f"{label_text}:",
                font=ctk.CTkFont(size=11)
            )
            label.pack(anchor="w")

            value_label = ctk.CTkLabel(
                item_frame,
                text=default_value,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#1f538d"
            )
            value_label.pack(anchor="w")

            self.summary_labels[key] = value_label

    def _build_income_sections(self, parent):
        """Build the income sections"""
        sections_frame = ctk.CTkFrame(parent)
        sections_frame.pack(fill="both", expand=True, pady=(0, 20))

        # Section title
        section_title = ctk.CTkLabel(
            sections_frame,
            text="Income Sources",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        section_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Income type cards
        self._build_income_type_cards(sections_frame)

    def _build_income_type_cards(self, parent):
        """Build income type selection cards"""
        cards_frame = ctk.CTkFrame(parent, fg_color="transparent")
        cards_frame.pack(fill="x", padx=15, pady=(0, 15))

        income_types = [
            {
                "key": "w2",
                "title": "W-2 Wages & Salaries",
                "description": "Wages, salaries, and tips from employers",
                "icon": "💼",
                "form": "W-2",
                "color": "#1f538d"
            },
            {
                "key": "interest",
                "title": "Interest Income",
                "description": "Interest from bank accounts, bonds (Form 1099-INT)",
                "icon": "💰",
                "form": "1099-INT",
                "color": "#2d7d32"
            },
            {
                "key": "dividends",
                "title": "Dividend Income",
                "description": "Dividends from stocks, mutual funds (Form 1099-DIV)",
                "icon": "📈",
                "form": "1099-DIV",
                "color": "#f57c00"
            },
            {
                "key": "self_employment",
                "title": "Self-Employment Income",
                "description": "Business income and expenses (Schedule C)",
                "icon": "🏢",
                "form": "Schedule C",
                "color": "#7b1fa2"
            },
            {
                "key": "retirement",
                "title": "Retirement Distributions",
                "description": "IRA, 401(k) distributions (Form 1099-R)",
                "icon": "🏖️",
                "form": "1099-R",
                "color": "#c21807"
            },
            {
                "key": "social_security",
                "title": "Social Security Benefits",
                "description": "SSA-1099 benefits received",
                "icon": "👴",
                "form": "SSA-1099",
                "color": "#00695c"
            },
            {
                "key": "capital_gains",
                "title": "Capital Gains & Losses",
                "description": "Investment gains/losses (Schedule D, Form 8949)",
                "icon": "📊",
                "form": "8949",
                "color": "#bf360c"
            },
            {
                "key": "rental",
                "title": "Rental Income",
                "description": "Income from rental properties (Schedule E)",
                "icon": "🏠",
                "form": "Schedule E",
                "color": "#4a148c"
            }
        ]

        self.income_cards = {}
        self.income_lists = {}

        for income_type in income_types:
            card = self._create_income_card(cards_frame, income_type)
            self.income_cards[income_type["key"]] = card
            card.pack(fill="x", pady=(0, 10))

    def _create_income_card(self, parent, income_type: Dict[str, Any]):
        """Create an income type card"""
        card_frame = ctk.CTkFrame(parent, border_width=1)

        # Header with icon and title
        header_frame = ctk.CTkFrame(card_frame, fg_color="transparent", height=50)
        header_frame.pack(fill="x", padx=15, pady=(15, 0))
        header_frame.pack_propagate(False)

        icon_label = ctk.CTkLabel(
            header_frame,
            text=income_type["icon"],
            font=ctk.CTkFont(size=24)
        )
        icon_label.pack(side="left", padx=(0, 10))

        title_label = ctk.CTkLabel(
            header_frame,
            text=income_type["title"],
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(side="left")

        form_label = ctk.CTkLabel(
            header_frame,
            text=income_type["form"],
            font=ctk.CTkFont(size=10),
            text_color="gray60"
        )
        form_label.pack(side="right")

        # Description
        desc_label = ctk.CTkLabel(
            card_frame,
            text=income_type["description"],
            font=ctk.CTkFont(size=11),
            text_color="gray60",
            wraplength=500
        )
        desc_label.pack(anchor="w", padx=15, pady=(5, 10))

        # Content area (initially hidden)
        content_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        # content_frame.pack(fill="x", padx=15, pady=(0, 15))  # Initially hidden

        # Items list
        list_frame = ctk.CTkScrollableFrame(content_frame, height=150)
        list_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Add button
        from gui.modern_ui_components import ModernButton

        button_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=(0, 15))

        add_button = ModernButton(
            button_frame,
            text=f"+ Add {income_type['title']}",
            command=lambda key=income_type["key"]: self._add_income_item(key),
            button_type="secondary"
        )
        add_button.pack(anchor="w")

        # Store references
        card_frame.content_frame = content_frame
        card_frame.list_frame = list_frame
        card_frame.income_type = income_type
        card_frame.is_expanded = False

        # Make card clickable to expand/collapse
        card_frame.bind("<Button-1>", lambda e, cf=card_frame: self._toggle_income_card(cf))
        header_frame.bind("<Button-1>", lambda e, cf=card_frame: self._toggle_income_card(cf))
        title_label.bind("<Button-1>", lambda e, cf=card_frame: self._toggle_income_card(cf))
        desc_label.bind("<Button-1>", lambda e, cf=card_frame: self._toggle_income_card(cf))

        # Store list reference
        self.income_lists[income_type["key"]] = list_frame

        return card_frame

    def _toggle_income_card(self, card_frame):
        """Toggle the expansion state of an income card"""
        if card_frame.is_expanded:
            # Collapse
            card_frame.content_frame.pack_forget()
            card_frame.configure(border_color="transparent")
            card_frame.is_expanded = False
        else:
            # Expand
            card_frame.content_frame.pack(fill="x", padx=15, pady=(0, 15))
            card_frame.configure(border_color=card_frame.income_type["color"])
            card_frame.is_expanded = True

    def _build_special_tools(self, parent):
        """Build the special tools section"""
        tools_frame = ctk.CTkFrame(parent)
        tools_frame.pack(fill="x", pady=(0, 20))

        tools_title = ctk.CTkLabel(
            tools_frame,
            text="🛠️ Tax Tools & Analysis",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        tools_title.pack(anchor="w", padx=15, pady=(15, 10))

        tools_grid = ctk.CTkFrame(tools_frame, fg_color="transparent")
        tools_grid.pack(fill="x", padx=15, pady=(0, 15))

        from gui.modern_ui_components import ModernButton

        # Wash sale checker
        wash_button = ModernButton(
            tools_grid,
            text="🔍 Check for Wash Sales",
            command=self._check_wash_sales,
            button_type="secondary"
        )
        wash_button.pack(side="left", padx=(0, 10))

        # Form 8949 generator
        form_8949_button = ModernButton(
            tools_grid,
            text="📄 Generate Form 8949",
            command=self._generate_form_8949,
            button_type="secondary"
        )
        form_8949_button.pack(side="left", padx=(0, 10))

        # Tax analysis
        analysis_button = ModernButton(
            tools_grid,
            text="📊 Income Analysis",
            command=self._show_income_analysis,
            button_type="secondary"
        )
        analysis_button.pack(side="left")

    def _build_action_buttons(self, parent):
        """Build action buttons"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", pady=(30, 20))

        # Progress indicator
        progress_label = ctk.CTkLabel(
            button_frame,
            text="Step 4 of 7: Income",
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        )
        progress_label.pack(anchor="w", pady=(0, 10))

        # Buttons
        button_row = ctk.CTkFrame(button_frame, fg_color="transparent")
        button_row.pack(fill="x")

        from gui.modern_ui_components import ModernButton

        ModernButton(
            button_row,
            text="← Back to Dependents",
            command=self._go_back,
            button_type="secondary"
        ).pack(side="left")

        ModernButton(
            button_row,
            text="Save and Continue →",
            command=self._save_and_continue,
            button_type="primary"
        ).pack(side="right")

    def load_data(self, tax_data: Dict[str, Any]):
        """Load tax data into the income page"""
        self.tax_data = tax_data
        self._load_existing_data()

    def _load_existing_data(self):
        """Load existing income data"""
        # Load W-2 data
        w2_forms = self.tax_data.get("income.w2_forms", [])
        self._refresh_income_list("w2", w2_forms)

        # Load interest data
        interest_income = self.tax_data.get("income.interest_income", [])
        self._refresh_income_list("interest", interest_income)

        # Load dividend data
        dividend_income = self.tax_data.get("income.dividend_income", [])
        self._refresh_income_list("dividends", dividend_income)

        # Load self-employment data
        self_employment = self.tax_data.get("income.self_employment", [])
        self._refresh_income_list("self_employment", self_employment)

        # Load retirement data
        retirement = self.tax_data.get("income.retirement_distributions", [])
        self._refresh_income_list("retirement", retirement)

        # Load social security data
        ss_benefits = self.tax_data.get("income.social_security", [])
        self._refresh_income_list("social_security", ss_benefits)

        # Load capital gains data
        capital_gains = self.tax_data.get("income.capital_gains", [])
        self._refresh_income_list("capital_gains", capital_gains)

        # Load rental data
        rental_income = self.tax_data.get("income.rental_income", [])
        self._refresh_income_list("rental", rental_income)

        # Update summary
        self._update_income_summary()

    def _refresh_income_list(self, income_type: str, items: List[Dict[str, Any]]):
        """Refresh the display for a specific income type"""
        list_frame = self.income_lists.get(income_type)
        if not list_frame:
            return

        # Clear existing items
        for widget in list_frame.winfo_children():
            widget.destroy()

        if not items:
            empty_label = ctk.CTkLabel(
                list_frame,
                text="No items added yet",
                font=ctk.CTkFont(size=11),
                text_color="gray60"
            )
            empty_label.pack(pady=20)
            return

        # Add items
        for i, item in enumerate(items):
            self._create_income_item(list_frame, income_type, item, i)

    def _create_income_item(self, parent, income_type: str, item: Dict[str, Any], index: int):
        """Create an income item display"""
        item_frame = ctk.CTkFrame(parent, border_width=1, border_color="gray80")
        item_frame.pack(fill="x", pady=(0, 5))

        # Content based on income type
        if income_type == "w2":
            title = f"{item.get('employer', 'Unknown Employer')}"
            subtitle = f"Wages: ${item.get('wages', 0):,.2f}"
        elif income_type == "interest":
            title = f"{item.get('payer', 'Unknown Payer')}"
            subtitle = f"Interest: ${item.get('amount', 0):,.2f}"
        elif income_type == "dividends":
            title = f"{item.get('payer', 'Unknown Payer')}"
            subtitle = f"Dividends: ${item.get('amount', 0):,.2f}"
        elif income_type == "self_employment":
            title = f"{item.get('business_name', 'Unnamed Business')}"
            subtitle = f"Net Profit: ${item.get('net_profit', 0):,.2f}"
        elif income_type == "retirement":
            title = f"{item.get('payer', 'Unknown Payer')}"
            subtitle = f"Taxable: ${item.get('taxable_amount', 0):,.2f}"
        elif income_type == "social_security":
            title = "Social Security Benefits"
            subtitle = f"Net Benefits: ${item.get('net_benefits', 0):,.2f}"
        elif income_type == "capital_gains":
            title = f"{item.get('description', 'Unknown Asset')}"
            gain_loss = item.get('gain_loss', 0)
            gain_text = f"Gain: ${gain_loss:,.2f}" if gain_loss >= 0 else f"Loss: ${abs(gain_loss):,.2f}"
            subtitle = f"{item.get('holding_period', 'Unknown')} | {gain_text}"
        elif income_type == "rental":
            title = f"{item.get('property_address', 'Unknown Property')}"
            subtitle = f"Net Income: ${item.get('net_income', 0):,.2f}"
        else:
            title = "Unknown Income Type"
            subtitle = "Amount: $0.00"

        # Title
        title_label = ctk.CTkLabel(
            item_frame,
            text=title,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        title_label.pack(anchor="w", padx=10, pady=(10, 0))

        # Subtitle
        subtitle_label = ctk.CTkLabel(
            item_frame,
            text=subtitle,
            font=ctk.CTkFont(size=10),
            text_color="gray60"
        )
        subtitle_label.pack(anchor="w", padx=10, pady=(0, 10))

        # Action buttons
        button_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=(0, 10))

        from gui.modern_ui_components import ModernButton

        edit_button = ModernButton(
            button_frame,
            text="Edit",
            command=lambda: self._edit_income_item(income_type, index),
            button_type="secondary",
            width=60,
            height=25
        )
        edit_button.pack(side="right", padx=(5, 0))

        delete_button = ModernButton(
            button_frame,
            text="Delete",
            command=lambda: self._delete_income_item(income_type, index),
            button_type="danger",
            width=60,
            height=25
        )
        delete_button.pack(side="right")

    def _update_income_summary(self):
        """Update the income summary display"""
        # Calculate totals
        w2_total = sum(item.get('wages', 0) for item in self.tax_data.get("income.w2_forms", []))
        interest_total = sum(item.get('amount', 0) for item in self.tax_data.get("income.interest_income", []))
        dividend_total = sum(item.get('amount', 0) for item in self.tax_data.get("income.dividend_income", []))
        se_total = sum(item.get('net_profit', 0) for item in self.tax_data.get("income.self_employment", []))
        retirement_total = sum(item.get('taxable_amount', 0) for item in self.tax_data.get("income.retirement_distributions", []))
        ss_total = sum(item.get('net_benefits', 0) for item in self.tax_data.get("income.social_security", []))
        capital_total = sum(item.get('gain_loss', 0) for item in self.tax_data.get("income.capital_gains", []))
        rental_total = sum(item.get('net_income', 0) for item in self.tax_data.get("income.rental_income", []))

        total_income = (w2_total + interest_total + dividend_total + se_total +
                       retirement_total + ss_total + capital_total + rental_total)

        # Update labels
        self.summary_labels["w2_wages"].configure(text=f"${w2_total:,.2f}")
        self.summary_labels["interest"].configure(text=f"${interest_total:,.2f}")
        self.summary_labels["dividends"].configure(text=f"${dividend_total:,.2f}")
        self.summary_labels["self_employment"].configure(text=f"${se_total:,.2f}")
        self.summary_labels["retirement"].configure(text=f"${retirement_total:,.2f}")
        self.summary_labels["ss_benefits"].configure(text=f"${ss_total:,.2f}")
        self.summary_labels["capital_gains"].configure(text=f"${capital_total:,.2f}")
        self.summary_labels["rental"].configure(text=f"${rental_total:,.2f}")
        self.summary_labels["total"].configure(text=f"${total_income:,.2f}")

    def _add_income_item(self, income_type: str):
        """Add a new income item"""
        if income_type == "w2":
            dialog = ModernW2Dialog(self, self.config, on_save=lambda data: self._on_income_saved("w2", data))
        elif income_type == "interest":
            dialog = ModernInterestDialog(self, self.config, on_save=lambda data: self._on_income_saved("interest", data))
        elif income_type == "dividends":
            dialog = ModernDividendDialog(self, self.config, on_save=lambda data: self._on_income_saved("dividends", data))
        elif income_type == "self_employment":
            dialog = ModernSelfEmploymentDialog(self, self.config, on_save=lambda data: self._on_income_saved("self_employment", data))
        elif income_type == "retirement":
            dialog = ModernRetirementDialog(self, self.config, on_save=lambda data: self._on_income_saved("retirement", data))
        elif income_type == "social_security":
            dialog = ModernSocialSecurityDialog(self, self.config, on_save=lambda data: self._on_income_saved("social_security", data))
        elif income_type == "capital_gains":
            dialog = ModernCapitalGainDialog(self, self.config, on_save=lambda data: self._on_income_saved("capital_gains", data))
        elif income_type == "rental":
            dialog = ModernRentalDialog(self, self.config, on_save=lambda data: self._on_income_saved("rental", data))

        if dialog:
            dialog.grab_set()

    def _edit_income_item(self, income_type: str, index: int):
        """Edit an existing income item"""
        # Get the data list for this income type
        data_key = self._get_data_key_for_income_type(income_type)
        items = self.tax_data.get(data_key, [])

        if index < len(items):
            item_data = items[index]

            if income_type == "w2":
                dialog = ModernW2Dialog(self, self.config, item_data=item_data, edit_index=index, on_save=lambda data, idx=index: self._on_income_updated("w2", data, idx))
            elif income_type == "interest":
                dialog = ModernInterestDialog(self, self.config, item_data=item_data, edit_index=index, on_save=lambda data, idx=index: self._on_income_updated("interest", data, idx))
            elif income_type == "dividends":
                dialog = ModernDividendDialog(self, self.config, item_data=item_data, edit_index=index, on_save=lambda data, idx=index: self._on_income_updated("dividends", data, idx))
            elif income_type == "self_employment":
                dialog = ModernSelfEmploymentDialog(self, self.config, item_data=item_data, edit_index=index, on_save=lambda data, idx=index: self._on_income_updated("self_employment", data, idx))
            elif income_type == "retirement":
                dialog = ModernRetirementDialog(self, self.config, item_data=item_data, edit_index=index, on_save=lambda data, idx=index: self._on_income_updated("retirement", data, idx))
            elif income_type == "social_security":
                dialog = ModernSocialSecurityDialog(self, self.config, item_data=item_data, edit_index=index, on_save=lambda data, idx=index: self._on_income_updated("social_security", data, idx))
            elif income_type == "capital_gains":
                dialog = ModernCapitalGainDialog(self, self.config, item_data=item_data, edit_index=index, on_save=lambda data, idx=index: self._on_income_updated("capital_gains", data, idx))
            elif income_type == "rental":
                dialog = ModernRentalDialog(self, self.config, item_data=item_data, edit_index=index, on_save=lambda data, idx=index: self._on_income_updated("rental", data, idx))

            if dialog:
                dialog.grab_set()

    def _delete_income_item(self, income_type: str, index: int):
        """Delete an income item"""
        data_key = self._get_data_key_for_income_type(income_type)
        items = self.tax_data.get(data_key, [])

        if index < len(items):
            item = items[index]

            # Get item description for confirmation
            if income_type == "w2":
                description = f"W-2 from {item.get('employer', 'Unknown')}"
            elif income_type == "interest":
                description = f"Interest from {item.get('payer', 'Unknown')}"
            elif income_type == "dividends":
                description = f"Dividends from {item.get('payer', 'Unknown')}"
            elif income_type == "self_employment":
                description = f"Business: {item.get('business_name', 'Unknown')}"
            elif income_type == "retirement":
                description = f"Retirement from {item.get('payer', 'Unknown')}"
            elif income_type == "social_security":
                description = "Social Security benefits"
            elif income_type == "capital_gains":
                description = f"Capital gain: {item.get('description', 'Unknown')}"
            elif income_type == "rental":
                description = f"Rental: {item.get('property_address', 'Unknown')}"
            else:
                description = "Income item"

            # Show confirmation dialog
            from gui.modern_ui_components import show_confirmation_dialog
            show_confirmation_dialog(
                self,
                "Delete Income Item",
                f"Are you sure you want to delete this {description}?",
                lambda: self._confirm_delete_income_item(income_type, index)
            )

    def _confirm_delete_income_item(self, income_type: str, index: int):
        """Confirm deletion of income item"""
        data_key = self._get_data_key_for_income_type(income_type)
        items = self.tax_data.get(data_key, [])

        if index < len(items):
            items.pop(index)
            self.tax_data[data_key] = items

            # Refresh display
            self._refresh_income_list(income_type, items)
            self._update_income_summary()

            # Show success message
            from gui.modern_ui_components import show_success_message
            show_success_message("Income item deleted successfully.")

    def _get_data_key_for_income_type(self, income_type: str) -> str:
        """Get the data key for an income type"""
        key_map = {
            "w2": "income.w2_forms",
            "interest": "income.interest_income",
            "dividends": "income.dividend_income",
            "self_employment": "income.self_employment",
            "retirement": "income.retirement_distributions",
            "social_security": "income.social_security",
            "capital_gains": "income.capital_gains",
            "rental": "income.rental_income"
        }
        return key_map.get(income_type, "")

    def _on_income_saved(self, income_type: str, data: Dict[str, Any]):
        """Handle income item saved"""
        data_key = self._get_data_key_for_income_type(income_type)
        if data_key not in self.tax_data:
            self.tax_data[data_key] = []
        self.tax_data[data_key].append(data)

        # Refresh display
        items = self.tax_data[data_key]
        self._refresh_income_list(income_type, items)
        self._update_income_summary()

        # Show success message
        from gui.modern_ui_components import show_success_message
        show_success_message("Income item added successfully.")

    def _on_income_updated(self, income_type: str, data: Dict[str, Any], index: int):
        """Handle income item updated"""
        data_key = self._get_data_key_for_income_type(income_type)
        items = self.tax_data.get(data_key, [])

        if index < len(items):
            items[index] = data
            self.tax_data[data_key] = items

            # Refresh display
            self._refresh_income_list(income_type, items)
            self._update_income_summary()

            # Show success message
            from gui.modern_ui_components import show_success_message
            show_success_message("Income item updated successfully.")

    def _check_wash_sales(self):
        """Check for potential wash sales"""
        capital_gains = self.tax_data.get("income.capital_gains", [])

        if not capital_gains:
            from gui.modern_ui_components import show_info_message
            show_info_message("No Capital Gains", "No capital gains/losses to check for wash sales.")
            return

        # Simple wash sale detection (simplified version)
        wash_sales = []
        for i, gain1 in enumerate(capital_gains):
            if gain1.get('gain_loss', 0) < 0:  # Loss
                loss_date = self._parse_date(gain1.get('date_sold', ''))
                if loss_date:
                    for j, gain2 in enumerate(capital_gains):
                        if i != j and gain2.get('gain_loss', 0) > 0:  # Gain
                            gain_date = self._parse_date(gain2.get('date_acquired', ''))
                            if gain_date:
                                days_diff = abs((gain_date - loss_date).days)
                                if days_diff <= 30:  # Within 30 days
                                    wash_sales.append({
                                        'loss_description': gain1.get('description', 'Unknown'),
                                        'gain_description': gain2.get('description', 'Unknown'),
                                        'days_between': days_diff
                                    })

        if not wash_sales:
            from gui.modern_ui_components import show_info_message
            show_info_message("Wash Sale Check", "No potential wash sales detected in your capital gains transactions.")
            return

        # Show wash sale results
        self._show_wash_sale_results(wash_sales)

    def _parse_date(self, date_str: str):
        """Parse date string"""
        try:
            return datetime.strptime(date_str, '%m/%d/%Y')
        except:
            return None

    def _show_wash_sale_results(self, wash_sales: List[Dict[str, Any]]):
        """Show wash sale analysis results"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Wash Sale Analysis")
        dialog.geometry("700x500")

        dialog.transient(self)
        dialog.grab_set()

        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        title_label = ctk.CTkLabel(
            main_frame,
            text="🚨 Potential Wash Sales Detected",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 20))

        # Results text
        text_frame = ctk.CTkFrame(main_frame)
        text_frame.pack(fill="both", expand=True)

        text_widget = ctk.CTkTextbox(text_frame, wrap="word")
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)

        text_widget.insert("0.0", f"Found {len(wash_sales)} potential wash sale(s):\n\n")

        for i, ws in enumerate(wash_sales, 1):
            text_widget.insert("end", f"Wash Sale #{i}:\n")
            text_widget.insert("end", f"  Loss: {ws['loss_description']}\n")
            text_widget.insert("end", f"  Purchase: {ws['gain_description']}\n")
            text_widget.insert("end", f"  Days Between: {ws['days_between']} days\n")
            text_widget.insert("end", "  ⚠️  This loss may be disallowed due to wash sale rules\n\n")

        text_widget.insert("end", "Note: This is a basic analysis. Wash sales occur when you sell securities at a loss\n")
        text_widget.insert("end", "and buy substantially identical securities within 30 days before or after the sale.\n")
        text_widget.insert("end", "Consult a tax professional for definitive wash sale determination.")

        text_widget.configure(state="disabled")

        # Close button
        ctk.CTkButton(main_frame, text="Close", command=dialog.destroy).pack(pady=(20, 0))

    def _generate_form_8949(self):
        """Generate Form 8949 summary"""
        capital_gains = self.tax_data.get("income.capital_gains", [])

        if not capital_gains:
            from gui.modern_ui_components import show_info_message
            show_info_message("Form 8949", "No capital gains/losses to report on Form 8949.")
            return

        # Show Form 8949 dialog
        self._show_form_8949_dialog(capital_gains)

    def _show_form_8949_dialog(self, capital_gains: List[Dict[str, Any]]):
        """Show Form 8949 summary dialog"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Form 8949 - Sales and Other Dispositions of Capital Assets")
        dialog.geometry("900x700")

        dialog.transient(self)
        dialog.grab_set()

        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        title_label = ctk.CTkLabel(
            main_frame,
            text="📄 Form 8949 Summary",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 20))

        # Create tabbed interface
        tabview = ctk.CTkTabview(main_frame)
        tabview.pack(fill="both", expand=True, pady=(0, 20))

        # Separate short-term and long-term
        short_term = [cg for cg in capital_gains if cg.get('holding_period') == 'Short-term']
        long_term = [cg for cg in capital_gains if cg.get('holding_period') == 'Long-term']

        if short_term:
            short_tab = tabview.add(f"Short-Term ({len(short_term)})")
            self._create_8949_tab(short_tab, short_term, "Short-Term")

        if long_term:
            long_tab = tabview.add(f"Long-Term ({len(long_term)})")
            self._create_8949_tab(long_tab, long_term, "Long-Term")

        # Summary tab
        summary_tab = tabview.add("Summary")
        self._create_8949_summary_tab(summary_tab, short_term, long_term)

        # Close button
        ctk.CTkButton(main_frame, text="Close", command=dialog.destroy).pack(pady=(0, 0))

    def _create_8949_tab(self, parent, transactions: List[Dict[str, Any]], holding_period: str):
        """Create a Form 8949 tab"""
        # Create scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(parent)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Header
        header_label = ctk.CTkLabel(
            scroll_frame,
            text=f"{holding_period} Capital Gains and Losses - Form 8949",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        header_label.pack(pady=(0, 20))

        # Transactions list
        for i, transaction in enumerate(transactions, 1):
            item_frame = ctk.CTkFrame(scroll_frame)
            item_frame.pack(fill="x", pady=(0, 10))

            # Transaction details
            desc = transaction.get('description', 'Unknown')
            acquired = transaction.get('date_acquired', 'Unknown')
            sold = transaction.get('date_sold', 'Unknown')
            proceeds = transaction.get('sales_price', 0)
            basis = transaction.get('adjusted_basis', transaction.get('cost_basis', 0))
            gain_loss = transaction.get('gain_loss', 0)

            details_text = f"""#{i}: {desc}
Date Acquired: {acquired} | Date Sold: {sold}
Sales Price: ${proceeds:,.2f} | Cost Basis: ${basis:,.2f}
Gain/Loss: ${gain_loss:,.2f}"""

            details_label = ctk.CTkLabel(
                item_frame,
                text=details_text,
                font=ctk.CTkFont(size=11),
                justify="left"
            )
            details_label.pack(anchor="w", padx=15, pady=10)

    def _create_8949_summary_tab(self, parent, short_term: List[Dict[str, Any]], long_term: List[Dict[str, Any]]):
        """Create the Form 8949 summary tab"""
        summary_frame = ctk.CTkFrame(parent, fg_color="transparent")
        summary_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Calculate totals
        short_proceeds = sum(t.get('sales_price', 0) for t in short_term)
        short_basis = sum(t.get('adjusted_basis', t.get('cost_basis', 0)) for t in short_term)
        short_net = sum(t.get('gain_loss', 0) for t in short_term)

        long_proceeds = sum(t.get('sales_price', 0) for t in long_term)
        long_basis = sum(t.get('adjusted_basis', t.get('cost_basis', 0)) for t in long_term)
        long_net = sum(t.get('gain_loss', 0) for t in long_term)

        total_proceeds = short_proceeds + long_proceeds
        total_basis = short_basis + long_basis
        total_net = short_net + long_net

        summary_text = f"""FORM 8949 SUMMARY

SHORT-TERM CAPITAL GAINS AND LOSSES:
  Total Proceeds: ${short_proceeds:,.2f}
  Total Cost Basis: ${short_basis:,.2f}
  Net Gain/Loss: ${short_net:,.2f}

LONG-TERM CAPITAL GAINS AND LOSSES:
  Total Proceeds: ${long_proceeds:,.2f}
  Total Cost Basis: ${long_basis:,.2f}
  Net Gain/Loss: ${long_net:,.2f}

COMBINED TOTALS:
  Total Proceeds: ${total_proceeds:,.2f}
  Total Cost Basis: ${total_basis:,.2f}
  Net Gain/Loss: ${total_net:,.2f}

Note: This summary is for informational purposes.
Use this data to complete Form 8949 and Schedule D."""

        summary_label = ctk.CTkLabel(
            summary_frame,
            text=summary_text,
            font=ctk.CTkFont(size=12),
            justify="left"
        )
        summary_label.pack(anchor="w")

    def _show_income_analysis(self):
        """Show income analysis dialog"""
        # Calculate income breakdown
        income_breakdown = self._calculate_income_breakdown()

        dialog = ctk.CTkToplevel(self)
        dialog.title("Income Analysis")
        dialog.geometry("600x500")

        dialog.transient(self)
        dialog.grab_set()

        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        title_label = ctk.CTkLabel(
            main_frame,
            text="📊 Income Analysis",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 20))

        # Analysis text
        analysis_text = f"""INCOME BREAKDOWN

Total Income: ${income_breakdown['total']:,.2f}

INCOME SOURCES:
• W-2 Wages: ${income_breakdown['w2']:,.2f} ({income_breakdown['w2_pct']:.1f}%)
• Interest: ${income_breakdown['interest']:,.2f} ({income_breakdown['interest_pct']:.1f}%)
• Dividends: ${income_breakdown['dividends']:,.2f} ({income_breakdown['dividends_pct']:.1f}%)
• Self-Employment: ${income_breakdown['self_employment']:,.2f} ({income_breakdown['se_pct']:.1f}%)
• Retirement: ${income_breakdown['retirement']:,.2f} ({income_breakdown['retirement_pct']:.1f}%)
• Social Security: ${income_breakdown['ss']:,.2f} ({income_breakdown['ss_pct']:.1f}%)
• Capital Gains: ${income_breakdown['capital']:,.2f} ({income_breakdown['capital_pct']:.1f}%)
• Rental: ${income_breakdown['rental']:,.2f} ({income_breakdown['rental_pct']:.1f}%)

TAX IMPLICATIONS:
• Primary income source: {income_breakdown['primary_source']}
• Diversification level: {income_breakdown['diversification']}
• Estimated tax bracket: {income_breakdown['tax_bracket']}"""

        analysis_label = ctk.CTkLabel(
            main_frame,
            text=analysis_text,
            font=ctk.CTkFont(size=12),
            justify="left"
        )
        analysis_label.pack(anchor="w")

        # Close button
        ctk.CTkButton(main_frame, text="Close", command=dialog.destroy).pack(pady=(20, 0))

    def _calculate_income_breakdown(self) -> Dict[str, Any]:
        """Calculate detailed income breakdown"""
        w2 = sum(item.get('wages', 0) for item in self.tax_data.get("income.w2_forms", []))
        interest = sum(item.get('amount', 0) for item in self.tax_data.get("income.interest_income", []))
        dividends = sum(item.get('amount', 0) for item in self.tax_data.get("income.dividend_income", []))
        se = sum(item.get('net_profit', 0) for item in self.tax_data.get("income.self_employment", []))
        retirement = sum(item.get('taxable_amount', 0) for item in self.tax_data.get("income.retirement_distributions", []))
        ss = sum(item.get('net_benefits', 0) for item in self.tax_data.get("income.social_security", []))
        capital = sum(item.get('gain_loss', 0) for item in self.tax_data.get("income.capital_gains", []))
        rental = sum(item.get('net_income', 0) for item in self.tax_data.get("income.rental_income", []))

        total = w2 + interest + dividends + se + retirement + ss + capital + rental

        # Calculate percentages
        def pct(amount): return (amount / total * 100) if total > 0 else 0

        # Determine primary source
        sources = [
            ("W-2 Wages", w2),
            ("Self-Employment", se),
            ("Retirement", retirement),
            ("Capital Gains", capital),
            ("Rental", rental),
            ("Interest", interest),
            ("Dividends", dividends),
            ("Social Security", ss)
        ]
        primary_source = max(sources, key=lambda x: x[1])[0] if sources else "None"

        # Determine diversification
        non_zero_sources = sum(1 for _, amount in sources if amount > 0)
        if non_zero_sources <= 1:
            diversification = "Low (single income source)"
        elif non_zero_sources <= 3:
            diversification = "Moderate"
        else:
            diversification = "High (diversified income)"

        # Estimate tax bracket (simplified)
        if total < 11000:
            tax_bracket = "10%"
        elif total < 44725:
            tax_bracket = "12%"
        elif total < 95375:
            tax_bracket = "22%"
        elif total < 182100:
            tax_bracket = "24%"
        elif total < 231250:
            tax_bracket = "32%"
        elif total < 578125:
            tax_bracket = "35%"
        else:
            tax_bracket = "37%"

        return {
            'total': total,
            'w2': w2, 'w2_pct': pct(w2),
            'interest': interest, 'interest_pct': pct(interest),
            'dividends': dividends, 'dividends_pct': pct(dividends),
            'self_employment': se, 'se_pct': pct(se),
            'retirement': retirement, 'retirement_pct': pct(retirement),
            'ss': ss, 'ss_pct': pct(ss),
            'capital': capital, 'capital_pct': pct(capital),
            'rental': rental, 'rental_pct': pct(rental),
            'primary_source': primary_source,
            'diversification': diversification,
            'tax_bracket': tax_bracket
        }

    def _save_and_continue(self):
        """Save form data and continue to next step"""
        # Mark income section as completed
        if "income" not in self.tax_data:
            self.tax_data["income"] = {}

        income_data = {
            "completed": True,
            "total_income": self._calculate_income_breakdown()['total']
        }

        if "income_section" not in self.tax_data:
            self.tax_data["income_section"] = {}
        self.tax_data["income_section"].update(income_data)

        # Call completion callback
        if self.on_complete:
            self.on_complete(self.tax_data)

    def _go_back(self):
        """Go back to the previous step"""
        if self.on_complete:
            self.on_complete(self.tax_data, action="back")

    def get_data(self) -> Dict[str, Any]:
        """Get the current form data"""
        return self.tax_data

    def is_complete(self) -> bool:
        """Check if the income section is complete"""
        income_section = self.tax_data.get("income_section", {})
        return income_section.get("completed", False)

    def get_progress_percentage(self) -> float:
        """Get completion percentage for this section"""
        if self.is_complete():
            return 100.0

        # Check if any income has been entered
        income_sources = [
            self.tax_data.get("income.w2_forms", []),
            self.tax_data.get("income.interest_income", []),
            self.tax_data.get("income.dividend_income", []),
            self.tax_data.get("income.self_employment", []),
            self.tax_data.get("income.retirement_distributions", []),
            self.tax_data.get("income.social_security", []),
            self.tax_data.get("income.capital_gains", []),
            self.tax_data.get("income.rental_income", [])
        ]

        has_any_income = any(len(source) > 0 for source in income_sources)
        return 100.0 if has_any_income else 0.0