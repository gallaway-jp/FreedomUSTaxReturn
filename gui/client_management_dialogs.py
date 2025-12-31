"""
Client Management Dialogs - GUI components for managing client accounts

Provides dialogs for creating, editing, and managing client accounts
in the tax preparation application.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Optional, Callable
from datetime import datetime

from services.authentication_service import AuthenticationService

logger = logging.getLogger(__name__)


class ClientManagementDialog:
    """
    Main dialog for managing client accounts.

    Allows tax professionals to view, create, edit, and manage client accounts.
    """

    def __init__(self, parent: tk.Tk, auth_service: AuthenticationService, session_token: str):
        """
        Initialize client management dialog.

        Args:
            parent: Parent window
            auth_service: Authentication service instance
            session_token: Valid session token
        """
        self.parent = parent
        self.auth_service = auth_service
        self.session_token = session_token

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Client Management")
        self.dialog.geometry("800x600")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets()
        self._load_clients()

        # Center the dialog
        self.dialog.geometry("+{}+{}".format(
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))

    def _create_widgets(self):
        """Create the dialog widgets"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Client Account Management",
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))

        # Toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(toolbar, text="Add Client", command=self._add_client).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Edit Client", command=self._edit_client).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Reset Password", command=self._reset_client_password).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Toggle 2FA", command=self._toggle_client_2fa).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Deactivate", command=self._deactivate_client).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Refresh", command=self._load_clients).pack(side=tk.RIGHT)

        # Client list
        list_frame = ttk.LabelFrame(main_frame, text="Client Accounts", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview for clients
        columns = ("Name", "Email", "SSN Last 4", "Status", "Last Login", "2FA")
        self.client_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)

        # Configure columns
        self.client_tree.heading("Name", text="Name")
        self.client_tree.heading("Email", text="Email")
        self.client_tree.heading("SSN Last 4", text="SSN Last 4")
        self.client_tree.heading("Status", text="Status")
        self.client_tree.heading("Last Login", text="Last Login")
        self.client_tree.heading("2FA", text="2FA")

        self.client_tree.column("Name", width=150)
        self.client_tree.column("Email", width=200)
        self.client_tree.column("SSN Last 4", width=80)
        self.client_tree.column("Status", width=80)
        self.client_tree.column("Last Login", width=120)
        self.client_tree.column("2FA", width=60)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.client_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.client_tree.xview)
        self.client_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.client_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="Close", command=self.dialog.destroy).pack(side=tk.RIGHT)

    def _load_clients(self):
        """Load and display client accounts"""
        # Clear existing items
        for item in self.client_tree.get_children():
            self.client_tree.delete(item)

        try:
            clients = self.auth_service.get_client_list(self.session_token)

            for client in clients:
                status = "Active" if client['is_active'] else "Inactive"
                last_login = "Never"
                if client['last_login']:
                    try:
                        dt = datetime.fromisoformat(client['last_login'])
                        last_login = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        last_login = client['last_login']

                two_fa = "Yes" if client['two_factor_enabled'] else "No"

                self.client_tree.insert("", tk.END, values=(
                    client['name'],
                    client['email'],
                    client['ssn_last4'],
                    status,
                    last_login,
                    two_fa
                ), tags=(client['id'],))

        except Exception as e:
            logger.error(f"Failed to load clients: {e}")
            messagebox.showerror("Error", f"Failed to load clients: {str(e)}")

    def _get_selected_client(self) -> Optional[str]:
        """Get the ID of the selected client"""
        selection = self.client_tree.selection()
        if not selection:
            return None

        item = selection[0]
        return self.client_tree.item(item, "tags")[0]

    def _add_client(self):
        """Open dialog to add a new client"""
        dialog = AddClientDialog(self.dialog, self.auth_service, self.session_token)
        if dialog.result:
            self._load_clients()

    def _edit_client(self):
        """Open dialog to edit selected client"""
        client_id = self._get_selected_client()
        if not client_id:
            messagebox.showwarning("No Selection", "Please select a client to edit.")
            return

        dialog = EditClientDialog(self.dialog, self.auth_service, self.session_token, client_id)
        if dialog.result:
            self._load_clients()

    def _reset_client_password(self):
        """Reset password for selected client"""
        client_id = self._get_selected_client()
        if not client_id:
            messagebox.showwarning("No Selection", "Please select a client.")
            return

        if messagebox.askyesno("Confirm", "Reset this client's password? They will need to set a new one."):
            try:
                # Generate a temporary password
                temp_password = "TempPass123!"  # In production, generate secure random password
                self.auth_service.change_client_password(self.session_token, client_id, temp_password)

                messagebox.showinfo("Success",
                    f"Password reset successfully. Temporary password: {temp_password}\n"
                    "Please provide this to the client and have them change it immediately.")
                self._load_clients()

            except Exception as e:
                logger.error(f"Failed to reset password: {e}")
                messagebox.showerror("Error", f"Failed to reset password: {str(e)}")

    def _toggle_client_2fa(self):
        """Toggle 2FA for selected client"""
        client_id = self._get_selected_client()
        if not client_id:
            messagebox.showwarning("No Selection", "Please select a client.")
            return

        # Check current 2FA status
        try:
            clients = self.auth_service.get_client_list(self.session_token)
            client = next((c for c in clients if c['id'] == client_id), None)
            if not client:
                return

            if client['two_factor_enabled']:
                # Disable 2FA
                if messagebox.askyesno("Confirm", "Disable 2FA for this client?"):
                    self.auth_service.disable_client_2fa(self.session_token, client_id)
                    messagebox.showinfo("Success", "2FA disabled for client.")
            else:
                # Enable 2FA - show setup dialog
                dialog = ClientTwoFactorSetupDialog(self.dialog, self.auth_service, self.session_token, client_id)
                if dialog.result:
                    messagebox.showinfo("Success", "2FA enabled for client.")

            self._load_clients()

        except Exception as e:
            logger.error(f"Failed to toggle 2FA: {e}")
            messagebox.showerror("Error", f"Failed to toggle 2FA: {str(e)}")

    def _deactivate_client(self):
        """Deactivate selected client"""
        client_id = self._get_selected_client()
        if not client_id:
            messagebox.showwarning("No Selection", "Please select a client.")
            return

        try:
            clients = self.auth_service.get_client_list(self.session_token)
            client = next((c for c in clients if c['id'] == client_id), None)
            if not client:
                return

            action = "deactivate" if client['is_active'] else "activate"
            if messagebox.askyesno("Confirm", f"{action.capitalize()} this client account?"):
                if client['is_active']:
                    self.auth_service.deactivate_client(self.session_token, client_id)
                else:
                    self.auth_service.activate_client(self.session_token, client_id)

                self._load_clients()

        except Exception as e:
            logger.error(f"Failed to change client status: {e}")
            messagebox.showerror("Error", f"Failed to change client status: {str(e)}")


class AddClientDialog:
    """
    Dialog for adding a new client account.
    """

    def __init__(self, parent: tk.Toplevel, auth_service: AuthenticationService, session_token: str):
        """
        Initialize add client dialog.

        Args:
            parent: Parent window
            auth_service: Authentication service instance
            session_token: Valid session token
        """
        self.parent = parent
        self.auth_service = auth_service
        self.session_token = session_token
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add New Client")
        self.dialog.geometry("400x350")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets()

        # Center the dialog
        self.dialog.geometry("+{}+{}".format(
            parent.winfo_rootx() + 100,
            parent.winfo_rooty() + 100
        ))

    def _create_widgets(self):
        """Create the dialog widgets"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Add New Client", font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 20))

        # Form fields
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.X, pady=(0, 20))

        # Name
        ttk.Label(form_frame, text="Full Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.name_var, width=30).grid(row=0, column=1, pady=5, padx=(10, 0))

        # Email
        ttk.Label(form_frame, text="Email:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.email_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.email_var, width=30).grid(row=1, column=1, pady=5, padx=(10, 0))

        # SSN Last 4
        ttk.Label(form_frame, text="SSN Last 4:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.ssn_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.ssn_var, width=10).grid(row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # Password
        ttk.Label(form_frame, text="Password:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.password_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.password_var, show="*", width=30).grid(row=3, column=1, pady=5, padx=(10, 0))

        # Confirm Password
        ttk.Label(form_frame, text="Confirm Password:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.confirm_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.confirm_var, show="*", width=30).grid(row=4, column=1, pady=5, padx=(10, 0))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Create Client", command=self._create_client).pack(side=tk.RIGHT)

    def _create_client(self):
        """Create the new client account"""
        name = self.name_var.get().strip()
        email = self.email_var.get().strip()
        ssn = self.ssn_var.get().strip()
        password = self.password_var.get()
        confirm = self.confirm_var.get()

        # Validation
        if not name:
            messagebox.showerror("Error", "Please enter the client's full name.")
            return

        if not email or "@" not in email:
            messagebox.showerror("Error", "Please enter a valid email address.")
            return

        if not ssn or len(ssn) != 4 or not ssn.isdigit():
            messagebox.showerror("Error", "Please enter the last 4 digits of the SSN.")
            return

        if not password:
            messagebox.showerror("Error", "Please enter a password.")
            return

        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match.")
            return

        try:
            client_id = self.auth_service.create_client_account(
                self.session_token, name, email, ssn, password
            )

            messagebox.showinfo("Success", f"Client account created successfully!\nClient ID: {client_id}")
            self.result = True
            self.dialog.destroy()

        except Exception as e:
            logger.error(f"Failed to create client: {e}")
            messagebox.showerror("Error", f"Failed to create client: {str(e)}")


class EditClientDialog:
    """
    Dialog for editing an existing client account.
    """

    def __init__(self, parent: tk.Toplevel, auth_service: AuthenticationService,
                 session_token: str, client_id: str):
        """
        Initialize edit client dialog.

        Args:
            parent: Parent window
            auth_service: Authentication service instance
            session_token: Valid session token
            client_id: ID of client to edit
        """
        self.parent = parent
        self.auth_service = auth_service
        self.session_token = session_token
        self.client_id = client_id
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Client")
        self.dialog.geometry("400x250")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._load_client_data()
        self._create_widgets()

        # Center the dialog
        self.dialog.geometry("+{}+{}".format(
            parent.winfo_rootx() + 100,
            parent.winfo_rooty() + 100
        ))

    def _load_client_data(self):
        """Load existing client data"""
        try:
            clients = self.auth_service.get_client_list(self.session_token)
            self.client_data = next((c for c in clients if c['id'] == self.client_id), None)
            if not self.client_data:
                raise ValueError("Client not found")
        except Exception as e:
            logger.error(f"Failed to load client data: {e}")
            messagebox.showerror("Error", f"Failed to load client data: {str(e)}")
            self.dialog.destroy()

    def _create_widgets(self):
        """Create the dialog widgets"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Edit Client Information", font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 20))

        # Form fields
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.X, pady=(0, 20))

        # Name
        ttk.Label(form_frame, text="Full Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar(value=self.client_data['name'])
        ttk.Entry(form_frame, textvariable=self.name_var, width=30).grid(row=0, column=1, pady=5, padx=(10, 0))

        # Email
        ttk.Label(form_frame, text="Email:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.email_var = tk.StringVar(value=self.client_data['email'])
        ttk.Entry(form_frame, textvariable=self.email_var, width=30).grid(row=1, column=1, pady=5, padx=(10, 0))

        # SSN Last 4 (read-only)
        ttk.Label(form_frame, text="SSN Last 4:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Label(form_frame, text=self.client_data['ssn_last4']).grid(row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Update", command=self._update_client).pack(side=tk.RIGHT)

    def _update_client(self):
        """Update the client information"""
        name = self.name_var.get().strip()
        email = self.email_var.get().strip()

        # Validation
        if not name:
            messagebox.showerror("Error", "Please enter the client's full name.")
            return

        if not email or "@" not in email:
            messagebox.showerror("Error", "Please enter a valid email address.")
            return

        try:
            self.auth_service.update_client_info(self.session_token, self.client_id, name, email)
            messagebox.showinfo("Success", "Client information updated successfully!")
            self.result = True
            self.dialog.destroy()

        except Exception as e:
            logger.error(f"Failed to update client: {e}")
            messagebox.showerror("Error", f"Failed to update client: {str(e)}")


class ClientTwoFactorSetupDialog:
    """
    Dialog for setting up 2FA for a client account.
    """

    def __init__(self, parent: tk.Toplevel, auth_service: AuthenticationService,
                 session_token: str, client_id: str):
        """
        Initialize 2FA setup dialog for client.

        Args:
            parent: Parent window
            auth_service: Authentication service instance
            session_token: Valid session token
            client_id: ID of client to setup 2FA for
        """
        self.parent = parent
        self.auth_service = auth_service
        self.session_token = session_token
        self.client_id = client_id
        self.result = None
        self.secret = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Setup 2FA for Client")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets()
        self._generate_qr_code()

        # Center the dialog
        self.dialog.geometry("+{}+{}".format(
            parent.winfo_rootx() + 100,
            parent.winfo_rooty() + 100
        ))

    def _create_widgets(self):
        """Create the dialog widgets"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Setup Two-Factor Authentication", font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))

        # Instructions
        instructions = (
            "1. Install an authenticator app (Google Authenticator, Authy, etc.)\n"
            "2. Scan the QR code below with your authenticator app\n"
            "3. Enter the 6-digit code from your authenticator app\n"
            "4. Click 'Enable 2FA' to complete setup"
        )
        ttk.Label(main_frame, text=instructions, justify=tk.LEFT).pack(pady=(0, 15))

        # QR Code frame
        qr_frame = ttk.LabelFrame(main_frame, text="QR Code", padding="10")
        qr_frame.pack(pady=(0, 15))

        self.qr_label = ttk.Label(qr_frame, text="Generating QR code...")
        self.qr_label.pack()

        # Manual entry
        manual_frame = ttk.Frame(main_frame)
        manual_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(manual_frame, text="Or enter this secret manually:").pack(anchor=tk.W)
        self.secret_var = tk.StringVar()
        secret_entry = ttk.Entry(manual_frame, textvariable=self.secret_var, state="readonly", width=50)
        secret_entry.pack(fill=tk.X, pady=(5, 0))

        # Verification code
        code_frame = ttk.Frame(main_frame)
        code_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(code_frame, text="Verification Code:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.code_var = tk.StringVar()
        ttk.Entry(code_frame, textvariable=self.code_var, width=10).grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Enable 2FA", command=self._enable_2fa).pack(side=tk.RIGHT)

    def _generate_qr_code(self):
        """Generate and display QR code"""
        try:
            setup_info = self.auth_service.get_client_2fa_setup_info(self.session_token, self.client_id)
            self.secret = setup_info['secret']
            self.secret_var.set(self.secret)

            # Generate QR code image
            import qrcode
            from PIL import Image, ImageTk
            import io

            qr = qrcode.QRCode(version=1, box_size=5, border=2)
            qr.add_data(setup_info['uri'])
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            img = img.resize((150, 150), Image.Resampling.LANCZOS)

            # Convert to PhotoImage
            bio = io.BytesIO()
            img.save(bio, format="PNG")
            bio.seek(0)
            self.qr_image = ImageTk.PhotoImage(Image.open(bio))

            self.qr_label.config(image=self.qr_image, text="")

        except Exception as e:
            logger.error(f"Failed to generate QR code: {e}")
            self.qr_label.config(text="Failed to generate QR code")

    def _enable_2fa(self):
        """Enable 2FA for the client"""
        code = self.code_var.get().strip()

        if not code or len(code) != 6 or not code.isdigit():
            messagebox.showerror("Error", "Please enter a valid 6-digit verification code.")
            return

        try:
            success = self.auth_service.enable_client_2fa(self.session_token, self.client_id, self.secret, code)

            if success:
                messagebox.showinfo("Success", "Two-factor authentication enabled successfully!")
                self.result = True
                self.dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to verify the code. Please try again.")

        except Exception as e:
            logger.error(f"Failed to enable 2FA: {e}")
            messagebox.showerror("Error", f"Failed to enable 2FA: {str(e)}")