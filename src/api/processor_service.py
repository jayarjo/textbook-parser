"""
Image Processor Service API

Exposes image processing functionality as a REST API.
Implements the standard Image Processor service interface.
"""

from fastapi import FastAPI, HTTPException
from pathlib import Path
from loguru import logger
import os

from ..image_processor import ImageProcessor
from .schemas import (
    HealthResponse,
    ServiceStatus,
    ErrorResponse,
    ImageProcessingRequest,
    ImageProcessingResponse,
    BatchImageProcessingRequest,
    BatchImageProcessingResponse,
)

# Initialize FastAPI app
app = FastAPI(
    title="Image Processor Service",
    description="Processes images to mask illustrations and enhance for OCR",
    version="0.1.0",
)

# Global processor instance
processor = None


def get_processor() -> ImageProcessor:
    """Get or create processor instance."""
    global processor
    if processor is None:
        processor = ImageProcessor(
            mask_color=(255, 255, 255),
            padding=int(os.getenv("PROCESSOR_PADDING", "5")),
        )
    return processor


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        service_name="image-processor",
        status=ServiceStatus.HEALTHY,
        details={"ready": True},
    )


@app.post("/process", response_model=ImageProcessingResponse)
async def process_image(request: ImageProcessingRequest):
    """
    Process a single page image.

    Masks illustrations and prepares image for OCR.

    Args:
        request: Image processing request

    Returns:
        Paths to processed images

    Example:
        ```json
        {
            "image_path": "/data/images/page_001.png",
            "layout_data": {...},
            "output_cleaned_path": "/data/cleaned/page_001.png",
            "output_illustrations_dir": "/data/illustrations"
        }
        ```
    """
    try:
        logger.info(f"Processing image: {request.image_path}")

        processor = get_processor()

        # Convert Pydantic model to dict for compatibility
        layout_dict = request.layout_data.dict()

        metadata = processor.process_page(
            image_path=Path(request.image_path),
            layout_data=layout_dict,
            output_cleaned_path=Path(request.output_cleaned_path),
            output_illustrations_dir=Path(request.output_illustrations_dir)
            if request.output_illustrations_dir
            else None,
        )

        return ImageProcessingResponse(
            success=True,
            original_path=metadata["original_path"],
            cleaned_path=metadata["cleaned_path"],
            illustration_paths=metadata["illustration_paths"],
            metadata=metadata,
        )

    except Exception as e:
        logger.error(f"Image processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Image processing failed",
                details=str(e),
                service="image-processor",
            ).dict(),
        )


@app.post("/process/batch", response_model=BatchImageProcessingResponse)
async def process_batch(request: BatchImageProcessingRequest):
    """
    Process multiple images in a batch.

    Args:
        request: Batch processing request

    Returns:
        Processing results for all images

    Example:
        ```json
        {
            "image_dir": "/data/images",
            "layout_results": {...},
            "output_cleaned_dir": "/data/cleaned",
            "output_illustrations_dir": "/data/illustrations"
        }
        ```
    """
    try:
        logger.info(f"Batch processing: {request.image_dir}")

        processor = get_processor()

        # Convert layout results to dict format
        layout_results_dict = {
            k: v.dict() for k, v in request.layout_results.items()
        }

        results = processor.process_batch(
            image_dir=Path(request.image_dir),
            layout_results=layout_results_dict,
            output_cleaned_dir=Path(request.output_cleaned_dir),
            output_illustrations_dir=Path(request.output_illustrations_dir)
            if request.output_illustrations_dir
            else None,
        )

        # Convert results
        response_results = {}
        for page_name, metadata in results.items():
            response_results[page_name] = ImageProcessingResponse(
                success=True,
                original_path=metadata["original_path"],
                cleaned_path=metadata["cleaned_path"],
                illustration_paths=metadata["illustration_paths"],
                metadata=metadata,
            )

        return BatchImageProcessingResponse(
            success=True,
            images_processed=len(results),
            results=response_results,
        )

    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Batch processing failed",
                details=str(e),
                service="image-processor",
            ).dict(),
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
