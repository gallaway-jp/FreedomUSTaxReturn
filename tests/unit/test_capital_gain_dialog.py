import pytest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
from gui.pages.income import CapitalGainDialog
from models.tax_data import TaxData
from config.app_config import AppConfig


class TestCapitalGainDialog:
    """Test cases for the CapitalGainDialog class"""

    @pytest.fixture
    def setup_dialog(self):
        """Set up a CapitalGainDialog instance for testing"""
        # Skip GUI tests if Tkinter is not properly configured
        try:
            test_root = tk.Tk()
            test_root.destroy()
        except tk.TclError:
            pytest.skip("Tkinter not properly configured for GUI tests")

        root = tk.Tk()
        config = AppConfig.from_env()
        tax_data = TaxData(config)
        theme_manager = Mock()
        theme_manager.get_color.side_effect = lambda color: {
            "success": "green",
            "error": "red",
            "fg": "black"
        }.get(color, "black")

        # Create dialog without showing it
        dialog = CapitalGainDialog(root, tax_data, theme_manager)

        yield dialog

        # Clean up
        root.destroy()

    @pytest.fixture
    def setup_dialog_with_data(self):
        """Set up a CapitalGainDialog with existing data for editing"""
        # Skip GUI tests if Tkinter is not properly configured
        try:
            test_root = tk.Tk()
            test_root.destroy()
        except tk.TclError:
            pytest.skip("Tkinter not properly configured for GUI tests")

        root = tk.Tk()
        config = AppConfig.from_env()
        tax_data = TaxData(config)
        theme_manager = Mock()
        theme_manager.get_color.side_effect = lambda color: {
            "success": "green",
            "error": "red",
            "fg": "black"
        }.get(color, "black")

        # Add some existing capital gains data
        current_year = tax_data.get_current_year()
        tax_data.data['years'][current_year]['income']['capital_gains'] = [
            {
                'description': 'Apple Inc Common Stock',
                'transaction_type': 'Sale',
                'holding_period': 'Long-term',
                'date_acquired': '01/15/2024',
                'date_sold': '01/15/2025',
                'sales_price': 10000.00,
                'cost_basis': 5000.00,
                'adjustment': 0.00,
                'adjusted_basis': 5000.00,
                'gain_loss': 5000.00,
                'brokerage_firm': 'Fidelity',
                'confirmation_number': 'CONF123',
                'wash_sale': False
            }
        ]

        # Create dialog for editing
        dialog = CapitalGainDialog(root, tax_data, theme_manager, edit_index=0)

        yield dialog

        # Clean up
        root.destroy()

    def test_capital_gain_dialog_initialization(self, setup_dialog):
        """Test that CapitalGainDialog initializes correctly"""
        dialog = setup_dialog
        assert dialog is not None
        assert hasattr(dialog, 'tax_data')
        assert hasattr(dialog, 'notebook')
        assert dialog.title() == "Add/Edit Capital Gain/Loss (Form 8949)"

    def test_capital_gain_dialog_with_existing_data(self, setup_dialog_with_data):
        """Test that CapitalGainDialog loads existing data correctly"""
        dialog = setup_dialog_with_data

        # Check that existing data is loaded
        assert dialog.description.get() == 'Apple Inc Common Stock'
        assert dialog.transaction_type.get() == 'Sale'
        assert dialog.holding_period.get() == 'Long-term'
        from datetime import date
        assert dialog.date_acquired.get() == date(2024, 1, 15)
        assert dialog.date_sold.get() == date(2025, 1, 15)
        assert dialog.sales_price.get() == '$10,000.00'
        assert dialog.cost_basis.get() == '$5,000.00'
        assert dialog.adjustment.get() == '$0.00'
        assert dialog.brokerage_firm.get() == 'Fidelity'
        assert dialog.confirmation_number.get() == 'CONF123'
        assert dialog.wash_sale.get() == False

    def test_gain_loss_calculation(self, setup_dialog):
        """Test that gain/loss is calculated correctly"""
        dialog = setup_dialog

        # Set test values
        dialog.sales_price.entry.delete(0, tk.END)
        dialog.sales_price.entry.insert(0, '10000')
        dialog.cost_basis.entry.delete(0, tk.END)
        dialog.cost_basis.entry.insert(0, '5000')
        dialog.adjustment.entry.delete(0, tk.END)
        dialog.adjustment.entry.insert(0, '0')

        # Trigger calculation
        dialog._recalculate_gain_loss()

        # Check result
        assert dialog.calculated_gain_loss.get() == '$5,000.00'

    def test_gain_loss_calculation_with_adjustment(self, setup_dialog):
        """Test gain/loss calculation with basis adjustment"""
        dialog = setup_dialog

        # Set test values with adjustment
        dialog.sales_price.entry.delete(0, tk.END)
        dialog.sales_price.entry.insert(0, '10000')
        dialog.cost_basis.entry.delete(0, tk.END)
        dialog.cost_basis.entry.insert(0, '5000')
        dialog.adjustment.entry.delete(0, tk.END)
        dialog.adjustment.entry.insert(0, '500')  # Adjustment reduces basis

        # Trigger calculation
        dialog._recalculate_gain_loss()

        # Check result (10000 - (5000 + 500) = 4500)
        assert dialog.calculated_gain_loss.get() == '$4,500.00'

    def test_loss_calculation(self, setup_dialog):
        """Test that losses are calculated correctly"""
        dialog = setup_dialog

        # Set test values for a loss
        dialog.sales_price.entry.delete(0, tk.END)
        dialog.sales_price.entry.insert(0, '5000')
        dialog.cost_basis.entry.delete(0, tk.END)
        dialog.cost_basis.entry.insert(0, '10000')
        dialog.adjustment.entry.delete(0, tk.END)
        dialog.adjustment.entry.insert(0, '0')

        # Trigger calculation
        dialog._recalculate_gain_loss()

        # Check result
        assert dialog.calculated_gain_loss.get() == '$-5,000.00'

    @patch('tkinter.messagebox.showerror')
    def test_save_capital_gain_validation_error(self, mock_messagebox, setup_dialog):
        """Test that validation errors are handled"""
        dialog = setup_dialog

        # Set invalid data
        dialog.sales_price.entry.delete(0, tk.END)
        dialog.sales_price.entry.insert(0, 'invalid')
        dialog.cost_basis.entry.delete(0, tk.END)
        dialog.cost_basis.entry.insert(0, '5000')

        # Try to save
        dialog.save_capital_gain()

        # Should show error message
        mock_messagebox.assert_called_once()

    def test_save_capital_gain_new_entry(self, setup_dialog):
        """Test saving a new capital gain entry"""
        dialog = setup_dialog

        # Set valid data
        dialog.description.entry.delete(0, tk.END)
        dialog.description.entry.insert(0, 'Test Stock')
        dialog.date_acquired.entry.delete(0, tk.END)
        dialog.date_acquired.entry.insert(0, '01/01/2024')
        dialog.date_sold.entry.delete(0, tk.END)
        dialog.date_sold.entry.insert(0, '01/01/2025')
        dialog.sales_price.entry.delete(0, tk.END)
        dialog.sales_price.entry.insert(0, '10000')
        dialog.cost_basis.entry.delete(0, tk.END)
        dialog.cost_basis.entry.insert(0, '8000')
        dialog.adjustment.entry.delete(0, tk.END)
        dialog.adjustment.entry.insert(0, '200')

        # Mock the destroy method
        dialog.destroy = Mock()

        # Save the entry
        dialog.save_capital_gain()

        # Check that data was added to tax_data
        capital_gains = dialog.tax_data.get('income.capital_gains', [])
        assert len(capital_gains) == 1
        assert capital_gains[0]['description'] == 'Test Stock'
        assert capital_gains[0]['gain_loss'] == 1800.00  # 10000 - (8000 + 200)

        # Check that dialog was closed
        dialog.destroy.assert_called_once()

    def test_save_capital_gain_edit_entry(self, setup_dialog_with_data):
        """Test saving an edited capital gain entry"""
        dialog = setup_dialog_with_data

        # Modify existing data
        dialog.description.entry.delete(0, tk.END)
        dialog.description.entry.insert(0, 'Modified Apple Inc Common Stock')

        # Mock the destroy method
        dialog.destroy = Mock()

        # Save the entry
        dialog.save_capital_gain()

        # Check that data was updated
        capital_gains = dialog.tax_data.get('income.capital_gains', [])
        assert len(capital_gains) == 1
        assert capital_gains[0]['description'] == 'Modified Apple Inc Common Stock'

        # Check that dialog was closed
        dialog.destroy.assert_called_once()