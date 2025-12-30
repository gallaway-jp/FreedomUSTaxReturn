"""
Theme manager for dark/light mode support
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any


class ThemeManager:
    """Manages application themes (light/dark mode)"""

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

    def __init__(self, root: tk.Tk):
        self.root = root
        self.current_theme = "light"
        self.themes = {
            "light": self.LIGHT_THEME,
            "dark": self.DARK_THEME
        }

    def set_theme(self, theme_name: str) -> None:
        """Set the application theme"""
        if theme_name not in self.themes:
            raise ValueError(f"Theme '{theme_name}' not found. Available: {list(self.themes.keys())}")

        self.current_theme = theme_name
        theme = self.themes[theme_name]

        # Configure root window
        self.root.configure(bg=theme["bg"])

        # Configure ttk styles
        style = ttk.Style()

        # Frame styles
        style.configure("TFrame", background=theme["frame_bg"])
        style.configure("Card.TFrame", background=theme["frame_bg"], relief="raised", borderwidth=1)

        # Label styles
        style.configure("TLabel", background=theme["label_bg"], foreground=theme["label_fg"])
        style.configure("Header.TLabel", font=("Arial", 20, "bold"), background=theme["label_bg"], foreground=theme["label_fg"])
        style.configure("Subheader.TLabel", font=("Arial", 12, "bold"), background=theme["label_bg"], foreground=theme["label_fg"])

        # Button styles
        style.configure("TButton", background=theme["button_bg"], foreground=theme["button_fg"])
        style.map("TButton",
            background=[("active", theme["highlight"])],
            foreground=[("active", theme["bg"])]
        )

        # Entry styles
        style.configure("TEntry", fieldbackground=theme["entry_bg"], foreground=theme["entry_fg"])

        # Checkbutton styles
        style.configure("TCheckbutton", background=theme["frame_bg"], foreground=theme["frame_fg"])

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
            borderwidth=0
        )
        style.map("Sidebar.TButton",
            background=[("active", theme["highlight"])],
            foreground=[("active", theme["bg"])]
        )

        style.configure("ActivePage.Sidebar.TButton",
            background=theme["highlight"],
            foreground=theme["bg"],
            relief="flat",
            borderwidth=0
        )

    def get_color(self, color_name: str) -> str:
        """Get a color value from the current theme"""
        return self.themes[self.current_theme].get(color_name, "#000000")

    def toggle_theme(self) -> str:
        """Toggle between light and dark themes"""
        new_theme = "dark" if self.current_theme == "light" else "light"
        self.set_theme(new_theme)
        return new_theme