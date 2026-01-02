"""
State Tax Calculator Window - Modernized

Interactive calculator for state tax computations with detailed analysis.
Uses CustomTkinter for modern, theme-aware interface.
"""

import customtkinter as ctk
from typing import Dict, Optional
from datetime import datetime

from services.state_tax_integration_service import (
    StateTaxIntegrationService,
    StateCode,
    FilingStatus,
    StateIncome,
    StateDeductions
)
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton
from config.app_config import AppConfig


class StateTaxCalculatorWindow:
    """
    Interactive state tax calculator for quick tax computations.
    
    Features:
    - Real-time tax calculations
    - Multiple state support
    - Income and deduction inputs
    - Detailed tax breakdown
    - Effective and marginal rate display
    """

    def __init__(self, parent: ctk.CTk, config: AppConfig, 
                 accessibility_service: AccessibilityService = None):
        self.parent = parent
        self.config = config
        self.accessibility_service = accessibility_service
        self.service = StateTaxIntegrationService(config, None)

        # Window setup
        self.window = ctk.CTkToplevel(parent)
        self.window.title("State Tax Calculator")
        self.window.geometry("1400x800")
        self.window.configure(fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"])

        # Variables
        self.selected_state: Optional[StateCode] = None
        self.income_values = {}
        self.deduction_values = {}

        # Create layout
        self._create_header()
        self._create_main_content()
        self._create_status_bar()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self.window)
        header_frame.pack(fill=ctk.X, padx=20, pady=(20, 10))

        title_label = ModernLabel(
            header_frame,
            text="🧮 State Tax Calculator",
            font_size=24,
            font_weight="bold"
        )
        title_label.pack(anchor=ctk.W, pady=(0, 5))

        subtitle_label = ModernLabel(
            header_frame,
            text="Calculate state income taxes with real-time results",
            font_size=12,
            text_color="gray"
        )
        subtitle_label.pack(anchor=ctk.W)

    def _create_main_content(self):
        """Create the main content area"""
        main_container = ctk.CTkFrame(self.window, fg_color="transparent")
        main_container.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(0, weight=0)
        main_container.grid_columnconfigure(1, weight=1)

        # Left panel - Input controls
        self._create_input_panel(main_container)

        # Right panel - Results display
        self._create_results_panel(main_container)

    def _create_input_panel(self, parent: ctk.CTkFrame):
        """Create left input panel"""
        input_frame = ModernFrame(parent)
        input_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        input_frame.grid_rowconfigure(5, weight=1)

        # State selection
        ModernLabel(input_frame, text="State Selection", font_size=12, font_weight="bold").pack(anchor=ctk.W, padx=10, pady=(10, 5))

        state_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        state_frame.pack(fill=ctk.X, padx=10, pady=5)

        ModernLabel(state_frame, text="Select State:").pack(side=ctk.LEFT, padx=(0, 5))
        
        state_codes = [s.value for s in StateCode]
        self.state_var = ctk.StringVar(value="CA")
        state_combo = ctk.CTkComboBox(
            state_frame,
            variable=self.state_var,
            values=state_codes,
            command=self._on_state_change,
            width=150
        )
        state_combo.pack(side=ctk.LEFT)

        # Filing status
        ModernLabel(input_frame, text="Filing Status", font_size=12, font_weight="bold").pack(anchor=ctk.W, padx=10, pady=(15, 5))

        status_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        status_frame.pack(fill=ctk.X, padx=10, pady=5)

        self.filing_status_var = ctk.StringVar(value="single")
        for status in ["single", "married_filing_jointly", "married_filing_separately", "head_of_household"]:
            rb = ctk.CTkRadioButton(
                status_frame,
                text=status.replace("_", " ").title(),
                variable=self.filing_status_var,
                value=status,
                command=self._calculate
            )
            rb.pack(anchor=ctk.W, padx=5, pady=2)

        # Income section
        ModernLabel(input_frame, text="Income Sources", font_size=12, font_weight="bold").pack(anchor=ctk.W, padx=10, pady=(15, 5))

        income_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        income_frame.pack(fill=ctk.X, padx=10, pady=5)
        income_frame.grid_columnconfigure(1, weight=1)

        self.income_entries = {}
        income_sources = ["Wages", "Interest", "Dividends", "Capital Gains", "Business Income", "Rental Income"]

        for idx, source in enumerate(income_sources):
            label = ctk.CTkLabel(income_frame, text=f"{source}:", text_color="gray", font=("", 10))
            label.grid(row=idx, column=0, sticky="w", padx=5, pady=3)

            entry = ctk.CTkEntry(income_frame, placeholder_text="$0", width=120)
            entry.grid(row=idx, column=1, sticky="ew", padx=5, pady=3)
            entry.bind("<KeyRelease>", lambda e, s=source.lower().replace(" ", "_"): self._on_input_change(s))
            self.income_entries[source.lower().replace(" ", "_")] = entry

        # Deductions section
        ModernLabel(input_frame, text="Deductions", font_size=12, font_weight="bold").pack(anchor=ctk.W, padx=10, pady=(15, 5))

        deduction_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        deduction_frame.pack(fill=ctk.X, padx=10, pady=5)
        deduction_frame.grid_columnconfigure(1, weight=1)

        self.deduction_entries = {}
        deductions = ["Standard Deduction", "Itemized Deductions", "Other Deductions"]

        for idx, deduction in enumerate(deductions):
            label = ctk.CTkLabel(deduction_frame, text=f"{deduction}:", text_color="gray", font=("", 10))
            label.grid(row=idx, column=0, sticky="w", padx=5, pady=3)

            entry = ctk.CTkEntry(deduction_frame, placeholder_text="$0", width=120)
            entry.grid(row=idx, column=1, sticky="ew", padx=5, pady=3)
            entry.bind("<KeyRelease>", lambda e, d=deduction.lower().replace(" ", "_"): self._on_input_change(d))
            self.deduction_entries[deduction.lower().replace(" ", "_")] = entry

        # Action buttons
        button_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        button_frame.pack(fill=ctk.X, padx=10, pady=(20, 0))

        ModernButton(
            button_frame,
            text="🧮 Calculate",
            command=self._calculate,
            button_type="primary",
            width=150
        ).pack(fill=ctk.X, pady=5)

        ModernButton(
            button_frame,
            text="🔄 Clear All",
            command=self._clear_inputs,
            button_type="secondary",
            width=150
        ).pack(fill=ctk.X, pady=5)

    def _create_results_panel(self, parent: ctk.CTkFrame):
        """Create right results panel"""
        results_frame = ModernFrame(parent)
        results_frame.grid(row=0, column=1, sticky="nsew")
        results_frame.grid_rowconfigure(2, weight=1)

        ModernLabel(results_frame, text="Calculation Results", font_size=12, font_weight="bold").pack(anchor=ctk.W, padx=10, pady=(10, 5))

        # Summary metrics
        metrics_frame = ctk.CTkFrame(results_frame, fg_color="transparent")
        metrics_frame.pack(fill=ctk.X, padx=10, pady=10)

        self.result_cards = {}
        metrics = [
            ("Gross Income", "gross_income"),
            ("Taxable Income", "taxable_income"),
            ("Tax Due", "tax_due"),
            ("Effective Rate", "effective_rate"),
            ("Marginal Rate", "marginal_rate")
        ]

        for row in range(2):
            for col in range(3):
                idx = row * 3 + col
                if idx < len(metrics):
                    metric_title, key = metrics[idx]
                    card = self._create_result_card(metrics_frame, metric_title)
                    card.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
                    self.result_cards[key] = card

        metrics_frame.grid_columnconfigure(0, weight=1)
        metrics_frame.grid_columnconfigure(1, weight=1)
        metrics_frame.grid_columnconfigure(2, weight=1)

        # Detailed breakdown
        ModernLabel(results_frame, text="Tax Breakdown", font_size=12, font_weight="bold").pack(anchor=ctk.W, padx=10, pady=(10, 5))

        self.breakdown_text = ctk.CTkTextbox(results_frame, height=300)
        self.breakdown_text.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)
        self.breakdown_text.insert("1.0", "Enter income and deductions, then click 'Calculate' to see detailed tax breakdown.")
        self.breakdown_text.configure(state="disabled")

        # Tax brackets display
        ModernLabel(results_frame, text="Applicable Tax Brackets", font_size=12, font_weight="bold").pack(anchor=ctk.W, padx=10, pady=(10, 5))

        self.brackets_text = ctk.CTkTextbox(results_frame, height=150)
        self.brackets_text.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)
        self.brackets_text.configure(state="disabled")

    def _create_result_card(self, parent, title):
        """Create a result metric card"""
        card = ctk.CTkFrame(parent, corner_radius=8, fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        
        title_label = ctk.CTkLabel(card, text=title, text_color="gray", font=("", 10))
        title_label.pack(padx=10, pady=(8, 2))

        value_label = ctk.CTkLabel(card, text="$0.00", text_color="white", font=("", 13, "bold"))
        value_label.pack(padx=10, pady=(2, 8))

        card.value_label = value_label
        return card

    def _create_status_bar(self):
        """Create status bar"""
        status_frame = ModernFrame(self.window)
        status_frame.pack(fill=ctk.X, padx=20, pady=10)

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Ready to calculate taxes",
            text_color="gray",
            font=("", 10)
        )
        self.status_label.pack(anchor=ctk.W)

    # ===== Action Methods =====

    def _on_state_change(self, state_code_str: str):
        """Handle state selection change"""
        try:
            self.selected_state = StateCode(state_code_str)
            self._update_tax_brackets()
            self._calculate()
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}")

    def _on_input_change(self, field_name: str):
        """Handle input change - recalculate"""
        self._calculate()

    def _get_income_total(self) -> float:
        """Get total income from entries"""
        total = 0.0
        for entry in self.income_entries.values():
            value = entry.get().replace("$", "").replace(",", "")
            if value:
                try:
                    total += float(value)
                except ValueError:
                    pass
        return total

    def _get_deductions_total(self) -> float:
        """Get total deductions from entries"""
        total = 0.0
        for entry in self.deduction_entries.values():
            value = entry.get().replace("$", "").replace(",", "")
            if value:
                try:
                    total += float(value)
                except ValueError:
                    pass
        return total

    def _calculate(self):
        """Perform tax calculation"""
        if not self.selected_state:
            try:
                self.selected_state = StateCode(self.state_var.get())
            except:
                return

        gross_income = self._get_income_total()
        total_deductions = self._get_deductions_total()
        taxable_income = max(0, gross_income - total_deductions)

        # Get state info
        state_info = self.service.state_tax_info.get(self.selected_state)
        if not state_info:
            self.status_label.configure(text="State information not available")
            return

        # Calculate tax
        tax_due = 0.0
        if state_info.flat_rate:
            tax_due = taxable_income * state_info.flat_rate
        elif state_info.tax_type.value == "no_income_tax":
            tax_due = 0.0
        else:
            # Progressive calculation would go here
            tax_due = taxable_income * 0.05  # Placeholder

        effective_rate = (tax_due / gross_income * 100) if gross_income > 0 else 0
        marginal_rate = (state_info.flat_rate * 100) if state_info.flat_rate else 5.0

        # Update result cards
        self.result_cards["gross_income"].value_label.configure(text=f"${gross_income:,.2f}")
        self.result_cards["taxable_income"].value_label.configure(text=f"${taxable_income:,.2f}")
        self.result_cards["tax_due"].value_label.configure(text=f"${tax_due:,.2f}")
        self.result_cards["effective_rate"].value_label.configure(text=f"{effective_rate:.2f}%")
        self.result_cards["marginal_rate"].value_label.configure(text=f"{marginal_rate:.2f}%")

        # Update breakdown
        self._update_breakdown(gross_income, total_deductions, taxable_income, tax_due)
        self.status_label.configure(text="Calculation complete")

    def _update_breakdown(self, gross: float, deductions: float, taxable: float, tax: float):
        """Update tax breakdown display"""
        breakdown_text = f"""Gross Income:             ${gross:>15,.2f}
Total Deductions:         ${deductions:>15,.2f}
─────────────────────────────────────
Taxable Income:           ${taxable:>15,.2f}

Tax Due:                  ${tax:>15,.2f}

State: {self.selected_state.value if self.selected_state else 'N/A'}
Filing Status: {self.filing_status_var.get().replace('_', ' ').title()}
"""

        self.breakdown_text.configure(state="normal")
        self.breakdown_text.delete("1.0", "end")
        self.breakdown_text.insert("1.0", breakdown_text)
        self.breakdown_text.configure(state="disabled")

    def _update_tax_brackets(self):
        """Update tax brackets display"""
        if not self.selected_state:
            return

        state_info = self.service.state_tax_info.get(self.selected_state)
        if not state_info:
            return

        brackets_text = f"State: {state_info.state_name}\n"
        brackets_text += f"Tax Type: {state_info.tax_type.value.replace('_', ' ').title()}\n"
        brackets_text += f"E-Filing: {'Yes' if state_info.e_filing_supported else 'No'}\n\n"

        if state_info.flat_rate:
            brackets_text += f"Flat Tax Rate: {state_info.flat_rate*100:.2f}%"
        elif state_info.tax_type.value == "no_income_tax":
            brackets_text += "No State Income Tax"
        else:
            brackets_text += "Progressive Tax System"

        self.brackets_text.configure(state="normal")
        self.brackets_text.delete("1.0", "end")
        self.brackets_text.insert("1.0", brackets_text)
        self.brackets_text.configure(state="disabled")

    def _clear_inputs(self):
        """Clear all input fields"""
        for entry in list(self.income_entries.values()) + list(self.deduction_entries.values()):
            entry.delete(0, "end")

        for card in self.result_cards.values():
            card.value_label.configure(text="$0.00")

        self.status_label.configure(text="Inputs cleared")
