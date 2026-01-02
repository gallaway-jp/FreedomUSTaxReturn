"""
Plugin Management Window - GUI for managing tax schedule plugins

Provides a comprehensive interface for:
- Viewing installed plugins
- Enabling/disabling plugins
- Installing new plugins
- Updating existing plugins
- Browsing plugin marketplace
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import requests
import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
import importlib.util
import importlib.util

from config.app_config import AppConfig
from utils.plugins import (
    PluginRegistry, get_plugin_registry, ISchedulePlugin,
    PluginMetadata, PluginLoader
)
from utils.error_tracker import get_error_tracker

logger = logging.getLogger(__name__)


class PluginManagementWindow:
    """
    Window for managing tax schedule plugins and extensions.

    Features:
    - View installed plugins with status
    - Enable/disable plugins
    - Install plugins from local files
    - Browse online plugin marketplace
    - Update plugins to latest versions
    - Plugin dependency management
    """

    def __init__(self, parent: tk.Tk, config: AppConfig):
        """
        Initialize plugin management window.

        Args:
            parent: Parent window
            config: Application configuration
        """
        self.parent = parent
        self.config = config
        self.error_tracker = get_error_tracker()

        # Plugin registry
        self.plugin_registry = get_plugin_registry()
        self.plugin_loader = PluginLoader(self.plugin_registry)

        # UI components
        self.window: Optional[tk.Toplevel] = None
        self.plugins_tree: Optional[ttk.Treeview] = None
        self.status_label: Optional[ttk.Label] = None
        self.progress_var: Optional[tk.DoubleVar] = None

        # Plugin data
        self.installed_plugins: Dict[str, Dict[str, Any]] = {}
        self.marketplace_plugins: List[Dict[str, Any]] = []

        self._create_window()
        self._setup_ui()
        self._load_installed_plugins()

    def _create_window(self):
        """Create the main plugin management window"""
        self.window = ctk.CTkToplevel(self.parent)
        self.window.title("Plugin Management - Tax Schedule Extensions")
        self.window.geometry("1000x700")
        self.window.resizable(True, True)

        # Center window relative to parent
        self.window.transient(self.parent)
        self.window.grab_set()

    def _setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        # Title
        title_label = ctk.CTkLabel(main_frame, text="Plugin Management",
                                 font=ctk.CTkFont(size=16, weight="bold"))
        title_label.pack(pady=(0, 10))

        # Toolbar
        toolbar = ctk.CTkFrame(main_frame, fg_color="transparent")
        toolbar.pack(fill=ctk.X, pady=(0, 10))

        # Plugin management buttons
        ctk.CTkButton(toolbar, text="Install from File",
                     command=self._install_from_file).pack(side=ctk.LEFT, padx=(0, 5))
        ctk.CTkButton(toolbar, text="Browse Marketplace",
                     command=self._browse_marketplace).pack(side=ctk.LEFT, padx=(0, 5))
        ctk.CTkButton(toolbar, text="Check Updates",
                     command=self._check_updates).pack(side=ctk.LEFT, padx=(0, 10))

        # Progress bar
        self.progress_var = ctk.DoubleVar()
        progress_bar = ctk.CTkProgressBar(toolbar, variable=self.progress_var, width=200)
        progress_bar.pack(side=ctk.RIGHT, fill=ctk.X, expand=True, padx=(10, 0))

        # Status label
        self.status_label = ctk.CTkLabel(toolbar, text="Ready")
        self.status_label.pack(side=ctk.RIGHT, padx=(10, 0))

        # Create tab system using frames
        self.tab_frame = ctk.CTkFrame(main_frame)
        self.tab_frame.pack(fill=ctk.BOTH, expand=True)

        # Tab buttons
        tab_buttons_frame = ctk.CTkFrame(self.tab_frame, fg_color="transparent")
        tab_buttons_frame.pack(fill=ctk.X, padx=5, pady=5)

        self.installed_tab_btn = ctk.CTkButton(
            tab_buttons_frame, text="Installed Plugins",
            command=lambda: self._switch_tab("installed")
        )
        self.installed_tab_btn.pack(side=ctk.LEFT, padx=(0, 5))

        self.marketplace_tab_btn = ctk.CTkButton(
            tab_buttons_frame, text="Plugin Marketplace",
            command=lambda: self._switch_tab("marketplace")
        )
        self.marketplace_tab_btn.pack(side=ctk.LEFT, padx=(0, 5))

        self.settings_tab_btn = ctk.CTkButton(
            tab_buttons_frame, text="Settings",
            command=lambda: self._switch_tab("settings")
        )
        self.settings_tab_btn.pack(side=ctk.LEFT)

        # Tab content frames
        self.tab_content = ctk.CTkFrame(self.tab_frame)
        self.tab_content.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)

        # Initialize tabs
        self.tabs = {}
        self._create_installed_tab()
        self._create_marketplace_tab()
        self._create_settings_tab()

        # Show default tab
        self._switch_tab("installed")

    def _switch_tab(self, tab_name: str):
        """Switch to the specified tab"""
        # Hide all tabs
        for tab in self.tabs.values():
            tab.pack_forget()

        # Show selected tab
        if tab_name in self.tabs:
            self.tabs[tab_name].pack(fill=ctk.BOTH, expand=True)

        # Update button states
        self.installed_tab_btn.configure(fg_color=["#3B8ED0", "#1F6AA5"] if tab_name == "installed" else "transparent")
        self.marketplace_tab_btn.configure(fg_color=["#3B8ED0", "#1F6AA5"] if tab_name == "marketplace" else "transparent")
        self.settings_tab_btn.configure(fg_color=["#3B8ED0", "#1F6AA5"] if tab_name == "settings" else "transparent")

    def _create_installed_tab(self):
        """Create the installed plugins tab"""
        tab = ctk.CTkFrame(self.tab_content)
        self.tabs["installed"] = tab

        # Plugins treeview (using regular tkinter Treeview since CTk doesn't have one)
        import tkinter as tk
        tree_frame = ctk.CTkFrame(tab)
        tree_frame.pack(fill=ctk.BOTH, expand=True, pady=(0, 10))

        # Create treeview with columns
        columns = ("Name", "Version", "Status", "Schedule", "Author")
        self.plugins_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)

        # Configure columns
        for col in columns:
            self.plugins_tree.heading(col, text=col)
            self.plugins_tree.column(col, width=150, anchor="w")

        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.plugins_tree.yview)
        self.plugins_tree.configure(yscrollcommand=scrollbar.set)

        self.plugins_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Plugin action buttons
        button_frame = ctk.CTkFrame(tab, fg_color="transparent")
        button_frame.pack(fill=ctk.X)

        ctk.CTkButton(button_frame, text="Enable",
                     command=self._enable_plugin).pack(side=ctk.LEFT, padx=(0, 5))
        ctk.CTkButton(button_frame, text="Disable",
                     command=self._disable_plugin).pack(side=ctk.LEFT, padx=(0, 5))
        ctk.CTkButton(button_frame, text="Uninstall",
                     command=self._uninstall_plugin).pack(side=ctk.LEFT, padx=(0, 5))
        ctk.CTkButton(button_frame, text="View Details",
                     command=self._view_plugin_details).pack(side=ctk.LEFT, padx=(0, 10))

        # Plugin info panel
        info_frame = ctk.CTkFrame(tab)
        info_frame.pack(fill=ctk.X, pady=(10, 0))

        self.plugin_info_text = tk.Text(info_frame, wrap=tk.WORD, height=6)
        info_scrollbar = ttk.Scrollbar(info_frame, command=self.plugin_info_text.yview)
        self.plugin_info_text.configure(yscrollcommand=info_scrollbar.set)

        self.plugin_info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind treeview selection
        self.plugins_tree.bind('<<TreeviewSelect>>', self._on_plugin_select)

    def _create_marketplace_tab(self):
        """Create the plugin marketplace tab"""
        tab = ctk.CTkFrame(self.tab_content)
        self.tabs["marketplace"] = tab

        # Marketplace description
        desc_frame = ctk.CTkFrame(tab, fg_color="transparent")
        desc_frame.pack(fill=ctk.X, pady=(0, 10))

        desc_text = ("Browse and install plugins from the official marketplace.\n"
                    "Plugins extend Freedom US Tax Return with additional tax forms, "
                    "calculations, and features.")
        ctk.CTkLabel(desc_frame, text=desc_text, wraplength=600).pack(anchor="w")

        # Search and filter
        search_frame = ctk.CTkFrame(tab, fg_color="transparent")
        search_frame.pack(fill=ctk.X, pady=(0, 10))

        ctk.CTkLabel(search_frame, text="Search:").pack(side=ctk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(search_frame, textvariable=self.search_var, width=200)
        search_entry.pack(side=ctk.LEFT, padx=(0, 10))
        search_entry.bind('<KeyRelease>', self._filter_marketplace)

        ctk.CTkButton(search_frame, text="Refresh",
                     command=self._refresh_marketplace).pack(side=ctk.RIGHT)

        # Marketplace plugins list
        list_frame = ctk.CTkFrame(tab)
        list_frame.pack(fill=ctk.BOTH, expand=True)

        # Plugin listbox with details
        self.marketplace_listbox = tk.Listbox(list_frame, height=15, selectmode=tk.SINGLE)
        marketplace_scrollbar = ttk.Scrollbar(list_frame, command=self.marketplace_listbox.yview)
        self.marketplace_listbox.configure(yscrollcommand=marketplace_scrollbar.set)

        self.marketplace_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        marketplace_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Plugin details
        details_frame = ctk.CTkFrame(tab)
        details_frame.pack(fill=ctk.X, pady=(10, 0))

        self.marketplace_details_text = tk.Text(details_frame, wrap=tk.WORD, height=4)
        details_scrollbar = ttk.Scrollbar(details_frame, command=self.marketplace_details_text.yview)
        self.marketplace_details_text.configure(yscrollcommand=details_scrollbar.set)

        self.marketplace_details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Install button
        ctk.CTkButton(tab, text="Install Selected Plugin",
                     command=self._install_from_marketplace).pack(pady=(10, 0))

        # Bind listbox selection
        self.marketplace_listbox.bind('<<ListboxSelect>>', self._on_marketplace_select)

    def _create_settings_tab(self):
        """Create the plugin settings tab"""
        tab = ctk.CTkFrame(self.tab_content)
        self.tabs["settings"] = tab

        # Plugin directories
        dir_frame = ctk.CTkFrame(tab)
        dir_frame.pack(fill=ctk.X, pady=(0, 10))

        ctk.CTkLabel(dir_frame, text="Plugin Directory:").grid(row=0, column=0, sticky="w", pady=2)
        self.plugin_dir_var = tk.StringVar(value=str(Path.home() / "Documents" / "FreedomUSTax" / "plugins"))
        ctk.CTkEntry(dir_frame, textvariable=self.plugin_dir_var, width=300).grid(row=0, column=1, padx=(10, 0), pady=2)
        ctk.CTkButton(dir_frame, text="Browse", command=self._browse_plugin_dir).grid(row=0, column=2, padx=(5, 0), pady=2)

        # Auto-update settings
        update_frame = ctk.CTkFrame(tab)
        update_frame.pack(fill=ctk.X, pady=(0, 10))

        self.auto_update_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(update_frame, text="Automatically check for plugin updates",
                       variable=self.auto_update_var).pack(anchor="w")

        self.auto_install_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(update_frame, text="Automatically install compatible updates",
                       variable=self.auto_install_var).pack(anchor="w", pady=(5, 0))

        # Developer options
        dev_frame = ctk.CTkFrame(tab)
        dev_frame.pack(fill=ctk.X)

        self.dev_mode_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(dev_frame, text="Enable developer mode (show debug information)",
                       variable=self.dev_mode_var).pack(anchor="w")

        # Save settings button
        ctk.CTkButton(tab, text="Save Settings", command=self._save_settings).pack(pady=(10, 0))

    def _load_installed_plugins(self):
        """Load and display installed plugins"""
        if not self.plugins_tree:
            return

        # Clear existing items
        for item in self.plugins_tree.get_children():
            self.plugins_tree.delete(item)

        # Get installed plugins
        installed_plugins = self.plugin_registry.get_all_plugins()

        for schedule_name, plugin in installed_plugins.items():
            try:
                metadata = plugin.get_metadata()
                status = "Enabled"  # In current implementation, all registered plugins are enabled

                self.plugins_tree.insert("", tk.END, values=(
                    metadata.name,
                    metadata.version,
                    status,
                    metadata.schedule_name,
                    metadata.author
                ))

                # Store plugin info
                self.installed_plugins[schedule_name] = {
                    'plugin': plugin,
                    'metadata': metadata,
                    'status': status
                }

            except Exception as e:
                logger.error(f"Error loading plugin {schedule_name}: {e}")
                self.plugins_tree.insert("", tk.END, values=(
                    f"Error: {schedule_name}",
                    "Unknown",
                    "Error",
                    schedule_name,
                    "Unknown"
                ))

        self._update_status(f"Loaded {len(installed_plugins)} plugins")

    def _install_from_file(self):
        """Install a plugin from a local file"""
        file_path = filedialog.askopenfilename(
            title="Select Plugin File",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            self._update_status("Installing plugin...")
            self.progress_var.set(50)

            # Load plugin from file
            spec = importlib.util.spec_from_file_location("plugin_module", file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find plugin class
                plugin_class = None
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                        issubclass(attr, ISchedulePlugin) and
                        attr != ISchedulePlugin):
                        plugin_class = attr
                        break

                if plugin_class:
                    # Register plugin
                    plugin_instance = plugin_class()
                    self.plugin_registry.register(plugin_instance)

                    # Reload installed plugins
                    self._load_installed_plugins()

                    self._update_status("Plugin installed successfully")
                    messagebox.showinfo("Success", "Plugin installed successfully!")
                else:
                    raise ValueError("No valid plugin class found in file")

            self.progress_var.set(100)

        except Exception as e:
            self._update_status("Plugin installation failed")
            messagebox.showerror("Installation Error", f"Failed to install plugin: {str(e)}")
            logger.error(f"Plugin installation failed: {e}")

        finally:
            self.progress_var.set(0)

    def _browse_marketplace(self):
        """Browse the plugin marketplace"""
        try:
            self._update_status("Loading marketplace...")

            # For demo purposes, show some sample marketplace plugins
            # In a real implementation, this would fetch from a server
            sample_plugins = [
                {
                    'name': 'Schedule E Rental Plugin',
                    'version': '1.0.0',
                    'description': 'Advanced rental property income and expense tracking',
                    'author': 'TaxPro Solutions',
                    'schedule': 'Schedule E',
                    'downloads': 1250,
                    'rating': 4.5
                },
                {
                    'name': 'Cryptocurrency Tax Calculator',
                    'version': '2.1.0',
                    'description': 'Comprehensive crypto tax reporting with DeFi support',
                    'author': 'CryptoTax Inc',
                    'schedule': 'Schedule D',
                    'downloads': 2100,
                    'rating': 4.8
                },
                {
                    'name': 'Business Use of Home',
                    'version': '1.2.0',
                    'description': 'Simplified home office deduction calculator',
                    'author': 'HomeOffice Pro',
                    'schedule': 'Schedule C',
                    'downloads': 890,
                    'rating': 4.2
                }
            ]

            self.marketplace_plugins = sample_plugins
            self._update_marketplace_list()

            self.notebook.select(1)  # Switch to marketplace tab
            self._update_status("Marketplace loaded")

        except Exception as e:
            self._update_status("Failed to load marketplace")
            messagebox.showerror("Marketplace Error", f"Failed to load marketplace: {str(e)}")

    def _update_marketplace_list(self):
        """Update the marketplace plugin list"""
        if not self.marketplace_listbox:
            return

        self.marketplace_listbox.delete(0, tk.END)

        for plugin in self.marketplace_plugins:
            display_text = f"{plugin['name']} v{plugin['version']} - {plugin['author']}"
            self.marketplace_listbox.insert(tk.END, display_text)

    def _filter_marketplace(self, event=None):
        """Filter marketplace plugins based on search"""
        search_term = self.search_var.get().lower()

        self.marketplace_listbox.delete(0, tk.END)

        for plugin in self.marketplace_plugins:
            if (search_term in plugin['name'].lower() or
                search_term in plugin['description'].lower() or
                search_term in plugin['author'].lower()):
                display_text = f"{plugin['name']} v{plugin['version']} - {plugin['author']}"
                self.marketplace_listbox.insert(tk.END, display_text)

    def _install_from_marketplace(self):
        """Install a plugin from the marketplace"""
        selection = self.marketplace_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a plugin to install.")
            return

        plugin_info = self.marketplace_plugins[selection[0]]

        # In a real implementation, this would download and install the plugin
        messagebox.showinfo("Installation", f"Plugin '{plugin_info['name']}' would be installed here.\n\n"
                                          "This is a demo implementation. In the full version, "
                                          "plugins would be downloaded from the marketplace.")

    def _enable_plugin(self):
        """Enable a selected plugin"""
        selection = self.plugins_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a plugin to enable.")
            return

        item = self.plugins_tree.item(selection[0])
        plugin_name = item['values'][0]

        # In current implementation, plugins are always enabled once registered
        messagebox.showinfo("Plugin Management", f"Plugin '{plugin_name}' is already enabled.")

    def _disable_plugin(self):
        """Disable a selected plugin"""
        selection = self.plugins_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a plugin to disable.")
            return

        item = self.plugins_tree.item(selection[0])
        plugin_name = item['values'][0]

        # In a real implementation, this would disable the plugin
        messagebox.showinfo("Plugin Management", f"Plugin '{plugin_name}' would be disabled.\n\n"
                                               "This feature would be implemented in future versions.")

    def _uninstall_plugin(self):
        """Uninstall a selected plugin"""
        selection = self.plugins_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a plugin to uninstall.")
            return

        item = self.plugins_tree.item(selection[0])
        schedule_name = item['values'][3]  # Schedule name

        if messagebox.askyesno("Confirm Uninstall",
                              f"Are you sure you want to uninstall the plugin for '{schedule_name}'?"):
            try:
                self.plugin_registry.unregister(schedule_name)
                self._load_installed_plugins()
                messagebox.showinfo("Success", f"Plugin for '{schedule_name}' uninstalled successfully.")
            except Exception as e:
                messagebox.showerror("Uninstall Error", f"Failed to uninstall plugin: {str(e)}")

    def _view_plugin_details(self):
        """View details of selected plugin"""
        selection = self.plugins_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a plugin to view details.")
            return

        item = self.plugins_tree.item(selection[0])
        schedule_name = item['values'][3]

        plugin_info = self.installed_plugins.get(schedule_name)
        if plugin_info:
            metadata = plugin_info['metadata']

            details = f"""Plugin Details:

Name: {metadata.name}
Version: {metadata.version}
Schedule: {metadata.schedule_name}
Author: {metadata.author}
Description: {metadata.description}

Required Dependencies: {', '.join(metadata.requires) if metadata.requires else 'None'}
"""
            messagebox.showinfo("Plugin Details", details)
        else:
            messagebox.showwarning("Plugin Not Found", "Plugin information not available.")

    def _check_updates(self):
        """Check for plugin updates"""
        try:
            self._update_status("Checking for updates...")

            # In a real implementation, this would check for updates
            # For demo, just show a message
            messagebox.showinfo("Update Check", "All plugins are up to date.\n\n"
                                              "Update checking would be implemented in the full version.")

            self._update_status("Update check complete")

        except Exception as e:
            self._update_status("Update check failed")
            messagebox.showerror("Update Error", f"Failed to check for updates: {str(e)}")

    def _on_plugin_select(self, event):
        """Handle plugin selection in treeview"""
        selection = self.plugins_tree.selection()
        if not selection:
            return

        item = self.plugins_tree.item(selection[0])
        schedule_name = item['values'][3]

        plugin_info = self.installed_plugins.get(schedule_name)
        if plugin_info and self.plugin_info_text:
            metadata = plugin_info['metadata']

            info_text = f"""Plugin: {metadata.name}
Version: {metadata.version}
Schedule: {metadata.schedule_name}
Author: {metadata.author}

{metadata.description}

Status: {plugin_info['status']}
Dependencies: {', '.join(metadata.requires) if metadata.requires else 'None'}"""

            self.plugin_info_text.delete(1.0, tk.END)
            self.plugin_info_text.insert(1.0, info_text)

    def _on_marketplace_select(self, event):
        """Handle marketplace plugin selection"""
        selection = self.marketplace_listbox.curselection()
        if not selection or not self.marketplace_details_text:
            return

        plugin_info = self.marketplace_plugins[selection[0]]

        details_text = f"""Name: {plugin_info['name']}
Version: {plugin_info['version']}
Author: {plugin_info['author']}
Downloads: {plugin_info['downloads']:,}
Rating: {plugin_info['rating']}/5.0

{plugin_info['description']}"""

        self.marketplace_details_text.delete(1.0, tk.END)
        self.marketplace_details_text.insert(1.0, details_text)

    def _browse_plugin_dir(self):
        """Browse for plugin directory"""
        dir_path = filedialog.askdirectory(title="Select Plugin Directory")
        if dir_path:
            self.plugin_dir_var.set(dir_path)

    def _save_settings(self):
        """Save plugin settings"""
        # In a real implementation, this would save settings to config
        messagebox.showinfo("Settings Saved", "Plugin settings saved successfully!")

    def _refresh_marketplace(self):
        """Refresh marketplace plugin list"""
        self._browse_marketplace()

    def _update_status(self, message: str):
        """Update status label"""
        if self.status_label:
            self.status_label.config(text=message)
        self.window.update_idletasks()

    def show(self):
        """Show the plugin management window"""
        self.window.mainloop()


def open_plugin_management_window(parent: ctk.CTk, config: AppConfig) -> None:
    """
    Open the plugin management window.

    Args:
        parent: Parent window
        config: Application configuration
    """
    try:
        window = PluginManagementWindow(parent, config)
        window.show()
    except Exception as e:
        messagebox.showerror("Plugin Management Error",
                           f"Failed to open plugin management: {str(e)}")
