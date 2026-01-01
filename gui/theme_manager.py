"""
Theme manager for dark/light mode support with accessibility integration
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional

from services.accessibility_service import AccessibilityService, ColorScheme


class ThemeManager:
    """Manages application themes (light/dark mode) with accessibility support"""

    # Light theme colors
    LIGHT_THEME = {
        "bg": "#ffffff",
        "fg": "#000000",
        "sidebar_bg": "#f0f0f0",
        "sidebar_fg": "#000000",
        "button_bg": "#e0e0e0",
        "button_fg": "#000000",
        "entry_bg": "#ffffff",
        "entry_fg": "#000000",
        "frame_bg": "#f8f8f8",
        "frame_fg": "#000000",
        "label_bg": "#f8f8f8",
        "label_fg": "#000000",
        "progress_bg": "#e0e0e0",
        "progress_fg": "#007acc",
        "border": "#cccccc",
        "highlight": "#007acc",
        "error": "#cc0000",
        "success": "#00aa00",
        "warning": "#ffaa00"
    }

    # Dark theme colors
    DARK_THEME = {
        "bg": "#2b2b2b",
        "fg": "#ffffff",
        "sidebar_bg": "#3c3c3c",
        "sidebar_fg": "#ffffff",
        "button_bg": "#505050",
        "button_fg": "#ffffff",
        "entry_bg": "#404040",
        "entry_fg": "#ffffff",
        "frame_bg": "#333333",
        "frame_fg": "#ffffff",
        "label_bg": "#333333",
        "label_fg": "#ffffff",
        "progress_bg": "#505050",
        "progress_fg": "#007acc",
        "border": "#555555",
        "highlight": "#007acc",
        "error": "#ff6b6b",
        "success": "#51cf66",
        "warning": "#ffd43b"
    }

    # High contrast theme colors
    HIGH_CONTRAST_THEME = {
        "bg": "#000000",
        "fg": "#ffffff",
        "sidebar_bg": "#000000",
        "sidebar_fg": "#ffffff",
        "button_bg": "#ffffff",
        "button_fg": "#000000",
        "entry_bg": "#ffffff",
        "entry_fg": "#000000",
        "frame_bg": "#000000",
        "frame_fg": "#ffffff",
        "label_bg": "#000000",
        "label_fg": "#ffffff",
        "progress_bg": "#ffffff",
        "progress_fg": "#000000",
        "border": "#ffffff",
        "highlight": "#ffff00",
        "error": "#ff0000",
        "success": "#00ff00",
        "warning": "#ffff00"
    }

    def __init__(self, root: tk.Tk, accessibility_service: Optional[AccessibilityService] = None):
        self.root = root
        self.accessibility_service = accessibility_service
        self.current_theme = "light"
        self.themes = {
            "light": self.LIGHT_THEME,
            "dark": self.DARK_THEME,
            "high_contrast": self.HIGH_CONTRAST_THEME
        }

        # Initialize with accessibility-aware theme
        self._initialize_theme()

    def _initialize_theme(self):
        """Initialize theme based on accessibility settings"""
        if self.accessibility_service:
            # Set theme based on accessibility color scheme
            if self.accessibility_service.profile.color_scheme == ColorScheme.DARK_MODE:
                self.current_theme = "dark"
            elif self.accessibility_service.profile.color_scheme == ColorScheme.HIGH_CONTRAST:
                self.current_theme = "high_contrast"
            else:
                self.current_theme = "light"
        else:
            self.current_theme = "light"

        self.apply_theme()

    def set_theme(self, theme_name: str) -> None:
        """Set the application theme"""
        if theme_name not in self.themes:
            raise ValueError(f"Theme '{theme_name}' not found. Available: {list(self.themes.keys())}")

        self.current_theme = theme_name

        # Update accessibility service if available
        if self.accessibility_service:
            if theme_name == "high_contrast":
                self.accessibility_service.update_profile(color_scheme=ColorScheme.HIGH_CONTRAST)
            elif theme_name == "dark":
                self.accessibility_service.update_profile(color_scheme=ColorScheme.DARK_MODE)
            else:
                self.accessibility_service.update_profile(color_scheme=ColorScheme.DEFAULT)

        self.apply_theme()

    def apply_theme(self) -> None:
        """Apply the current theme to the application"""
        theme = self.themes[self.current_theme]

        # Apply accessibility overrides if needed
        if self.accessibility_service and self.accessibility_service.profile.high_contrast:
            # Override with high contrast colors
            hc_colors = self.accessibility_service.get_color_scheme()
            theme = theme.copy()
            theme.update({
                "bg": hc_colors.get("bg", theme["bg"]),
                "fg": hc_colors.get("fg", theme["fg"]),
                "button_bg": hc_colors.get("button_bg", theme["button_bg"]),
                "button_fg": hc_colors.get("button_fg", theme["button_fg"]),
                "entry_bg": hc_colors.get("entry_bg", theme["entry_bg"]),
                "entry_fg": hc_colors.get("entry_fg", theme["entry_fg"]),
                "highlight": hc_colors.get("focus_bg", theme["highlight"])
            })

        # Configure root window
        self.root.configure(bg=theme["bg"])

        # Configure ttk styles
        style = ttk.Style()

        # Frame styles
        style.configure("TFrame", background=theme["frame_bg"])
        style.configure("Card.TFrame", background=theme["frame_bg"], relief="raised", borderwidth=1)

        # Label styles
        base_font_size = 9
        if self.accessibility_service:
            base_font_size = self.accessibility_service.profile.font_size

        style.configure("TLabel",
            background=theme["label_bg"],
            foreground=theme["label_fg"],
            font=("Segoe UI", base_font_size)
        )
        style.configure("Header.TLabel",
            font=("Segoe UI", base_font_size + 8, "bold"),
            background=theme["label_bg"],
            foreground=theme["label_fg"]
        )
        style.configure("Subheader.TLabel",
            font=("Segoe UI", base_font_size + 4, "bold"),
            background=theme["label_bg"],
            foreground=theme["label_fg"]
        )

        # Button styles
        button_padx = 5
        button_pady = 2
        if self.accessibility_service and self.accessibility_service.profile.large_click_targets:
            button_padx = 10
            button_pady = 5

        style.configure("TButton",
            background=theme["button_bg"],
            foreground=theme["button_fg"],
            font=("Segoe UI", base_font_size),
            padx=button_padx,
            pady=button_pady
        )
        style.map("TButton",
            background=[("active", theme["highlight"])],
            foreground=[("active", theme["bg"])]
        )

        # Entry styles
        style.configure("TEntry",
            fieldbackground=theme["entry_bg"],
            foreground=theme["entry_fg"],
            font=("Segoe UI", base_font_size)
        )

        # Checkbutton styles
        style.configure("TCheckbutton",
            background=theme["frame_bg"],
            foreground=theme["frame_fg"],
            font=("Segoe UI", base_font_size)
        )

        # Progressbar styles
        style.configure("TProgressbar",
            background=theme["progress_fg"],
            troughcolor=theme["progress_bg"],
            borderwidth=0,
            lightcolor=theme["progress_fg"],
            darkcolor=theme["progress_fg"]
        )

        # Custom styles for specific widgets
        style.configure("Sidebar.TButton",
            background=theme["sidebar_bg"],
            foreground=theme["sidebar_fg"],
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", base_font_size),
            padx=button_padx,
            pady=button_pady
        )
        style.map("Sidebar.TButton",
            background=[("active", theme["highlight"])],
            foreground=[("active", theme["bg"])]
        )

        style.configure("ActivePage.Sidebar.TButton",
            background=theme["highlight"],
            foreground=theme["bg"],
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", base_font_size),
            padx=button_padx,
            pady=button_pady
        )

        # Apply focus indicators if enabled
        if self.accessibility_service and self.accessibility_service.profile.focus_indicators:
            self._configure_focus_indicators(style, theme)

    def _configure_focus_indicators(self, style: ttk.Style, theme: Dict[str, str]):
        """Configure focus indicators for accessibility"""
        # Add focus ring styling
        focus_color = theme.get("highlight", "#007acc")

        # Button focus
        style.map("TButton",
            relief=[("focus", "solid")],
            bordercolor=[("focus", focus_color)]
        )

        # Entry focus
        style.map("TEntry",
            bordercolor=[("focus", focus_color)],
            lightcolor=[("focus", focus_color)],
            darkcolor=[("focus", focus_color)]
        )

    def get_color(self, color_name: str) -> str:
        """Get a color value from the current theme"""
        return self.themes[self.current_theme].get(color_name, "#000000")

    def get_current_theme(self) -> Dict[str, str]:
        """Get the current theme colors"""
        return self.themes[self.current_theme]

    def toggle_theme(self) -> str:
        """Toggle between light and dark themes"""
        new_theme = "dark" if self.current_theme == "light" else "light"
        self.set_theme(new_theme)
        return new_theme

    def apply_theme_to_window(self, window: tk.Toplevel) -> None:
        """Apply current theme to a specific window"""
        theme = self.themes[self.current_theme]

        # Apply accessibility overrides
        if self.accessibility_service and self.accessibility_service.profile.high_contrast:
            hc_colors = self.accessibility_service.get_color_scheme()
            theme = theme.copy()
            theme.update({
                "bg": hc_colors.get("bg", theme["bg"]),
                "fg": hc_colors.get("fg", theme["fg"])
            })

        window.configure(bg=theme["bg"])

        # Apply to all child widgets
        self._apply_theme_to_children(window, theme)

    def _apply_theme_to_children(self, widget: tk.Widget, theme: Dict[str, str]) -> None:
        """Recursively apply theme to all child widgets"""
        for child in widget.winfo_children():
            widget_type = child.winfo_class()

            try:
                if widget_type in ('Label', 'Button', 'Entry', 'Text', 'Frame', 'Toplevel'):
                    # Apply background and foreground
                    if 'bg' in child.config():
                        bg_color = theme.get("bg", "#ffffff")
                        if widget_type == 'Frame':
                            bg_color = theme.get("frame_bg", bg_color)
                        elif widget_type in ('Button',):
                            bg_color = theme.get("button_bg", bg_color)
                        elif widget_type in ('Entry',):
                            bg_color = theme.get("entry_bg", bg_color)

                        child.configure(bg=bg_color)

                    if 'fg' in child.config():
                        fg_color = theme.get("fg", "#000000")
                        if widget_type in ('Button',):
                            fg_color = theme.get("button_fg", fg_color)
                        elif widget_type in ('Entry',):
                            fg_color = theme.get("entry_fg", fg_color)

                        child.configure(fg=fg_color)

                # Apply font sizing if accessibility service is available
                if self.accessibility_service and 'font' in child.config():
                    current_font = child.cget('font')
                    if current_font:
                        # Update font size based on accessibility settings
                        new_size = self.accessibility_service.profile.font_size
                        # This is a simplified font update - in practice you'd parse the font tuple
                        try:
                            child.configure(font=("Segoe UI", new_size))
                        except:
                            pass  # Skip if font update fails

            except tk.TclError:
                # Skip widgets that don't support these configurations
                pass

            # Recurse on children
            if hasattr(child, 'winfo_children'):
                self._apply_theme_to_children(child, theme)

    def get_bg_color(self) -> str:
        """Get background color for current theme"""
        return self.get_color("bg")

    def get_fg_color(self) -> str:
        """Get foreground color for current theme"""
        return self.get_color("fg")

    def refresh_theme(self) -> None:
        """Refresh the current theme (useful after accessibility changes)"""
        self.apply_theme()