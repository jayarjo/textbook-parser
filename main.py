#!/usr/bin/env python3
"""
Textbook Parser - Main Entry Point

Command-line interface for the illustrated book text extraction pipeline.
"""

import argparse
import sys
from pathlib import Path
from loguru import logger

from src.config import PipelineConfig
from src.pipeline import TextbookPipeline


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    logger.remove()

    if verbose:
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
            level="DEBUG",
        )
    else:
        logger.add(
            sys.stderr,
            format="<level>{level: <8}</level> | <level>{message}</level>",
            level="INFO",
        )

    # Also log to file
    logger.add(
        "textbook_parser.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="DEBUG",
        rotation="10 MB",
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract text and illustrations from online textbooks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a book from URL
  python main.py --url "https://example.com/book" --title "My Textbook"

  # Use custom configuration
  python main.py --config config/my_config.yaml

  # Run specific steps only
  python main.py --config config.yaml --step ocr

  # Skip retrieval and use existing images
  python main.py --config config.yaml --skip-retrieval

  # Process with verbose logging
  python main.py --url "https://example.com/book" -v
        """,
    )

    # Input options
    parser.add_argument(
        "--url",
        type=str,
        help="URL of the book viewer",
    )

    parser.add_argument(
        "--title",
        type=str,
        default="untitled_book",
        help="Title of the book",
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration YAML file",
    )

    # Processing options
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Output directory for processed files",
    )

    parser.add_argument(
        "--skip-retrieval",
        action="store_true",
        help="Skip image retrieval (use existing images)",
    )

    parser.add_argument(
        "--skip-interpretation",
        action="store_true",
        help="Skip illustration interpretation",
    )

    parser.add_argument(
        "--step",
        type=str,
        choices=["retrieve", "analyze", "process", "ocr", "interpret", "export"],
        help="Run only a specific step",
    )

    # OCR options
    parser.add_argument(
        "--ocr-engine",
        type=str,
        choices=["tesseract", "paddleocr"],
        default="tesseract",
        help="OCR engine to use",
    )

    parser.add_argument(
        "--languages",
        type=str,
        nargs="+",
        default=["kat", "eng"],
        help="OCR languages (e.g., kat eng)",
    )

    # Illustration interpretation options
    parser.add_argument(
        "--vision-provider",
        type=str,
        choices=["openai", "anthropic", "google"],
        default="openai",
        help="Vision AI provider",
    )

    # Logging
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    try:
        # Load or create configuration
        if args.config:
            logger.info(f"Loading configuration from {args.config}")
            config = PipelineConfig.from_yaml(args.config)
        else:
            logger.info("Using default configuration")
            config = PipelineConfig()

        # Override config with command-line arguments
        if args.url:
            config.book_url = args.url

        if args.title:
            config.book_title = args.title

        if args.output_dir:
            config.output_dir = Path(args.output_dir)

        if args.ocr_engine:
            config.ocr.engine = args.ocr_engine

        if args.languages:
            config.ocr.languages = args.languages

        if args.vision_provider:
            config.illustration_interpreter.provider = args.vision_provider

        # Initialize pipeline
        logger.info("Initializing pipeline...")
        pipeline = TextbookPipeline(config)

        # Run pipeline or specific step
        if args.step:
            logger.info(f"Running step: {args.step}")
            pipeline.run_step(args.step, url=config.book_url)
        else:
            logger.info("Running full pipeline")
            summary = pipeline.run(
                skip_retrieval=args.skip_retrieval,
                skip_illustration_interpretation=args.skip_interpretation,
            )

            logger.info("\n✓ Pipeline completed successfully!")
            logger.info(f"Output directory: {config.output_dir}")

    except KeyboardInterrupt:
        logger.warning("\nPipeline interrupted by user")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        if args.verbose:
            logger.exception("Full traceback:")
        sys.exit(1)


if __name__ == "__main__":
    main()
