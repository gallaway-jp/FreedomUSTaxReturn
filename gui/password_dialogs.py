"""
Password Protection Dialog - GUI for authentication and password management

Provides dialogs for setting master password, authentication, and password changes.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional

from services.authentication_service import AuthenticationError, PasswordPolicyError


class PasswordDialog:
    """
    Base class for password-related dialogs.

    Provides common functionality for password input and validation.
    """

    def __init__(self, parent: tk.Toplevel, title: str, auth_service):
        """
        Initialize password dialog.

        Args:
            parent: Parent window
            title: Dialog title
            auth_service: Authentication service instance
        """
        self.parent = parent
        self.auth_service = auth_service
        self.result = None

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center dialog
        self.dialog.geometry("+{}+{}".format(
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))

        self._create_widgets()

    def _create_widgets(self):
        """Create dialog widgets - to be overridden by subclasses"""
        pass

    def show(self):
        """Show dialog and wait for result"""
        self.dialog.wait_window()
        return self.result


class SetMasterPasswordDialog(PasswordDialog):
    """
    Dialog for setting the initial master password.
    """

    def __init__(self, parent: tk.Toplevel, auth_service):
        super().__init__(parent, "Set Master Password", auth_service)

    def _create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Set Master Password",
                               font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))

        # Description
        desc_label = ttk.Label(main_frame,
                              text="Create a strong master password to protect your tax data.\n"
                                   "This password will be required to access the application.",
                              wraplength=350, justify=tk.LEFT)
        desc_label.pack(pady=(0, 20))

        # Password entry
        ttk.Label(main_frame, text="Password:").pack(anchor=tk.W)
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(main_frame, textvariable=self.password_var,
                                  show="*", width=30)
        password_entry.pack(pady=(0, 10), fill=tk.X)
        password_entry.focus()

        # Confirm password entry
        ttk.Label(main_frame, text="Confirm Password:").pack(anchor=tk.W)
        self.confirm_var = tk.StringVar()
        confirm_entry = ttk.Entry(main_frame, textvariable=self.confirm_var,
                                 show="*", width=30)
        confirm_entry.pack(pady=(0, 10), fill=tk.X)

        # Password requirements
        req_frame = ttk.LabelFrame(main_frame, text="Password Requirements", padding=10)
        req_frame.pack(fill=tk.X, pady=(0, 20))

        policy = self.auth_service.get_password_policy_requirements()
        requirements = []
        requirements.append(f"• At least {policy['min_length']} characters")
        if policy['require_uppercase']:
            requirements.append("• At least one uppercase letter")
        if policy['require_lowercase']:
            requirements.append("• At least one lowercase letter")
        if policy['require_digits']:
            requirements.append("• At least one number")
        if policy['require_special_chars']:
            requirements.append("• At least one special character (!@#$%^&*)")

        req_text = "\n".join(requirements)
        ttk.Label(req_frame, text=req_text, justify=tk.LEFT).pack(anchor=tk.W)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Set Password", command=self._set_password).pack(side=tk.RIGHT)

    def _set_password(self):
        """Set the master password"""
        password = self.password_var.get()
        confirm = self.confirm_var.get()

        if not password:
            messagebox.showerror("Error", "Please enter a password")
            return

        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match")
            return

        try:
            self.auth_service.create_master_password(password)
            self.result = True
            self.dialog.destroy()
        except PasswordPolicyError as e:
            messagebox.showerror("Password Policy Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set password: {e}")

    def _cancel(self):
        """Cancel password setting"""
        self.result = False
        self.dialog.destroy()


class AuthenticateDialog(PasswordDialog):
    """
    Dialog for authenticating with master password.
    """

    def __init__(self, parent: tk.Toplevel, auth_service):
        super().__init__(parent, "Authentication Required", auth_service)

    def _create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Enter Master Password",
                               font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))

        # Description
        desc_label = ttk.Label(main_frame,
                              text="Enter your master password to access the application.",
                              wraplength=350, justify=tk.LEFT)
        desc_label.pack(pady=(0, 20))

        # Password entry
        ttk.Label(main_frame, text="Master Password:").pack(anchor=tk.W)
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(main_frame, textvariable=self.password_var,
                                  show="*", width=30)
        password_entry.pack(pady=(0, 10), fill=tk.X)
        password_entry.focus()

        # Bind Enter key
        password_entry.bind("<Return>", lambda e: self._authenticate())

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Login", command=self._authenticate).pack(side=tk.RIGHT)

    def _authenticate(self):
        """Authenticate with password"""
        password = self.password_var.get()

        if not password:
            messagebox.showerror("Error", "Please enter your password")
            return

        try:
            session_token = self.auth_service.authenticate_master_password(password)
            self.result = session_token
            self.dialog.destroy()
        except AuthenticationError as e:
            messagebox.showerror("Authentication Failed", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Authentication error: {e}")

    def _cancel(self):
        """Cancel authentication"""
        self.result = None
        self.dialog.destroy()


class ChangePasswordDialog(PasswordDialog):
    """
    Dialog for changing the master password.
    """

    def __init__(self, parent: tk.Toplevel, auth_service):
        super().__init__(parent, "Change Master Password", auth_service)

    def _create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Change Master Password",
                               font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))

        # Current password
        ttk.Label(main_frame, text="Current Password:").pack(anchor=tk.W)
        self.current_var = tk.StringVar()
        current_entry = ttk.Entry(main_frame, textvariable=self.current_var,
                                 show="*", width=30)
        current_entry.pack(pady=(0, 10), fill=tk.X)
        current_entry.focus()

        # New password
        ttk.Label(main_frame, text="New Password:").pack(anchor=tk.W)
        self.new_var = tk.StringVar()
        new_entry = ttk.Entry(main_frame, textvariable=self.new_var, show="*", width=30)
        new_entry.pack(pady=(0, 10), fill=tk.X)

        # Confirm new password
        ttk.Label(main_frame, text="Confirm New Password:").pack(anchor=tk.W)
        self.confirm_var = tk.StringVar()
        confirm_entry = ttk.Entry(main_frame, textvariable=self.confirm_var,
                                 show="*", width=30)
        confirm_entry.pack(pady=(0, 10), fill=tk.X)

        # Password requirements
        req_frame = ttk.LabelFrame(main_frame, text="Password Requirements", padding=10)
        req_frame.pack(fill=tk.X, pady=(0, 20))

        policy = self.auth_service.get_password_policy_requirements()
        requirements = []
        requirements.append(f"• At least {policy['min_length']} characters")
        if policy['require_uppercase']:
            requirements.append("• At least one uppercase letter")
        if policy['require_lowercase']:
            requirements.append("• At least one lowercase letter")
        if policy['require_digits']:
            requirements.append("• At least one number")
        if policy['require_special_chars']:
            requirements.append("• At least one special character (!@#$%^&*)")

        req_text = "\n".join(requirements)
        ttk.Label(req_frame, text=req_text, justify=tk.LEFT).pack(anchor=tk.W)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Change Password", command=self._change_password).pack(side=tk.RIGHT)

    def _change_password(self):
        """Change the master password"""
        current = self.current_var.get()
        new = self.new_var.get()
        confirm = self.confirm_var.get()

        if not current or not new:
            messagebox.showerror("Error", "Please fill in all fields")
            return

        if new != confirm:
            messagebox.showerror("Error", "New passwords do not match")
            return

        try:
            self.auth_service.change_master_password(current, new)
            messagebox.showinfo("Success", "Password changed successfully")
            self.result = True
            self.dialog.destroy()
        except AuthenticationError as e:
            messagebox.showerror("Authentication Failed", str(e))
        except PasswordPolicyError as e:
            messagebox.showerror("Password Policy Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to change password: {e}")

    def _cancel(self):
        """Cancel password change"""
        self.result = False
        self.dialog.destroy()</content>
<parameter name="filePath">d:\Development\Python\FreedomUSTaxReturn\gui\password_dialogs.py