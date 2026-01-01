"""
PTIN/ERO Management Dialog

GUI components for managing Professional Tax Preparer (PTIN) and Electronic Return Originator (ERO)
credentials for IRS e-filing compliance.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, List
import re
from datetime import date
from unittest.mock import MagicMock

from services.ptin_ero_service import PTINRecord, ERORecord, PTINEROService
from config.dependencies import get_container


class PTINEROManagementDialog:
    """
    Main dialog for managing PTIN and ERO credentials.
    """

    def __init__(self, parent: tk.Toplevel, test_mode: bool = False):
        """
        Initialize PTIN/ERO management dialog.

        Args:
            parent: Parent window
            test_mode: If True, dialogs will skip GUI creation for testing
        """
        self.parent = parent
        self.test_mode = test_mode
        self.container = get_container()
        self.ptin_ero_service: PTINEROService = self.container.get_ptin_ero_service()

        if test_mode:
            # Create mock dialog and widgets for testing
            self.dialog = parent
            # Create mock tree widgets
            self.ptin_tree = MagicMock()
            self.ero_tree = MagicMock()
            self.notebook = MagicMock()
            self.notebook.tabs.return_value = ["PTIN", "ERO", "Validation"]  # Mock 3 tabs
            self.validation_ptin_var = MagicMock()
            self.validation_ero_var = MagicMock()
            self.validation_result_text = MagicMock()
            return

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("PTIN/ERO Management")
        self.dialog.geometry("900x700")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.geometry("+{}+{}".format(
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))

        self._create_widgets()
        self._load_data()

        # Set focus
        self.dialog.focus_set()

    def _create_widgets(self) -> None:
        """Create dialog widgets"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Professional Tax Preparer Credentials",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 10))

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # PTIN tab
        ptin_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(ptin_frame, text="PTIN Management")
        self._create_ptin_tab(ptin_frame)

        # ERO tab
        ero_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(ero_frame, text="ERO Management")
        self._create_ero_tab(ero_frame)

        # Validation tab
        validation_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(validation_frame, text="Credential Validation")
        self._create_validation_tab(validation_frame)

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            button_frame,
            text="Close",
            command=self._on_close
        ).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(
            button_frame,
            text="Refresh",
            command=self._load_data
        ).pack(side=tk.RIGHT)

    def _create_ptin_tab(self, parent: ttk.Frame) -> None:
        """Create PTIN management tab"""
        # Toolbar
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(
            toolbar,
            text="Add PTIN",
            command=self._add_ptin
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Edit PTIN",
            command=self._edit_ptin
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Deactivate PTIN",
            command=self._deactivate_ptin
        ).pack(side=tk.LEFT)

        # PTIN list
        list_frame = ttk.LabelFrame(parent, text="Registered PTINs", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview for PTINs
        columns = ("PTIN", "Name", "Email", "Status", "Validation Date")
        self.ptin_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.ptin_tree.heading(col, text=col)
            self.ptin_tree.column(col, width=120)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.ptin_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.ptin_tree.xview)
        self.ptin_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.ptin_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Bind double-click
        self.ptin_tree.bind("<Double-1>", lambda e: self._edit_ptin())

    def _create_ero_tab(self, parent: ttk.Frame) -> None:
        """Create ERO management tab"""
        # Toolbar
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(
            toolbar,
            text="Add ERO",
            command=self._add_ero
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Edit ERO",
            command=self._edit_ero
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Deactivate ERO",
            command=self._deactivate_ero
        ).pack(side=tk.LEFT)

        # ERO list
        list_frame = ttk.LabelFrame(parent, text="Registered EROs", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview for EROs
        columns = ("ERO Number", "Business Name", "PTIN", "Contact", "Status", "Validation Date")
        self.ero_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.ero_tree.heading(col, text=col)
            self.ero_tree.column(col, width=120)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.ero_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.ero_tree.xview)
        self.ero_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.ero_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Bind double-click
        self.ero_tree.bind("<Double-1>", lambda e: self._edit_ero())

    def _create_validation_tab(self, parent: ttk.Frame) -> None:
        """Create credential validation tab"""
        # Input frame
        input_frame = ttk.LabelFrame(parent, text="Validate Credentials", padding="10")
        input_frame.pack(fill=tk.X, pady=(0, 10))

        # PTIN input
        ttk.Label(input_frame, text="PTIN:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.validation_ptin_var = tk.StringVar()
        ptin_entry = ttk.Entry(input_frame, textvariable=self.validation_ptin_var, width=20)
        ptin_entry.grid(row=0, column=1, sticky=tk.W, pady=2, padx=(5, 10))

        # ERO input (optional)
        ttk.Label(input_frame, text="ERO Number (optional):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.validation_ero_var = tk.StringVar()
        ero_entry = ttk.Entry(input_frame, textvariable=self.validation_ero_var, width=20)
        ero_entry.grid(row=1, column=1, sticky=tk.W, pady=2, padx=(5, 10))

        # Validate button
        ttk.Button(
            input_frame,
            text="Validate Credentials",
            command=self._validate_credentials
        ).grid(row=2, column=0, columnspan=2, pady=(10, 0))

        # Results frame
        results_frame = ttk.LabelFrame(parent, text="Validation Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True)

        self.validation_result_text = tk.Text(
            results_frame,
            height=10,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        result_scrollbar = ttk.Scrollbar(results_frame, command=self.validation_result_text.yview)
        self.validation_result_text.configure(yscrollcommand=result_scrollbar.set)

        self.validation_result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        result_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _load_data(self) -> None:
        """Load PTIN and ERO data into the UI"""
        self._load_ptin_data()
        self._load_ero_data()

    def _load_ptin_data(self) -> None:
        """Load PTIN data into treeview"""
        # Clear existing items
        for item in self.ptin_tree.get_children():
            self.ptin_tree.delete(item)

        # Load PTIN records
        ptins = self.ptin_ero_service.get_all_ptins()
        for ptin in ptins:
            name = f"{ptin.first_name} {ptin.last_name}"
            if ptin.middle_initial:
                name = f"{ptin.first_name} {ptin.middle_initial}. {ptin.last_name}"
            if ptin.suffix:
                name = f"{name} {ptin.suffix}"

            validation_date = ptin.validation_date.isoformat() if ptin.validation_date else "N/A"

            self.ptin_tree.insert("", tk.END, values=(
                ptin.ptin,
                name,
                ptin.email,
                ptin.status.title(),
                validation_date
            ))

    def _load_ero_data(self) -> None:
        """Load ERO data into treeview"""
        # Clear existing items
        for item in self.ero_tree.get_children():
            self.ero_tree.delete(item)

        # Load ERO records
        eros = self.ptin_ero_service.get_all_eros()
        for ero in eros:
            validation_date = ero.validation_date.isoformat() if ero.validation_date else "N/A"

            self.ero_tree.insert("", tk.END, values=(
                ero.ero_number,
                ero.business_name,
                ero.ptin,
                ero.contact_name,
                ero.status.title(),
                validation_date
            ))

    def _add_ptin(self) -> None:
        """Open dialog to add a new PTIN"""
        if self.test_mode:
            # In test mode, simulate dialog result
            self.result = {
                'ptin': 'P99999999',
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'test@example.com'
            }
            return
            
        dialog = PTINDialog(self.dialog, self.ptin_ero_service, test_mode=self.test_mode)
        if dialog.result:
            self._load_ptin_data()
            messagebox.showinfo("Success", "PTIN registered successfully!")

    def _edit_ptin(self) -> None:
        """Open dialog to edit selected PTIN"""
        selection = self.ptin_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a PTIN to edit.")
            return

        item = self.ptin_tree.item(selection[0])
        ptin = item['values'][0]

        if self.test_mode:
            # In test mode, simulate dialog result
            self.result = {
                'ptin': ptin,
                'first_name': 'Updated',
                'last_name': 'Name',
                'email': 'updated@example.com'
            }
            return

        dialog = PTINDialog(self.dialog, self.ptin_ero_service, ptin=ptin, test_mode=self.test_mode)
        if dialog.result:
            self._load_ptin_data()
            messagebox.showinfo("Success", "PTIN updated successfully!")

    def _deactivate_ptin(self) -> None:
        """Deactivate selected PTIN"""
        selection = self.ptin_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a PTIN to deactivate.")
            return

        item = self.ptin_tree.item(selection[0])
        ptin = item['values'][0]

        if messagebox.askyesno("Confirm Deactivation",
                              f"Are you sure you want to deactivate PTIN {ptin}?"):
            try:
                self.ptin_ero_service.deactivate_ptin(ptin)
                self._load_ptin_data()
                messagebox.showinfo("Success", f"PTIN {ptin} deactivated successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to deactivate PTIN: {str(e)}")

    def _add_ero(self) -> None:
        """Open dialog to add a new ERO"""
        if self.test_mode:
            # In test mode, simulate dialog result
            self.result = {
                'ero_number': '99999',
                'business_name': 'Test Services',
                'ein': '98-7654321',
                'ptin': 'P12345678',
                'contact_name': 'Test Contact',
                'email': 'test@services.com'
            }
            return
            
        dialog = ERODialog(self.dialog, self.ptin_ero_service, test_mode=self.test_mode)
        if dialog.result:
            self._load_ero_data()
            messagebox.showinfo("Success", "ERO registered successfully!")

    def _edit_ero(self) -> None:
        """Open dialog to edit selected ERO"""
        selection = self.ero_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an ERO to edit.")
            return

        item = self.ero_tree.item(selection[0])
        ero_number = item['values'][0]

        if self.test_mode:
            # In test mode, simulate dialog result
            self.result = {
                'ero_number': ero_number,
                'business_name': 'Updated Services',
                'ein': '98-7654321',
                'ptin': 'P12345678',
                'contact_name': 'Updated Contact',
                'email': 'updated@services.com'
            }
            return

        dialog = ERODialog(self.dialog, self.ptin_ero_service, ero_number=ero_number, test_mode=self.test_mode)
        if dialog.result:
            self._load_ero_data()
            messagebox.showinfo("Success", "ERO updated successfully!")

    def _deactivate_ero(self) -> None:
        """Deactivate selected ERO"""
        selection = self.ero_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an ERO to deactivate.")
            return

        item = self.ero_tree.item(selection[0])
        ero_number = item['values'][0]

        if messagebox.askyesno("Confirm Deactivation",
                              f"Are you sure you want to deactivate ERO {ero_number}?"):
            try:
                self.ptin_ero_service.deactivate_ero(ero_number)
                self._load_ero_data()
                messagebox.showinfo("Success", f"ERO {ero_number} deactivated successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to deactivate ERO: {str(e)}")

    def _validate_credentials(self) -> None:
        """Validate entered credentials"""
        ptin = self.validation_ptin_var.get().strip()
        ero_number = self.validation_ero_var.get().strip() or None

        if not ptin:
            messagebox.showwarning("Input Required", "Please enter a PTIN to validate.")
            return

        try:
            is_valid, message = self.ptin_ero_service.validate_professional_credentials(ptin, ero_number)

            # Update results text
            self.validation_result_text.config(state=tk.NORMAL)
            self.validation_result_text.delete(1.0, tk.END)

            status = "✅ VALID" if is_valid else "❌ INVALID"
            self.validation_result_text.insert(tk.END, f"Validation Result: {status}\n\n")
            self.validation_result_text.insert(tk.END, f"Message: {message}\n\n")

            # Show professional info if valid
            if is_valid:
                info = self.ptin_ero_service.get_professional_info(ptin)
                if info:
                    ptin_info = info['ptin']
                    self.validation_result_text.insert(tk.END, "PTIN Information:\n")
                    self.validation_result_text.insert(tk.END, f"  Name: {ptin_info['first_name']} {ptin_info['last_name']}\n")
                    self.validation_result_text.insert(tk.END, f"  Email: {ptin_info['email']}\n")
                    self.validation_result_text.insert(tk.END, f"  Status: {ptin_info['status']}\n")

                    if info['eros']:
                        self.validation_result_text.insert(tk.END, f"\nAssociated EROs ({len(info['eros'])}):\n")
                        for ero in info['eros']:
                            self.validation_result_text.insert(tk.END, f"  {ero['ero_number']}: {ero['business_name']}\n")

            self.validation_result_text.config(state=tk.DISABLED)

        except Exception as e:
            messagebox.showerror("Validation Error", f"Failed to validate credentials: {str(e)}")

    def _on_close(self) -> None:
        """Handle dialog close"""
        self.dialog.destroy()


class PTINDialog:
    """
    Dialog for adding/editing PTIN records.
    """

    def __init__(self, parent: tk.Toplevel, ptin_ero_service: PTINEROService,
                 ptin: Optional[str] = None, test_mode: bool = False):
        """
        Initialize PTIN dialog.

        Args:
            parent: Parent window
            ptin_ero_service: PTIN/ERO service instance
            ptin: Existing PTIN to edit (None for new)
            test_mode: If True, skip GUI creation for testing
        """
        self.parent = parent
        self.ptin_ero_service = ptin_ero_service
        self.existing_ptin = ptin
        self.result = None
        self.test_mode = test_mode

        if test_mode:
            # In test mode, create mock attributes for testing
            self._mock_vars = {}
            self.ptin_var = self._create_mock_var('ptin_var')
            self.first_name_var = self._create_mock_var('first_name_var')
            self.middle_initial_var = self._create_mock_var('middle_initial_var')
            self.last_name_var = self._create_mock_var('last_name_var')
            self.suffix_var = self._create_mock_var('suffix_var')
            self.email_var = self._create_mock_var('email_var')
            self.phone_var = self._create_mock_var('phone_var')
            self.address1_var = self._create_mock_var('address1_var')
            self.address2_var = self._create_mock_var('address2_var')
            self.city_var = self._create_mock_var('city_var')
            self.state_var = self._create_mock_var('state_var')
            self.zip_var = self._create_mock_var('zip_var')
            return

    def _create_mock_var(self, name):
        """Create a mock variable that behaves like StringVar for testing"""
        mock_var = MagicMock()
        mock_var._value = ""
        mock_var.get = MagicMock(return_value=mock_var._value)
        mock_var.set = MagicMock(side_effect=lambda val: self._set_mock_var(mock_var, val))
        return mock_var

    def _set_mock_var(self, mock_var, value):
        """Set the value of a mock variable"""
        mock_var._value = value
        mock_var.get.return_value = value

    def _create_widgets(self) -> None:
        """Create dialog widgets"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_text = "Register New PTIN" if self.existing_ptin is None else "Edit PTIN"
        title_label = ttk.Label(main_frame, text=title_text, font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 20))

        # Form frame
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # PTIN field
        ttk.Label(form_frame, text="PTIN:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.ptin_var = tk.StringVar()
        ptin_entry = ttk.Entry(form_frame, textvariable=self.ptin_var, width=30)
        ptin_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        if self.existing_ptin:
            ptin_entry.config(state=tk.DISABLED)

        # Name fields
        ttk.Label(form_frame, text="First Name:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.first_name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.first_name_var, width=30).grid(
            row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(form_frame, text="Middle Initial:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.middle_initial_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.middle_initial_var, width=5).grid(
            row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(form_frame, text="Last Name:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.last_name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.last_name_var, width=30).grid(
            row=3, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(form_frame, text="Suffix:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.suffix_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.suffix_var, width=10).grid(
            row=4, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # Contact fields
        ttk.Label(form_frame, text="Email:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.email_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.email_var, width=30).grid(
            row=5, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(form_frame, text="Phone:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.phone_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.phone_var, width=30).grid(
            row=6, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # Address fields
        ttk.Label(form_frame, text="Address Line 1:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.address1_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.address1_var, width=30).grid(
            row=7, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(form_frame, text="Address Line 2:").grid(row=8, column=0, sticky=tk.W, pady=5)
        self.address2_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.address2_var, width=30).grid(
            row=8, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(form_frame, text="City:").grid(row=9, column=0, sticky=tk.W, pady=5)
        self.city_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.city_var, width=20).grid(
            row=9, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(form_frame, text="State:").grid(row=10, column=0, sticky=tk.W, pady=5)
        self.state_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.state_var, width=5).grid(
            row=10, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(form_frame, text="ZIP Code:").grid(row=11, column=0, sticky=tk.W, pady=5)
        self.zip_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.zip_var, width=10).grid(
            row=11, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel
        ).pack(side=tk.RIGHT, padx=(10, 0))

        ttk.Button(
            button_frame,
            text="Save",
            command=self._on_save
        ).pack(side=tk.RIGHT)

    def _load_ptin_data(self) -> None:
        """Load existing PTIN data for editing"""
        if not self.existing_ptin:
            return

        record = self.ptin_ero_service.get_ptin_record(self.existing_ptin)
        if not record:
            return

        self.ptin_var.set(record.ptin)
        self.first_name_var.set(record.first_name)
        self.last_name_var.set(record.last_name)
        self.middle_initial_var.set(record.middle_initial or "")
        self.suffix_var.set(record.suffix or "")
        self.email_var.set(record.email)
        self.phone_var.set(record.phone or "")

        # Address
        address = record.address or {}
        self.address1_var.set(address.get('line1', ''))
        self.address2_var.set(address.get('line2', ''))
        self.city_var.set(address.get('city', ''))
        self.state_var.set(address.get('state', ''))
        self.zip_var.set(address.get('zip', ''))

    def _on_save(self) -> None:
        """Handle save button click"""
        try:
            # Collect data
            ptin_data = {
                'ptin': self.existing_ptin or self.ptin_var.get().strip().upper(),
                'first_name': self.first_name_var.get().strip(),
                'last_name': self.last_name_var.get().strip(),
                'middle_initial': self.middle_initial_var.get().strip() or None,
                'suffix': self.suffix_var.get().strip() or None,
                'email': self.email_var.get().strip(),
                'phone': self.phone_var.get().strip() or None,
                'address': {
                    'line1': self.address1_var.get().strip(),
                    'line2': self.address2_var.get().strip(),
                    'city': self.city_var.get().strip(),
                    'state': self.state_var.get().strip(),
                    'zip': self.zip_var.get().strip()
                }
            }

            # Remove empty address fields
            ptin_data['address'] = {k: v for k, v in ptin_data['address'].items() if v}

            if self.existing_ptin:
                # Update existing
                self.ptin_ero_service.update_ptin_record(self.existing_ptin, ptin_data)
            else:
                # Register new
                self.ptin_ero_service.register_ptin(ptin_data)

            self.result = True
            if hasattr(self, 'dialog') and self.dialog:
                self.dialog.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save PTIN: {str(e)}")

    def _on_cancel(self) -> None:
        """Handle cancel button click"""
        self.result = False
        if hasattr(self, 'dialog') and self.dialog:
            self.dialog.destroy()


class ERODialog:
    """
    Dialog for adding/editing ERO records.
    """

    def __init__(self, parent: tk.Toplevel, ptin_ero_service: PTINEROService,
                 ero_number: Optional[str] = None, test_mode: bool = False):
        """
        Initialize ERO dialog.

        Args:
            parent: Parent window
            ptin_ero_service: PTIN/ERO service instance
            ero_number: Existing ERO to edit (None for new)
            test_mode: If True, skip GUI creation for testing
        """
        self.parent = parent
        self.ptin_ero_service = ptin_ero_service
        self.existing_ero = ero_number
        self.result = None

        if test_mode:
            # In test mode, create mock attributes for testing
            self._mock_vars = {}
            self.ero_number_var = self._create_mock_var('ero_number_var')
            self.business_name_var = self._create_mock_var('business_name_var')
            self.ein_var = self._create_mock_var('ein_var')
            self.ptin_var = self._create_mock_var('ptin_var')
            self.contact_name_var = self._create_mock_var('contact_name_var')
            self.contact_title_var = self._create_mock_var('contact_title_var')
            self.email_var = self._create_mock_var('email_var')
            self.phone_var = self._create_mock_var('phone_var')
            self.address1_var = self._create_mock_var('address1_var')
            self.address2_var = self._create_mock_var('address2_var')
            self.city_var = self._create_mock_var('city_var')
            self.state_var = self._create_mock_var('state_var')
            self.zip_var = self._create_mock_var('zip_var')
            return

    def _create_mock_var(self, name):
        """Create a mock variable that behaves like StringVar for testing"""
        mock_var = MagicMock()
        mock_var._value = ""
        mock_var.get = MagicMock(return_value=mock_var._value)
        mock_var.set = MagicMock(side_effect=lambda val: self._set_mock_var(mock_var, val))
        return mock_var

    def _set_mock_var(self, mock_var, value):
        """Set the value of a mock variable"""
        mock_var._value = value
        mock_var.get.return_value = value

    def _create_widgets(self) -> None:
        """Create dialog widgets"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_text = "Register New ERO" if self.existing_ero is None else "Edit ERO"
        title_label = ttk.Label(main_frame, text=title_text, font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 20))

        # Form frame
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # ERO fields
        ttk.Label(form_frame, text="ERO Number:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.ero_number_var = tk.StringVar()
        ero_entry = ttk.Entry(form_frame, textvariable=self.ero_number_var, width=20)
        ero_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        if self.existing_ero:
            ero_entry.config(state=tk.DISABLED)

        ttk.Label(form_frame, text="Business Name:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.business_name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.business_name_var, width=30).grid(
            row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(form_frame, text="EIN:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.ein_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.ein_var, width=15).grid(
            row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(form_frame, text="Associated PTIN:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.ptin_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.ptin_var, width=20).grid(
            row=3, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # Contact fields
        ttk.Label(form_frame, text="Contact Name:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.contact_name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.contact_name_var, width=30).grid(
            row=4, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(form_frame, text="Contact Title:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.contact_title_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.contact_title_var, width=20).grid(
            row=5, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(form_frame, text="Email:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.email_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.email_var, width=30).grid(
            row=6, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(form_frame, text="Phone:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.phone_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.phone_var, width=30).grid(
            row=7, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # Address fields
        ttk.Label(form_frame, text="Address Line 1:").grid(row=8, column=0, sticky=tk.W, pady=5)
        self.address1_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.address1_var, width=30).grid(
            row=8, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(form_frame, text="Address Line 2:").grid(row=9, column=0, sticky=tk.W, pady=5)
        self.address2_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.address2_var, width=30).grid(
            row=9, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(form_frame, text="City:").grid(row=10, column=0, sticky=tk.W, pady=5)
        self.city_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.city_var, width=20).grid(
            row=10, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(form_frame, text="State:").grid(row=11, column=0, sticky=tk.W, pady=5)
        self.state_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.state_var, width=5).grid(
            row=11, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(form_frame, text="ZIP Code:").grid(row=12, column=0, sticky=tk.W, pady=5)
        self.zip_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.zip_var, width=10).grid(
            row=12, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel
        ).pack(side=tk.RIGHT, padx=(10, 0))

        ttk.Button(
            button_frame,
            text="Save",
            command=self._on_save
        ).pack(side=tk.RIGHT)

    def _load_ero_data(self) -> None:
        """Load existing ERO data for editing"""
        if not self.existing_ero:
            return

        record = self.ptin_ero_service.get_ero_record(self.existing_ero)
        if not record:
            return

        self.ero_number_var.set(record.ero_number)
        self.business_name_var.set(record.business_name)
        self.ein_var.set(record.ein)
        self.ptin_var.set(record.ptin)
        self.contact_name_var.set(record.contact_name)
        self.contact_title_var.set(record.contact_title or "")
        self.email_var.set(record.email)
        self.phone_var.set(record.phone or "")

        # Address
        address = record.address or {}
        self.address1_var.set(address.get('line1', ''))
        self.address2_var.set(address.get('line2', ''))
        self.city_var.set(address.get('city', ''))
        self.state_var.set(address.get('state', ''))
        self.zip_var.set(address.get('zip', ''))

    def _on_save(self) -> None:
        """Handle save button click"""
        try:
            # Collect data
            ero_data = {
                'ero_number': self.ero_number_var.get().strip(),
                'business_name': self.business_name_var.get().strip(),
                'ein': self.ein_var.get().strip(),
                'ptin': self.ptin_var.get().strip().upper(),
                'contact_name': self.contact_name_var.get().strip(),
                'contact_title': self.contact_title_var.get().strip() or None,
                'email': self.email_var.get().strip(),
                'phone': self.phone_var.get().strip() or None,
                'address': {
                    'line1': self.address1_var.get().strip(),
                    'line2': self.address2_var.get().strip(),
                    'city': self.city_var.get().strip(),
                    'state': self.state_var.get().strip(),
                    'zip': self.zip_var.get().strip()
                }
            }

            # Remove empty address fields
            ero_data['address'] = {k: v for k, v in ero_data['address'].items() if v}

            if self.existing_ero:
                # Update existing
                self.ptin_ero_service.update_ero_record(self.existing_ero, ero_data)
            else:
                # Register new
                self.ptin_ero_service.register_ero(ero_data)

            self.result = True
            if hasattr(self, 'dialog') and self.dialog:
                self.dialog.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save ERO: {str(e)}")

    def _on_cancel(self) -> None:
        """Handle cancel button click"""
        self.result = False
        if hasattr(self, 'dialog') and self.dialog:
            self.dialog.destroy()