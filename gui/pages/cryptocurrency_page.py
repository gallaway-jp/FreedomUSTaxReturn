"""
Cryptocurrency Tax Reporting Page

Page for managing cryptocurrency transactions and tax reporting.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, List
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.cryptocurrency_tax_service import (
    CryptocurrencyTaxService,
    CryptoTransaction,
    CryptoTransactionType,
    CapitalGainLoss
)


class CryptocurrencyPage(ttk.Frame):
    """
    Page for cryptocurrency tax reporting.

    Allows users to:
    - Add/edit/delete cryptocurrency transactions
    - View capital gains/losses calculations
    - Generate tax reports
    - Import transactions from CSV
    """

    def __init__(self, parent, tax_data: TaxData, main_window, config: AppConfig):
        super().__init__(parent)
        self.tax_data = tax_data
        self.main_window = main_window
        self.config = config

        # Initialize service
        self.crypto_service = CryptocurrencyTaxService(config)

        # UI components
        self.transactions_tree = None
        self.gains_tree = None
        self.summary_labels = {}

        self.build_ui()
        self.load_data()

    def build_ui(self):
        """Build the page UI"""
        # Create main container with padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 10))

        title_label = ttk.Label(
            header_frame,
            text="Cryptocurrency Tax Reporting",
            font=("Arial", 16, "bold")
        )
        title_label.pack(anchor="w")

        description_label = ttk.Label(
            header_frame,
            text="Track cryptocurrency transactions and calculate capital gains/losses for tax reporting.",
            wraplength=600,
            justify="left"
        )
        description_label.pack(anchor="w", pady=(5, 0))

        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True, pady=(10, 0))

        # Transactions tab
        transactions_frame = ttk.Frame(notebook)
        notebook.add(transactions_frame, text="Transactions")

        self.build_transactions_tab(transactions_frame)

        # Gains/Losses tab
        gains_frame = ttk.Frame(notebook)
        notebook.add(gains_frame, text="Gains & Losses")

        self.build_gains_tab(gains_frame)

        # Summary tab
        summary_frame = ttk.Frame(notebook)
        notebook.add(summary_frame, text="Tax Summary")

        self.build_summary_tab(summary_frame)

    def build_transactions_tab(self, parent):
        """Build the transactions tab"""
        # Toolbar
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill="x", pady=(0, 10))

        ttk.Button(
            toolbar,
            text="Add Transaction",
            command=self.add_transaction
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Edit Selected",
            command=self.edit_selected_transaction
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Delete Selected",
            command=self.delete_selected_transaction
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Import CSV",
            command=self.import_csv
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Export for Tax Software",
            command=self.export_for_tax_software
        ).pack(side="right")

        # Transactions treeview
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill="both", expand=True)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal")

        self.transactions_tree = ttk.Treeview(
            tree_frame,
            columns=("date", "type", "crypto", "amount", "price", "total", "fees", "exchange"),
            show="headings",
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )

        # Configure columns
        self.transactions_tree.heading("date", text="Date")
        self.transactions_tree.heading("type", text="Type")
        self.transactions_tree.heading("crypto", text="Cryptocurrency")
        self.transactions_tree.heading("amount", text="Amount")
        self.transactions_tree.heading("price", text="Price/Unit")
        self.transactions_tree.heading("total", text="Total Value")
        self.transactions_tree.heading("fees", text="Fees")
        self.transactions_tree.heading("exchange", text="Exchange")

        self.transactions_tree.column("date", width=100)
        self.transactions_tree.column("type", width=80)
        self.transactions_tree.column("crypto", width=100)
        self.transactions_tree.column("amount", width=100)
        self.transactions_tree.column("price", width=100)
        self.transactions_tree.column("total", width=100)
        self.transactions_tree.column("fees", width=80)
        self.transactions_tree.column("exchange", width=100)

        # Pack tree and scrollbars
        self.transactions_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        v_scrollbar.config(command=self.transactions_tree.yview)
        h_scrollbar.config(command=self.transactions_tree.xview)

    def build_gains_tab(self, parent):
        """Build the gains/losses tab"""
        # Calculate button
        ttk.Button(
            parent,
            text="Calculate Gains & Losses",
            command=self.calculate_gains_losses
        ).pack(pady=(0, 10))

        # Gains/Losses treeview
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill="both", expand=True)

        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal")

        self.gains_tree = ttk.Treeview(
            tree_frame,
            columns=("description", "acquired", "sold", "sales_price", "cost_basis", "gain_loss", "period", "crypto"),
            show="headings",
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )

        # Configure columns
        self.gains_tree.heading("description", text="Description")
        self.gains_tree.heading("acquired", text="Date Acquired")
        self.gains_tree.heading("sold", text="Date Sold")
        self.gains_tree.heading("sales_price", text="Sales Price")
        self.gains_tree.heading("cost_basis", text="Cost Basis")
        self.gains_tree.heading("gain_loss", text="Gain/Loss")
        self.gains_tree.heading("period", text="Holding Period")
        self.gains_tree.heading("crypto", text="Crypto")

        self.gains_tree.column("description", width=200)
        self.gains_tree.column("acquired", width=100)
        self.gains_tree.column("sold", width=100)
        self.gains_tree.column("sales_price", width=100)
        self.gains_tree.column("cost_basis", width=100)
        self.gains_tree.column("gain_loss", width=100)
        self.gains_tree.column("period", width=100)
        self.gains_tree.column("crypto", width=80)

        # Pack tree and scrollbars
        self.gains_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        v_scrollbar.config(command=self.gains_tree.yview)
        h_scrollbar.config(command=self.gains_tree.xview)

    def build_summary_tab(self, parent):
        """Build the tax summary tab"""
        # Summary frame
        summary_frame = ttk.LabelFrame(parent, text="Tax Year Summary", padding="10")
        summary_frame.pack(fill="x", pady=(0, 10))

        # Summary labels
        summary_items = [
            ("Short-term Gains:", "short_term_gains"),
            ("Short-term Losses:", "short_term_losses"),
            ("Long-term Gains:", "long_term_gains"),
            ("Long-term Losses:", "long_term_losses"),
            ("Net Short-term:", "net_short_term"),
            ("Net Long-term:", "net_long_term"),
            ("Total Net Capital Gains:", "total_net_capital_gains"),
            ("Estimated Federal Tax:", "estimated_federal_tax"),
        ]

        for i, (label_text, key) in enumerate(summary_items):
            ttk.Label(summary_frame, text=label_text).grid(row=i, column=0, sticky="w", pady=2)
            self.summary_labels[key] = ttk.Label(summary_frame, text="$0.00")
            self.summary_labels[key].grid(row=i, column=1, sticky="e", pady=2, padx=(10, 0))

        # Refresh button
        ttk.Button(
            parent,
            text="Refresh Summary",
            command=self.refresh_summary
        ).pack(pady=(10, 0))

    def add_transaction(self):
        """Add a new transaction"""
        dialog = CryptoTransactionDialog(self, self.crypto_service, self.tax_data)
        if dialog.result:
            self.load_transactions()

    def edit_selected_transaction(self):
        """Edit the selected transaction"""
        selection = self.transactions_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a transaction to edit.")
            return

        # Get transaction data from selected row
        item = self.transactions_tree.item(selection[0])
        values = item['values']

        # This would need to be implemented to reconstruct the transaction
        # For now, show placeholder
        messagebox.showinfo("Edit Transaction", "Edit functionality coming soon!")

    def delete_selected_transaction(self):
        """Delete the selected transaction"""
        selection = self.transactions_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a transaction to delete.")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this transaction?"):
            # This would need to be implemented
            messagebox.showinfo("Delete Transaction", "Delete functionality coming soon!")

    def import_csv(self):
        """Import transactions from CSV"""
        filename = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if filename:
            try:
                successful, failed = self.crypto_service.import_from_csv(self.tax_data, filename)
                messagebox.showinfo(
                    "Import Complete",
                    f"Imported {successful} transactions successfully.\n"
                    f"{failed} transactions failed to import."
                )
                self.load_transactions()
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import CSV: {str(e)}")

    def export_for_tax_software(self):
        """Export data for tax software"""
        try:
            tax_year = self.tax_data.get_current_year()
            csv_data = self.crypto_service.export_for_turbotax(self.tax_data, tax_year)

            if not csv_data:
                messagebox.showwarning("No Data", "No cryptocurrency data to export.")
                return

            filename = filedialog.asksaveasfilename(
                title="Save CSV for Tax Software",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )

            if filename:
                with open(filename, 'w') as f:
                    f.write(csv_data)
                messagebox.showinfo("Export Complete", f"Data exported to {filename}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data: {str(e)}")

    def calculate_gains_losses(self):
        """Calculate and display gains/losses"""
        try:
            tax_year = self.tax_data.get_current_year()
            gains_losses = self.crypto_service.calculate_capital_gains_losses(self.tax_data, tax_year)

            # Clear existing items
            for item in self.gains_tree.get_children():
                self.gains_tree.delete(item)

            # Add gains/losses to tree
            for gl in gains_losses:
                self.gains_tree.insert("", "end", values=(
                    gl.description,
                    gl.date_acquired.strftime("%Y-%m-%d"),
                    gl.date_sold.strftime("%Y-%m-%d"),
                    f"${gl.sales_price:.2f}",
                    f"${gl.cost_basis:.2f}",
                    f"${gl.gain_loss:.2f}",
                    gl.holding_period,
                    gl.cryptocurrency
                ))

            messagebox.showinfo("Calculation Complete", f"Calculated {len(gains_losses)} capital gains/losses.")

        except Exception as e:
            messagebox.showerror("Calculation Error", f"Failed to calculate gains/losses: {str(e)}")

    def refresh_summary(self):
        """Refresh the tax summary"""
        try:
            tax_year = self.tax_data.get_current_year()
            summary = self.crypto_service.get_tax_liability_estimate(self.tax_data, tax_year)

            for key, label in self.summary_labels.items():
                value = summary.get(key, 0)
                if isinstance(value, Decimal):
                    label.config(text=f"${value:.2f}")
                else:
                    label.config(text=f"${value:.2f}")

        except Exception as e:
            messagebox.showerror("Summary Error", f"Failed to refresh summary: {str(e)}")

    def load_data(self):
        """Load all data"""
        self.load_transactions()
        self.refresh_summary()

    def load_transactions(self):
        """Load transactions into the treeview"""
        try:
            # Clear existing items
            for item in self.transactions_tree.get_children():
                self.transactions_tree.delete(item)

            # Load transactions
            transactions = self.crypto_service.get_transactions(self.tax_data)

            # Add to treeview
            for transaction in transactions:
                self.transactions_tree.insert("", "end", values=(
                    transaction.date.strftime("%Y-%m-%d"),
                    transaction.type.value.title(),
                    transaction.cryptocurrency,
                    f"{transaction.amount:.8f}",
                    f"${transaction.price_per_unit:.2f}",
                    f"${transaction.total_value:.2f}",
                    f"${transaction.fees:.2f}",
                    transaction.exchange
                ))

        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load transactions: {str(e)}")

    def on_show(self):
        """Called when this page is shown"""
        self.load_data()

    def validate_page(self) -> bool:
        """Validate the page data"""
        return True

    def save_data(self):
        """Save page data to tax data model"""
        pass  # Data is saved through the service

    def load_data_from_model(self):
        """Load data from tax data model"""
        self.load_data()


class CryptoTransactionDialog:
    """Dialog for adding/editing cryptocurrency transactions"""

    def __init__(self, parent, crypto_service: CryptocurrencyTaxService, tax_data: TaxData, edit_transaction=None):
        self.parent = parent
        self.crypto_service = crypto_service
        self.tax_data = tax_data
        self.edit_transaction = edit_transaction
        self.result = None

        self.build_dialog()

    def build_dialog(self):
        """Build the transaction dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Add Cryptocurrency Transaction")
        self.dialog.geometry("500x600")
        self.dialog.resizable(False, False)

        # Make dialog modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Form fields
        form_frame = ttk.Frame(self.dialog, padding="20")
        form_frame.pack(fill="both", expand=True)

        # Date
        ttk.Label(form_frame, text="Date:").grid(row=0, column=0, sticky="w", pady=5)
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(form_frame, textvariable=self.date_var).grid(row=0, column=1, sticky="ew", pady=5)

        # Type
        ttk.Label(form_frame, text="Type:").grid(row=1, column=0, sticky="w", pady=5)
        self.type_var = tk.StringVar(value="buy")
        type_combo = ttk.Combobox(
            form_frame,
            textvariable=self.type_var,
            values=[t.value for t in CryptoTransactionType],
            state="readonly"
        )
        type_combo.grid(row=1, column=1, sticky="ew", pady=5)

        # Cryptocurrency
        ttk.Label(form_frame, text="Cryptocurrency:").grid(row=2, column=0, sticky="w", pady=5)
        self.crypto_var = tk.StringVar(value="BTC")
        ttk.Entry(form_frame, textvariable=self.crypto_var).grid(row=2, column=1, sticky="ew", pady=5)

        # Amount
        ttk.Label(form_frame, text="Amount:").grid(row=3, column=0, sticky="w", pady=5)
        self.amount_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.amount_var).grid(row=3, column=1, sticky="ew", pady=5)

        # Price per unit
        ttk.Label(form_frame, text="Price per Unit ($):").grid(row=4, column=0, sticky="w", pady=5)
        self.price_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.price_var).grid(row=4, column=1, sticky="ew", pady=5)

        # Fees
        ttk.Label(form_frame, text="Fees ($):").grid(row=5, column=0, sticky="w", pady=5)
        self.fees_var = tk.StringVar(value="0.00")
        ttk.Entry(form_frame, textvariable=self.fees_var).grid(row=5, column=1, sticky="ew", pady=5)

        # Exchange
        ttk.Label(form_frame, text="Exchange:").grid(row=6, column=0, sticky="w", pady=5)
        self.exchange_var = tk.StringVar(value="Coinbase")
        ttk.Entry(form_frame, textvariable=self.exchange_var).grid(row=6, column=1, sticky="ew", pady=5)

        # Transaction ID
        ttk.Label(form_frame, text="Transaction ID:").grid(row=7, column=0, sticky="w", pady=5)
        self.tx_id_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.tx_id_var).grid(row=7, column=1, sticky="ew", pady=5)

        # Description
        ttk.Label(form_frame, text="Description:").grid(row=8, column=0, sticky="w", pady=5)
        self.desc_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.desc_var).grid(row=8, column=1, sticky="ew", pady=5)

        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=9, column=0, columnspan=2, pady=(20, 0))

        ttk.Button(
            button_frame,
            text="Save",
            command=self.save_transaction
        ).pack(side="left", padx=(0, 10))

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy
        ).pack(side="left")

        # Configure grid
        form_frame.columnconfigure(1, weight=1)

    def save_transaction(self):
        """Save the transaction"""
        try:
            # Validate inputs
            if not self.amount_var.get() or not self.price_var.get():
                messagebox.showerror("Validation Error", "Amount and price are required.")
                return

            # Create transaction
            transaction = CryptoTransaction(
                date=datetime.strptime(self.date_var.get(), "%Y-%m-%d").date(),
                type=CryptoTransactionType(self.type_var.get()),
                cryptocurrency=self.crypto_var.get().upper(),
                amount=Decimal(self.amount_var.get()),
                price_per_unit=Decimal(self.price_var.get()),
                total_value=Decimal(self.amount_var.get()) * Decimal(self.price_var.get()),
                fees=Decimal(self.fees_var.get() or "0"),
                exchange=self.exchange_var.get(),
                transaction_id=self.tx_id_var.get() or f"tx_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                description=self.desc_var.get()
            )

            # Save to service
            if self.crypto_service.add_transaction(self.tax_data, transaction):
                self.result = transaction
                self.dialog.destroy()
                messagebox.showinfo("Success", "Transaction added successfully!")
            else:
                messagebox.showerror("Error", "Failed to add transaction. Check for duplicate transaction ID.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save transaction: {str(e)}")