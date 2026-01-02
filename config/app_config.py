"""
Application configuration with environment variable support

This module centralizes all configuration settings to improve maintainability
and make it easier to adjust settings for different environments.
"""

import os
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Dict, Any


@dataclass
class AppConfig:
    """
    Application configuration settings.

    Can be customized via environment variables:
    - TAX_SAFE_DIR: Directory for storing tax returns
    - TAX_KEY_FILE: Path to encryption key file
    - TAX_YEAR: Current tax year
    - WINDOW_WIDTH: Application window width
    - WINDOW_HEIGHT: Application window height
    - ENCRYPTION_ENABLED: Enable/disable encryption (true/false)
    """

    # Application version
    version: str = "3.0.0"

    # File storage paths
    safe_dir: Path = Path.home() / "Documents" / "TaxReturns"
    key_file: Path = Path.home() / ".tax_encryption_key"
    log_dir: Optional[Path] = None  # Defaults to safe_dir/logs

    # UI Settings
    window_width: int = 1200
    window_height: int = 800
    window_title: str = "Freedom US Tax Return - Free Tax Preparation"
    theme: str = "System"  # "Light", "Dark", or "System"

    # Tax Year Settings
    tax_year: int = 2026

    # Security
    encryption_enabled: bool = True

    # Performance
    cache_calculations: bool = True
    cache_size: int = 128

    # Internationalization
    default_language: str = "system"
    supported_languages: list = None  # Will be set in __post_init__

    def __post_init__(self):
        """Set default log directory if not specified"""
        if self.log_dir is None:
            self.log_dir = self.safe_dir / "logs"

        # Set supported languages if not specified
        if self.supported_languages is None:
            self.supported_languages = ['en', 'es', 'fr', 'de', 'zh', 'ja', 'ko', 'pt', 'it', 'ru']

    @property
    def user_settings_file(self) -> Path:
        """Get the path to the user settings file"""
        return Path.home() / ".freedom_tax_settings.json"

    def load_user_settings(self) -> None:
        """
        Load user settings from persistent storage.
        This overrides default settings with user preferences.
        """
        settings_file = self.user_settings_file
        if settings_file.exists():
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    user_settings = json.load(f)

                # Apply user settings
                if 'theme' in user_settings:
                    self.theme = user_settings['theme']
                if 'default_language' in user_settings:
                    self.default_language = user_settings['default_language']
                if 'window_width' in user_settings:
                    self.window_width = user_settings['window_width']
                if 'window_height' in user_settings:
                    self.window_height = user_settings['window_height']

            except (json.JSONDecodeError, IOError) as e:
                # If settings file is corrupted, ignore it and use defaults
                print(f"Warning: Could not load user settings: {e}")

    def save_user_settings(self) -> None:
        """
        Save current user settings to persistent storage.
        Only saves settings that users can modify through the UI.
        """
        user_settings = {
            'theme': self.theme,
            'default_language': self.default_language,
            'window_width': self.window_width,
            'window_height': self.window_height,
        }

        settings_file = self.user_settings_file
        try:
            # Ensure the directory exists
            settings_file.parent.mkdir(parents=True, exist_ok=True)

            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(user_settings, f, indent=2, ensure_ascii=False)

        except IOError as e:
            print(f"Warning: Could not save user settings: {e}")

    def clear_user_settings(self) -> None:
        """
        Clear user settings by deleting the settings file.
        This will cause the application to use default settings.
        """
        settings_file = self.user_settings_file
        try:
            if settings_file.exists():
                settings_file.unlink()
        except IOError as e:
            print(f"Warning: Could not clear user settings: {e}")

    def reset_to_defaults(self) -> None:
        """
        Reset configurable settings to their default values.
        This affects settings that users can modify through the UI.
        """
        # Reset theme to default
        self.theme = "System"  # Use "System" as the default theme

        # Reset language to default
        self.default_language = "system"  # Use "system" as the default language

        # Reset window size to defaults
        self.window_width = 1200
        self.window_height = 800

    @classmethod
    def from_env(cls) -> 'AppConfig':
        """
        Create configuration from environment variables.

        Returns:
            AppConfig instance with settings from environment

        Example:
            >>> os.environ['TAX_YEAR'] = '2024'
            >>> config = AppConfig.from_env()
            >>> config.tax_year
            2024
        """
        config = cls(
            safe_dir=Path(os.getenv("TAX_SAFE_DIR", cls.safe_dir)),
            key_file=Path(os.getenv("TAX_KEY_FILE", cls.key_file)),
            tax_year=int(os.getenv("TAX_YEAR", cls.tax_year)),
            window_width=int(os.getenv("WINDOW_WIDTH", cls.window_width)),
            window_height=int(os.getenv("WINDOW_HEIGHT", cls.window_height)),
            theme=os.getenv("APP_THEME", cls.theme),
            default_language=os.getenv("APP_LANGUAGE", cls.default_language),
            encryption_enabled=os.getenv("ENCRYPTION_ENABLED", "true").lower() == "true"
        )

        # Load user settings after environment settings
        config.load_user_settings()

        return config

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist"""
        self.safe_dir.mkdir(parents=True, exist_ok=True)
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)


# Global config instance (can be overridden for testing)
config = AppConfig.from_env()
