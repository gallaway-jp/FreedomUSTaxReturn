"""
Unit tests for plugin management window functionality.

Tests the plugin management interface, including:
- Plugin loading and display
- Plugin installation from files
- Marketplace browsing
- Plugin enable/disable functionality
"""

import pytest
import unittest.mock as mock
from unittest.mock import Mock, patch
import customtkinter as ctk
import tkinter as tk

from gui.plugin_management_window import PluginManagementWindow, open_plugin_management_window
from config.app_config import AppConfig
from utils.plugins import PluginRegistry, get_plugin_registry


class TestPluginManagementWindow:
    """Test cases for the plugin management window"""

    @pytest.fixture
    def mock_parent(self):
        """Create a mock parent window"""
        parent = Mock(spec=ctk.CTk)
        parent.tk = Mock()  # Add tk attribute for tkinter compatibility
        parent._last_child_ids = {}  # Add tkinter internal attribute
        parent._w = "."  # Add tkinter widget path
        parent.children = {}  # Add tkinter children dict
        parent.master = None  # Root window has no master
        return parent

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration"""
        config = Mock(spec=AppConfig)
        return config

    @pytest.fixture
    def mock_registry(self):
        """Create a mock plugin registry"""
        registry = Mock(spec=PluginRegistry)
        registry.get_all_plugins.return_value = {}
        return registry

    @patch('gui.plugin_management_window.PluginManagementWindow._setup_ui')
    @patch('gui.plugin_management_window.PluginManagementWindow._create_window')
    @patch('gui.plugin_management_window.get_plugin_registry')
    def test_window_creation(self, mock_get_registry, mock_create_window, mock_setup_ui, mock_parent, mock_config, mock_registry):
        """Test that the plugin management window can be created"""
        mock_get_registry.return_value = mock_registry

        # This should not raise an exception
        window = PluginManagementWindow(mock_parent, mock_config)

        # Verify the window was created
        assert window.config == mock_config
        assert window.plugin_registry == mock_registry
        mock_create_window.assert_called_once()
        mock_setup_ui.assert_called_once()

    @patch('gui.plugin_management_window.PluginManagementWindow._setup_ui')
    @patch('gui.plugin_management_window.PluginManagementWindow._create_window')
    @patch('gui.plugin_management_window.get_plugin_registry')
    def test_load_installed_plugins(self, mock_get_registry, mock_create_window, mock_setup_ui, mock_parent, mock_config, mock_registry):
        """Test loading and displaying installed plugins"""
        mock_get_registry.return_value = mock_registry

        window = PluginManagementWindow(mock_parent, mock_config)

        # Mock UI components
        window.window = Mock()
        window.status_label = Mock()
        window.plugins_tree = Mock()
        window.plugins_tree.get_children.return_value = []
        window.plugins_tree.insert = Mock()

        # Mock plugin info
        mock_plugin = Mock()
        mock_metadata = Mock()
        mock_metadata.name = "Test Plugin"
        mock_metadata.version = "1.0.0"
        mock_metadata.schedule_name = "Schedule C"
        mock_metadata.author = "Test Author"
        mock_plugin.get_metadata.return_value = mock_metadata

        mock_registry.get_all_plugins.return_value = {
            "schedule_c": mock_plugin
        }

        # Call the method
        window._load_installed_plugins()

        # Verify the plugin was added to the tree
        window.plugins_tree.insert.assert_called_once()
        call_args = window.plugins_tree.insert.call_args
        assert call_args[0][0] == ""  # parent
        assert call_args[0][1] == "end"  # position
        assert "Test Plugin" in call_args[1]["values"]  # values

    @patch('gui.plugin_management_window.PluginManagementWindow')
    @patch('gui.plugin_management_window.get_plugin_registry')
    def test_open_plugin_management_window(self, mock_get_registry, mock_window_class, mock_parent, mock_config, mock_registry):
        """Test the open_plugin_management_window function"""
        mock_get_registry.return_value = mock_registry

        mock_window_instance = Mock()
        mock_window_class.return_value = mock_window_instance

        # Call the function
        open_plugin_management_window(mock_parent, mock_config)

        # Verify the window was created and shown
        mock_window_class.assert_called_once_with(mock_parent, mock_config)
        mock_window_instance.show.assert_called_once()

    @patch('gui.plugin_management_window.PluginManagementWindow')
    @patch('gui.plugin_management_window.get_plugin_registry')
    def test_open_plugin_management_window_error_handling(self, mock_get_registry, mock_window_class, mock_parent, mock_config, mock_registry):
        """Test error handling in open_plugin_management_window"""
        mock_get_registry.return_value = mock_registry

        mock_window_instance = Mock()
        mock_window_instance.show.side_effect = Exception("Test error")
        mock_window_class.return_value = mock_window_instance

        with patch('gui.plugin_management_window.messagebox') as mock_messagebox:
            # Call the function
            open_plugin_management_window(mock_parent, mock_config)

            # Verify error message was shown
            mock_messagebox.showerror.assert_called_once()
            call_args = mock_messagebox.showerror.call_args
            assert call_args[0][0] == "Plugin Management Error"
            assert "Test error" in call_args[0][1]

    @patch('gui.plugin_management_window.PluginManagementWindow._setup_ui')
    @patch('gui.plugin_management_window.PluginManagementWindow._create_window')
    def test_tab_switching(self, mock_create_window, mock_setup_ui, mock_parent, mock_config):
        """Test tab switching functionality"""
        with patch('gui.plugin_management_window.get_plugin_registry'):
            window = PluginManagementWindow(mock_parent, mock_config)

            # Mock tab frames
            window.tabs = {
                "installed": Mock(),
                "marketplace": Mock(),
                "settings": Mock()
            }

            # Mock tab buttons
            window.installed_tab_btn = Mock()
            window.marketplace_tab_btn = Mock()
            window.settings_tab_btn = Mock()

            # Test switching to marketplace tab
            window._switch_tab("marketplace")

            # Verify correct tab is shown and buttons are updated
            window.tabs["installed"].pack_forget.assert_called_once()
            window.tabs["marketplace"].pack.assert_called_once()
            window.tabs["settings"].pack_forget.assert_called_once()

            # Verify button states
            window.installed_tab_btn.configure.assert_called_with(fg_color="transparent")
            window.marketplace_tab_btn.configure.assert_called_with(fg_color=["#3B8ED0", "#1F6AA5"])
            window.settings_tab_btn.configure.assert_called_with(fg_color="transparent")


class TestPluginManagementIntegration:
    """Integration tests for plugin management"""

    def test_plugin_registry_integration(self):
        """Test that plugin management integrates with the registry"""
        registry = get_plugin_registry()

        # Verify registry is accessible
        assert registry is not None
        assert hasattr(registry, 'get_all_plugins')
        assert hasattr(registry, 'register')
        assert hasattr(registry, 'unregister')

    def test_config_integration(self):
        """Test that plugin management integrates with config"""
        config = AppConfig.from_env()

        # Verify config has necessary attributes
        assert hasattr(config, 'version')
        assert hasattr(config, 'window_title')
        assert hasattr(config, 'tax_year')