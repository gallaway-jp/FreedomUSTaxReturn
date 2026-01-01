# OCR Setup Guide

This guide explains how to set up OCR (Optical Character Recognition) functionality for receipt scanning in Freedom US Tax Return.

## Prerequisites

### 1. Install EasyOCR

EasyOCR is a Python library that provides OCR capabilities without requiring external dependencies like Tesseract.

**EasyOCR is automatically installed when you install the application dependencies:**

```bash
pip install -r requirements.txt
```

EasyOCR includes pre-trained models and works out-of-the-box without additional installation steps.

## Configuration

### Environment Variables (Optional)

EasyOCR doesn't require external configuration, but you can control GPU usage if needed:

```bash
# Force CPU usage (recommended for compatibility)
set EASYOCR_GPU=False
```

### Application Configuration

The application automatically initializes EasyOCR with English language support. No additional configuration is required.

## Usage

### GUI Interface

1. Launch the Freedom US Tax Return application
2. Navigate to the Analytics section
3. Click "Receipt Scanning" button
4. Upload receipt images or use camera capture (mobile)
5. OCR will automatically extract text and categorize expenses

### Programmatic Usage

```python
from config.app_config import AppConfig
from services.receipt_scanning_service import ReceiptScanningService

config = AppConfig()
scanner = ReceiptScanningService(config)

# Scan a receipt image
result = scanner.scan_receipt("path/to/receipt.jpg")
if result.success:
    print(f"Vendor: {result.receipt_data.vendor_name}")
    print(f"Total: ${result.receipt_data.total_amount}")
    print(f"Category: {result.receipt_data.category}")
```

## Features

- **Automatic Text Extraction**: High-accuracy OCR from receipt images using EasyOCR
- **Intelligent Parsing**: Extracts vendor, amount, date, and tax information
- **Tax Categorization**: Automatic classification into tax-relevant categories
- **Quality Assessment**: Image quality scoring for OCR confidence
- **Batch Processing**: Process multiple receipts simultaneously
- **Mobile Integration**: Camera support via web interface

## Troubleshooting

### EasyOCR Import Error
```
ModuleNotFoundError: No module named 'easyocr'
```

**Solution:**
```bash
pip install easyocr
```

### Memory Issues
EasyOCR can be memory-intensive with large images.

**Solutions:**
- Resize large images before processing
- Use CPU mode (default): `EASYOCR_GPU=False`
- Process images one at a time for batch operations

### Poor OCR Quality
- Ensure images are well-lit and focused
- Use higher resolution images when possible
- Avoid skewed or rotated images
- Clean receipts before scanning

### Performance Issues
- EasyOCR may take longer to initialize on first use (downloads models)
- Subsequent uses are faster as models are cached
- Consider using GPU if available: `EASYOCR_GPU=True`

## Technical Details

### Dependencies
- `easyocr>=1.7.0`: OCR text extraction (includes pre-trained models)
- `opencv-python`: Image processing and preprocessing
- `numpy`: Numerical operations for image processing

### Supported Image Formats
- JPEG/JPG
- PNG
- BMP
- TIFF
- PDF (converted to images)

### OCR Configuration
- **Language**: English (en)
- **GPU Usage**: Disabled by default for compatibility
- **Detection Confidence**: >0.3 for receipts, >0.5 for documents
- **Text Recognition**: Transformer-based models included

## Testing

Run the comprehensive test suite:

```bash
python -m pytest tests/ -v -k "ocr or receipt"
```

Or run the specific OCR test:

```bash
python test_ocr.py
```

## Advantages of EasyOCR

- **No External Dependencies**: Works immediately after pip install
- **Pre-trained Models**: No need to download or configure Tesseract
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Modern Architecture**: Uses deep learning for better accuracy
- **Active Development**: Regularly updated with improvements