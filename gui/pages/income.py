"""
Income page
"""

import tkinter as tk
from tkinter import ttk, messagebox
from gui.widgets.section_header import SectionHeader
from gui.widgets.form_field import FormField

class IncomePage(ttk.Frame):
    """Income information collection page"""
    
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
        """Build the income form"""
        # Page title
        title = ttk.Label(
            self.scrollable_frame,
            text="Income",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=(0, 10), anchor="w")
        
        instruction = ttk.Label(
            self.scrollable_frame,
            text="Report all sources of income you received during the tax year.",
            wraplength=700,
            foreground="gray"
        )
        instruction.pack(pady=(0, 20), anchor="w")
        
        # W-2 Wages
        SectionHeader(self.scrollable_frame, "W-2 Wages and Salaries").pack(fill="x", pady=(10, 10))
        
        w2_info = ttk.Label(
            self.scrollable_frame,
            text="Enter information from each W-2 form you received from employers.",
            foreground="gray",
            font=("Arial", 9)
        )
        w2_info.pack(anchor="w", pady=(0, 10))
        
        self.w2_list_frame = ttk.Frame(self.scrollable_frame)
        self.w2_list_frame.pack(fill="x", pady=5)
        
        self.refresh_w2_list()
        
        add_w2_btn = ttk.Button(
            self.scrollable_frame,
            text="+ Add W-2",
            command=self.add_w2
        )
        add_w2_btn.pack(anchor="w", pady=5)
        
        # Interest Income
        SectionHeader(self.scrollable_frame, "Interest Income").pack(fill="x", pady=(20, 10))
        
        interest_info = ttk.Label(
            self.scrollable_frame,
            text="Report interest from bank accounts, bonds, or other sources (Form 1099-INT).",
            foreground="gray",
            font=("Arial", 9)
        )
        interest_info.pack(anchor="w", pady=(0, 10))
        
        self.interest_list_frame = ttk.Frame(self.scrollable_frame)
        self.interest_list_frame.pack(fill="x", pady=5)
        
        self.refresh_interest_list()
        
        add_interest_btn = ttk.Button(
            self.scrollable_frame,
            text="+ Add Interest Income",
            command=self.add_interest
        )
        add_interest_btn.pack(anchor="w", pady=5)
        
        # Dividend Income
        SectionHeader(self.scrollable_frame, "Dividend Income").pack(fill="x", pady=(20, 10))
        
        dividend_info = ttk.Label(
            self.scrollable_frame,
            text="Report dividends from stocks or mutual funds (Form 1099-DIV).",
            foreground="gray",
            font=("Arial", 9)
        )
        dividend_info.pack(anchor="w", pady=(0, 10))
        
        self.dividend_list_frame = ttk.Frame(self.scrollable_frame)
        self.dividend_list_frame.pack(fill="x", pady=5)
        
        self.refresh_dividend_list()
        
        add_dividend_btn = ttk.Button(
            self.scrollable_frame,
            text="+ Add Dividend Income",
            command=self.add_dividend
        )
        add_dividend_btn.pack(anchor="w", pady=5)
        
        # Navigation buttons
        button_frame = ttk.Frame(self.scrollable_frame)
        button_frame.pack(fill="x", pady=30)
        
        back_btn = ttk.Button(
            button_frame,
            text="Back",
            command=lambda: self.main_window.show_page("filing_status")
        )
        back_btn.pack(side="left")
        
        save_btn = ttk.Button(
            button_frame,
            text="Save and Continue",
            command=self.save_and_continue
        )
        save_btn.pack(side="right")
    
    def refresh_w2_list(self):
        """Refresh W-2 list display"""
        # Clear existing widgets
        for widget in self.w2_list_frame.winfo_children():
            widget.destroy()
        
        w2_forms = self.tax_data.get("income.w2_forms", [])
        
        for idx, w2 in enumerate(w2_forms):
            frame = ttk.Frame(self.w2_list_frame, relief="solid", borderwidth=1)
            frame.pack(fill="x", pady=5, padx=5)
            
            info_text = f"Employer: {w2.get('employer', 'N/A')} | Wages: ${w2.get('wages', 0):,.2f} | Federal Withholding: ${w2.get('federal_withholding', 0):,.2f}"
            
            label = ttk.Label(frame, text=info_text)
            label.pack(side="left", padx=10, pady=10)
            
            delete_btn = ttk.Button(
                frame,
                text="Delete",
                command=lambda i=idx: self.delete_w2(i)
            )
            delete_btn.pack(side="right", padx=10, pady=10)
    
    def add_w2(self):
        """Add new W-2 form"""
        dialog = W2Dialog(self, self.tax_data)
        self.wait_window(dialog)
        self.refresh_w2_list()
    
    def delete_w2(self, index):
        """Delete W-2 form"""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this W-2?"):
            self.tax_data.remove_from_list("income.w2_forms", index)
            self.refresh_w2_list()
    
    def refresh_interest_list(self):
        """Refresh interest income list"""
        for widget in self.interest_list_frame.winfo_children():
            widget.destroy()
        
        interest_forms = self.tax_data.get("income.interest_income", [])
        
        for idx, interest in enumerate(interest_forms):
            frame = ttk.Frame(self.interest_list_frame, relief="solid", borderwidth=1)
            frame.pack(fill="x", pady=5, padx=5)
            
            info_text = f"Payer: {interest.get('payer', 'N/A')} | Amount: ${interest.get('amount', 0):,.2f}"
            
            label = ttk.Label(frame, text=info_text)
            label.pack(side="left", padx=10, pady=10)
            
            delete_btn = ttk.Button(
                frame,
                text="Delete",
                command=lambda i=idx: self.delete_interest(i)
            )
            delete_btn.pack(side="right", padx=10, pady=10)
    
    def add_interest(self):
        """Add interest income"""
        dialog = InterestDialog(self, self.tax_data)
        self.wait_window(dialog)
        self.refresh_interest_list()
    
    def delete_interest(self, index):
        """Delete interest income"""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this interest income?"):
            self.tax_data.remove_from_list("income.interest_income", index)
            self.refresh_interest_list()
    
    def refresh_dividend_list(self):
        """Refresh dividend income list"""
        for widget in self.dividend_list_frame.winfo_children():
            widget.destroy()
        
        dividend_forms = self.tax_data.get("income.dividend_income", [])
        
        for idx, dividend in enumerate(dividend_forms):
            frame = ttk.Frame(self.dividend_list_frame, relief="solid", borderwidth=1)
            frame.pack(fill="x", pady=5, padx=5)
            
            info_text = f"Payer: {dividend.get('payer', 'N/A')} | Amount: ${dividend.get('amount', 0):,.2f}"
            
            label = ttk.Label(frame, text=info_text)
            label.pack(side="left", padx=10, pady=10)
            
            delete_btn = ttk.Button(
                frame,
                text="Delete",
                command=lambda i=idx: self.delete_dividend(i)
            )
            delete_btn.pack(side="right", padx=10, pady=10)
    
    def add_dividend(self):
        """Add dividend income"""
        dialog = DividendDialog(self, self.tax_data)
        self.wait_window(dialog)
        self.refresh_dividend_list()
    
    def delete_dividend(self, index):
        """Delete dividend income"""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this dividend income?"):
            self.tax_data.remove_from_list("income.dividend_income", index)
            self.refresh_dividend_list()
    
    def save_and_continue(self):
        """Save data and move to next page"""
        self.main_window.show_page("deductions")


class W2Dialog(tk.Toplevel):
    """Dialog for entering W-2 information"""
    
    def __init__(self, parent, tax_data):
        super().__init__(parent)
        self.tax_data = tax_data
        self.title("Add W-2")
        self.geometry("500x400")
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Build form
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="W-2 Information", font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        self.employer = FormField(main_frame, "Employer Name", "")
        self.employer.pack(fill="x", pady=5)
        
        self.ein = FormField(main_frame, "Employer ID Number (EIN)", "")
        self.ein.pack(fill="x", pady=5)
        
        self.wages = FormField(main_frame, "Wages (Box 1)", "")
        self.wages.pack(fill="x", pady=5)
        
        self.federal_withholding = FormField(main_frame, "Federal Income Tax Withheld (Box 2)", "")
        self.federal_withholding.pack(fill="x", pady=5)
        
        self.social_security_wages = FormField(main_frame, "Social Security Wages (Box 3)", "")
        self.social_security_wages.pack(fill="x", pady=5)
        
        self.medicare_wages = FormField(main_frame, "Medicare Wages (Box 5)", "")
        self.medicare_wages.pack(fill="x", pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=20)
        
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side="left")
        ttk.Button(button_frame, text="Add W-2", command=self.add_w2).pack(side="right")
    
    def add_w2(self):
        """Add W-2 to tax data"""
        try:
            w2_data = {
                "employer": self.employer.get(),
                "ein": self.ein.get(),
                "wages": float(self.wages.get() or 0),
                "federal_withholding": float(self.federal_withholding.get() or 0),
                "social_security_wages": float(self.social_security_wages.get() or 0),
                "medicare_wages": float(self.medicare_wages.get() or 0),
            }
            
            self.tax_data.add_to_list("income.w2_forms", w2_data)
            self.destroy()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for amounts.")


class InterestDialog(tk.Toplevel):
    """Dialog for entering interest income"""
    
    def __init__(self, parent, tax_data):
        super().__init__(parent)
        self.tax_data = tax_data
        self.title("Add Interest Income")
        self.geometry("400x250")
        
        self.transient(parent)
        self.grab_set()
        
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="Interest Income (1099-INT)", font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        self.payer = FormField(main_frame, "Payer Name", "")
        self.payer.pack(fill="x", pady=5)
        
        self.amount = FormField(main_frame, "Interest Amount", "")
        self.amount.pack(fill="x", pady=5)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=20)
        
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side="left")
        ttk.Button(button_frame, text="Add", command=self.add_interest).pack(side="right")
    
    def add_interest(self):
        """Add interest income to tax data"""
        try:
            interest_data = {
                "payer": self.payer.get(),
                "amount": float(self.amount.get() or 0),
            }
            
            self.tax_data.add_to_list("income.interest_income", interest_data)
            self.destroy()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for the amount.")


class DividendDialog(tk.Toplevel):
    """Dialog for entering dividend income"""
    
    def __init__(self, parent, tax_data):
        super().__init__(parent)
        self.tax_data = tax_data
        self.title("Add Dividend Income")
        self.geometry("400x250")
        
        self.transient(parent)
        self.grab_set()
        
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="Dividend Income (1099-DIV)", font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        self.payer = FormField(main_frame, "Payer Name", "")
        self.payer.pack(fill="x", pady=5)
        
        self.amount = FormField(main_frame, "Dividend Amount", "")
        self.amount.pack(fill="x", pady=5)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=20)
        
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side="left")
        ttk.Button(button_frame, text="Add", command=self.add_dividend).pack(side="right")
    
    def add_dividend(self):
        """Add dividend income to tax data"""
        try:
            dividend_data = {
                "payer": self.payer.get(),
                "amount": float(self.amount.get() or 0),
            }
            
            self.tax_data.add_to_list("income.dividend_income", dividend_data)
            self.destroy()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for the amount.")
