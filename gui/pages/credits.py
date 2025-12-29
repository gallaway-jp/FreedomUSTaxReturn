"""
Credits and Taxes page
"""

import tkinter as tk
from tkinter import ttk
from gui.widgets.section_header import SectionHeader
from gui.widgets.form_field import FormField

class CreditsPage(ttk.Frame):
    """Credits and taxes page"""
    
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
        """Build the credits form"""
        # Page title
        title = ttk.Label(
            self.scrollable_frame,
            text="Tax Credits",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=(0, 10), anchor="w")
        
        instruction = ttk.Label(
            self.scrollable_frame,
            text="Tax credits reduce your tax liability dollar-for-dollar. Enter information about credits you may qualify for.",
            wraplength=700,
            foreground="gray"
        )
        instruction.pack(pady=(0, 20), anchor="w")
        
        # Common credits
        SectionHeader(self.scrollable_frame, "Common Tax Credits").pack(fill="x", pady=(10, 10))
        
        # Child Tax Credit
        ctc_frame = ttk.LabelFrame(self.scrollable_frame, text="Child Tax Credit", padding="10")
        ctc_frame.pack(fill="x", pady=10)
        
        ctc_info = ttk.Label(
            ctc_frame,
            text="Up to $2,000 per qualifying child under age 17",
            foreground="gray",
            font=("Arial", 9)
        )
        ctc_info.pack(anchor="w", pady=(0, 5))
        
        self.num_children = FormField(
            ctc_frame,
            "Number of qualifying children",
            str(len(self.tax_data.get("credits.child_tax_credit.qualifying_children", [])))
        )
        self.num_children.pack(fill="x", pady=5)
        
        # Earned Income Credit
        eic_frame = ttk.LabelFrame(self.scrollable_frame, text="Earned Income Credit (EIC)", padding="10")
        eic_frame.pack(fill="x", pady=10)
        
        eic_info = ttk.Label(
            eic_frame,
            text="Credit for low to moderate income workers",
            foreground="gray",
            font=("Arial", 9)
        )
        eic_info.pack(anchor="w", pady=(0, 5))
        
        self.claim_eic = tk.BooleanVar(value=bool(self.tax_data.get("credits.earned_income_credit.qualifying_children")))
        eic_cb = ttk.Checkbutton(
            eic_frame,
            text="I want to claim the Earned Income Credit",
            variable=self.claim_eic
        )
        eic_cb.pack(anchor="w", pady=5)
        
        # Education Credits
        edu_frame = ttk.LabelFrame(self.scrollable_frame, text="Education Credits", padding="10")
        edu_frame.pack(fill="x", pady=10)
        
        edu_info = ttk.Label(
            edu_frame,
            text="American Opportunity Tax Credit (up to $2,500) or Lifetime Learning Credit (up to $2,000)",
            foreground="gray",
            font=("Arial", 9)
        )
        edu_info.pack(anchor="w", pady=(0, 5))
        
        self.claim_edu = tk.BooleanVar(
            value=bool(
                self.tax_data.get("credits.education_credits.american_opportunity") or 
                self.tax_data.get("credits.education_credits.lifetime_learning")
            )
        )
        edu_cb = ttk.Checkbutton(
            edu_frame,
            text="I paid qualified education expenses",
            variable=self.claim_edu
        )
        edu_cb.pack(anchor="w", pady=5)
        
        # Retirement Savings Credit
        retire_frame = ttk.LabelFrame(self.scrollable_frame, text="Retirement Savings Contributions Credit", padding="10")
        retire_frame.pack(fill="x", pady=10)
        
        retire_info = ttk.Label(
            retire_frame,
            text="Credit for contributions to IRA, 401(k), or other retirement plans",
            foreground="gray",
            font=("Arial", 9)
        )
        retire_info.pack(anchor="w", pady=(0, 5))
        
        self.retire_contrib = FormField(
            retire_frame,
            "Retirement plan contributions",
            str(self.tax_data.get("credits.retirement_savings_credit", 0))
        )
        self.retire_contrib.pack(fill="x", pady=5)
        
        # Navigation buttons
        button_frame = ttk.Frame(self.scrollable_frame)
        button_frame.pack(fill="x", pady=30)
        
        back_btn = ttk.Button(
            button_frame,
            text="Back",
            command=lambda: self.main_window.show_page("deductions")
        )
        back_btn.pack(side="left")
        
        save_btn = ttk.Button(
            button_frame,
            text="Save and Continue",
            command=self.save_and_continue
        )
        save_btn.pack(side="right")
    
    def save_and_continue(self):
        """Save data and move to next page"""
        # Save child tax credit info
        num_children = int(self.num_children.get() or 0)
        children_list = []
        for i in range(num_children):
            children_list.append({"name": f"Child {i+1}", "qualifying": True})
        self.tax_data.set("credits.child_tax_credit.qualifying_children", children_list)
        
        # Save EIC info
        if self.claim_eic.get():
            if not self.tax_data.get("credits.earned_income_credit.qualifying_children"):
                self.tax_data.set("credits.earned_income_credit.qualifying_children", children_list)
        else:
            self.tax_data.set("credits.earned_income_credit.qualifying_children", [])
        
        # Save retirement savings credit
        try:
            contrib = float(self.retire_contrib.get() or 0)
            self.tax_data.set("credits.retirement_savings_credit", contrib)
        except ValueError:
            pass
        
        self.main_window.show_page("payments")
