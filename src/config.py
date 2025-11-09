"""
Configuration management for the textbook parser pipeline.
"""

from typing import Optional, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field
import yaml
import os
from dotenv import load_dotenv

load_dotenv()


class RetrieverConfig(BaseModel):
    """Configuration for the image retriever module."""
    headless: bool = True
    timeout: int = 30000
    max_retries: int = 3
    wait_for_images: int = 2000
    user_agent: Optional[str] = None


class LayoutAnalyzerConfig(BaseModel):
    """Configuration for the layout analyzer module."""
    model_name: str = "lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config"
    confidence_threshold: float = 0.5
    device: str = "cpu"  # or "cuda"


class ImageProcessorConfig(BaseModel):
    """Configuration for the image processor module."""
    mask_color: tuple = (255, 255, 255)  # White
    padding: int = 5  # Padding around illustration bboxes


class OCRConfig(BaseModel):
    """Configuration for OCR engine."""
    engine: str = "tesseract"  # "tesseract" or "paddleocr"
    languages: list = ["kat", "eng"]  # Georgian and English
    tesseract_config: str = "--psm 6"  # Page segmentation mode
    confidence_threshold: float = 60.0


class IllustrationInterpreterConfig(BaseModel):
    """Configuration for illustration interpretation."""
    provider: str = "openai"  # "openai", "anthropic", or "google"
    model: str = "gpt-4-vision-preview"
    max_tokens: int = 500
    temperature: float = 0.7


class NotebookIntegrationConfig(BaseModel):
    """Configuration for Google Notebook integration."""
    enabled: bool = False
    credentials_path: Optional[str] = None
    notebook_id: Optional[str] = None


class PipelineConfig(BaseModel):
    """Main pipeline configuration."""
    output_dir: Path = Field(default_factory=lambda: Path("output"))
    book_url: Optional[str] = None
    book_title: Optional[str] = "untitled_book"

    # Module configurations
    retriever: RetrieverConfig = Field(default_factory=RetrieverConfig)
    layout_analyzer: LayoutAnalyzerConfig = Field(default_factory=LayoutAnalyzerConfig)
    image_processor: ImageProcessorConfig = Field(default_factory=ImageProcessorConfig)
    ocr: OCRConfig = Field(default_factory=OCRConfig)
    illustration_interpreter: IllustrationInterpreterConfig = Field(
        default_factory=IllustrationInterpreterConfig
    )
    notebook_integration: NotebookIntegrationConfig = Field(
        default_factory=NotebookIntegrationConfig
    )

    # API Keys (loaded from environment)
    openai_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    anthropic_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    google_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("GOOGLE_API_KEY"))

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "PipelineConfig":
        """Load configuration from YAML file."""
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, yaml_path: str) -> None:
        """Save configuration to YAML file."""
        with open(yaml_path, "w") as f:
            yaml.dump(self.dict(), f, default_flow_style=False)

    def setup_directories(self) -> None:
        """Create all necessary output directories."""
        directories = [
            self.output_dir / "images",
            self.output_dir / "cleaned",
            self.output_dir / "text",
            self.output_dir / "illustrations",
            self.output_dir / "metadata",
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
