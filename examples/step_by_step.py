#!/usr/bin/env python3
"""
Example of running pipeline steps individually for more control.
"""

from pathlib import Path
from src.config import PipelineConfig
from src.pipeline import TextbookPipeline


def main():
    """Run pipeline steps individually."""

    # Create configuration
    config = PipelineConfig(
        book_url="https://example.com/textbook",
        book_title="Example Textbook",
        output_dir=Path("output/step_by_step"),
    )

    # Initialize pipeline
    pipeline = TextbookPipeline(config)

    print("Running pipeline steps individually...\n")

    # Step 1: Retrieve images
    print("[1/6] Retrieving images...")
    image_paths = pipeline.run_step("retrieve", url=config.book_url)
    print(f"✓ Retrieved {len(image_paths)} images\n")

    # Step 2: Analyze layouts
    print("[2/6] Analyzing layouts...")
    layout_results = pipeline.run_step("analyze")
    print(f"✓ Analyzed {len(layout_results)} pages\n")

    # Step 3: Process images
    print("[3/6] Processing images...")
    processing_results = pipeline.run_step("process")
    print(f"✓ Processed {len(processing_results)} images\n")

    # Step 4: Extract text
    print("[4/6] Extracting text...")
    ocr_results = pipeline.run_step("ocr")
    total_words = sum(r.word_count for r in ocr_results.values())
    print(f"✓ Extracted {total_words} words\n")

    # Step 5: Interpret illustrations (optional - requires API key)
    if pipeline.illustration_interpreter:
        print("[5/6] Interpreting illustrations...")
        interpretation_results = pipeline.run_step("interpret")
        print(f"✓ Interpreted {len(interpretation_results)} illustrations\n")
    else:
        print("[5/6] Skipping illustration interpretation (no API key)\n")

    # Step 6: Export for NotebookLM
    print("[6/6] Exporting for NotebookLM...")
    exports = pipeline.run_step("export")
    print(f"✓ Exported {len(exports)} files\n")

    print("=" * 60)
    print("All steps completed successfully!")
    print(f"Output directory: {config.output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
