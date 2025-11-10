"""
SVG Text Processor Service API

Exposes SVG text extraction functionality as a REST API.
"""

from fastapi import FastAPI, HTTPException
from pathlib import Path
from loguru import logger
from typing import Optional
from pydantic import BaseModel

from ..svg_processor import SVGTextProcessor
from .schemas import (
    HealthResponse,
    ServiceStatus,
    ErrorResponse,
)


# Pydantic models
class SVGProcessRequest(BaseModel):
    """Request for processing a single SVG file."""
    svg_path: str


class SVGBatchRequest(BaseModel):
    """Request for batch processing SVG files."""
    svg_dir: str
    output_path: Optional[str] = None


class SVGProcessResponse(BaseModel):
    """Response from SVG processing."""
    success: bool
    file: str
    text: str
    text_elements: int = 0
    characters: int = 0
    error: Optional[str] = None


class SVGBatchResponse(BaseModel):
    """Response from batch SVG processing."""
    success: bool
    files_processed: int
    files_succeeded: int
    total_characters: int
    output_path: Optional[str] = None


# Initialize FastAPI app
app = FastAPI(
    title="SVG Text Processor Service",
    description="Extracts text directly from SVG/SVGZ files without OCR",
    version="0.1.0",
)

# Global processor instance
processor = SVGTextProcessor()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        service_name="svg-processor",
        status=ServiceStatus.HEALTHY,
        details={"processor": "ready"},
    )


@app.post("/process", response_model=SVGProcessResponse)
async def process_svg(request: SVGProcessRequest):
    """
    Process a single SVG/SVGZ file and extract text.

    Args:
        request: SVG processing request

    Returns:
        Extracted text and metadata
    """
    try:
        logger.info(f"Processing SVG file: {request.svg_path}")

        svg_path = Path(request.svg_path)
        if not svg_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"SVG file not found: {request.svg_path}"
            )

        result = processor.process_file(svg_path)

        return SVGProcessResponse(**result)

    except Exception as e:
        logger.error(f"SVG processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="SVG processing failed",
                details=str(e),
                service="svg-processor",
            ).dict(),
        )


@app.post("/process/batch", response_model=SVGBatchResponse)
async def process_svg_batch(request: SVGBatchRequest):
    """
    Process all SVG/SVGZ files in a directory.

    Args:
        request: Batch processing request

    Returns:
        Batch processing results
    """
    try:
        logger.info(f"Batch processing SVG files from: {request.svg_dir}")

        svg_dir = Path(request.svg_dir)
        if not svg_dir.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Directory not found: {request.svg_dir}"
            )

        output_path = Path(request.output_path) if request.output_path else None

        result = processor.process_batch(svg_dir, output_path)

        return SVGBatchResponse(**result)

    except Exception as e:
        logger.error(f"Batch SVG processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Batch SVG processing failed",
                details=str(e),
                service="svg-processor",
            ).dict(),
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8007)
