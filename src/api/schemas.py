"""
Common API schemas and models for all services.

These define the standard interface that all pipeline services must implement.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ServiceStatus(str, Enum):
    """Service health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthResponse(BaseModel):
    """Standard health check response for all services."""
    service_name: str
    version: str = "0.1.0"
    status: ServiceStatus
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    details: Optional[str] = None
    service: str


class BoundingBox(BaseModel):
    """Standard bounding box representation."""
    x1: int
    y1: int
    x2: int
    y2: int
    label: str
    confidence: float = Field(ge=0.0, le=1.0)


# ============================================================================
# Image Retriever Service API
# ============================================================================

class RetrievalRequest(BaseModel):
    """Request to retrieve images from a URL."""
    url: str
    strategy: str = "intercept"  # intercept, screenshot, download
    max_pages: Optional[int] = None
    output_dir: str = "/data/images"


class RetrievalResponse(BaseModel):
    """Response from image retrieval."""
    success: bool
    image_count: int
    image_paths: List[str]
    metadata: Dict[str, Any] = {}


# ============================================================================
# Layout Analyzer Service API
# ============================================================================

class LayoutAnalysisRequest(BaseModel):
    """Request to analyze page layout."""
    image_path: str
    confidence_threshold: float = 0.5


class PageLayoutResponse(BaseModel):
    """Layout analysis result for a single page."""
    page_path: str
    text_blocks: List[BoundingBox] = []
    illustrations: List[BoundingBox] = []
    captions: List[BoundingBox] = []
    titles: List[BoundingBox] = []
    tables: List[BoundingBox] = []
    other: List[BoundingBox] = []


class BatchLayoutAnalysisRequest(BaseModel):
    """Request to analyze multiple images."""
    image_dir: str
    confidence_threshold: float = 0.5


class BatchLayoutAnalysisResponse(BaseModel):
    """Batch layout analysis results."""
    success: bool
    pages_analyzed: int
    results: Dict[str, PageLayoutResponse]


# ============================================================================
# Image Processor Service API
# ============================================================================

class ImageProcessingRequest(BaseModel):
    """Request to process a single image."""
    image_path: str
    layout_data: PageLayoutResponse
    output_cleaned_path: str
    output_illustrations_dir: Optional[str] = None


class ImageProcessingResponse(BaseModel):
    """Image processing result."""
    success: bool
    original_path: str
    cleaned_path: str
    illustration_paths: List[str] = []
    metadata: Dict[str, Any] = {}


class BatchImageProcessingRequest(BaseModel):
    """Request to process multiple images."""
    image_dir: str
    layout_results: Dict[str, PageLayoutResponse]
    output_cleaned_dir: str
    output_illustrations_dir: Optional[str] = None


class BatchImageProcessingResponse(BaseModel):
    """Batch image processing results."""
    success: bool
    images_processed: int
    results: Dict[str, ImageProcessingResponse]


# ============================================================================
# OCR Engine Service API
# ============================================================================

class OCRRequest(BaseModel):
    """Request to extract text from an image."""
    image_path: str
    languages: List[str] = ["kat", "eng"]
    confidence_threshold: float = 60.0


class OCRResponse(BaseModel):
    """OCR result for a single image."""
    success: bool
    page_path: str
    text: str
    confidence: float
    word_count: int
    char_count: int
    line_data: List[Dict[str, Any]] = []


class BatchOCRRequest(BaseModel):
    """Request to extract text from multiple images."""
    image_dir: str
    output_dir: str
    languages: List[str] = ["kat", "eng"]
    confidence_threshold: float = 60.0
    combine: bool = True


class BatchOCRResponse(BaseModel):
    """Batch OCR results."""
    success: bool
    pages_processed: int
    total_words: int
    results: Dict[str, OCRResponse]
    combined_text_path: Optional[str] = None


# ============================================================================
# Illustration Interpreter Service API
# ============================================================================

class IllustrationInterpretationRequest(BaseModel):
    """Request to interpret an illustration."""
    image_path: str
    context: Optional[str] = None


class IllustrationInterpretationResponse(BaseModel):
    """Illustration interpretation result."""
    success: bool
    image_path: str
    caption: str
    description: str
    tags: List[str] = []
    educational_value: str = ""
    related_concepts: List[str] = []


class BatchInterpretationRequest(BaseModel):
    """Request to interpret multiple illustrations."""
    illustration_dir: str
    context: Optional[str] = None


class BatchInterpretationResponse(BaseModel):
    """Batch interpretation results."""
    success: bool
    illustrations_interpreted: int
    results: Dict[str, IllustrationInterpretationResponse]


# ============================================================================
# Pipeline Orchestrator API
# ============================================================================

class PipelineRequest(BaseModel):
    """Request to run the complete pipeline."""
    book_url: Optional[str] = None
    book_title: str = "untitled_book"
    skip_retrieval: bool = False
    skip_interpretation: bool = False
    config_overrides: Optional[Dict[str, Any]] = None


class PipelineStepRequest(BaseModel):
    """Request to run a specific pipeline step."""
    step_name: str  # retrieve, analyze, process, ocr, interpret, export
    parameters: Dict[str, Any] = {}


class PipelineResponse(BaseModel):
    """Pipeline execution result."""
    success: bool
    summary: Dict[str, Any]
    errors: List[str] = []
