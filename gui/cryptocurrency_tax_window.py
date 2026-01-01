"""
Cryptocurrency Tax Reporting Window

GUI for managing cryptocurrency transactions and tax reporting for Form 8949 and Schedule D.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
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

    def __init__(self, parent: tk.Tk, config: AppConfig, tax_data: Optional[TaxData] = None):
        """
        Initialize cryptocurrency tax reporting window.

        Args:
            parent: Parent window
            config: Application configuration
            tax_data: Tax return data to analyze
        """
        self.parent = parent
        self.config = config
        self.tax_data = tax_data
        self.error_tracker = get_error_tracker()

        # Initialize service
        self.crypto_service = CryptocurrencyTaxService(config)

        # Current data
        self.transactions: List[CryptoTransaction] = []
        self.capital_gains: List[CapitalGainLoss] = []
        self.holding_method = HoldingMethod.FIFO

        # UI components
        self.window: Optional[tk.Toplevel] = None
        self.notebook: Optional[ttk.Notebook] = None
        self.transactions_tree: Optional[ttk.Treeview] = None
        self.gains_tree: Optional[ttk.Treeview] = None
        self.progress_var: Optional[tk.DoubleVar] = None
        self.status_label: Optional[ttk.Label] = None

        # Form variables
        self.transaction_vars = {}
        self.filter_vars = {}

    def show(self):
        """Show the cryptocurrency tax reporting window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Cryptocurrency Tax Reporting - Freedom US Tax Return")
        self.window.geometry("1200x800")
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

        # Create main frame
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Cryptocurrency Tax Reporting",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 10))

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, pady=(0, 10))

        # Create tabs
        self._create_transactions_tab()
        self._create_gains_losses_tab()
        self._create_reports_tab()

        # Progress bar
        self.progress_var = tk.DoubleVar()
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill="x", pady=(0, 5))

        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(side="left", fill="x", expand=True)

        # Status label
        self.status_label = ttk.Label(progress_frame, text="Ready")
        self.status_label.pack(side="right", padx=(10, 0))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(
            button_frame,
            text="Import CSV",
            command=self._import_csv
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            button_frame,
            text="Export CSV",
            command=self._export_csv
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            button_frame,
            text="Calculate Gains",
            command=self._calculate_gains
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            button_frame,
            text="Generate Form 8949",
            command=self._generate_form_8949
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            button_frame,
            text="Close",
            command=self._close_window
        ).pack(side="right")

    def _create_transactions_tab(self):
        """Create the transactions management tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Transactions")

        # Split into left (list) and right (form) panels
        left_frame = ttk.Frame(tab)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        right_frame = ttk.LabelFrame(tab, text="Transaction Details")
        right_frame.pack(side="right", fill="both", padx=(5, 0))

        # Transactions list
        list_frame = ttk.LabelFrame(left_frame, text="Cryptocurrency Transactions")
        list_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Treeview for transactions
        columns = ("Date", "Type", "Cryptocurrency", "Amount", "Price", "Value", "Exchange")
        self.transactions_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.transactions_tree.heading(col, text=col)
            self.transactions_tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.transactions_tree.yview)
        self.transactions_tree.configure(yscrollcommand=scrollbar.set)

        self.transactions_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Transaction buttons
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill="x")

        ttk.Button(btn_frame, text="Add Transaction", command=self._add_transaction).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Edit Transaction", command=self._edit_transaction).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Delete Transaction", command=self._delete_transaction).pack(side="left", padx=(0, 5))

        # Transaction form
        self._create_transaction_form(right_frame)

    def _create_transaction_form(self, parent):
        """Create the transaction entry form"""
        # Date
        ttk.Label(parent, text="Date:").grid(row=0, column=0, sticky="w", pady=2)
        self.transaction_vars['date'] = tk.StringVar()
        date_entry = ttk.Entry(parent, textvariable=self.transaction_vars['date'])
        date_entry.grid(row=0, column=1, sticky="ew", pady=2, padx=(5, 0))

        # Type
        ttk.Label(parent, text="Type:").grid(row=1, column=0, sticky="w", pady=2)
        self.transaction_vars['type'] = tk.StringVar()
        type_combo = ttk.Combobox(
            parent,
            textvariable=self.transaction_vars['type'],
            values=[t.value for t in CryptoTransactionType],
            state="readonly"
        )
        type_combo.grid(row=1, column=1, sticky="ew", pady=2, padx=(5, 0))

        # Cryptocurrency
        ttk.Label(parent, text="Cryptocurrency:").grid(row=2, column=0, sticky="w", pady=2)
        self.transaction_vars['crypto'] = tk.StringVar()
        crypto_entry = ttk.Entry(parent, textvariable=self.transaction_vars['crypto'])
        crypto_entry.grid(row=2, column=1, sticky="ew", pady=2, padx=(5, 0))

        # Amount
        ttk.Label(parent, text="Amount:").grid(row=3, column=0, sticky="w", pady=2)
        self.transaction_vars['amount'] = tk.StringVar()
        amount_entry = ttk.Entry(parent, textvariable=self.transaction_vars['amount'])
        amount_entry.grid(row=3, column=1, sticky="ew", pady=2, padx=(5, 0))

        # Price per unit
        ttk.Label(parent, text="Price per Unit:").grid(row=4, column=0, sticky="w", pady=2)
        self.transaction_vars['price'] = tk.StringVar()
        price_entry = ttk.Entry(parent, textvariable=self.transaction_vars['price'])
        price_entry.grid(row=4, column=1, sticky="ew", pady=2, padx=(5, 0))

        # Exchange
        ttk.Label(parent, text="Exchange:").grid(row=5, column=0, sticky="w", pady=2)
        self.transaction_vars['exchange'] = tk.StringVar()
        exchange_entry = ttk.Entry(parent, textvariable=self.transaction_vars['exchange'])
        exchange_entry.grid(row=5, column=1, sticky="ew", pady=2, padx=(5, 0))

        # Notes
        ttk.Label(parent, text="Notes:").grid(row=6, column=0, sticky="nw", pady=2)
        self.transaction_vars['notes'] = tk.StringVar()
        notes_entry = tk.Text(parent, height=3, width=30)
        notes_entry.grid(row=6, column=1, sticky="ew", pady=2, padx=(5, 0))

        # Form buttons
        form_btn_frame = ttk.Frame(parent)
        form_btn_frame.grid(row=7, column=0, columnspan=2, pady=(10, 0))

        ttk.Button(form_btn_frame, text="Save", command=self._save_transaction).pack(side="left", padx=(0, 5))
        ttk.Button(form_btn_frame, text="Clear", command=self._clear_transaction_form).pack(side="left")

        # Configure grid weights
        parent.columnconfigure(1, weight=1)

    def _create_gains_losses_tab(self):
        """Create the capital gains and losses tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Capital Gains/Losses")

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