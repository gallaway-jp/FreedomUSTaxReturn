"""
Modern Form Viewer Page

CustomTkinter implementation for viewing tax return summaries, required forms, and PDF export.
"""

import customtkinter as ctk
from typing import Optional, Callable
from tkinter import messagebox, filedialog, simpledialog
from pathlib import Path

from config.app_config import AppConfig
from models.tax_data import TaxData
from utils.w2_calculator import W2Calculator


class ModernFormViewerPage(ctk.CTkFrame):
    """
    Modern form viewer page using CustomTkinter.

    Features:
    - Tax return summary with key financial information
    - Required forms listing with view buttons
    - Form 1040 preview in modern text display
    - PDF export with password protection
    - Save return functionality
    """

    def __init__(self, parent, tax_data: TaxData, config: AppConfig,
                 on_back_callback: Optional[Callable] = None):
        """
        Initialize the modern form viewer page.

        Args:
            parent: Parent widget
            tax_data: Tax data model
            config: Application configuration
            on_back_callback: Callback when back button is clicked
        """
        super().__init__(parent)
        self.tax_data = tax_data
        self.config = config
        self.on_back_callback = on_back_callback

        # Cache calculated totals for performance
        self._cached_totals = self.tax_data.calculate_totals()

        # UI components
        self.summary_frame = None
        self.forms_frame = None
        self.preview_frame = None

        self.build_ui()

    def build_ui(self):
        """Build the modern UI with scrollable content"""
        # Header section
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        title_label = ctk.CTkLabel(
            header_frame,
            text="Tax Return Summary & Forms",
            font=ctk.CTkFont(size=24)
        )
        title_label.pack(anchor="w", pady=(10, 5))

        instruction_label = ctk.CTkLabel(
            header_frame,
            text="Review your tax return summary and required forms below.",
            font=ctk.CTkFont(size=12),
            wraplength=700,
            justify="left"
        )
        instruction_label.pack(anchor="w", pady=(0, 10))

        # Scrollable frame for content
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Build sections
        self.build_summary_section()
        self.build_forms_section()
        self.build_preview_section()
        self.build_action_buttons()

    def build_summary_section(self):
        """Build the tax return summary section"""
        # Section header
        summary_header = ctk.CTkLabel(
            self.scrollable_frame,
            text="Tax Return Summary",
            font=ctk.CTkFont(size=18)
        )
        summary_header.pack(anchor="w", pady=(20, 15))

        # Summary card
        self.summary_frame = ctk.CTkFrame(self.scrollable_frame)
        self.summary_frame.pack(fill="x", pady=(0, 20))

        # Personal information
        self._add_summary_personal_info()

        # Financial summary
        self._add_summary_financial_info()

    def _add_summary_personal_info(self):
        """Add personal information to summary"""
        personal_frame = ctk.CTkFrame(self.summary_frame, fg_color="transparent")
        personal_frame.pack(fill="x", padx=20, pady=(20, 10))

        # Name
        name = f"{self.tax_data.get('personal_info.first_name')} {self.tax_data.get('personal_info.last_name')}"
        name_label = ctk.CTkLabel(
            personal_frame,
            text=f"Taxpayer: {name}",
            font=ctk.CTkFont(size=14)
        )
        name_label.pack(anchor="w", pady=(0, 5))

        # SSN (masked)
        ssn = self.tax_data.get('personal_info.ssn', 'N/A')
        masked_ssn = f"***-**-{ssn[-4:]}" if ssn != 'N/A' and len(ssn) >= 4 else 'N/A'
        ssn_label = ctk.CTkLabel(
            personal_frame,
            text=f"SSN: {masked_ssn}",
            font=ctk.CTkFont(size=12)
        )
        ssn_label.pack(anchor="w", pady=(0, 5))

        # Filing status
        filing_status = self._get_filing_status_text()
        status_label = ctk.CTkLabel(
            personal_frame,
            text=f"Filing Status: {filing_status}",
            font=ctk.CTkFont(size=12)
        )
        status_label.pack(anchor="w")

    def _add_summary_financial_info(self):
        """Add financial information to summary"""
        financial_frame = ctk.CTkFrame(self.summary_frame, fg_color="transparent")
        financial_frame.pack(fill="x", padx=20, pady=(10, 20))

        totals = self._cached_totals

        # Income section
        income_title = ctk.CTkLabel(
            financial_frame,
            text="Income Information",
            font=ctk.CTkFont(size=14)
        )
        income_title.pack(anchor="w", pady=(0, 10))

        self._add_financial_row(financial_frame, "Total Income", f"${totals['total_income']:,.2f}")
        self._add_financial_row(financial_frame, "Adjusted Gross Income", f"${totals['adjusted_gross_income']:,.2f}")
        self._add_financial_row(financial_frame, "Taxable Income", f"${totals['taxable_income']:,.2f}")

        # Separator
        separator1 = ctk.CTkFrame(financial_frame, height=2, fg_color="gray70")
        separator1.pack(fill="x", pady=15)

        # Tax section
        tax_title = ctk.CTkLabel(
            financial_frame,
            text="Tax & Payments",
            font=ctk.CTkFont(size=14)
        )
        tax_title.pack(anchor="w", pady=(0, 10))

        self._add_financial_row(financial_frame, "Total Tax", f"${totals['total_tax']:,.2f}", "red")
        self._add_financial_row(financial_frame, "Total Payments", f"${totals['total_payments']:,.2f}", "green")

        # Separator
        separator2 = ctk.CTkFrame(financial_frame, height=2, fg_color="gray70")
        separator2.pack(fill="x", pady=15)

        # Refund/Owe section
        refund_owe_title = ctk.CTkLabel(
            financial_frame,
            text="Refund or Amount Owed",
            font=ctk.CTkFont(size=14)
        )
        refund_owe_title.pack(anchor="w", pady=(0, 10))

        refund_owe = totals['refund_or_owe']
        if refund_owe > 0:
            self._add_financial_row(financial_frame, "REFUND", f"${refund_owe:,.2f}", "green", large=True, bold=True)
        elif refund_owe < 0:
            self._add_financial_row(financial_frame, "AMOUNT OWED", f"${-refund_owe:,.2f}", "red", large=True, bold=True)
        else:
            self._add_financial_row(financial_frame, "Balance", "$0.00", "black", large=True, bold=True)

    def _add_financial_row(self, parent, label: str, value: str, color: str = "black",
                          large: bool = False, bold: bool = False):
        """Add a financial information row"""
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", pady=2)

        font_size = 16 if large else 12
        font_weight = "bold" if bold else "normal"

        label_widget = ctk.CTkLabel(
            row_frame,
            text=label,
            font=ctk.CTkFont(size=font_size, weight=font_weight)
        )
        label_widget.pack(side="left")

        value_widget = ctk.CTkLabel(
            row_frame,
            text=value,
            font=ctk.CTkFont(size=font_size, weight=font_weight),
            text_color=color
        )
        value_widget.pack(side="right")

    def build_forms_section(self):
        """Build the required forms section"""
        # Section header
        forms_header = ctk.CTkLabel(
            self.scrollable_frame,
            text="Required Forms",
            font=ctk.CTkFont(size=18)
        )
        forms_header.pack(anchor="w", pady=(20, 15))

        # Forms container
        self.forms_frame = ctk.CTkFrame(self.scrollable_frame)
        self.forms_frame.pack(fill="x", pady=(0, 20))

        # Get required forms
        forms = self.tax_data.get_required_forms()

        if not forms:
            no_forms_label = ctk.CTkLabel(
                self.forms_frame,
                text="No additional forms required based on your tax situation.",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            no_forms_label.pack(pady=20)
            return

        # Forms count
        forms_count_label = ctk.CTkLabel(
            self.forms_frame,
            text=f"Based on your entries, you need to file the following {len(forms)} form(s):",
            font=ctk.CTkFont(size=12)
        )
        forms_count_label.pack(anchor="w", padx=20, pady=(20, 15))

        # Forms list
        for form in forms:
            self._add_form_item(form)

    def _add_form_item(self, form_name: str):
        """Add a form item to the list"""
        form_frame = ctk.CTkFrame(self.forms_frame)
        form_frame.pack(fill="x", padx=20, pady=(0, 10))

        # Form name
        form_label = ctk.CTkLabel(
            form_frame,
            text=f"• {form_name}",
            font=ctk.CTkFont(size=14)
        )
        form_label.pack(side="left", padx=10, pady=10)

        # View button
        view_button = ctk.CTkButton(
            form_frame,
            text="View Form",
            width=100,
            command=lambda f=form_name: self.view_form(f)
        )
        view_button.pack(side="right", padx=10, pady=10)

    def build_preview_section(self):
        """Build the Form 1040 preview section"""
        # Section header
        preview_header = ctk.CTkLabel(
            self.scrollable_frame,
            text="Form 1040 Preview",
            font=ctk.CTkFont(size=18)
        )
        preview_header.pack(anchor="w", pady=(20, 15))

        # Preview container
        self.preview_frame = ctk.CTkFrame(self.scrollable_frame)
        self.preview_frame.pack(fill="x", pady=(0, 20))

        # Create text box for form preview
        self.preview_textbox = ctk.CTkTextbox(
            self.preview_frame,
            font=ctk.CTkFont(family="Courier", size=10),
            wrap="none"
        )
        self.preview_textbox.pack(fill="both", expand=True, padx=20, pady=20)

        # Build and display form preview
        form_text = self._build_form_1040_text()
        self.preview_textbox.insert("0.0", form_text)
        self.preview_textbox.configure(state="disabled")

    def build_action_buttons(self):
        """Build the action buttons section"""
        buttons_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(20, 20))

        # Back button
        back_button = ctk.CTkButton(
            buttons_frame,
            text="← Back to Payments",
            command=self._on_back,
            width=150
        )
        back_button.pack(side="left")

        # Save button
        save_button = ctk.CTkButton(
            buttons_frame,
            text="Save Return",
            command=self.save_return,
            fg_color="blue",
            hover_color="dark blue",
            width=120
        )
        save_button.pack(side="right", padx=(10, 0))

        # Export button
        export_button = ctk.CTkButton(
            buttons_frame,
            text="Export to PDF",
            command=self.export_to_pdf,
            fg_color="green",
            hover_color="dark green",
            width=120
        )
        export_button.pack(side="right")

    def _get_filing_status_text(self) -> str:
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

    def _build_form_1040_text(self) -> str:
        """Build text representation of Form 1040"""
        totals = self._cached_totals

        lines = []
        lines.append("=" * 80)
        lines.append("FORM 1040 - U.S. Individual Income Tax Return")
        lines.append(f"Tax Year: {self.tax_data.get('metadata.tax_year', '2025')}")
        lines.append("=" * 80)
        lines.append("")

        # Personal information
        lines.append("PERSONAL INFORMATION")
        lines.append("-" * 80)
        lines.append(f"Name: {self.tax_data.get('personal_info.first_name')} {self.tax_data.get('personal_info.last_name')}")
        lines.append(f"SSN: {self.tax_data.get('personal_info.ssn')}")
        lines.append(f"Address: {self.tax_data.get('personal_info.address')}")
        lines.append(f"         {self.tax_data.get('personal_info.city')}, {self.tax_data.get('personal_info.state')} {self.tax_data.get('personal_info.zip_code')}")
        lines.append(f"Filing Status: {self._get_filing_status_text()}")
        lines.append("")

        # Income
        lines.append("INCOME")
        lines.append("-" * 80)

        # Get income section once for performance
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

    def view_form(self, form_name: str):
        """View specific form"""
        messagebox.showinfo(
            "View Form",
            f"Viewing {form_name}\n\nForm viewer functionality will display the actual IRS form with your data populated."
        )

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
        # This would typically call a save method from the main window
        messagebox.showinfo("Save Return", "Return saved successfully.")

    def refresh_data(self):
        """Refresh the form viewer with current tax data"""
        # Recalculate totals
        self._cached_totals = self.tax_data.calculate_totals()

        # Clear and rebuild sections
        for widget in self.summary_frame.winfo_children():
            widget.destroy()
        for widget in self.forms_frame.winfo_children():
            widget.destroy()

        self._add_summary_personal_info()
        self._add_summary_financial_info()

        # Rebuild forms section
        forms = self.tax_data.get_required_forms()
        if not forms:
            no_forms_label = ctk.CTkLabel(
                self.forms_frame,
                text="No additional forms required based on your tax situation.",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            no_forms_label.pack(pady=20)
        else:
            forms_count_label = ctk.CTkLabel(
                self.forms_frame,
                text=f"Based on your entries, you need to file the following {len(forms)} form(s):",
                font=ctk.CTkFont(size=12)
            )
            forms_count_label.pack(anchor="w", padx=20, pady=(20, 15))

            for form in forms:
                self._add_form_item(form)

        # Update preview
        form_text = self._build_form_1040_text()
        self.preview_textbox.configure(state="normal")
        self.preview_textbox.delete("0.0", "end")
        self.preview_textbox.insert("0.0", form_text)
        self.preview_textbox.configure(state="disabled")

    def _on_back(self):
        """Handle back button click"""
        if self.on_back_callback:
            self.on_back_callback()