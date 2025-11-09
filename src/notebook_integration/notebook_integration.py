"""
Google Notebook Integration Module

Integrates with Google NotebookLM to generate:
- Audio/video summaries
- Quiz questions
- Analytical reports
- Study guides
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from loguru import logger

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    import pickle
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    logger.warning("Google API libraries not available.")


class NotebookIntegration:
    """
    Integrates extracted book content with Google NotebookLM.

    Note: As of 2025, Google NotebookLM does not have a public API.
    This module provides a framework for when the API becomes available,
    and currently exports data in formats compatible with manual upload.
    """

    def __init__(
        self,
        credentials_path: Optional[Path] = None,
        notebook_id: Optional[str] = None,
    ):
        """
        Initialize the notebook integration.

        Args:
            credentials_path: Path to Google API credentials
            notebook_id: Google Notebook ID (if API available)
        """
        self.credentials_path = credentials_path
        self.notebook_id = notebook_id
        self.service = None

        if GOOGLE_API_AVAILABLE and credentials_path:
            self._initialize_service()
        else:
            logger.info(
                "Google Notebook API not available. "
                "Will export data in compatible format."
            )

    def _initialize_service(self) -> None:
        """Initialize Google API service (placeholder for future API)."""
        logger.info("Initializing Google Notebook service...")

        # This is a placeholder - Google NotebookLM doesn't have a public API yet
        # When it becomes available, this would authenticate and create a service

        try:
            creds = None
            token_path = Path("token.pickle")

            if token_path.exists():
                with open(token_path, "rb") as token:
                    creds = pickle.load(token)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_path),
                        scopes=["https://www.googleapis.com/auth/documents"],
                    )
                    creds = flow.run_local_server(port=0)

                with open(token_path, "wb") as token:
                    pickle.dump(creds, token)

            # Would initialize service here when API is available
            logger.info("Google API credentials configured")

        except Exception as e:
            logger.warning(f"Could not initialize Google service: {e}")

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
