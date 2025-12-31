"""
Dialog for creating amended tax returns
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional
from datetime import datetime
from models.tax_data import TaxData


class AmendedReturnDialog:
    """Dialog for creating a new amended return"""
    
    def __init__(self, parent, tax_data: TaxData):
        self.parent = parent
        self.tax_data = tax_data
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Create Amended Return")
        self.dialog.geometry("600x500")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+{}+{}".format(
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))
        
        self._create_widgets()
        self._populate_years()
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def _create_widgets(self):
        """Create dialog widgets"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Create Amended Return", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Instructions
        instructions = (
            "An amended return (Form 1040-X) is used to correct errors or make changes "
            "to a previously filed tax return. Select the tax year you want to amend "
            "and provide the required information."
        )
        instr_label = ttk.Label(main_frame, text=instructions, wraplength=550, 
                               justify=tk.LEFT)
        instr_label.pack(pady=(0, 20))
        
        # Tax year selection
        year_frame = ttk.LabelFrame(main_frame, text="Original Return Information", padding="10")
        year_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(year_frame, text="Tax Year to Amend:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.year_var = tk.StringVar()
        self.year_combo = ttk.Combobox(year_frame, textvariable=self.year_var, state="readonly", width=10)
        self.year_combo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        ttk.Label(year_frame, text="Original Filing Date (MM/DD/YYYY):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.filing_date_var = tk.StringVar()
        self.filing_date_entry = ttk.Entry(year_frame, textvariable=self.filing_date_var, width=15)
        self.filing_date_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # Reason codes
        reason_frame = ttk.LabelFrame(main_frame, text="Reason for Amendment", padding="10")
        reason_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(reason_frame, text="Select all applicable reason codes:").pack(anchor=tk.W)
        
        # Reason code checkboxes
        self.reason_vars = {}
        reasons = [
            ('A', 'Income (wages, interest, etc.)'),
            ('B', 'Deductions (standard/itemized)'),
            ('C', 'Credits'),
            ('D', 'Filing status change'),
            ('E', 'Payments (withholding, estimated)'),
            ('F', 'Other'),
            ('G', 'Other (explain below)')
        ]
        
        for code, description in reasons:
            var = tk.BooleanVar()
            self.reason_vars[code] = var
            ttk.Checkbutton(reason_frame, text=f"{code} - {description}", 
                           variable=var).pack(anchor=tk.W, pady=2)
        
        # Explanation
        ttk.Label(reason_frame, text="Explanation of changes:").pack(anchor=tk.W, pady=(10, 5))
        self.explanation_text = tk.Text(reason_frame, height=4, width=60, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(reason_frame, orient=tk.VERTICAL, command=self.explanation_text.yview)
        self.explanation_text.config(yscrollcommand=scrollbar.set)
        self.explanation_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(button_frame, text="Create Amended Return", 
                  command=self._create_amended_return).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="Cancel", 
                  command=self.dialog.destroy).pack(side=tk.RIGHT)
    
    def _populate_years(self):
        """Populate the tax year dropdown with available years"""
        available_years = []
        for year, year_data in self.tax_data.data.get("years", {}).items():
            # Check if this year has basic personal info (indicating a return exists)
            if year_data.get("personal_info", {}).get("first_name"):
                available_years.append(str(year))
        
        available_years.sort(reverse=True)  # Most recent first
        self.year_combo['values'] = available_years
        
        if available_years:
            self.year_combo.set(available_years[0])  # Select most recent
    
    def _create_amended_return(self):
        """Validate input and create the amended return"""
        # Validate tax year
        try:
            original_year = int(self.year_var.get())
        except ValueError:
            messagebox.showerror("Invalid Year", "Please select a valid tax year.")
            return
        
        # Validate filing date
        filing_date = self.filing_date_var.get().strip()
        if not filing_date:
            messagebox.showerror("Missing Date", "Please enter the original filing date.")
            return
        
        # Validate date format
        try:
            datetime.strptime(filing_date, '%m/%d/%Y')
        except ValueError:
            messagebox.showerror("Invalid Date", "Please enter the date in MM/DD/YYYY format.")
            return
        
        # Validate reason codes
        selected_codes = [code for code, var in self.reason_vars.items() if var.get()]
        if not selected_codes:
            messagebox.showerror("No Reason Selected", "Please select at least one reason code.")
            return
        
        # Get explanation
        explanation = self.explanation_text.get("1.0", tk.END).strip()
        
        # Store result
        self.result = {
            'original_year': original_year,
            'filing_date': filing_date,
            'reason_codes': selected_codes,
            'explanation': explanation
        }
        
        self.dialog.destroy()