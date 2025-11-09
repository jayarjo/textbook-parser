"""
Main Pipeline Orchestrator

Coordinates all modules to execute the complete extraction and processing workflow.
"""

from pathlib import Path
from typing import Optional, Dict, Any
import json
from loguru import logger

from .config import PipelineConfig
from .retriever import ImageRetriever
from .layout_analyzer import LayoutAnalyzer
from .image_processor import ImageProcessor
from .ocr_engine import OCREngine
from .illustration_interpreter import IllustrationInterpreter
from .notebook_integration import NotebookIntegration


class TextbookPipeline:
    """
    Main pipeline for processing illustrated textbooks.

    Workflow:
    1. Retrieve book page images
    2. Analyze page layouts
    3. Process images (mask illustrations)
    4. Extract text via OCR
    5. Interpret illustrations
    6. Generate Google Notebook content
    """

    def __init__(self, config: PipelineConfig):
        """
        Initialize the pipeline.

        Args:
            config: Pipeline configuration
        """
        self.config = config
        self.config.setup_directories()

        # Initialize all modules
        self._initialize_modules()

        # Track pipeline state
        self.state: Dict[str, Any] = {
            "images_retrieved": False,
            "layout_analyzed": False,
            "images_processed": False,
            "text_extracted": False,
            "illustrations_interpreted": False,
            "notebook_exported": False,
        }

    def _initialize_modules(self) -> None:
        """Initialize all pipeline modules."""
        logger.info("Initializing pipeline modules")

        # Image Retriever
        self.retriever = ImageRetriever(
            output_dir=self.config.output_dir / "images",
            headless=self.config.retriever.headless,
            timeout=self.config.retriever.timeout,
            max_retries=self.config.retriever.max_retries,
            wait_for_images=self.config.retriever.wait_for_images,
            user_agent=self.config.retriever.user_agent,
        )

        # Layout Analyzer
        self.layout_analyzer = LayoutAnalyzer(
            model_name=self.config.layout_analyzer.model_name,
            confidence_threshold=self.config.layout_analyzer.confidence_threshold,
            device=self.config.layout_analyzer.device,
        )

        # Image Processor
        self.image_processor = ImageProcessor(
            mask_color=self.config.image_processor.mask_color,
            padding=self.config.image_processor.padding,
        )

        # OCR Engine
        self.ocr_engine = OCREngine(
            engine=self.config.ocr.engine,
            languages=self.config.ocr.languages,
            tesseract_config=self.config.ocr.tesseract_config,
            confidence_threshold=self.config.ocr.confidence_threshold,
        )

        # Illustration Interpreter (if API key available)
        self.illustration_interpreter = None
        if self.config.openai_api_key:
            self.illustration_interpreter = IllustrationInterpreter(
                provider=self.config.illustration_interpreter.provider,
                model=self.config.illustration_interpreter.model,
                api_key=self.config.openai_api_key,
                max_tokens=self.config.illustration_interpreter.max_tokens,
                temperature=self.config.illustration_interpreter.temperature,
            )
        elif self.config.anthropic_api_key:
            self.illustration_interpreter = IllustrationInterpreter(
                provider="anthropic",
                model="claude-3-opus-20240229",
                api_key=self.config.anthropic_api_key,
            )
        elif self.config.google_api_key:
            self.illustration_interpreter = IllustrationInterpreter(
                provider="google",
                model="gemini-pro-vision",
                api_key=self.config.google_api_key,
            )
        else:
            logger.warning("No API key provided for illustration interpretation")

        # Notebook Integration
        self.notebook_integration = NotebookIntegration(
            credentials_path=Path(self.config.notebook_integration.credentials_path)
            if self.config.notebook_integration.credentials_path
            else None,
            notebook_id=self.config.notebook_integration.notebook_id,
        )

        logger.info("All modules initialized")

    def run(
        self,
        book_url: Optional[str] = None,
        skip_retrieval: bool = False,
        skip_illustration_interpretation: bool = False,
    ) -> Dict[str, Any]:
        """
        Run the complete pipeline.

        Args:
            book_url: URL of the book viewer (if not in config)
            skip_retrieval: Skip image retrieval (use existing images)
            skip_illustration_interpretation: Skip illustration interpretation

        Returns:
            Pipeline execution summary
        """
        logger.info("=" * 60)
        logger.info("Starting Textbook Processing Pipeline")
        logger.info("=" * 60)

        url = book_url or self.config.book_url
        if not url and not skip_retrieval:
            raise ValueError("book_url must be provided")

        summary = {}

        try:
            # Step 1: Retrieve Images
            if not skip_retrieval:
                logger.info("\n[Step 1/6] Retrieving book page images...")
                image_paths = self.retriever.retrieve_images_sync(url)
                self.state["images_retrieved"] = True
                summary["images_retrieved"] = len(image_paths)
                logger.info(f"✓ Retrieved {len(image_paths)} images")
            else:
                logger.info("\n[Step 1/6] Skipping image retrieval (using existing images)")
                image_paths = list((self.config.output_dir / "images").glob("*.png"))
                summary["images_retrieved"] = len(image_paths)

            # Step 2: Analyze Layouts
            logger.info("\n[Step 2/6] Analyzing page layouts...")
            layout_results = self.layout_analyzer.analyze_directory(
                image_dir=self.config.output_dir / "images",
                output_path=self.config.output_dir / "metadata" / "layout_analysis.json",
            )
            self.state["layout_analyzed"] = True
            summary["pages_analyzed"] = len(layout_results)
            logger.info(f"✓ Analyzed {len(layout_results)} page layouts")

            # Step 3: Process Images
            logger.info("\n[Step 3/6] Processing images (masking illustrations)...")
            processing_results = self.image_processor.process_batch(
                image_dir=self.config.output_dir / "images",
                layout_results={k: v.to_dict() for k, v in layout_results.items()},
                output_cleaned_dir=self.config.output_dir / "cleaned",
                output_illustrations_dir=self.config.output_dir / "illustrations",
            )
            self.state["images_processed"] = True
            summary["images_processed"] = len(processing_results)
            total_illustrations = sum(
                r["illustrations_count"] for r in processing_results.values()
            )
            summary["illustrations_extracted"] = total_illustrations
            logger.info(f"✓ Processed {len(processing_results)} images")
            logger.info(f"✓ Extracted {total_illustrations} illustrations")

            # Save processing metadata
            with open(
                self.config.output_dir / "metadata" / "processing_metadata.json",
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(processing_results, f, indent=2)

            # Step 4: Extract Text
            logger.info("\n[Step 4/6] Extracting text via OCR...")
            ocr_results = self.ocr_engine.extract_batch(
                image_dir=self.config.output_dir / "cleaned",
                output_dir=self.config.output_dir / "text",
                combine=True,
            )
            self.state["text_extracted"] = True
            summary["pages_ocr"] = len(ocr_results)
            total_words = sum(r.word_count for r in ocr_results.values())
            summary["total_words"] = total_words
            logger.info(f"✓ Extracted text from {len(ocr_results)} pages")
            logger.info(f"✓ Total words: {total_words}")

            # Step 5: Interpret Illustrations
            if self.illustration_interpreter and not skip_illustration_interpretation:
                logger.info("\n[Step 5/6] Interpreting illustrations...")
                illustration_dir = self.config.output_dir / "illustrations"

                if list(illustration_dir.glob("*.png")):
                    interpretation_results = self.illustration_interpreter.interpret_batch(
                        illustration_dir=illustration_dir,
                        output_path=self.config.output_dir
                        / "metadata"
                        / "illustration_descriptions.json",
                        context=f"Educational textbook: {self.config.book_title}",
                    )
                    self.state["illustrations_interpreted"] = True
                    summary["illustrations_interpreted"] = len(interpretation_results)
                    logger.info(f"✓ Interpreted {len(interpretation_results)} illustrations")
                else:
                    logger.info("No illustrations to interpret")
                    summary["illustrations_interpreted"] = 0
            else:
                logger.info("\n[Step 5/6] Skipping illustration interpretation")
                summary["illustrations_interpreted"] = 0

            # Step 6: Export for Google Notebook
            logger.info("\n[Step 6/6] Exporting for Google NotebookLM...")
            exports = self.notebook_integration.export_for_notebooklm(
                text_path=self.config.output_dir / "text" / "book_full.txt",
                illustrations_data_path=self.config.output_dir
                / "metadata"
                / "illustration_descriptions.json",
                output_dir=self.config.output_dir / "notebook_export",
                book_title=self.config.book_title or "Textbook",
            )
            self.state["notebook_exported"] = True
            summary["notebook_files_exported"] = len(exports)
            logger.info(f"✓ Exported {len(exports)} files for NotebookLM")

            # Final summary
            logger.info("\n" + "=" * 60)
            logger.info("Pipeline Execution Complete!")
            logger.info("=" * 60)
            logger.info(f"Images retrieved: {summary.get('images_retrieved', 0)}")
            logger.info(f"Pages analyzed: {summary.get('pages_analyzed', 0)}")
            logger.info(f"Illustrations extracted: {summary.get('illustrations_extracted', 0)}")
            logger.info(f"Text extracted: {summary.get('total_words', 0)} words")
            logger.info(
                f"Illustrations interpreted: {summary.get('illustrations_interpreted', 0)}"
            )
            logger.info(
                f"NotebookLM files: {summary.get('notebook_files_exported', 0)}"
            )

            # Save summary
            summary_path = self.config.output_dir / "pipeline_summary.json"
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
            logger.info(f"\nSummary saved to: {summary_path}")

            logger.info(f"\nOutput directory: {self.config.output_dir}")
            logger.info("=" * 60)

            return summary

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise

    def run_step(self, step_name: str, **kwargs) -> Any:
        """
        Run a single pipeline step.

        Args:
            step_name: Name of the step to run
            **kwargs: Step-specific arguments

        Returns:
            Step result
        """
        logger.info(f"Running step: {step_name}")

        if step_name == "retrieve":
            url = kwargs.get("url") or self.config.book_url
            return self.retriever.retrieve_images_sync(url)

        elif step_name == "analyze":
            return self.layout_analyzer.analyze_directory(
                image_dir=self.config.output_dir / "images",
                output_path=self.config.output_dir / "metadata" / "layout_analysis.json",
            )

        elif step_name == "process":
            layout_path = self.config.output_dir / "metadata" / "layout_analysis.json"
            layout_results = self.layout_analyzer.load_results(layout_path)
            return self.image_processor.process_batch(
                image_dir=self.config.output_dir / "images",
                layout_results=layout_results,
                output_cleaned_dir=self.config.output_dir / "cleaned",
                output_illustrations_dir=self.config.output_dir / "illustrations",
            )

        elif step_name == "ocr":
            return self.ocr_engine.extract_batch(
                image_dir=self.config.output_dir / "cleaned",
                output_dir=self.config.output_dir / "text",
                combine=True,
            )

        elif step_name == "interpret":
            if not self.illustration_interpreter:
                raise RuntimeError("Illustration interpreter not available")
            return self.illustration_interpreter.interpret_batch(
                illustration_dir=self.config.output_dir / "illustrations",
                output_path=self.config.output_dir
                / "metadata"
                / "illustration_descriptions.json",
            )

        elif step_name == "export":
            return self.notebook_integration.export_for_notebooklm(
                text_path=self.config.output_dir / "text" / "book_full.txt",
                illustrations_data_path=self.config.output_dir
                / "metadata"
                / "illustration_descriptions.json",
                output_dir=self.config.output_dir / "notebook_export",
                book_title=self.config.book_title or "Textbook",
            )

        else:
            raise ValueError(f"Unknown step: {step_name}")
