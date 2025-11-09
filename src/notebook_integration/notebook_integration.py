"""
Google Notebook Integration Module

Integrates with Google NotebookLM using Playwright automation to:
- Create new notebooks
- Upload source documents
- Generate audio overviews
- Generate quizzes and flashcards
- Generate study guides
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import time
from loguru import logger

try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available. Install with: pip install playwright && playwright install")


class NotebookIntegration:
    """
    Integrates extracted book content with Google NotebookLM using browser automation.

    Since NotebookLM doesn't have a public API, this module uses Playwright to:
    - Navigate to notebooklm.google.com
    - Create new notebooks
    - Upload source documents
    - Request generation of audio, quizzes, flashcards, etc.
    """

    def __init__(
        self,
        headless: bool = True,
        slow_mo: int = 500,
        timeout: int = 60000,
        user_data_dir: Optional[Path] = None,
    ):
        """
        Initialize the notebook integration.

        Args:
            headless: Run browser in headless mode
            slow_mo: Slow down operations by N milliseconds (useful for debugging)
            timeout: Default timeout for operations in milliseconds
            user_data_dir: Path to Chrome user data dir (for persistent login)
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is required for NotebookLM integration. "
                "Install with: pip install playwright && playwright install chromium"
            )

        self.headless = headless
        self.slow_mo = slow_mo
        self.timeout = timeout
        self.user_data_dir = user_data_dir
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def __enter__(self):
        """Context manager entry."""
        self.start_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def start_browser(self) -> None:
        """Start the Playwright browser."""
        logger.info("Starting browser for NotebookLM automation...")

        self.playwright = sync_playwright().start()

        # Launch browser with options
        launch_options = {
            "headless": self.headless,
            "slow_mo": self.slow_mo,
        }

        self.browser = self.playwright.chromium.launch(**launch_options)

        # Create context with user data dir if provided (for persistent login)
        context_options = {
            "viewport": {"width": 1920, "height": 1080},
        }

        if self.user_data_dir:
            # Use persistent context to maintain login
            self.context = self.browser.new_context(
                storage_state=str(self.user_data_dir / "storage.json")
                if (self.user_data_dir / "storage.json").exists()
                else None,
                **context_options
            )
        else:
            self.context = self.browser.new_context(**context_options)

        self.page = self.context.new_page()
        self.page.set_default_timeout(self.timeout)

        logger.info("Browser started successfully")

    def close(self) -> None:
        """Close the browser and cleanup."""
        logger.info("Closing browser...")

        # Save storage state if using persistent context
        if self.user_data_dir and self.context:
            storage_path = self.user_data_dir / "storage.json"
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.context.storage_state(path=str(storage_path))
            logger.info(f"Saved browser state to {storage_path}")

        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

        logger.info("Browser closed")

    def navigate_to_notebooklm(self) -> None:
        """Navigate to Google NotebookLM."""
        logger.info("Navigating to NotebookLM...")

        if not self.page:
            raise RuntimeError("Browser not started. Call start_browser() first.")

        self.page.goto("https://notebooklm.google.com", wait_until="networkidle")
        logger.info("Loaded NotebookLM")

    def create_new_notebook(self, notebook_name: Optional[str] = None) -> str:
        """
        Create a new notebook in NotebookLM.

        Args:
            notebook_name: Name for the notebook (optional)

        Returns:
            Notebook URL
        """
        logger.info(f"Creating new notebook: {notebook_name or 'Untitled'}")

        if not self.page:
            raise RuntimeError("Browser not started")

        try:
            # Look for "New notebook" or "Create" button
            # Note: Selectors may need adjustment based on NotebookLM UI updates
            create_button_selectors = [
                'button:has-text("New notebook")',
                'button:has-text("Create")',
                'button:has-text("+")',
                '[aria-label*="New notebook"]',
                '[aria-label*="Create notebook"]',
            ]

            button_found = False
            for selector in create_button_selectors:
                try:
                    self.page.click(selector, timeout=5000)
                    button_found = True
                    logger.info(f"Clicked create button: {selector}")
                    break
                except PlaywrightTimeout:
                    continue

            if not button_found:
                logger.warning("Could not find create notebook button, may already be on new notebook page")

            # Wait for the notebook to be created
            self.page.wait_for_load_state("networkidle")
            time.sleep(2)  # Additional wait for UI to settle

            # Get the notebook URL
            notebook_url = self.page.url
            logger.info(f"Created notebook: {notebook_url}")

            # Set notebook name if provided
            if notebook_name:
                try:
                    # Look for title input/editable element
                    title_selectors = [
                        'input[placeholder*="Untitled"]',
                        '[contenteditable="true"]:has-text("Untitled")',
                        'h1[contenteditable="true"]',
                    ]

                    for selector in title_selectors:
                        try:
                            self.page.click(selector, timeout=3000)
                            self.page.fill(selector, notebook_name)
                            logger.info(f"Set notebook name: {notebook_name}")
                            break
                        except PlaywrightTimeout:
                            continue
                except Exception as e:
                    logger.warning(f"Could not set notebook name: {e}")

            return notebook_url

        except Exception as e:
            logger.error(f"Error creating notebook: {e}")
            raise

    def upload_source_file(self, file_path: Path) -> bool:
        """
        Upload a source file to the current notebook.

        Args:
            file_path: Path to the file to upload (supports .md, .txt, .pdf, .docx)

        Returns:
            True if upload successful
        """
        logger.info(f"Uploading source file: {file_path}")

        if not self.page:
            raise RuntimeError("Browser not started")

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            # Look for upload button/area
            upload_selectors = [
                'button:has-text("Add source")',
                'button:has-text("Upload")',
                'input[type="file"]',
                '[aria-label*="Add source"]',
                '[aria-label*="Upload"]',
            ]

            # Try to find and click upload button
            for selector in upload_selectors:
                try:
                    if 'input[type="file"]' in selector:
                        # Direct file input
                        file_input = self.page.locator(selector)
                        file_input.set_input_files(str(file_path))
                        logger.info("File uploaded via file input")
                        break
                    else:
                        # Button that reveals file input
                        self.page.click(selector, timeout=5000)
                        time.sleep(1)

                        # Now look for the file input
                        file_input = self.page.locator('input[type="file"]')
                        if file_input.count() > 0:
                            file_input.first.set_input_files(str(file_path))
                            logger.info("File uploaded via button -> file input")
                            break
                except PlaywrightTimeout:
                    continue

            # Wait for upload to complete
            logger.info("Waiting for upload to process...")
            time.sleep(5)  # Give it time to process the file

            # Look for success indicators
            try:
                # Wait for the source to appear in the sources list
                self.page.wait_for_selector(
                    f'text="{file_path.name}"',
                    timeout=30000
                )
                logger.info("Source file uploaded successfully")
                return True
            except PlaywrightTimeout:
                logger.warning("Upload may have succeeded but couldn't confirm")
                return True

        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            raise

    def generate_audio_overview(self) -> bool:
        """
        Request generation of audio overview.

        Returns:
            True if request successful
        """
        logger.info("Requesting audio overview generation...")

        if not self.page:
            raise RuntimeError("Browser not started")

        try:
            # Look for audio overview button
            audio_selectors = [
                'button:has-text("Audio overview")',
                'button:has-text("Generate audio")',
                '[aria-label*="Audio overview"]',
                '[aria-label*="Generate audio"]',
            ]

            for selector in audio_selectors:
                try:
                    self.page.click(selector, timeout=5000)
                    logger.info("Clicked audio overview button")

                    # Wait for generation to start
                    time.sleep(2)

                    # Look for generation started indicator
                    try:
                        self.page.wait_for_selector(
                            'text=/Generating|Creating|Processing/',
                            timeout=5000
                        )
                        logger.info("Audio overview generation started")
                    except PlaywrightTimeout:
                        logger.info("Audio overview generation may have started")

                    return True
                except PlaywrightTimeout:
                    continue

            logger.warning("Could not find audio overview button")
            return False

        except Exception as e:
            logger.error(f"Error generating audio overview: {e}")
            return False

    def generate_study_guide(self) -> bool:
        """
        Request generation of study guide.

        Returns:
            True if request successful
        """
        logger.info("Requesting study guide generation...")

        if not self.page:
            raise RuntimeError("Browser not started")

        try:
            # Type in the chat/prompt area to request study guide
            prompt_selectors = [
                'textarea[placeholder*="Ask"]',
                'textarea[placeholder*="question"]',
                'input[type="text"]',
                '[contenteditable="true"]',
            ]

            for selector in prompt_selectors:
                try:
                    self.page.click(selector, timeout=5000)
                    self.page.fill(
                        selector,
                        "Create a comprehensive study guide with key concepts, important terms, and practice questions."
                    )

                    # Press Enter or click send
                    self.page.keyboard.press("Enter")
                    logger.info("Requested study guide generation")
                    time.sleep(2)
                    return True
                except PlaywrightTimeout:
                    continue

            logger.warning("Could not find prompt input")
            return False

        except Exception as e:
            logger.error(f"Error generating study guide: {e}")
            return False

    def generate_quiz(self, num_questions: int = 10) -> bool:
        """
        Request generation of quiz questions.

        Args:
            num_questions: Number of quiz questions to generate

        Returns:
            True if request successful
        """
        logger.info(f"Requesting quiz with {num_questions} questions...")

        if not self.page:
            raise RuntimeError("Browser not started")

        try:
            # Look for quiz/flashcards button or use chat
            quiz_selectors = [
                'button:has-text("Quiz")',
                'button:has-text("Practice")',
                'button:has-text("Flashcard")',
                '[aria-label*="Quiz"]',
                '[aria-label*="Practice"]',
            ]

            # Try clicking quiz button first
            for selector in quiz_selectors:
                try:
                    self.page.click(selector, timeout=5000)
                    logger.info("Clicked quiz button")
                    time.sleep(2)
                    return True
                except PlaywrightTimeout:
                    continue

            # If no button found, use chat prompt
            prompt_selectors = [
                'textarea[placeholder*="Ask"]',
                'textarea[placeholder*="question"]',
                'input[type="text"]',
                '[contenteditable="true"]',
            ]

            for selector in prompt_selectors:
                try:
                    self.page.click(selector, timeout=5000)
                    self.page.fill(
                        selector,
                        f"Generate {num_questions} multiple-choice quiz questions covering the main concepts from this content."
                    )

                    # Press Enter or click send
                    self.page.keyboard.press("Enter")
                    logger.info("Requested quiz generation via chat")
                    time.sleep(2)
                    return True
                except PlaywrightTimeout:
                    continue

            logger.warning("Could not find quiz button or prompt input")
            return False

        except Exception as e:
            logger.error(f"Error generating quiz: {e}")
            return False

    def generate_flashcards(self) -> bool:
        """
        Request generation of flashcards.

        Returns:
            True if request successful
        """
        logger.info("Requesting flashcard generation...")

        if not self.page:
            raise RuntimeError("Browser not started")

        try:
            # Use chat prompt to request flashcards
            prompt_selectors = [
                'textarea[placeholder*="Ask"]',
                'textarea[placeholder*="question"]',
                'input[type="text"]',
                '[contenteditable="true"]',
            ]

            for selector in prompt_selectors:
                try:
                    self.page.click(selector, timeout=5000)
                    self.page.fill(
                        selector,
                        "Create flashcards for all important terms and concepts in this content."
                    )

                    # Press Enter or click send
                    self.page.keyboard.press("Enter")
                    logger.info("Requested flashcard generation")
                    time.sleep(2)
                    return True
                except PlaywrightTimeout:
                    continue

            logger.warning("Could not find prompt input for flashcards")
            return False

        except Exception as e:
            logger.error(f"Error generating flashcards: {e}")
            return False

    def automate_full_workflow(
        self,
        source_file: Path,
        notebook_name: Optional[str] = None,
        generate_audio: bool = True,
        generate_quiz_count: Optional[int] = 10,
        generate_flashcards_flag: bool = True,
        generate_study_guide_flag: bool = True,
    ) -> Dict[str, Any]:
        """
        Run the complete NotebookLM automation workflow.

        Args:
            source_file: Path to source file to upload
            notebook_name: Name for the notebook
            generate_audio: Whether to generate audio overview
            generate_quiz_count: Number of quiz questions (None to skip)
            generate_flashcards_flag: Whether to generate flashcards
            generate_study_guide_flag: Whether to generate study guide

        Returns:
            Dictionary with workflow results
        """
        logger.info("Starting full NotebookLM automation workflow...")

        results = {
            "success": False,
            "notebook_url": None,
            "uploaded": False,
            "audio_generated": False,
            "quiz_generated": False,
            "flashcards_generated": False,
            "study_guide_generated": False,
            "errors": [],
        }

        try:
            # Step 1: Navigate to NotebookLM
            self.navigate_to_notebooklm()
            time.sleep(2)

            # Step 2: Create new notebook
            try:
                notebook_url = self.create_new_notebook(notebook_name)
                results["notebook_url"] = notebook_url
            except Exception as e:
                error_msg = f"Failed to create notebook: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                return results

            # Step 3: Upload source file
            try:
                uploaded = self.upload_source_file(source_file)
                results["uploaded"] = uploaded

                if not uploaded:
                    raise RuntimeError("Upload failed")

                # Wait for processing
                time.sleep(5)
            except Exception as e:
                error_msg = f"Failed to upload file: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                return results

            # Step 4: Generate audio overview
            if generate_audio:
                try:
                    results["audio_generated"] = self.generate_audio_overview()
                    time.sleep(3)
                except Exception as e:
                    error_msg = f"Failed to generate audio: {e}"
                    logger.warning(error_msg)
                    results["errors"].append(error_msg)

            # Step 5: Generate quiz
            if generate_quiz_count:
                try:
                    results["quiz_generated"] = self.generate_quiz(generate_quiz_count)
                    time.sleep(3)
                except Exception as e:
                    error_msg = f"Failed to generate quiz: {e}"
                    logger.warning(error_msg)
                    results["errors"].append(error_msg)

            # Step 6: Generate flashcards
            if generate_flashcards_flag:
                try:
                    results["flashcards_generated"] = self.generate_flashcards()
                    time.sleep(3)
                except Exception as e:
                    error_msg = f"Failed to generate flashcards: {e}"
                    logger.warning(error_msg)
                    results["errors"].append(error_msg)

            # Step 7: Generate study guide
            if generate_study_guide_flag:
                try:
                    results["study_guide_generated"] = self.generate_study_guide()
                    time.sleep(3)
                except Exception as e:
                    error_msg = f"Failed to generate study guide: {e}"
                    logger.warning(error_msg)
                    results["errors"].append(error_msg)

            results["success"] = results["uploaded"]
            logger.info("Workflow completed successfully")

            return results

        except Exception as e:
            error_msg = f"Workflow error: {e}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            return results

    def create_notebook_source(
        self,
        text_content: str,
        illustration_descriptions: List[Dict[str, Any]],
        metadata: Dict[str, Any],
        output_path: Path,
    ) -> Path:
        """
        Create a source document for Google NotebookLM.

        Args:
            text_content: Full extracted text
            illustration_descriptions: List of illustration interpretations
            metadata: Book metadata
            output_path: Path to save the source document

        Returns:
            Path to created document
        """
        logger.info("Creating Google Notebook source document")

        # Format content for NotebookLM
        formatted_content = self._format_for_notebook(
            text_content, illustration_descriptions, metadata
        )

        # Save as Markdown (NotebookLM accepts MD, TXT, PDF, etc.)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(formatted_content)

        logger.info(f"Created source document: {output_path}")

        # Also create a structured JSON version
        json_path = output_path.with_suffix(".json")
        self._create_structured_json(
            text_content, illustration_descriptions, metadata, json_path
        )

        return output_path

    def _format_for_notebook(
        self,
        text_content: str,
        illustration_descriptions: List[Dict[str, Any]],
        metadata: Dict[str, Any],
    ) -> str:
        """Format content as Markdown for NotebookLM."""
        lines = []

        # Title and metadata
        lines.append(f"# {metadata.get('title', 'Book Content')}\n")

        if metadata.get("author"):
            lines.append(f"**Author:** {metadata['author']}\n")

        if metadata.get("date"):
            lines.append(f"**Date:** {metadata['date']}\n")

        lines.append("\n---\n\n")

        # Main text content
        lines.append("## Text Content\n\n")
        lines.append(text_content)
        lines.append("\n\n---\n\n")

        # Illustrations section
        if illustration_descriptions:
            lines.append("## Illustrations and Figures\n\n")

            for idx, illus in enumerate(illustration_descriptions, 1):
                lines.append(f"### Figure {idx}\n\n")

                if illus.get("caption"):
                    lines.append(f"**Caption:** {illus['caption']}\n\n")

                if illus.get("description"):
                    lines.append(f"{illus['description']}\n\n")

                if illus.get("tags"):
                    tags = ", ".join(illus["tags"])
                    lines.append(f"**Tags:** {tags}\n\n")

                if illus.get("educational_value"):
                    lines.append(f"**Educational Value:** {illus['educational_value']}\n\n")

                if illus.get("related_concepts"):
                    concepts = ", ".join(illus["related_concepts"])
                    lines.append(f"**Related Concepts:** {concepts}\n\n")

                lines.append("---\n\n")

        return "".join(lines)

    def _create_structured_json(
        self,
        text_content: str,
        illustration_descriptions: List[Dict[str, Any]],
        metadata: Dict[str, Any],
        output_path: Path,
    ) -> None:
        """Create a structured JSON version of the content."""
        structured_data = {
            "metadata": metadata,
            "text_content": text_content,
            "illustrations": illustration_descriptions,
            "statistics": {
                "total_characters": len(text_content),
                "total_words": len(text_content.split()),
                "total_illustrations": len(illustration_descriptions),
            },
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(structured_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Created structured JSON: {output_path}")

    def generate_quiz_prompts(
        self, text_content: str, num_questions: int = 10
    ) -> List[str]:
        """
        Generate quiz question prompts based on the content.

        Args:
            text_content: Extracted text
            num_questions: Number of quiz questions to generate

        Returns:
            List of quiz prompts
        """
        logger.info(f"Generating {num_questions} quiz prompts")

        # These are prompts that can be used with NotebookLM or other AI tools
        prompts = [
            f"Based on the following text, create {num_questions} multiple-choice questions "
            f"to test comprehension:\n\n{text_content[:2000]}...",
            "Generate short-answer questions that focus on key concepts and facts.",
            "Create discussion questions that encourage critical thinking about the material.",
            "Design true/false questions about the main ideas presented in the text.",
        ]

        return prompts

    def generate_summary_prompts(self, text_content: str) -> List[str]:
        """
        Generate summary prompts for the content.

        Args:
            text_content: Extracted text

        Returns:
            List of summary prompts
        """
        logger.info("Generating summary prompts")

        prompts = [
            f"Summarize the following text in 3-5 key points:\n\n{text_content[:2000]}...",
            "Create a detailed chapter-by-chapter summary.",
            "Identify and explain the main themes and concepts.",
            "Generate a brief executive summary (200 words).",
        ]

        return prompts

    def create_study_guide(
        self,
        text_content: str,
        illustration_descriptions: List[Dict[str, Any]],
        output_path: Path,
    ) -> Path:
        """
        Create a comprehensive study guide.

        Args:
            text_content: Extracted text
            illustration_descriptions: Illustration interpretations
            output_path: Path to save study guide

        Returns:
            Path to study guide
        """
        logger.info("Creating study guide")

        lines = []

        lines.append("# Study Guide\n\n")

        # Key Concepts
        lines.append("## Key Concepts\n\n")
        lines.append("- [To be extracted from text analysis]\n\n")

        # Important Terms
        lines.append("## Important Terms and Definitions\n\n")
        lines.append("- [To be extracted from text analysis]\n\n")

        # Visual Learning Aids
        if illustration_descriptions:
            lines.append("## Visual Learning Aids\n\n")

            for illus in illustration_descriptions:
                if illus.get("caption"):
                    lines.append(f"- **{illus['caption']}**")

                if illus.get("educational_value"):
                    lines.append(f": {illus['educational_value']}")

                lines.append("\n")

            lines.append("\n")

        # Quiz Prompts
        lines.append("## Practice Questions\n\n")
        quiz_prompts = self.generate_quiz_prompts(text_content)
        for idx, prompt in enumerate(quiz_prompts, 1):
            lines.append(f"{idx}. {prompt}\n\n")

        # Summary Prompts
        lines.append("## Summary Exercises\n\n")
        summary_prompts = self.generate_summary_prompts(text_content)
        for idx, prompt in enumerate(summary_prompts, 1):
            lines.append(f"{idx}. {prompt}\n\n")

        # Save study guide
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("".join(lines))

        logger.info(f"Created study guide: {output_path}")

        return output_path

    def export_for_notebooklm(
        self,
        text_path: Path,
        illustrations_data_path: Path,
        output_dir: Path,
        book_title: str = "Textbook",
    ) -> Dict[str, Path]:
        """
        Export all content in NotebookLM-compatible format.

        Args:
            text_path: Path to extracted text file
            illustrations_data_path: Path to illustration descriptions JSON
            output_dir: Directory to save exports
            book_title: Title of the book

        Returns:
            Dictionary of exported file paths
        """
        logger.info("Exporting content for Google NotebookLM")

        output_dir.mkdir(parents=True, exist_ok=True)

        # Load content
        with open(text_path, "r", encoding="utf-8") as f:
            text_content = f.read()

        illustration_descriptions = []
        if illustrations_data_path.exists():
            with open(illustrations_data_path, "r", encoding="utf-8") as f:
                illus_data = json.load(f)
                illustration_descriptions = list(illus_data.values())

        metadata = {
            "title": book_title,
            "source": "Automated extraction pipeline",
            "date": "2025",
        }

        # Create exports
        exports = {}

        # Markdown source document
        exports["source_md"] = self.create_notebook_source(
            text_content,
            illustration_descriptions,
            metadata,
            output_dir / "notebook_source.md",
        )

        # Study guide
        exports["study_guide"] = self.create_study_guide(
            text_content,
            illustration_descriptions,
            output_dir / "study_guide.md",
        )

        # Instructions file
        instructions_path = output_dir / "notebooklm_instructions.md"
        with open(instructions_path, "w", encoding="utf-8") as f:
            f.write(self._create_instructions())
        exports["instructions"] = instructions_path

        logger.info(f"Exported {len(exports)} files for NotebookLM")

        return exports

    def _create_instructions(self) -> str:
        """Create instructions for using the exported content with NotebookLM."""
        return """# How to Use with Google NotebookLM

## Step 1: Upload Source Document

1. Go to https://notebooklm.google.com
2. Create a new notebook
3. Upload the `notebook_source.md` file as a source

## Step 2: Generate Content

Once the source is uploaded, you can ask NotebookLM to:

- **Generate Audio Overview**: NotebookLM can create an audio summary of the content
- **Create Study Guides**: Ask for summaries, key points, or study notes
- **Generate Quizzes**: Request practice questions based on the material
- **Answer Questions**: Ask specific questions about the content

## Example Prompts:

1. "Create a comprehensive summary of this textbook"
2. "Generate 20 multiple-choice questions covering the main concepts"
3. "What are the key themes in this material?"
4. "Create a study guide with important terms and concepts"
5. "Generate an audio briefing document about this content"

## Step 3: Review and Refine

- Review the generated content
- Ask follow-up questions for clarification
- Request regeneration if needed

## Additional Files:

- `study_guide.md`: Pre-formatted study guide template
- `notebook_source.json`: Structured data version of the content

---

Note: Google NotebookLM features may vary based on availability and updates.
"""
