"""
Two-Factor Authentication Dialogs - GUI for 2FA setup and management

Provides dialogs for enabling/disabling 2FA, entering verification codes,
and managing backup codes.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
import qrcode
from PIL import Image, ImageTk
import io

from services.authentication_service import AuthenticationError


class TwoFactorSetupDialog:
    """
    Dialog for setting up Two-Factor Authentication.

    Shows QR code and allows user to enter verification code.
    """

    def __init__(self, parent: tk.Toplevel, auth_service, setup_info: dict):
        """
        Initialize 2FA setup dialog.

        Args:
            parent: Parent window
            auth_service: Authentication service instance
            setup_info: 2FA setup information from service
        """
        self.parent = parent
        self.auth_service = auth_service
        self.setup_info = setup_info
        self.result = None

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Enable Two-Factor Authentication")
        self.dialog.geometry("500x650")
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
        """Create dialog widgets"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Enable Two-Factor Authentication",
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))

        # Instructions
        instructions = (
            "1. Install an authenticator app (Google Authenticator, Authy, etc.)\n"
            "2. Scan the QR code below with your authenticator app\n"
            "3. Enter the 6-digit code from your app to verify setup"
        )
        instr_label = ttk.Label(main_frame, text=instructions, justify=tk.LEFT)
        instr_label.pack(pady=(0, 20))

        # QR Code frame
        qr_frame = ttk.LabelFrame(main_frame, text="QR Code", padding=10)
        qr_frame.pack(pady=(0, 20))

        # Generate and display QR code
        self._display_qr_code(qr_frame)

        # Manual entry option
        manual_frame = ttk.LabelFrame(main_frame, text="Manual Entry", padding=10)
        manual_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(manual_frame, text="If you can't scan the QR code, enter this key manually:").pack(anchor=tk.W)
        secret_label = ttk.Label(manual_frame, text=self.setup_info['secret'],
                                font=("Courier", 10), foreground="blue")
        secret_label.pack(pady=(5, 0))

        # Verification code entry
        code_frame = ttk.Frame(main_frame)
        code_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(code_frame, text="Verification Code:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.code_var = tk.StringVar()
        code_entry = ttk.Entry(code_frame, textvariable=self.code_var, width=10, font=("Arial", 14))
        code_entry.grid(row=0, column=1, sticky=tk.W)
        code_entry.focus()

        # Backup codes info
        backup_info = (
            "⚠️  Important: Save your backup codes!\n"
            "You'll receive 10 backup codes after setup.\n"
            "Store them securely - you can use them to access\n"
            "your account if you lose your authenticator device."
        )
        backup_label = ttk.Label(main_frame, text=backup_info, foreground="red", justify=tk.LEFT)
        backup_label.pack(pady=(0, 20))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="Enable 2FA", command=self._enable_2fa).pack(side=tk.RIGHT)

    def _display_qr_code(self, parent_frame):
        """Generate and display QR code"""
        try:
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=5, border=2)
            qr.add_data(self.setup_info['uri'])
            qr.make(fit=True)

            # Create image
            img = qr.make_image(fill_color="black", back_color="white")

            # Convert to PhotoImage
            # First convert PIL to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)

            # Create PhotoImage
            self.qr_image = ImageTk.PhotoImage(Image.open(img_bytes))

            # Display
            qr_label = ttk.Label(parent_frame, image=self.qr_image)
            qr_label.pack()

        except Exception as e:
            error_label = ttk.Label(parent_frame, text=f"Error generating QR code:\n{str(e)}",
                                   foreground="red")
            error_label.pack()

    def _enable_2fa(self):
        """Enable 2FA with verification code"""
        code = self.code_var.get().strip()

        if not code:
            messagebox.showerror("Error", "Please enter the verification code.")
            return

        if len(code) != 6 or not code.isdigit():
            messagebox.showerror("Error", "Verification code must be 6 digits.")
            return

        try:
            # This would need the session token in a real implementation
            # For now, we'll assume it's called from an authenticated context
            success = self.auth_service.enable_2fa("dummy_session", self.setup_info['secret'], code)

            if success:
                # Show backup codes
                backup_codes = self.setup_info['backup_codes']
                codes_text = "BACKUP CODES\n\n" + "\n".join(backup_codes) + "\n\n⚠️  SAVE THESE CODES SECURELY!\nYou can use them to access your account if you lose your device."

                messagebox.showinfo("2FA Enabled",
                                  "Two-Factor Authentication has been enabled!\n\n" + codes_text)

                self.result = True
                self.dialog.destroy()

        except AuthenticationError as e:
            messagebox.showerror("Error", str(e))

    def _cancel(self):
        """Cancel 2FA setup"""
        self.result = False
        self.dialog.destroy()

    def show(self):
        """Show dialog and wait for result"""
        self.dialog.wait_window()
        return self.result


class TwoFactorVerifyDialog:
    """
    Dialog for entering 2FA verification code during authentication.
    """

    def __init__(self, parent: tk.Toplevel, auth_service):
        """
        Initialize 2FA verification dialog.

        Args:
            parent: Parent window
            auth_service: Authentication service instance
        """
        self.parent = parent
        self.auth_service = auth_service
        self.result = None

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Two-Factor Authentication")
        self.dialog.geometry("350x200")
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
        """Create dialog widgets"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Enter Verification Code",
                               font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))

        # Instructions
        instr_label = ttk.Label(main_frame,
                               text="Enter the 6-digit code from your authenticator app:")
        instr_label.pack(pady=(0, 15))

        # Code entry
        entry_frame = ttk.Frame(main_frame)
        entry_frame.pack(pady=(0, 20))

        self.code_var = tk.StringVar()
        code_entry = ttk.Entry(entry_frame, textvariable=self.code_var,
                              width=8, font=("Arial", 16), justify=tk.CENTER)
        code_entry.pack()
        code_entry.focus()

        # Alternative option
        alt_label = ttk.Label(main_frame,
                             text="Or use a backup code",
                             font=("Arial", 8), foreground="blue")
        alt_label.pack()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="Verify", command=self._verify).pack(side=tk.RIGHT)

    def _verify(self):
        """Verify the entered code"""
        code = self.code_var.get().strip()

        if not code:
            messagebox.showerror("Error", "Please enter a verification code.")
            return

        try:
            if self.auth_service.verify_2fa_code(code):
                self.result = True
                self.dialog.destroy()
            else:
                messagebox.showerror("Error", "Invalid verification code.")
        except Exception as e:
            messagebox.showerror("Error", f"Verification failed: {str(e)}")

    def _cancel(self):
        """Cancel verification"""
        self.result = False
        self.dialog.destroy()

    def show(self):
        """Show dialog and wait for result"""
        self.dialog.wait_window()
        return self.result


class TwoFactorDisableDialog:
    """
    Dialog for disabling Two-Factor Authentication.
    """

    def __init__(self, parent: tk.Toplevel, auth_service):
        """
        Initialize 2FA disable dialog.

        Args:
            parent: Parent window
            auth_service: Authentication service instance
        """
        self.parent = parent
        self.auth_service = auth_service
        self.result = None

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Disable Two-Factor Authentication")
        self.dialog.geometry("400x250")
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
        """Create dialog widgets"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Warning icon and title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(pady=(0, 15))

        warning_label = ttk.Label(title_frame, text="⚠️", font=("Arial", 24), foreground="orange")
        warning_label.pack(side=tk.LEFT, padx=(0, 10))

        title_label = ttk.Label(title_frame, text="Disable Two-Factor Authentication",
                               font=("Arial", 12, "bold"))
        title_label.pack(side=tk.LEFT)

        # Warning message
        warning_text = (
            "Disabling 2FA will make your account less secure.\n"
            "You'll only need your password to access the application.\n\n"
            "Enter your password to confirm:"
        )
        warning_label = ttk.Label(main_frame, text=warning_text, justify=tk.LEFT)
        warning_label.pack(pady=(0, 15))

        # Password entry
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(main_frame, textvariable=self.password_var, show="*", width=30)
        password_entry.pack(pady=(0, 20))
        password_entry.focus()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="Disable 2FA", command=self._disable_2fa).pack(side=tk.RIGHT)

    def _disable_2fa(self):
        """Disable 2FA after password verification"""
        password = self.password_var.get()

        if not password:
            messagebox.showerror("Error", "Please enter your password.")
            return

        try:
            # This would need the session token in a real implementation
            success = self.auth_service.disable_2fa("dummy_session", password)

            if success:
                messagebox.showinfo("Success", "Two-Factor Authentication has been disabled.")
                self.result = True
                self.dialog.destroy()

        except AuthenticationError as e:
            messagebox.showerror("Error", str(e))

    def _cancel(self):
        """Cancel disabling 2FA"""
        self.result = False
        self.dialog.destroy()

    def show(self):
        """Show dialog and wait for result"""
        self.dialog.wait_window()
        return self.result