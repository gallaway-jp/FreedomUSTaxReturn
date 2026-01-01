"""
Accessibility Settings Dialog

Provides a comprehensive interface for configuring accessibility settings,
ensuring Section 508 and WCAG 2.1 AA compliance.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
from typing import Optional, Dict, Any
from pathlib import Path

from services.accessibility_service import (
    AccessibilityService,
    AccessibilityLevel,
    ColorScheme
)
from gui.theme_manager import ThemeManager


class AccessibilitySettingsDialog:
    """Dialog for configuring accessibility settings"""

    def __init__(self, parent: tk.Tk, accessibility_service: AccessibilityService,
                 theme_manager: ThemeManager):
        self.parent = parent
        self.service = accessibility_service
        self.theme_manager = theme_manager
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Accessibility Settings")
        self.dialog.geometry("700x600")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Make dialog itself accessible
        self.service.make_accessible(
            self.dialog,
            label="Accessibility Settings Dialog",
            role="dialog"
        )

        self._create_widgets()
        self._load_current_settings()
        self.theme_manager.apply_theme_to_window(self.dialog)

        # Center the dialog
        self.dialog.geometry("+{}+{}".format(
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))

        self.dialog.wait_window()

    def _create_widgets(self):
        """Create dialog widgets"""
        # Main container
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Accessibility Settings",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))

        self.service.make_accessible(
            title_label,
            label="Accessibility Settings",
            role="heading"
        )

        # Create notebook for organized tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # General tab
        general_frame = ttk.Frame(notebook, padding="10")
        notebook.add(general_frame, text="General")
        self._create_general_tab(general_frame)

        # Visual tab
        visual_frame = ttk.Frame(notebook, padding="10")
        notebook.add(visual_frame, text="Visual")
        self._create_visual_tab(visual_frame)

        # Navigation tab
        navigation_frame = ttk.Frame(notebook, padding="10")
        notebook.add(navigation_frame, text="Navigation")
        self._create_navigation_tab(navigation_frame)

        # Compliance tab
        compliance_frame = ttk.Frame(notebook, padding="10")
        notebook.add(compliance_frame, text="Compliance")
        self._create_compliance_tab(compliance_frame)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(
            button_frame,
            text="Apply",
            command=self._apply_settings
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            button_frame,
            text="Reset to Defaults",
            command=self._reset_to_defaults
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel
        ).pack(side=tk.RIGHT)

        # Make buttons accessible
        for child in button_frame.winfo_children():
            if isinstance(child, ttk.Button):
                self.service.make_accessible(
                    child,
                    label=child.cget('text'),
                    role="button"
                )

    def _create_general_tab(self, parent: ttk.Frame):
        """Create the general accessibility settings tab"""
        # Accessibility Level
        level_frame = ttk.LabelFrame(parent, text="Compliance Level", padding="10")
        level_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(level_frame, text="Accessibility Standard:").grid(row=0, column=0, sticky=tk.W, pady=5)

        self.level_var = tk.StringVar()
        level_combo = ttk.Combobox(
            level_frame,
            textvariable=self.level_var,
            values=[level.value for level in AccessibilityLevel],
            state="readonly",
            width=20
        )
        level_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)

        self.service.make_accessible(
            level_combo,
            label="Accessibility compliance level",
            description="Choose the level of accessibility compliance"
        )

        # Font Size
        ttk.Label(level_frame, text="Font Size:").grid(row=1, column=0, sticky=tk.W, pady=5)

        self.font_size_var = tk.IntVar()
        font_spin = tk.Spinbox(
            level_frame,
            from_=10,
            to=24,
            textvariable=self.font_size_var,
            width=5
        )
        font_spin.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)

        self.service.make_accessible(
            font_spin,
            label="Font size",
            description="Adjust the base font size for better readability"
        )

        # Screen Reader Support
        reader_frame = ttk.LabelFrame(parent, text="Assistive Technology", padding="10")
        reader_frame.pack(fill=tk.X, pady=(0, 15))

        self.screen_reader_var = tk.BooleanVar()
        ttk.Checkbutton(
            reader_frame,
            text="Enable screen reader optimizations",
            variable=self.screen_reader_var
        ).pack(anchor=tk.W)

        self.announce_var = tk.BooleanVar()
        ttk.Checkbutton(
            reader_frame,
            text="Announce UI changes to screen readers",
            variable=self.announce_var
        ).pack(anchor=tk.W, pady=(5, 0))

    def _create_visual_tab(self, parent: ttk.Frame):
        """Create the visual accessibility settings tab"""
        # Color Scheme
        color_frame = ttk.LabelFrame(parent, text="Color Scheme", padding="10")
        color_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(color_frame, text="Color Scheme:").grid(row=0, column=0, sticky=tk.W, pady=5)

        self.color_scheme_var = tk.StringVar()
        color_combo = ttk.Combobox(
            color_frame,
            textvariable=self.color_scheme_var,
            values=[scheme.value for scheme in ColorScheme],
            state="readonly",
            width=20
        )
        color_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)

        self.service.make_accessible(
            color_combo,
            label="Color scheme selection",
            description="Choose a color scheme for better visibility"
        )

        # Visual Enhancements
        visual_frame = ttk.LabelFrame(parent, text="Visual Enhancements", padding="10")
        visual_frame.pack(fill=tk.X, pady=(0, 15))

        self.high_contrast_var = tk.BooleanVar()
        ttk.Checkbutton(
            visual_frame,
            text="High contrast mode",
            variable=self.high_contrast_var
        ).pack(anchor=tk.W, pady=(0, 5))

        self.focus_var = tk.BooleanVar()
        ttk.Checkbutton(
            visual_frame,
            text="Show focus indicators",
            variable=self.focus_var
        ).pack(anchor=tk.W, pady=(0, 5))

        self.tooltips_var = tk.BooleanVar()
        ttk.Checkbutton(
            visual_frame,
            text="Show tooltips",
            variable=self.tooltips_var
        ).pack(anchor=tk.W)

    def _create_navigation_tab(self, parent: ttk.Frame):
        """Create the navigation accessibility settings tab"""
        # Keyboard Navigation
        keyboard_frame = ttk.LabelFrame(parent, text="Keyboard Navigation", padding="10")
        keyboard_frame.pack(fill=tk.X, pady=(0, 15))

        self.keyboard_nav_var = tk.BooleanVar()
        ttk.Checkbutton(
            keyboard_frame,
            text="Enable full keyboard navigation",
            variable=self.keyboard_nav_var
        ).pack(anchor=tk.W, pady=(0, 10))

        # Keyboard Shortcuts
        shortcuts_label = ttk.Label(
            keyboard_frame,
            text="Common Keyboard Shortcuts:",
            font=("Arial", 10, "bold")
        )
        shortcuts_label.pack(anchor=tk.W, pady=(10, 5))

        shortcuts_text = tk.Text(
            keyboard_frame,
            height=8,
            width=60,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        shortcuts_text.pack(fill=tk.X)

        # Populate shortcuts
        shortcuts = self.service.get_keyboard_shortcuts()
        shortcuts_text.config(state=tk.NORMAL)
        for key, description in shortcuts.items():
            shortcuts_text.insert(tk.END, f"{key:15} - {description}\n")
        shortcuts_text.config(state=tk.DISABLED)

        self.service.make_accessible(
            shortcuts_text,
            label="Keyboard shortcuts reference",
            description="List of available keyboard shortcuts"
        )

        # Additional Options
        options_frame = ttk.LabelFrame(parent, text="Additional Options", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 15))

        self.large_targets_var = tk.BooleanVar()
        ttk.Checkbutton(
            options_frame,
            text="Enlarge click targets for easier interaction",
            variable=self.large_targets_var
        ).pack(anchor=tk.W, pady=(0, 5))

        self.auto_complete_var = tk.BooleanVar()
        ttk.Checkbutton(
            options_frame,
            text="Enable auto-completion in forms",
            variable=self.auto_complete_var
        ).pack(anchor=tk.W, pady=(0, 5))

        self.reduced_motion_var = tk.BooleanVar()
        ttk.Checkbutton(
            options_frame,
            text="Reduce animations and motion effects",
            variable=self.reduced_motion_var
        ).pack(anchor=tk.W)

    def _create_compliance_tab(self, parent: ttk.Frame):
        """Create the compliance information tab"""
        # Compliance Report
        report_frame = ttk.LabelFrame(parent, text="Compliance Report", padding="10")
        report_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Generate report
        report = self.service.get_compliance_report()

        report_text = tk.Text(
            report_frame,
            height=15,
            width=60,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        report_text.pack(fill=tk.BOTH, expand=True)

        # Format report
        report_content = f"""ACCESSIBILITY COMPLIANCE REPORT

Compliance Level: {report['compliance_level'].upper()}
Estimated Compliance: {report['estimated_compliance']:.1f}%

FEATURES ENABLED:
"""

        for feature, enabled in report['features_enabled'].items():
            status = "✓" if enabled else "✗"
            report_content += f"{status} {feature.replace('_', ' ').title()}\n"

        report_content += f"\nColor Scheme: {report['color_scheme'].replace('_', ' ').title()}\n"
        report_content += f"Font Size: {report['font_size']}pt\n"

        report_text.config(state=tk.NORMAL)
        report_text.insert(tk.END, report_content)
        report_text.config(state=tk.DISABLED)

        self.service.make_accessible(
            report_text,
            label="Accessibility compliance report",
            description="Current accessibility compliance status and settings"
        )

        # Standards Information
        info_frame = ttk.LabelFrame(parent, text="Standards Information", padding="10")
        info_frame.pack(fill=tk.X)

        info_text = """WCAG 2.1 AA Standards:
• 4.5:1 contrast ratio for normal text
• 3:1 contrast ratio for large text
• Keyboard navigation support
• Screen reader compatibility
• Focus indicators and management

Section 508 Requirements:
• Equivalent keyboard access
• Screen reader compatibility
• Color and contrast requirements
• Form accessibility
• Error identification and suggestions"""

        info_label = ttk.Label(
            info_frame,
            text=info_text,
            justify=tk.LEFT
        )
        info_label.pack(anchor=tk.W)

        self.service.make_accessible(
            info_label,
            label="Accessibility standards information",
            description="Information about WCAG and Section 508 standards"
        )

    def _load_current_settings(self):
        """Load current accessibility settings into the dialog"""
        profile = self.service.profile

        # General settings
        self.level_var.set(profile.level.value)
        self.font_size_var.set(profile.font_size)
        self.screen_reader_var.set(profile.screen_reader)
        self.announce_var.set(profile.announce_changes)

        # Visual settings
        self.color_scheme_var.set(profile.color_scheme.value)
        self.high_contrast_var.set(profile.high_contrast)
        self.focus_var.set(profile.focus_indicators)
        self.tooltips_var.set(profile.tooltips_enabled)

        # Navigation settings
        self.keyboard_nav_var.set(profile.keyboard_navigation)
        self.large_targets_var.set(profile.large_click_targets)
        self.auto_complete_var.set(profile.auto_complete)
        self.reduced_motion_var.set(profile.reduced_motion)

    def _apply_settings(self):
        """Apply the accessibility settings"""
        try:
            # Update profile with dialog values
            self.service.update_profile(
                level=AccessibilityLevel(self.level_var.get()),
                font_size=self.font_size_var.get(),
                screen_reader=self.screen_reader_var.get(),
                announce_changes=self.announce_var.get(),
                color_scheme=ColorScheme(self.color_scheme_var.get()),
                high_contrast=self.high_contrast_var.get(),
                focus_indicators=self.focus_var.get(),
                tooltips_enabled=self.tooltips_var.get(),
                keyboard_navigation=self.keyboard_nav_var.get(),
                large_click_targets=self.large_targets_var.get(),
                auto_complete=self.auto_complete_var.get(),
                reduced_motion=self.reduced_motion_var.get()
            )

            messagebox.showinfo(
                "Settings Applied",
                "Accessibility settings have been applied successfully.\n\n" +
                "Some changes may require restarting the application to take full effect."
            )

            self.result = True
            self.dialog.destroy()

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to apply accessibility settings:\n\n{str(e)}"
            )

    def _reset_to_defaults(self):
        """Reset all settings to defaults"""
        if messagebox.askyesno(
            "Reset to Defaults",
            "Are you sure you want to reset all accessibility settings to their defaults?\n\n" +
            "This action cannot be undone."
        ):
            # Reset profile to defaults
            self.service.profile = AccessibilityProfile()
            self.service.save_profile()

            # Reload dialog
            self._load_current_settings()

            messagebox.showinfo(
                "Settings Reset",
                "Accessibility settings have been reset to defaults."
            )

    def _on_cancel(self):
        """Handle cancel button"""
        self.result = None
        self.dialog.destroy()


class AccessibilityHelpDialog:
    """Dialog providing accessibility help and guidance"""

    def __init__(self, parent: tk.Tk, accessibility_service: AccessibilityService,
                 theme_manager: ThemeManager):
        self.parent = parent
        self.service = accessibility_service
        self.theme_manager = theme_manager

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Accessibility Help")
        self.dialog.geometry("600x500")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.service.make_accessible(
            self.dialog,
            label="Accessibility Help Dialog",
            role="dialog"
        )

        self._create_widgets()
        self.theme_manager.apply_theme_to_window(self.dialog)

        # Center the dialog
        self.dialog.geometry("+{}+{}".format(
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))

        self.dialog.wait_window()

    def _create_widgets(self):
        """Create help dialog widgets"""
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            frame,
            text="Accessibility Help & Features",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 20))

        # Help content
        help_text = tk.Text(
            frame,
            wrap=tk.WORD,
            padx=10,
            pady=10,
            state=tk.DISABLED
        )
        help_text.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(frame, command=help_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        help_text.config(yscrollcommand=scrollbar.set)

        # Populate help content
        content = """ACCESSIBILITY FEATURES & HELP

NAVIGATION:
• Use Tab and Shift+Tab to move between interactive elements
• Press Enter or Space to activate buttons and select items
• Press Escape to close dialogs or cancel actions
• Use arrow keys to navigate within lists and menus

KEYBOARD SHORTCUTS:
• Ctrl+S: Save current work
• Ctrl+O: Open file
• Ctrl+N: New document
• F1: Open help
• Alt+F4: Close application

SCREEN READER SUPPORT:
• All interactive elements have accessible names and descriptions
• UI changes are announced when screen reader mode is enabled
• Use standard screen reader navigation commands

VISUAL ENHANCEMENTS:
• High contrast mode for improved visibility
• Focus indicators show which element is currently selected
• Enlarged click targets for easier interaction
• Customizable color schemes including dark mode

COMPLIANCE STANDARDS:
This application is designed to meet WCAG 2.1 AA standards and Section 508 requirements for accessibility.

For additional assistance, please contact technical support or refer to the user manual.
"""

        help_text.config(state=tk.NORMAL)
        help_text.insert(tk.END, content)
        help_text.config(state=tk.DISABLED)

        self.service.make_accessible(
            help_text,
            label="Accessibility help content",
            description="Help information about accessibility features and usage"
        )

        # Close button
        ttk.Button(
            frame,
            text="Close",
            command=self.dialog.destroy
        ).pack(pady=(20, 0))

        self.service.make_accessible(
            ttk.Button,
            label="Close help dialog",
            role="button"
        )