"""
Translation Management Window

GUI for managing application translations and language settings.
Allows users to switch languages and view translation statistics.
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
import json
from typing import Optional, Dict, Any
from pathlib import Path

from config.app_config import AppConfig
from services.translation_service import TranslationService
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton, show_info_message, show_error_message


class TranslationManagementWindow:
    """
    Window for managing translations and language settings.

    Features:
    - Language selection and switching
    - Translation statistics display
    - Missing translation identification
    - Translation file management
    """

    def __init__(self, parent: ctk.CTk, config: AppConfig, translation_service: Optional[TranslationService] = None):
        """
        Initialize translation management window.

        Args:
            parent: Parent window
            config: Application configuration
            translation_service: Translation service instance
        """
        self.parent = parent
        self.config = config
        self.translation_service = translation_service or TranslationService(config)

        # UI components
        self.window: Optional[ctk.CTkToplevel] = None
        self.notebook: Optional[ttk.Notebook] = None
        self.language_var: Optional[ctk.StringVar] = None
        self.stats_tree: Optional[ttk.Treeview] = None
        self.missing_tree: Optional[ttk.Treeview] = None

        # Current data
        self.current_stats: Dict[str, Dict[str, Any]] = {}

    def show(self):
        """Show the translation management window"""
        self.window = ctk.CTkToplevel(self.parent)
        self.window.title("Translation Management - Freedom US Tax Return")
        self.window.geometry("900x700")
        self.window.resizable(True, True)

        # Initialize UI
        self._setup_ui()
        self._load_data()

        # Center window
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

        # Make modal
        self.window.transient(self.parent)
        self.window.grab_set()
        self.parent.wait_window(self.window)

    def _setup_ui(self):
        """Setup the main user interface"""
        if not self.window:
            return

        # Create main frame
        main_frame = ModernFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ModernLabel(
            main_frame,
            text="Translation Management",
            font=ctk.CTkFont(size=18)
        )
        title_label.pack(pady=(0, 20))

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, pady=(0, 20))

        # Create tabs
        self._create_language_tab()
        self._create_statistics_tab()
        self._create_missing_tab()

        # Buttons
        button_frame = ModernFrame(main_frame)
        button_frame.pack(fill="x", pady=(20, 0))

        ModernButton(
            button_frame,
            text="Apply Language",
            command=self._apply_language,
            button_type="primary"
        ).pack(side="left", padx=(0, 10))

        ModernButton(
            button_frame,
            text="Refresh Statistics",
            command=self._refresh_statistics,
            button_type="secondary"
        ).pack(side="left", padx=(0, 10))

        ModernButton(
            button_frame,
            text="Close",
            command=self._close_window,
            button_type="secondary"
        ).pack(side="right")

    def _create_language_tab(self):
        """Create the language selection tab"""
        tab = ModernFrame(self.notebook)
        self.notebook.add(tab, text="Language Settings")

        # Current language display
        current_frame = ModernFrame(tab)
        current_frame.pack(fill="x", padx=10, pady=10)

        ModernLabel(
            current_frame,
            text="Current Language:",
            font=ctk.CTkFont()
        ).pack(side="left", padx=(0, 10))

        current_lang_label = ModernLabel(
            current_frame,
            text=self.translation_service.get_language_name()
        )
        current_lang_label.pack(side="left")

        # Language selection
        select_frame = ModernFrame(tab)
        select_frame.pack(fill="x", padx=10, pady=(20, 10))

        ModernLabel(
            select_frame,
            text="Select Language:",
            font=ctk.CTkFont()
        ).pack(anchor="w", pady=(0, 10))

        self.language_var = ctk.StringVar(value=self.translation_service.get_language())

        # Create language options
        languages = self.translation_service.get_available_languages()
        for code, name in languages.items():
            rb = ctk.CTkRadioButton(
                select_frame,
                text=f"{name} ({code})",
                variable=self.language_var,
                value=code
            )
            rb.pack(anchor="w", pady=2)

        # Language info
        info_frame = ModernFrame(tab)
        info_frame.pack(fill="x", padx=10, pady=(20, 10))

        info_text = """
Language Settings:
• Changes take effect immediately
• Some UI elements may require restart
• Translations are managed using Babel (.po/.mo files)
• All supported languages include full translations
• English is used as fallback for missing translations
        """

        ModernLabel(
            info_frame,
            text=info_text.strip(),
            justify="left"
        ).pack(anchor="w")

    def _create_statistics_tab(self):
        """Create the translation statistics tab"""
        tab = ModernFrame(self.notebook)
        self.notebook.add(tab, text="Translation Statistics")

        # Statistics tree
        tree_frame = ModernFrame(tab)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create treeview
        columns = ("Language", "Total Keys", "Completion %", "Missing Keys")
        self.stats_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)

        # Configure columns
        for col in columns:
            self.stats_tree.heading(col, text=col)
            self.stats_tree.column(col, width=150, anchor="center")

        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.stats_tree.yview)
        self.stats_tree.configure(yscrollcommand=scrollbar.set)

        self.stats_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Statistics info
        info_frame = ModernFrame(tab)
        info_frame.pack(fill="x", padx=10, pady=(10, 0))

        info_text = """
Translation Statistics:
• Shows completion status for each language
• English serves as the base language (100%)
• Completion % indicates translated keys vs total keys
• Missing keys require translation work
        """

        ModernLabel(
            info_frame,
            text=info_text.strip(),
            justify="left"
        ).pack(anchor="w")

    def _create_missing_tab(self):
        """Create the missing translations tab"""
        tab = ModernFrame(self.notebook)
        self.notebook.add(tab, text="Missing Translations")

        # Info about Babel
        info_frame = ModernFrame(tab)
        info_frame.pack(fill="x", padx=10, pady=(10, 5))

        info_text = """
Note: Translations are managed using Babel (.po/.mo files).
To add new translations, edit the .po files in the locale/ directory.
        """

        ModernLabel(
            info_frame,
            text=info_text.strip(),
            justify="left",
            font=ctk.CTkFont(size=10)
        ).pack(anchor="w")

        # Language selection for missing translations
        select_frame = ModernFrame(tab)
        select_frame.pack(fill="x", padx=10, pady=10)

        ModernLabel(
            select_frame,
            text="Check Missing Translations for:",
            font=ctk.CTkFont()
        ).pack(anchor="w", pady=(0, 10))

        self.missing_lang_var = ctk.StringVar(value="es")  # Default to Spanish

        # Language dropdown
        lang_combo = ctk.CTkComboBox(
            select_frame,
            variable=self.missing_lang_var,
            values=list(self.translation_service.get_available_languages().keys()),
            command=self._update_missing_translations
        )
        lang_combo.pack(anchor="w")

        # Missing translations tree
        tree_frame = ModernFrame(tab)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(10, 10))

        # Create treeview
        columns = ("Key", "English Text")
        self.missing_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)

        # Configure columns
        self.missing_tree.heading("Key", text="Translation Key")
        self.missing_tree.column("Key", width=200, anchor="w")
        self.missing_tree.heading("English Text", text="English Text")
        self.missing_tree.column("English Text", width=400, anchor="w")

        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.missing_tree.yview)
        self.missing_tree.configure(yscrollcommand=scrollbar.set)

        self.missing_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Action buttons
        action_frame = ModernFrame(tab)
        action_frame.pack(fill="x", padx=10, pady=(0, 10))

        ModernButton(
            action_frame,
            text="Export Missing Keys",
            command=self._export_missing_keys,
            button_type="secondary"
        ).pack(side="left", padx=(0, 10))

        ModernButton(
            action_frame,
            text="Refresh",
            command=self._update_missing_translations,
            button_type="secondary"
        ).pack(side="left")

    def _load_data(self):
        """Load initial data"""
        self._refresh_statistics()
        self._update_missing_translations()

    def _apply_language(self):
        """Apply the selected language"""
        if not self.language_var:
            return

        new_language = self.language_var.get()
        if self.translation_service.set_language(new_language):
            show_info_message(
                "Language Changed",
                f"Language has been changed to {self.translation_service.get_language_name()}.\n\n"
                "Some interface elements may require an application restart to display correctly."
            )
            # Update current language display
            self._refresh_statistics()
        else:
            show_error_message("Language Error", "Failed to change language. Please try again.")

    def _refresh_statistics(self):
        """Refresh translation statistics"""
        if not self.stats_tree:
            return

        # Clear existing data
        for item in self.stats_tree.get_children():
            self.stats_tree.delete(item)

        # Get statistics
        self.current_stats = self.translation_service.get_translation_stats()

        # Add data to tree
        for lang_code, stats in self.current_stats.items():
            self.stats_tree.insert("", "end", values=(
                f"{stats['name']} ({lang_code})",
                stats['total_keys'],
                f"{stats['completion_percentage']}%",
                stats['missing_keys']
            ))

    def _update_missing_translations(self, *args):
        """Update the missing translations display"""
        if not self.missing_tree or not hasattr(self, 'missing_lang_var'):
            return

        # Clear existing data
        for item in self.missing_tree.get_children():
            self.missing_tree.delete(item)

        # Get missing translations
        lang_code = self.missing_lang_var.get()
        missing_keys = self.translation_service.get_missing_translations(lang_code)

        # Add data to tree
        for key in missing_keys:
            english_text = self.translation_service.translate(key, language_code='en')
            self.missing_tree.insert("", "end", values=(key, english_text))

    def _export_missing_keys(self):
        """Export missing translation keys to a file"""
        if not hasattr(self, 'missing_lang_var'):
            return

        lang_code = self.missing_lang_var.get()
        missing_keys = self.translation_service.get_missing_translations(lang_code)

        if not missing_keys:
            show_info_message("Export Complete", "No missing translations found for export.")
            return

        try:
            # Create export data
            export_data = {}
            for key in missing_keys:
                export_data[key] = self.translation_service.translate(key, language_code='en')

            # Save to file
            filename = f"missing_translations_{lang_code}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            show_info_message(
                "Export Complete",
                f"Missing translation keys exported to {filename}\n\n"
                f"Total missing keys: {len(missing_keys)}"
            )

        except Exception as e:
            show_error_message("Export Failed", f"Failed to export missing keys: {str(e)}")

    def _close_window(self):
        """Close the translation management window"""
        if self.window:
            self.window.destroy()