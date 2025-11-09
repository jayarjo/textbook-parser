# Multi-Container API Setup - Quick Start Guide

This guide shows you how to use the unified REST API architecture to process textbooks with maximum flexibility.

## 🚀 Start All Services

```bash
# Build all service containers
./docker-build.sh multi

# Start all services
docker compose --profile multi-container up
```

**Services will start on:**
- Orchestrator: http://localhost:8000
- Retriever: http://localhost:8001
- Layout Analyzer: http://localhost:8002
- Image Processor: http://localhost:8003
- OCR Engine: http://localhost:8004
- Interpreter: http://localhost:8005

## 📖 Interactive API Documentation

Each service has automatic Swagger UI documentation:

```bash
# Open in your browser
http://localhost:8000/docs  # Orchestrator
http://localhost:8001/docs  # Retriever
http://localhost:8002/docs  # Layout Analyzer
http://localhost:8003/docs  # Image Processor
http://localhost:8004/docs  # OCR Engine
http://localhost:8005/docs  # Interpreter
```

## 🔍 Check Services Health

```bash
# Check all services
curl http://localhost:8000/health

# Check individual service
curl http://localhost:8004/health
```

## 📚 Process a Complete Book

### Option 1: Use the Orchestrator (Easiest)

```bash
curl -X POST http://localhost:8000/pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "book_url": "https://example.com/book",
    "book_title": "Georgian History",
    "skip_retrieval": false,
    "skip_interpretation": false
  }'
```

### Option 2: Call Services Individually

#### Step 1: Retrieve Images

```bash
curl -X POST http://localhost:8001/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/book",
    "strategy": "intercept",
    "max_pages": 100,
    "output_dir": "/data/images"
  }'
```

#### Step 2: Analyze Layouts

```bash
curl -X POST http://localhost:8002/analyze/batch \
  -H "Content-Type: application/json" \
  -d '{
    "image_dir": "/data/images",
    "confidence_threshold": 0.5
  }'
```

#### Step 3: Process Images

```bash
curl -X POST http://localhost:8003/process/batch \
  -H "Content-Type: application/json" \
  -d '{
    "image_dir": "/data/images",
    "layout_results": {...},
    "output_cleaned_dir": "/data/cleaned",
    "output_illustrations_dir": "/data/illustrations"
  }'
```

#### Step 4: Extract Text

```bash
curl -X POST http://localhost:8004/extract/batch \
  -H "Content-Type: application/json" \
  -d '{
    "image_dir": "/data/cleaned",
    "output_dir": "/data/text",
    "languages": ["kat", "eng"],
    "confidence_threshold": 60.0,
    "combine": true
  }'
```

#### Step 5: Interpret Illustrations

```bash
curl -X POST http://localhost:8005/interpret/batch \
  -H "Content-Type: application/json" \
  -d '{
    "illustration_dir": "/data/illustrations",
    "context": "Educational Georgian history textbook"
  }'
```

## 🔄 Replace a Service

### Example: Use Google Cloud Vision Instead of Tesseract

1. **Create your custom OCR service** (Python example):

```python
# custom_ocr.py
from fastapi import FastAPI
from google.cloud import vision

app = FastAPI(title="Google Cloud Vision OCR")

@app.get("/health")
def health():
    return {"service_name": "google-ocr", "status": "healthy"}

@app.post("/extract")
def extract(request: dict):
    # Your Google Vision implementation
    client = vision.ImageAnnotatorClient()
    # ... implementation ...
    return {
        "success": True,
        "text": extracted_text,
        "confidence": 90.0,
        # ... other fields
    }

@app.post("/extract/batch")
def extract_batch(request: dict):
    # Batch implementation
    pass
```

2. **Create Dockerfile**:

```dockerfile
FROM python:3.9-slim
WORKDIR /app
RUN pip install fastapi uvicorn google-cloud-vision
COPY custom_ocr.py .
CMD ["uvicorn", "custom_ocr:app", "--host", "0.0.0.0", "--port", "8004"]
```

3. **Update docker compose.yml**:

```yaml
services:
  ocr-engine:
    build: ./custom-services/google-ocr
    image: custom-google-ocr:latest
    ports:
      - "8004:8004"
    volumes:
      - shared-data:/data
    environment:
      - GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
```

4. **Rebuild and restart**:

```bash
docker compose --profile multi-container up --build ocr-engine
```

**That's it!** The orchestrator and other services will automatically use your custom OCR implementation because it follows the same API interface.

## 🔧 Scale Individual Services

```bash
# Scale OCR to handle more load
docker compose --profile multi-container up --scale ocr-engine=3

# Scale interpreter for many illustrations
docker compose --profile multi-container up --scale interpreter=2
```

## 📊 Monitor Services

```bash
# View all logs
docker compose logs -f

# View specific service logs
docker compose logs -f ocr-engine

# Check service status
docker compose ps
```

## 🧪 Test Individual Service

```bash
# Test OCR with a sample image
curl -X POST http://localhost:8004/extract \
  -H "Content-Type: application/json" \
  -d '{
    "image_path": "/data/test.png",
    "languages": ["kat", "eng"],
    "confidence_threshold": 60.0
  }'

# Pretty print the response
curl -X POST http://localhost:8004/extract \
  -H "Content-Type: application/json" \
  -d '{"image_path": "/data/test.png", "languages": ["kat"]}' \
  | python -m json.tool
```

## 🐛 Debug a Service

```bash
# Enter service container
docker exec -it ocr-engine /bin/bash

# Check service health from inside
curl http://localhost:8004/health

# View Python errors
docker compose logs ocr-engine | grep -i error
```

## 📁 Access Processed Files

Processed files are in the shared volume:

```bash
# Enter any container to access /data
docker exec -it orchestrator /bin/bash
cd /data

# Directory structure:
# /data/images/          - Retrieved images
# /data/cleaned/         - Images with illustrations masked
# /data/text/            - Extracted text
# /data/illustrations/   - Cropped illustrations
# /data/metadata/        - Processing metadata
```

Or mount the volume to your host:

```yaml
volumes:
  shared-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /host/path/to/output
```

## 🎯 Common Use Cases

### 1. Process Only OCR (Skip Retrieval)

```bash
curl -X POST http://localhost:8000/pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "skip_retrieval": true,
    "book_title": "My Book"
  }'
```

### 2. Process Without Illustration Interpretation

```bash
curl -X POST http://localhost:8000/pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "book_url": "https://example.com/book",
    "skip_interpretation": true
  }'
```

### 3. Run a Single Step

```bash
curl -X POST http://localhost:8000/pipeline/step \
  -H "Content-Type: application/json" \
  -d '{
    "step_name": "ocr",
    "parameters": {
      "image_dir": "/data/cleaned",
      "output_dir": "/data/text"
    }
  }'
```

## 🛠️ Alternative Technology Stacks

You can replace services with completely different technology:

| Service | Alternative Options |
|---------|---------------------|
| **Retriever** | Node.js + Puppeteer, Scrapy, Custom scraper |
| **Layout Analyzer** | Azure Computer Vision, AWS Textract, Custom YOLO |
| **Image Processor** | ImageMagick, Custom OpenCV pipeline |
| **OCR** | Google Vision, AWS Textract, Azure OCR, ABBYY |
| **Interpreter** | Claude API, Gemini, Custom VLM, LLaVA |

As long as your service implements the API contract defined in `API.md`, it will work seamlessly with the pipeline.

## 📖 Full Documentation

- **API Reference**: See [API.md](API.md)
- **Docker Guide**: See [DOCKER.md](DOCKER.md)
- **Installation**: See [INSTALL.md](INSTALL.md)
- **Main README**: See [README.md](README.md)

## 🆘 Troubleshooting

### Services won't start

```bash
# Check logs
docker compose logs

# Rebuild from scratch
docker compose down
docker compose --profile multi-container build --no-cache
docker compose --profile multi-container up
```

### Service returns 500 error

```bash
# Check service logs
docker compose logs service-name

# Check if service is healthy
curl http://localhost:PORT/health
```

### Can't access shared data

```bash
# Check volume permissions
docker exec -it orchestrator ls -la /data

# Fix permissions if needed
docker exec -it --user root orchestrator chown -R parser:parser /data
```

## 🎉 Success!

You now have a fully functional microservices architecture for textbook processing where:

- ✅ Each service runs independently
- ✅ Services communicate via REST APIs
- ✅ Any service can be replaced with alternatives
- ✅ Services can be scaled independently
- ✅ Full API documentation available
- ✅ Easy testing and debugging

Happy textbook parsing! 🚀
