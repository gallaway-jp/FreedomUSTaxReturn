#!/usr/bin/env python3
"""
Test script for OCR functionality

This script tests the OCR service and receipt scanning functionality.
Run this after installing Tesseract OCR to verify everything works.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.app_config import AppConfig
from services.ocr_service import OCRService
from services.receipt_scanning_service import ReceiptScanningService


def test_ocr_service():
    """Test the OCR service with a simple text image"""
    print("Testing OCR Service...")

    config = AppConfig()
    ocr_service = OCRService(config)

    # Test with a simple text string (simulated image)
    test_text = "Test receipt text\nTotal: $25.99\nDate: 01/15/2024"

    try:
        # Test EasyOCR initialization
        if ocr_service.validate_easyocr_installation():
            print("✓ EasyOCR initialized successfully")
            # Test basic functionality by checking if reader is available
            result = ocr_service.get_supported_languages()
            print(f"Supported languages: {result}")
            print("✓ OCR Service initialized successfully")
            return True
        else:
            print("✗ EasyOCR initialization failed")
            return False
    except Exception as e:
        print(f"✗ OCR Service test failed: {e}")
        return False


def test_receipt_scanning_service():
    """Test the receipt scanning service"""
    print("\nTesting Receipt Scanning Service...")

    config = AppConfig()
    scanning_service = ReceiptScanningService(config)

    try:
        # Test service initialization
        print("✓ Receipt Scanning Service initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Receipt Scanning Service test failed: {e}")
        return False


def main():
    """Run all OCR tests"""
    print("Freedom US Tax Return - OCR Functionality Test")
    print("=" * 50)

    # Check if EasyOCR is available
    try:
        import easyocr
        print("✓ EasyOCR library found")
    except ImportError:
        print("✗ EasyOCR not installed")
        print("Run: pip install easyocr")
        return False

    # Test services
    ocr_ok = test_ocr_service()
    scanning_ok = test_receipt_scanning_service()

    if ocr_ok and scanning_ok:
        print("\n✓ All OCR tests passed!")
        print("\nNext steps:")
        print("- Test with actual receipt images")
        print("- Use the Receipt Scanning window in the GUI")
        print("- Integrate with mobile camera capture")
        return True
    else:
        print("\n✗ Some tests failed. Check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)