"""
Freedom US Tax Return - Free Tax Return Assistance Application
Main application entry point

Tax Year: 2025 (Returns filed in 2026)

This version uses the modern CustomTkinter-based UI with guided tax interview,
intelligent form recommendations, and enhanced accessibility support.
"""

from config.app_config import AppConfig
from gui.modern_main_window import ModernMainWindow
from services.accessibility_service import AccessibilityService
from services.encryption_service import EncryptionService

def main():
    """Initialize and run the modern application"""
    # Load configuration
    config = AppConfig.from_env()
    
    # Initialize accessibility service for modern UI
    encryption_service = EncryptionService(config.key_file)
    accessibility_service = AccessibilityService(config, encryption_service)
    
    # Create and run modern main window
    app = ModernMainWindow(config, accessibility_service)
    app.mainloop()

if __name__ == "__main__":
    main()
