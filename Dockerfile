# Multi-stage Dockerfile for Textbook Parser Pipeline
# Optimized for size and build speed

# Stage 1: Base image with system dependencies
FROM python:3.9-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-kat \
    tesseract-ocr-eng \
    tesseract-ocr-rus \
    libtesseract-dev \
    libgl1 \
    libglib2.0-0 \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Stage 2: Python dependencies builder
FROM base AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies with optimizations
# First install torch separately (required by detectron2 during build)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch==2.1.2 torchvision==0.16.2

# Then install the rest of the requirements
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and browsers
RUN playwright install-deps chromium && \
    playwright install chromium

# Stage 3: Runtime image
FROM base AS runtime

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy application code
COPY . /app

# Create output directory
RUN mkdir -p /app/output

# Set working directory
WORKDIR /app

# Default command
CMD ["python", "main.py", "--help"]

# Stage 4: GPU-enabled version (optional)
FROM runtime AS gpu

# Install CUDA dependencies (if needed for GPU acceleration)
RUN apt-get update && apt-get install -y \
    nvidia-cuda-toolkit \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch with CUDA support
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cu118
