"""
Payments page
"""

import tkinter as tk
from tkinter import ttk
from gui.widgets.section_header import SectionHeader
from gui.widgets.form_field import FormField
from utils.w2_calculator import W2Calculator

class PaymentsPage(ttk.Frame):
    """Tax payments page"""
    
    def __init__(self, parent, tax_data, main_window, theme_manager=None):
        super().__init__(parent)
        self.tax_data = tax_data
        self.main_window = main_window
        self.theme_manager = theme_manager
        
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
        """Build the payments form"""
        # Page title
        title = ttk.Label(
            self.scrollable_frame,
            text="Tax Payments",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=(0, 10), anchor="w")
        
        instruction = ttk.Label(
            self.scrollable_frame,
            text="Enter any federal income tax payments you made during the year.",
            wraplength=700,
            foreground="gray"
        )
        instruction.pack(pady=(0, 20), anchor="w")
        
        # Federal withholding (from W-2s)
        SectionHeader(self.scrollable_frame, "Federal Income Tax Withheld").pack(fill="x", pady=(10, 10))
        
        # Calculate total withholding from W-2s
        w2_forms = self.tax_data.get("income.w2_forms", [])
        total_withholding = W2Calculator.calculate_total_withholding(w2_forms)
        
        withholding_info = ttk.Label(
            self.scrollable_frame,
            text=f"Total from W-2 forms: ${total_withholding:,.2f}",
            font=("Arial", 11)
        )
        withholding_info.pack(anchor="w", pady=5)
        
        # Estimated tax payments
        SectionHeader(self.scrollable_frame, "Estimated Tax Payments").pack(fill="x", pady=(20, 10))
        
        est_info = ttk.Label(
            self.scrollable_frame,
            text="Enter any estimated tax payments you made during the year (Form 1040-ES).",
            foreground="gray",
            font=("Arial", 9)
        )
        est_info.pack(anchor="w", pady=(0, 10))
        
        self.est_list_frame = ttk.Frame(self.scrollable_frame)
        self.est_list_frame.pack(fill="x", pady=5)
        
        self.refresh_estimated_list()
        
        add_est_btn = ttk.Button(
            self.scrollable_frame,
            text="+ Add Estimated Payment",
            command=self.add_estimated_payment
        )
        add_est_btn.pack(anchor="w", pady=5)
        
        # Prior year overpayment
        SectionHeader(self.scrollable_frame, "Other Payments").pack(fill="x", pady=(20, 10))
        
        self.prior_overpayment = FormField(
            self.scrollable_frame,
            "Prior year overpayment applied to this year",
            str(self.tax_data.get("payments.prior_year_overpayment", 0)),
            theme_manager=self.theme_manager
        )
        self.prior_overpayment.pack(fill="x", pady=5)
        
        # Calculate total
        self.calculate_total()
        
        # Navigation buttons
        button_frame = ttk.Frame(self.scrollable_frame)
        button_frame.pack(fill="x", pady=30)
        
        back_btn = ttk.Button(
            button_frame,
            text="Back",
            command=lambda: self.main_window.show_page("credits")
        )
        back_btn.pack(side="left")
        
        save_btn = ttk.Button(
            button_frame,
            text="Save and View Forms",
            command=self.save_and_continue
        )
        save_btn.pack(side="right")
    
    def refresh_estimated_list(self):
        """Refresh estimated payments list"""
        for widget in self.est_list_frame.winfo_children():
            widget.destroy()
        
        est_payments = self.tax_data.get("payments.estimated_payments", [])
        
        for idx, payment in enumerate(est_payments):
            frame = ttk.Frame(self.est_list_frame, relief="solid", borderwidth=1)
            frame.pack(fill="x", pady=5, padx=5)
            
            info_text = f"Date: {payment.get('date', 'N/A')} | Amount: ${payment.get('amount', 0):,.2f}"
            
            label = ttk.Label(frame, text=info_text)
            label.pack(side="left", padx=10, pady=10)
            
            delete_btn = ttk.Button(
                frame,
                text="Delete",
                command=lambda i=idx: self.delete_estimated(i)
            )
            delete_btn.pack(side="right", padx=10, pady=10)
    
    def add_estimated_payment(self):
        """Add estimated tax payment"""
        dialog = EstimatedPaymentDialog(self, self.tax_data, self.theme_manager)
        self.wait_window(dialog)
        self.refresh_estimated_list()
        self.calculate_total()
    
    def delete_estimated(self, index):
        """Delete estimated payment"""
        from tkinter import messagebox
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this payment?"):
            self.tax_data.remove_from_list("payments.estimated_payments", index)
            self.refresh_estimated_list()
            self.calculate_total()
    
    def calculate_total(self):
        """Calculate total payments"""
        w2_forms = self.tax_data.get("income.w2_forms", [])
        total_withholding = W2Calculator.calculate_total_withholding(w2_forms)
        
        est_payments = self.tax_data.get("payments.estimated_payments", [])
        total_estimated = sum(p.get("amount", 0) for p in est_payments)
        
        try:
            prior_overpayment = float(self.prior_overpayment.get() or 0)
        except ValueError:
            prior_overpayment = 0
        
        total = total_withholding + total_estimated + prior_overpayment
        
        # Display total
        if hasattr(self, 'total_label'):
            self.total_label.destroy()
        
        self.total_label = ttk.Label(
            self.scrollable_frame,
            text=f"Total Payments: ${total:,.2f}",
            font=("Arial", 14, "bold"),
            foreground="green"
        )
        self.total_label.pack(pady=20)
    
    def save_and_continue(self):
        """Save data and move to form viewer"""
        # Save federal withholding from W-2s
        w2_forms = self.tax_data.get("income.w2_forms", [])
        total_withholding = W2Calculator.calculate_total_withholding(w2_forms)
        self.tax_data.set("payments.federal_withholding", total_withholding)
        
        # Save prior year overpayment
        try:
            prior_overpayment = float(self.prior_overpayment.get() or 0)
            self.tax_data.set("payments.prior_year_overpayment", prior_overpayment)
        except ValueError:
            pass
        
        self.main_window.show_page("form_viewer")
    
    def refresh_data(self):
        """Refresh the form with current tax data"""
        # Refresh estimated payments list
        self.refresh_estimated_list()
        
        # Reload prior year overpayment
        self.prior_overpayment.set(str(self.tax_data.get("payments.prior_year_overpayment", 0)))
        
        # Recalculate totals
        self.calculate_total()


class EstimatedPaymentDialog(tk.Toplevel):
    """Dialog for entering estimated tax payments"""
    
    def __init__(self, parent, tax_data, theme_manager=None):
        super().__init__(parent)
        self.tax_data = tax_data
        self.theme_manager = theme_manager
        self.title("Add Estimated Tax Payment")
        self.geometry("400x250")
        
        self.transient(parent)
        self.grab_set()
        
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="Estimated Tax Payment", font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        self.date = FormField(main_frame, "Payment Date (MM/DD/YYYY)", "", field_type="date", theme_manager=self.theme_manager)
        self.date.pack(fill="x", pady=5)
        
        self.amount = FormField(main_frame, "Amount Paid", "", field_type="currency", theme_manager=self.theme_manager)
        self.amount.pack(fill="x", pady=5)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=20)
        
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side="left")
        ttk.Button(button_frame, text="Add", command=self.add_payment).pack(side="right")
    
    def add_payment(self):
        """Add payment to tax data"""
        try:
            payment_data = {
                "date": self.date.get(),
                "amount": float(self.amount.get() or 0),
            }
            
            self.tax_data.add_to_list("payments.estimated_payments", payment_data)
            self.destroy()
        except ValueError:
            from tkinter import messagebox
            messagebox.showerror("Invalid Input", "Please enter a valid number for the amount.")
