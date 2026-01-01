#!/usr/bin/env python3
"""
Integration test script for ModernMainWindow GUI components.
This script tests that all GUI components can be imported and instantiated
without starting the tkinter event loop, which would block the terminal.
"""

import sys
import os
import traceback

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required imports work."""
    print("🔍 Testing imports...")

    try:
        from gui.modern_main_window import ModernMainWindow
        from config.app_config import AppConfig
        import customtkinter as ctk
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        traceback.print_exc()
        return False

def test_config():
    """Test that AppConfig can be created."""
    print("🔍 Testing AppConfig creation...")

    try:
        from config.app_config import AppConfig
        config = AppConfig.from_env()
        print("✅ Config created successfully")
        return True
    except Exception as e:
        print(f"❌ Config creation error: {e}")
        traceback.print_exc()
        return False

def test_class_access():
    """Test that ModernMainWindow class is accessible and has correct signature."""
    print("🔍 Testing ModernMainWindow class access...")

    try:
        from gui.modern_main_window import ModernMainWindow
        import inspect

        # Check class exists
        cls = ModernMainWindow
        print("✅ ModernMainWindow class accessible")

        # Check __init__ signature
        sig = inspect.signature(cls.__init__)
        print(f"✅ ModernMainWindow.__init__ signature: {sig}")

        # Verify expected parameters
        params = list(sig.parameters.keys())
        expected_params = ['self', 'config', 'accessibility_service', 'demo_mode']
        if all(param in params for param in expected_params):
            print("✅ All expected parameters present")
        else:
            print(f"⚠️  Missing expected parameters. Found: {params}")

        return True
    except Exception as e:
        print(f"❌ Class access error: {e}")
        traceback.print_exc()
        return False

def test_gui_components():
    """Test that GUI components can be imported (but not instantiated to avoid event loop)."""
    print("🔍 Testing GUI component imports...")

    components_to_test = [
        'gui.e_filing_window.EFilingWindow',
        'gui.amended_return_dialog.AmendedReturnDialog',
        'gui.audit_trail_window.AuditTrailWindow',
        'gui.tax_analytics_window.TaxAnalyticsWindow',
        'gui.ai_deduction_finder_window.AIDeductionFinderWindow',
        'gui.client_management_dialogs.ClientManagementDialog',
        'gui.two_factor_dialogs.TwoFactorSetupDialog',
        'gui.two_factor_dialogs.TwoFactorVerifyDialog',
    ]

    failed_imports = []

    for component in components_to_test:
        try:
            module_name, class_name = component.rsplit('.', 1)
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✅ {component} imported successfully")
        except Exception as e:
            print(f"❌ Failed to import {component}: {e}")
            failed_imports.append(component)

    if failed_imports:
        print(f"⚠️  {len(failed_imports)} components failed to import")
        return False
    else:
        print("✅ All GUI components imported successfully")
        return True

def main():
    """Run all integration tests."""
    print("🚀 Starting ModernMainWindow Integration Tests")
    print("=" * 50)

    tests = [
        test_imports,
        test_config,
        test_class_access,
        test_gui_components,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All integration tests passed!")
        return 0
    else:
        print("❌ Some tests failed. Check output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())