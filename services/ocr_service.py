"""
OCR Service - Document scanning and text extraction for tax documents

Provides OCR functionality for receipts, W-2 forms, 1099 forms, and other
tax-related documents with intelligent data extraction and classification.
"""

import re
import cv2
import numpy as np
from PIL import Image
import easyocr
import io
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
import logging

from config.app_config import AppConfig
from services.exceptions import InvalidInputException, ServiceExecutionException
from services.error_logger import get_error_logger


class OCRService:
    """
    Service for OCR processing of tax documents.

    Features:
    - Receipt scanning and data extraction
    - W-2 form OCR and parsing
    - 1099 form OCR and parsing
    - Document classification
    - Image preprocessing for better OCR accuracy
    """

    def __init__(self, config: AppConfig):
        """
        Initialize OCR service.

        Args:
            config: Application configuration
        """
        self.config = config
        self.error_logger = get_error_logger()

        # Initialize EasyOCR reader (English language)
        # EasyOCR comes with pre-trained models and requires no external dependencies
        try:
            self.reader = easyocr.Reader(['en'], gpu=False)  # Use CPU for better compatibility
        except Exception as e:
            self.error_logger.log_error(e, "Failed to initialize EasyOCR reader")
            self.reader = None

        # Try to set Tesseract path if configured
        if hasattr(config, 'tesseract_path') and config.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = config.tesseract_path

        # Document type patterns
        self.document_patterns = {
            'receipt': {
                'keywords': ['receipt', 'invoice', 'paid', 'total', 'tax', 'subtotal'],
                'amount_pattern': r'\$?\d{1,3}(?:,\d{3})*\.\d{2}',
                'date_pattern': r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            },
            'w2': {
                'keywords': ['w-2', 'w2', 'wage and tax statement', 'social security', 'federal income tax'],
                'ssn_pattern': r'\d{3}-\d{2}-\d{4}',
                'ein_pattern': r'\d{2}-\d{7}',
            },
            '1099': {
                'keywords': ['1099', 'misc', 'div', 'int', 'interest', 'dividends'],
                'amount_pattern': r'\$?\d{1,3}(?:,\d{3})*\.\d{2}',
                'tin_pattern': r'\d{2}-\d{7}|\d{3}-\d{2}-\d{4}',
            }
        }

    def process_image(self, image_path: Path) -> Dict[str, Any]:
        """
        Process an image file and extract text and data.

        Args:
            image_path: Path to the image file

        Returns:
            Dictionary containing extracted text and parsed data
        """
        try:
            # Validate input
            if not image_path.exists():
                raise InvalidInputException(f"Image file not found: {image_path}")

            # Load and preprocess image
            image = self._load_and_preprocess_image(str(image_path))

            # Extract text
            extracted_text = self._extract_text(image)

            # Classify document type
            doc_type = self._classify_document(extracted_text)

            # Parse document data
            parsed_data = self._parse_document_data(extracted_text, doc_type)

            return {
                'document_type': doc_type,
                'extracted_text': extracted_text,
                'parsed_data': parsed_data,
                'confidence': self._calculate_confidence(parsed_data),
                'processing_timestamp': datetime.now().isoformat(),
                'image_path': str(image_path)
            }

        except Exception as e:
            self.error_logger.track_error(
                error=e,
                context={"operation": "process_image", "image_path": str(image_path)}
            )
            raise ServiceExecutionException(f"Failed to process image: {str(e)}")

    def process_image_from_bytes(self, image_bytes: bytes, filename: str = "uploaded_image") -> Dict[str, Any]:
        """
        Process an image from bytes (for web uploads).

        Args:
            image_bytes: Raw image bytes
            filename: Original filename

        Returns:
            Dictionary containing extracted text and parsed data
        """
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))

            # Convert to OpenCV format
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # Preprocess
            processed_image = self._preprocess_image(opencv_image)

            # Extract text
            extracted_text = self._extract_text(processed_image)

            # Classify and parse
            doc_type = self._classify_document(extracted_text)
            parsed_data = self._parse_document_data(extracted_text, doc_type)

            return {
                'document_type': doc_type,
                'extracted_text': extracted_text,
                'parsed_data': parsed_data,
                'confidence': self._calculate_confidence(parsed_data),
                'processing_timestamp': datetime.now().isoformat(),
                'filename': filename
            }

        except Exception as e:
            self.error_logger.track_error(
                error=e,
                context={"operation": "process_image_from_bytes", "filename": filename}
            )
            raise ServiceExecutionException(f"Failed to process image bytes: {str(e)}")

    def _load_and_preprocess_image(self, image_path: str) -> np.ndarray:
        """Load image from file and preprocess for OCR."""
        # Read image
        image = cv2.imread(image_path)

        if image is None:
            raise InvalidInputException(f"Could not load image: {image_path}")

        # Preprocess for better OCR
        return self._preprocess_image(image)

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR accuracy.

        Applies: grayscale, noise reduction, thresholding, morphological operations
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Noise reduction
        denoised = cv2.medianBlur(gray, 3)

        # Adaptive thresholding for better text extraction
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        # Morphological operations to clean up
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel)

        return processed

    def _extract_text(self, image: np.ndarray) -> str:
        """
        Extract text from preprocessed image using EasyOCR.

        Args:
            image: Preprocessed image array

        Returns:
            Extracted text as string
        """
        if self.reader is None:
            raise ServiceExecutionException("OCR reader not initialized")

        try:
            # EasyOCR expects RGB format, convert if necessary
            if len(image.shape) == 2:  # Grayscale
                rgb_image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            else:
                rgb_image = image

            # Extract text using EasyOCR
            # Returns list of tuples: [(bbox, text, confidence), ...]
            results = self.reader.readtext(rgb_image, detail=1)

            # Combine all detected text with high confidence
            text_lines = []
            for (bbox, text, confidence) in results:
                if confidence > 0.5:  # Only include reasonably confident detections
                    text_lines.append(text)

            # Join lines with newlines to preserve structure
            return '\n'.join(text_lines)

        except Exception as e:
            self.error_logger.log_error(e, "OCR text extraction failed")
            return ""

    def _classify_document(self, text: str) -> str:
        """
        Classify document type based on extracted text.

        Returns: 'receipt', 'w2', '1099', or 'unknown'
        """
        text_lower = text.lower()

        # Count keyword matches for each document type
        scores = {}
        for doc_type, patterns in self.document_patterns.items():
            score = 0
            for keyword in patterns['keywords']:
                if keyword in text_lower:
                    score += 1
            scores[doc_type] = score

        # Return highest scoring document type
        if scores:
            best_match = max(scores, key=scores.get)
            if scores[best_match] > 0:
                return best_match

        return 'unknown'

    def _parse_document_data(self, text: str, doc_type: str) -> Dict[str, Any]:
        """Parse extracted text into structured data based on document type."""
        if doc_type == 'receipt':
            return self._parse_receipt(text)
        elif doc_type == 'w2':
            return self._parse_w2(text)
        elif doc_type == '1099':
            return self._parse_1099(text)
        else:
            return self._parse_generic(text)

    def _parse_receipt(self, text: str) -> Dict[str, Any]:
        """Parse receipt data."""
        data = {
            'vendor_name': None,
            'date': None,
            'total_amount': None,
            'tax_amount': None,
            'items': []
        }

        lines = text.split('\n')

        # Extract vendor name (usually first non-empty line)
        for line in lines:
            line = line.strip()
            if line and len(line) > 3 and not line.replace('.', '').replace(' ', '').isdigit():
                data['vendor_name'] = line
                break

        # Extract amounts
        amounts = re.findall(r'\$?(\d{1,3}(?:,\d{3})*\.\d{2})', text)
        if amounts:
            # Assume last amount is total
            data['total_amount'] = float(amounts[-1].replace(',', ''))

            # Look for tax amount
            for line in lines:
                if 'tax' in line.lower():
                    tax_matches = re.findall(r'\$?(\d{1,3}(?:,\d{3})*\.\d{2})', line)
                    if tax_matches:
                        data['tax_amount'] = float(tax_matches[0].replace(',', ''))
                        break

        # Extract date
        date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text)
        if date_match:
            data['date'] = date_match.group(1)

        return data

    def _parse_w2(self, text: str) -> Dict[str, Any]:
        """Parse W-2 form data."""
        data = {
            'employee_ssn': None,
            'employer_ein': None,
            'wages_tips': None,
            'federal_income_tax': None,
            'social_security_wages': None,
            'social_security_tax': None,
            'medicare_wages': None,
            'medicare_tax': None
        }

        # Extract SSN
        ssn_match = re.search(r'(\d{3}-\d{2}-\d{4})', text)
        if ssn_match:
            data['employee_ssn'] = ssn_match.group(1)

        # Extract EIN
        ein_match = re.search(r'(\d{2}-\d{7})', text)
        if ein_match:
            data['employer_ein'] = ein_match.group(1)

        # Extract box values (simplified - would need more sophisticated parsing for real W-2)
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if 'wages' in line_lower and 'tips' in line_lower:
                amount_match = re.search(r'\$?(\d{1,3}(?:,\d{3})*\.\d{2})', line)
                if amount_match:
                    data['wages_tips'] = float(amount_match.group(1).replace(',', ''))

        return data

    def _parse_1099(self, text: str) -> Dict[str, Any]:
        """Parse 1099 form data."""
        data = {
            'payer_tin': None,
            'recipient_tin': None,
            'amount': None,
            'federal_income_tax': None,
            'form_type': None
        }

        # Determine form type
        text_lower = text.lower()
        if 'div' in text_lower:
            data['form_type'] = '1099-DIV'
        elif 'int' in text_lower:
            data['form_type'] = '1099-INT'
        elif 'misc' in text_lower:
            data['form_type'] = '1099-MISC'

        # Extract TINs
        tins = re.findall(r'\d{2}-\d{7}|\d{3}-\d{2}-\d{4}', text)
        if len(tins) >= 1:
            data['payer_tin'] = tins[0]
        if len(tins) >= 2:
            data['recipient_tin'] = tins[1]

        # Extract amounts
        amounts = re.findall(r'\$?(\d{1,3}(?:,\d{3})*\.\d{2})', text)
        if amounts:
            data['amount'] = float(amounts[0].replace(',', ''))

        return data

    def _parse_generic(self, text: str) -> Dict[str, Any]:
        """Parse generic document data."""
        return {
            'extracted_text': text,
            'word_count': len(text.split()),
            'line_count': len(text.split('\n')),
            'contains_numbers': bool(re.search(r'\d', text)),
            'contains_currency': bool(re.search(r'\$|\d+\.\d{2}', text))
        }

    def _calculate_confidence(self, parsed_data: Dict[str, Any]) -> float:
        """Calculate confidence score for parsed data."""
        confidence = 0.0
        total_fields = 0

        for key, value in parsed_data.items():
            total_fields += 1
            if value is not None and value != "":
                confidence += 1.0

        return confidence / total_fields if total_fields > 0 else 0.0

    def validate_easyocr_installation(self) -> bool:
        """
        Validate that EasyOCR is properly installed and initialized.

        Returns:
            True if EasyOCR is available, False otherwise
        """
        try:
            return self.reader is not None
        except Exception:
            return False

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported OCR languages.

        Returns:
            List of language codes supported by EasyOCR
        """
        # EasyOCR supports many languages, but we initialized with English
        # In a full implementation, you could check what languages are available
        try:
            if self.reader is not None:
                return ['en']  # English is what we initialized with
            else:
                return []
        except Exception:
            return []