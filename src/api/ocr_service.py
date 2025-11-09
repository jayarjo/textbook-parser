"""
OCR Engine Service API

Exposes OCR functionality as a REST API.
Implements the standard OCR Engine service interface.
"""

from fastapi import FastAPI, HTTPException
from pathlib import Path
from loguru import logger
import os

from ..ocr_engine import OCREngine
from .schemas import (
    HealthResponse,
    ServiceStatus,
    ErrorResponse,
    OCRRequest,
    OCRResponse,
    BatchOCRRequest,
    BatchOCRResponse,
)

# Initialize FastAPI app
app = FastAPI(
    title="OCR Engine Service",
    description="Extracts text from images using Tesseract or PaddleOCR",
    version="0.1.0",
)

# Global OCR engine instance
ocr_engine = None


def get_ocr_engine(languages=None) -> OCREngine:
    """Get or create OCR engine instance."""
    global ocr_engine
    if ocr_engine is None:
        ocr_engine = OCREngine(
            engine=os.getenv("OCR_ENGINE", "tesseract"),
            languages=languages or ["kat", "eng"],
            confidence_threshold=float(os.getenv("OCR_CONFIDENCE", "60.0")),
        )
    return ocr_engine


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        get_ocr_engine()
        return HealthResponse(
            service_name="ocr-engine",
            status=ServiceStatus.HEALTHY,
            details={"engine": os.getenv("OCR_ENGINE", "tesseract")},
        )
    except Exception as e:
        return HealthResponse(
            service_name="ocr-engine",
            status=ServiceStatus.UNHEALTHY,
            details={"error": str(e)},
        )


@app.post("/extract", response_model=OCRResponse)
async def extract_text(request: OCRRequest):
    """
    Extract text from a single image.

    Args:
        request: OCR request

    Returns:
        Extracted text with metadata

    Example:
        ```json
        {
            "image_path": "/data/cleaned/page_001.png",
            "languages": ["kat", "eng"],
            "confidence_threshold": 60.0
        }
        ```
    """
    try:
        logger.info(f"Extracting text from: {request.image_path}")

        ocr = get_ocr_engine(request.languages)
        result = ocr.extract_text(Path(request.image_path))

        return OCRResponse(
            success=True,
            page_path=str(result.page_path),
            text=result.text,
            confidence=result.confidence,
            word_count=result.word_count,
            char_count=result.char_count,
            line_data=result.line_data,
        )

    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="OCR extraction failed",
                details=str(e),
                service="ocr-engine",
            ).dict(),
        )


@app.post("/extract/batch", response_model=BatchOCRResponse)
async def extract_batch(request: BatchOCRRequest):
    """
    Extract text from multiple images in a directory.

    Args:
        request: Batch OCR request

    Returns:
        Extracted text for all images

    Example:
        ```json
        {
            "image_dir": "/data/cleaned",
            "output_dir": "/data/text",
            "languages": ["kat", "eng"],
            "confidence_threshold": 60.0,
            "combine": true
        }
        ```
    """
    try:
        logger.info(f"Batch OCR on: {request.image_dir}")

        ocr = get_ocr_engine(request.languages)
        results = ocr.extract_batch(
            image_dir=Path(request.image_dir),
            output_dir=Path(request.output_dir),
            combine=request.combine,
        )

        # Convert results
        response_results = {}
        total_words = 0
        for page_name, result in results.items():
            response_results[page_name] = OCRResponse(
                success=True,
                page_path=str(result.page_path),
                text=result.text,
                confidence=result.confidence,
                word_count=result.word_count,
                char_count=result.char_count,
                line_data=result.line_data,
            )
            total_words += result.word_count

        combined_path = None
        if request.combine:
            combined_path = str(Path(request.output_dir) / "book_full.txt")

        return BatchOCRResponse(
            success=True,
            pages_processed=len(results),
            total_words=total_words,
            results=response_results,
            combined_text_path=combined_path,
        )

    except Exception as e:
        logger.error(f"Batch OCR failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Batch OCR failed",
                details=str(e),
                service="ocr-engine",
            ).dict(),
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8004)
