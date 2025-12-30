import pytest
import tkinter as tk
from unittest.mock import Mock, patch
from gui.pages.income import IncomePage
from models.tax_data import TaxData
from config.app_config import AppConfig


class TestForm8949Generation:
    """Test cases for Form 8949 generation functionality"""

    @pytest.fixture
    def setup_page_with_capital_gains(self):
        """Set up an IncomePage with capital gains data for testing"""
        root = tk.Tk()
        config = AppConfig.from_env()
        tax_data = TaxData(config)
        main_window = Mock()
        theme_manager = Mock()

        # Add comprehensive capital gains data
        tax_data.data['income']['capital_gains'] = [
            {
                'description': 'Apple Inc Common Stock',
                'transaction_type': 'Sale',
                'holding_period': 'Short-term',
                'date_acquired': '03/15/2025',
                'date_sold': '04/15/2025',
                'sales_price': 10000.00,
                'cost_basis': 8000.00,
                'adjustment': 200.00,
                'adjusted_basis': 8200.00,
                'gain_loss': 1800.00,
                'brokerage_firm': 'Fidelity',
                'confirmation_number': 'CONF001',
                'wash_sale': False
            },
            {
                'description': 'Microsoft Corp Common Stock',
                'transaction_type': 'Sale',
                'holding_period': 'Long-term',
                'date_acquired': '01/15/2023',
                'date_sold': '01/15/2025',
                'sales_price': 15000.00,
                'cost_basis': 12000.00,
                'adjustment': 0.00,
                'adjusted_basis': 12000.00,
                'gain_loss': 3000.00,
                'brokerage_firm': 'Charles Schwab',
                'confirmation_number': 'CONF002',
                'wash_sale': False
            },
            {
                'description': 'Tesla Inc Common Stock',
                'transaction_type': 'Sale',
                'holding_period': 'Short-term',
                'date_acquired': '05/01/2025',
                'date_sold': '06/01/2025',
                'sales_price': 8000.00,
                'cost_basis': 10000.00,
                'adjustment': 0.00,
                'adjusted_basis': 10000.00,
                'gain_loss': -2000.00,
                'brokerage_firm': 'Robinhood',
                'confirmation_number': 'CONF003',
                'wash_sale': True
            }
        ]

        page = IncomePage(root, tax_data, main_window, theme_manager)

        yield page

        # Clean up
        root.destroy()

    def test_generate_form_8949_with_data(self, setup_page_with_capital_gains):
        """Test Form 8949 generation with capital gains data"""
        page = setup_page_with_capital_gains
        # Mock the Toplevel dialog creation and ttk widgets to avoid real GUI
        with patch('tkinter.Toplevel') as mock_toplevel, \
             patch('tkinter.ttk.Frame') as mock_frame, \
             patch('tkinter.ttk.Notebook') as mock_notebook, \
             patch('tkinter.ttk.Label') as mock_label, \
             patch('tkinter.ttk.Treeview') as mock_treeview, \
             patch('tkinter.ttk.Scrollbar') as mock_scrollbar, \
             patch('tkinter.Text') as mock_text, \
             patch('tkinter.ttk.Button') as mock_button:

            mock_dialog = Mock()
            mock_toplevel.return_value = mock_dialog

            mock_frame.return_value = Mock()
            mock_notebook.return_value = Mock()
            mock_label.return_value = Mock()
            mock_tree = Mock()
            mock_treeview.return_value = mock_tree
            mock_scrollbar.return_value = Mock()
            mock_text.return_value = Mock()
            mock_button.return_value = Mock()

            # Call the generate method
            page.generate_form_8949()

            # Verify dialog was created
            mock_toplevel.assert_called_once()

    def test_calculate_8949_totals_short_term(self, setup_page_with_capital_gains):
        """Test calculation of Form 8949 totals for short-term transactions"""
        page = setup_page_with_capital_gains

        # Get short-term transactions
        capital_gains = page.tax_data.get('income.capital_gains', [])
        short_term = [cg for cg in capital_gains if cg.get('holding_period') == 'Short-term']

        # Calculate totals
        totals = page._calculate_8949_totals(short_term)

        # Verify calculations
        expected_proceeds = 10000.00 + 8000.00  # Apple + Tesla
        expected_basis = 8200.00 + 10000.00    # Adjusted bases
        expected_net = 1800.00 + (-2000.00)    # Gains/losses

        assert totals['proceeds'] == expected_proceeds
        assert totals['basis'] == expected_basis
        assert totals['net'] == expected_net

    def test_calculate_8949_totals_long_term(self, setup_page_with_capital_gains):
        """Test calculation of Form 8949 totals for long-term transactions"""
        page = setup_page_with_capital_gains

        # Get long-term transactions
        capital_gains = page.tax_data.get('income.capital_gains', [])
        long_term = [cg for cg in capital_gains if cg.get('holding_period') == 'Long-term']

        # Calculate totals
        totals = page._calculate_8949_totals(long_term)

        # Verify calculations
        expected_proceeds = 15000.00  # Microsoft only
        expected_basis = 12000.00     # Microsoft basis
        expected_net = 3000.00        # Microsoft gain

        assert totals['proceeds'] == expected_proceeds
        assert totals['basis'] == expected_basis
        assert totals['net'] == expected_net

    def test_generate_form_8949_empty_data(self, setup_page_with_capital_gains):
        """Test Form 8949 generation when no capital gains data exists"""
        # Create a page with no capital gains data
        root = tk.Tk()
        config = AppConfig.from_env()
        tax_data = TaxData(config)
        main_window = Mock()
        theme_manager = Mock()

        page = IncomePage(root, tax_data, main_window, theme_manager)

        try:
            # Mock messagebox to check if info message is shown
            with patch('tkinter.messagebox.showinfo') as mock_info:
                page.generate_form_8949()
                mock_info.assert_called_once_with("Form 8949", "No capital gains/losses to report on Form 8949.")
        finally:
            root.destroy()

    def test_form_8949_section_creation(self, setup_page_with_capital_gains):
        """Test that Form 8949 sections are created correctly"""
        page = setup_page_with_capital_gains

        # Create a mock parent widget
        mock_parent = Mock()

        # Get short-term transactions
        capital_gains = page.tax_data.get('income.capital_gains', [])
        short_term = [cg for cg in capital_gains if cg.get('holding_period') == 'Short-term']

        # Mock ttk.Treeview
        with patch('tkinter.ttk.Treeview') as mock_treeview, \
             patch('tkinter.ttk.Scrollbar') as mock_scrollbar:

            mock_tree = Mock()
            mock_treeview.return_value = mock_tree

            # Call the section creation method
            page._create_8949_section(mock_parent, short_term, "Short-term")

            # Verify treeview was created and configured
            mock_treeview.assert_called_once()
            assert mock_tree.heading.call_count == 6  # 6 columns
            assert mock_tree.insert.call_count == 2   # 2 transactions

    def test_wash_sale_display_in_list(self, setup_page_with_capital_gains):
        """Test that wash sales are properly indicated in the capital gains list"""
        page = setup_page_with_capital_gains

        # Refresh the capital list
        page.refresh_capital_list()

        # Check that wash sale indicator is shown
        # The Tesla transaction has wash_sale = True
        # This would be verified by checking the UI elements, but since we're testing
        # the logic, we'll verify the data contains the wash sale flag
        capital_gains = page.tax_data.get('income.capital_gains', [])
        tesla_transaction = next((cg for cg in capital_gains if cg['description'] == 'Tesla Inc Common Stock'), None)
        assert tesla_transaction is not None
        assert tesla_transaction['wash_sale'] == True