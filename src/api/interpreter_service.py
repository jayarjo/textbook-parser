"""
Illustration Interpreter Service API

Exposes illustration interpretation functionality as a REST API.
Implements the standard Illustration Interpreter service interface.
"""

from fastapi import FastAPI, HTTPException
from pathlib import Path
from loguru import logger
import os

from ..illustration_interpreter import IllustrationInterpreter
from .schemas import (
    HealthResponse,
    ServiceStatus,
    ErrorResponse,
    IllustrationInterpretationRequest,
    IllustrationInterpretationResponse,
    BatchInterpretationRequest,
    BatchInterpretationResponse,
)

# Initialize FastAPI app
app = FastAPI(
    title="Illustration Interpreter Service",
    description="Interprets illustrations using vision-language models",
    version="0.1.0",
)

# Global interpreter instance
interpreter = None


def get_interpreter() -> IllustrationInterpreter:
    """Get or create interpreter instance."""
    global interpreter
    if interpreter is None:
        provider = os.getenv("VISION_PROVIDER", "openai")
        api_key = os.getenv(f"{provider.upper()}_API_KEY")

        if not api_key:
            raise ValueError(f"API key not found for provider: {provider}")

        interpreter = IllustrationInterpreter(
            provider=provider,
            model=os.getenv("VISION_MODEL", "gpt-4-vision-preview"),
            api_key=api_key,
        )
    return interpreter


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        provider = os.getenv("VISION_PROVIDER", "openai")
        api_key = os.getenv(f"{provider.upper()}_API_KEY")

        if not api_key:
            return HealthResponse(
                service_name="interpreter",
                status=ServiceStatus.DEGRADED,
                details={"error": "API key not configured"},
            )

        return HealthResponse(
            service_name="interpreter",
            status=ServiceStatus.HEALTHY,
            details={"provider": provider},
        )
    except Exception as e:
        return HealthResponse(
            service_name="interpreter",
            status=ServiceStatus.UNHEALTHY,
            details={"error": str(e)},
        )


@app.post("/interpret", response_model=IllustrationInterpretationResponse)
async def interpret_illustration(request: IllustrationInterpretationRequest):
    """
    Interpret a single illustration using AI vision models.

    Args:
        request: Interpretation request

    Returns:
        Caption, description, tags, and educational value

    Example:
        ```json
        {
            "image_path": "/data/illustrations/page_001_illus_01.png",
            "context": "Georgian history textbook chapter about medieval castles"
        }
        ```
    """
    try:
        logger.info(f"Interpreting illustration: {request.image_path}")

        interp = get_interpreter()
        result = interp.interpret_illustration(
            Path(request.image_path), context=request.context
        )

        return IllustrationInterpretationResponse(
            success=True,
            image_path=str(result.image_path),
            caption=result.caption,
            description=result.description,
            tags=result.tags,
            educational_value=result.educational_value,
            related_concepts=result.related_concepts,
        )

    except Exception as e:
        logger.error(f"Interpretation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Interpretation failed",
                details=str(e),
                service="interpreter",
            ).dict(),
        )


@app.post("/interpret/batch", response_model=BatchInterpretationResponse)
async def interpret_batch(request: BatchInterpretationRequest):
    """
    Interpret multiple illustrations in a directory.

    Args:
        request: Batch interpretation request

    Returns:
        Interpretations for all illustrations

    Example:
        ```json
        {
            "illustration_dir": "/data/illustrations",
            "context": "Educational textbook about Georgian history"
        }
        ```
    """
    try:
        logger.info(f"Batch interpreting: {request.illustration_dir}")

        interp = get_interpreter()
        output_path = Path(request.illustration_dir) / "interpretations.json"

        results = interp.interpret_batch(
            illustration_dir=Path(request.illustration_dir),
            output_path=output_path,
            context=request.context,
        )

        # Convert results
        response_results = {}
        for name, result in results.items():
            response_results[name] = IllustrationInterpretationResponse(
                success=True,
                image_path=str(result.image_path),
                caption=result.caption,
                description=result.description,
                tags=result.tags,
                educational_value=result.educational_value,
                related_concepts=result.related_concepts,
            )

        return BatchInterpretationResponse(
            success=True,
            illustrations_interpreted=len(results),
            results=response_results,
        )

    except Exception as e:
        logger.error(f"Batch interpretation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Batch interpretation failed",
                details=str(e),
                service="interpreter",
            ).dict(),
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8005)
