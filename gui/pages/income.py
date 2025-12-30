"""
Income page
"""

import tkinter as tk
from tkinter import ttk, messagebox
from gui.widgets.section_header import SectionHeader
from gui.widgets.form_field import FormField

class IncomePage(ttk.Frame):
    """Income information collection page"""
    
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
        
        # Self-Employment Income (Schedule C)
        SectionHeader(self.scrollable_frame, "Self-Employment Income").pack(fill="x", pady=(20, 10))
        
        se_info = ttk.Label(
            self.scrollable_frame,
            text="Report income from self-employment or business activities (Schedule C).",
            foreground="gray",
            font=("Arial", 9)
        )
        se_info.pack(anchor="w", pady=(0, 10))
        
        self.se_list_frame = ttk.Frame(self.scrollable_frame)
        self.se_list_frame.pack(fill="x", pady=5)
        
        self.refresh_se_list()
        
        add_se_btn = ttk.Button(
            self.scrollable_frame,
            text="+ Add Self-Employment Income",
            command=self.add_self_employment
        )
        add_se_btn.pack(anchor="w", pady=5)
        
        # Retirement Distributions (1099-R)
        SectionHeader(self.scrollable_frame, "Retirement Distributions").pack(fill="x", pady=(20, 10))
        
        retirement_info = ttk.Label(
            self.scrollable_frame,
            text="Report distributions from retirement accounts (1099-R).",
            foreground="gray",
            font=("Arial", 9)
        )
        retirement_info.pack(anchor="w", pady=(0, 10))
        
        self.retirement_list_frame = ttk.Frame(self.scrollable_frame)
        self.retirement_list_frame.pack(fill="x", pady=5)
        
        self.refresh_retirement_list()
        
        add_retirement_btn = ttk.Button(
            self.scrollable_frame,
            text="+ Add Retirement Distribution",
            command=self.add_retirement
        )
        add_retirement_btn.pack(anchor="w", pady=5)
        
        # Social Security Benefits
        SectionHeader(self.scrollable_frame, "Social Security Benefits").pack(fill="x", pady=(20, 10))
        
        ss_info = ttk.Label(
            self.scrollable_frame,
            text="Report Social Security benefits received during the tax year.",
            foreground="gray",
            font=("Arial", 9)
        )
        ss_info.pack(anchor="w", pady=(0, 10))
        
        self.ss_list_frame = ttk.Frame(self.scrollable_frame)
        self.ss_list_frame.pack(fill="x", pady=5)
        
        self.refresh_ss_list()
        
        add_ss_btn = ttk.Button(
            self.scrollable_frame,
            text="+ Add Social Security Benefits",
            command=self.add_social_security
        )
        add_ss_btn.pack(anchor="w", pady=5)
        
        # Capital Gains/Losses (Schedule D)
        SectionHeader(self.scrollable_frame, "Capital Gains and Losses").pack(fill="x", pady=(20, 10))
        
        capital_info = ttk.Label(
            self.scrollable_frame,
            text="Report capital gains and losses from investments (Schedule D).",
            foreground="gray",
            font=("Arial", 9)
        )
        capital_info.pack(anchor="w", pady=(0, 10))
        
        self.capital_list_frame = ttk.Frame(self.scrollable_frame)
        self.capital_list_frame.pack(fill="x", pady=5)
        
        self.refresh_capital_list()
        
        add_capital_btn = ttk.Button(
            self.scrollable_frame,
            text="+ Add Capital Gain/Loss",
            command=self.add_capital_gain
        )
        add_capital_btn.pack(anchor="w", pady=5)
        
        # Rental Income (Schedule E)
        SectionHeader(self.scrollable_frame, "Rental Income").pack(fill="x", pady=(20, 10))
        
        rental_info = ttk.Label(
            self.scrollable_frame,
            text="Report income from rental properties (Schedule E).",
            foreground="gray",
            font=("Arial", 9)
        )
        rental_info.pack(anchor="w", pady=(0, 10))
        
        self.rental_list_frame = ttk.Frame(self.scrollable_frame)
        self.rental_list_frame.pack(fill="x", pady=5)
        
        self.refresh_rental_list()
        
        add_rental_btn = ttk.Button(
            self.scrollable_frame,
            text="+ Add Rental Income",
            command=self.add_rental_income
        )
        add_rental_btn.pack(anchor="w", pady=5)
        
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
        dialog = W2Dialog(self, self.tax_data, self.theme_manager)
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
        dialog = InterestDialog(self, self.tax_data, self.theme_manager)
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
        dialog = DividendDialog(self, self.tax_data, self.theme_manager)
        self.wait_window(dialog)
        self.refresh_dividend_list()
    
    def delete_dividend(self, index):
        """Delete dividend income"""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this dividend income?"):
            self.tax_data.remove_from_list("income.dividend_income", index)
            self.refresh_dividend_list()
    
    def refresh_se_list(self):
        """Refresh self-employment income list"""
        for widget in self.se_list_frame.winfo_children():
            widget.destroy()
        
        se_forms = self.tax_data.get("income.self_employment", [])
        
        for idx, se in enumerate(se_forms):
            frame = ttk.Frame(self.se_list_frame, relief="solid", borderwidth=1)
            frame.pack(fill="x", pady=5, padx=5)
            
            info_text = f"Business: {se.get('business_name', 'N/A')} | Gross Income: ${se.get('gross_income', 0):,.2f} | Net Profit: ${se.get('net_profit', 0):,.2f}"
            
            label = ttk.Label(frame, text=info_text)
            label.pack(side="left", padx=10, pady=10)
            
            delete_btn = ttk.Button(
                frame,
                text="Delete",
                command=lambda i=idx: self.delete_self_employment(i)
            )
            delete_btn.pack(side="right", padx=10, pady=10)
    
    def add_self_employment(self):
        """Add self-employment income"""
        dialog = SelfEmploymentDialog(self, self.tax_data, self.theme_manager)
        self.wait_window(dialog)
        self.refresh_se_list()
    
    def delete_self_employment(self, index):
        """Delete self-employment income"""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this self-employment income?"):
            self.tax_data.remove_from_list("income.self_employment", index)
            self.refresh_se_list()
    
    def refresh_retirement_list(self):
        """Refresh retirement distributions list"""
        for widget in self.retirement_list_frame.winfo_children():
            widget.destroy()
        
        retirement_forms = self.tax_data.get("income.retirement_distributions", [])
        
        for idx, retirement in enumerate(retirement_forms):
            frame = ttk.Frame(self.retirement_list_frame, relief="solid", borderwidth=1)
            frame.pack(fill="x", pady=5, padx=5)
            
            info_text = f"Payer: {retirement.get('payer', 'N/A')} | Gross Distribution: ${retirement.get('gross_distribution', 0):,.2f} | Taxable Amount: ${retirement.get('taxable_amount', 0):,.2f}"
            
            label = ttk.Label(frame, text=info_text)
            label.pack(side="left", padx=10, pady=10)
            
            delete_btn = ttk.Button(
                frame,
                text="Delete",
                command=lambda i=idx: self.delete_retirement(i)
            )
            delete_btn.pack(side="right", padx=10, pady=10)
    
    def add_retirement(self):
        """Add retirement distribution"""
        dialog = RetirementDialog(self, self.tax_data, self.theme_manager)
        self.wait_window(dialog)
        self.refresh_retirement_list()
    
    def delete_retirement(self, index):
        """Delete retirement distribution"""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this retirement distribution?"):
            self.tax_data.remove_from_list("income.retirement_distributions", index)
            self.refresh_retirement_list()
    
    def refresh_ss_list(self):
        """Refresh Social Security benefits list"""
        for widget in self.ss_list_frame.winfo_children():
            widget.destroy()
        
        ss_forms = self.tax_data.get("income.social_security", [])
        
        for idx, ss in enumerate(ss_forms):
            frame = ttk.Frame(self.ss_list_frame, relief="solid", borderwidth=1)
            frame.pack(fill="x", pady=5, padx=5)
            
            info_text = f"Net Benefits: ${ss.get('net_benefits', 0):,.2f} | Repayment: ${ss.get('repayment', 0):,.2f}"
            
            label = ttk.Label(frame, text=info_text)
            label.pack(side="left", padx=10, pady=10)
            
            delete_btn = ttk.Button(
                frame,
                text="Delete",
                command=lambda i=idx: self.delete_social_security(i)
            )
            delete_btn.pack(side="right", padx=10, pady=10)
    
    def add_social_security(self):
        """Add Social Security benefits"""
        dialog = SocialSecurityDialog(self, self.tax_data, self.theme_manager)
        self.wait_window(dialog)
        self.refresh_ss_list()
    
    def delete_social_security(self, index):
        """Delete Social Security benefits"""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this Social Security benefit?"):
            self.tax_data.remove_from_list("income.social_security", index)
            self.refresh_ss_list()
    
    def refresh_capital_list(self):
        """Refresh capital gains/losses list"""
        for widget in self.capital_list_frame.winfo_children():
            widget.destroy()
        
        capital_forms = self.tax_data.get("income.capital_gains", [])
        
        for idx, capital in enumerate(capital_forms):
            frame = ttk.Frame(self.capital_list_frame, relief="solid", borderwidth=1)
            frame.pack(fill="x", pady=5, padx=5)
            
            gain_loss = capital.get('gain_loss', 0)
            gain_loss_text = f"Gain: ${gain_loss:,.2f}" if gain_loss >= 0 else f"Loss: ${abs(gain_loss):,.2f}"
            info_text = f"Description: {capital.get('description', 'N/A')} | {gain_loss_text}"
            
            label = ttk.Label(frame, text=info_text)
            label.pack(side="left", padx=10, pady=10)
            
            delete_btn = ttk.Button(
                frame,
                text="Delete",
                command=lambda i=idx: self.delete_capital_gain(i)
            )
            delete_btn.pack(side="right", padx=10, pady=10)
    
    def add_capital_gain(self):
        """Add capital gain/loss"""
        dialog = CapitalGainDialog(self, self.tax_data, self.theme_manager)
        self.wait_window(dialog)
        self.refresh_capital_list()
    
    def delete_capital_gain(self, index):
        """Delete capital gain/loss"""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this capital gain/loss?"):
            self.tax_data.remove_from_list("income.capital_gains", index)
            self.refresh_capital_list()
    
    def refresh_rental_list(self):
        """Refresh rental income list"""
        for widget in self.rental_list_frame.winfo_children():
            widget.destroy()
        
        rental_forms = self.tax_data.get("income.rental_income", [])
        
        for idx, rental in enumerate(rental_forms):
            frame = ttk.Frame(self.rental_list_frame, relief="solid", borderwidth=1)
            frame.pack(fill="x", pady=5, padx=5)
            
            info_text = f"Property: {rental.get('property_address', 'N/A')} | Gross Rent: ${rental.get('gross_rent', 0):,.2f} | Net Income: ${rental.get('net_income', 0):,.2f}"
            
            label = ttk.Label(frame, text=info_text)
            label.pack(side="left", padx=10, pady=10)
            
            delete_btn = ttk.Button(
                frame,
                text="Delete",
                command=lambda i=idx: self.delete_rental_income(i)
            )
            delete_btn.pack(side="right", padx=10, pady=10)
    
    def add_rental_income(self):
        """Add rental income"""
        dialog = RentalIncomeDialog(self, self.tax_data, self.theme_manager)
        self.wait_window(dialog)
        self.refresh_rental_list()
    
    def delete_rental_income(self, index):
        """Delete rental income"""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this rental income?"):
            self.tax_data.remove_from_list("income.rental_income", index)
            self.refresh_rental_list()
    
    def save_and_continue(self):
        """Save data and move to next page"""
        self.main_window.show_page("deductions")


class W2Dialog(tk.Toplevel):
    """Dialog for entering W-2 information"""
    
    def __init__(self, parent, tax_data, theme_manager=None):
        super().__init__(parent)
        self.tax_data = tax_data
        self.theme_manager = theme_manager
        self.title("Add W-2")
        self.geometry("500x400")
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Build form
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="W-2 Information", font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        self.employer = FormField(main_frame, "Employer Name", "", theme_manager=self.theme_manager)
        self.employer.pack(fill="x", pady=5)
        
        self.ein = FormField(main_frame, "Employer ID Number (EIN)", "", theme_manager=self.theme_manager)
        self.ein.pack(fill="x", pady=5)
        
        self.wages = FormField(main_frame, "Wages (Box 1)", "", field_type="currency", theme_manager=self.theme_manager)
        self.wages.pack(fill="x", pady=5)
        
        self.federal_withholding = FormField(main_frame, "Federal Income Tax Withheld (Box 2)", "", field_type="currency", theme_manager=self.theme_manager)
        self.federal_withholding.pack(fill="x", pady=5)
        
        self.social_security_wages = FormField(main_frame, "Social Security Wages (Box 3)", "", field_type="currency", theme_manager=self.theme_manager)
        self.social_security_wages.pack(fill="x", pady=5)
        
        self.medicare_wages = FormField(main_frame, "Medicare Wages (Box 5)", "", field_type="currency", theme_manager=self.theme_manager)
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
    
    def __init__(self, parent, tax_data, theme_manager=None):
        super().__init__(parent)
        self.tax_data = tax_data
        self.theme_manager = theme_manager
        self.title("Add Interest Income")
        self.geometry("400x250")
        
        self.transient(parent)
        self.grab_set()
        
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="Interest Income (1099-INT)", font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        self.payer = FormField(main_frame, "Payer Name", "", theme_manager=self.theme_manager)
        self.payer.pack(fill="x", pady=5)
        
        self.amount = FormField(main_frame, "Interest Amount", "", field_type="currency", theme_manager=self.theme_manager)
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
    
    def __init__(self, parent, tax_data, theme_manager=None):
        super().__init__(parent)
        self.tax_data = tax_data
        self.theme_manager = theme_manager
        self.title("Add Dividend Income")
        self.geometry("400x250")
        
        self.transient(parent)
        self.grab_set()
        
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="Dividend Income (1099-DIV)", font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        self.payer = FormField(main_frame, "Payer Name", "", theme_manager=self.theme_manager)
        self.payer.pack(fill="x", pady=5)
        
        self.amount = FormField(main_frame, "Dividend Amount", "", field_type="currency", theme_manager=self.theme_manager)
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
                "amount": float(self.amount.get().replace('$', '').replace(',', '') or 0),
            }
            
            self.tax_data.add_to_list("income.dividend_income", dividend_data)
            self.destroy()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for the amount.")


class SelfEmploymentDialog(tk.Toplevel):
    """Dialog for entering self-employment income"""
    
    def __init__(self, parent, tax_data, theme_manager=None):
        super().__init__(parent)
        self.tax_data = tax_data
        self.theme_manager = theme_manager
        self.title("Add Self-Employment Income")
        self.geometry("500x400")
        
        self.transient(parent)
        self.grab_set()
        
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="Self-Employment Income (Schedule C)", font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        self.business_name = FormField(main_frame, "Business Name/Description", "", theme_manager=self.theme_manager)
        self.business_name.pack(fill="x", pady=5)
        
        self.business_code = FormField(main_frame, "Business Code (from instructions)", "", theme_manager=self.theme_manager)
        self.business_code.pack(fill="x", pady=5)
        
        self.gross_income = FormField(main_frame, "Gross Receipts/Income", "", field_type="currency", theme_manager=self.theme_manager)
        self.gross_income.pack(fill="x", pady=5)
        
        self.expenses = FormField(main_frame, "Business Expenses", "", field_type="currency", theme_manager=self.theme_manager)
        self.expenses.pack(fill="x", pady=5)
        
        self.net_profit = FormField(main_frame, "Net Profit/Loss", "", field_type="currency", theme_manager=self.theme_manager)
        self.net_profit.pack(fill="x", pady=5)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=20)
        
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side="left")
        ttk.Button(button_frame, text="Add", command=self.add_self_employment).pack(side="right")
    
    def add_self_employment(self):
        """Add self-employment income to tax data"""
        try:
            se_data = {
                "business_name": self.business_name.get(),
                "business_code": self.business_code.get(),
                "gross_income": float(self.gross_income.get().replace('$', '').replace(',', '') or 0),
                "expenses": float(self.expenses.get().replace('$', '').replace(',', '') or 0),
                "net_profit": float(self.net_profit.get().replace('$', '').replace(',', '') or 0),
            }
            
            self.tax_data.add_to_list("income.self_employment", se_data)
            self.destroy()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for amounts.")


class RetirementDialog(tk.Toplevel):
    """Dialog for entering retirement distributions"""
    
    def __init__(self, parent, tax_data, theme_manager=None):
        super().__init__(parent)
        self.tax_data = tax_data
        self.theme_manager = theme_manager
        self.title("Add Retirement Distribution")
        self.geometry("500x350")
        
        self.transient(parent)
        self.grab_set()
        
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="Retirement Distribution (1099-R)", font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        self.payer = FormField(main_frame, "Payer Name", "", theme_manager=self.theme_manager)
        self.payer.pack(fill="x", pady=5)
        
        self.gross_distribution = FormField(main_frame, "Gross Distribution", "", field_type="currency", theme_manager=self.theme_manager)
        self.gross_distribution.pack(fill="x", pady=5)
        
        self.taxable_amount = FormField(main_frame, "Taxable Amount", "", field_type="currency", theme_manager=self.theme_manager)
        self.taxable_amount.pack(fill="x", pady=5)
        
        self.federal_tax_withheld = FormField(main_frame, "Federal Income Tax Withheld", "", field_type="currency", theme_manager=self.theme_manager)
        self.federal_tax_withheld.pack(fill="x", pady=5)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=20)
        
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side="left")
        ttk.Button(button_frame, text="Add", command=self.add_retirement).pack(side="right")
    
    def add_retirement(self):
        """Add retirement distribution to tax data"""
        try:
            retirement_data = {
                "payer": self.payer.get(),
                "gross_distribution": float(self.gross_distribution.get().replace('$', '').replace(',', '') or 0),
                "taxable_amount": float(self.taxable_amount.get().replace('$', '').replace(',', '') or 0),
                "federal_tax_withheld": float(self.federal_tax_withheld.get().replace('$', '').replace(',', '') or 0),
            }
            
            self.tax_data.add_to_list("income.retirement_distributions", retirement_data)
            self.destroy()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for amounts.")


class SocialSecurityDialog(tk.Toplevel):
    """Dialog for entering Social Security benefits"""
    
    def __init__(self, parent, tax_data, theme_manager=None):
        super().__init__(parent)
        self.tax_data = tax_data
        self.theme_manager = theme_manager
        self.title("Add Social Security Benefits")
        self.geometry("400x250")
        
        self.transient(parent)
        self.grab_set()
        
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="Social Security Benefits", font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        self.net_benefits = FormField(main_frame, "Net Benefits Received", "", field_type="currency", theme_manager=self.theme_manager)
        self.net_benefits.pack(fill="x", pady=5)
        
        self.repayment = FormField(main_frame, "Repayment/Recovery", "", field_type="currency", theme_manager=self.theme_manager)
        self.repayment.pack(fill="x", pady=5)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=20)
        
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side="left")
        ttk.Button(button_frame, text="Add", command=self.add_social_security).pack(side="right")
    
    def add_social_security(self):
        """Add Social Security benefits to tax data"""
        try:
            ss_data = {
                "net_benefits": float(self.net_benefits.get().replace('$', '').replace(',', '') or 0),
                "repayment": float(self.repayment.get().replace('$', '').replace(',', '') or 0),
            }
            
            self.tax_data.add_to_list("income.social_security", ss_data)
            self.destroy()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for amounts.")


class CapitalGainDialog(tk.Toplevel):
    """Dialog for entering capital gains/losses"""
    
    def __init__(self, parent, tax_data, theme_manager=None):
        super().__init__(parent)
        self.tax_data = tax_data
        self.theme_manager = theme_manager
        self.title("Add Capital Gain/Loss")
        self.geometry("500x350")
        
        self.transient(parent)
        self.grab_set()
        
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="Capital Gain/Loss (Schedule D)", font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        self.description = FormField(main_frame, "Description of Property", "", theme_manager=self.theme_manager)
        self.description.pack(fill="x", pady=5)
        
        self.date_acquired = FormField(main_frame, "Date Acquired (MM/DD/YYYY)", "", field_type="date", theme_manager=self.theme_manager)
        self.date_acquired.pack(fill="x", pady=5)
        
        self.date_sold = FormField(main_frame, "Date Sold (MM/DD/YYYY)", "", field_type="date", theme_manager=self.theme_manager)
        self.date_sold.pack(fill="x", pady=5)
        
        self.sales_price = FormField(main_frame, "Sales Price", "", field_type="currency", theme_manager=self.theme_manager)
        self.sales_price.pack(fill="x", pady=5)
        
        self.cost_basis = FormField(main_frame, "Cost Basis", "", field_type="currency", theme_manager=self.theme_manager)
        self.cost_basis.pack(fill="x", pady=5)
        
        self.gain_loss = FormField(main_frame, "Gain/Loss Amount", "", field_type="currency", theme_manager=self.theme_manager)
        self.gain_loss.pack(fill="x", pady=5)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=20)
        
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side="left")
        ttk.Button(button_frame, text="Add", command=self.add_capital_gain).pack(side="right")
    
    def add_capital_gain(self):
        """Add capital gain/loss to tax data"""
        try:
            gain_loss_value = float(self.gain_loss.get().replace('$', '').replace(',', '') or 0)
            
            capital_data = {
                "description": self.description.get(),
                "date_acquired": self.date_acquired.get(),
                "date_sold": self.date_sold.get(),
                "sales_price": float(self.sales_price.get().replace('$', '').replace(',', '') or 0),
                "cost_basis": float(self.cost_basis.get().replace('$', '').replace(',', '') or 0),
                "gain_loss": gain_loss_value,
            }
            
            self.tax_data.add_to_list("income.capital_gains", capital_data)
            self.destroy()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for amounts and dates.")


class RentalIncomeDialog(tk.Toplevel):
    """Dialog for entering rental income"""
    
    def __init__(self, parent, tax_data, theme_manager=None):
        super().__init__(parent)
        self.tax_data = tax_data
        self.theme_manager = theme_manager
        self.title("Add Rental Income")
        self.geometry("500x400")
        
        self.transient(parent)
        self.grab_set()
        
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="Rental Income (Schedule E)", font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        self.property_address = FormField(main_frame, "Property Address", "", theme_manager=self.theme_manager)
        self.property_address.pack(fill="x", pady=5)
        
        self.gross_rent = FormField(main_frame, "Gross Rents Received", "", field_type="currency", theme_manager=self.theme_manager)
        self.gross_rent.pack(fill="x", pady=5)
        
        self.expenses = FormField(main_frame, "Rental Expenses", "", field_type="currency", theme_manager=self.theme_manager)
        self.expenses.pack(fill="x", pady=5)
        
        self.depreciation = FormField(main_frame, "Depreciation", "", field_type="currency", theme_manager=self.theme_manager)
        self.depreciation.pack(fill="x", pady=5)
        
        self.net_income = FormField(main_frame, "Net Rental Income/Loss", "", field_type="currency", theme_manager=self.theme_manager)
        self.net_income.pack(fill="x", pady=5)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=20)
        
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side="left")
        ttk.Button(button_frame, text="Add", command=self.add_rental_income).pack(side="right")
    
    def add_rental_income(self):
        """Add rental income to tax data"""
        try:
            rental_data = {
                "property_address": self.property_address.get(),
                "gross_rent": float(self.gross_rent.get().replace('$', '').replace(',', '') or 0),
                "expenses": float(self.expenses.get().replace('$', '').replace(',', '') or 0),
                "depreciation": float(self.depreciation.get().replace('$', '').replace(',', '') or 0),
                "net_income": float(self.net_income.get().replace('$', '').replace(',', '') or 0),
            }
            
            self.tax_data.add_to_list("income.rental_income", rental_data)
            self.destroy()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for amounts.")
