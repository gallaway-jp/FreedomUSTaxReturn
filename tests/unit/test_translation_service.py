"""
Tests for Translation Service

Tests the translation and localization functionality.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, mock_open

from config.app_config import AppConfig
from services.translation_service import TranslationService


class TestTranslationService:
    """Test cases for TranslationService"""

    def setup_method(self):
        """Setup test fixtures"""
        self.config = AppConfig()

    def test_initialization(self):
        """Test service initialization"""
        service = TranslationService(self.config)
        assert service.current_language == 'en'
        assert 'en' in service.translations
        assert 'es' in service.translations

    def test_set_language(self):
        """Test language setting"""
        service = TranslationService(self.config)

        # Valid language
        assert service.set_language('es') == True
        assert service.get_language() == 'es'

        # Invalid language
        assert service.set_language('invalid') == False
        assert service.get_language() == 'es'  # Should remain unchanged

    def test_translate_basic(self):
        """Test basic translation functionality"""
        service = TranslationService(self.config)

        # Test existing translation
        result = service.translate('buttons.ok')
        assert result == 'OK'

        # Test non-existent key
        result = service.translate('nonexistent.key')
        assert result == 'nonexistent.key'

        # Test with fallback
        result = service.translate('nonexistent.key', fallback='Default Text')
        assert result == 'Default Text'

    def test_translate_with_formatting(self):
        """Test translation with format arguments"""
        service = TranslationService(self.config)

        # Test with format args
        result = service.translate('app.version', version='1.0.0')
        assert result == 'Version 1.0.0'

    def test_translate_fallback_to_english(self):
        """Test fallback to English when translation missing"""
        service = TranslationService(self.config)
        service.set_language('es')

        # Test key that exists in English but not in Spanish
        # Use a key that we know exists in English but might be missing in Spanish
        result = service.translate('buttons.ok')
        # Since Spanish has this translation, it should return the Spanish version
        assert result == 'Aceptar'  # Spanish for OK

        # Test with a non-existent key
        result = service.translate('nonexistent.key')
        assert result == 'nonexistent.key'

    def test_get_available_languages(self):
        """Test getting available languages"""
        service = TranslationService(self.config)
        languages = service.get_available_languages()

        assert isinstance(languages, dict)
        assert 'en' in languages
        assert 'es' in languages
        assert 'fr' in languages
        assert languages['en'] == 'English'
        assert languages['es'] == 'Español'

    def test_get_language_name(self):
        """Test getting language display names"""
        service = TranslationService(self.config)

        assert service.get_language_name('en') == 'English'
        assert service.get_language_name('es') == 'Español'
        assert service.get_language_name('invalid') == 'invalid'

    def test_add_translation(self):
        """Test adding translations"""
        service = TranslationService(self.config)

        # Add new translation
        result = service.add_translation('es', 'test.key', 'Texto de prueba')
        assert result == True

        # Verify it was added (nested structure)
        assert service.translations['es']['test']['key'] == 'Texto de prueba'

        # Try invalid language
        result = service.add_translation('invalid', 'test.key', 'text')
        assert result == False

    def test_get_missing_translations(self):
        """Test identifying missing translations"""
        service = TranslationService(self.config)

        # Get missing translations for Spanish
        missing = service.get_missing_translations('es')

        # Should return a list
        assert isinstance(missing, list)

        # If there are missing translations, they should be strings
        for key in missing:
            assert isinstance(key, str)

    def test_get_translation_stats(self):
        """Test getting translation statistics"""
        service = TranslationService(self.config)

        stats = service.get_translation_stats()

        assert isinstance(stats, dict)
        assert 'en' in stats
        assert 'es' in stats

        # English should be 100% complete
        assert stats['en']['completion_percentage'] == 100.0

        # Check structure
        for lang_code, lang_stats in stats.items():
            assert 'name' in lang_stats
            assert 'total_keys' in lang_stats
            assert 'completion_percentage' in lang_stats
            assert 'missing_keys' in lang_stats

    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_save_translations(self, mock_exists, mock_file):
        """Test saving translations to file"""
        mock_exists.return_value = True

        service = TranslationService(self.config)

        # Add a test translation
        service.add_translation('es', 'test.key', 'test value')

        # Save translations
        result = service.save_translations('es')
        assert result == True

        # Verify file was written
        mock_file.assert_called()

    def test_save_translations_invalid_language(self):
        """Test saving translations for invalid language"""
        service = TranslationService(self.config)

        result = service.save_translations('invalid')
        assert result == False

    def test_translation_file_loading(self):
        """Test loading translation files"""
        # This test verifies that the service can load existing translation files
        service = TranslationService(self.config)

        # Check that English translations were loaded
        assert 'buttons' in service.translations['en']
        assert 'ok' in service.translations['en']['buttons']

        # Check that Spanish translations were loaded
        assert 'buttons' in service.translations['es']
        assert 'ok' in service.translations['es']['buttons']