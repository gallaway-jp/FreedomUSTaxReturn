"""
Image Processing Utilities for Receipt Scanning

This module provides utilities for preprocessing receipt images
to improve OCR accuracy and quality assessment.
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ReceiptImageProcessor:
    """
    Utility class for preprocessing receipt images for OCR.

    Provides methods for:
    - Image enhancement and noise reduction
    - Perspective correction
    - Contrast and brightness adjustment
    - Quality assessment
    """

    @staticmethod
    def preprocess_image(image_path: str) -> Tuple[np.ndarray, float]:
        """
        Preprocess an image for OCR processing.

        Args:
            image_path: Path to the image file

        Returns:
            Tuple of (processed_image, quality_score)
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")

            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Assess initial quality
            initial_quality = ReceiptImageProcessor._calculate_quality_score(gray)

            # Apply preprocessing steps
            processed = ReceiptImageProcessor._enhance_image(gray)
            processed = ReceiptImageProcessor._reduce_noise(processed)
            processed = ReceiptImageProcessor._correct_skew(processed)
            processed = ReceiptImageProcessor._binarize_image(processed)

            # Calculate final quality score
            final_quality = ReceiptImageProcessor._calculate_quality_score(processed)

            return processed, final_quality

        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            # Return original image if processing fails
            fallback_image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if fallback_image is None:
                raise ValueError(f"Could not load image: {image_path}")
            return fallback_image, 0.0

    @staticmethod
    def _enhance_image(image: np.ndarray) -> np.ndarray:
        """
        Enhance image contrast and brightness.

        Args:
            image: Input grayscale image

        Returns:
            Enhanced image
        """
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(image)

        # Additional contrast enhancement
        enhanced = cv2.convertScaleAbs(enhanced, alpha=1.2, beta=10)

        return enhanced

    @staticmethod
    def _reduce_noise(image: np.ndarray) -> np.ndarray:
        """
        Reduce noise in the image.

        Args:
            image: Input image

        Returns:
            Denoised image
        """
        # Apply bilateral filter to reduce noise while preserving edges
        denoised = cv2.bilateralFilter(image, 9, 75, 75)

        # Apply median blur for additional noise reduction
        denoised = cv2.medianBlur(denoised, 3)

        return denoised

    @staticmethod
    def _correct_skew(image: np.ndarray) -> np.ndarray:
        """
        Correct skew in the image.

        Args:
            image: Input image

        Returns:
            Deskewed image
        """
        try:
            # Find contours to detect text regions
            contours, _ = cv2.findContours(image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

            if not contours:
                return image

            # Find the largest contour (likely the receipt)
            largest_contour = max(contours, key=cv2.contourArea)

            # Get minimum area rectangle
            rect = cv2.minAreaRect(largest_contour)
            angle = rect[2]

            # Correct angle if needed
            if abs(angle) > 5:  # Only correct if skew is significant
                # Get rotation matrix
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)

                # Rotate image
                rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC,
                                        borderMode=cv2.BORDER_REPLICATE)
                return rotated

        except Exception as e:
            logger.warning(f"Skew correction failed: {e}")

        return image

    @staticmethod
    def _binarize_image(image: np.ndarray) -> np.ndarray:
        """
        Convert image to binary (black and white).

        Args:
            image: Input grayscale image

        Returns:
            Binarized image
        """
        # Apply Gaussian blur to reduce noise before thresholding
        blurred = cv2.GaussianBlur(image, (5, 5), 0)

        # Use adaptive thresholding for better results on varying lighting
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        # Apply morphological operations to clean up the image
        kernel = np.ones((1, 1), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        return binary

    @staticmethod
    def _calculate_quality_score(image: np.ndarray) -> float:
        """
        Calculate a quality score for the image.

        Args:
            image: Input image

        Returns:
            Quality score between 0-100
        """
        try:
            # Sharpness using Laplacian variance
            laplacian_var = cv2.Laplacian(image, cv2.CV_64F).var()
            sharpness = min(100, laplacian_var / 500 * 100)

            # Contrast
            contrast = image.std()
            contrast_score = min(100, contrast / 64 * 100)

            # Brightness
            brightness = np.mean(image)
            brightness_score = 100 - abs(brightness - 128) / 128 * 100

            # Overall quality score
            quality = (sharpness * 0.4 + contrast_score * 0.3 + brightness_score * 0.3)

            return max(0, min(100, quality))

        except Exception:
            return 50.0  # Default medium quality

    @staticmethod
    def resize_for_ocr(image: np.ndarray, target_height: int = 1000) -> np.ndarray:
        """
        Resize image to optimal height for OCR while maintaining aspect ratio.

        Args:
            image: Input image
            target_height: Target height in pixels

        Returns:
            Resized image
        """
        height, width = image.shape[:2]
        aspect_ratio = width / height

        new_width = int(target_height * aspect_ratio)
        resized = cv2.resize(image, (new_width, target_height), interpolation=cv2.INTER_CUBIC)

        return resized

    @staticmethod
    def detect_receipt_region(image: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        Detect the receipt region in an image.

        Args:
            image: Input image

        Returns:
            Bounding box (x, y, w, h) of receipt region or None
        """
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150)

            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if not contours:
                return None

            # Find the largest contour that could be a receipt
            # Receipts are typically rectangular and have reasonable aspect ratios
            valid_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < 10000:  # Too small
                    continue

                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)

                # Check aspect ratio (receipts are usually taller than wide)
                aspect_ratio = h / w if w > 0 else 0
                if 1.2 < aspect_ratio < 5.0:  # Reasonable receipt aspect ratio
                    valid_contours.append((contour, area, (x, y, w, h)))

            if valid_contours:
                # Return the bounding box of the largest valid contour
                _, _, bbox = max(valid_contours, key=lambda x: x[1])
                return bbox

        except Exception as e:
            logger.warning(f"Receipt region detection failed: {e}")

        return None

    @staticmethod
    def crop_to_receipt(image: np.ndarray) -> np.ndarray:
        """
        Crop image to the detected receipt region.

        Args:
            image: Input image

        Returns:
            Cropped image
        """
        bbox = ReceiptImageProcessor.detect_receipt_region(image)

        if bbox:
            x, y, w, h = bbox
            # Add some padding
            padding = 10
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(image.shape[1] - x, w + 2 * padding)
            h = min(image.shape[0] - y, h + 2 * padding)

            cropped = image[y:y+h, x:x+w]
            return cropped

        return image  # Return original if no receipt detected

    @staticmethod
    def enhance_text_contrast(image: np.ndarray) -> np.ndarray:
        """
        Enhance text contrast for better OCR.

        Args:
            image: Input binary image

        Returns:
            Enhanced image
        """
        # Apply dilation to make text thicker
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        dilated = cv2.dilate(image, kernel, iterations=1)

        # Apply erosion to clean up
        eroded = cv2.erode(dilated, kernel, iterations=1)

        return eroded

    @staticmethod
    def save_processed_image(image: np.ndarray, output_path: str) -> bool:
        """
        Save processed image to file.

        Args:
            image: Image to save
            output_path: Output file path

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert to PIL Image for better saving options
            if len(image.shape) == 2:  # Grayscale
                pil_image = Image.fromarray(image)
            else:  # Color
                pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

            pil_image.save(output_path)
            return True

        except Exception as e:
            logger.error(f"Failed to save image: {e}")
            return False