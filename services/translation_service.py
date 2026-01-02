"""
Translation and Localization Service

Provides internationalization (i18n) support for the Freedom US Tax Return application.
Uses Babel library for professional translation management with .po/.mo files.
"""

import gettext
import locale
import os
from typing import Dict, Optional, Any
from pathlib import Path
from config.app_config import AppConfig


class TranslationService:
    """
    Service for managing translations and localization using Babel.

    Features:
    - Multiple language support using Babel
    - Fallback to English for missing translations
    - Dynamic language switching
    - Professional .po/.mo file management
    """

    # Supported languages with Babel locale codes
    SUPPORTED_LANGUAGES = {
        'en': ('en', 'English'),
        'es': ('es', 'Español'),
        'fr': ('fr', 'Français'),
        'de': ('de', 'Deutsch'),
        'zh': ('zh', '中文'),
        'ja': ('ja', '日本語'),
        'ko': ('ko', '한국어'),
        'pt': ('pt', 'Português'),
        'it': ('it', 'Italiano'),
        'ru': ('ru', 'Русский')
    }

    def __init__(self, config: AppConfig):
        """
        Initialize translation service.

        Args:
            config: Application configuration
        """
        self.config = config
        self.current_language = config.default_language  # Use language from config
        if self.current_language == 'system':
            self.current_language = 'en'
        self._translators: Dict[str, Optional[gettext.GNUTranslations]] = {}
        self._load_translators()

    def _load_translators(self):
        """Load translation files for all supported languages"""
        locale_dir = Path(__file__).parent.parent / 'locale'

        for lang_code, (babel_locale, _) in self.SUPPORTED_LANGUAGES.items():
            try:
                translator = gettext.translation(
                    'messages',
                    localedir=str(locale_dir),
                    languages=[babel_locale],
                    fallback=True
                )
                self._translators[lang_code] = translator
            except FileNotFoundError:
                # No translation file found, use null translator
                self._translators[lang_code] = None

    def set_language(self, language_code: str) -> bool:
        """
        Set the current language.

        Args:
            language_code: ISO language code (e.g., 'en', 'es', 'fr') or 'system' for default

        Returns:
            True if language was set successfully, False otherwise
        """
        if language_code == 'system':
            # System default maps to English
            self.current_language = 'en'
            return True
        elif language_code in self.SUPPORTED_LANGUAGES:
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
        if code in self.SUPPORTED_LANGUAGES:
            return self.SUPPORTED_LANGUAGES[code][1]
        return code

    def translate(self, key: str, fallback: Optional[str] = None, language_code: Optional[str] = None, **kwargs) -> str:
        """
        Translate a key to the specified or current language.

        Args:
            key: Translation key
            fallback: Fallback text if translation not found
            language_code: Specific language code to translate to, or None for current language
            **kwargs: Format arguments for the translation

        Returns:
            Translated text
        """
        target_language = language_code or self.current_language
        translator = self._translators.get(target_language)

        if translator:
            # Try to translate
            translated = translator.gettext(key)
            if translated != key:  # Translation found
                return translated.format(**kwargs) if kwargs else translated

        # Try English fallback if not already using English
        if target_language != 'en':
            english_translator = self._translators.get('en')
            if english_translator:
                translated = english_translator.gettext(key)
                if translated != key:  # Translation found
                    return translated.format(**kwargs) if kwargs else translated

        # Use fallback or key itself
        text = fallback or key
        return text.format(**kwargs) if kwargs else text

    def get_available_languages(self) -> Dict[str, str]:
        """Get dictionary of available language codes and names"""
        return {code: name for code, (_, name) in self.SUPPORTED_LANGUAGES.items()}

    def get_missing_translations(self, language_code: str) -> list:
        """
        Get list of keys that are missing translations for a language.

        Args:
            language_code: Language code to check

        Returns:
            List of missing translation keys
        """
        if language_code not in self.SUPPORTED_LANGUAGES:
            return []

        english_translator = self._translators.get('en')
        target_translator = self._translators.get(language_code)

        if not english_translator or not target_translator:
            return []

        if not hasattr(english_translator, '_catalog') or not hasattr(target_translator, '_catalog'):
            return []

        # Get all English keys
        english_keys = set(k for k in english_translator._catalog.keys() if k and k.strip())

        # Get translated keys in target language (where msgstr != msgid)
        translated_keys = set(k for k, v in target_translator._catalog.items()
                            if k and k.strip() and v and v != k)

        # Missing keys are those in English but not properly translated in target language
        missing_keys = english_keys - translated_keys

        return sorted(list(missing_keys))

    def get_translation_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get translation statistics for all languages.

        Returns:
            Dictionary with language stats
        """
        stats = {}

        # Get total keys from English (assuming English has all keys)
        english_translator = self._translators.get('en')
        total_keys = 0
        if english_translator and hasattr(english_translator, '_catalog'):
            # Count all non-empty msgid entries (excluding header)
            total_keys = len([k for k in english_translator._catalog.keys()
                            if k and k.strip()])

        for lang_code, (_, lang_name) in self.SUPPORTED_LANGUAGES.items():
            translator = self._translators.get(lang_code)

            if translator and hasattr(translator, '_catalog'):
                # Count translated entries (where msgstr is different from msgid)
                translated_keys = len([k for k, v in translator._catalog.items()
                                     if k and k.strip() and v and v != k])
                completion = (translated_keys / total_keys * 100) if total_keys > 0 else 0
                missing = total_keys - translated_keys

                stats[lang_code] = {
                    'name': lang_name,
                    'total_keys': translated_keys,
                    'completion_percentage': round(completion, 1),
                    'missing_keys': missing
                }
            else:
                stats[lang_code] = {
                    'name': lang_name,
                    'total_keys': 0,
                    'completion_percentage': 0.0,
                    'missing_keys': total_keys
                }

        return stats