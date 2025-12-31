"""
Receipt Scanning and OCR Service

This service provides OCR capabilities for scanning receipts and extracting
tax-relevant information including amounts, dates, vendors, and categories.
"""

import os
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, date
from decimal import Decimal
import cv2
import numpy as np
from PIL import Image
import pytesseract

from config.app_config import AppConfig
from utils.error_tracker import get_error_tracker

logger = logging.getLogger(__name__)


@dataclass
class ReceiptData:
    """Extracted data from a scanned receipt"""

    vendor_name: str
    total_amount: Decimal
    tax_amount: Optional[Decimal]
    date: Optional[date]
    items: List[Dict[str, Any]]
    category: str
    confidence_score: float
    raw_text: str
    extracted_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'vendor_name': self.vendor_name,
            'total_amount': self.total_amount,
            'tax_amount': self.tax_amount,
            'date': self.date.isoformat() if self.date else None,
            'items': self.items,
            'category': self.category,
            'confidence_score': self.confidence_score,
            'raw_text': self.raw_text,
            'extracted_at': self.extracted_at.isoformat()
        }


@dataclass
class ScanResult:
    """Result of a receipt scanning operation"""

    success: bool
    receipt_data: Optional[ReceiptData]
    error_message: Optional[str]
    processing_time: float
    image_quality_score: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'success': self.success,
            'receipt_data': self.receipt_data.to_dict() if self.receipt_data else None,
            'error_message': self.error_message,
            'processing_time': self.processing_time,
            'image_quality_score': self.image_quality_score
        }


class ReceiptScanningService:
    """
    Service for scanning receipts using OCR and extracting tax-relevant data.

    Features:
    - Image preprocessing for better OCR accuracy
    - Text extraction and parsing
    - Vendor identification
    - Amount and date extraction
    - Tax category classification
    - Confidence scoring
    """

    def __init__(self, config: AppConfig):
        """
        Initialize the receipt scanning service.

        Args:
            config: Application configuration
        """
        self.config = config
        self.error_tracker = get_error_tracker()

        # Configure Tesseract path if needed
        if hasattr(config, 'tesseract_path') and config.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = config.tesseract_path

        # Tax-relevant keywords for categorization
        self.category_keywords = {
            'medical': ['pharmacy', 'doctor', 'hospital', 'clinic', 'medical', 'dental', 'prescription', 'rx'],
            'charitable': ['donation', 'charity', 'church', 'temple', 'mosque', 'nonprofit', 'contribution'],
            'business': ['office', 'supplies', 'equipment', 'software', 'computer', 'printer', 'business'],
            'education': ['bookstore', 'university', 'college', 'school', 'tuition', 'textbook', 'education'],
            'vehicle': ['gas', 'gasoline', 'fuel', 'auto', 'car', 'truck', 'vehicle', 'repair', 'oil'],
            'home_office': ['home depot', 'lowes', 'office depot', 'staples', 'furniture', 'desk', 'chair'],
            'retirement': ['ira', '401k', 'retirement', 'pension', 'annuity'],
            'energy': ['electric', 'gas bill', 'utility', 'solar', 'energy'],
            'state_local': ['property tax', 'county', 'state', 'local', 'license'],
            'miscellaneous': []  # Default category
        }

        # Common vendor patterns
        self.vendor_patterns = {
            'walmart': re.compile(r'walmart|wal-mart', re.IGNORECASE),
            'target': re.compile(r'target', re.IGNORECASE),
            'costco': re.compile(r'costco', re.IGNORECASE),
            'amazon': re.compile(r'amazon', re.IGNORECASE),
            'home_depot': re.compile(r'home\s+depot|home\s+depot', re.IGNORECASE),
            'lowes': re.compile(r'lowes|lowe\'s', re.IGNORECASE),
            'cvs': re.compile(r'cvs|pharmacy', re.IGNORECASE),
            'walgreens': re.compile(r'walgreens', re.IGNORECASE),
            'shell': re.compile(r'shell|fuel', re.IGNORECASE),
            'chevron': re.compile(r'chevron|texaco', re.IGNORECASE),
        }

    def scan_receipt(self, image_path: str) -> ScanResult:
        """
        Scan a receipt image and extract data.

        Args:
            image_path: Path to the receipt image file

        Returns:
            ScanResult with extracted data or error information
        """
        start_time = datetime.now()

        try:
            # Validate image file
            if not os.path.exists(image_path):
                return ScanResult(
                    success=False,
                    receipt_data=None,
                    error_message=f"Image file not found: {image_path}",
                    processing_time=0.0,
                    image_quality_score=0.0
                )

            # Load and preprocess image
            image = self._load_image(image_path)
            quality_score = self._assess_image_quality(image)

            # Extract text using OCR
            raw_text = self._extract_text(image)

            if not raw_text.strip():
                return ScanResult(
                    success=False,
                    receipt_data=None,
                    error_message="No text could be extracted from the image",
                    processing_time=(datetime.now() - start_time).total_seconds(),
                    image_quality_score=quality_score
                )

            # Parse extracted data
            receipt_data = self._parse_receipt_data(raw_text)

            processing_time = (datetime.now() - start_time).total_seconds()

            return ScanResult(
                success=True,
                receipt_data=receipt_data,
                error_message=None,
                processing_time=processing_time,
                image_quality_score=quality_score
            )

        except Exception as e:
            self.error_tracker.track_error(e, "Receipt Scanning")
            return ScanResult(
                success=False,
                receipt_data=None,
                error_message=f"Scanning failed: {str(e)}",
                processing_time=(datetime.now() - start_time).total_seconds(),
                image_quality_score=0.0
            )

    def _load_image(self, image_path: str) -> np.ndarray:
        """
        Load and preprocess image for OCR.

        Args:
            image_path: Path to image file

        Returns:
            Preprocessed image as numpy array
        """
        # Load image
        image = cv2.imread(image_path)

        if image is None:
            raise ValueError(f"Could not load image: {image_path}")

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply noise reduction
        denoised = cv2.medianBlur(gray, 3)

        # Enhance contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        # Apply thresholding for better OCR
        _, threshold = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return threshold

    def _assess_image_quality(self, image: np.ndarray) -> float:
        """
        Assess the quality of the image for OCR processing.

        Args:
            image: Preprocessed image

        Returns:
            Quality score between 0-100
        """
        try:
            # Calculate image sharpness using Laplacian variance
            laplacian_var = cv2.Laplacian(image, cv2.CV_64F).var()

            # Calculate brightness
            brightness = np.mean(image)

            # Calculate contrast
            contrast = image.std()

            # Combine metrics into quality score
            sharpness_score = min(100, laplacian_var / 500 * 100)
            brightness_score = 100 - abs(brightness - 128) / 128 * 100
            contrast_score = min(100, contrast / 64 * 100)

            quality_score = (sharpness_score * 0.4 + brightness_score * 0.3 + contrast_score * 0.3)

            return max(0, min(100, quality_score))

        except Exception:
            return 50.0  # Default medium quality

    def _extract_text(self, image: np.ndarray) -> str:
        """
        Extract text from image using OCR.

        Args:
            image: Preprocessed image

        Returns:
            Extracted text
        """
        # Convert to PIL Image for pytesseract
        pil_image = Image.fromarray(image)

        # Configure OCR settings for receipt scanning
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,$/- '

        # Extract text
        text = pytesseract.image_to_string(pil_image, config=custom_config)

        return text

    def _parse_receipt_data(self, raw_text: str) -> ReceiptData:
        """
        Parse extracted text to extract receipt data.

        Args:
            raw_text: Raw OCR text

        Returns:
            Parsed receipt data
        """
        # Extract vendor name
        vendor_name = self._extract_vendor(raw_text)

        # Extract total amount
        total_amount = self._extract_total_amount(raw_text)

        # Extract tax amount
        tax_amount = self._extract_tax_amount(raw_text)

        # Extract date
        receipt_date = self._extract_date(raw_text)

        # Extract items (simplified)
        items = self._extract_items(raw_text)

        # Determine category
        category = self._categorize_receipt(vendor_name, raw_text)

        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(raw_text, total_amount, vendor_name)

        return ReceiptData(
            vendor_name=vendor_name,
            total_amount=total_amount,
            tax_amount=tax_amount,
            date=receipt_date,
            items=items,
            category=category,
            confidence_score=confidence_score,
            raw_text=raw_text,
            extracted_at=datetime.now()
        )

    def _extract_vendor(self, text: str) -> str:
        """
        Extract vendor/store name from receipt text.

        Args:
            text: OCR text

        Returns:
            Vendor name
        """
        lines = text.split('\n')

        # Look for vendor patterns
        for line in lines[:5]:  # Check first few lines
            line = line.strip()
            if len(line) > 3 and not any(char.isdigit() for char in line):
                # Check against known vendor patterns
                for vendor, pattern in self.vendor_patterns.items():
                    if pattern.search(line):
                        return vendor.title()

                # Return the line if it looks like a vendor name
                if len(line) <= 50 and not line.startswith('$'):
                    return line.title()

        return "Unknown Vendor"

    def _extract_total_amount(self, text: str) -> Decimal:
        """
        Extract total amount from receipt text.

        Args:
            text: OCR text

        Returns:
            Total amount as Decimal
        """
        # Look for patterns like "TOTAL", "AMOUNT DUE", etc.
        total_patterns = [
            r'TOTAL[:\s]*\$?(\d+\.?\d*)',
            r'AMOUNT\s+DUE[:\s]*\$?(\d+\.?\d*)',
            r'BALANCE[:\s]*\$?(\d+\.?\d*)',
            r'GRAND\s+TOTAL[:\s]*\$?(\d+\.?\d*)',
        ]

        for pattern in total_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    return Decimal(matches[-1])  # Take the last match (usually the final total)
                except:
                    continue

        # Fallback: look for the largest dollar amount
        dollar_pattern = r'\$?(\d+\.\d{2})'
        amounts = re.findall(dollar_pattern, text)
        if amounts:
            try:
                amounts_decimal = [Decimal(amount) for amount in amounts]
                return max(amounts_decimal)  # Assume largest is total
            except:
                pass

        return Decimal('0.00')

    def _extract_tax_amount(self, text: str) -> Optional[Decimal]:
        """
        Extract tax amount from receipt text.

        Args:
            text: OCR text

        Returns:
            Tax amount as Decimal or None
        """
        tax_patterns = [
            r'TAX[:\s]*\$?(\d+\.?\d*)',
            r'SALES\s+TAX[:\s]*\$?(\d+\.?\d*)',
            r'TAX\s+AMOUNT[:\s]*\$?(\d+\.?\d*)',
        ]

        for pattern in tax_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    return Decimal(matches[-1])
                except:
                    continue

        return None

    def _extract_date(self, text: str) -> Optional[date]:
        """
        Extract date from receipt text.

        Args:
            text: OCR text

        Returns:
            Extracted date or None
        """
        # Common date patterns
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',  # MM/DD/YYYY or MM/DD/YY
            r'(\d{2,4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY/MM/DD or YY/MM/DD
            r'(\w{3})\s+(\d{1,2}),?\s+(\d{2,4})',    # Mon DD, YYYY
        ]

        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    if len(match) == 3:
                        # Handle different date formats
                        if len(match[2]) == 4:  # YYYY format
                            year = int(match[2])
                            month = int(match[0]) if int(match[0]) <= 12 else int(match[1])
                            day = int(match[1]) if int(match[0]) <= 12 else int(match[0])
                        else:  # YY format
                            year = 2000 + int(match[2])
                            month = int(match[0]) if int(match[0]) <= 12 else int(match[1])
                            day = int(match[1]) if int(match[0]) <= 12 else int(match[0])

                        # Validate date
                        if 1 <= month <= 12 and 1 <= day <= 31 and 2020 <= year <= 2030:
                            return date(year, month, day)
                except:
                    continue

        return None

    def _extract_items(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract individual items from receipt (simplified implementation).

        Args:
            text: OCR text

        Returns:
            List of item dictionaries
        """
        # This is a simplified implementation
        # A full implementation would need more sophisticated parsing
        items = []

        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            # Look for lines that might contain items (have prices)
            if '$' in line or re.search(r'\d+\.\d{2}', line):
                # Extract description and price
                price_match = re.search(r'(\d+\.\d{2})', line)
                if price_match:
                    price = Decimal(price_match.group(1))
                    description = line.replace(price_match.group(0), '').strip()
                    if description:
                        items.append({
                            'description': description,
                            'price': price
                        })

        return items

    def _categorize_receipt(self, vendor: str, text: str) -> str:
        """
        Categorize receipt based on vendor and content.

        Args:
            vendor: Vendor name
            text: OCR text

        Returns:
            Category name
        """
        # Combine vendor and text for analysis
        combined_text = f"{vendor} {text}".lower()

        # Check each category
        for category, keywords in self.category_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                return category

        return "miscellaneous"

    def _calculate_confidence_score(self, text: str, total_amount: Decimal, vendor_name: str) -> float:
        """
        Calculate confidence score for the extracted data.

        Args:
            text: Raw OCR text
            total_amount: Extracted total amount
            vendor_name: Extracted vendor name

        Returns:
            Confidence score (0-100)
        """
        score = 0.0

        # Text length (more text = higher confidence)
        if len(text) > 100:
            score += 30
        elif len(text) > 50:
            score += 20
        elif len(text) > 20:
            score += 10

        # Amount found
        if total_amount > 0:
            score += 25

        # Vendor identified
        if vendor_name and vendor_name != "Unknown Vendor":
            score += 20

        # Date found
        if re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', text):
            score += 15

        # Multiple dollar amounts (suggests detailed receipt)
        dollar_count = len(re.findall(r'\$?\d+\.\d{2}', text))
        if dollar_count > 3:
            score += 10

        return min(100.0, score)