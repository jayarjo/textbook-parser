# Textbook Parser - Service API Documentation

Complete API reference for all pipeline services. This document defines the standard interface that allows you to **replace any service** with an alternative implementation.

## Table of Contents

1. [Overview](#overview)
2. [Service Architecture](#service-architecture)
3. [Common Conventions](#common-conventions)
4. [Image Retriever Service](#image-retriever-service)
5. [Layout Analyzer Service](#layout-analyzer-service)
6. [Image Processor Service](#image-processor-service)
7. [OCR Engine Service](#ocr-engine-service)
8. [Illustration Interpreter Service](#illustration-interpreter-service)
9. [Pipeline Orchestrator Service](#pipeline-orchestrator-service)
10. [Creating Alternative Implementations](#creating-alternative-implementations)
11. [Testing Your Implementation](#testing-your-implementation)

---

## Overview

The textbook parser uses a **microservices architecture** where each pipeline step is an independent REST API service. This allows you to:

- **Replace individual services** with alternative implementations
- **Scale services independently** based on workload
- **Use different technology stacks** for each service
- **Deploy services on different infrastructure**

### Key Principles

1. **Stateless**: Services don't maintain state between requests
2. **RESTful**: Standard HTTP methods (GET, POST)
3. **JSON**: All requests and responses use JSON
4. **Consistent**: All services follow the same patterns
5. **Documented**: OpenAPI/Swagger docs available at `/docs` endpoint

---

## Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Pipeline Orchestrator                     │
│                    http://orchestrator:8000                  │
└────────────┬──────────────────────────────────┬─────────────┘
             │                                  │
    ┌────────▼────────┐              ┌─────────▼──────────┐
    │   Retriever     │              │  Layout Analyzer   │
    │   Port: 8001    │              │    Port: 8002      │
    └────────┬────────┘              └─────────┬──────────┘
             │                                  │
    ┌────────▼────────┐              ┌─────────▼──────────┐
    │ Image Processor │              │    OCR Engine      │
    │   Port: 8003    │              │    Port: 8004      │
    └────────┬────────┘              └─────────┬──────────┘
             │                                  │
             └──────────┬───────────────────────┘
                        │
              ┌─────────▼──────────┐
              │    Interpreter     │
              │    Port: 8005      │
              └────────────────────┘
```

### Service Ports

| Service | Port | Purpose |
|---------|------|---------|
| Orchestrator | 8000 | Coordinates all services |
| Retriever | 8001 | Downloads book images |
| Layout Analyzer | 8002 | Detects page elements |
| Image Processor | 8003 | Masks and enhances images |
| OCR Engine | 8004 | Extracts text |
| Interpreter | 8005 | Analyzes illustrations |

---

## Common Conventions

### Health Check Endpoint

**All services** must implement a health check endpoint:

```
GET /health
```

**Response:**
```json
{
  "service_name": "service-name",
  "version": "0.1.0",
  "status": "healthy",  // or "degraded", "unhealthy"
  "details": {
    // service-specific details
  }
}
```

### Error Response Format

**All services** must return errors in this format:

```json
{
  "error": "Brief error description",
  "details": "Detailed error message",
  "service": "service-name"
}
```

### Standard Headers

```
Content-Type: application/json
Accept: application/json
```

### Common Data Types

#### BoundingBox

```json
{
  "x1": 100,
  "y1": 150,
  "x2": 400,
  "y2": 350,
  "label": "Figure",
  "confidence": 0.92
}
```

---

## Image Retriever Service

**Base URL:** `http://retriever:8001`

Downloads book page images from online sources.

### POST /retrieve

Retrieve images from a book URL.

**Request:**
```json
{
  "url": "https://example.com/book-viewer",
  "strategy": "intercept",  // "intercept", "screenshot", "download"
  "max_pages": 100,  // optional, null for all pages
  "output_dir": "/data/images"
}
```

**Response:**
```json
{
  "success": true,
  "image_count": 100,
  "image_paths": [
    "/data/images/page_001.png",
    "/data/images/page_002.png"
  ],
  "metadata": {
    "strategy": "intercept",
    "url": "https://example.com/book-viewer"
  }
}
```

**Strategies:**

1. **intercept** - Intercept network requests (best quality)
2. **screenshot** - Take page screenshots (reliable)
3. **download** - Direct image download (fastest)

### Implementation Requirements

Your alternative implementation must:

- Accept a URL and download all accessible images
- Save images sequentially (`page_001.png`, `page_002.png`, etc.)
- Support pagination/navigation
- Handle errors gracefully (timeouts, missing pages)
- Return complete list of downloaded image paths

### Example Alternative Stack

- **Python + Selenium**: For different browser automation
- **Node.js + Puppeteer**: JavaScript-based retrieval
- **Scrapy**: For static image scraping
- **Custom downloader**: If images have direct URLs

---

## Layout Analyzer Service

**Base URL:** `http://layout-analyzer:8002`

Analyzes document layout to detect text blocks, illustrations, tables, etc.

### POST /analyze

Analyze a single page image.

**Request:**
```json
{
  "image_path": "/data/images/page_001.png",
  "confidence_threshold": 0.5
}
```

**Response:**
```json
{
  "page_path": "/data/images/page_001.png",
  "text_blocks": [
    {
      "x1": 50, "y1": 100, "x2": 500, "y2": 200,
      "label": "Text",
      "confidence": 0.95
    }
  ],
  "illustrations": [
    {
      "x1": 100, "y1": 300, "x2": 400, "y2": 500,
      "label": "Figure",
      "confidence": 0.89
    }
  ],
  "captions": [],
  "titles": [],
  "tables": [],
  "other": []
}
```

### POST /analyze/batch

Analyze multiple images.

**Request:**
```json
{
  "image_dir": "/data/images",
  "confidence_threshold": 0.5
}
```

**Response:**
```json
{
  "success": true,
  "pages_analyzed": 100,
  "results": {
    "page_001": { /* PageLayoutResponse */ },
    "page_002": { /* PageLayoutResponse */ }
  }
}
```

### Implementation Requirements

Your alternative implementation must:

- Detect at minimum: text blocks and illustrations
- Return bounding boxes in (x1, y1, x2, y2) format
- Provide confidence scores (0.0 to 1.0)
- Support batch processing
- Handle various page layouts

### Example Alternative Stack

- **PaddleOCR Layout**: Chinese/multilingual layout analysis
- **DocTR**: Document Text Recognition library
- **Custom YOLO model**: Trained on your specific documents
- **Azure Computer Vision**: Cloud-based layout detection
- **OpenCV + Heuristics**: Rule-based detection

---

## Image Processor Service

**Base URL:** `http://image-processor:8003`

Processes images to mask illustrations and enhance for OCR.

### POST /process

Process a single image.

**Request:**
```json
{
  "image_path": "/data/images/page_001.png",
  "layout_data": {
    "page_path": "/data/images/page_001.png",
    "text_blocks": [],
    "illustrations": [
      {
        "x1": 100, "y1": 300, "x2": 400, "y2": 500,
        "label": "Figure",
        "confidence": 0.89
      }
    ]
  },
  "output_cleaned_path": "/data/cleaned/page_001.png",
  "output_illustrations_dir": "/data/illustrations"
}
```

**Response:**
```json
{
  "success": true,
  "original_path": "/data/images/page_001.png",
  "cleaned_path": "/data/cleaned/page_001.png",
  "illustration_paths": [
    "/data/illustrations/page_001_illus_01.png"
  ],
  "metadata": {
    "illustrations_count": 1,
    "original_size": [1920, 1080]
  }
}
```

### POST /process/batch

Process multiple images.

**Request:**
```json
{
  "image_dir": "/data/images",
  "layout_results": {
    "page_001": { /* layout data */ }
  },
  "output_cleaned_dir": "/data/cleaned",
  "output_illustrations_dir": "/data/illustrations"
}
```

### Implementation Requirements

Your alternative implementation must:

- Mask illustration regions (typically with white)
- Extract and save individual illustrations
- Optionally enhance images for OCR (contrast, sharpness)
- Maintain image dimensions and quality
- Support batch processing

### Example Alternative Stack

- **ImageMagick**: Command-line image processing
- **Pillow + scikit-image**: Advanced image manipulation
- **OpenCV**: Computer vision operations
- **Cloud services**: AWS Rekognition, Google Vision
- **Custom processing**: Domain-specific enhancements

---

## OCR Engine Service

**Base URL:** `http://ocr-engine:8004`

Extracts text from images using OCR.

### POST /extract

Extract text from a single image.

**Request:**
```json
{
  "image_path": "/data/cleaned/page_001.png",
  "languages": ["kat", "eng"],
  "confidence_threshold": 60.0
}
```

**Response:**
```json
{
  "success": true,
  "page_path": "/data/cleaned/page_001.png",
  "text": "Extracted text content here...",
  "confidence": 87.5,
  "word_count": 245,
  "char_count": 1532,
  "line_data": [
    {
      "text": "First line of text",
      "confidence": 89.2,
      "bbox": [50, 100, 500, 120]
    }
  ]
}
```

### POST /extract/batch

Extract text from multiple images.

**Request:**
```json
{
  "image_dir": "/data/cleaned",
  "output_dir": "/data/text",
  "languages": ["kat", "eng"],
  "confidence_threshold": 60.0,
  "combine": true
}
```

**Response:**
```json
{
  "success": true,
  "pages_processed": 100,
  "total_words": 24500,
  "results": {
    "page_001": { /* OCRResponse */ }
  },
  "combined_text_path": "/data/text/book_full.txt"
}
```

### Implementation Requirements

Your alternative implementation must:

- Support multiple languages (especially Georgian/ქართული)
- Return extracted text as UTF-8 string
- Provide confidence scores
- Save individual page text files
- Optionally combine all text into one file
- Support batch processing

### Language Codes

Common language codes:
- `kat` - Georgian (ქართული)
- `eng` - English
- `rus` - Russian
- `fra` - French
- `deu` - German

### Example Alternative Stack

- **Google Cloud Vision API**: Cloud-based OCR
- **AWS Textract**: Amazon OCR service
- **Azure Computer Vision**: Microsoft OCR
- **EasyOCR**: Python OCR library
- **Custom model**: Trained on specific fonts/scripts
- **ABBYY FineReader**: Commercial OCR

---

## Illustration Interpreter Service

**Base URL:** `http://illustration-interpreter:8005`

Interprets illustrations using vision-language AI models.

### POST /interpret

Interpret a single illustration.

**Request:**
```json
{
  "image_path": "/data/illustrations/page_001_illus_01.png",
  "context": "Georgian history textbook about medieval castles"
}
```

**Response:**
```json
{
  "success": true,
  "image_path": "/data/illustrations/page_001_illus_01.png",
  "caption": "14th century Georgian fortress in the mountains",
  "description": "The illustration shows a well-preserved medieval stone fortress perched on a mountainside. The fortification features characteristic Georgian architecture with distinctive towers and defensive walls.",
  "tags": ["architecture", "medieval", "fortress", "Georgia", "history"],
  "educational_value": "Demonstrates typical defensive architecture of medieval Georgia, showing how geography influenced fortress construction.",
  "related_concepts": ["medieval architecture", "Georgian history", "defensive structures", "mountain fortifications"]
}
```

### POST /interpret/batch

Interpret multiple illustrations.

**Request:**
```json
{
  "illustration_dir": "/data/illustrations",
  "context": "Educational textbook about Georgian history"
}
```

**Response:**
```json
{
  "success": true,
  "illustrations_interpreted": 25,
  "results": {
    "page_001_illus_01": { /* InterpretationResponse */ }
  }
}
```

### Implementation Requirements

Your alternative implementation must:

- Analyze image content
- Generate meaningful captions (1-2 sentences)
- Provide detailed descriptions (1 paragraph)
- Extract relevant tags/keywords
- Explain educational value
- Identify related concepts
- Support batch processing

### Example Alternative Stack

- **OpenAI GPT-4 Vision**: Current default
- **Anthropic Claude**: Alternative vision model
- **Google Gemini**: Google's vision-language model
- **Azure AI Vision**: Microsoft's service
- **BLIP-2**: Open-source vision-language model
- **LLaVA**: Open-source alternative
- **Custom model**: Fine-tuned on educational content

---

## Pipeline Orchestrator Service

**Base URL:** `http://orchestrator:8000`

Coordinates all services to execute the complete pipeline.

### POST /pipeline

Run the complete pipeline.

**Request:**
```json
{
  "book_url": "https://example.com/book",
  "book_title": "Georgian History Textbook",
  "skip_retrieval": false,
  "skip_interpretation": false,
  "config_overrides": {
    "ocr_languages": ["kat", "eng"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "summary": {
    "images_retrieved": 100,
    "pages_analyzed": 100,
    "images_processed": 100,
    "illustrations_extracted": 25,
    "pages_ocr": 100,
    "total_words": 24500,
    "illustrations_interpreted": 25
  },
  "errors": []
}
```

### POST /pipeline/step

Run a specific pipeline step.

**Request:**
```json
{
  "step_name": "ocr",
  "parameters": {
    "image_dir": "/data/cleaned",
    "output_dir": "/data/text",
    "languages": ["kat", "eng"]
  }
}
```

**Response:**
Returns the response from the specific service endpoint.

---

## Creating Alternative Implementations

### Step 1: Choose Your Service to Replace

Identify which service you want to replace:

- **Retriever**: Different scraping method
- **Layout Analyzer**: Different ML model
- **Image Processor**: Different enhancement techniques
- **OCR Engine**: Different OCR provider
- **Interpreter**: Different AI model

### Step 2: Implement the API Contract

Your service must implement:

1. **Health check endpoint**: `GET /health`
2. **Processing endpoint(s)**: Follow the schema
3. **Error handling**: Return standard error format
4. **Logging**: For debugging

### Step 3: Test Your Service

```bash
# Test health check
curl http://localhost:8004/health

# Test main endpoint
curl -X POST http://localhost:8004/extract \
  -H "Content-Type: application/json" \
  -d '{
    "image_path": "/data/test.png",
    "languages": ["eng"],
    "confidence_threshold": 60.0
  }'
```

### Step 4: Update Docker Compose

Replace the service in `docker-compose.yml`:

```yaml
services:
  ocr-engine:
    image: your-custom-ocr:latest
    ports:
      - "8004:8004"
    volumes:
      - shared-data:/data
    environment:
      - YOUR_CUSTOM_CONFIG=value
```

### Step 5: Deploy and Test

```bash
docker-compose --profile multi-container up
```

---

## Testing Your Implementation

### 1. Unit Tests

Test individual endpoints:

```python
import requests

def test_ocr_extract():
    response = requests.post(
        "http://localhost:8004/extract",
        json={
            "image_path": "/data/test.png",
            "languages": ["eng"],
            "confidence_threshold": 60.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert len(data["text"]) > 0
```

### 2. Integration Tests

Test service interaction:

```bash
# Run orchestrator test
curl -X POST http://localhost:8000/pipeline/step \
  -H "Content-Type: application/json" \
  -d '{
    "step_name": "ocr",
    "parameters": {"image_dir": "/data/test"}
  }'
```

### 3. Performance Tests

Measure throughput and latency:

```bash
# Use Apache Bench
ab -n 100 -c 10 -p request.json \
  -T application/json \
  http://localhost:8004/extract
```

### 4. Compatibility Tests

Ensure your service works with orchestrator:

```bash
# Full pipeline test
docker-compose --profile multi-container up
# Monitor logs for errors
docker-compose logs -f
```

---

## Example: Creating a Custom OCR Service

### Using Google Cloud Vision

```python
# custom_ocr_service.py
from fastapi import FastAPI
from google.cloud import vision
import os

app = FastAPI()

client = vision.ImageAnnotatorClient()

@app.get("/health")
def health():
    return {"service_name": "custom-ocr", "status": "healthy"}

@app.post("/extract")
def extract(request: OCRRequest):
    # Read image
    with open(request.image_path, 'rb') as f:
        content = f.read()

    image = vision.Image(content=content)

    # Perform OCR
    response = client.text_detection(image=image)
    texts = response.text_annotations

    if texts:
        extracted_text = texts[0].description
    else:
        extracted_text = ""

    return OCRResponse(
        success=True,
        page_path=request.image_path,
        text=extracted_text,
        confidence=85.0,  # Google doesn't provide this
        word_count=len(extracted_text.split()),
        char_count=len(extracted_text)
    )
```

### Docker file for Custom Service

```dockerfile
FROM python:3.9-slim

WORKDIR /app

RUN pip install fastapi uvicorn google-cloud-vision

COPY custom_ocr_service.py .
COPY credentials.json /app/

ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json

CMD ["uvicorn", "custom_ocr_service:app", "--host", "0.0.0.0", "--port", "8004"]
```

### Update docker-compose.yml

```yaml
services:
  ocr-engine:
    build:
      context: ./custom-services/ocr
      dockerfile: Dockerfile
    image: custom-ocr:latest
    container_name: ocr-engine
    ports:
      - "8004:8004"
    volumes:
      - shared-data:/data
      - ./credentials.json:/app/credentials.json
```

---

## OpenAPI Documentation

Each service automatically generates interactive API documentation:

- **Swagger UI**: `http://service:port/docs`
- **ReDoc**: `http://service:port/redoc`
- **OpenAPI JSON**: `http://service:port/openapi.json`

### Example

```
http://localhost:8004/docs  # OCR service Swagger UI
http://localhost:8002/docs  # Layout analyzer Swagger UI
```

---

## Support and Resources

- **Full source code**: See `src/api/` directory
- **Schema definitions**: `src/api/schemas.py`
- **Example implementations**: Each service in `src/api/*_service.py`
- **Docker configuration**: `docker-compose.yml`

For questions or issues with implementing custom services, please open a GitHub issue.

---

**This API specification is versioned at 0.1.0 and may evolve based on community feedback.**
