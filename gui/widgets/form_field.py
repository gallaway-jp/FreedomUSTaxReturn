"""
Form field widget - reusable labeled entry field with validation
"""

import tkinter as tk
from tkinter import ttk
import re
from datetime import datetime

class FormField(ttk.Frame):
    """Labeled entry field widget with validation"""

    def __init__(self, parent, label_text, initial_value="", width=None,
                 field_type="text", required=False, validation_callback=None, tooltip=""):
        super().__init__(parent)
        
        self.label_text = label_text
        self.field_type = field_type
        self.required = required
        self.validation_callback = validation_callback
        self.tooltip_text = tooltip
        self.is_valid = True
        
        # Label with required indicator
        label_frame = ttk.Frame(self)
        label_frame.pack(anchor="w", pady=(0, 3))
        
        self.label = ttk.Label(label_frame, text=label_text)
        self.label.pack(side="left")
        
        if required:
            self.required_label = ttk.Label(
                label_frame,
                text="*",
                foreground="red",
                font=("Arial", 10, "bold")
            )
            self.required_label.pack(side="left")
        
        # Entry frame
        entry_frame = ttk.Frame(self)
        entry_frame.pack(fill="x")
        
        # Entry
        self.entry = ttk.Entry(entry_frame, width=width)
        self.entry.pack(side="left", fill="x", expand=True)
        
        # Validation indicator
        self.validation_icon = ttk.Label(entry_frame, text="", width=2)
        self.validation_icon.pack(side="right")
        
        if initial_value:
            self.entry.insert(0, str(initial_value))
        
        # Bind events
        self.entry.bind('<KeyRelease>', self._on_key_release)
        self.entry.bind('<FocusOut>', self._on_focus_out)
        self.entry.bind('<FocusIn>', self._on_focus_in)
        
        # Tooltip setup
        self.tooltip_window = None
        if tooltip:
            self.entry.bind('<Enter>', self._show_tooltip)
            self.entry.bind('<Leave>', self._hide_tooltip)
    def _apply_field_type_formatting(self):
        """Apply formatting based on field type"""
        if self.field_type == "ssn":
            self.entry.config(width=15)  # XXX-XX-XXXX
            self.entry.bind('<KeyPress>', self._format_ssn)
        elif self.field_type == "currency":
            self.entry.bind('<KeyRelease>', self._format_currency)
        elif self.field_type == "date":
            self.entry.config(width=12)  # MM/DD/YYYY
            # Could add date picker button here

    def _format_ssn(self, event):
        """Format SSN as XXX-XX-XXXX"""
        if event.keysym in ('BackSpace', 'Delete', 'Left', 'Right', 'Home', 'End'):
            return

        value = self.entry.get().replace('-', '')
        if not value.isdigit():
            return "break"

        formatted = ""
        if len(value) >= 3:
            formatted = value[:3] + '-'
            if len(value) >= 5:
                formatted += value[3:5] + '-'
                if len(value) >= 9:
                    formatted += value[5:9]
                else:
                    formatted += value[5:]
            else:
                formatted += value[3:]
        else:
            formatted = value

        self.entry.delete(0, tk.END)
        self.entry.insert(0, formatted)

        # Limit to 11 characters (XXX-XX-XXXX)
        if len(formatted) >= 11:
            return "break"

    def _format_currency(self, event=None):
        """Format as currency"""
        if event and event.keysym in ('BackSpace', 'Delete', 'Left', 'Right', 'Home', 'End', 'Tab'):
            return

        value = self.entry.get().replace('$', '').replace(',', '').strip()

        if value and value.replace('.', '').isdigit():
            try:
                # Allow decimal point
                if '.' in value:
                    parts = value.split('.')
                    if len(parts) == 2 and len(parts[1]) <= 2:
                        num_value = float(value)
                        formatted = f"${num_value:,.2f}"
                        current_pos = self.entry.index(tk.INSERT)
                        self.entry.delete(0, tk.END)
                        self.entry.insert(0, formatted)
                        # Try to maintain cursor position
                        try:
                            self.entry.icursor(current_pos)
                        except:
                            pass
                else:
                    num_value = int(float(value))
                    formatted = f"${num_value:,}"
                    self.entry.delete(0, tk.END)
                    self.entry.insert(0, formatted)
            except ValueError:
                pass

    def _on_key_release(self, event):
        """Handle key release for real-time validation"""
        self._validate()

    def _on_focus_out(self, event):
        """Handle focus out for final validation"""
        self._validate()
    
    def _on_focus_in(self, event):
        """Handle focus in event"""
        pass  # Could be used for additional focus behavior
    
    def _show_tooltip(self, event):
        """Show tooltip"""
        if not self.tooltip_text:
            return
        
        # Calculate position
        x = self.entry.winfo_rootx() + 25
        y = self.entry.winfo_rooty() + 25
        
        # Create tooltip window
        self.tooltip_window = tk.Toplevel(self.entry)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # Create tooltip label
        label = ttk.Label(
            self.tooltip_window,
            text=self.tooltip_text,
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            padding=(5, 3),
            wraplength=300
        )
        label.pack()
        
        # Bring to front
        self.tooltip_window.lift()
    
    def _hide_tooltip(self, event):
        """Hide tooltip"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def _validate(self):
        """Validate the field"""
        value = self.entry.get().strip()
        is_valid = True
        error_msg = ""

        # Required field validation
        if self.required and not value:
            is_valid = False
            error_msg = "This field is required"
        elif value:
            # Type-specific validation
            if self.field_type == "ssn":
                # Check SSN format XXX-XX-XXXX
                if not re.match(r'^\d{3}-\d{2}-\d{4}$', value):
                    is_valid = False
                    error_msg = "SSN must be in format XXX-XX-XXXX"
            elif self.field_type == "email":
                # Basic email validation
                if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', value):
                    is_valid = False
                    error_msg = "Invalid email format"
            elif self.field_type == "date":
                # Date validation MM/DD/YYYY
                try:
                    datetime.strptime(value, '%m/%d/%Y')
                except ValueError:
                    is_valid = False
                    error_msg = "Date must be in format MM/DD/YYYY"
            elif self.field_type == "currency":
                # Currency validation
                clean_value = value.replace('$', '').replace(',', '')
                try:
                    float(clean_value)
                except ValueError:
                    is_valid = False
                    error_msg = "Invalid currency format"
            elif self.field_type == "zip":
                # ZIP code validation
                if not re.match(r'^\d{5}(-\d{4})?$', value):
                    is_valid = False
                    error_msg = "ZIP code must be 5 or 9 digits"
            elif self.field_type == "phone":
                # Phone validation - basic
                digits_only = re.sub(r'\D', '', value)
                if len(digits_only) < 10:
                    is_valid = False
                    error_msg = "Phone number must have at least 10 digits"

        # Update visual indicators
        self._update_validation_display(is_valid, error_msg)

        # Call external validation callback
        if self.validation_callback:
            self.validation_callback(is_valid, error_msg)

        self.is_valid = is_valid
        return is_valid

    def _update_validation_display(self, is_valid, error_msg):
        """Update visual validation indicators"""
        if is_valid:
            self.validation_icon.config(text="✓", foreground="green")
            self.label.config(foreground="black")
            # Remove tooltip if it exists
            try:
                self.entry.config(state="normal")
            except:
                pass
        else:
            self.validation_icon.config(text="✗", foreground="red")
            self.label.config(foreground="red")
            # Could add tooltip with error message here

    def get(self):
        """Get the current value"""
        return self.entry.get()

    def set(self, value):
        """Set the value"""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, str(value))
        self._validate()

    def clear(self):
        """Clear the field"""
        self.entry.delete(0, tk.END)
        self._validate()

    def focus(self):
        """Set focus to this field"""
        self.entry.focus_set()

    def is_field_valid(self):
        """Check if field is valid"""
        return self.is_valid
