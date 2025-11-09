"""
Layout Analyzer Service API

Exposes document layout analysis functionality as a REST API.
Implements the standard Layout Analyzer service interface.
"""

from fastapi import FastAPI, HTTPException
from pathlib import Path
from loguru import logger
import os

from ..layout_analyzer import LayoutAnalyzer
from .schemas import (
    HealthResponse,
    ServiceStatus,
    ErrorResponse,
    LayoutAnalysisRequest,
    PageLayoutResponse,
    BatchLayoutAnalysisRequest,
    BatchLayoutAnalysisResponse,
    BoundingBox,
)

# Initialize FastAPI app
app = FastAPI(
    title="Layout Analyzer Service",
    description="Analyzes document layout to detect text blocks, illustrations, and other elements",
    version="0.1.0",
)

# Global analyzer instance
analyzer = None


def get_analyzer() -> LayoutAnalyzer:
    """Get or create analyzer instance."""
    global analyzer
    if analyzer is None:
        analyzer = LayoutAnalyzer(
            confidence_threshold=float(os.getenv("LAYOUT_CONFIDENCE", "0.5")),
            device=os.getenv("LAYOUT_DEVICE", "cpu"),
        )
    return analyzer


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        get_analyzer()
        return HealthResponse(
            service_name="layout-analyzer",
            status=ServiceStatus.HEALTHY,
            details={"model": "loaded"},
        )
    except Exception as e:
        return HealthResponse(
            service_name="layout-analyzer",
            status=ServiceStatus.DEGRADED,
            details={"error": str(e)},
        )


@app.post("/analyze", response_model=PageLayoutResponse)
async def analyze_layout(request: LayoutAnalysisRequest):
    """
    Analyze layout of a single page image.

    Args:
        request: Layout analysis request

    Returns:
        Detected layout elements with bounding boxes

    Example:
        ```json
        {
            "image_path": "/data/images/page_001.png",
            "confidence_threshold": 0.5
        }
        ```
    """
    try:
        logger.info(f"Analyzing layout: {request.image_path}")

        analyzer = get_analyzer()
        layout = analyzer.analyze_page(Path(request.image_path))

        # Convert to response format
        def bbox_to_schema(bbox_obj):
            return BoundingBox(
                x1=bbox_obj.x1,
                y1=bbox_obj.y1,
                x2=bbox_obj.x2,
                y2=bbox_obj.y2,
                label=bbox_obj.label,
                confidence=bbox_obj.score,
            )

        return PageLayoutResponse(
            page_path=str(layout.page_path),
            text_blocks=[bbox_to_schema(b) for b in layout.text_blocks],
            illustrations=[bbox_to_schema(b) for b in layout.illustrations],
            captions=[bbox_to_schema(b) for b in layout.captions],
            titles=[bbox_to_schema(b) for b in layout.titles],
            tables=[bbox_to_schema(b) for b in layout.tables],
            other=[bbox_to_schema(b) for b in layout.other],
        )

    except Exception as e:
        logger.error(f"Layout analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Layout analysis failed",
                details=str(e),
                service="layout-analyzer",
            ).dict(),
        )


@app.post("/analyze/batch", response_model=BatchLayoutAnalysisResponse)
async def analyze_batch(request: BatchLayoutAnalysisRequest):
    """
    Analyze layout of multiple images in a directory.

    Args:
        request: Batch analysis request

    Returns:
        Layout analysis results for all pages

    Example:
        ```json
        {
            "image_dir": "/data/images",
            "confidence_threshold": 0.5
        }
        ```
    """
    try:
        logger.info(f"Batch analyzing: {request.image_dir}")

        analyzer = get_analyzer()
        results = analyzer.analyze_directory(Path(request.image_dir))

        # Convert results
        response_results = {}
        for page_name, layout in results.items():
            def bbox_to_schema(bbox_obj):
                return BoundingBox(
                    x1=bbox_obj.x1,
                    y1=bbox_obj.y1,
                    x2=bbox_obj.x2,
                    y2=bbox_obj.y2,
                    label=bbox_obj.label,
                    confidence=bbox_obj.score,
                )

            response_results[page_name] = PageLayoutResponse(
                page_path=str(layout.page_path),
                text_blocks=[bbox_to_schema(b) for b in layout.text_blocks],
                illustrations=[bbox_to_schema(b) for b in layout.illustrations],
                captions=[bbox_to_schema(b) for b in layout.captions],
                titles=[bbox_to_schema(b) for b in layout.titles],
                tables=[bbox_to_schema(b) for b in layout.tables],
                other=[bbox_to_schema(b) for b in layout.other],
            )

        return BatchLayoutAnalysisResponse(
            success=True,
            pages_analyzed=len(results),
            results=response_results,
        )

    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Batch analysis failed",
                details=str(e),
                service="layout-analyzer",
            ).dict(),
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
