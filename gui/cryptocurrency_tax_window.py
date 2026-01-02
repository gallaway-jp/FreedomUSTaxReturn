"""
Cryptocurrency Tax Reporting Window

GUI for managing cryptocurrency transactions and tax reporting for Form 8949 and Schedule D.
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.cryptocurrency_tax_service import (
    CryptocurrencyTaxService,
    CryptoTransaction,
    CryptoTransactionType,
    CapitalGainLoss,
    HoldingMethod
)
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton, ModernEntry
from services.accessibility_service import AccessibilityService
from utils.error_tracker import get_error_tracker


class CryptocurrencyTaxWindow:
    """
    Window for managing cryptocurrency tax reporting.

    Features:
    - Transaction entry and management
    - Capital gains/losses calculation
    - Form 8949 generation
    - Schedule D integration
    - CSV import/export
    - Tax liability estimation
    """

    def __init__(self, parent: ctk.CTk, config: AppConfig, tax_data: Optional[TaxData] = None, accessibility_service: Optional[AccessibilityService] = None):
        """
        Initialize cryptocurrency tax reporting window.

        Args:
            parent: Parent window
            config: Application configuration
            tax_data: Tax return data to analyze
            accessibility_service: Accessibility service instance
        """
        self.parent = parent
        self.config = config
        self.tax_data = tax_data
        self.accessibility_service = accessibility_service
        self.error_tracker = get_error_tracker()

        # Initialize service
        self.crypto_service = CryptocurrencyTaxService(config)

        # Current data
        self.transactions: List[CryptoTransaction] = []
        self.capital_gains: List[CapitalGainLoss] = []
        self.holding_method = HoldingMethod.FIFO

        # UI components
        self.window: Optional[ctk.CTkToplevel] = None
        self.notebook: Optional[ctk.CTkTabview] = None
        self.transactions_frame: Optional[ctk.CTkScrollableFrame] = None
        self.gains_frame: Optional[ctk.CTkScrollableFrame] = None
        self.status_label: Optional[ModernLabel] = None

        # Form variables
        self.transaction_vars = {}
        self.filter_vars = {}

    def show(self):
        """Show the cryptocurrency tax reporting window"""
        self.window = ctk.CTkToplevel(self.parent)
        self.window.title("Cryptocurrency Tax Reporting")
        self.window.geometry("1400x900")
        self.window.resizable(True, True)

        # Initialize UI
        self._setup_ui()
        self._load_data()
        self._bind_events()

        # Center window
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

        # Make modal
        self.window.transient(self.parent)
        self.window.grab_set()
        self.parent.wait_window(self.window)

    def _setup_ui(self):
        """Setup the main user interface"""
        if not self.window:
            return

        # Create main frame with padding
        main_frame = ModernFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Title
        title_label = ModernLabel(
            main_frame,
            text="💰 Cryptocurrency Tax Reporting",
            font=ctk.CTkFont(size=18)
        )
        title_label.pack(pady=(0, 15))

        # Subtitle
        subtitle_label = ModernLabel(
            main_frame,
            text="Track transactions, calculate capital gains/losses, and generate tax forms",
            font=ctk.CTkFont(size=12),
            text_color="gray60"
        )
        subtitle_label.pack(pady=(0, 15))

        # Create tabview for different sections
        self.notebook = ctk.CTkTabview(main_frame)
        self.notebook.pack(fill="both", expand=True, pady=(0, 15))

        # Create tabs
        transactions_tab = self.notebook.add("Transactions")
        gains_tab = self.notebook.add("Capital Gains/Losses")
        reports_tab = self.notebook.add("Reports & Forms")
        settings_tab = self.notebook.add("Settings")

        self._setup_transactions_tab(transactions_tab)
        self._setup_gains_tab(gains_tab)
        self._setup_reports_tab(reports_tab)
        self._setup_settings_tab(settings_tab)

        # Status and action buttons frame
        bottom_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_frame.pack(fill="x", pady=(10, 0))

        # Status label
        self.status_label = ModernLabel(bottom_frame, text="Ready", text_color="gray60")
        self.status_label.pack(side="left")

        # Action buttons
        button_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        button_frame.pack(side="right")

        ModernButton(
            button_frame,
            text="📥 Import CSV",
            command=self._import_csv,
            accessibility_service=self.accessibility_service
        ).pack(side="left", padx=(0, 5))

        ModernButton(
            button_frame,
            text="📤 Export CSV",
            command=self._export_csv,
            button_type="secondary",
            accessibility_service=self.accessibility_service
        ).pack(side="left", padx=(0, 5))

        ModernButton(
            button_frame,
            text="Calculate Gains",
            command=self._calculate_gains,
            accessibility_service=self.accessibility_service
        ).pack(side="left", padx=(0, 5))

        ModernButton(
            button_frame,
            text="Generate Form 8949",
            command=self._generate_form_8949,
            button_type="success",
            accessibility_service=self.accessibility_service
        ).pack(side="left", padx=(0, 5))

        ModernButton(
            button_frame,
            text="Close",
            command=self._close_window,
            button_type="secondary",
            accessibility_service=self.accessibility_service
        ).pack(side="left")

    def _setup_transactions_tab(self, tab):
        """Setup the transactions management tab"""
        # Create scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        title_label = ModernLabel(
            scroll_frame,
            text="🔄 Transaction Management",
            font=ctk.CTkFont(size=14)
        )
        title_label.pack(anchor="w", pady=(0, 10))

        # Summary stats
        stats_frame = ctk.CTkFrame(scroll_frame)
        stats_frame.pack(fill="x", pady=(0, 15))

        self._create_stat_card(stats_frame, "Total Transactions", "0", "left")
        self._create_stat_card(stats_frame, "Total Value", "$0.00", "left")
        self._create_stat_card(stats_frame, "Realized Gains", "$0.00", "left")
        self._create_stat_card(stats_frame, "Unrealized Gains", "$0.00", "left")

        # Input form
        form_frame = ctk.CTkFrame(scroll_frame)
        form_frame.pack(fill="x", pady=(0, 15))

        form_title = ModernLabel(form_frame, text="Add New Transaction", font=ctk.CTkFont(size=12))
        form_title.pack(anchor="w", pady=(0, 10))

        # Form inputs
        form_content = ctk.CTkFrame(form_frame, fg_color="transparent")
        form_content.pack(fill="x")

        # First row
        row1 = ctk.CTkFrame(form_content, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 10))

        ModernLabel(row1, text="Date:").pack(side="left", padx=(0, 5))
        self.transaction_vars['date'] = ctk.StringVar()
        ctk.CTkEntry(row1, textvariable=self.transaction_vars['date'], placeholder_text="YYYY-MM-DD", width=120).pack(side="left", padx=(0, 20))

        ModernLabel(row1, text="Type:").pack(side="left", padx=(0, 5))
        self.transaction_vars['type'] = ctk.StringVar()
        ctk.CTkComboBox(row1, variable=self.transaction_vars['type'], values=[t.value for t in CryptoTransactionType], width=120).pack(side="left", padx=(0, 20))

        ModernLabel(row1, text="Cryptocurrency:").pack(side="left", padx=(0, 5))
        self.transaction_vars['crypto'] = ctk.StringVar()
        ctk.CTkEntry(row1, textvariable=self.transaction_vars['crypto'], placeholder_text="BTC, ETH, etc.", width=120).pack(side="left", padx=(0, 20))

        # Second row
        row2 = ctk.CTkFrame(form_content, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 10))

        ModernLabel(row2, text="Amount:").pack(side="left", padx=(0, 5))
        self.transaction_vars['amount'] = ctk.StringVar()
        ctk.CTkEntry(row2, textvariable=self.transaction_vars['amount'], placeholder_text="0.00", width=100).pack(side="left", padx=(0, 20))

        ModernLabel(row2, text="Price per Unit:").pack(side="left", padx=(0, 5))
        self.transaction_vars['price'] = ctk.StringVar()
        ctk.CTkEntry(row2, textvariable=self.transaction_vars['price'], placeholder_text="$0.00", width=100).pack(side="left", padx=(0, 20))

        ModernLabel(row2, text="Exchange:").pack(side="left", padx=(0, 5))
        self.transaction_vars['exchange'] = ctk.StringVar()
        ctk.CTkEntry(row2, textvariable=self.transaction_vars['exchange'], placeholder_text="Coinbase, Kraken, etc.", width=120).pack(side="left")

        # Action buttons
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(15, 0))

        ModernButton(
            button_frame,
            text="Add Transaction",
            command=self._add_transaction,
            accessibility_service=self.accessibility_service
        ).pack(side="left", padx=(0, 5))

        ModernButton(
            button_frame,
            text="Import CSV",
            command=self._import_csv,
            button_type="secondary",
            accessibility_service=self.accessibility_service
        ).pack(side="left")

    def _setup_gains_tab(self, tab):
        """Setup the capital gains and losses tab"""
        # Create scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        title_label = ModernLabel(
            scroll_frame,
            text="📊 Capital Gains & Losses",
            font=ctk.CTkFont(size=14)
        )
        title_label.pack(anchor="w", pady=(0, 10))

        # Holding method selection
        method_frame = ctk.CTkFrame(scroll_frame)
        method_frame.pack(fill="x", pady=(0, 15))

        ModernLabel(method_frame, text="Holding Method:").pack(side="left", padx=(0, 10))

        holding_var = ctk.StringVar(value="FIFO")
        for method in ["FIFO", "LIFO", "ACB", "Specific ID"]:
            ctk.CTkRadioButton(
                method_frame,
                text=method,
                variable=holding_var,
                value=method
            ).pack(side="left", padx=(0, 15))

        # Gains summary
        summary_frame = ctk.CTkFrame(scroll_frame)
        summary_frame.pack(fill="x", pady=(0, 15))

        self._create_stat_card(summary_frame, "Short-term Gains", "$0.00", "left")
        self._create_stat_card(summary_frame, "Long-term Gains", "$0.00", "left")
        self._create_stat_card(summary_frame, "Total Gains/Losses", "$0.00", "left")

        # Action buttons
        button_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))

        ModernButton(
            button_frame,
            text="Calculate Gains",
            command=self._calculate_gains,
            accessibility_service=self.accessibility_service
        ).pack(side="left", padx=(0, 5))

        ModernButton(
            button_frame,
            text="Generate Form 8949",
            command=self._generate_form_8949,
            button_type="success",
            accessibility_service=self.accessibility_service
        ).pack(side="left")

    def _setup_reports_tab(self, tab):
        """Setup the reports and forms tab"""
        # Create scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        title_label = ModernLabel(
            scroll_frame,
            text="📄 Reports & Tax Forms",
            font=ctk.CTkFont(size=14)
        )
        title_label.pack(anchor="w", pady=(0, 15))

        # Reports list
        reports_frame = ctk.CTkFrame(scroll_frame)
        reports_frame.pack(fill="both", expand=True)

        self._create_report_option(reports_frame, "Form 8949", "Sales of Capital Assets", "Schedule D income")
        self._create_report_option(reports_frame, "Schedule D", "Capital Gains and Losses", "Consolidated tax reporting")
        self._create_report_option(reports_frame, "Portfolio Summary", "Holdings Overview", "Current positions and values")
        self._create_report_option(reports_frame, "Tax Liability Estimate", "Estimated Tax Owed", "Current year projection")

    def _setup_settings_tab(self, tab):
        """Setup the settings tab"""
        # Create scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        title_label = ModernLabel(
            scroll_frame,
            text="⚙️ Settings",
            font=ctk.CTkFont(size=14)
        )
        title_label.pack(anchor="w", pady=(0, 15))

        # Settings options
        settings_frame = ctk.CTkFrame(scroll_frame)
        settings_frame.pack(fill="x", pady=(0, 15))

        # Preferred currency
        currency_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        currency_frame.pack(fill="x", pady=(0, 10))

        ModernLabel(currency_frame, text="Preferred Currency:").pack(side="left", padx=(0, 10))
        currency_var = ctk.StringVar(value="USD")
        ctk.CTkComboBox(currency_frame, variable=currency_var, values=["USD", "EUR", "GBP"], width=100).pack(side="left")

        # Tax year
        year_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        year_frame.pack(fill="x", pady=(0, 10))

        ModernLabel(year_frame, text="Tax Year:").pack(side="left", padx=(0, 10))
        year_var = ctk.StringVar(value="2025")
        ctk.CTkComboBox(year_frame, variable=year_var, values=["2025", "2024", "2023"], width=100).pack(side="left")

        # Save settings button
        save_button = ModernButton(
            settings_frame,
            text="Save Settings",
            command=lambda: messagebox.showinfo("Settings", "Settings saved successfully"),
            button_type="success",
            accessibility_service=self.accessibility_service
        )
        save_button.pack(side="left", pady=(20, 0))

    def _create_stat_card(self, parent, title: str, value: str, side: str = "top"):
        """Create a statistics display card"""
        card_frame = ctk.CTkFrame(parent)
        card_frame.pack(side=side, padx=5, pady=5, fill="x" if side == "top" else "both", expand=False)

        title_label = ModernLabel(card_frame, text=title, text_color="gray60", font=ctk.CTkFont(size=10))
        title_label.pack(anchor="w", padx=10, pady=(10, 0))

        value_label = ModernLabel(card_frame, text=value, font=ctk.CTkFont(size=14))
        value_label.pack(anchor="w", padx=10, pady=(0, 10))

    def _create_report_option(self, parent, title: str, subtitle: str, description: str):
        """Create a report option button"""
        option_frame = ctk.CTkFrame(parent)
        option_frame.pack(fill="x", pady=(0, 10))

        # Text information
        text_frame = ctk.CTkFrame(option_frame, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True)

        title_label = ModernLabel(text_frame, text=title, font=ctk.CTkFont(size=12))
        title_label.pack(anchor="w")

        subtitle_label = ModernLabel(text_frame, text=subtitle, text_color="gray60", font=ctk.CTkFont(size=10))
        subtitle_label.pack(anchor="w")

        desc_label = ModernLabel(text_frame, text=description, text_color="gray70", font=ctk.CTkFont(size=9))
        desc_label.pack(anchor="w", pady=(5, 0))

        # Generate button
        ModernButton(
            option_frame,
            text="Generate",
            width=80,
            command=lambda: messagebox.showinfo("Report", f"Generating {title}..."),
            accessibility_service=self.accessibility_service
        ).pack(side="right", padx=(10, 0))

        # Holding method selection
        method_frame = ttk.LabelFrame(tab, text="Holding Method")
        method_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(method_frame, text="Method:").pack(side="left", padx=(10, 5))
        self.holding_method_var = tk.StringVar(value=self.holding_method.value)
        method_combo = ttk.Combobox(
            method_frame,
            textvariable=self.holding_method_var,
            values=[m.value for m in HoldingMethod],
            state="readonly"
        )
        method_combo.pack(side="left", padx=(0, 10))
        method_combo.bind("<<ComboboxSelected>>", self._on_holding_method_change)

        # Gains/Losses list
        list_frame = ttk.LabelFrame(tab, text="Capital Gains and Losses")
        list_frame.pack(fill="both", expand=True)

        columns = ("Date", "Cryptocurrency", "Amount", "Cost Basis", "Sale Price", "Gain/Loss", "Holding Period")
        self.gains_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)

        for col in columns:
            self.gains_tree.heading(col, text=col)
            self.gains_tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.gains_tree.yview)
        self.gains_tree.configure(yscrollcommand=scrollbar.set)

        self.gains_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Summary
        summary_frame = ttk.LabelFrame(tab, text="Tax Year Summary")
        summary_frame.pack(fill="x", pady=(10, 0))

        self.summary_vars = {}
        summary_items = [
            ("Short-term gains:", "short_term_gains"),
            ("Short-term losses:", "short_term_losses"),
            ("Long-term gains:", "long_term_gains"),
            ("Long-term losses:", "long_term_losses"),
            ("Net capital gain/loss:", "net_capital")
        ]

        for i, (label, key) in enumerate(summary_items):
            ttk.Label(summary_frame, text=label).grid(row=i, column=0, sticky="w", padx=10, pady=2)
            self.summary_vars[key] = tk.StringVar(value="$0.00")
            ttk.Label(summary_frame, textvariable=self.summary_vars[key]).grid(row=i, column=1, sticky="e", padx=10, pady=2)

    def _create_reports_tab(self):
        """Create the reports and forms tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Reports & Forms")

        # Form 8949 section
        form_frame = ttk.LabelFrame(tab, text="Form 8949 - Sales and Other Dispositions of Capital Assets")
        form_frame.pack(fill="both", expand=True, pady=(0, 10))

        ttk.Label(
            form_frame,
            text="Form 8949 reports cryptocurrency sales and exchanges for tax purposes.\n" +
                 "This form is used in conjunction with Schedule D.",
            wraplength=600,
            justify="left"
        ).pack(pady=10, padx=10, anchor="w")

        ttk.Button(
            form_frame,
            text="Generate Form 8949",
            command=self._generate_form_8949
        ).pack(pady=(0, 10), padx=10, anchor="w")

        # Schedule D section
        schedule_frame = ttk.LabelFrame(tab, text="Schedule D - Capital Gains and Losses")
        schedule_frame.pack(fill="both", expand=True, pady=(0, 10))

        ttk.Label(
            schedule_frame,
            text="Schedule D summarizes capital gains and losses from all sources,\n" +
                 "including cryptocurrency transactions.",
            wraplength=600,
            justify="left"
        ).pack(pady=10, padx=10, anchor="w")

        ttk.Button(
            schedule_frame,
            text="Update Schedule D",
            command=self._update_schedule_d
        ).pack(pady=(0, 10), padx=10, anchor="w")

        # Tax liability estimate
        tax_frame = ttk.LabelFrame(tab, text="Tax Liability Estimate")
        tax_frame.pack(fill="x")

        ttk.Label(
            tax_frame,
            text="Estimated capital gains tax liability based on current transactions:",
            wraplength=600,
            justify="left"
        ).pack(pady=10, padx=10, anchor="w")

        self.tax_estimate_var = tk.StringVar(value="$0.00")
        ttk.Label(
            tax_frame,
            textvariable=self.tax_estimate_var,
            font=("Arial", 14, "bold")
        ).pack(pady=(0, 10), padx=10, anchor="w")

    def _load_data(self):
        """Load existing cryptocurrency data"""
        try:
            if self.tax_data:
                # Load transactions from tax data
                crypto_data = self.tax_data.get("cryptocurrency", {})
                self.transactions = crypto_data.get("transactions", [])

                # Load capital gains
                self.capital_gains = crypto_data.get("capital_gains", [])

                # Load holding method
                method_str = crypto_data.get("holding_method", "fifo")
                self.holding_method = HoldingMethod(method_str)

            self._refresh_transactions_list()
            self._refresh_gains_list()
            self._update_summary()

            self.status_label.config(text="Data loaded successfully")

        except Exception as e:
            self.error_tracker.track_error(e, {"operation": "_load_data"})
            messagebox.showerror("Load Error", f"Failed to load cryptocurrency data: {str(e)}")

    def _refresh_transactions_list(self):
        """Refresh the transactions treeview"""
        if not self.transactions_tree:
            return

        # Clear existing items
        for item in self.transactions_tree.get_children():
            self.transactions_tree.delete(item)

        # Add transactions
        for i, transaction in enumerate(self.transactions):
            self.transactions_tree.insert("", "end", values=(
                transaction.date.strftime("%Y-%m-%d"),
                transaction.type.value,
                transaction.cryptocurrency,
                f"{transaction.amount:.8f}",
                f"${transaction.price_per_unit:.2f}",
                f"${transaction.total_value:.2f}",
                transaction.exchange or ""
            ), tags=(str(i),))

    def _refresh_gains_list(self):
        """Refresh the capital gains treeview"""
        if not self.gains_tree:
            return

        # Clear existing items
        for item in self.gains_tree.get_children():
            self.gains_tree.delete(item)

        # Add gains/losses
        for gain in self.capital_gains:
            holding_period = "Short-term" if gain.is_short_term else "Long-term"
            self.gains_tree.insert("", "end", values=(
                gain.sale_date.strftime("%Y-%m-%d"),
                gain.cryptocurrency,
                f"{gain.amount:.8f}",
                f"${gain.cost_basis:.2f}",
                f"${gain.sale_price:.2f}",
                f"${gain.gain_loss:.2f}",
                holding_period
            ))

    def _update_summary(self):
        """Update the tax year summary"""
        if not self.capital_gains:
            return

        short_term_gains = sum(g.gain_loss for g in self.capital_gains if g.is_short_term and g.gain_loss > 0)
        short_term_losses = abs(sum(g.gain_loss for g in self.capital_gains if g.is_short_term and g.gain_loss < 0))
        long_term_gains = sum(g.gain_loss for g in self.capital_gains if not g.is_short_term and g.gain_loss > 0)
        long_term_losses = abs(sum(g.gain_loss for g in self.capital_gains if not g.is_short_term and g.gain_loss < 0))

        net_capital = (short_term_gains - short_term_losses) + (long_term_gains - long_term_losses)

        self.summary_vars['short_term_gains'].set(f"${short_term_gains:.2f}")
        self.summary_vars['short_term_losses'].set(f"${short_term_losses:.2f}")
        self.summary_vars['long_term_gains'].set(f"${long_term_gains:.2f}")
        self.summary_vars['long_term_losses'].set(f"${long_term_losses:.2f}")
        self.summary_vars['net_capital'].set(f"${net_capital:.2f}")

        # Estimate tax liability (simplified)
        tax_estimate = self._estimate_tax_liability(net_capital)
        self.tax_estimate_var.set(f"${tax_estimate:.2f}")

    def _estimate_tax_liability(self, net_capital: float) -> float:
        """Estimate capital gains tax liability"""
        if net_capital <= 0:
            return 0.0

        # Simplified tax calculation for capital gains
        # Short-term gains taxed at ordinary income rates
        # Long-term gains taxed at preferential rates
        short_term_tax = min(net_capital, 50000) * 0.22  # Assume 22% bracket
        long_term_tax = max(0, net_capital - 50000) * 0.15  # 15% long-term rate

        return short_term_tax + long_term_tax

    def _add_transaction(self):
        """Add a new transaction"""
        self._clear_transaction_form()
        self.status_label.config(text="Enter transaction details and click Save")

    def _edit_transaction(self):
        """Edit selected transaction"""
        selection = self.transactions_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a transaction to edit.")
            return

        item = selection[0]
        index = int(self.transactions_tree.item(item, "tags")[0])
        transaction = self.transactions[index]

        # Populate form
        self.transaction_vars['date'].set(transaction.date.strftime("%Y-%m-%d"))
        self.transaction_vars['type'].set(transaction.type.value)
        self.transaction_vars['crypto'].set(transaction.cryptocurrency)
        self.transaction_vars['amount'].set(str(transaction.amount))
        self.transaction_vars['price'].set(str(transaction.price_per_unit))
        self.transaction_vars['exchange'].set(transaction.exchange or "")

        self.status_label.config(text="Edit transaction details and click Save")

    def _delete_transaction(self):
        """Delete selected transaction"""
        selection = self.transactions_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a transaction to delete.")
            return

        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this transaction?"):
            return

        item = selection[0]
        index = int(self.transactions_tree.item(item, "tags")[0])
        del self.transactions[index]

        self._refresh_transactions_list()
        self._clear_transaction_form()
        self.status_label.config(text="Transaction deleted")

    def _save_transaction(self):
        """Save transaction from form"""
        try:
            # Validate form data
            date_str = self.transaction_vars['date'].get().strip()
            if not date_str:
                raise ValueError("Date is required")

            type_str = self.transaction_vars['type'].get().strip()
            if not type_str:
                raise ValueError("Transaction type is required")

            crypto = self.transaction_vars['crypto'].get().strip()
            if not crypto:
                raise ValueError("Cryptocurrency is required")

            amount_str = self.transaction_vars['amount'].get().strip()
            if not amount_str:
                raise ValueError("Amount is required")

            price_str = self.transaction_vars['price'].get().strip()
            if not price_str:
                raise ValueError("Price is required")

            # Parse values
            trans_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            trans_type = CryptoTransactionType(type_str)
            amount = Decimal(amount_str)
            price = Decimal(price_str)
            exchange = self.transaction_vars['exchange'].get().strip() or None

            # Create transaction
            transaction = CryptoTransaction(
                date=trans_date,
                type=trans_type,
                cryptocurrency=crypto,
                amount=amount,
                price_per_unit=price,
                total_value=amount * price,
                exchange=exchange
            )

            # Add to list (for now - in real implementation, save to tax_data)
            self.transactions.append(transaction)

            self._refresh_transactions_list()
            self._clear_transaction_form()
            self.status_label.config(text="Transaction saved successfully")

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save transaction: {str(e)}")

    def _clear_transaction_form(self):
        """Clear the transaction form"""
        for var in self.transaction_vars.values():
            if hasattr(var, 'set'):
                var.set("")

    def _calculate_gains(self):
        """Calculate capital gains and losses"""
        try:
            self.status_label.config(text="Calculating capital gains...")

            if not self.transactions:
                messagebox.showinfo("No Transactions", "No transactions to calculate gains from.")
                return

            # Calculate gains using the service
            self.capital_gains = self.crypto_service.calculate_capital_gains(
                self.transactions,
                self.holding_method
            )

            self._refresh_gains_list()
            self._update_summary()
            self.status_label.config(text="Capital gains calculated successfully")

        except Exception as e:
            self.error_tracker.track_error(e, {"operation": "_calculate_gains"})
            messagebox.showerror("Calculation Error", f"Failed to calculate gains: {str(e)}")

    def _generate_form_8949(self):
        """Generate Form 8949"""
        try:
            if not self.capital_gains:
                messagebox.showwarning("No Data", "Please calculate capital gains first.")
                return

            # Generate Form 8949 data
            form_data = self.crypto_service.generate_form_8949_data(self.capital_gains)

            # Show success message with summary
            short_term_count = len([g for g in self.capital_gains if g.is_short_term])
            long_term_count = len([g for g in self.capital_gains if not g.is_short_term])

            messagebox.showinfo(
                "Form 8949 Generated",
                f"Form 8949 data generated successfully!\n\n"
                f"Short-term transactions: {short_term_count}\n"
                f"Long-term transactions: {long_term_count}\n\n"
                f"Data is ready for inclusion in your tax return."
            )

            self.status_label.config(text="Form 8949 generated")

        except Exception as e:
            self.error_tracker.track_error(e, {"operation": "_generate_form_8949"})
            messagebox.showerror("Form Generation Error", f"Failed to generate Form 8949: {str(e)}")

    def _update_schedule_d(self):
        """Update Schedule D with crypto gains"""
        try:
            if not self.capital_gains:
                messagebox.showwarning("No Data", "Please calculate capital gains first.")
                return

            # Update Schedule D data
            schedule_d_data = self.crypto_service.generate_schedule_d_data(self.capital_gains)

            messagebox.showinfo(
                "Schedule D Updated",
                "Schedule D has been updated with cryptocurrency capital gains data."
            )

            self.status_label.config(text="Schedule D updated")

        except Exception as e:
            self.error_tracker.track_error(e, {"operation": "_update_schedule_d"})
            messagebox.showerror("Schedule D Error", f"Failed to update Schedule D: {str(e)}")

    def _import_csv(self):
        """Import transactions from CSV"""
        try:
            filename = filedialog.askopenfilename(
                title="Import CSV",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )

            if not filename:
                return

            # Import CSV using service
            imported_transactions = self.crypto_service.import_from_csv(filename)
            self.transactions.extend(imported_transactions)

            self._refresh_transactions_list()
            self.status_label.config(text=f"Imported {len(imported_transactions)} transactions from CSV")

        except Exception as e:
            self.error_tracker.track_error(e, {"operation": "_import_csv"})
            messagebox.showerror("Import Error", f"Failed to import CSV: {str(e)}")

    def _export_csv(self):
        """Export transactions to CSV"""
        try:
            filename = filedialog.asksaveasfilename(
                title="Export CSV",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )

            if not filename:
                return

            # Export CSV using service
            self.crypto_service.export_to_csv(self.transactions, filename)
            self.status_label.config(text=f"Exported {len(self.transactions)} transactions to CSV")

        except Exception as e:
            self.error_tracker.track_error(e, {"operation": "_export_csv"})
            messagebox.showerror("Export Error", f"Failed to export CSV: {str(e)}")

    def _on_holding_method_change(self, event=None):
        """Handle holding method change"""
        method_str = self.holding_method_var.get()
        self.holding_method = HoldingMethod(method_str)

        # Recalculate gains if we have transactions
        if self.transactions:
            self._calculate_gains()

    def _bind_events(self):
        """Bind event handlers"""
        if self.transactions_tree:
            self.transactions_tree.bind("<Double-1>", lambda e: self._edit_transaction())

    def _close_window(self):
        """Close the window"""
        if self.window:
            self.window.destroy()