"""
Form Viewer page - shows calculated forms and summary
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from gui.widgets.section_header import SectionHeader
from utils.w2_calculator import W2Calculator

class FormViewerPage(ttk.Frame):
    """Form viewer and summary page"""
    
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
        """Build the form viewer"""
        # Page title
        title = ttk.Label(
            self.scrollable_frame,
            text="Tax Return Summary & Forms",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=(0, 10), anchor="w")
        
        instruction = ttk.Label(
            self.scrollable_frame,
            text="Review your tax return summary and required forms below.",
            wraplength=700,
            foreground="gray"
        )
        instruction.pack(pady=(0, 20), anchor="w")
        
        # Performance: Calculate totals once and cache
        self._cached_totals = self.tax_data.calculate_totals()
        
        # Summary section
        SectionHeader(self.scrollable_frame, "Tax Return Summary").pack(fill="x", pady=(10, 10))
        
        summary_frame = ttk.Frame(self.scrollable_frame, relief="solid", borderwidth=2, padding="15")
        summary_frame.pack(fill="x", pady=10)
        
        # Personal info
        name = f"{self.tax_data.get('personal_info.first_name')} {self.tax_data.get('personal_info.last_name')}"
        ssn = self.tax_data.get('personal_info.ssn', 'N/A')
        filing_status = self.get_filing_status_text()
        
        self.add_summary_row(summary_frame, "Taxpayer:", name)
        self.add_summary_row(summary_frame, "SSN:", ssn[-4:].rjust(len(ssn), '*') if ssn != 'N/A' else 'N/A')
        self.add_summary_row(summary_frame, "Filing Status:", filing_status)
        
        ttk.Separator(summary_frame, orient="horizontal").pack(fill="x", pady=10)
        
        # Performance: Use cached totals
        totals = self._cached_totals
        
        # Income summary
        self.add_summary_row(summary_frame, "Total Income:", f"${totals['total_income']:,.2f}")
        self.add_summary_row(summary_frame, "Adjusted Gross Income:", f"${totals['adjusted_gross_income']:,.2f}")
        self.add_summary_row(summary_frame, "Taxable Income:", f"${totals['taxable_income']:,.2f}")
        
        ttk.Separator(summary_frame, orient="horizontal").pack(fill="x", pady=10)
        
        # Tax and payments
        self.add_summary_row(summary_frame, "Total Tax:", f"${totals['total_tax']:,.2f}", "red")
        self.add_summary_row(summary_frame, "Total Payments:", f"${totals['total_payments']:,.2f}", "green")
        
        ttk.Separator(summary_frame, orient="horizontal").pack(fill="x", pady=10)
        
        # Refund or owe
        refund_owe = totals['refund_or_owe']
        if refund_owe > 0:
            label_text = "Refund:"
            color = "green"
            amount_text = f"${refund_owe:,.2f}"
        elif refund_owe < 0:
            label_text = "Amount Owed:"
            color = "red"
            amount_text = f"${-refund_owe:,.2f}"
        else:
            label_text = "Balance:"
            color = "black"
            amount_text = "$0.00"
        
        self.add_summary_row(summary_frame, label_text, amount_text, color, bold=True, large=True)
        
        # Required forms
        SectionHeader(self.scrollable_frame, "Required Forms").pack(fill="x", pady=(30, 10))
        
        forms = self.tax_data.get_required_forms()
        
        forms_info = ttk.Label(
            self.scrollable_frame,
            text=f"Based on your entries, you need to file the following {len(forms)} form(s):",
            foreground="gray"
        )
        forms_info.pack(anchor="w", pady=(0, 10))
        
        forms_frame = ttk.Frame(self.scrollable_frame)
        forms_frame.pack(fill="x", pady=5)
        
        for form in forms:
            form_item = ttk.Frame(forms_frame, relief="solid", borderwidth=1)
            form_item.pack(fill="x", pady=3, padx=5)
            
            form_label = ttk.Label(
                form_item,
                text=f"• {form}",
                font=("Arial", 11)
            )
            form_label.pack(side="left", padx=15, pady=8)
            
            view_btn = ttk.Button(
                form_item,
                text="View Form",
                command=lambda f=form: self.view_form(f)
            )
            view_btn.pack(side="right", padx=10, pady=5)
        
        # Form data preview
        SectionHeader(self.scrollable_frame, "Form 1040 Preview").pack(fill="x", pady=(30, 10))
        
        self.show_form_1040_preview()
        
        # Action buttons
        button_frame = ttk.Frame(self.scrollable_frame)
        button_frame.pack(fill="x", pady=30)
        
        back_btn = ttk.Button(
            button_frame,
            text="Back",
            command=lambda: self.main_window.show_page("payments")
        )
        back_btn.pack(side="left")
        
        export_btn = ttk.Button(
            button_frame,
            text="Export to PDF",
            command=self.export_to_pdf
        )
        export_btn.pack(side="right", padx=(5, 0))
        
        save_btn = ttk.Button(
            button_frame,
            text="Save Return",
            command=self.save_return
        )
        save_btn.pack(side="right")
    
    def add_summary_row(self, parent, label, value, color="black", bold=False, large=False):
        """Add a row to the summary"""
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=3)
        
        font_size = 14 if large else 11
        font_weight = "bold" if bold else "normal"
        
        label_widget = ttk.Label(
            row,
            text=label,
            font=("Arial", font_size, font_weight)
        )
        label_widget.pack(side="left")
        
        value_widget = ttk.Label(
            row,
            text=value,
            font=("Arial", font_size, font_weight),
            foreground=color
        )
        value_widget.pack(side="right")
    
    def get_filing_status_text(self):
        """Convert filing status code to readable text"""
        status_map = {
            "Single": "Single",
            "MFJ": "Married Filing Jointly",
            "MFS": "Married Filing Separately",
            "HOH": "Head of Household",
            "QW": "Qualifying Widow(er)",
        }
        status = self.tax_data.get("filing_status.status", "")
        return status_map.get(status, status)
    
    def show_form_1040_preview(self):
        """Show preview of Form 1040 data"""
        preview_frame = ttk.Frame(self.scrollable_frame, relief="sunken", borderwidth=1, padding="10")
        preview_frame.pack(fill="both", expand=True, pady=5)
        
        # Create text widget for form preview
        text = tk.Text(preview_frame, height=30, width=80, font=("Courier", 9))
        text.pack(fill="both", expand=True)
        
        # Build form preview
        form_text = self.build_form_1040_text()
        text.insert("1.0", form_text)
        text.config(state="disabled")
        
        # Add scrollbar
        text_scroll = ttk.Scrollbar(preview_frame, command=text.yview)
        text.config(yscrollcommand=text_scroll.set)
    
    def build_form_1040_text(self):
        """Build text representation of Form 1040"""
        # Performance: Use cached totals instead of recalculating
        totals = self._cached_totals
        
        lines = []
        lines.append("=" * 80)
        lines.append("FORM 1040 - U.S. Individual Income Tax Return")
        lines.append(f"Tax Year: {self.tax_data.get('metadata.tax_year')}")
        lines.append("=" * 80)
        lines.append("")
        
        # Personal information
        lines.append("PERSONAL INFORMATION")
        lines.append("-" * 80)
        lines.append(f"Name: {self.tax_data.get('personal_info.first_name')} {self.tax_data.get('personal_info.last_name')}")
        lines.append(f"SSN: {self.tax_data.get('personal_info.ssn')}")
        lines.append(f"Address: {self.tax_data.get('personal_info.address')}")
        lines.append(f"         {self.tax_data.get('personal_info.city')}, {self.tax_data.get('personal_info.state')} {self.tax_data.get('personal_info.zip_code')}")
        lines.append(f"Filing Status: {self.get_filing_status_text()}")
        lines.append("")
        
        # Income
        lines.append("INCOME")
        lines.append("-" * 80)
        
        # Performance: Get income section once
        income_section = self.tax_data.get_section("income")
        
        # W-2 wages
        w2_forms = income_section.get("w2_forms", [])
        total_w2 = W2Calculator.calculate_total_wages(w2_forms)
        lines.append(f"Line 1  - Wages, salaries, tips, etc.......................... ${total_w2:>15,.2f}")
        
        # Interest
        interest_income = self.tax_data.get("income.interest_income", [])
        total_interest = sum(i.get("amount", 0) for i in interest_income)
        if total_interest > 0:
            lines.append(f"Line 2b - Taxable interest................................. ${total_interest:>15,.2f}")
        
        # Dividends
        dividend_income = self.tax_data.get("income.dividend_income", [])
        total_dividends = sum(d.get("amount", 0) for d in dividend_income)
        if total_dividends > 0:
            lines.append(f"Line 3b - Qualified dividends.............................. ${total_dividends:>15,.2f}")
        
        lines.append(f"\nLine 9  - TOTAL INCOME..................................... ${totals['total_income']:>15,.2f}")
        lines.append("")
        
        # AGI
        lines.append("ADJUSTED GROSS INCOME")
        lines.append("-" * 80)
        lines.append(f"Line 11 - ADJUSTED GROSS INCOME............................ ${totals['adjusted_gross_income']:>15,.2f}")
        lines.append("")
        
        # Deductions
        lines.append("DEDUCTIONS")
        lines.append("-" * 80)
        deduction_method = self.tax_data.get("deductions.method")
        if deduction_method == "standard":
            lines.append("Line 12 - Standard deduction")
        else:
            lines.append("Line 12 - Itemized deductions")
        lines.append("")
        
        # Taxable income
        lines.append(f"Line 15 - TAXABLE INCOME................................... ${totals['taxable_income']:>15,.2f}")
        lines.append("")
        
        # Tax
        lines.append("TAX AND CREDITS")
        lines.append("-" * 80)
        lines.append(f"Line 16 - Tax.............................................. ${totals['total_tax']:>15,.2f}")
        lines.append("")
        
        # Payments
        lines.append("PAYMENTS")
        lines.append("-" * 80)
        w2_withholding = W2Calculator.calculate_total_withholding(w2_forms)
        lines.append(f"Line 25 - Federal income tax withheld...................... ${w2_withholding:>15,.2f}")
        
        est_payments = self.tax_data.get("payments.estimated_payments", [])
        total_est = sum(p.get("amount", 0) for p in est_payments)
        if total_est > 0:
            lines.append(f"Line 26 - Estimated tax payments........................... ${total_est:>15,.2f}")
        
        lines.append(f"\nLine 33 - TOTAL PAYMENTS................................... ${totals['total_payments']:>15,.2f}")
        lines.append("")
        
        # Refund or amount owed
        lines.append("REFUND OR AMOUNT YOU OWE")
        lines.append("-" * 80)
        refund_owe = totals['refund_or_owe']
        if refund_owe > 0:
            lines.append(f"Line 34 - REFUND........................................... ${refund_owe:>15,.2f}")
        elif refund_owe < 0:
            lines.append(f"Line 37 - AMOUNT YOU OWE................................... ${-refund_owe:>15,.2f}")
        else:
            lines.append("Line 34 - No refund or amount owed")
        
        lines.append("")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def view_form(self, form_name):
        """View specific form"""
        messagebox.showinfo("View Form", f"Viewing {form_name}\n\nForm viewer functionality will display the actual IRS form with your data populated.")
    
    def export_to_pdf(self):
        """Export forms to PDF with password protection"""
        from utils.pdf_form_filler import TaxReturnPDFExporter
        import logging
        
        logger = logging.getLogger(__name__)
        
        filename = self._get_export_filename()
        if not filename:
            return
        
        password = self._get_password_if_requested()
        if password is False:  # User cancelled during password setup
            return
        
        self._perform_pdf_export(filename, password, logger)
    
    def _get_export_filename(self) -> str:
        """Get filename for PDF export from user"""
        return filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=f"tax_return_{self.tax_data.get('metadata.tax_year', '2025')}.pdf"
        )
    
    def _get_password_if_requested(self):
        """
        Prompt user for PDF password if they want protection.
        
        Returns:
            str: Valid password
            None: User chose no password
            False: User cancelled password setup
        """
        password_prompt = messagebox.askyesno(
            "PDF Security",
            "Would you like to password-protect your tax return PDF?\n\n"
            "This is HIGHLY RECOMMENDED to protect your sensitive information.\n\n"
            "Click Yes to add password protection."
        )
        
        if not password_prompt:
            return None
        
        password = self._prompt_for_password()
        if not password:
            return None
        
        if not self._confirm_password(password):
            return False
        
        if not self._validate_password_strength(password):
            return False
        
        return password
    
    def _prompt_for_password(self) -> str:
        """Prompt user to enter password"""
        return simpledialog.askstring(
            "PDF Password",
            "Enter a strong password for your tax return PDF:\n\n"
            "(You will need this password to open the PDF)",
            show='*'
        )
    
    def _confirm_password(self, password: str) -> bool:
        """Confirm password matches"""
        confirm = simpledialog.askstring(
            "Confirm Password",
            "Re-enter your password to confirm:",
            show='*'
        )
        
        if password != confirm:
            messagebox.showerror("Password Mismatch", "Passwords do not match. Export cancelled.")
            return False
        return True
    
    def _validate_password_strength(self, password: str) -> bool:
        """Validate password meets minimum strength requirements"""
        if len(password) >= 8:
            return True
        
        return messagebox.askyesno(
            "Weak Password",
            "Your password is short. For better security, use at least 8 characters.\n\nContinue anyway?"
        )
    
    def _perform_pdf_export(self, filename: str, password, logger):
        """Perform the actual PDF export operation"""
        try:
            exporter = TaxReturnPDFExporter()
            success = exporter.export_complete_return(
                self.tax_data,
                filename,
                password=password
            )
            
            if success:
                self._show_export_success(filename, password, logger)
            else:
                self._show_export_failure(filename, logger)
                
        except FileNotFoundError as e:
            self._show_file_not_found_error(e, logger)
        except Exception as e:
            self._show_generic_export_error(e, logger)
    
    def _show_export_success(self, filename: str, password, logger):
        """Show success message for PDF export"""
        security_msg = " (password protected)" if password else " (NOT password protected)"
        messagebox.showinfo(
            "Export Successful",
            f"Tax return exported successfully{security_msg}:\n{filename}\n\n"
            f"{'Remember your password!' if password else 'Warning: PDF is not encrypted. Anyone can view it.'}"
        )
        logger.info(f"PDF exported: {filename} (encrypted={bool(password)})")
    
    def _show_export_failure(self, filename: str, logger):
        """Show error message for export failure"""
        logger.error(f"PDF export failed: {filename}")
        messagebox.showerror(
            "Export Failed",
            "Failed to export tax return. Please try again or check the application logs."
        )
    
    def _show_file_not_found_error(self, error: Exception, logger):
        """Show error message for missing form files"""
        logger.error(f"Form file not found: {error}")
        messagebox.showerror(
            "File Not Found",
            "Required IRS form file not found. Please ensure the IRSTaxReturnDocumentation folder is intact."
        )
    
    def _show_generic_export_error(self, error: Exception, logger):
        """Show error message for unexpected export errors"""
        logger.error(f"PDF export error: {error}", exc_info=True)
        messagebox.showerror(
            "Export Error",
            "An unexpected error occurred while exporting. Please check file permissions and try again."
        )
    
    def save_return(self):
        """Save return to file"""
        self.main_window.save_progress()
