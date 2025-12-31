"""
E-Filing Window - GUI for IRS Electronic Filing
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Dict, Any, Optional
import threading
import json

from services.e_filing_service import EFilingService
from models.tax_data import TaxData
from config.app_config import AppConfig


class EFilingWindow:
    """
    GUI window for e-filing tax returns with the IRS.
    """

    def __init__(self, parent: tk.Tk, tax_data: TaxData, config: AppConfig, e_filing_service: EFilingService):
        """
        Initialize e-filing window.

        Args:
            parent: Parent window
            tax_data: Tax return data
            config: Application configuration
            e_filing_service: E-filing service instance
        """
        self.parent = parent
        self.tax_data = tax_data
        self.config = config
        self.e_filing_service = e_filing_service

        self.window = tk.Toplevel(parent)
        self.window.title("IRS E-Filing - Freedom US Tax Return")
        self.window.geometry("800x600")
        self.window.resizable(True, True)

        # Initialize variables
        self.xml_content = ""
        self.signed_xml = ""
        self.submission_result = None

        self._create_ui()
        self._load_initial_data()

    def _create_ui(self):
        """Create the user interface."""
        # Main notebook for different tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self._create_prepare_tab()
        self._create_submit_tab()
        self._create_status_tab()

    def _create_prepare_tab(self):
        """Create the preparation tab."""
        prepare_frame = ttk.Frame(self.notebook)
        self.notebook.add(prepare_frame, text="Prepare E-File")

        # Taxpayer information section
        taxpayer_group = ttk.LabelFrame(prepare_frame, text="Taxpayer Information", padding=10)
        taxpayer_group.pack(fill=tk.X, pady=(0, 10))

        # Personal info fields
        info_frame = ttk.Frame(taxpayer_group)
        info_frame.pack(fill=tk.X)

        ttk.Label(info_frame, text="SSN:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.ssn_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.ssn_var, width=15).grid(row=0, column=1, padx=(0, 20))

        ttk.Label(info_frame, text="Name:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.name_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.name_var, width=30).grid(row=0, column=3)

        # Filing status
        ttk.Label(info_frame, text="Filing Status:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0), padx=(0, 5))
        self.filing_status_var = tk.StringVar()
        status_combo = ttk.Combobox(info_frame, textvariable=self.filing_status_var,
                                   values=['single', 'married_filing_jointly', 'married_filing_separately', 'head_of_household'],
                                   state='readonly', width=25)
        status_combo.grid(row=1, column=1, pady=(10, 0), padx=(0, 20))
        status_combo.current(0)

        # Tax year
        ttk.Label(info_frame, text="Tax Year:").grid(row=1, column=2, sticky=tk.W, pady=(10, 0), padx=(0, 5))
        self.tax_year_var = tk.StringVar(value="2025")
        ttk.Entry(info_frame, textvariable=self.tax_year_var, width=10).grid(row=1, column=3, pady=(10, 0))

        # Generate XML button
        ttk.Button(prepare_frame, text="Generate E-File XML",
                  command=self._generate_xml).pack(pady=(10, 0))

        # XML preview
        xml_group = ttk.LabelFrame(prepare_frame, text="XML Preview", padding=10)
        xml_group.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.xml_text = scrolledtext.ScrolledText(xml_group, height=15, wrap=tk.WORD)
        self.xml_text.pack(fill=tk.BOTH, expand=True)

        # Validation status
        self.validation_label = ttk.Label(xml_group, text="")
        self.validation_label.pack(anchor=tk.W, pady=(5, 0))

    def _create_submit_tab(self):
        """Create the submission tab."""
        submit_frame = ttk.Frame(self.notebook)
        self.notebook.add(submit_frame, text="Submit to IRS")

        # Authentication section
        auth_group = ttk.LabelFrame(submit_frame, text="IRS Authentication", padding=10)
        auth_group.pack(fill=tk.X, pady=(0, 10))

        auth_frame = ttk.Frame(auth_group)
        auth_frame.pack(fill=tk.X)

        # Row 1: EFIN and PIN
        ttk.Label(auth_frame, text="EFIN:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.efin_var = tk.StringVar()
        ttk.Entry(auth_frame, textvariable=self.efin_var, width=15).grid(row=0, column=1, padx=(0, 20))

        ttk.Label(auth_frame, text="PIN:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.pin_var = tk.StringVar()
        ttk.Entry(auth_frame, textvariable=self.pin_var, width=10, show="*").grid(row=0, column=3, padx=(0, 20))

        ttk.Label(auth_frame, text="Test Mode:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.test_mode_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(auth_frame, variable=self.test_mode_var).grid(row=0, column=5)

        # Row 2: PTIN (Professional Tax Identification Number)
        ttk.Label(auth_frame, text="PTIN:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0), padx=(0, 5))
        self.ptin_var = tk.StringVar()
        ttk.Entry(auth_frame, textvariable=self.ptin_var, width=15).grid(row=1, column=1, pady=(10, 0), padx=(0, 20))

        ttk.Label(auth_frame, text="(Optional - for professional preparers)").grid(row=1, column=2, columnspan=3, sticky=tk.W, pady=(10, 0))

        # Signature section
        sig_group = ttk.LabelFrame(submit_frame, text="Digital Signature", padding=10)
        sig_group.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(sig_group, text="Sign E-File XML",
                  command=self._sign_xml).pack(anchor=tk.W)

        self.signature_status_label = ttk.Label(sig_group, text="")
        self.signature_status_label.pack(anchor=tk.W, pady=(5, 0))

        # Submit section
        submit_group = ttk.LabelFrame(submit_frame, text="Submit to IRS", padding=10)
        submit_group.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(submit_group, text="Submit E-File to IRS",
                  command=self._submit_to_irs).pack(anchor=tk.W)

        # Submission results
        results_group = ttk.LabelFrame(submit_frame, text="Submission Results", padding=10)
        results_group.pack(fill=tk.BOTH, expand=True)

        self.results_text = scrolledtext.ScrolledText(results_group, height=10, wrap=tk.WORD)
        self.results_text.pack(fill=tk.BOTH, expand=True)

    def _create_status_tab(self):
        """Create the status tracking tab."""
        status_frame = ttk.Frame(self.notebook)
        self.notebook.add(status_frame, text="Status Tracking")

        # Status controls
        controls_frame = ttk.Frame(status_frame)
        controls_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(controls_frame, text="Confirmation Number:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.confirmation_var = tk.StringVar()
        ttk.Entry(controls_frame, textvariable=self.confirmation_var, width=20).grid(row=0, column=1, padx=(0, 10))

        ttk.Button(controls_frame, text="Check Status",
                  command=self._check_status).grid(row=0, column=2, padx=(0, 10))

        ttk.Button(controls_frame, text="Refresh All",
                  command=self._refresh_all_status).grid(row=0, column=3)

        # Status display
        status_group = ttk.LabelFrame(status_frame, text="E-File Status", padding=10)
        status_group.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Create treeview for status display
        columns = ('confirmation', 'status', 'submitted', 'tax_year', 'test_mode')
        self.status_tree = ttk.Treeview(status_group, columns=columns, show='headings', height=15)

        # Define headings
        self.status_tree.heading('confirmation', text='Confirmation #')
        self.status_tree.heading('status', text='Status')
        self.status_tree.heading('submitted', text='Submitted')
        self.status_tree.heading('tax_year', text='Tax Year')
        self.status_tree.heading('test_mode', text='Test Mode')

        # Define column widths
        self.status_tree.column('confirmation', width=150)
        self.status_tree.column('status', width=100)
        self.status_tree.column('submitted', width=150)
        self.status_tree.column('tax_year', width=80)
        self.status_tree.column('test_mode', width=80)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(status_group, orient=tk.VERTICAL, command=self.status_tree.yview)
        self.status_tree.configure(yscrollcommand=scrollbar.set)

        self.status_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Status details
        details_group = ttk.LabelFrame(status_frame, text="Status Details", padding=10)
        details_group.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.status_details_text = scrolledtext.ScrolledText(details_group, height=8, wrap=tk.WORD)
        self.status_details_text.pack(fill=tk.BOTH, expand=True)

        # Bind selection event
        self.status_tree.bind('<<TreeviewSelect>>', self._on_status_select)

    def _load_initial_data(self):
        """Load initial data from tax return."""
        personal_info = self.tax_data.get('personal_info', {})
        self.ssn_var.set(personal_info.get('ssn', ''))
        self.name_var.set(f"{personal_info.get('first_name', '')} {personal_info.get('last_name', '')}".strip())

        filing_status = self.tax_data.get('filing_status', 'single')
        self.filing_status_var.set(filing_status)

        # Load existing acknowledgments
        self._refresh_all_status()

    def _generate_xml(self):
        """Generate e-file XML."""
        try:
            # Update tax data with form values
            tax_year = int(self.tax_year_var.get())

            # Generate XML
            self.xml_content = self.e_filing_service.generate_efile_xml(self.tax_data, tax_year)

            # Display XML
            self.xml_text.delete(1.0, tk.END)
            self.xml_text.insert(tk.END, self.xml_content)

            # Validate XML
            validation_result = self.e_filing_service.validate_efile_xml(self.xml_content)

            if validation_result['valid']:
                self.validation_label.config(text="✓ XML is valid", foreground="green")
            else:
                errors = "; ".join(validation_result['errors'])
                self.validation_label.config(text=f"✗ Validation errors: {errors}", foreground="red")

            messagebox.showinfo("Success", "E-file XML generated successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate XML: {str(e)}")
            self.validation_label.config(text=f"✗ Error: {str(e)}", foreground="red")

    def _sign_xml(self):
        """Sign the e-file XML."""
        if not self.xml_content:
            messagebox.showwarning("Warning", "Please generate XML first!")
            return

        try:
            signature_data = {
                'efin': self.efin_var.get(),
                'pin': self.pin_var.get(),
                'ptin': self.ptin_var.get().strip() if self.ptin_var.get().strip() else None
            }

            self.signed_xml = self.e_filing_service.sign_efile_xml(self.xml_content, signature_data)
            self.signature_status_label.config(text="✓ XML signed successfully", foreground="green")

            messagebox.showinfo("Success", "E-file XML signed successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to sign XML: {str(e)}")
            self.signature_status_label.config(text=f"✗ Signing failed: {str(e)}", foreground="red")

    def _submit_to_irs(self):
        """Submit e-file to IRS."""
        if not self.signed_xml:
            messagebox.showwarning("Warning", "Please sign XML first!")
            return

        if not self.efin_var.get() or not self.pin_var.get():
            messagebox.showwarning("Warning", "Please enter EFIN and PIN!")
            return

        # Check if PTIN is provided and validate it
        ptin = self.ptin_var.get().strip()
        if ptin and not ptin.upper().startswith('P'):
            messagebox.showwarning("Warning", "PTIN should start with 'P' (e.g., P12345678)")
            return

        # Disable submit button during submission
        submit_button = self.notebook.winfo_children()[1].winfo_children()[2].winfo_children()[1]  # Complex path to button
        submit_button.config(state='disabled')

        def submit_thread():
            try:
                submission_data = {
                    'efin': self.efin_var.get(),
                    'pin': self.pin_var.get(),
                    'ptin': ptin if ptin else None,
                    'tax_year': int(self.tax_year_var.get()),
                    'test_mode': self.test_mode_var.get()
                }

                self.submission_result = self.e_filing_service.submit_efile_to_irs(
                    self.signed_xml, submission_data
                )

                # Update UI in main thread
                self.window.after(0, lambda: self._show_submission_result())

            except Exception as e:
                self.window.after(0, lambda: messagebox.showerror("Error", f"Submission failed: {str(e)}"))
            finally:
                self.window.after(0, lambda: submit_button.config(state='normal'))

        # Run submission in background thread
        threading.Thread(target=submit_thread, daemon=True).start()

    def _show_submission_result(self):
        """Show submission results."""
        if self.submission_result:
            result_text = json.dumps(self.submission_result, indent=2)
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, result_text)

            if self.submission_result.get('success'):
                messagebox.showinfo("Success", "E-file submitted successfully!")
                # Refresh status tab
                self._refresh_all_status()
            else:
                messagebox.showerror("Submission Failed", self.submission_result.get('error', 'Unknown error'))

    def _check_status(self):
        """Check status of a specific confirmation number."""
        confirmation = self.confirmation_var.get().strip()
        if not confirmation:
            messagebox.showwarning("Warning", "Please enter a confirmation number!")
            return

        try:
            submission_data = {
                'efin': self.efin_var.get(),
                'test_mode': self.test_mode_var.get()
            }

            status = self.e_filing_service.check_efile_status(confirmation, submission_data)

            # Display status details
            details = json.dumps(status, indent=2)
            self.status_details_text.delete(1.0, tk.END)
            self.status_details_text.insert(tk.END, details)

            # Refresh the status list
            self._refresh_all_status()

            messagebox.showinfo("Status Check", f"Status: {status.get('status', 'Unknown')}")

        except Exception as e:
            messagebox.showerror("Error", f"Status check failed: {str(e)}")

    def _refresh_all_status(self):
        """Refresh all acknowledgment statuses."""
        # Clear existing items
        for item in self.status_tree.get_children():
            self.status_tree.delete(item)

        try:
            acknowledgments = self.e_filing_service.get_all_acknowledgments()

            for conf_num, data in acknowledgments.items():
                self.status_tree.insert('', tk.END, values=(
                    conf_num,
                    data.get('status', 'Unknown'),
                    data.get('submission_date', 'Unknown'),
                    data.get('tax_year', 'Unknown'),
                    'Yes' if data.get('test_mode') else 'No'
                ))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load acknowledgments: {str(e)}")

    def _on_status_select(self, event):
        """Handle status selection in treeview."""
        selection = self.status_tree.selection()
        if selection:
            item = self.status_tree.item(selection[0])
            confirmation = item['values'][0]

            # Get full status details
            status = self.e_filing_service.get_acknowledgment_status(confirmation)
            if status:
                details = json.dumps(status, indent=2)
                self.status_details_text.delete(1.0, tk.END)
                self.status_details_text.insert(tk.END, details)
                self.confirmation_var.set(confirmation)


def open_e_filing_window(parent: tk.Tk, tax_data: TaxData, config: AppConfig = None, ptin_ero_service = None):
    """
    Open the e-filing window.

    Args:
        parent: Parent window
        tax_data: Tax return data
        config: Application configuration
        ptin_ero_service: PTIN/ERO service instance
    """
    if config is None:
        config = AppConfig.from_env()

    # Import here to avoid circular imports
    from services.e_filing_service import EFilingService

    e_filing_service = EFilingService(config, ptin_ero_service=ptin_ero_service)
    EFilingWindow(parent, tax_data, config, e_filing_service)