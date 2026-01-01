"""
Legacy Main Window - DEPRECATED

This module has been superseded by the modern CustomTkinter UI.
See gui/modern_main_window.py for the current implementation.

This file is kept for backward compatibility with existing code that imports
from gui.main_window. It redirects to the modern implementation.

DEPRECATION: This legacy Tkinter-based UI will be removed in a future version.
Please migrate your code to use ModernMainWindow from gui.modern_main_window.
"""

import warnings
from config.app_config import AppConfig
from services.accessibility_service import AccessibilityService
from services.encryption_service import EncryptionService
from gui.modern_main_window import ModernMainWindow

# Issue deprecation warning when this module is imported
warnings.warn(
    "The legacy Tkinter UI (gui.main_window.MainWindow) is deprecated. "
    "Please use gui.modern_main_window.ModernMainWindow instead. "
    "The legacy UI will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)


class MainWindow:
    """
    DEPRECATED: Legacy Tkinter-based main window.
    
    This class is a compatibility wrapper that redirects to ModernMainWindow.
    For new code, use ModernMainWindow directly.
    """
    
    def __init__(self, root, config: AppConfig = None):
        """
        Initialize the main window (legacy Tkinter version).
        
        Args:
            root: Legacy Tkinter root window (ignored - using CustomTkinter)
            config: Application configuration
            
        Note: The root parameter is ignored as the modern UI uses CustomTkinter.
        The window instance is created internally.
        """
        warnings.warn(
            "MainWindow is deprecated. Use ModernMainWindow instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        self.root = root  # Keep for compatibility
        self.config = config or AppConfig.from_env()
        
        # Initialize accessibility service
        encryption_service = EncryptionService(self.config.key_file)
        accessibility_service = AccessibilityService(self.config, encryption_service)
        
        # Create the modern window as the actual implementation
        self.modern_window = ModernMainWindow(self.config, accessibility_service)
        
    def show(self):
        """Show the window (legacy compatibility method)"""
        if hasattr(self.modern_window, 'show'):
            self.modern_window.show()
        else:
            self.modern_window.mainloop()
