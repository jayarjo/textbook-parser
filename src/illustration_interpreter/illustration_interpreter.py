"""
Illustration Interpreter Module

Uses vision-language models to analyze and describe illustrations:
- Generate captions
- Provide detailed descriptions
- Extract semantic tags
- Identify educational content
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import base64
from loguru import logger

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available. Install with: pip install openai")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic not available. Install with: pip install anthropic")

try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    logger.warning("Google AI not available. Install with: pip install google-generativeai")


class IllustrationDescription:
    """Represents the interpretation of a single illustration."""

    def __init__(self, image_path: Path):
        self.image_path = image_path
        self.caption: str = ""
        self.description: str = ""
        self.tags: List[str] = []
        self.educational_value: str = ""
        self.related_concepts: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "image_path": str(self.image_path),
            "caption": self.caption,
            "description": self.description,
            "tags": self.tags,
            "educational_value": self.educational_value,
            "related_concepts": self.related_concepts,
        }


class IllustrationInterpreter:
    """
    Interprets illustrations using vision-language models.

    Supports multiple providers:
    - OpenAI (GPT-4 Vision)
    - Anthropic (Claude 3 with vision)
    - Google (Gemini Pro Vision)
    """

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4-vision-preview",
        api_key: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
    ):
        """
        Initialize the illustration interpreter.

        Args:
            provider: AI provider ("openai", "anthropic", or "google")
            model: Model name
            api_key: API key for the provider
            max_tokens: Maximum tokens for generation
            temperature: Sampling temperature
        """
        self.provider = provider.lower()
        self.model = model
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.client = None

        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the AI client."""
        if self.provider == "openai":
            if not OPENAI_AVAILABLE:
                raise RuntimeError("OpenAI is not available.")
            if not self.api_key:
                raise ValueError("OpenAI API key is required.")
            self.client = openai.OpenAI(api_key=self.api_key)
            logger.info("Using OpenAI for illustration interpretation")

        elif self.provider == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                raise RuntimeError("Anthropic is not available.")
            if not self.api_key:
                raise ValueError("Anthropic API key is required.")
            self.client = anthropic.Anthropic(api_key=self.api_key)
            logger.info("Using Anthropic for illustration interpretation")

        elif self.provider == "google":
            if not GOOGLE_AVAILABLE:
                raise RuntimeError("Google AI is not available.")
            if not self.api_key:
                raise ValueError("Google API key is required.")
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model)
            logger.info("Using Google AI for illustration interpretation")

        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def interpret_illustration(
        self, image_path: Path, context: Optional[str] = None
    ) -> IllustrationDescription:
        """
        Interpret a single illustration.

        Args:
            image_path: Path to the illustration image
            context: Optional context about the book/chapter

        Returns:
            IllustrationDescription object
        """
        logger.debug(f"Interpreting illustration: {image_path}")

        result = IllustrationDescription(image_path)

        try:
            if self.provider == "openai":
                result = self._interpret_with_openai(image_path, context)
            elif self.provider == "anthropic":
                result = self._interpret_with_anthropic(image_path, context)
            elif self.provider == "google":
                result = self._interpret_with_google(image_path, context)

            logger.debug(f"Generated caption: {result.caption[:50]}...")

        except Exception as e:
            logger.error(f"Interpretation failed for {image_path}: {e}")

        return result

    def _interpret_with_openai(
        self, image_path: Path, context: Optional[str] = None
    ) -> IllustrationDescription:
        """Interpret using OpenAI GPT-4 Vision."""
        result = IllustrationDescription(image_path)

        # Encode image to base64
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        # Build prompt
        prompt = self._build_prompt(context)

        # Call API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_data}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        # Parse response
        content = response.choices[0].message.content
        self._parse_response(content, result)

        return result

    def _interpret_with_anthropic(
        self, image_path: Path, context: Optional[str] = None
    ) -> IllustrationDescription:
        """Interpret using Anthropic Claude with vision."""
        result = IllustrationDescription(image_path)

        # Encode image to base64
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        # Detect image type
        image_type = "image/png"
        if image_path.suffix.lower() in [".jpg", ".jpeg"]:
            image_type = "image/jpeg"

        # Build prompt
        prompt = self._build_prompt(context)

        # Call API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": image_type,
                                "data": image_data,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )

        # Parse response
        content = response.content[0].text
        self._parse_response(content, result)

        return result

    def _interpret_with_google(
        self, image_path: Path, context: Optional[str] = None
    ) -> IllustrationDescription:
        """Interpret using Google Gemini Vision."""
        result = IllustrationDescription(image_path)

        # Load image
        from PIL import Image
        image = Image.open(image_path)

        # Build prompt
        prompt = self._build_prompt(context)

        # Call API
        response = self.client.generate_content([prompt, image])

        # Parse response
        self._parse_response(response.text, result)

        return result

    def _build_prompt(self, context: Optional[str] = None) -> str:
        """Build the prompt for the vision model."""
        base_prompt = """Analyze this illustration from an educational textbook.

Please provide:
1. **Caption**: A concise 1-2 sentence description
2. **Description**: A detailed paragraph explaining what the illustration shows
3. **Tags**: 5-10 relevant keywords (comma-separated)
4. **Educational Value**: How this illustration supports learning
5. **Related Concepts**: Key concepts or topics this illustration relates to (comma-separated)

Format your response as follows:
CAPTION: [your caption]
DESCRIPTION: [your description]
TAGS: [tag1, tag2, tag3, ...]
EDUCATIONAL_VALUE: [explanation]
RELATED_CONCEPTS: [concept1, concept2, ...]
"""

        if context:
            base_prompt += f"\n\nContext: {context}"

        return base_prompt

    def _parse_response(self, content: str, result: IllustrationDescription) -> None:
        """Parse the AI response into structured data."""
        lines = content.split("\n")

        for line in lines:
            line = line.strip()

            if line.startswith("CAPTION:"):
                result.caption = line.replace("CAPTION:", "").strip()

            elif line.startswith("DESCRIPTION:"):
                result.description = line.replace("DESCRIPTION:", "").strip()

            elif line.startswith("TAGS:"):
                tags_str = line.replace("TAGS:", "").strip()
                result.tags = [tag.strip() for tag in tags_str.split(",")]

            elif line.startswith("EDUCATIONAL_VALUE:"):
                result.educational_value = line.replace("EDUCATIONAL_VALUE:", "").strip()

            elif line.startswith("RELATED_CONCEPTS:"):
                concepts_str = line.replace("RELATED_CONCEPTS:", "").strip()
                result.related_concepts = [c.strip() for c in concepts_str.split(",")]

        # If parsing failed, use the entire content as description
        if not result.caption and not result.description:
            result.description = content

    def interpret_batch(
        self,
        illustration_dir: Path,
        output_path: Path,
        context: Optional[str] = None,
    ) -> Dict[str, IllustrationDescription]:
        """
        Interpret multiple illustrations.

        Args:
            illustration_dir: Directory containing illustration images
            output_path: Path to save results JSON
            context: Optional context about the book

        Returns:
            Dictionary mapping illustration names to descriptions
        """
        logger.info(f"Interpreting illustrations from {illustration_dir}")

        results = {}
        image_files = sorted(illustration_dir.glob("*.png")) + sorted(
            illustration_dir.glob("*.jpg")
        )

        for image_path in image_files:
            try:
                description = self.interpret_illustration(image_path, context)
                results[image_path.stem] = description
            except Exception as e:
                logger.error(f"Failed to interpret {image_path}: {e}")

        logger.info(f"Interpreted {len(results)} illustrations")

        # Save results
        self.save_results(results, output_path)

        return results

    def save_results(
        self, results: Dict[str, IllustrationDescription], output_path: Path
    ) -> None:
        """Save interpretation results to JSON file."""
        output_data = {
            name: description.to_dict() for name, description in results.items()
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved illustration interpretations to {output_path}")

    @staticmethod
    def load_results(input_path: Path) -> Dict[str, Dict[str, Any]]:
        """Load interpretation results from JSON file."""
        with open(input_path, "r", encoding="utf-8") as f:
            return json.load(f)
