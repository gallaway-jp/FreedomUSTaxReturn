"""
Modern Settings Page - Consolidated settings interface

Provides a unified settings page with theme toggle, password change,
language selection, and other application settings.
"""

import customtkinter as ctk
from typing import Optional, Callable, Dict, Any
import tkinter as tk

from config.app_config import AppConfig
from services.translation_service import TranslationService
from services.authentication_service import AuthenticationService
from gui.modern_ui_components import (
    ModernFrame, ModernLabel, ModernButton, ModernEntry,
    show_info_message, show_error_message, show_confirmation
)


class ModernSettingsPage(ctk.CTkScrollableFrame):
    """
    Modern settings page with consolidated application settings.

    Features:
    - Theme toggle (Light/Dark/System)
    - Password change functionality
    - Language selection
    - Accessibility settings
    - Application preferences
    """

    def __init__(
        self,
        parent,
        config: AppConfig,
        translation_service: TranslationService,
        auth_service: AuthenticationService,
        on_theme_changed: Optional[Callable] = None,
        on_language_changed: Optional[Callable] = None,
        **kwargs
    ):
        """
        Initialize the settings page.

        Args:
            parent: Parent widget
            config: Application configuration
            translation_service: Translation service for language management
            auth_service: Authentication service for password management
            on_theme_changed: Callback when theme is changed
            on_language_changed: Callback when language is changed
        """
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.config = config
        self.translation_service = translation_service
        self.auth_service = auth_service
        self.on_theme_changed = on_theme_changed
        self.on_language_changed = on_language_changed

        # Available languages - get from translation service and add System Default
        self.available_languages = self.translation_service.get_available_languages()
        self.available_languages['system'] = 'System Default'

        self._setup_ui()

    def _setup_ui(self):
        """Setup the settings page UI"""
        # Add padding to the scrollable frame
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # ===== APPEARANCE SETTINGS =====
        self._create_section_header(content_frame, "🎨 APPEARANCE")

        # Theme selection
        theme_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        theme_frame.pack(fill="x", padx=10, pady=10)

        theme_label = ModernLabel(
            theme_frame,
            text="Theme:",
            font=ctk.CTkFont(size=12)
        )
        theme_label.pack(anchor="w", pady=(0, 5))

        # Theme buttons in a horizontal layout
        theme_buttons_frame = ctk.CTkFrame(theme_frame, fg_color="transparent")
        theme_buttons_frame.pack(fill="x")

        self.theme_var = ctk.StringVar(value=self._get_current_theme())

        themes = [
            ("Light", "Light"),
            ("Dark", "Dark"),
            ("System", "System")
        ]

        for theme_name, theme_value in themes:
            theme_btn = ctk.CTkRadioButton(
                theme_buttons_frame,
                text=theme_name,
                variable=self.theme_var,
                value=theme_value,
                command=self._on_theme_changed,
                font=ctk.CTkFont(size=11)
            )
            theme_btn.pack(side="left", padx=(0, 20), pady=5)

        # ===== SECURITY SETTINGS =====
        self._create_section_header(content_frame, "🔒 SECURITY")

        # Password change section
        password_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        password_frame.pack(fill="x", padx=10, pady=10)

        password_label = ModernLabel(
            password_frame,
            text="Change Password:",
            font=ctk.CTkFont(size=12)
        )
        password_label.pack(anchor="w", pady=(0, 10))

        # Current password
        current_label = ModernLabel(password_frame, text="Current Password:")
        current_label.pack(anchor="w", pady=(0, 2))
        self.current_password_entry = ModernEntry(
            password_frame,
            show="•",
            placeholder_text="Enter current password"
        )
        self.current_password_entry.pack(fill="x", pady=(0, 10))

        # New password
        new_label = ModernLabel(password_frame, text="New Password:")
        new_label.pack(anchor="w", pady=(0, 2))
        self.new_password_entry = ModernEntry(
            password_frame,
            show="•",
            placeholder_text="Enter new password"
        )
        self.new_password_entry.pack(fill="x", pady=(0, 10))

        # Confirm new password
        confirm_label = ModernLabel(password_frame, text="Confirm New Password:")
        confirm_label.pack(anchor="w", pady=(0, 2))
        self.confirm_password_entry = ModernEntry(
            password_frame,
            show="•",
            placeholder_text="Confirm new password"
        )
        self.confirm_password_entry.pack(fill="x", pady=(0, 10))

        # Change password button
        change_btn = ModernButton(
            password_frame,
            text="Change Password",
            command=self._change_password,
            button_type="secondary",
            height=35
        )
        change_btn.pack(pady=(10, 0))

        # ===== LANGUAGE SETTINGS =====
        self._create_section_header(content_frame, "🌐 LANGUAGE")

        # Language selection
        language_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        language_frame.pack(fill="x", padx=10, pady=10)

        language_label = ModernLabel(
            language_frame,
            text="Language:",
            font=ctk.CTkFont(size=12)
        )
        language_label.pack(anchor="w", pady=(0, 5))

        # Language dropdown
        current_lang = self.translation_service.get_language()
        current_lang_name = self.available_languages.get(current_lang, current_lang)

        self.language_var = ctk.StringVar(value=current_lang)

        language_dropdown = ctk.CTkOptionMenu(
            language_frame,
            values=list(self.available_languages.values()),
            command=self._on_language_changed,
            font=ctk.CTkFont(size=11)
        )
        language_dropdown.set(current_lang_name)
        language_dropdown.pack(fill="x", pady=(0, 5))

        # Language info
        info_label = ModernLabel(
            language_frame,
            text="Changes take effect after restarting the application.",
            font=ctk.CTkFont(size=10),
            text_color="gray60"
        )
        info_label.pack(anchor="w", pady=(5, 0))

        # ===== RESET SETTINGS =====
        self._create_section_header(content_frame, "🔄 RESET")

        # Reset to defaults button
        reset_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        reset_frame.pack(fill="x", padx=10, pady=10)

        reset_button = ModernButton(
            reset_frame,
            text="Reset All Settings to Defaults",
            command=self._reset_to_defaults,
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "gray90")
        )
        reset_button.pack(anchor="w", pady=5)

        reset_info = ModernLabel(
            reset_frame,
            text="This will reset theme, language, and window size to default values.",
            font=ctk.CTkFont(size=10),
            text_color="gray60"
        )
        reset_info.pack(anchor="w", pady=(0, 5))

        # ===== APPLICATION INFO =====
        self._create_section_header(content_frame, "ℹ️ APPLICATION")

        # Version info
        info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=10)

        version_label = ModernLabel(
            info_frame,
            text=f"Version: {self.config.version}",
            font=ctk.CTkFont(size=11)
        )
        version_label.pack(anchor="w", pady=2)

        year_label = ModernLabel(
            info_frame,
            text=f"Tax Year: {self.config.tax_year}",
            font=ctk.CTkFont(size=11)
        )
        year_label.pack(anchor="w", pady=2)

    def _create_section_header(self, parent, title: str):
        """Create a section header with horizontal divider"""
        # Header frame
        header_frame = ctk.CTkFrame(parent, fg_color="transparent", height=40)
        header_frame.pack(fill="x", padx=5, pady=(20, 5))
        header_frame.pack_propagate(False)

        # Title label
        title_label = ModernLabel(
            header_frame,
            text=title,
            font=ctk.CTkFont(size=14),
            text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"]
        )
        title_label.pack(side="left")

        # Horizontal divider line
        divider = ctk.CTkFrame(header_frame, height=2, fg_color="gray60")
        divider.pack(side="right", fill="x", expand=True, padx=(10, 0))

    def _get_current_theme(self) -> str:
        """Get the current theme setting from config"""
        # Return the saved theme setting, not the runtime appearance mode
        return self.config.theme

    def _on_theme_changed(self):
        """Handle theme change"""
        new_theme = self.theme_var.get()
        try:
            ctk.set_appearance_mode(new_theme)

            # Save theme setting to config
            self.config.theme = new_theme
            self.config.save_user_settings()

            if self.on_theme_changed:
                self.on_theme_changed(new_theme)
        except Exception as e:
            show_error_message("Theme Error", f"Failed to change theme: {str(e)}")

    def _change_password(self):
        """Handle password change"""
        current = self.current_password_entry.get().strip()
        new_pass = self.new_password_entry.get().strip()
        confirm = self.confirm_password_entry.get().strip()

        # Validation
        if not current or not new_pass or not confirm:
            show_error_message("Validation Error", "All password fields are required.")
            return

        if new_pass != confirm:
            show_error_message("Validation Error", "New password and confirmation do not match.")
            return

        if len(new_pass) < 8:
            show_error_message("Validation Error", "New password must be at least 8 characters long.")
            return

        try:
            # Authenticate with current password
            session_token = self.auth_service.authenticate_master_password(current)
            if not session_token:
                show_error_message("Authentication Failed", "Current password is incorrect.")
                return

            # Change password
            self.auth_service.change_master_password(current, new_pass)

            # Clear form
            self.current_password_entry.delete(0, "end")
            self.new_password_entry.delete(0, "end")
            self.confirm_password_entry.delete(0, "end")

            show_info_message("Password Changed", "Your password has been changed successfully.")

        except Exception as e:
            show_error_message("Password Change Failed", f"Failed to change password: {str(e)}")

    def _on_language_changed(self, selected_language_name: str):
        """Handle language change"""
        # Find language code from name
        language_code = None
        for code, name in self.available_languages.items():
            if name == selected_language_name:
                language_code = code
                break

        if not language_code:
            show_error_message("Language Error", "Invalid language selection.")
            return

        # Don't convert 'system' to 'en' - let the translation service handle it
        # if language_code == 'system':
        #     language_code = 'en'  # Default language

        try:
            # Change language
            self.translation_service.set_language(language_code)

            # Save language setting to config (preserve 'system' as-is)
            self.config.default_language = language_code
            self.config.save_user_settings()

            if self.on_language_changed:
                self.on_language_changed(language_code)

        except Exception as e:
            show_error_message("Language Error", f"Failed to change language: {str(e)}")

    def refresh_settings(self):
        """Refresh settings display"""
        # Update current theme from config
        self.theme_var.set(self.config.theme)

        # Update current language display
        # Use the saved language setting to determine what to show
        saved_language = self.config.default_language
        if saved_language == 'system':
            current_lang_name = 'System Default'
        else:
            current_lang_name = self.available_languages.get(saved_language, saved_language)

        # Note: The dropdown doesn't have a direct way to update selection,
        # so this is a limitation of the current implementation

    def _reset_to_defaults(self):
        """Reset all settings to defaults"""
        # Show confirmation dialog
        confirmed = show_confirmation(
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?\n\nThis will:\n• Reset theme to System\n• Reset language to System Default\n• Reset window size to default\n\nThis action cannot be undone."
        )

        if not confirmed:
            return

        try:
            # Clear user settings file
            self.config.clear_user_settings()

            # Reset to defaults
            self.config.reset_to_defaults()

            # Apply default theme
            ctk.set_appearance_mode("System")
            self.theme_var.set("System")

            # Apply default language
            self.translation_service.set_language("system")

            # Update language dropdown display
            # Note: We can't directly update the dropdown selection,
            # but the refresh_settings method will handle this

            # Save the default settings
            self.config.save_user_settings()

            # Notify callbacks
            if self.on_theme_changed:
                self.on_theme_changed("System")
            if self.on_language_changed:
                self.on_language_changed("system")

            show_info_message("Settings Reset", "All settings have been reset to defaults.")

        except Exception as e:
            show_error_message("Reset Failed", f"Failed to reset settings: {str(e)}")