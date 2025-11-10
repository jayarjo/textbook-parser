"""
Pipeline Orchestrator Service API

Coordinates all pipeline services to execute the complete workflow.
Implements the standard Orchestrator service interface.
"""

from fastapi import FastAPI, HTTPException
from pathlib import Path
from loguru import logger
import httpx
import os
from typing import Dict, Any

from .schemas import (
    HealthResponse,
    ServiceStatus,
    ErrorResponse,
    PipelineRequest,
    PipelineStepRequest,
    PipelineResponse,
)

# Initialize FastAPI app
app = FastAPI(
    title="Pipeline Orchestrator Service",
    description="Coordinates all pipeline services to process textbooks",
    version="0.1.0",
)

# Service URLs (from environment or defaults)
SERVICE_URLS = {
    "retriever": os.getenv("RETRIEVER_URL", "http://retriever:8001"),
    "layout_analyzer": os.getenv("LAYOUT_ANALYZER_URL", "http://layout-analyzer:8002"),
    "image_processor": os.getenv("IMAGE_PROCESSOR_URL", "http://image-processor:8003"),
    "ocr_engine": os.getenv("OCR_ENGINE_URL", "http://ocr-engine:8004"),
    "interpreter": os.getenv("INTERPRETER_URL", "http://illustration-interpreter:8005"),
}


async def check_service_health(service_name: str, url: str) -> Dict[str, Any]:
    """Check health of a service."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{url}/health")
            return {"service": service_name, "status": "healthy", "details": response.json()}
    except Exception as e:
        return {"service": service_name, "status": "unhealthy", "error": str(e)}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint - checks all services."""
    service_statuses = {}

    for service_name, url in SERVICE_URLS.items():
        status = await check_service_health(service_name, url)
        service_statuses[service_name] = status

    # Determine overall status
    all_healthy = all(s["status"] == "healthy" for s in service_statuses.values())

    return HealthResponse(
        service_name="orchestrator",
        status=ServiceStatus.HEALTHY if all_healthy else ServiceStatus.DEGRADED,
        details={"services": service_statuses},
    )


@app.post("/pipeline", response_model=PipelineResponse)
async def run_pipeline(request: PipelineRequest):
    """
    Run the complete pipeline.

    Coordinates all services to process a book from URL to final output.

    Args:
        request: Pipeline request with book URL and options

    Returns:
        Pipeline execution summary

    Example:
        ```json
        {
            "book_url": "https://example.com/book",
            "book_title": "Georgian History",
            "skip_retrieval": false,
            "skip_interpretation": false
        }
        ```
    """
    try:
        logger.info(f"Starting pipeline for: {request.book_title}")

        summary = {}
        errors = []

        # Data paths (shared volume)
        data_dir = Path("/data")
        images_dir = data_dir / "images"
        cleaned_dir = data_dir / "cleaned"
        text_dir = data_dir / "text"
        illustrations_dir = data_dir / "illustrations"

        async with httpx.AsyncClient(timeout=300.0) as client:
            # Step 1: Retrieve Images
            if not request.skip_retrieval:
                logger.info("Step 1: Retrieving images...")
                try:
                    response = await client.post(
                        f"{SERVICE_URLS['retriever']}/retrieve",
                        json={
                            "url": request.book_url,
                            "strategy": "intercept",
                            "max_pages": request.max_pages,  # Pass through pagination
                            "output_dir": str(images_dir),
                        },
                    )
                    response.raise_for_status()
                    result = response.json()
                    summary["images_retrieved"] = result["image_count"]
                    logger.info(f"✓ Retrieved {result['image_count']} images")
                except Exception as e:
                    errors.append(f"Image retrieval failed: {str(e)}")
                    logger.error(f"Image retrieval failed: {e}")

            # Step 2: Analyze Layouts
            logger.info("Step 2: Analyzing layouts...")
            try:
                response = await client.post(
                    f"{SERVICE_URLS['layout_analyzer']}/analyze/batch",
                    json={
                        "image_dir": str(images_dir),
                        "confidence_threshold": 0.5,
                    },
                )
                response.raise_for_status()
                result = response.json()
                layout_results = result["results"]
                summary["pages_analyzed"] = result["pages_analyzed"]
                logger.info(f"✓ Analyzed {result['pages_analyzed']} pages")
            except Exception as e:
                errors.append(f"Layout analysis failed: {str(e)}")
                logger.error(f"Layout analysis failed: {e}")
                raise

            # Step 3: Process Images
            logger.info("Step 3: Processing images...")
            try:
                response = await client.post(
                    f"{SERVICE_URLS['image_processor']}/process/batch",
                    json={
                        "image_dir": str(images_dir),
                        "layout_results": layout_results,
                        "output_cleaned_dir": str(cleaned_dir),
                        "output_illustrations_dir": str(illustrations_dir),
                    },
                )
                response.raise_for_status()
                result = response.json()
                summary["images_processed"] = result["images_processed"]
                # Count total illustrations
                total_illustrations = sum(
                    len(r["illustration_paths"]) for r in result["results"].values()
                )
                summary["illustrations_extracted"] = total_illustrations
                logger.info(f"✓ Processed {result['images_processed']} images")
            except Exception as e:
                errors.append(f"Image processing failed: {str(e)}")
                logger.error(f"Image processing failed: {e}")
                raise

            # Step 4: Extract Text
            logger.info("Step 4: Extracting text...")
            try:
                response = await client.post(
                    f"{SERVICE_URLS['ocr_engine']}/extract/batch",
                    json={
                        "image_dir": str(cleaned_dir),
                        "output_dir": str(text_dir),
                        "languages": ["kat", "eng"],
                        "confidence_threshold": 60.0,
                        "combine": True,
                    },
                )
                response.raise_for_status()
                result = response.json()
                summary["pages_ocr"] = result["pages_processed"]
                summary["total_words"] = result["total_words"]
                logger.info(f"✓ Extracted {result['total_words']} words")
            except Exception as e:
                errors.append(f"OCR failed: {str(e)}")
                logger.error(f"OCR failed: {e}")
                raise

            # Step 5: Interpret Illustrations (if not skipped)
            if not request.skip_interpretation:
                logger.info("Step 5: Interpreting illustrations...")
                try:
                    response = await client.post(
                        f"{SERVICE_URLS['interpreter']}/interpret/batch",
                        json={
                            "illustration_dir": str(illustrations_dir),
                            "context": f"Educational textbook: {request.book_title}",
                        },
                    )
                    response.raise_for_status()
                    result = response.json()
                    summary["illustrations_interpreted"] = result[
                        "illustrations_interpreted"
                    ]
                    logger.info(
                        f"✓ Interpreted {result['illustrations_interpreted']} illustrations"
                    )
                except Exception as e:
                    errors.append(f"Interpretation failed: {str(e)}")
                    logger.error(f"Interpretation failed: {e}")
            else:
                summary["illustrations_interpreted"] = 0

        logger.info("Pipeline execution complete!")

        return PipelineResponse(
            success=len(errors) == 0,
            summary=summary,
            errors=errors,
        )

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Pipeline execution failed",
                details=str(e),
                service="orchestrator",
            ).dict(),
        )


@app.post("/pipeline/step", response_model=Dict[str, Any])
async def run_pipeline_step(request: PipelineStepRequest):
    """
    Run a specific pipeline step.

    Args:
        request: Step request with step name and parameters

    Returns:
        Step execution result

    Example:
        ```json
        {
            "step_name": "ocr",
            "parameters": {
                "image_dir": "/data/cleaned",
                "output_dir": "/data/text"
            }
        }
        ```
    """
    try:
        logger.info(f"Running step: {request.step_name}")

        step_mapping = {
            "retrieve": ("retriever", "/retrieve"),
            "analyze": ("layout_analyzer", "/analyze/batch"),
            "process": ("image_processor", "/process/batch"),
            "ocr": ("ocr_engine", "/extract/batch"),
            "interpret": ("interpreter", "/interpret/batch"),
        }

        if request.step_name not in step_mapping:
            raise HTTPException(status_code=400, detail=f"Unknown step: {request.step_name}")

        service_name, endpoint = step_mapping[request.step_name]
        service_url = SERVICE_URLS[service_name]

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{service_url}{endpoint}",
                json=request.parameters,
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPError as e:
        logger.error(f"Step execution failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Step {request.step_name} failed: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
