"""
Filing Status page
"""

import tkinter as tk
from tkinter import ttk
from gui.widgets.section_header import SectionHeader

class FilingStatusPage(ttk.Frame):
    """Filing status selection page"""
    
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
        """Build the filing status form"""
        # Page title
        title = ttk.Label(
            self.scrollable_frame,
            text="Filing Status",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=(0, 10), anchor="w")
        
        instruction = ttk.Label(
            self.scrollable_frame,
            text="Select your filing status. This determines your tax rates and standard deduction.",
            wraplength=700,
            foreground="gray"
        )
        instruction.pack(pady=(0, 20), anchor="w")
        
        # Filing status options
        self.status_var = tk.StringVar(value=self.tax_data.get("filing_status.status", ""))
        
        statuses = [
            ("Single", "Single", 
             "Use this status if you are unmarried or legally separated."),
            ("Married Filing Jointly", "MFJ",
             "Use if you are married and filing a joint return with your spouse."),
            ("Married Filing Separately", "MFS",
             "Use if you are married but filing separately from your spouse."),
            ("Head of Household", "HOH",
             "Use if you are unmarried and pay more than half the cost of keeping up a home for a qualifying person."),
            ("Qualifying Widow(er)", "QW",
             "Use if your spouse died in the previous two years and you have a dependent child."),
        ]
        
        for label, value, description in statuses:
            frame = ttk.Frame(self.scrollable_frame, relief="solid", borderwidth=1)
            frame.pack(fill="x", pady=10, padx=5)
            
            rb = ttk.Radiobutton(
                frame,
                text=label,
                variable=self.status_var,
                value=value,
                command=self.on_status_change
            )
            rb.pack(anchor="w", padx=10, pady=(10, 5))
            
            desc_label = ttk.Label(
                frame,
                text=description,
                wraplength=650,
                foreground="gray",
                font=("Arial", 9)
            )
            desc_label.pack(anchor="w", padx=30, pady=(0, 10))
        
        # Additional questions
        SectionHeader(self.scrollable_frame, "Additional Information").pack(fill="x", pady=(30, 10))
        
        self.dependent_var = tk.BooleanVar(
            value=self.tax_data.get("filing_status.is_dependent", False)
        )
        dependent_cb = ttk.Checkbutton(
            self.scrollable_frame,
            text="Someone can claim you as a dependent",
            variable=self.dependent_var
        )
        dependent_cb.pack(anchor="w", pady=5)
        
        # Navigation buttons
        button_frame = ttk.Frame(self.scrollable_frame)
        button_frame.pack(fill="x", pady=30)
        
        back_btn = ttk.Button(
            button_frame,
            text="Back",
            command=lambda: self.main_window.show_page("personal_info")
        )
        back_btn.pack(side="left")
        
        save_btn = ttk.Button(
            button_frame,
            text="Save and Continue",
            command=self.save_and_continue
        )
        save_btn.pack(side="right")
    
    def on_status_change(self):
        """Handle filing status change"""
        # Could add conditional logic here
        pass
    
    def save_and_continue(self):
        """Save data and move to next page"""
        self.tax_data.set("filing_status.status", self.status_var.get())
        self.tax_data.set("filing_status.is_dependent", self.dependent_var.get())
        
        # Navigate to next page
        self.main_window.show_page("income")
    
    def refresh_data(self):
        """Refresh the form with current tax data"""
        # Reload filing status data
        self.status_var.set(self.tax_data.get("filing_status.status", ""))
        self.dependent_var.set(self.tax_data.get("filing_status.is_dependent", False))
