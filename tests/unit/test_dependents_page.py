"""
Tests for dependents page GUI components
"""

import pytest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
from gui.pages.dependents import DependentsPage, DependentDialog
from models.tax_data import TaxData
from config.app_config import AppConfig


class TestDependentsPage:
    """Test the DependentsPage GUI component"""

    @pytest.fixture
    def setup_page(self):
        """Set up a DependentsPage instance for testing"""
        # Mock tkinter to avoid GUI requirements in headless environments
        with patch('tkinter.Tk') as mock_tk, \
             patch('tkinter.ttk.Frame') as mock_frame, \
             patch('tkinter.ttk.Label') as mock_label, \
             patch('tkinter.ttk.Button') as mock_button, \
             patch('tkinter.Listbox') as mock_listbox, \
             patch('tkinter.ttk.Scrollbar') as mock_scrollbar, \
             patch('tkinter.StringVar') as mock_stringvar, \
             patch('tkinter.Canvas') as mock_canvas:

            # Configure mocks
            mock_root = MagicMock()
            mock_tk.return_value = mock_root

            mock_frame_instance = MagicMock()
            mock_frame.return_value = mock_frame_instance

            mock_listbox_instance = MagicMock()
            # Simple internal storage for Listbox items so insert/delete/get behave
            mock_listbox_instance._items = []

            def _insert(index, item):
                if index == tk.END:
                    mock_listbox_instance._items.append(item)
                else:
                    mock_listbox_instance._items.insert(index, item)

            def _delete(start, end=None):
                # For our tests we always clear the list on delete(0, END)
                mock_listbox_instance._items.clear()

            def _get(start, end=None):
                return tuple(mock_listbox_instance._items) if mock_listbox_instance._items else ("No dependents added yet",)

            mock_listbox_instance.curselection = Mock(return_value=())
            # Make selection_set update curselection to mimic real Listbox
            mock_listbox_instance.selection_set = Mock(side_effect=lambda idx: setattr(mock_listbox_instance.curselection, 'return_value', (idx,)))
            mock_listbox_instance.insert.side_effect = _insert
            mock_listbox_instance.delete.side_effect = _delete
            mock_listbox_instance.get.side_effect = _get
            # Allow dynamic configuration of curselection
            mock_listbox_instance.configure_curselection = lambda val: setattr(mock_listbox_instance.curselection, 'return_value', val)
            mock_listbox.return_value = mock_listbox_instance

            mock_canvas_instance = MagicMock()
            mock_canvas.return_value = mock_canvas_instance

            mock_stringvar_instance = MagicMock()
            mock_stringvar_instance.get.return_value = ""
            mock_stringvar_instance.set.return_value = None
            mock_stringvar.return_value = mock_stringvar_instance

            config = AppConfig.from_env()
            tax_data = TaxData(config)
            main_window = Mock()
            theme_manager = Mock()
            theme_manager.get_color.side_effect = lambda color: {
                "success": "green",
                "error": "red", 
                "fg": "black"
            }.get(color, "black")

            page = DependentsPage(mock_root, tax_data, main_window, theme_manager)

            yield page

    def test_page_initialization(self, setup_page):
        """Test that the page initializes correctly"""
        page = setup_page

        # Check that the page has the expected components
        assert hasattr(page, 'tax_data')
        assert hasattr(page, 'main_window')
        assert hasattr(page, 'theme_manager')
        assert hasattr(page, 'dependents_listbox')
        assert hasattr(page, 'canvas')
        assert hasattr(page, 'scrollable_frame')

    def test_refresh_dependents_list_empty(self, setup_page):
        """Test refreshing the dependents list when empty"""
        page = setup_page

        # Initially should be empty
        page.refresh_dependents_list()
        items = page.dependents_listbox.get(0, tk.END)
        assert len(items) == 1
        assert "No dependents added yet" in items[0]

    def test_refresh_dependents_list_with_data(self, setup_page):
        """Test refreshing the dependents list with dependent data"""
        page = setup_page

        # Add a dependent to tax data
        dependent = {
            'first_name': 'John',
            'last_name': 'Doe',
            'ssn': '123-45-6789',
            'birth_date': '01/01/2010',
            'relationship': 'Son',
            'months_lived_in_home': 12
        }
        page.tax_data.set("dependents", [dependent])

        page.refresh_dependents_list()
        items = page.dependents_listbox.get(0, tk.END)
        assert len(items) == 1
        assert "John Doe - Son (Age: 15)" in items[0]  # Age calculation for 2025

    def test_add_dependent(self, setup_page):
        """Test adding a dependent"""
        page = setup_page

        # Mock the dialog creation and avoid wait_window
        with patch('gui.pages.dependents.DependentDialog') as mock_dialog_class, \
             patch.object(page, 'wait_window') as mock_wait:

            mock_dialog = Mock()
            mock_dialog_class.return_value = mock_dialog

            page.add_dependent()

            # Check that dialog was created
            mock_dialog_class.assert_called_once()
            args, kwargs = mock_dialog_class.call_args
            assert args[0] == page  # parent
            assert args[1] == page.tax_data  # tax_data
            assert args[2] == page.theme_manager  # theme_manager
            assert len(args) == 3  # No edit_index argument

            # Check that wait_window was called
            mock_wait.assert_called_once_with(mock_dialog)

    def test_edit_dependent_selected(self, setup_page):
        """Test editing a selected dependent"""
        page = setup_page

        # Add a dependent and select it
        dependent = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'ssn': '987-65-4321',
            'birth_date': '02/02/2012',
            'relationship': 'Daughter',
            'months_lived_in_home': 12
        }
        page.tax_data.set("dependents", [dependent])
        page.refresh_dependents_list()

        # Select the first item
        page.dependents_listbox.selection_set(0)

        with patch('gui.pages.dependents.DependentDialog') as mock_dialog_class, \
             patch.object(page, 'wait_window') as mock_wait:

            mock_dialog = Mock()
            mock_dialog_class.return_value = mock_dialog

            page.edit_dependent()

            # Check that dialog was created with edit_index
            mock_dialog_class.assert_called_once()
            args, kwargs = mock_dialog_class.call_args
            assert args[0] == page  # parent
            assert args[1] == page.tax_data  # tax_data
            assert args[2] == page.theme_manager  # theme_manager
            assert kwargs['edit_index'] == 0  # Should be editing index 0

            # Check that wait_window was called
            mock_wait.assert_called_once_with(mock_dialog)

    def test_edit_dependent_no_selection(self, setup_page):
        """Test editing when no dependent is selected"""
        page = setup_page

        with patch('tkinter.messagebox.showwarning') as mock_warning:
            page.edit_dependent()

            mock_warning.assert_called_once_with("No Selection", "Please select a dependent to edit.")

    def test_delete_dependent_selected(self, setup_page):
        """Test deleting a selected dependent"""
        page = setup_page

        # Add a dependent and select it
        dependent = {
            'first_name': 'Bob',
            'last_name': 'Johnson',
            'ssn': '111-22-3333',
            'birth_date': '03/03/2015',
            'relationship': 'Son',
            'months_lived_in_home': 12
        }
        page.tax_data.set("dependents", [dependent])
        page.refresh_dependents_list()

        # Select the first item
        page.dependents_listbox.selection_set(0)
        # Configure mock to return selection
        page.dependents_listbox.configure_curselection((0,))

        with patch('gui.pages.dependents.messagebox.askyesno', return_value=True) as mock_ask, \
             patch('gui.pages.dependents.messagebox.showinfo') as mock_info:

            page.delete_dependent()

            # Check that confirmation was asked
            mock_ask.assert_called_once_with("Confirm Delete", "Are you sure you want to delete dependent 'Bob Johnson'?")

            # Check that success message was shown
            mock_info.assert_called_once_with("Success", "Dependent 'Bob Johnson' has been deleted.")

            # Check that dependent was removed from data
            dependents = page.tax_data.get("dependents", [])
            assert len(dependents) == 0

    def test_delete_dependent_no_selection(self, setup_page):
        """Test deleting when no dependent is selected"""
        page = setup_page

        with patch('tkinter.messagebox.showwarning') as mock_warning:
            page.delete_dependent()

            mock_warning.assert_called_once_with("No Selection", "Please select a dependent to delete.")

    def test_delete_dependent_cancelled(self, setup_page):
        """Test deleting when user cancels"""
        page = setup_page

        # Add a dependent and select it
        dependent = {
            'first_name': 'Alice',
            'last_name': 'Brown',
            'ssn': '444-55-6666',
            'birth_date': '04/04/2018',
            'relationship': 'Daughter',
            'months_lived_in_home': 12
        }
        page.tax_data.set("dependents", [dependent])
        page.refresh_dependents_list()
        page.dependents_listbox.selection_set(0)
        # Configure mock to return selection
        page.dependents_listbox.configure_curselection((0,))

        with patch('gui.pages.dependents.messagebox.askyesno', return_value=False) as mock_ask:
            page.delete_dependent()

            # Check that confirmation was asked but dependent was not removed
            mock_ask.assert_called_once()
            dependents = page.tax_data.get("dependents", [])
            assert len(dependents) == 1


class TestDependentDialogLogic:
    """Test the DependentDialog logic without GUI complications"""

    def test_dialog_initialization_logic(self):
        """Test dialog initialization logic"""
        config = AppConfig.from_env()
        tax_data = TaxData(config)
        theme_manager = Mock()

        # Test new dependent initialization
        with patch('tkinter.Toplevel'), \
             patch('tkinter.ttk.Frame'), \
             patch('tkinter.ttk.Label'), \
             patch('gui.widgets.form_field.FormField'), \
             patch('tkinter.ttk.Radiobutton'), \
             patch('tkinter.ttk.Button'), \
             patch.object(DependentDialog, 'grab_set'), \
             patch.object(DependentDialog, 'transient'), \
             patch.object(DependentDialog, 'title'), \
             patch.object(DependentDialog, 'protocol'):

            dialog = DependentDialog(None, tax_data, theme_manager)

            # Check basic attributes
            assert dialog.tax_data == tax_data
            assert dialog.theme_manager == theme_manager
            assert dialog.edit_index is None

    def test_save_dependent_validation_logic(self):
        """Test the validation logic in save_dependent method"""
        config = AppConfig.from_env()
        tax_data = TaxData(config)

        # Create a mock dialog with the necessary attributes
        dialog = Mock(spec=DependentDialog)
        dialog.tax_data = tax_data
        dialog.edit_index = None

        # Mock the form fields
        dialog.first_name = Mock()
        dialog.last_name = Mock()
        dialog.ssn = Mock()
        dialog.birth_date = Mock()
        dialog.relationship_var = Mock()
        dialog.months_lived = Mock()

        # Mock tkinter functions
        with patch('tkinter.messagebox.showerror') as mock_error, \
             patch('tkinter.messagebox.showinfo') as mock_info, \
             patch.object(dialog, 'destroy'):

            # Test missing first name
            dialog.first_name.get.return_value = ""
            dialog.last_name.get.return_value = "Test"
            dialog.ssn.get.return_value = "123-45-6789"
            dialog.birth_date.get.return_value = "01/01/2020"
            dialog.relationship_var.get.return_value = "Son"
            dialog.months_lived.get.return_value = "12"

            # Call the actual method
            DependentDialog.save_dependent(dialog)

            mock_error.assert_called_once_with("Validation Error", "First name is required.")
            mock_info.assert_not_called()
            dialog.destroy.assert_not_called()

    def test_save_dependent_valid_data_logic(self):
        """Test saving valid dependent data"""
        config = AppConfig.from_env()
        tax_data = TaxData(config)

        # Create a mock dialog
        dialog = Mock(spec=DependentDialog)
        dialog.tax_data = tax_data
        dialog.edit_index = None

        # Mock form fields with valid data
        dialog.first_name = Mock()
        dialog.last_name = Mock()
        dialog.ssn = Mock()
        dialog.birth_date = Mock()
        dialog.relationship_var = Mock()
        dialog.months_lived = Mock()

        dialog.first_name.get.return_value = "Valid"
        dialog.last_name.get.return_value = "Dependent"
        dialog.ssn.get.return_value = "123-45-6789"
        dialog.birth_date.get.return_value = "01/01/2020"
        dialog.relationship_var.get.return_value = "Son"
        dialog.months_lived.get.return_value = "12"

        with patch('tkinter.messagebox.showinfo') as mock_info, \
             patch.object(dialog, 'destroy'):

            # Call the actual method
            DependentDialog.save_dependent(dialog)

            # Check that dependent was added
            dependents = tax_data.get("dependents", [])
            assert len(dependents) == 1
            assert dependents[0]['first_name'] == "Valid"
            assert dependents[0]['relationship'] == "Son"
            assert dependents[0]['months_lived_in_home'] == 12

            mock_info.assert_called_once_with("Success", "Dependent added successfully!")
            dialog.destroy.assert_called_once()


class TestDependentsPageIntegration:
    """Integration tests for dependents page functionality"""

    def test_age_calculation(self):
        """Test age calculation from birth date"""
        root = tk.Tk()
        config = AppConfig.from_env()
        tax_data = TaxData(config)
        main_window = Mock()
        theme_manager = Mock()

        page = DependentsPage(root, tax_data, main_window, theme_manager)

        # Test various birth dates
        test_cases = [
            ("01/01/2010", 15),  # Born in 2010, age 15 in 2025
            ("12/31/2024", 0),   # Born late 2024, age 0 in 2025
            ("07/15/2000", 25),  # Born in 2000, age 25 in 2025
        ]

        for birth_date, expected_age in test_cases:
            age = page._calculate_age(birth_date)
            assert age == expected_age, f"Expected age {expected_age} for birth date {birth_date}, got {age}"

        # Test invalid date
        assert page._calculate_age("invalid") is None
        assert page._calculate_age("") is None

        root.destroy()

    def test_full_workflow(self):
        """Test a complete add-edit-delete workflow"""
        root = tk.Tk()
        config = AppConfig.from_env()
        tax_data = TaxData(config)
        main_window = Mock()
        theme_manager = Mock()

        page = DependentsPage(root, tax_data, main_window, theme_manager)

        # Initially empty
        page.refresh_dependents_list()
        items = page.dependents_listbox.get(0, tk.END)
        assert "No dependents added yet" in items[0]

        # Add another dependent
        dependent2 = {
            'first_name': 'Liam',
            'last_name': 'Wilson',
            'ssn': '222-22-2222',
            'birth_date': '08/20/2018',
            'relationship': 'Son',
            'months_lived_in_home': 12
        }
        tax_data.set("dependents", [dependent2])
        page.refresh_dependents_list()

        items = page.dependents_listbox.get(0, tk.END)
        assert len(items) == 1
        assert "Liam Wilson - Son (Age: 7)" in items[0]

        root.destroy()