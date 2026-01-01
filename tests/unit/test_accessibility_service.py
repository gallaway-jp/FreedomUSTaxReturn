"""
Unit tests for Accessibility Service

Tests comprehensive accessibility features including WCAG 2.1 AA compliance,
Section 508 requirements, and screen reader support.
"""

import unittest
import os
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
import tkinter as tk

from services.accessibility_service import (
    AccessibilityService,
    AccessibilityLevel,
    ColorScheme,
    AccessibilityProfile
)
from config.app_config import AppConfig
from services.encryption_service import EncryptionService


class TestAccessibilityProfile(unittest.TestCase):
    """Test AccessibilityProfile class"""

    def test_profile_initialization(self):
        """Test profile initializes with correct defaults"""
        profile = AccessibilityProfile()

        self.assertEqual(profile.level, AccessibilityLevel.AA)
        self.assertEqual(profile.color_scheme, ColorScheme.DEFAULT)
        self.assertEqual(profile.font_size, 12)
        self.assertFalse(profile.high_contrast)
        self.assertFalse(profile.screen_reader)
        self.assertTrue(profile.keyboard_navigation)
        self.assertTrue(profile.focus_indicators)
        self.assertFalse(profile.reduced_motion)
        self.assertFalse(profile.large_click_targets)
        self.assertTrue(profile.auto_complete)
        self.assertTrue(profile.tooltips_enabled)
        self.assertTrue(profile.announce_changes)

    def test_custom_colors_initialization(self):
        """Test custom colors are properly initialized"""
        profile = AccessibilityProfile()

        expected_colors = {
            'bg': '#000000',
            'fg': '#FFFFFF',
            'button_bg': '#FFFFFF',
            'button_fg': '#000000',
            'entry_bg': '#FFFFFF',
            'entry_fg': '#000000',
            'focus_bg': '#FFFF00',
            'focus_fg': '#000000'
        }

        self.assertEqual(profile.custom_colors, expected_colors)


class TestAccessibilityService(unittest.TestCase):
    """Test AccessibilityService functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()

        # Mock config
        self.config = Mock(spec=AppConfig)
        self.config.safe_dir = self.temp_dir

        # Mock encryption service with proper return values
        self.encryption = Mock(spec=EncryptionService)
        self.encryption.encrypt_dict.return_value = {"encrypted": "data"}
        self.encryption.decrypt_dict.return_value = {
            'level': 'AA',
            'color_scheme': 'DEFAULT',
            'font_size': 16,
            'high_contrast': True,
            'screen_reader': False,
            'keyboard_navigation': True,
            'focus_indicators': True,
            'reduced_motion': False,
            'large_click_targets': False,
            'auto_complete': True,
            'tooltips_enabled': True,
            'announce_changes': True,
            'custom_colors': {'bg': '#000000', 'fg': '#FFFFFF', 'button_bg': '#FFFFFF', 'button_fg': '#000000', 'entry_bg': '#FFFFFF', 'entry_fg': '#000000', 'focus_bg': '#FFFF00', 'focus_fg': '#000000'}
        }

        # Create service
        self.service = AccessibilityService(self.config, self.encryption)

    def tearDown(self):
        """Clean up test fixtures"""
        # Remove test files
        profile_file = os.path.join(self.temp_dir, "accessibility_profile.json")
        if os.path.exists(profile_file):
            os.remove(profile_file)
        os.rmdir(self.temp_dir)

    def test_service_initialization(self):
        """Test service initializes correctly"""
        self.assertIsInstance(self.service.profile, AccessibilityProfile)
        self.assertEqual(self.service.config, self.config)
        self.assertEqual(self.service.encryption, self.encryption)

    def test_profile_file_path(self):
        """Test profile file path is set correctly"""
        expected_path = os.path.join(self.temp_dir, "accessibility_profile.json")
        self.assertEqual(self.service.profile_file, expected_path)

    def test_save_and_load_profile(self):
        """Test saving and loading accessibility profile"""
        # Modify profile
        self.service.profile.font_size = 16
        self.service.profile.high_contrast = True
        self.service.profile.level = AccessibilityLevel.AAA

        # Configure mock to return the saved data
        self.encryption.decrypt_dict.return_value = {
            'level': 'aaa',
            'color_scheme': 'default',
            'font_size': 16,
            'high_contrast': True,
            'screen_reader': False,
            'keyboard_navigation': True,
            'focus_indicators': True,
            'reduced_motion': False,
            'large_click_targets': False,
            'auto_complete': True,
            'tooltips_enabled': True,
            'announce_changes': True,
            'custom_colors': {'bg': '#000000', 'fg': '#FFFFFF', 'button_bg': '#FFFFFF', 'button_fg': '#000000', 'entry_bg': '#FFFFFF', 'entry_fg': '#000000', 'focus_bg': '#FFFF00', 'focus_fg': '#000000'}
        }

        # Save profile
        self.service.save_profile()

        # Create new service instance (simulates restart)
        new_service = AccessibilityService(self.config, self.encryption)

        # Verify profile was loaded
        self.assertEqual(new_service.profile.font_size, 16)
        self.assertTrue(new_service.profile.high_contrast)
        self.assertEqual(new_service.profile.level, AccessibilityLevel.AAA)

    def test_update_profile(self):
        """Test updating profile settings"""
        # Update multiple settings
        self.service.update_profile(
            font_size=18,
            high_contrast=True,
            keyboard_navigation=False
        )

        self.assertEqual(self.service.profile.font_size, 18)
        self.assertTrue(self.service.profile.high_contrast)
        self.assertFalse(self.service.profile.keyboard_navigation)

    def test_get_color_scheme_default(self):
        """Test getting default color scheme"""
        self.service.profile.color_scheme = ColorScheme.DEFAULT
        colors = self.service.get_color_scheme()

        expected_colors = {
            'bg': '#F0F0F0',
            'fg': '#000000',
            'button_bg': '#E1E1E1',
            'button_fg': '#000000',
            'entry_bg': '#FFFFFF',
            'entry_fg': '#000000',
            'focus_bg': '#0078D4',
            'focus_fg': '#FFFFFF'
        }

        self.assertEqual(colors, expected_colors)

    def test_get_color_scheme_high_contrast(self):
        """Test getting high contrast color scheme"""
        self.service.profile.color_scheme = ColorScheme.HIGH_CONTRAST
        colors = self.service.get_color_scheme()

        # Should return custom colors
        self.assertEqual(colors['bg'], '#000000')
        self.assertEqual(colors['fg'], '#FFFFFF')

    def test_get_color_scheme_dark_mode(self):
        """Test getting dark mode color scheme"""
        self.service.profile.color_scheme = ColorScheme.DARK_MODE
        colors = self.service.get_color_scheme()

        expected_colors = {
            'bg': '#2B2B2B',
            'fg': '#FFFFFF',
            'button_bg': '#404040',
            'button_fg': '#FFFFFF',
            'entry_bg': '#404040',
            'entry_fg': '#FFFFFF',
            'focus_bg': '#0078D4',
            'focus_fg': '#FFFFFF'
        }

        self.assertEqual(colors, expected_colors)

    def test_get_font_settings(self):
        """Test getting font settings"""
        self.service.profile.font_size = 14
        fonts = self.service.get_font_settings()

        expected_fonts = {
            'family': 'Segoe UI',
            'size': 14,
            'weight': 'normal',
            'large_size': 18,
            'heading_size': 22
        }

        self.assertEqual(fonts, expected_fonts)

    def test_set_accessibility_level(self):
        """Test setting accessibility level"""
        self.service.set_accessibility_level(AccessibilityLevel.AAA)
        self.assertEqual(self.service.profile.level, AccessibilityLevel.AAA)

    def test_set_color_scheme(self):
        """Test setting color scheme"""
        self.service.set_color_scheme(ColorScheme.DARK_MODE)
        self.assertEqual(self.service.profile.color_scheme, ColorScheme.DARK_MODE)

    def test_set_font_size(self):
        """Test setting font size with clamping"""
        # Test normal size
        self.service.set_font_size(16)
        self.assertEqual(self.service.profile.font_size, 16)

        # Test minimum clamping
        self.service.set_font_size(5)
        self.assertEqual(self.service.profile.font_size, 10)

        # Test maximum clamping
        self.service.set_font_size(30)
        self.assertEqual(self.service.profile.font_size, 24)

    def test_toggle_high_contrast(self):
        """Test toggling high contrast mode"""
        # Initially false
        self.assertFalse(self.service.profile.high_contrast)

        # Toggle on
        self.service.toggle_high_contrast()
        self.assertTrue(self.service.profile.high_contrast)

        # Toggle off
        self.service.toggle_high_contrast()
        self.assertFalse(self.service.profile.high_contrast)

    def test_toggle_keyboard_navigation(self):
        """Test toggling keyboard navigation"""
        # Initially true
        self.assertTrue(self.service.profile.keyboard_navigation)

        # Toggle off
        self.service.toggle_keyboard_navigation()
        self.assertFalse(self.service.profile.keyboard_navigation)

        # Toggle on
        self.service.toggle_keyboard_navigation()
        self.assertTrue(self.service.profile.keyboard_navigation)

    def test_enable_screen_reader_mode(self):
        """Test enabling screen reader mode"""
        # Initially false
        self.assertFalse(self.service.profile.screen_reader)

        # Enable
        self.service.enable_screen_reader_mode(True)
        self.assertTrue(self.service.profile.screen_reader)

        # Disable
        self.service.enable_screen_reader_mode(False)
        self.assertFalse(self.service.profile.screen_reader)

    def test_get_keyboard_shortcuts(self):
        """Test getting keyboard shortcuts"""
        shortcuts = self.service.get_keyboard_shortcuts()

        expected_shortcuts = {
            'Tab': 'Move to next focusable element',
            'Shift+Tab': 'Move to previous focusable element',
            'Enter/Space': 'Activate button or select item',
            'Escape': 'Close dialog or cancel action',
            'Ctrl+S': 'Save current work',
            'Ctrl+O': 'Open file',
            'Ctrl+N': 'New document',
            'F1': 'Help',
            'Alt+F4': 'Close application'
        }

        self.assertEqual(shortcuts, expected_shortcuts)

    def test_announce_change(self):
        """Test announcing changes for screen readers"""
        with patch.object(self.service.logger, 'info') as mock_log:
            self.service.profile.announce_changes = True
            self.service.profile.screen_reader = True

            self.service.announce_change("Test message")

            mock_log.assert_called_once_with("Accessibility announcement: Test message")

    def test_get_compliance_report(self):
        """Test generating compliance report"""
        report = self.service.get_compliance_report()

        # Check structure
        self.assertIn('compliance_level', report)
        self.assertIn('features_enabled', report)
        self.assertIn('color_scheme', report)
        self.assertIn('font_size', report)
        self.assertIn('estimated_compliance', report)

        # Check values
        self.assertEqual(report['compliance_level'], 'aa')
        self.assertEqual(report['color_scheme'], 'default')
        self.assertEqual(report['font_size'], 12)
        self.assertIsInstance(report['estimated_compliance'], float)

    def test_validate_accessibility_basic_widget(self):
        """Test basic accessibility validation"""
        # Create a mock widget
        widget = Mock()
        widget.cget = Mock(side_effect=lambda key: {
            'takefocus': True,
            'bg': '#FFFFFF',
            'fg': '#000000'
        }.get(key, None))

        # Mock accessible attributes
        widget.accessible_name = "Test Widget"

        issues = self.service.validate_accessibility(widget)

        # Should have no issues for a properly configured widget
        self.assertEqual(len(issues), 0)

    def test_validate_accessibility_missing_name(self):
        """Test validation detects missing accessible name"""
        widget = Mock()
        widget.cget = Mock(return_value=True)
        # Configure mock to not have accessible_name attribute
        delattr(widget, 'accessible_name')

        issues = self.service.validate_accessibility(widget)

        self.assertIn("Missing accessible name/label", issues)

    def test_validate_accessibility_no_keyboard_access(self):
        """Test validation detects lack of keyboard access"""
        widget = Mock()
        widget.cget = Mock(side_effect=lambda key: {
            'takefocus': False,
            'bg': '#FFFFFF',
            'fg': '#000000'
        }.get(key, None))
        widget.accessible_name = "Test Widget"

        issues = self.service.validate_accessibility(widget)

        self.assertIn("Widget not keyboard accessible", issues)

    @patch('tkinter.Tk')
    def test_make_accessible_basic(self, mock_tk):
        """Test making a widget accessible"""
        # Create mock widget
        widget = Mock()
        widget.accessible_name = None
        widget.accessible_description = None
        widget.accessible_role = None

        # Make accessible
        self.service.make_accessible(widget, label="Test Label", description="Test Description", role="button")

        self.assertEqual(widget.accessible_name, "Test Label")
        self.assertEqual(widget.accessible_description, "Test Description")
        self.assertEqual(widget.accessible_role, "button")

    def test_encryption_integration(self):
        """Test that profile data is encrypted when saved"""
        # Setup encryption mock
        self.encryption.encrypt_dict.return_value = '{"encrypted": "data"}'

        # Save profile
        self.service.save_profile()

        # Verify encryption was called
        self.encryption.encrypt_dict.assert_called_once()

        # Verify file was created
        self.assertTrue(os.path.exists(self.service.profile_file))

    def test_encryption_decryption_on_load(self):
        """Test that profile data is decrypted when loaded"""
        # Setup encryption mock
        self.encryption.decrypt_dict.return_value = '{"font_size": 20, "high_contrast": true}'

        # Create a file with "encrypted" data
        with open(self.service.profile_file, 'w') as f:
            json.dump({"dummy": "data"}, f)

        # Create new service (should load and decrypt)
        new_service = AccessibilityService(self.config, self.encryption)

        # Verify decryption was called
        self.encryption.decrypt_dict.assert_called_once()

    def test_profile_persistence_error_handling(self):
        """Test error handling when profile persistence fails"""
        # Make directory read-only to cause save error
        os.chmod(self.temp_dir, 0o444)

        try:
            # This should not raise an exception
            self.service.save_profile()
        finally:
            # Restore permissions
            os.chmod(self.temp_dir, 0o755)

    def test_font_size_bounds(self):
        """Test font size is properly bounded"""
        # Test lower bound
        self.service.set_font_size(8)
        self.assertEqual(self.service.profile.font_size, 10)

        # Test upper bound
        self.service.set_font_size(26)
        self.assertEqual(self.service.profile.font_size, 24)

        # Test valid range
        self.service.set_font_size(16)
        self.assertEqual(self.service.profile.font_size, 16)


if __name__ == '__main__':
    unittest.main()