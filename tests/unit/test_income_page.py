import pytest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
from gui.pages.income import IncomePage
from models.tax_data import TaxData
from config.app_config import AppConfig


class TestIncomePage:
    """Test cases for the IncomePage class"""

    @pytest.fixture
    def setup_page(self):
        """Set up an IncomePage instance for testing"""
        root = tk.Tk()
        config = AppConfig.from_env()
        tax_data = TaxData(config)
        main_window = Mock()
        theme_manager = Mock()

        page = IncomePage(root, tax_data, main_window, theme_manager)

        yield page

        # Clean up
        root.destroy()

    def test_income_page_initialization(self, setup_page):
        """Test that IncomePage initializes correctly"""
        page = setup_page
        assert page is not None
        assert hasattr(page, 'tax_data')
        assert hasattr(page, 'main_window')
        assert hasattr(page, 'se_list_frame')

    def test_refresh_se_list_empty(self, setup_page):
        """Test refreshing self-employment list with no businesses"""
        page = setup_page
        page.refresh_se_list()
        # Should not crash with empty list
        assert True

    def test_refresh_se_list_with_businesses(self, setup_page):
        """Test refreshing self-employment list with businesses"""
        page = setup_page
        # Add some test business data
        page.tax_data.data['income']['self_employment'] = [
            {
                'business_name': 'Test Business',
                'net_profit': 50000.0
            }
        ]
        page.refresh_se_list()
        # Should not crash with business data
        assert True

    @patch('gui.pages.income.SelfEmploymentDialog')
    @patch.object(IncomePage, 'wait_window')
    def test_add_self_employment_opens_dialog(self, mock_wait, mock_dialog, setup_page):
        """Test that add self-employment button creates dialog"""
        page = setup_page
        # Mock the dialog
        mock_instance = Mock()
        mock_dialog.return_value = mock_instance

        # Call the add method
        page.add_self_employment()

        # Verify dialog was created
        mock_dialog.assert_called_once_with(page, page.tax_data, page.theme_manager)
        mock_wait.assert_called_once_with(mock_instance)

    @patch('gui.pages.income.SelfEmploymentDialog')
    @patch.object(IncomePage, 'wait_window')
    def test_edit_self_employment_opens_dialog(self, mock_wait, mock_dialog, setup_page):
        """Test that edit self-employment button creates dialog with index"""
        page = setup_page
        # Add test business data
        page.tax_data.data['income']['self_employment'] = [
            {
                'business_name': 'Existing Business',
                'net_profit': 30000.0
            }
        ]
        page.refresh_se_list()

        # Mock the dialog
        mock_instance = Mock()
        mock_dialog.return_value = mock_instance

        # Call the edit method directly with index 0
        page.edit_self_employment(0)

        # Verify dialog was created with edit_index
        mock_dialog.assert_called_once_with(page, page.tax_data, page.theme_manager, edit_index=0)
        mock_wait.assert_called_once_with(mock_instance)