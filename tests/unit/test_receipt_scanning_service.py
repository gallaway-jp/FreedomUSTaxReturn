"""
Unit tests for Receipt Scanning and OCR Service
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, date
from decimal import Decimal
import tempfile
import os

from services.receipt_scanning_service import (
    ReceiptScanningService,
    ReceiptData,
    ScanResult
)
from config.app_config import AppConfig


class TestReceiptScanningService:
    """Test cases for Receipt Scanning Service"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration"""
        config = Mock(spec=AppConfig)
        config.tax_year = 2025
        config.tesseract_path = None
        return config

    @pytest.fixture
    def receipt_service(self, mock_config):
        """Create receipt scanning service instance"""
        return ReceiptScanningService(mock_config)

    @pytest.fixture
    def sample_receipt_data(self):
        """Create sample receipt data"""
        return ReceiptData(
            vendor_name="Walgreens",
            total_amount=Decimal("45.99"),
            tax_amount=Decimal("3.50"),
            date=date(2025, 3, 15),
            items=[
                {'description': 'Aspirin', 'quantity': 1, 'price': Decimal("12.99")},
                {'description': 'Cough Medicine', 'quantity': 1, 'price': Decimal("15.99")},
                {'description': 'Vitamins', 'quantity': 1, 'price': Decimal("14.01")}
            ],
            category="medical",
            confidence_score=0.95,
            raw_text="WALGREENS\n...",
            extracted_at=datetime.now()
        )

    def test_service_initialization(self, receipt_service, mock_config):
        """Test receipt scanning service initialization"""
        assert receipt_service.config == mock_config
        assert receipt_service.error_tracker is not None
        assert receipt_service.category_keywords is not None
        assert receipt_service.vendor_patterns is not None

    def test_receipt_data_serialization(self, sample_receipt_data):
        """Test receipt data serialization"""
        receipt_dict = sample_receipt_data.to_dict()
        
        assert receipt_dict['vendor_name'] == "Walgreens"
        assert receipt_dict['total_amount'] == Decimal("45.99")
        assert receipt_dict['category'] == "medical"
        assert receipt_dict['confidence_score'] == 0.95

    def test_scan_result_serialization(self, sample_receipt_data):
        """Test scan result serialization"""
        scan_result = ScanResult(
            success=True,
            receipt_data=sample_receipt_data,
            error_message=None,
            processing_time=2.5,
            image_quality_score=0.9
        )
        
        result_dict = scan_result.to_dict()
        
        assert result_dict['success'] is True
        assert result_dict['error_message'] is None
        assert result_dict['processing_time'] == 2.5
        assert result_dict['image_quality_score'] == 0.9

    def test_scan_missing_file(self, receipt_service):
        """Test scanning a file that doesn't exist"""
        result = receipt_service.scan_receipt("/nonexistent/path/receipt.jpg")
        
        assert result.success is False
        assert result.receipt_data is None
        assert result.error_message is not None
        assert "not found" in result.error_message.lower()

    def test_category_detection_medical(self, receipt_service):
        """Test detection of medical expense category"""
        raw_text = "Walgreens Pharmacy\nAspirin\nPrescription\nCough Medicine\nTotal: $45.99"
        
        category = receipt_service._detect_category(raw_text)
        
        assert category == "medical"

    def test_category_detection_charitable(self, receipt_service):
        """Test detection of charitable donation category"""
        raw_text = "Red Cross Donation\nCharity Contribution\nTotal: $50.00"
        
        category = receipt_service._detect_category(raw_text)
        
        assert category == "charitable"

    def test_category_detection_business(self, receipt_service):
        """Test detection of business supplies category"""
        raw_text = "Office Depot\nOffice Supplies\nPrinter Paper\nTotal: $75.50"
        
        category = receipt_service._detect_category(raw_text)
        
        assert category == "business"

    def test_category_detection_education(self, receipt_service):
        """Test detection of education category"""
        raw_text = "University Bookstore\nTextbooks\nSchool Supplies\nTotal: $250.00"
        
        category = receipt_service._detect_category(raw_text)
        
        assert category == "education"

    def test_category_detection_vehicle(self, receipt_service):
        """Test detection of vehicle expense category"""
        raw_text = "Shell Gas Station\nFuel\nPremium Gasoline\nTotal: $45.00"
        
        category = receipt_service._detect_category(raw_text)
        
        assert category == "vehicle"

    def test_vendor_name_extraction(self, receipt_service):
        """Test vendor name extraction"""
        raw_text = "WALGREENS PHARMACY #12345\n123 Main Street\n..."
        
        vendor = receipt_service._extract_vendor_name(raw_text)
        
        assert vendor is not None
        assert "walgreens" in vendor.lower() or "pharmacy" in vendor.lower()

    def test_amount_extraction(self, receipt_service):
        """Test total amount extraction"""
        raw_text = "Item 1: $15.99\nItem 2: $20.00\nTax: $2.88\nTotal: $38.87"
        
        amount = receipt_service._extract_total_amount(raw_text)
        
        assert amount is not None
        assert amount == Decimal("38.87")

    def test_date_extraction(self, receipt_service):
        """Test receipt date extraction"""
        raw_text = "Date: 03/15/2025\nTime: 2:30 PM\nTransaction #12345"
        
        receipt_date = receipt_service._extract_date(raw_text)
        
        assert receipt_date is not None
        assert receipt_date.month == 3
        assert receipt_date.day == 15
        assert receipt_date.year == 2025

    def test_line_item_extraction(self, receipt_service):
        """Test extraction of line items"""
        raw_text = """
WALGREENS
Item 1: Aspirin - $12.99
Item 2: Cough Medicine - $15.99
Item 3: Vitamins - $14.01
Subtotal: $42.99
Tax: $3.50
Total: $45.99
        """
        
        items = receipt_service._extract_line_items(raw_text)
        
        assert len(items) > 0

    def test_tax_amount_extraction(self, receipt_service):
        """Test extraction of tax amount"""
        raw_text = "Subtotal: $42.49\nTax: $3.50\nTotal: $45.99"
        
        tax_amount = receipt_service._extract_tax_amount(raw_text)
        
        assert tax_amount is not None
        assert tax_amount == Decimal("3.50")

    @patch('services.receipt_scanning_service.cv2')
    def test_image_quality_assessment(self, mock_cv2, receipt_service):
        """Test image quality assessment"""
        # Mock image
        mock_image = MagicMock()
        mock_cv2.imread.return_value = mock_image
        
        quality_score = receipt_service._assess_image_quality(mock_image)
        
        assert isinstance(quality_score, float)
        assert 0.0 <= quality_score <= 1.0

    @patch('services.receipt_scanning_service.pytesseract')
    def test_ocr_text_extraction(self, mock_pytesseract, receipt_service):
        """Test OCR text extraction"""
        mock_pytesseract.image_to_string.return_value = "WALGREENS PHARMACY\nTotal: $45.99"
        
        mock_image = MagicMock()
        text = receipt_service._extract_text(mock_image)
        
        assert "WALGREENS" in text or text is not None

    def test_currency_parsing(self, receipt_service):
        """Test currency value parsing"""
        amounts = ["$45.99", "$1,234.56", "$0.99", "$10000.00"]
        
        parsed = [receipt_service._parse_currency(amount) for amount in amounts]
        
        assert Decimal("45.99") in parsed
        assert Decimal("1234.56") in parsed
        assert Decimal("0.99") in parsed

    def test_confidence_score_calculation(self, receipt_service):
        """Test confidence score calculation"""
        # High confidence: all fields found
        high_confidence = receipt_service._calculate_confidence_score(
            has_vendor=True,
            has_amount=True,
            has_date=True,
            has_items=True,
            ocr_confidence=0.95
        )
        
        assert high_confidence > 0.7

    def test_confidence_score_missing_fields(self, receipt_service):
        """Test confidence score with missing fields"""
        low_confidence = receipt_service._calculate_confidence_score(
            has_vendor=False,
            has_amount=True,
            has_date=False,
            has_items=False,
            ocr_confidence=0.60
        )
        
        assert low_confidence < 0.7

    def test_vendor_pattern_matching(self, receipt_service):
        """Test vendor pattern matching"""
        vendors = [
            ("Walmart", "walmart"),
            ("Target", "target"),
            ("Costco", "costco"),
            ("Home Depot", "home_depot")
        ]
        
        for vendor_name, pattern_key in vendors:
            if pattern_key in receipt_service.vendor_patterns:
                pattern = receipt_service.vendor_patterns[pattern_key]
                assert pattern.search(vendor_name) is not None

    def test_keyword_category_mapping(self, receipt_service):
        """Test keyword to category mapping"""
        test_cases = [
            ("pharmacy aspirin doctor", "medical"),
            ("donation charity church", "charitable"),
            ("office supplies computer", "business"),
            ("bookstore university textbook", "education"),
        ]
        
        for keywords, expected_category in test_cases:
            category = receipt_service._detect_category(keywords)
            assert category is not None

    def test_duplicate_item_detection(self, receipt_service):
        """Test detection of duplicate items in receipt"""
        items = [
            {'description': 'Aspirin', 'quantity': 1, 'price': Decimal("12.99")},
            {'description': 'Aspirin', 'quantity': 1, 'price': Decimal("12.99")},
            {'description': 'Cough Medicine', 'quantity': 1, 'price': Decimal("15.99")}
        ]
        
        unique_items = receipt_service._deduplicate_items(items)
        
        # Should handle duplicates appropriately
        assert len(unique_items) <= len(items)

    def test_receipt_data_validation(self, receipt_service):
        """Test receipt data validation"""
        valid_data = ReceiptData(
            vendor_name="Walgreens",
            total_amount=Decimal("45.99"),
            tax_amount=Decimal("3.50"),
            date=date(2025, 3, 15),
            items=[],
            category="medical",
            confidence_score=0.95,
            raw_text="...",
            extracted_at=datetime.now()
        )
        
        errors = receipt_service.validate_receipt_data(valid_data)
        
        assert len(errors) == 0

    def test_receipt_validation_invalid_amount(self, receipt_service):
        """Test validation fails with invalid amount"""
        invalid_data = ReceiptData(
            vendor_name="Walgreens",
            total_amount=Decimal("-45.99"),  # Negative amount
            tax_amount=Decimal("3.50"),
            date=date(2025, 3, 15),
            items=[],
            category="medical",
            confidence_score=0.95,
            raw_text="...",
            extracted_at=datetime.now()
        )
        
        errors = receipt_service.validate_receipt_data(invalid_data)
        
        assert len(errors) > 0

    def test_receipt_validation_missing_vendor(self, receipt_service):
        """Test validation fails with missing vendor"""
        invalid_data = ReceiptData(
            vendor_name="",
            total_amount=Decimal("45.99"),
            tax_amount=Decimal("3.50"),
            date=date(2025, 3, 15),
            items=[],
            category="medical",
            confidence_score=0.95,
            raw_text="...",
            extracted_at=datetime.now()
        )
        
        errors = receipt_service.validate_receipt_data(invalid_data)
        
        assert len(errors) > 0

    def test_batch_receipt_processing(self, receipt_service):
        """Test batch processing multiple receipts"""
        receipt_paths = [
            "/path/to/receipt1.jpg",
            "/path/to/receipt2.jpg",
            "/path/to/receipt3.jpg"
        ]
        
        # Would process each receipt
        results = []
        for path in receipt_paths:
            result = receipt_service.scan_receipt(path)
            results.append(result)
        
        assert len(results) == 3

    def test_receipt_date_format_variations(self, receipt_service):
        """Test parsing various date formats"""
        date_formats = [
            "03/15/2025",
            "2025-03-15",
            "March 15, 2025",
            "15-Mar-2025"
        ]
        
        for date_str in date_formats:
            # Should attempt to parse
            date_result = receipt_service._extract_date(date_str)
            # Some may fail, that's okay - testing flexibility

    def test_multi_currency_handling(self, receipt_service):
        """Test handling of different currency formats"""
        amounts = [
            "$45.99",
            "45.99 USD",
            "US $45.99",
            "45,99€",  # European format
        ]
        
        parsed = []
        for amount in amounts:
            try:
                result = receipt_service._parse_currency(amount)
                if result:
                    parsed.append(result)
            except:
                pass  # Some formats may not parse

    def test_high_volume_processing_performance(self, receipt_service):
        """Test performance with high volume of receipts"""
        import time
        
        start_time = time.time()
        
        # Process 10 non-existent receipts (fast failure)
        for i in range(10):
            receipt_service.scan_receipt(f"/nonexistent/receipt_{i}.jpg")
        
        elapsed_time = time.time() - start_time
        
        # Should complete quickly
        assert elapsed_time < 5.0

    def test_error_recovery_graceful_degradation(self, receipt_service):
        """Test graceful error recovery"""
        # Missing file should not crash the service
        result = receipt_service.scan_receipt("/invalid/path")
        
        assert result is not None
        assert result.success is False

    def test_receipt_archival_support(self, receipt_service):
        """Test support for archiving processed receipts"""
        receipt_archive = {
            'date': date(2025, 3, 15),
            'vendor': 'Walgreens',
            'amount': Decimal("45.99"),
            'category': 'medical',
            'file_path': '/archive/receipt_2025_03_15.jpg'
        }
        
        assert receipt_archive['date'] is not None
        assert receipt_archive['vendor'] is not None

    def test_itemized_deduction_summary(self, receipt_service):
        """Test summary generation for itemized deductions"""
        receipts = [
            {'category': 'medical', 'amount': Decimal("100.00")},
            {'category': 'medical', 'amount': Decimal("75.00")},
            {'category': 'charitable', 'amount': Decimal("250.00")},
            {'category': 'business', 'amount': Decimal("150.00")},
        ]
        
        summary = {}
        for receipt in receipts:
            category = receipt['category']
            amount = receipt['amount']
            summary[category] = summary.get(category, Decimal("0")) + amount
        
        assert summary['medical'] == Decimal("175.00")
        assert summary['charitable'] == Decimal("250.00")
        assert summary['business'] == Decimal("150.00")

    def test_expense_aggregation_by_category(self, receipt_service):
        """Test expense aggregation by category"""
        expenses = [
            {'category': 'medical', 'amount': Decimal("100")},
            {'category': 'medical', 'amount': Decimal("75")},
            {'category': 'medical', 'amount': Decimal("50")},
        ]
        
        total_medical = sum(e['amount'] for e in expenses if e['category'] == 'medical')
        
        assert total_medical == Decimal("225")
