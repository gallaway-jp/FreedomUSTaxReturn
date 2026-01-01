"""
Modern UI Components - CustomTkinter wrappers for consistent styling

Provides modern, accessible UI components built on CustomTkinter for the
tax application, ensuring consistent appearance and behavior across all forms.
"""

import customtkinter as ctk
from typing import Optional, Callable, Any, Union, List
import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import datetime, date
import re


class ModernFrame(ctk.CTkFrame):
    """Modern frame with consistent styling"""

    def __init__(self, master, title: Optional[str] = None, **kwargs):
        super().__init__(master, **kwargs)

        if title:
            self.title_label = ctk.CTkLabel(
                self,
                text=title,
                font=ctk.CTkFont(size=16, weight="bold")
            )
            self.title_label.pack(pady=(10, 5), padx=10, anchor="w")


class ModernLabel(ctk.CTkLabel):
    """Modern label with consistent styling and accessibility support"""

    def __init__(self, master, text: str = "", required: bool = False, accessibility_service=None, **kwargs):
        # Add asterisk for required fields
        display_text = f"{text} *" if required else text

        super().__init__(master, text=display_text, **kwargs)

        if required:
            self.configure(text_color="red")

        # Apply accessibility features if service is provided
        if accessibility_service:
            accessibility_service.make_accessible(
                self,
                label=text,
                role="label"
            )


class ModernEntry(ctk.CTkEntry):
    """Modern entry field with validation, help text, and accessibility support"""

    def __init__(self, master, label_text: str = "", help_text: str = "",
                 validator: Optional[Callable] = None, required: bool = False,
                 accessibility_service=None, **kwargs):
        self.frame = ctk.CTkFrame(master)
        self.frame.pack(fill="x", pady=2)

        # Label
        if label_text:
            self.label = ModernLabel(
                self.frame,
                text=label_text,
                required=required,
                font=ctk.CTkFont(size=12),
                accessibility_service=accessibility_service
            )
            self.label.pack(anchor="w", padx=5, pady=(5, 0))

        # Entry field
        super().__init__(self.frame, **kwargs)
        self.pack(fill="x", padx=5, pady=(0, 5))

        # Apply accessibility features if service is provided
        if accessibility_service:
            accessibility_service.make_accessible(
                self,
                label=label_text,
                role="textbox"
            )

        # Help text
        if help_text:
            self.help_label = ctk.CTkLabel(
                self.frame,
                text=help_text,
                font=ctk.CTkFont(size=10),
                text_color="gray60"
            )
            self.help_label.pack(anchor="w", padx=5, pady=(0, 5))
            self.original_help = help_text

        self.validator = validator
        self.bind("<FocusOut>", self._validate)

    def _validate(self, event=None):
        """Validate input on focus loss"""
        if self.validator:
            value = self.get()
            is_valid, error_msg = self.validator(value)
            if not is_valid:
                self.configure(border_color="red")
                if hasattr(self, 'help_label'):
                    self.help_label.configure(text=error_msg, text_color="red")
            else:
                self.configure(border_color=["#979DA2", "#565B5E"])
                if hasattr(self, 'help_label') and hasattr(self, 'original_help'):
                    self.help_label.configure(text=self.original_help, text_color="gray60")

    def get_frame(self):
        """Get the containing frame"""
        return self.frame


class ModernComboBox(ctk.CTkComboBox):
    """Modern combobox with label and help text"""

    def __init__(self, master, label_text: str = "", help_text: str = "",
                 values: Optional[List[str]] = None, required: bool = False,
                 **kwargs):
        self.frame = ctk.CTkFrame(master)
        self.frame.pack(fill="x", pady=2)

        # Label
        if label_text:
            self.label = ModernLabel(
                self.frame,
                text=label_text,
                required=required,
                font=ctk.CTkFont(size=12)
            )
            self.label.pack(anchor="w", padx=5, pady=(5, 0))

        # Combobox
        super().__init__(self.frame, values=values or [], **kwargs)
        self.pack(fill="x", padx=5, pady=(0, 5))

        # Help text
        if help_text:
            self.help_label = ctk.CTkLabel(
                self.frame,
                text=help_text,
                font=ctk.CTkFont(size=10),
                text_color="gray60"
            )
            self.help_label.pack(anchor="w", padx=5, pady=(0, 5))


class ModernButton(ctk.CTkButton):
    """Modern button with consistent styling and accessibility support"""

    def __init__(self, master, text: str, command: Optional[Callable] = None,
                 button_type: str = "primary", accessibility_service=None, **kwargs):
        # Set colors based on type
        if button_type == "primary":
            fg_color = "#1f538d"
            hover_color = "#14375e"
        elif button_type == "secondary":
            fg_color = "#6c757d"
            hover_color = "#545b62"
        elif button_type == "success":
            fg_color = "#28a745"
            hover_color = "#1e7e34"
        elif button_type == "danger":
            fg_color = "#dc3545"
            hover_color = "#bd2130"
        else:
            fg_color = None
            hover_color = None

        super().__init__(
            master,
            text=text,
            command=command,
            fg_color=fg_color,
            hover_color=hover_color,
            **kwargs
        )

        # Apply accessibility features if service is provided
        if accessibility_service:
            accessibility_service.make_accessible(
                self,
                label=text,
                role="button"
            )


class ModernCheckBox(ctk.CTkCheckBox):
    """Modern checkbox with label"""

    def __init__(self, master, text: str = "", **kwargs):
        super().__init__(master, text=text, **kwargs)


class ModernRadioGroup(ctk.CTkFrame):
    """Modern radio button group"""

    def __init__(self, master, label_text: str = "", options: List[str] = None,
                 help_text: str = "", required: bool = False, **kwargs):
        super().__init__(master, **kwargs)

        self.selected_value = tk.StringVar()

        # Label
        if label_text:
            self.label = ModernLabel(
                self,
                text=label_text,
                required=required,
                font=ctk.CTkFont(size=12)
            )
            self.label.pack(anchor="w", padx=5, pady=(5, 0))

        # Radio buttons
        self.radio_buttons = []
        for option in options or []:
            rb = ctk.CTkRadioButton(
                self,
                text=option,
                variable=self.selected_value,
                value=option
            )
            rb.pack(anchor="w", padx=20, pady=2)
            self.radio_buttons.append(rb)

        # Help text
        if help_text:
            self.help_label = ctk.CTkLabel(
                self,
                text=help_text,
                font=ctk.CTkFont(size=10),
                text_color="gray60"
            )
            self.help_label.pack(anchor="w", padx=5, pady=(0, 5))

    def get(self) -> str:
        """Get selected value"""
        return self.selected_value.get()

    def set(self, value: str):
        """Set selected value"""
        self.selected_value.set(value)


class ModernTextBox(ctk.CTkTextbox):
    """Modern text box with label"""

    def __init__(self, master, label_text: str = "", help_text: str = "",
                 height: int = 100, required: bool = False, **kwargs):
        self.frame = ctk.CTkFrame(master)
        self.frame.pack(fill="x", pady=2)

        # Label
        if label_text:
            self.label = ModernLabel(
                self.frame,
                text=label_text,
                required=required,
                font=ctk.CTkFont(size=12)
            )
            self.label.pack(anchor="w", padx=5, pady=(5, 0))

        # Text box
        super().__init__(self.frame, height=height, **kwargs)
        self.pack(fill="x", padx=5, pady=(0, 5))

        # Help text
        if help_text:
            self.help_label = ctk.CTkLabel(
                self.frame,
                text=help_text,
                font=ctk.CTkFont(size=10),
                text_color="gray60"
            )
            self.help_label.pack(anchor="w", padx=5, pady=(0, 5))


class ModernProgressBar(ctk.CTkProgressBar):
    """Modern progress bar with label"""

    def __init__(self, master, label_text: str = "", **kwargs):
        self.frame = ctk.CTkFrame(master)
        self.frame.pack(fill="x", pady=5)

        if label_text:
            self.label = ctk.CTkLabel(
                self.frame,
                text=label_text,
                font=ctk.CTkFont(size=12)
            )
            self.label.pack(anchor="w", padx=5, pady=(5, 0))

        super().__init__(self.frame, **kwargs)
        self.pack(fill="x", padx=5, pady=(0, 5))


class ModernScrollableFrame(ctk.CTkScrollableFrame):
    """Modern scrollable frame with consistent styling"""

    def __init__(self, master, title: Optional[str] = None, **kwargs):
        super().__init__(master, **kwargs)

        if title:
            self.title_label = ctk.CTkLabel(
                self,
                text=title,
                font=ctk.CTkFont(size=16, weight="bold")
            )
            self.title_label.pack(pady=(10, 5), padx=10, anchor="w")


class ModernTabView(ctk.CTkTabview):
    """Modern tab view with consistent styling"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)


class ModernDialog(ctk.CTkToplevel):
    """Modern dialog window"""

    def __init__(self, master, title: str = "", **kwargs):
        super().__init__(master, **kwargs)
        self.title(title)

        # Center dialog
        self.geometry("600x400")
        self.resizable(True, True)

        # Make modal
        self.transient(master)
        self.grab_set()

        # Focus
        self.focus_set()


# Utility functions for common validations
def validate_ssn(value: str) -> tuple[bool, str]:
    """Validate Social Security Number format"""
    if not value:
        return False, "SSN is required"

    # Remove dashes and spaces
    clean_value = re.sub(r'[-\s]', '', value)

    if len(clean_value) != 9:
        return False, "SSN must be 9 digits"

    if not clean_value.isdigit():
        return False, "SSN must contain only numbers"

    # Format: XXX-XX-XXXX
    formatted = f"{clean_value[:3]}-{clean_value[3:5]}-{clean_value[5:]}"
    return True, formatted


def validate_zip_code(value: str) -> tuple[bool, str]:
    """Validate ZIP code format"""
    if not value:
        return False, "ZIP code is required"

    clean_value = value.strip()

    if len(clean_value) == 5 and clean_value.isdigit():
        return True, clean_value
    elif len(clean_value) == 10 and clean_value[5] == '-' and clean_value[:5].isdigit() and clean_value[6:].isdigit():
        return True, clean_value
    else:
        return False, "ZIP code must be 5 digits or 5+4 format (e.g., 12345 or 12345-6789)"


def validate_currency(value: str) -> tuple[bool, str]:
    """Validate currency amount"""
    if not value:
        return True, ""  # Allow empty

    try:
        # Remove commas, dollar signs, etc.
        clean_value = re.sub(r'[$,\s]', '', value)
        amount = float(clean_value)

        if amount < 0:
            return False, "Amount cannot be negative"

        return True, ".2f"
    except ValueError:
        return False, "Please enter a valid dollar amount"


def validate_date(value: str) -> tuple[bool, str]:
    """Validate date format"""
    if not value:
        return True, ""  # Allow empty

    try:
        # Try MM/DD/YYYY format
        date_obj = datetime.strptime(value, "%m/%d/%Y")
        return True, date_obj.strftime("%m/%d/%Y")
    except ValueError:
        return False, "Please enter date in MM/DD/YYYY format"


def show_info_message(title: str, message: str):
    """Show info message dialog"""
    messagebox.showinfo(title, message)


def show_error_message(title: str, message: str):
    """Show error message dialog"""
    messagebox.showerror(title, message)


def show_warning_message(title: str, message: str):
    """Show warning message dialog"""
    messagebox.showwarning(title, message)


def show_confirmation(title: str, message: str) -> bool:
    """Show confirmation dialog"""
    return messagebox.askyesno(title, message)


def show_file_dialog(**kwargs) -> Optional[str]:
    """Show file selection dialog"""
    return filedialog.askopenfilename(**kwargs)


def show_save_dialog(**kwargs) -> Optional[str]:
    """Show file save dialog"""
    return filedialog.asksaveasfilename(**kwargs)