#!/usr/bin/env python3
"""
Simple usage example of the textbook parser pipeline.
"""

from pathlib import Path
from src.config import PipelineConfig
from src.pipeline import TextbookPipeline


def main():
    """Simple example of processing a textbook."""

    # Create configuration
    config = PipelineConfig(
        book_url="https://example.com/textbook",
        book_title="Example Textbook",
        output_dir=Path("output/example"),
    )

    # Configure OCR for Georgian text
    config.ocr.engine = "tesseract"
    config.ocr.languages = ["kat", "eng"]

    # Configure illustration interpretation (requires API key)
    # config.openai_api_key = "your-api-key-here"

    # Initialize and run pipeline
    pipeline = TextbookPipeline(config)

    # Run complete pipeline
    summary = pipeline.run(
        skip_retrieval=False,  # Set to True if images already downloaded
        skip_illustration_interpretation=True,  # Set to False if you have API key
    )

    print(f"\n✓ Processing complete!")
    print(f"Pages processed: {summary.get('pages_analyzed', 0)}")
    print(f"Text extracted: {summary.get('total_words', 0)} words")
    print(f"Output directory: {config.output_dir}")


if __name__ == "__main__":
    main()
