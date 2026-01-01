#!/usr/bin/env python3
"""
Launcher for the Modern Freedom US Tax Return Application

Runs the CustomTkinter-based modern UI with guided tax interview.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.app_config import AppConfig
from gui.modern_main_window import ModernMainWindow


def main():
    """Main application entry point"""
    try:
        # Initialize configuration
        config = AppConfig()

        # Create and run the modern main window
        app = ModernMainWindow(config)
        app.run()

    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()