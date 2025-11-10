"""
Image Retriever Service API

Exposes image retrieval functionality as a REST API.
Implements the standard Retriever service interface.
"""

from fastapi import FastAPI, HTTPException
from pathlib import Path
from loguru import logger
import os

from ..retriever import ImageRetriever
from .schemas import (
    HealthResponse,
    ServiceStatus,
    ErrorResponse,
    RetrievalRequest,
    RetrievalResponse,
)

# Initialize FastAPI app
app = FastAPI(
    title="Image Retriever Service",
    description="Retrieves book page images from web sources using browser automation",
    version="0.1.0",
)

# Global retriever instance (initialized on first request)
retriever_instance = None


def get_retriever(output_dir: str) -> ImageRetriever:
    """Get or create retriever instance."""
    return ImageRetriever(
        output_dir=Path(output_dir),
        headless=True,
        timeout=int(os.getenv("RETRIEVER_TIMEOUT", "30000")),
        max_retries=int(os.getenv("RETRIEVER_MAX_RETRIES", "3")),
        wait_for_images=int(os.getenv("RETRIEVER_WAIT_FOR_IMAGES", "2000")),
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        service_name="retriever",
        status=ServiceStatus.HEALTHY,
        details={"playwright": "available"},
    )


@app.post("/retrieve", response_model=RetrievalResponse)
async def retrieve_images(request: RetrievalRequest):
    """
    Retrieve book page images from a URL.

    Args:
        request: Retrieval request with URL and options

    Returns:
        List of retrieved image paths

    Example:
        ```json
        {
            "url": "https://example.com/book",
            "strategy": "intercept",
            "max_pages": 100,
            "output_dir": "/data/images"
        }
        ```
    """
    try:
        logger.info(f"Retrieving images from {request.url}")

        retriever = get_retriever(request.output_dir)

        # Use async method directly since we're in an async endpoint
        image_paths = await retriever.retrieve_images(
            url=request.url,
            strategy=request.strategy,
            max_pages=request.max_pages,
            page_start=request.page_start,
            page_end=request.page_end,
        )

        return RetrievalResponse(
            success=True,
            image_count=len(image_paths),
            image_paths=[str(p) for p in image_paths],
            metadata={
                "strategy": request.strategy,
                "url": request.url,
            },
        )

    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Retrieval failed",
                details=str(e),
                service="retriever",
            ).dict(),
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
