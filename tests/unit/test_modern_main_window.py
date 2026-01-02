"""
Unit tests for Modern Main Window GUI integration

Tests the main window functionality including sidebar buttons,
keyboard shortcuts, and feature integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from gui.modern_main_window import ModernMainWindow
from config.app_config import AppConfig
from models.tax_data import TaxData


class TestModernMainWindowIntegration:
    """Test integration of features in the modern main window"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration"""
        config = Mock(spec=AppConfig)
        return config

    @pytest.fixture
    def mock_tax_data(self):
        """Create mock tax data"""
        tax_data = Mock(spec=TaxData)
        tax_data.get_current_year.return_value = 2026
        return tax_data

    @patch('gui.modern_main_window.ctk.CTk')
    @patch('gui.modern_main_window.AccessibilityService')
    @patch('gui.modern_main_window.TaxInterviewService')
    @patch('gui.modern_main_window.FormRecommendationService')
    @patch('gui.modern_main_window.EncryptionService')
    @patch('gui.modern_main_window.PTINEROService')
    @patch('gui.modern_main_window.AuthenticationService')
    def test_tax_analytics_button_integration(self, mock_auth, mock_ptin, mock_encrypt,
                                             mock_recommend, mock_interview, mock_accessibility,
                                             mock_ctk, mock_config, mock_tax_data):
        """Test that tax analytics button is properly integrated"""
        # Setup mocks
        mock_window = Mock()
        mock_ctk.return_value = mock_window

        # Mock services
        mock_accessibility.return_value = None
        mock_interview.return_value = Mock()
        mock_recommend.return_value = Mock()
        mock_encrypt.return_value = Mock()
        mock_ptin.return_value = Mock()
        mock_auth.return_value = Mock()

        # Create main window
        window = ModernMainWindow(mock_config, demo_mode=True)

        # Verify that _show_tax_analytics method exists
        assert hasattr(window, '_show_tax_analytics')
        assert callable(window._show_tax_analytics)

    @patch('gui.modern_main_window.TaxAnalyticsWindow')
    @patch('services.tax_calculation_service.TaxCalculationService')
    def test_show_tax_analytics_method(self, mock_calc_service, mock_analytics_window,
                                      mock_config, mock_tax_data):
        """Test the _show_tax_analytics method functionality"""
        with patch('gui.modern_main_window.ctk.CTk') as mock_ctk, \
             patch('gui.modern_main_window.AccessibilityService') as mock_access, \
             patch('gui.modern_main_window.TaxInterviewService') as mock_interview, \
             patch('gui.modern_main_window.FormRecommendationService') as mock_recommend, \
             patch('gui.modern_main_window.EncryptionService') as mock_encrypt, \
             patch('gui.modern_main_window.PTINEROService') as mock_ptin, \
             patch('gui.modern_main_window.AuthenticationService') as mock_auth:

            # Setup mocks
            mock_window = Mock()
            mock_ctk.return_value = mock_window

            # Mock services
            mock_access.return_value = None
            mock_interview.return_value = Mock()
            mock_recommend.return_value = Mock()
            mock_encrypt.return_value = Mock()
            mock_ptin.return_value = Mock()
            mock_auth.return_value = Mock()

            # Create main window
            window = ModernMainWindow(mock_config, demo_mode=True)
            window.tax_data = mock_tax_data

            # Mock the analytics window
            mock_analytics_instance = Mock()
            mock_analytics_window.return_value = mock_analytics_instance

            # Call the method
            window._show_tax_analytics()

            # Verify TaxAnalyticsWindow was created with correct parameters
            mock_analytics_window.assert_called_once()
            call_args = mock_analytics_window.call_args
            assert call_args[0][0] == window  # parent
            assert call_args[0][1] == mock_config  # config
            assert call_args[0][2] == mock_tax_data  # tax_data

            # Verify show() was called
            mock_analytics_instance.show.assert_called_once()

    @patch('gui.modern_main_window.show_error_message')
    def test_show_tax_analytics_no_data(self, mock_error_msg, mock_config):
        """Test _show_tax_analytics when no tax data exists"""
        with patch('gui.modern_main_window.ctk.CTk') as mock_ctk, \
             patch('gui.modern_main_window.AccessibilityService') as mock_access, \
             patch('gui.modern_main_window.TaxInterviewService') as mock_interview, \
             patch('gui.modern_main_window.FormRecommendationService') as mock_recommend, \
             patch('gui.modern_main_window.EncryptionService') as mock_encrypt, \
             patch('gui.modern_main_window.PTINEROService') as mock_ptin, \
             patch('gui.modern_main_window.AuthenticationService') as mock_auth:

            # Setup mocks
            mock_window = Mock()
            mock_ctk.return_value = mock_window

            # Mock services
            mock_access.return_value = None
            mock_interview.return_value = Mock()
            mock_recommend.return_value = Mock()
            mock_encrypt.return_value = Mock()
            mock_ptin.return_value = Mock()
            mock_auth.return_value = Mock()

            # Create main window
            window = ModernMainWindow(mock_config, demo_mode=True)
            window.tax_data = None  # No tax data

            # Call the method
            window._show_tax_analytics()

            # Verify error message was shown
            mock_error_msg.assert_called_once_with(
                "No Tax Data",
                "Please complete the tax interview first to view analytics."
            )

    @patch('gui.modern_main_window.TaxAnalyticsWindow')
    @patch('services.tax_calculation_service.TaxCalculationService')
    @patch('gui.modern_main_window.show_error_message')
    def test_show_tax_analytics_error_handling(self, mock_error_msg, mock_calc_service,
                                               mock_analytics_window, mock_config, mock_tax_data):
        """Test error handling in _show_tax_analytics"""
        with patch('gui.modern_main_window.ctk.CTk') as mock_ctk, \
             patch('gui.modern_main_window.AccessibilityService') as mock_access, \
             patch('gui.modern_main_window.TaxInterviewService') as mock_interview, \
             patch('gui.modern_main_window.FormRecommendationService') as mock_recommend, \
             patch('gui.modern_main_window.EncryptionService') as mock_encrypt, \
             patch('gui.modern_main_window.PTINEROService') as mock_ptin, \
             patch('gui.modern_main_window.AuthenticationService') as mock_auth:

            # Setup mocks
            mock_window = Mock()
            mock_ctk.return_value = mock_window

            # Mock services
            mock_access.return_value = None
            mock_interview.return_value = Mock()
            mock_recommend.return_value = Mock()
            mock_encrypt.return_value = Mock()
            mock_ptin.return_value = Mock()
            mock_auth.return_value = Mock()

            # Create main window
            window = ModernMainWindow(mock_config, demo_mode=True)
            window.tax_data = mock_tax_data

            # Make TaxAnalyticsWindow raise an exception
            mock_analytics_window.side_effect = Exception("Test error")

            # Call the method
            window._show_tax_analytics()

    @patch('gui.modern_main_window.show_info_message')
    @patch('gui.modern_main_window.show_error_message')
    def test_save_progress_with_data(self, mock_error_msg, mock_info_msg, mock_config, mock_tax_data):
        """Test _save_progress method with valid tax data"""
        with patch('gui.modern_main_window.ctk.CTk') as mock_ctk, \
             patch('gui.modern_main_window.AccessibilityService') as mock_access, \
             patch('gui.modern_main_window.TaxInterviewService') as mock_interview, \
             patch('gui.modern_main_window.FormRecommendationService') as mock_recommend, \
             patch('gui.modern_main_window.EncryptionService') as mock_encrypt, \
             patch('gui.modern_main_window.PTINEROService') as mock_ptin, \
             patch('gui.modern_main_window.AuthenticationService') as mock_auth:

            # Setup mocks
            mock_window = Mock()
            mock_ctk.return_value = mock_window

            # Mock services
            mock_access.return_value = None
            mock_interview.return_value = Mock()
            mock_recommend.return_value = Mock()
            mock_encrypt.return_value = Mock()
            mock_ptin.return_value = Mock()
            mock_auth.return_value = Mock()

            # Create main window
            window = ModernMainWindow(mock_config, demo_mode=True)
            window.tax_data = mock_tax_data

            # Mock the save_to_file method
            mock_tax_data.save_to_file.return_value = "/path/to/saved/file.enc"

            # Call the method
            window._save_progress()

            # Verify save_to_file was called
            mock_tax_data.save_to_file.assert_called_once()
            call_args = mock_tax_data.save_to_file.call_args
            assert call_args[0][0].startswith("progress_2026_")  # Should start with progress_2026_
            assert call_args[0][0].endswith(".enc")  # Should end with .enc

            # Verify success message was shown
            mock_info_msg.assert_called_once()
            call_args = mock_info_msg.call_args
            assert call_args[0][0] == "Progress Saved"
            assert "has been saved successfully" in call_args[0][1]

    @patch('gui.modern_main_window.show_error_message')
    def test_save_progress_no_data(self, mock_error_msg, mock_config):
        """Test _save_progress method with no tax data"""
        with patch('gui.modern_main_window.ctk.CTk') as mock_ctk, \
             patch('gui.modern_main_window.AccessibilityService') as mock_access, \
             patch('gui.modern_main_window.TaxInterviewService') as mock_interview, \
             patch('gui.modern_main_window.FormRecommendationService') as mock_recommend, \
             patch('gui.modern_main_window.EncryptionService') as mock_encrypt, \
             patch('gui.modern_main_window.PTINEROService') as mock_ptin, \
             patch('gui.modern_main_window.AuthenticationService') as mock_auth:

            # Setup mocks
            mock_window = Mock()
            mock_ctk.return_value = mock_window

            # Mock services
            mock_access.return_value = None
            mock_interview.return_value = Mock()
            mock_recommend.return_value = Mock()
            mock_encrypt.return_value = Mock()
            mock_ptin.return_value = Mock()
            mock_auth.return_value = Mock()

            # Create main window (no tax_data set)
            window = ModernMainWindow(mock_config, demo_mode=True)

            # Call the method
            window._save_progress()

            # Verify error message was shown
            mock_error_msg.assert_called_once()
            call_args = mock_error_msg.call_args
            assert call_args[0][0] == "No Data"
            assert "start the tax interview first" in call_args[0][1]