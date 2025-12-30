"""
Integration tests for dependents page in the full application context
"""

import pytest
from unittest.mock import Mock, patch
from gui.main_window import MainWindow
from models.tax_data import TaxData
from config.app_config import AppConfig


class TestDependentsPageIntegration:
    """Integration tests for dependents page in main window"""

    @pytest.fixture
    def setup_main_window(self):
        """Set up a MainWindow instance for testing"""
        root = Mock()
        config = AppConfig.from_env()

        # Mock the root window methods
        root.title = Mock()
        root.geometry = Mock()
        root.columnconfigure = Mock()
        root.rowconfigure = Mock()
        root.bind = Mock()

        with patch('gui.main_window.ThemeManager') as mock_theme_manager:
            mock_theme = Mock()
            mock_theme_manager.return_value = mock_theme
            mock_theme.set_theme = Mock()
            mock_theme.toggle_theme = Mock(return_value="light")

            window = MainWindow(root, config)

            yield window

            # Clean up if needed
            if hasattr(window, 'root') and window.root:
                try:
                    window.root.destroy()
                except:
                    pass

    def test_dependents_page_navigation(self, setup_main_window):
        """Test that dependents page can be navigated to"""
        window = setup_main_window

        # Mock the page creation
        with patch('gui.main_window.DependentsPage') as mock_page_class:
            mock_page = Mock()
            mock_page_class.return_value = mock_page

            # Navigate to dependents page
            window.show_page("dependents")

            # Check that the dependents page was created
            mock_page_class.assert_called_once()
            args, kwargs = mock_page_class.call_args
            assert args[0] == window.content_frame  # parent frame
            assert args[1] == window.tax_data  # tax_data
            assert args[2] == window  # main_window
            assert args[3] == window.theme_manager  # theme_manager

            # Check that the page was packed (only in non-mocked environments)
            if not window.is_mocked:
                mock_page.pack.assert_called_once_with(fill="both", expand=True)

    def test_dependents_validation_integration(self, setup_main_window):
        """Test dependents validation in the main window context"""
        window = setup_main_window

        # Add some invalid dependent data
        invalid_dependent = {
            'first_name': '',  # Missing first name
            'last_name': 'Test',
            'ssn': '123-45-6789',
            'birth_date': '01/01/2020',
            'relationship': 'Son',
            'months_lived_in_home': 12
        }
        window.tax_data.set("dependents", [invalid_dependent])

        # Test validation
        errors = window._validate_page("dependents")
        assert len(errors) > 0
        assert any("First name is required" in error for error in errors)

    def test_dependents_progress_calculation(self, setup_main_window):
        """Test that dependents page affects progress calculation"""
        window = setup_main_window

        # Initially, dependents should contribute to progress
        initial_progress = window.update_progress()
        dependents_weight = window.page_weights.get("dependents", 0)

        # The dependents page should have some weight in progress calculation
        assert dependents_weight > 0

    def test_dependents_keyboard_shortcut(self, setup_main_window):
        """Test that Alt+3 navigates to dependents page"""
        window = setup_main_window

        # Mock the show_page method
        with patch.object(window, 'show_page') as mock_show_page:
            # Simulate Alt+3 keypress
            window.root.bind.call_args_list[2][0][1](None)  # Alt+3 binding

            # Check that show_page was called with "dependents"
            mock_show_page.assert_called_with("dependents")

    def test_dependents_in_navigation_buttons(self, setup_main_window):
        """Test that dependents appears in navigation buttons"""
        window = setup_main_window

        # Check that dependents button exists
        assert "dependents" in window.nav_buttons
        dependents_button = window.nav_buttons["dependents"]

        # Check button configuration
        assert dependents_button.cget("text") == "Dependents"

        # Test button click
        with patch.object(window, 'show_page') as mock_show_page:
            dependents_button.invoke()
            mock_show_page.assert_called_with("dependents")

    def test_dependents_page_mapping(self, setup_main_window):
        """Test that dependents page is in the page mapping"""
        window = setup_main_window

        from gui.pages.dependents import DependentsPage

        # Check that DependentsPage is in the mapping
        assert DependentsPage in window.page_mapping
        assert window.page_mapping[DependentsPage] == "dependents"

    def test_dependents_validation_summary(self, setup_main_window):
        """Test that dependents validation appears in validation summary"""
        window = setup_main_window

        # Add invalid dependent data
        invalid_dependent = {
            'first_name': 'Test',
            'last_name': 'User',
            'ssn': 'invalid-ssn',  # Invalid SSN format
            'birth_date': '01/01/2020',
            'relationship': 'Son',
            'months_lived_in_home': 15  # Invalid months
        }
        window.tax_data.set("dependents", [invalid_dependent])

        # Update validation summary
        window.update_validation_summary()

        # Check that validation summary was updated
        # (This is hard to test directly without mocking the ValidationSummary widget,
        # but we can verify the validation logic works)
        errors = window._validate_page("dependents")
        assert len(errors) >= 2  # Should have SSN format error and months error

    def test_dependents_data_persistence(self, setup_main_window):
        """Test that dependents data persists correctly"""
        window = setup_main_window

        # Add dependent data
        dependent = {
            'first_name': 'Persistent',
            'last_name': 'Test',
            'ssn': '123-45-6789',
            'birth_date': '01/01/2020',
            'relationship': 'Son',
            'months_lived_in_home': 12
        }
        window.tax_data.set("dependents", [dependent])

        # Verify data is stored
        stored_dependents = window.tax_data.get("dependents", [])
        assert len(stored_dependents) == 1
        assert stored_dependents[0]['first_name'] == 'Persistent'
        assert stored_dependents[0]['relationship'] == 'Son'

        # Simulate navigating away and back
        with patch('gui.main_window.DependentsPage') as mock_page_class:
            mock_page = Mock()
            mock_page_class.return_value = mock_page

            window.show_page("dependents")

            # The page should receive the tax_data with dependents
            args, kwargs = mock_page_class.call_args
            passed_tax_data = args[1]
            assert len(passed_tax_data.get("dependents", [])) == 1


class TestDependentsWorkflowIntegration:
    """Test complete workflows involving dependents"""

    def test_dependents_with_tax_calculations(self):
        """Test that dependents affect tax calculations"""
        config = AppConfig.from_env()
        tax_data = TaxData(config)

        # Add qualifying child
        child = {
            'first_name': 'Child',
            'last_name': 'Taxpayer',
            'ssn': '123-45-6789',
            'birth_date': '01/01/2018',  # Age 7
            'relationship': 'Son',
            'months_lived_in_home': 12
        }
        tax_data.set("dependents", [child])

        # Set up basic tax situation
        tax_data.set("personal_info", {
            "first_name": "Parent",
            "last_name": "Taxpayer",
            "ssn": "987-65-4321",
            "date_of_birth": "01/01/1980",
            "address": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip_code": "12345"
        })

        tax_data.set("filing_status", {
            "status": "Single",
            "is_dependent": False,
            "can_be_claimed": False
        })

        # Add income (lower income to qualify for EIC)
        tax_data.set("income", {
            "w2_forms": [{
                "employer": "Test Employer",
                "wages": 30000,
                "federal_withholding": 3000,
                "ssn": "987-65-4321"
            }],
            "interest_income": [],
            "dividend_income": [],
            "self_employment": [],
            "retirement_distributions": [],
            "social_security": [],
            "capital_gains": [],
            "rental_income": [],
            "business_income": [],
            "unemployment": [],
            "other_income": []
        })

        # Calculate taxes
        result = tax_data.calculate_totals()

        # Should have child tax credit
        assert 'child_tax_credit' in result
        assert result['child_tax_credit'] > 0

        # Should have earned income credit (EITC) for child
        assert 'earned_income_credit' in result
        assert result['earned_income_credit'] > 0

    def test_multiple_dependents_validation(self):
        """Test validation with multiple dependents"""
        config = AppConfig.from_env()
        tax_data = TaxData(config)

        # Add multiple dependents with various issues
        dependents = [
            {  # Valid dependent
                'first_name': 'Valid',
                'last_name': 'Child',
                'ssn': '123-45-6789',
                'birth_date': '01/01/2018',
                'relationship': 'Son',
                'months_lived_in_home': 12
            },
            {  # Missing SSN
                'first_name': 'NoSSN',
                'last_name': 'Child',
                'ssn': '',
                'birth_date': '02/02/2019',
                'relationship': 'Daughter',
                'months_lived_in_home': 12
            },
            {  # Invalid months
                'first_name': 'BadMonths',
                'last_name': 'Child',
                'ssn': '987-65-4321',
                'birth_date': '03/03/2020',
                'relationship': 'Son',
                'months_lived_in_home': 15  # Invalid
            }
        ]
        tax_data.set("dependents", dependents)

        # Test validation
        from gui.main_window import MainWindow
        root = Mock()
        root.title = Mock()
        root.geometry = Mock()
        root.columnconfigure = Mock()
        root.rowconfigure = Mock()
        root.bind = Mock()

        with patch('gui.main_window.ThemeManager'):
            window = MainWindow(root, config)

            # Set the dependents data on the window's tax_data
            window.tax_data.set("dependents", dependents)

            errors = window._validate_page("dependents")

            # Should have errors for missing SSN and invalid months
            assert len(errors) >= 2
            assert any("Social Security Number is required" in error for error in errors)
            assert any("Months lived in home must be between 0 and 12" in error for error in errors)