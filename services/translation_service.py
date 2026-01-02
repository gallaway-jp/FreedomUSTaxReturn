"""
Translation and Localization Service

Provides internationalization (i18n) support for the Freedom US Tax Return application.
Supports multiple languages with fallback to English for missing translations.
"""

import json
import os
from typing import Dict, Optional, Any
from pathlib import Path
from config.app_config import AppConfig


class TranslationService:
    """
    Service for managing translations and localization.

    Features:
    - Multiple language support
    - Fallback to English for missing translations
    - Dynamic language switching
    - Translation key management
    - JSON-based translation files
    """

    # Supported languages
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'es': 'Español',
        'fr': 'Français',
        'de': 'Deutsch',
        'zh': '中文',
        'ja': '日本語',
        'ko': '한국어',
        'pt': 'Português',
        'it': 'Italiano',
        'ru': 'Русский'
    }

    def __init__(self, config: AppConfig):
        """
        Initialize translation service.

        Args:
            config: Application configuration
        """
        self.config = config
        self.current_language = 'en'  # Default to English
        self.translations: Dict[str, Dict[str, str]] = {}
        self._load_translations()

    def _load_translations(self):
        """Load all available translation files"""
        translations_dir = Path(__file__).parent.parent / 'data' / 'translations'

        # Ensure translations directory exists
        translations_dir.mkdir(parents=True, exist_ok=True)

        # Load each language file
        for lang_code in self.SUPPORTED_LANGUAGES.keys():
            translation_file = translations_dir / f'{lang_code}.json'
            if translation_file.exists():
                try:
                    with open(translation_file, 'r', encoding='utf-8') as f:
                        self.translations[lang_code] = json.load(f)
                except Exception as e:
                    print(f"Error loading translation file {translation_file}: {e}")
                    self.translations[lang_code] = {}
            else:
                self.translations[lang_code] = {}

    def set_language(self, language_code: str) -> bool:
        """
        Set the current language.

        Args:
            language_code: ISO language code (e.g., 'en', 'es', 'fr')

        Returns:
            True if language was set successfully, False otherwise
        """
        if language_code in self.SUPPORTED_LANGUAGES:
            self.current_language = language_code
            return True
        return False

    def get_language(self) -> str:
        """Get the current language code"""
        return self.current_language

    def get_language_name(self, language_code: Optional[str] = None) -> str:
        """
        Get the display name for a language code.

        Args:
            language_code: Language code to get name for, or None for current language

        Returns:
            Display name of the language
        """
        code = language_code or self.current_language
        return self.SUPPORTED_LANGUAGES.get(code, code)

    def translate(self, key: str, fallback: Optional[str] = None, **kwargs) -> str:
        """
        Translate a key to the current language.

        Args:
            key: Translation key (supports dot notation for nested keys)
            fallback: Fallback text if translation not found
            **kwargs: Format arguments for the translation

        Returns:
            Translated text
        """
        def get_nested_value(data: dict, key_path: str):
            """Get nested value using dot notation"""
            keys = key_path.split('.')
            current = data
            for k in keys:
                if isinstance(current, dict) and k in current:
                    current = current[k]
                else:
                    return None
            return current

        # Try current language first
        if self.current_language in self.translations:
            translation = get_nested_value(self.translations[self.current_language], key)
            if translation:
                return translation.format(**kwargs) if kwargs else translation

        # Try English fallback
        if 'en' in self.translations and self.current_language != 'en':
            translation = get_nested_value(self.translations['en'], key)
            if translation:
                return translation.format(**kwargs) if kwargs else translation

        # Use fallback or key itself
        text = fallback or key
        return text.format(**kwargs) if kwargs else text

    def get_available_languages(self) -> Dict[str, str]:
        """Get dictionary of available language codes and names"""
        return self.SUPPORTED_LANGUAGES.copy()

    def add_translation(self, language_code: str, key: str, text: str) -> bool:
        """
        Add or update a translation.

        Args:
            language_code: Language code
            key: Translation key (supports dot notation for nested keys)
            text: Translated text

        Returns:
            True if translation was added successfully
        """
        if language_code not in self.SUPPORTED_LANGUAGES:
            return False

        if language_code not in self.translations:
            self.translations[language_code] = {}

        def set_nested_value(data: dict, key_path: str, value: str):
            """Set nested value using dot notation"""
            keys = key_path.split('.')
            current = data
            for k in keys[:-1]:  # All keys except the last
                if k not in current or not isinstance(current[k], dict):
                    current[k] = {}
                current = current[k]
            current[keys[-1]] = value

        set_nested_value(self.translations[language_code], key, text)
        return True

    def save_translations(self, language_code: str) -> bool:
        """
        Save translations for a language to file.

        Args:
            language_code: Language code to save

        Returns:
            True if saved successfully
        """
        if language_code not in self.translations:
            return False

        translations_dir = Path(__file__).parent.parent / 'data' / 'translations'
        translation_file = translations_dir / f'{language_code}.json'

        try:
            with open(translation_file, 'w', encoding='utf-8') as f:
                json.dump(self.translations[language_code], f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving translation file {translation_file}: {e}")
            return False

    def get_missing_translations(self, language_code: str) -> list:
        """
        Get list of keys that are missing translations for a language.

        Args:
            language_code: Language code to check

        Returns:
            List of missing translation keys
        """
        if language_code not in self.translations or 'en' not in self.translations:
            return []

        english_keys = set(self.translations['en'].keys())
        language_keys = set(self.translations[language_code].keys())

        return list(english_keys - language_keys)

    def get_translation_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get translation statistics for all languages.

        Returns:
            Dictionary with language stats
        """
        stats = {}

        if 'en' in self.translations:
            english_count = len(self.translations['en'])

            for lang_code, lang_name in self.SUPPORTED_LANGUAGES.items():
                if lang_code in self.translations:
                    lang_count = len(self.translations[lang_code])
                    completion = (lang_count / english_count * 100) if english_count > 0 else 0
                    missing = english_count - lang_count

                    stats[lang_code] = {
                        'name': lang_name,
                        'total_keys': lang_count,
                        'completion_percentage': round(completion, 1),
                        'missing_keys': missing
                    }
                else:
                    stats[lang_code] = {
                        'name': lang_name,
                        'total_keys': 0,
                        'completion_percentage': 0.0,
                        'missing_keys': english_count
                    }

        return stats