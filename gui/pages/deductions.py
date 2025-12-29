"""
Deductions page
"""

import tkinter as tk
from tkinter import ttk
from gui.widgets.section_header import SectionHeader
from gui.widgets.form_field import FormField

class DeductionsPage(ttk.Frame):
    """Deductions page"""
    
    def __init__(self, parent, tax_data, main_window):
        super().__init__(parent)
        self.tax_data = tax_data
        self.main_window = main_window
        
        # Create scrollable canvas
        self.canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Build form
        self.build_form()
    
    def build_form(self):
        """Build the deductions form"""
        # Page title
        title = ttk.Label(
            self.scrollable_frame,
            text="Deductions",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=(0, 10), anchor="w")
        
        instruction = ttk.Label(
            self.scrollable_frame,
            text="Choose between standard deduction or itemizing your deductions.",
            wraplength=700,
            foreground="gray"
        )
        instruction.pack(pady=(0, 20), anchor="w")
        
        # Deduction method selection
        SectionHeader(self.scrollable_frame, "Deduction Method").pack(fill="x", pady=(10, 10))
        
        self.method_var = tk.StringVar(value=self.tax_data.get("deductions.method", "standard"))
        
        standard_rb = ttk.Radiobutton(
            self.scrollable_frame,
            text="Standard Deduction (Recommended for most people)",
            variable=self.method_var,
            value="standard",
            command=self.on_method_change
        )
        standard_rb.pack(anchor="w", pady=5)
        
        # Show standard deduction amount
        filing_status = self.tax_data.get("filing_status.status")
        standard_amounts = {
            "Single": "$14,600",
            "MFJ": "$29,200",
            "MFS": "$14,600",
            "HOH": "$21,900",
            "QW": "$29,200",
        }
        std_amount = standard_amounts.get(filing_status, "$14,600")
        
        std_info = ttk.Label(
            self.scrollable_frame,
            text=f"Your standard deduction: {std_amount}",
            foreground="gray",
            font=("Arial", 9)
        )
        std_info.pack(anchor="w", padx=30, pady=(0, 10))
        
        itemized_rb = ttk.Radiobutton(
            self.scrollable_frame,
            text="Itemized Deductions (Use if total exceeds standard deduction)",
            variable=self.method_var,
            value="itemized",
            command=self.on_method_change
        )
        itemized_rb.pack(anchor="w", pady=5)
        
        # Itemized deductions frame
        self.itemized_frame = ttk.Frame(self.scrollable_frame)
        self.itemized_frame.pack(fill="x", pady=10)
        
        SectionHeader(self.itemized_frame, "Itemized Deductions").pack(fill="x", pady=(10, 10))
        
        self.medical = FormField(
            self.itemized_frame,
            "Medical and Dental Expenses (over 7.5% of AGI)",
            str(self.tax_data.get("deductions.medical_expenses", 0))
        )
        self.medical.pack(fill="x", pady=5)
        
        self.taxes = FormField(
            self.itemized_frame,
            "State and Local Taxes (max $10,000)",
            str(self.tax_data.get("deductions.state_local_taxes", 0))
        )
        self.taxes.pack(fill="x", pady=5)
        
        self.mortgage = FormField(
            self.itemized_frame,
            "Mortgage Interest",
            str(self.tax_data.get("deductions.mortgage_interest", 0))
        )
        self.mortgage.pack(fill="x", pady=5)
        
        self.charitable = FormField(
            self.itemized_frame,
            "Charitable Contributions",
            str(self.tax_data.get("deductions.charitable_contributions", 0))
        )
        self.charitable.pack(fill="x", pady=5)
        
        # Calculate total
        self.total_label = ttk.Label(
            self.itemized_frame,
            text="Total Itemized Deductions: $0",
            font=("Arial", 11, "bold")
        )
        self.total_label.pack(anchor="w", pady=10)
        
        calculate_btn = ttk.Button(
            self.itemized_frame,
            text="Calculate Total",
            command=self.calculate_itemized_total
        )
        calculate_btn.pack(anchor="w", pady=5)
        
        # Show/hide itemized frame based on selection
        self.on_method_change()
        
        # Navigation buttons
        button_frame = ttk.Frame(self.scrollable_frame)
        button_frame.pack(fill="x", pady=30)
        
        back_btn = ttk.Button(
            button_frame,
            text="Back",
            command=lambda: self.main_window.show_page("income")
        )
        back_btn.pack(side="left")
        
        save_btn = ttk.Button(
            button_frame,
            text="Save and Continue",
            command=self.save_and_continue
        )
        save_btn.pack(side="right")
    
    def on_method_change(self):
        """Handle deduction method change"""
        if self.method_var.get() == "standard":
            self.itemized_frame.pack_forget()
        else:
            self.itemized_frame.pack(fill="x", pady=10)
    
    def calculate_itemized_total(self):
        """Calculate total itemized deductions"""
        try:
            total = (
                float(self.medical.get() or 0) +
                float(self.taxes.get() or 0) +
                float(self.mortgage.get() or 0) +
                float(self.charitable.get() or 0)
            )
            self.total_label.config(text=f"Total Itemized Deductions: ${total:,.2f}")
        except ValueError:
            self.total_label.config(text="Error: Please enter valid numbers")
    
    def save_and_continue(self):
        """Save data and move to next page"""
        self.tax_data.set("deductions.method", self.method_var.get())
        
        if self.method_var.get() == "itemized":
            try:
                self.tax_data.set("deductions.medical_expenses", float(self.medical.get() or 0))
                self.tax_data.set("deductions.state_local_taxes", float(self.taxes.get() or 0))
                self.tax_data.set("deductions.mortgage_interest", float(self.mortgage.get() or 0))
                self.tax_data.set("deductions.charitable_contributions", float(self.charitable.get() or 0))
            except ValueError:
                from tkinter import messagebox
                messagebox.showerror("Invalid Input", "Please enter valid numbers for deduction amounts.")
                return
        
        self.main_window.show_page("credits")
