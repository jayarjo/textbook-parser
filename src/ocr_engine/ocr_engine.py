"""
OCR Engine Module

Extracts text from page images using various OCR engines:
- Tesseract OCR (with Georgian language support)
- PaddleOCR (multilingual support)
- Google Cloud Vision API (optional, high accuracy)
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import json
from loguru import logger

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("Tesseract not available. Install with: pip install pytesseract")

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    logger.warning("PaddleOCR not available. Install with: pip install paddleocr")

from PIL import Image
import re


class OCRResult:
    """Represents OCR result for a single page."""

    def __init__(self, page_path: Path):
        self.page_path = page_path
        self.text: str = ""
        self.confidence: float = 0.0
        self.line_data: List[Dict[str, Any]] = []
        self.word_count: int = 0
        self.char_count: int = 0

    def add_text(self, text: str, confidence: float = 100.0) -> None:
        """Add text to the result."""
        self.text += text
        self.confidence = confidence
        self.word_count = len(self.text.split())
        self.char_count = len(self.text)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "page_path": str(self.page_path),
            "text": self.text,
            "confidence": self.confidence,
            "word_count": self.word_count,
            "char_count": self.char_count,
            "line_data": self.line_data,
        }


class OCREngine:
    """
    Performs OCR on page images to extract text.

    Supports multiple OCR backends with focus on Georgian language support.
    """

    def __init__(
        self,
        engine: str = "tesseract",
        languages: List[str] = None,
        tesseract_config: str = "--psm 6",
        confidence_threshold: float = 60.0,
    ):
        """
        Initialize the OCR engine.

        Args:
            engine: OCR engine to use ("tesseract" or "paddleocr")
            languages: List of language codes (e.g., ["kat", "eng"])
            tesseract_config: Tesseract configuration string
            confidence_threshold: Minimum confidence threshold for results
        """
        self.engine = engine.lower()
        self.languages = languages or ["kat", "eng"]
        self.tesseract_config = tesseract_config
        self.confidence_threshold = confidence_threshold
        self.ocr_instance = None

        self._initialize_engine()

    def _initialize_engine(self) -> None:
        """Initialize the selected OCR engine."""
        if self.engine == "tesseract":
            if not TESSERACT_AVAILABLE:
                raise RuntimeError("Tesseract is not available. Please install pytesseract.")
            logger.info("Using Tesseract OCR")

        elif self.engine == "paddleocr":
            if not PADDLEOCR_AVAILABLE:
                raise RuntimeError("PaddleOCR is not available. Please install paddleocr.")
            logger.info("Initializing PaddleOCR...")
            # Initialize PaddleOCR with specified languages
            self.ocr_instance = PaddleOCR(
                use_angle_cls=True,
                lang="en",  # PaddleOCR uses "en" for English, may need custom model for Georgian
                show_log=False,
            )
            logger.info("PaddleOCR initialized")

        else:
            raise ValueError(f"Unknown OCR engine: {self.engine}")

    def extract_text(self, image_path: Path) -> OCRResult:
        """
        Extract text from a single image.

        Args:
            image_path: Path to the image file

        Returns:
            OCRResult object with extracted text
        """
        logger.debug(f"Extracting text from: {image_path}")

        result = OCRResult(image_path)

        try:
            if self.engine == "tesseract":
                result = self._extract_with_tesseract(image_path)
            elif self.engine == "paddleocr":
                result = self._extract_with_paddleocr(image_path)

            logger.debug(
                f"Extracted {result.word_count} words "
                f"(confidence: {result.confidence:.1f}%)"
            )

        except Exception as e:
            logger.error(f"OCR failed for {image_path}: {e}")

        return result

    def _extract_with_tesseract(self, image_path: Path) -> OCRResult:
        """Extract text using Tesseract OCR."""
        result = OCRResult(image_path)

        # Load image
        image = Image.open(image_path)

        # Build language string
        lang_string = "+".join(self.languages)

        # Extract text with detailed data
        try:
            # Get detailed OCR data
            data = pytesseract.image_to_data(
                image,
                lang=lang_string,
                config=self.tesseract_config,
                output_type=pytesseract.Output.DICT,
            )

            # Process results
            lines = {}
            for i in range(len(data["text"])):
                conf = float(data["conf"][i])
                text = data["text"][i].strip()

                if conf < self.confidence_threshold or not text:
                    continue

                block_num = data["block_num"][i]
                line_num = data["line_num"][i]
                key = f"{block_num}_{line_num}"

                if key not in lines:
                    lines[key] = {
                        "text": "",
                        "confidences": [],
                        "bbox": [
                            data["left"][i],
                            data["top"][i],
                            data["left"][i] + data["width"][i],
                            data["top"][i] + data["height"][i],
                        ],
                    }

                lines[key]["text"] += text + " "
                lines[key]["confidences"].append(conf)

            # Combine lines into full text
            full_text = []
            for line_data in lines.values():
                line_text = line_data["text"].strip()
                if line_text:
                    full_text.append(line_text)
                    result.line_data.append({
                        "text": line_text,
                        "confidence": sum(line_data["confidences"]) / len(line_data["confidences"]),
                        "bbox": line_data["bbox"],
                    })

            result.add_text(
                "\n".join(full_text),
                confidence=sum(ld["confidence"] for ld in result.line_data) / len(result.line_data)
                if result.line_data else 0.0,
            )

        except Exception as e:
            logger.error(f"Tesseract extraction failed: {e}")
            # Fallback to simple text extraction
            try:
                text = pytesseract.image_to_string(
                    image,
                    lang=lang_string,
                    config=self.tesseract_config,
                )
                result.add_text(text)
            except Exception as e2:
                logger.error(f"Fallback extraction also failed: {e2}")

        return result

    def _extract_with_paddleocr(self, image_path: Path) -> OCRResult:
        """Extract text using PaddleOCR."""
        result = OCRResult(image_path)

        try:
            # Run OCR
            ocr_result = self.ocr_instance.ocr(str(image_path), cls=True)

            if not ocr_result or not ocr_result[0]:
                return result

            # Process results
            lines = []
            confidences = []

            for line in ocr_result[0]:
                bbox = line[0]  # Bounding box coordinates
                text_info = line[1]  # (text, confidence)
                text = text_info[0]
                confidence = text_info[1] * 100  # Convert to percentage

                if confidence < self.confidence_threshold:
                    continue

                lines.append(text)
                confidences.append(confidence)

                result.line_data.append({
                    "text": text,
                    "confidence": confidence,
                    "bbox": bbox,
                })

            # Combine all text
            full_text = "\n".join(lines)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            result.add_text(full_text, avg_confidence)

        except Exception as e:
            logger.error(f"PaddleOCR extraction failed: {e}")

        return result

    def extract_batch(
        self,
        image_dir: Path,
        output_dir: Path,
        combine: bool = True,
    ) -> Dict[str, OCRResult]:
        """
        Extract text from multiple images.

        Args:
            image_dir: Directory containing images
            output_dir: Directory to save text files
            combine: If True, also create a combined text file

        Returns:
            Dictionary mapping page names to OCRResult objects
        """
        logger.info(f"Extracting text from {image_dir}")

        output_dir.mkdir(parents=True, exist_ok=True)
        results = {}

        # Find all image files
        image_files = sorted(image_dir.glob("*.png")) + sorted(image_dir.glob("*.jpg"))

        for image_path in image_files:
            page_name = image_path.stem

            # Extract text
            ocr_result = self.extract_text(image_path)
            results[page_name] = ocr_result

            # Save individual page text
            text_path = output_dir / f"{page_name}.txt"
            with open(text_path, "w", encoding="utf-8") as f:
                f.write(ocr_result.text)

        logger.info(f"Extracted text from {len(results)} pages")

        # Create combined text file
        if combine and results:
            combined_path = output_dir / "book_full.txt"
            with open(combined_path, "w", encoding="utf-8") as f:
                for page_name in sorted(results.keys()):
                    f.write(f"\n\n--- {page_name} ---\n\n")
                    f.write(results[page_name].text)

            logger.info(f"Created combined text file: {combined_path}")

        # Save metadata
        metadata_path = output_dir / "ocr_metadata.json"
        self.save_metadata(results, metadata_path)

        return results

    def save_metadata(self, results: Dict[str, OCRResult], output_path: Path) -> None:
        """Save OCR metadata to JSON file."""
        metadata = {
            page_name: result.to_dict() for page_name, result in results.items()
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved OCR metadata to {output_path}")

    @staticmethod
    def post_process_text(text: str) -> str:
        """
        Post-process extracted text to fix common OCR errors.

        Args:
            text: Raw OCR text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r" +", " ", text)
        text = re.sub(r"\n\n+", "\n\n", text)

        # Remove hyphenation at line breaks
        text = re.sub(r"-\n", "", text)

        # Fix common punctuation issues
        text = re.sub(r" ([.,!?;:])", r"\1", text)

        # Trim whitespace
        text = text.strip()

        return text
