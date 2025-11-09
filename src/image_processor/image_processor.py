"""
Image Processor Module

Processes page images to improve OCR accuracy:
- Masks illustrations with white rectangles
- Crops and saves illustration regions
- Applies image enhancement techniques
"""

from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance
from loguru import logger


class ImageProcessor:
    """
    Processes book page images for optimal OCR and illustration extraction.

    Main operations:
    - Mask illustration regions to improve OCR
    - Extract and save individual illustrations
    - Apply image enhancements (contrast, brightness, etc.)
    """

    def __init__(
        self,
        mask_color: Tuple[int, int, int] = (255, 255, 255),
        padding: int = 5,
    ):
        """
        Initialize the image processor.

        Args:
            mask_color: RGB color for masking illustrations (default: white)
            padding: Additional padding around illustration bboxes (pixels)
        """
        self.mask_color = mask_color
        self.padding = padding

    def process_page(
        self,
        image_path: Path,
        layout_data: Dict[str, Any],
        output_cleaned_path: Path,
        output_illustrations_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Process a single page image.

        Args:
            image_path: Path to original page image
            layout_data: Layout analysis data with bounding boxes
            output_cleaned_path: Path to save cleaned (masked) image
            output_illustrations_dir: Directory to save cropped illustrations

        Returns:
            Processing metadata
        """
        logger.debug(f"Processing page: {image_path}")

        # Load image
        image = Image.open(image_path)
        original_size = image.size

        # Create a copy for masking
        masked_image = image.copy()

        # Extract and save illustrations
        illustration_paths = []
        if output_illustrations_dir and "illustrations" in layout_data:
            illustration_paths = self._extract_illustrations(
                image, layout_data["illustrations"], output_illustrations_dir, image_path.stem
            )

        # Mask illustrations for clean OCR
        if "illustrations" in layout_data:
            masked_image = self._mask_regions(masked_image, layout_data["illustrations"])

        # Optionally mask other non-text regions (tables, etc.)
        for region_type in ["tables", "other"]:
            if region_type in layout_data and layout_data[region_type]:
                # Only mask if they're large enough to interfere with OCR
                large_regions = [
                    r for r in layout_data[region_type]
                    if self._calculate_area(r["bbox"]) > 10000
                ]
                if large_regions:
                    masked_image = self._mask_regions(masked_image, large_regions)

        # Apply image enhancements for better OCR
        masked_image = self._enhance_for_ocr(masked_image)

        # Save cleaned image
        output_cleaned_path.parent.mkdir(parents=True, exist_ok=True)
        masked_image.save(output_cleaned_path)
        logger.debug(f"Saved cleaned image: {output_cleaned_path}")

        return {
            "original_path": str(image_path),
            "cleaned_path": str(output_cleaned_path),
            "original_size": original_size,
            "illustrations_count": len(illustration_paths),
            "illustration_paths": [str(p) for p in illustration_paths],
        }

    def _mask_regions(
        self, image: Image.Image, regions: List[Dict[str, Any]]
    ) -> Image.Image:
        """
        Mask specified regions with a solid color.

        Args:
            image: PIL Image
            regions: List of region dictionaries with 'bbox' key

        Returns:
            Masked image
        """
        draw = ImageDraw.Draw(image)

        for region in regions:
            bbox = region["bbox"]
            # Expand bbox with padding
            x1 = max(0, bbox[0] - self.padding)
            y1 = max(0, bbox[1] - self.padding)
            x2 = min(image.width, bbox[2] + self.padding)
            y2 = min(image.height, bbox[3] + self.padding)

            # Draw filled rectangle
            draw.rectangle([x1, y1, x2, y2], fill=self.mask_color)

        return image

    def _extract_illustrations(
        self,
        image: Image.Image,
        illustrations: List[Dict[str, Any]],
        output_dir: Path,
        page_name: str,
    ) -> List[Path]:
        """
        Extract and save individual illustration crops.

        Args:
            image: Original page image
            illustrations: List of illustration dictionaries
            output_dir: Directory to save illustrations
            page_name: Name of the page (for filename)

        Returns:
            List of paths to saved illustrations
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        saved_paths = []

        for idx, illus in enumerate(illustrations, 1):
            bbox = illus["bbox"]

            # Crop illustration with padding
            x1 = max(0, bbox[0] - self.padding)
            y1 = max(0, bbox[1] - self.padding)
            x2 = min(image.width, bbox[2] + self.padding)
            y2 = min(image.height, bbox[3] + self.padding)

            cropped = image.crop((x1, y1, x2, y2))

            # Save
            output_path = output_dir / f"{page_name}_illus_{idx:02d}.png"
            cropped.save(output_path)
            saved_paths.append(output_path)
            logger.debug(f"Saved illustration: {output_path}")

        return saved_paths

    def _enhance_for_ocr(self, image: Image.Image) -> Image.Image:
        """
        Apply image enhancements to improve OCR accuracy.

        Args:
            image: Input image

        Returns:
            Enhanced image
        """
        # Convert to grayscale if needed for certain enhancements
        # But return in original mode for compatibility

        # Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)

        # Increase sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.3)

        return image

    def _calculate_area(self, bbox: List[int]) -> int:
        """Calculate area of a bounding box."""
        return (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])

    def process_batch(
        self,
        image_dir: Path,
        layout_results: Dict[str, Dict[str, Any]],
        output_cleaned_dir: Path,
        output_illustrations_dir: Optional[Path] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Process a batch of page images.

        Args:
            image_dir: Directory containing original images
            layout_results: Layout analysis results for all pages
            output_cleaned_dir: Directory to save cleaned images
            output_illustrations_dir: Directory to save illustrations

        Returns:
            Processing metadata for all pages
        """
        logger.info(f"Processing batch from {image_dir}")

        results = {}
        for page_name, layout_data in layout_results.items():
            # Find the corresponding image file
            image_path = None
            for ext in [".png", ".jpg", ".jpeg"]:
                candidate = image_dir / f"{page_name}{ext}"
                if candidate.exists():
                    image_path = candidate
                    break

            if not image_path:
                logger.warning(f"Image not found for page: {page_name}")
                continue

            # Process the page
            output_cleaned_path = output_cleaned_dir / f"{page_name}.png"

            try:
                metadata = self.process_page(
                    image_path,
                    layout_data,
                    output_cleaned_path,
                    output_illustrations_dir,
                )
                results[page_name] = metadata
            except Exception as e:
                logger.error(f"Failed to process {page_name}: {e}")

        logger.info(f"Processed {len(results)} pages")
        return results

    @staticmethod
    def apply_deskew(image: Image.Image) -> Image.Image:
        """
        Detect and correct skew in the image.

        Args:
            image: Input image

        Returns:
            Deskewed image
        """
        # Convert PIL to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # Convert to grayscale
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Detect lines using Hough transform
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

        if lines is None:
            return image

        # Calculate average angle
        angles = []
        for rho, theta in lines[:, 0]:
            angle = np.degrees(theta) - 90
            angles.append(angle)

        median_angle = np.median(angles)

        # Rotate image
        if abs(median_angle) > 0.5:  # Only rotate if significant skew
            height, width = cv_image.shape[:2]
            center = (width // 2, height // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
            rotated = cv2.warpAffine(
                cv_image, rotation_matrix, (width, height),
                flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
            )

            # Convert back to PIL
            return Image.fromarray(cv2.cvtColor(rotated, cv2.COLOR_BGR2RGB))

        return image

    @staticmethod
    def remove_noise(image: Image.Image) -> Image.Image:
        """
        Remove noise from the image.

        Args:
            image: Input image

        Returns:
            Denoised image
        """
        # Convert to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # Apply bilateral filter to reduce noise while preserving edges
        denoised = cv2.bilateralFilter(cv_image, 9, 75, 75)

        # Convert back to PIL
        return Image.fromarray(cv2.cvtColor(denoised, cv2.COLOR_BGR2RGB))
