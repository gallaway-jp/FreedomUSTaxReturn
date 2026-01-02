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
from services.authentication_service import AuthenticationService

def main():
    """Initialize and run the modern application"""
    # Load configuration
    config = AppConfig.from_env()
    
    # Initialize core services
    encryption_service = EncryptionService(config.key_file)
    auth_service = AuthenticationService(config)
    
    # Set up demo master password if not already set
    demo_password = "DemoPassword123!"
    if not auth_service.is_master_password_set():
        try:
            auth_service.create_master_password(demo_password)
            print(f"Demo master password set to: {demo_password}")
            print("Please change this password in production!")
        except Exception as e:
            print(f"Warning: Could not set demo password: {e}")
    
    # Authenticate with demo password
    try:
        session_token = auth_service.authenticate_master_password(demo_password)
        print("Authenticated successfully")
    except Exception as e:
        print(f"Warning: Could not authenticate with demo password: {e}")
        print("Resetting demo password...")
        try:
            # Reset the master password
            auth_service.create_master_password(demo_password)
            session_token = auth_service.authenticate_master_password(demo_password)
            print("Demo password reset and authentication successful")
        except Exception as reset_error:
            print(f"Failed to reset password: {reset_error}")
            session_token = None
    
    # Initialize accessibility service for modern UI
    accessibility_service = AccessibilityService(config, encryption_service)
    
    # Create and run modern main window
    app = ModernMainWindow(config, accessibility_service, demo_mode=True)
    app.mainloop()

if __name__ == "__main__":
    main()
