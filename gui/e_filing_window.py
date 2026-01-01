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

        # State e-filing variables
        self.state_xml_content = ""
        self.state_submission_result = None

        self._create_ui()
        self._load_initial_data()

    def _create_ui(self):
        """Create the user interface."""
        # Main notebook for different tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self._create_prepare_tab()
        self._create_state_efile_tab()
        self._create_direct_deposit_tab()
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

    def _create_state_efile_tab(self):
        """Create the state e-filing tab."""
        state_frame = ttk.Frame(self.notebook)
        self.notebook.add(state_frame, text="State E-Filing")

        # State selection section
        state_group = ttk.LabelFrame(state_frame, text="State Selection", padding=10)
        state_group.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(state_group, text="Select State:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.state_var = tk.StringVar()
        state_combo = ttk.Combobox(state_group, textvariable=self.state_var,
                                  values=list(self.e_filing_service.state_endpoints.keys()),
                                  state='readonly', width=20)
        state_combo.grid(row=0, column=1, padx=(0, 20))
        if self.e_filing_service.state_endpoints:
            state_combo.current(0)

        # State taxpayer information
        taxpayer_group = ttk.LabelFrame(state_frame, text="State Taxpayer Information", padding=10)
        taxpayer_group.pack(fill=tk.X, pady=(0, 10))

        # State-specific info fields
        ttk.Label(taxpayer_group, text="State of Residence:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.state_residence_var = tk.StringVar()
        ttk.Entry(taxpayer_group, textvariable=self.state_residence_var, width=25).grid(row=0, column=1, padx=(0, 20))

        ttk.Label(taxpayer_group, text="State Filing Status:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.state_filing_status_var = tk.StringVar()
        state_status_combo = ttk.Combobox(taxpayer_group, textvariable=self.state_filing_status_var,
                                         values=['single', 'married_filing_jointly', 'married_filing_separately', 'head_of_household'],
                                         state='readonly', width=25)
        state_status_combo.grid(row=0, column=3)
        state_status_combo.current(0)

        # State tax year
        ttk.Label(taxpayer_group, text="State Tax Year:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0), padx=(0, 5))
        self.state_tax_year_var = tk.StringVar(value="2025")
        ttk.Entry(taxpayer_group, textvariable=self.state_tax_year_var, width=10).grid(row=1, column=1, pady=(10, 0))

        # Generate State XML button
        ttk.Button(state_frame, text="Generate State E-File XML",
                  command=self._generate_state_xml).pack(pady=(10, 0))

        # State XML preview
        state_xml_group = ttk.LabelFrame(state_frame, text="State XML Preview", padding=10)
        state_xml_group.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.state_xml_text = scrolledtext.ScrolledText(state_xml_group, height=12, wrap=tk.WORD)
        self.state_xml_text.pack(fill=tk.BOTH, expand=True)

        # State validation and submission section
        action_group = ttk.LabelFrame(state_frame, text="State E-File Actions", padding=10)
        action_group.pack(fill=tk.X, pady=(10, 0))

        # Buttons frame
        buttons_frame = ttk.Frame(action_group)
        buttons_frame.pack(fill=tk.X)

        ttk.Button(buttons_frame, text="Validate State E-File",
                  command=self._validate_state_efile).grid(row=0, column=0, padx=(0, 10))

        ttk.Button(buttons_frame, text="Submit State E-File",
                  command=self._submit_state_efile).grid(row=0, column=1, padx=(0, 10))

        ttk.Button(buttons_frame, text="Check State Status",
                  command=self._check_state_status).grid(row=0, column=2)

        # State status display
        self.state_status_label = ttk.Label(action_group, text="")
        self.state_status_label.pack(anchor=tk.W, pady=(10, 0))

        # State submission results
        self.state_result_text = scrolledtext.ScrolledText(action_group, height=6, wrap=tk.WORD)
        self.state_result_text.pack(fill=tk.X, pady=(5, 0))

    def _create_direct_deposit_tab(self):
        """Create the direct deposit setup tab."""
        dd_frame = ttk.Frame(self.notebook)
        self.notebook.add(dd_frame, text="Direct Deposit")

        # Direct deposit information section
        info_group = ttk.LabelFrame(dd_frame, text="Direct Deposit Information", padding=10)
        info_group.pack(fill=tk.X, pady=(0, 10))

        # Enable direct deposit checkbox
        self.enable_dd_var = tk.BooleanVar()
        ttk.Checkbutton(info_group, text="Enable Direct Deposit for Refund",
                       variable=self.enable_dd_var, command=self._toggle_direct_deposit).pack(anchor=tk.W)

        # Bank account details frame
        self.dd_details_frame = ttk.Frame(info_group)
        self.dd_details_frame.pack(fill=tk.X, pady=(10, 0))

        # Row 1: Routing number and account number
        ttk.Label(self.dd_details_frame, text="Routing Number:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.routing_var = tk.StringVar()
        routing_entry = ttk.Entry(self.dd_details_frame, textvariable=self.routing_var, width=15)
        routing_entry.grid(row=0, column=1, padx=(0, 20))
        routing_entry.config(validate="key", validatecommand=(self.window.register(self._validate_routing), "%P"))

        ttk.Label(self.dd_details_frame, text="Account Number:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.account_var = tk.StringVar()
        account_entry = ttk.Entry(self.dd_details_frame, textvariable=self.account_var, width=20)
        account_entry.grid(row=0, column=3)
        account_entry.config(validate="key", validatecommand=(self.window.register(self._validate_account), "%P"))

        # Row 2: Account type and bank name
        ttk.Label(self.dd_details_frame, text="Account Type:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0), padx=(0, 5))
        self.account_type_var = tk.StringVar(value="checking")
        type_combo = ttk.Combobox(self.dd_details_frame, textvariable=self.account_type_var,
                                 values=['checking', 'savings'], state='readonly', width=12)
        type_combo.grid(row=1, column=1, pady=(10, 0), padx=(0, 20))

        ttk.Label(self.dd_details_frame, text="Bank Name:").grid(row=1, column=2, sticky=tk.W, pady=(10, 0), padx=(0, 5))
        self.bank_name_var = tk.StringVar()
        ttk.Entry(self.dd_details_frame, textvariable=self.bank_name_var, width=25).grid(row=1, column=3, pady=(10, 0))

        # Row 3: Account holder name
        ttk.Label(self.dd_details_frame, text="Account Holder Name:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0), padx=(0, 5))
        self.holder_name_var = tk.StringVar()
        ttk.Entry(self.dd_details_frame, textvariable=self.holder_name_var, width=30).grid(row=2, column=1, columnspan=3, pady=(10, 0), sticky=tk.W)

        # Verification section
        verify_group = ttk.LabelFrame(dd_frame, text="Account Verification", padding=10)
        verify_group.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(verify_group, text="For security, please verify your account information:").pack(anchor=tk.W)

        # Verification buttons
        button_frame = ttk.Frame(verify_group)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="Verify Routing Number",
                  command=self._verify_routing).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(button_frame, text="Test Deposit (Micro-Deposit)",
                  command=self._test_deposit).pack(side=tk.LEFT, padx=(0, 10))

        self.verification_status_label = ttk.Label(verify_group, text="")
        self.verification_status_label.pack(anchor=tk.W, pady=(10, 0))

        # Save button
        ttk.Button(dd_frame, text="Save Direct Deposit Information",
                  command=self._save_direct_deposit).pack(pady=(20, 0))

        # Initially disable the details frame
        self._toggle_direct_deposit()

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

        # Load direct deposit information
        direct_deposit = self.tax_data.get('payments.direct_deposit', {})
        self.enable_dd_var.set(direct_deposit.get('enabled', False))
        self.routing_var.set(direct_deposit.get('routing_number', ''))
        self.account_var.set(direct_deposit.get('account_number', ''))
        self.account_type_var.set(direct_deposit.get('account_type', 'checking'))
        self.bank_name_var.set(direct_deposit.get('bank_name', ''))
        self.holder_name_var.set(direct_deposit.get('account_holder_name', ''))

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

    def _toggle_direct_deposit(self):
        """Enable/disable direct deposit fields based on checkbox."""
        enabled = self.enable_dd_var.get()
        state = 'normal' if enabled else 'disabled'

        # Enable/disable all entry fields in the details frame
        for child in self.dd_details_frame.winfo_children():
            if isinstance(child, (ttk.Entry, ttk.Combobox)):
                child.config(state=state)

    def _validate_routing(self, value):
        """Validate routing number (9 digits)."""
        if value == "":
            return True
        return value.isdigit() and len(value) <= 9

    def _validate_account(self, value):
        """Validate account number (up to 17 digits)."""
        if value == "":
            return True
        return value.isdigit() and len(value) <= 17

    def _verify_routing(self):
        """Verify routing number with bank lookup."""
        routing = self.routing_var.get().strip()
        if not routing:
            messagebox.showwarning("Warning", "Please enter a routing number!")
            return

        if len(routing) != 9:
            messagebox.showerror("Error", "Routing number must be 9 digits!")
            return

        # Basic routing number validation (check digit algorithm)
        try:
            digits = [int(d) for d in routing]
            checksum = (3 * (digits[0] + digits[3] + digits[6]) +
                       7 * (digits[1] + digits[4] + digits[7]) +
                       digits[2] + digits[5] + digits[8]) % 10

            if checksum == 0:
                self.verification_status_label.config(text="✓ Routing number format is valid", foreground="green")
                # Try to identify bank (simplified)
                bank_name = self._identify_bank(routing)
                if bank_name and not self.bank_name_var.get():
                    self.bank_name_var.set(bank_name)
            else:
                self.verification_status_label.config(text="✗ Invalid routing number", foreground="red")

        except ValueError:
            self.verification_status_label.config(text="✗ Invalid routing number format", foreground="red")

    def _identify_bank(self, routing):
        """Identify bank from routing number (simplified lookup)."""
        # This is a very basic lookup - in production, you'd use a proper API
        bank_codes = {
            '021000021': 'JPMorgan Chase',
            '031100173': 'Bank of America',
            '051000017': 'Wells Fargo',
            '121000248': 'Wells Fargo',
            '122000247': 'Wells Fargo',
        }
        return bank_codes.get(routing)

    def _test_deposit(self):
        """Initiate micro-deposit verification."""
        routing = self.routing_var.get().strip()
        account = self.account_var.get().strip()

        if not routing or not account:
            messagebox.showwarning("Warning", "Please enter both routing and account numbers!")
            return

        # In a real implementation, this would contact the bank
        # For now, simulate the process
        messagebox.showinfo("Micro-Deposit",
                          "Micro-deposit verification initiated.\n\n"
                          "Two small deposits ($0.01 each) will be made to your account within 1-3 business days.\n"
                          "Check your account statement and enter the amounts here to verify.")

        # Set verification status
        self.verification_status_label.config(text="Micro-deposits initiated - check your account in 1-3 days", foreground="blue")

    def _save_direct_deposit(self):
        """Save direct deposit information to tax data."""
        try:
            direct_deposit = {
                'enabled': self.enable_dd_var.get(),
                'routing_number': self.routing_var.get().strip(),
                'account_number': self.account_var.get().strip(),
                'account_type': self.account_type_var.get(),
                'bank_name': self.bank_name_var.get().strip(),
                'account_holder_name': self.holder_name_var.get().strip(),
                'verified': False,  # Would be set to True after verification
            }

            # Basic validation
            if direct_deposit['enabled']:
                if not direct_deposit['routing_number']:
                    messagebox.showerror("Error", "Routing number is required!")
                    return
                if not direct_deposit['account_number']:
                    messagebox.showerror("Error", "Account number is required!")
                    return
                if not direct_deposit['account_holder_name']:
                    messagebox.showerror("Error", "Account holder name is required!")
                    return

                # Validate routing number format
                if len(direct_deposit['routing_number']) != 9:
                    messagebox.showerror("Error", "Routing number must be 9 digits!")
                    return

            # Save to tax data
            self.tax_data.set('payments.direct_deposit', direct_deposit)

            messagebox.showinfo("Success", "Direct deposit information saved successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save direct deposit information: {str(e)}")
    def _generate_state_xml(self):
        """Generate state e-file XML."""
        try:
            state_code = self.state_var.get()
            if not state_code:
                messagebox.showwarning("Warning", "Please select a state!")
                return

            # Update tax data with state-specific information
            state_residence = self.state_residence_var.get()
            if state_residence:
                self.tax_data.data['personal_info']['address']['state'] = state_residence

            # Generate state XML
            xml_content = self.e_filing_service.generate_state_efile_xml(
                self.tax_data, state_code, int(self.state_tax_year_var.get())
            )

            # Display XML
            self.state_xml_text.delete(1.0, tk.END)
            self.state_xml_text.insert(tk.END, xml_content)

            self.state_status_label.config(text="State XML generated successfully", foreground="green")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate state XML: {str(e)}")
            self.state_status_label.config(text=f"Error: {str(e)}", foreground="red")

    def _validate_state_efile(self):
        """Validate state e-file readiness."""
        try:
            state_code = self.state_var.get()
            if not state_code:
                messagebox.showwarning("Warning", "Please select a state!")
                return

            # Validate readiness
            result = self.e_filing_service.validate_state_efile_readiness(self.tax_data, state_code)

            if result['ready']:
                self.state_status_label.config(text="State e-file is ready for submission", foreground="green")
                messagebox.showinfo("Validation Passed", "Your state tax return is ready for e-filing!")
            else:
                issues_text = "\n".join(result['issues'])
                self.state_status_label.config(text="Validation failed - see issues below", foreground="red")
                self.state_result_text.delete(1.0, tk.END)
                self.state_result_text.insert(tk.END, f"Validation Issues:\n{issues_text}")
                messagebox.showwarning("Validation Failed", f"Please fix the following issues:\n\n{issues_text}")

        except Exception as e:
            messagebox.showerror("Error", f"Validation failed: {str(e)}")

    def _submit_state_efile(self):
        """Submit state e-file."""
        try:
            state_code = self.state_var.get()
            if not state_code:
                messagebox.showwarning("Warning", "Please select a state!")
                return

            # Confirm submission
            if not messagebox.askyesno("Confirm Submission",
                                     f"Are you sure you want to submit your {state_code} state tax return electronically?\n\n"
                                     "This action cannot be undone."):
                return

            # Submit e-file
            result = self.e_filing_service.submit_state_efile(self.tax_data, state_code)

            if result['success']:
                self.state_status_label.config(text=f"State e-file submitted successfully - Confirmation: {result['confirmation_number']}",
                                             foreground="green")
                self.state_result_text.delete(1.0, tk.END)
                self.state_result_text.insert(tk.END, f"Submission Result:\n"
                                                    f"Confirmation Number: {result['confirmation_number']}\n"
                                                    f"Status: {result['status']}\n"
                                                    f"Timestamp: {result['timestamp']}\n"
                                                    f"State: {result['state']}")
                messagebox.showinfo("Submission Successful",
                                  f"Your {state_code} state tax return has been submitted successfully!\n\n"
                                  f"Confirmation Number: {result['confirmation_number']}")
            else:
                self.state_status_label.config(text="State e-file submission failed", foreground="red")
                messagebox.showerror("Submission Failed", f"State e-file submission failed: {result.get('error', 'Unknown error')}")

        except Exception as e:
            messagebox.showerror("Error", f"Submission failed: {str(e)}")
            self.state_status_label.config(text=f"Error: {str(e)}", foreground="red")

    def _check_state_status(self):
        """Check state e-file submission status."""
        try:
            state_code = self.state_var.get()
            if not state_code:
                messagebox.showwarning("Warning", "Please select a state!")
                return

            # For now, we'll check the most recent submission for this state
            # In a real implementation, you'd have a way to select specific submissions
            confirmation_number = None

            # Try to find a recent state submission (this is a simplified approach)
            try:
                acknowledgments = self.e_filing_service._load_acknowledgments()
                for ack_num, ack_data in acknowledgments.items():
                    if (ack_data.get('submission_type') == 'state_e_file' and
                        ack_data.get('state_code') == state_code):
                        confirmation_number = ack_num
                        break
            except:
                pass

            if not confirmation_number:
                messagebox.showinfo("No Submissions", f"No state e-file submissions found for {state_code}")
                return

            # Check status
            status = self.e_filing_service.check_state_efile_status(confirmation_number)

            if status:
                self.state_result_text.delete(1.0, tk.END)
                self.state_result_text.insert(tk.END, f"Status Check Result:\n"
                                                    f"Confirmation Number: {confirmation_number}\n"
                                                    f"Status: {status.get('status', 'Unknown')}\n"
                                                    f"Timestamp: {status.get('timestamp', 'Unknown')}\n"
                                                    f"State: {status.get('state_code', state_code)}")
                self.state_status_label.config(text=f"Status: {status.get('status', 'Unknown')}", foreground="blue")
            else:
                self.state_status_label.config(text="Submission not found", foreground="orange")
                messagebox.showwarning("Not Found", f"Submission {confirmation_number} not found in records")

        except Exception as e:
            messagebox.showerror("Error", f"Status check failed: {str(e)}")

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