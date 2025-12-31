"""
Client Login Dialog - Secure authentication for client portal access

Provides a login interface for clients to access their secure tax portal.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
import logging

from services.authentication_service import AuthenticationService
from gui.client_portal_window import ClientPortalWindow
from config.dependencies import get_container

logger = logging.getLogger(__name__)


class ClientLoginDialog:
    """
    Dialog for client authentication to access the client portal.
    """

    def __init__(self, parent: tk.Tk, on_successful_login: Optional[Callable] = None):
        """
        Initialize client login dialog.

        Args:
            parent: Parent window
            on_successful_login: Callback function called after successful login
        """
        self.parent = parent
        self.on_successful_login = on_successful_login
        self.container = get_container()
        self.auth_service: AuthenticationService = self.container.get_authentication_service()

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Client Portal Login")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets()

        # Center the dialog
        self.dialog.geometry("+{}+{}".format(
            parent.winfo_rootx() + 100,
            parent.winfo_rooty() + 100
        ))

        # Set focus
        self.dialog.focus_set()

    def _create_widgets(self) -> None:
        """Create dialog widgets"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Client Portal Login",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 20))

        # Login form
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.X, pady=(0, 20))

        # Email field
        ttk.Label(form_frame, text="Email:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.email_var = tk.StringVar()
        email_entry = ttk.Entry(form_frame, textvariable=self.email_var, width=30)
        email_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        email_entry.focus()

        # Password field
        ttk.Label(form_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(form_frame, textvariable=self.password_var, show="*", width=30)
        password_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # 2FA code field (initially hidden)
        self.twofa_frame = ttk.Frame(form_frame)
        ttk.Label(self.twofa_frame, text="2FA Code:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.twofa_var = tk.StringVar()
        twofa_entry = ttk.Entry(self.twofa_frame, textvariable=self.twofa_var, width=10)
        twofa_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # Remember me checkbox
        self.remember_var = tk.BooleanVar()
        ttk.Checkbutton(
            form_frame,
            text="Remember me",
            variable=self.remember_var
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT, padx=(5, 0))

        self.login_btn = ttk.Button(
            button_frame,
            text="Login",
            command=self._attempt_login
        )
        self.login_btn.pack(side=tk.RIGHT)

        # Forgot password link
        forgot_frame = ttk.Frame(main_frame)
        forgot_frame.pack(fill=tk.X, pady=(10, 0))

        forgot_link = ttk.Label(
            forgot_frame,
            text="Forgot your password?",
            foreground="blue",
            cursor="hand2"
        )
        forgot_link.pack(anchor=tk.CENTER)
        forgot_link.bind("<Button-1>", lambda e: self._forgot_password())

        # Bind Enter key
        self.dialog.bind("<Return>", lambda e: self._attempt_login())

    def _attempt_login(self) -> None:
        """Attempt client login"""
        email = self.email_var.get().strip()
        password = self.password_var.get()
        twofa_code = self.twofa_var.get().strip() if self.twofa_frame.winfo_ismapped() else None

        # Basic validation
        if not email or not password:
            messagebox.showerror("Error", "Please enter both email and password.")
            return

        if "@" not in email:
            messagebox.showerror("Error", "Please enter a valid email address.")
            return

        # Disable login button during attempt
        self.login_btn.config(state=tk.DISABLED, text="Logging in...")

        try:
            # Attempt authentication
            result = self.auth_service.authenticate_client(email, password, twofa_code)

            if result['success']:
                client_info = result['client_info']

                # Close login dialog
                self.dialog.destroy()

                # Open client portal
                portal = ClientPortalWindow(
                    self.parent,
                    client_info['id'],
                    client_info['name']
                )

                # Call success callback if provided
                if self.on_successful_login:
                    self.on_successful_login(client_info)

            else:
                error_msg = result.get('error', 'Login failed')

                # Check if 2FA is required
                if result.get('requires_2fa'):
                    # Show 2FA input field
                    self.twofa_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
                    self.twofa_var.set("")
                    self.login_btn.config(state=tk.NORMAL, text="Login")
                    messagebox.showinfo("2FA Required", "Please enter your two-factor authentication code.")
                    return

                # Show error message
                messagebox.showerror("Login Failed", error_msg)
                self.login_btn.config(state=tk.NORMAL, text="Login")

        except Exception as e:
            logger.error(f"Login error: {e}")
            messagebox.showerror("Error", f"Login failed: {str(e)}")
            self.login_btn.config(state=tk.NORMAL, text="Login")

    def _forgot_password(self) -> None:
        """Handle forgot password"""
        # In a real implementation, this would open a password reset dialog
        messagebox.showinfo("Forgot Password", "Password reset functionality coming soon!\n\nPlease contact your tax preparer for assistance.")