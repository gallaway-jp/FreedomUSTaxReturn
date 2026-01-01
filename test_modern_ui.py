#!/usr/bin/env python3
"""
Test script for CustomTkinter UI components

Tests the modern UI components and tax interview functionality.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import customtkinter as ctk
    print("✓ CustomTkinter imported successfully")
except ImportError as e:
    print(f"✗ CustomTkinter import failed: {e}")
    print("Please install CustomTkinter: pip install customtkinter")
    sys.exit(1)

from config.app_config import AppConfig
from gui.modern_main_window import ModernMainWindow
from gui.modern_ui_components import (
    ModernFrame, ModernLabel, ModernEntry, ModernButton,
    ModernComboBox, ModernRadioGroup, validate_ssn, validate_zip_code
)
from services.tax_interview_service import TaxInterviewService


def test_ui_components():
    """Test basic UI components"""
    print("\n--- Testing UI Components ---")

    # Create a test window
    test_window = ctk.CTk()
    test_window.title("UI Components Test")
    test_window.geometry("400x300")

    # Test ModernFrame
    frame = ModernFrame(test_window, title="Test Frame")
    frame.pack(pady=10, padx=10, fill="x")

    # Test ModernLabel
    label = ModernLabel(frame, text="Test Label", required=True)
    label.pack(pady=5)

    # Test ModernEntry with validation
    entry = ModernEntry(
        frame,
        label_text="SSN",
        help_text="Enter your Social Security Number (XXX-XX-XXXX)",
        validator=validate_ssn,
        required=True
    )
    entry.pack(pady=5)

    # Test ModernButton
    button = ModernButton(frame, text="Test Button", command=lambda: print("Button clicked"))
    button.pack(pady=5)

    # Test validation
    print("Testing SSN validation...")
    valid, result = validate_ssn("123-45-6789")
    print(f"SSN '123-45-6789': {'✓ Valid' if valid else '✗ Invalid'} - {result}")

    invalid, result = validate_ssn("123")
    print(f"SSN '123': {'✓ Valid' if invalid else '✗ Invalid'} - {result}")

    print("Testing ZIP validation...")
    valid, result = validate_zip_code("12345")
    print(f"ZIP '12345': {'✓ Valid' if valid else '✗ Invalid'} - {result}")

    valid, result = validate_zip_code("12345-6789")
    print(f"ZIP '12345-6789': {'✓ Valid' if valid else '✗ Invalid'} - {result}")

    # Close test window
    test_window.after(1000, test_window.destroy)
    test_window.mainloop()

    print("✓ UI components test completed")


def test_tax_interview_service():
    """Test the tax interview service"""
    print("\n--- Testing Tax Interview Service ---")

    try:
        config = AppConfig()
        service = TaxInterviewService(config)

        # Test starting interview
        questions = service.start_interview()
        print(f"✓ Started interview with {len(questions)} initial questions")

        # Test answering a question
        if questions:
            first_question = questions[0]
            print(f"First question: {first_question.text}")

            # Answer yes/no question
            result = service.answer_question(first_question.id, True)
            print(f"✓ Answered question, got {len(result['next_questions'])} follow-up questions")
            print(f"✓ Generated {len(result['recommendations'])} recommendations")

        # Test progress
        progress = service.get_progress_percentage()
        print(f"✓ Interview progress: {progress:.1f}%")

        print("✓ Tax interview service test completed")

    except Exception as e:
        print(f"✗ Tax interview service test failed: {e}")


def test_main_window():
    """Test the main window (brief test)"""
    print("\n--- Testing Main Window ---")

    try:
        config = AppConfig()

        # Create main window
        app = ModernMainWindow(config)

        # Test that it initializes
        print("✓ Main window initialized successfully")

        # Close after a short delay (don't actually run the full app)
        app.after(500, app.destroy)
        app.mainloop()

        print("✓ Main window test completed")

    except Exception as e:
        print(f"✗ Main window test failed: {e}")


def main():
    """Run all tests"""
    print("Testing CustomTkinter UI Implementation")
    print("=" * 50)

    # Test imports
    test_ui_components()

    # Test services
    test_tax_interview_service()

    # Test main window
    test_main_window()

    print("\n" + "=" * 50)
    print("All tests completed!")
    print("\nTo run the full application:")
    print("python -m gui.modern_main_window")


if __name__ == "__main__":
    main()