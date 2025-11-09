"""
Layout Analyzer Module

Uses LayoutParser and Detectron2 to segment book pages into different regions:
- Text blocks
- Illustrations/figures
- Captions
- Tables
- Titles/headers
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import json
from loguru import logger
import cv2
import numpy as np

try:
    import layoutparser as lp
    LAYOUTPARSER_AVAILABLE = True
except ImportError:
    LAYOUTPARSER_AVAILABLE = False
    logger.warning("LayoutParser not available. Install with: pip install layoutparser[layoutmodels]")


class BoundingBox:
    """Represents a bounding box with coordinates and metadata."""

    def __init__(self, x1: float, y1: float, x2: float, y2: float, label: str, score: float):
        self.x1 = int(x1)
        self.y1 = int(y1)
        self.x2 = int(x2)
        self.y2 = int(y2)
        self.label = label
        self.score = score

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "bbox": [self.x1, self.y1, self.x2, self.y2],
            "label": self.label,
            "score": self.score,
        }

    def area(self) -> int:
        """Calculate the area of the bounding box."""
        return (self.x2 - self.x1) * (self.y2 - self.y1)

    def expand(self, padding: int) -> "BoundingBox":
        """Expand the bounding box by padding pixels."""
        return BoundingBox(
            max(0, self.x1 - padding),
            max(0, self.y1 - padding),
            self.x2 + padding,
            self.y2 + padding,
            self.label,
            self.score,
        )


class PageLayout:
    """Represents the layout analysis result for a single page."""

    def __init__(self, page_path: Path):
        self.page_path = page_path
        self.text_blocks: List[BoundingBox] = []
        self.illustrations: List[BoundingBox] = []
        self.captions: List[BoundingBox] = []
        self.titles: List[BoundingBox] = []
        self.tables: List[BoundingBox] = []
        self.other: List[BoundingBox] = []

    def add_element(self, bbox: BoundingBox) -> None:
        """Add a layout element to the appropriate category."""
        label_lower = bbox.label.lower()

        if "text" in label_lower or "paragraph" in label_lower:
            self.text_blocks.append(bbox)
        elif "figure" in label_lower or "image" in label_lower:
            self.illustrations.append(bbox)
        elif "caption" in label_lower:
            self.captions.append(bbox)
        elif "title" in label_lower or "heading" in label_lower:
            self.titles.append(bbox)
        elif "table" in label_lower:
            self.tables.append(bbox)
        else:
            self.other.append(bbox)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "page_path": str(self.page_path),
            "text_blocks": [bbox.to_dict() for bbox in self.text_blocks],
            "illustrations": [bbox.to_dict() for bbox in self.illustrations],
            "captions": [bbox.to_dict() for bbox in self.captions],
            "titles": [bbox.to_dict() for bbox in self.titles],
            "tables": [bbox.to_dict() for bbox in self.tables],
            "other": [bbox.to_dict() for bbox in self.other],
        }


class LayoutAnalyzer:
    """
    Analyzes document layout to detect and classify different regions.

    Uses LayoutParser with pre-trained models for document understanding.
    """

    def __init__(
        self,
        model_name: str = "lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config",
        confidence_threshold: float = 0.5,
        device: str = "cpu",
    ):
        """
        Initialize the layout analyzer.

        Args:
            model_name: LayoutParser model identifier
            confidence_threshold: Minimum confidence score for detections
            device: Device to run model on ("cpu" or "cuda")
        """
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.device = device
        self.model = None

        if LAYOUTPARSER_AVAILABLE:
            self._load_model()
        else:
            logger.warning("LayoutParser not available. Using fallback heuristics.")

    def _load_model(self) -> None:
        """Load the layout detection model."""
        try:
            logger.info(f"Loading layout model: {self.model_name}")
            self.model = lp.Detectron2LayoutModel(
                config_path=self.model_name,
                extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", self.confidence_threshold],
                label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"},
            )
            logger.info("Layout model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load layout model: {e}")
            self.model = None

    def analyze_page(self, image_path: Path) -> PageLayout:
        """
        Analyze a single page image to detect layout elements.

        Args:
            image_path: Path to the page image

        Returns:
            PageLayout object with detected elements
        """
        logger.debug(f"Analyzing layout: {image_path}")

        page_layout = PageLayout(image_path)

        # Load image
        image = cv2.imread(str(image_path))
        if image is None:
            logger.error(f"Failed to load image: {image_path}")
            return page_layout

        if self.model is not None:
            # Use LayoutParser for detection
            try:
                layout = self.model.detect(image)

                for block in layout:
                    bbox = BoundingBox(
                        x1=block.block.x_1,
                        y1=block.block.y_1,
                        x2=block.block.x_2,
                        y2=block.block.y_2,
                        label=block.type,
                        score=block.score,
                    )
                    page_layout.add_element(bbox)

                logger.debug(
                    f"Detected {len(page_layout.illustrations)} illustrations, "
                    f"{len(page_layout.text_blocks)} text blocks"
                )
            except Exception as e:
                logger.error(f"Layout detection failed: {e}")
                # Fall back to heuristics
                self._fallback_detection(image, page_layout)
        else:
            # Use fallback heuristics
            self._fallback_detection(image, page_layout)

        return page_layout

    def _fallback_detection(self, image: np.ndarray, page_layout: PageLayout) -> None:
        """
        Fallback layout detection using simple image processing heuristics.

        This is used when LayoutParser is not available or fails.
        """
        logger.debug("Using fallback detection heuristics")

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply thresholding
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        height, width = image.shape[:2]
        min_area = (width * height) * 0.01  # Minimum 1% of page area

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue

            x, y, w, h = cv2.boundingRect(contour)

            # Heuristic: Assume larger regions with high aspect ratio variance are illustrations
            aspect_ratio = w / h if h > 0 else 0

            if area > (width * height) * 0.1 and 0.3 < aspect_ratio < 3:
                # Likely an illustration
                bbox = BoundingBox(x, y, x + w, y + h, "Figure", 0.5)
                page_layout.add_element(bbox)
            else:
                # Likely text
                bbox = BoundingBox(x, y, x + w, y + h, "Text", 0.5)
                page_layout.add_element(bbox)

    def analyze_directory(
        self, image_dir: Path, output_path: Optional[Path] = None
    ) -> Dict[str, PageLayout]:
        """
        Analyze all images in a directory.

        Args:
            image_dir: Directory containing page images
            output_path: Optional path to save results as JSON

        Returns:
            Dictionary mapping page names to PageLayout objects
        """
        logger.info(f"Analyzing directory: {image_dir}")

        results = {}
        image_files = sorted(image_dir.glob("*.png")) + sorted(image_dir.glob("*.jpg"))

        for image_path in image_files:
            page_layout = self.analyze_page(image_path)
            results[image_path.stem] = page_layout

        logger.info(f"Analyzed {len(results)} pages")

        # Save results if output path specified
        if output_path:
            self.save_results(results, output_path)

        return results

    def save_results(self, results: Dict[str, PageLayout], output_path: Path) -> None:
        """
        Save layout analysis results to JSON file.

        Args:
            results: Dictionary of page layouts
            output_path: Path to output JSON file
        """
        output_data = {
            page_name: layout.to_dict() for page_name, layout in results.items()
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved layout results to {output_path}")

    @staticmethod
    def load_results(input_path: Path) -> Dict[str, Dict[str, Any]]:
        """
        Load layout analysis results from JSON file.

        Args:
            input_path: Path to JSON file

        Returns:
            Dictionary of layout data
        """
        with open(input_path, "r", encoding="utf-8") as f:
            return json.load(f)
