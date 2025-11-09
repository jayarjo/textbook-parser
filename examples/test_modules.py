#!/usr/bin/env python3
"""
Test individual modules without running the full pipeline.
"""

from pathlib import Path
from src.ocr_engine import OCREngine
from src.layout_analyzer import LayoutAnalyzer
from src.image_processor import ImageProcessor


def test_ocr():
    """Test OCR on a single image."""
    print("Testing OCR Engine...")

    ocr = OCREngine(
        engine="tesseract",
        languages=["kat", "eng"],
        confidence_threshold=60.0,
    )

    # Test with an image (replace with actual path)
    test_image = Path("test_images/sample_page.png")

    if test_image.exists():
        result = ocr.extract_text(test_image)
        print(f"Extracted text: {result.text[:200]}...")
        print(f"Confidence: {result.confidence:.2f}%")
        print(f"Word count: {result.word_count}")
    else:
        print(f"Test image not found: {test_image}")


def test_layout_analyzer():
    """Test layout analysis on a single image."""
    print("\nTesting Layout Analyzer...")

    analyzer = LayoutAnalyzer(
        confidence_threshold=0.5,
        device="cpu",
    )

    # Test with an image
    test_image = Path("test_images/sample_page.png")

    if test_image.exists():
        layout = analyzer.analyze_page(test_image)
        print(f"Text blocks: {len(layout.text_blocks)}")
        print(f"Illustrations: {len(layout.illustrations)}")
        print(f"Tables: {len(layout.tables)}")
        print(f"Titles: {len(layout.titles)}")
    else:
        print(f"Test image not found: {test_image}")


def test_image_processor():
    """Test image processing."""
    print("\nTesting Image Processor...")

    processor = ImageProcessor(
        mask_color=(255, 255, 255),
        padding=5,
    )

    test_image = Path("test_images/sample_page.png")
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)

    if test_image.exists():
        # Create dummy layout data
        layout_data = {
            "illustrations": [
                {"bbox": [100, 100, 300, 300], "label": "Figure", "score": 0.9}
            ],
            "text_blocks": [
                {"bbox": [50, 400, 500, 600], "label": "Text", "score": 0.95}
            ],
        }

        result = processor.process_page(
            test_image,
            layout_data,
            output_dir / "cleaned.png",
            output_dir / "illustrations",
        )

        print(f"Processed image: {result['cleaned_path']}")
        print(f"Illustrations extracted: {result['illustrations_count']}")
    else:
        print(f"Test image not found: {test_image}")


def main():
    """Run all module tests."""
    print("=" * 60)
    print("Testing Individual Modules")
    print("=" * 60)

    test_ocr()
    test_layout_analyzer()
    test_image_processor()

    print("\n" + "=" * 60)
    print("Module testing complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
