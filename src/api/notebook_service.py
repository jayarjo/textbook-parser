"""
NotebookLM Integration API Service

FastAPI service for automating Google NotebookLM interactions using Playwright.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Optional, Dict, Any
import uvicorn
from loguru import logger

from src.notebook_integration.notebook_integration import NotebookIntegration

app = FastAPI(
    title="NotebookLM Integration Service",
    description="Automates Google NotebookLM using Playwright",
    version="0.1.0"
)


# Request/Response Models
class NotebookRequest(BaseModel):
    """Request to create and populate a NotebookLM notebook."""
    source_file_path: str = Field(..., description="Path to source file to upload")
    notebook_name: Optional[str] = Field(None, description="Name for the notebook")
    generate_audio: bool = Field(True, description="Generate audio overview")
    generate_quiz: bool = Field(True, description="Generate quiz questions")
    quiz_question_count: int = Field(10, description="Number of quiz questions")
    generate_flashcards: bool = Field(True, description="Generate flashcards")
    generate_study_guide: bool = Field(True, description="Generate study guide")
    headless: bool = Field(True, description="Run browser in headless mode")
    user_data_dir: Optional[str] = Field(None, description="Path to browser user data dir for persistent login")


class NotebookResponse(BaseModel):
    """Response from NotebookLM automation."""
    success: bool
    notebook_url: Optional[str] = None
    uploaded: bool = False
    audio_generated: bool = False
    quiz_generated: bool = False
    flashcards_generated: bool = False
    study_guide_generated: bool = False
    errors: list = []
    message: str = ""


class HealthResponse(BaseModel):
    """Health check response."""
    service_name: str
    version: str
    status: str
    playwright_available: bool


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        from playwright.sync_api import sync_playwright
        playwright_available = True
    except ImportError:
        playwright_available = False

    return HealthResponse(
        service_name="notebook-integration",
        version="0.1.0",
        status="healthy" if playwright_available else "degraded",
        playwright_available=playwright_available
    )


@app.post("/automate", response_model=NotebookResponse)
async def automate_notebooklm(request: NotebookRequest):
    """
    Automate the complete NotebookLM workflow.

    This endpoint:
    1. Opens NotebookLM in a browser
    2. Creates a new notebook
    3. Uploads the source file
    4. Requests generation of audio, quiz, flashcards, and study guide

    Note: This is a synchronous operation that may take several minutes.
    For long-running operations, consider using background tasks.
    """
    logger.info(f"Starting NotebookLM automation for: {request.source_file_path}")

    source_path = Path(request.source_file_path)

    if not source_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Source file not found: {source_path}"
        )

    user_data_path = Path(request.user_data_dir) if request.user_data_dir else None

    try:
        # Initialize and run automation
        with NotebookIntegration(
            headless=request.headless,
            slow_mo=500,
            timeout=60000,
            user_data_dir=user_data_path
        ) as notebook:
            results = notebook.automate_full_workflow(
                source_file=source_path,
                notebook_name=request.notebook_name,
                generate_audio=request.generate_audio,
                generate_quiz_count=request.quiz_question_count if request.generate_quiz else None,
                generate_flashcards_flag=request.generate_flashcards,
                generate_study_guide_flag=request.generate_study_guide
            )

        # Build response
        response = NotebookResponse(
            success=results["success"],
            notebook_url=results.get("notebook_url"),
            uploaded=results.get("uploaded", False),
            audio_generated=results.get("audio_generated", False),
            quiz_generated=results.get("quiz_generated", False),
            flashcards_generated=results.get("flashcards_generated", False),
            study_guide_generated=results.get("study_guide_generated", False),
            errors=results.get("errors", []),
            message="NotebookLM automation completed successfully" if results["success"]
                   else "NotebookLM automation completed with errors"
        )

        return response

    except ImportError as e:
        logger.error(f"Playwright not available: {e}")
        raise HTTPException(
            status_code=500,
            detail="Playwright not installed. Run: pip install playwright && playwright install chromium"
        )
    except Exception as e:
        logger.error(f"Error during NotebookLM automation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Automation error: {str(e)}"
        )


@app.post("/create-notebook", response_model=Dict[str, Any])
async def create_notebook_only(notebook_name: Optional[str] = None, headless: bool = True):
    """
    Create a new NotebookLM notebook only (without uploading content).

    Returns the notebook URL.
    """
    logger.info(f"Creating new notebook: {notebook_name or 'Untitled'}")

    try:
        with NotebookIntegration(headless=headless) as notebook:
            notebook.navigate_to_notebooklm()
            notebook_url = notebook.create_new_notebook(notebook_name)

        return {
            "success": True,
            "notebook_url": notebook_url,
            "message": "Notebook created successfully"
        }

    except Exception as e:
        logger.error(f"Error creating notebook: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create notebook: {str(e)}"
        )


@app.post("/upload-file", response_model=Dict[str, Any])
async def upload_file_only(
    source_file_path: str,
    notebook_url: str,
    headless: bool = True
):
    """
    Upload a file to an existing NotebookLM notebook.

    Requires the notebook to already be open in the browser.
    """
    logger.info(f"Uploading file to notebook: {notebook_url}")

    source_path = Path(source_file_path)

    if not source_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Source file not found: {source_path}"
        )

    try:
        with NotebookIntegration(headless=headless) as notebook:
            # Navigate to the specific notebook
            notebook.page.goto(notebook_url, wait_until="networkidle")

            # Upload file
            success = notebook.upload_source_file(source_path)

        return {
            "success": success,
            "message": "File uploaded successfully" if success else "Upload may have failed"
        }

    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8006,
        log_level="info"
    )
