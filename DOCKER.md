# Docker Deployment Guide

Complete guide for running the Textbook Parser pipeline using Docker.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Container Options](#container-options)
3. [Single Container Setup](#single-container-setup)
4. [Multi-Container Setup](#multi-container-setup)
5. [GPU Support](#gpu-support)
6. [Configuration](#configuration)
7. [Volume Mounts](#volume-mounts)
8. [Troubleshooting](#troubleshooting)

## Quick Start

### Build and Run (Single Container)

```bash
# Build the container
./docker-build.sh single

# Run with a book URL
./docker-run.sh single --url "https://example.com/book" --title "My Book"

# Or use a config file
./docker-run.sh single --config config/example_georgian_book.yaml
```

## Container Options

We provide **three deployment options**:

### 1. Single Container (Recommended for Most Users)
- **Best for**: Simple usage, testing, most books
- **Pros**: Easy to use, single command, no orchestration needed
- **Cons**: Larger image (~3-4 GB), all dependencies even if not used
- **Use when**: You want simplicity and ease of use

### 2. Multi-Container Setup
- **Best for**: Production, scaling, processing multiple books
- **Pros**: Smaller individual images, can scale services independently, better resource isolation
- **Cons**: More complex setup, requires docker compose
- **Use when**: You need to process many books or scale specific steps

### 3. GPU-Enabled Container
- **Best for**: Faster layout analysis with GPU acceleration
- **Pros**: Significantly faster for layout analysis
- **Cons**: Requires NVIDIA GPU and nvidia-docker
- **Use when**: You have a GPU and process many pages

## Single Container Setup

### Build

```bash
# Build the container
./docker-build.sh single

# Or manually
docker build -t textbook-parser:latest --target runtime -f Dockerfile .
```

### Run Examples

```bash
# Process a book from URL
./docker-run.sh single --url "https://example.com/book" --title "Georgian History"

# Use a configuration file
./docker-run.sh single --config config/example_georgian_book.yaml

# Run specific step only
./docker-run.sh single --config config/default_config.yaml --step ocr --skip-retrieval

# Enable verbose logging
./docker-run.sh single --url "https://example.com/book" -v

# Open bash shell for debugging
./docker-run.sh bash
```

### Manual Docker Run

```bash
docker run --rm -it \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/.env:/app/.env \
  textbook-parser:latest \
  python main.py --url "https://example.com/book"
```

## Multi-Container Setup

### Architecture

The multi-container setup splits the pipeline into separate services:

- **Retriever**: Image downloading (Playwright)
- **Layout Analyzer**: Document layout detection (LayoutParser + Detectron2)
- **Image Processor**: Illustration masking and enhancement
- **OCR Engine**: Text extraction (Tesseract + PaddleOCR)
- **Interpreter**: Illustration understanding (GPT-4V/Claude/Gemini)
- **Orchestrator**: Coordinates all services

### Build

```bash
# Build all service containers
./docker-build.sh multi

# Or manually
docker compose build
```

### Run

```bash
# Run all services
./docker-run.sh multi

# Or manually
docker compose --profile multi-container up
```

### Run in Background

```bash
docker compose --profile multi-container up -d

# View logs
docker compose logs -f

# Stop services
docker compose --profile multi-container down
```

### Scale Individual Services

```bash
# Scale OCR engine to 3 instances
docker compose --profile multi-container up --scale ocr-engine=3
```

## GPU Support

### Prerequisites

1. **NVIDIA GPU** with CUDA support
2. **nvidia-docker** installed ([installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html))

### Build GPU Container

```bash
./docker-build.sh gpu

# Or manually
docker build -t textbook-parser:gpu --target gpu -f Dockerfile .
```

### Run with GPU

```bash
./docker-run.sh gpu --config config/example_georgian_book.yaml

# Or manually
docker run --rm -it \
  --gpus all \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/.env:/app/.env \
  textbook-parser:gpu \
  python main.py --config config/example_georgian_book.yaml
```

### Verify GPU Access

```bash
docker run --rm --gpus all textbook-parser:gpu python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

## Configuration

### Environment Variables

Create a `.env` file with your API keys:

```bash
cp .env.example .env
# Edit .env and add your keys
```

The `.env` file is automatically mounted in the container.

### Configuration Files

Configuration files in `config/` are mounted and accessible in the container:

```yaml
# config/my_book.yaml
book_url: "https://example.com/my-book"
book_title: "My Custom Book"
output_dir: "/app/output"

ocr:
  engine: "tesseract"
  languages: ["kat", "eng"]
```

### Using Configuration

```bash
./docker-run.sh single --config config/my_book.yaml
```

## Volume Mounts

The following directories are mounted by default:

| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `./output` | `/app/output` | Pipeline output files |
| `./config` | `/app/config` | Configuration files |
| `./.env` | `/app/.env` | API keys and secrets |

### Custom Volume Mounts

```bash
docker run --rm -it \
  -v /path/to/custom/output:/app/output \
  -v /path/to/custom/config:/app/config \
  textbook-parser:latest \
  python main.py --config /app/config/my_config.yaml
```

## Image Sizes

Approximate sizes for different container variants:

| Container | Size | Build Time |
|-----------|------|------------|
| Single (CPU) | ~3.5 GB | 5-10 min |
| GPU | ~5.0 GB | 10-15 min |
| Retriever | ~800 MB | 2-3 min |
| Layout Analyzer | ~2.0 GB | 5-8 min |
| Image Processor | ~400 MB | 1-2 min |
| OCR Engine | ~1.2 GB | 3-5 min |
| Interpreter | ~300 MB | 1-2 min |

## Docker Compose Profiles

We use profiles to avoid running all containers by default:

```bash
# Run single container (default)
docker compose up

# Run multi-container setup
docker compose --profile multi-container up

# Run specific services
docker compose --profile multi-container up retriever ocr-engine
```

## Performance Optimization

### Build Cache

Use BuildKit for faster builds:

```bash
DOCKER_BUILDKIT=1 docker build -t textbook-parser:latest -f Dockerfile .
```

### Multi-Stage Builds

Our Dockerfile uses multi-stage builds to minimize final image size:

1. **Base**: System dependencies
2. **Builder**: Python dependencies compilation
3. **Runtime**: Final minimal image
4. **GPU**: GPU-enabled variant

### Resource Limits

Limit container resources:

```bash
docker run --rm -it \
  --memory="4g" \
  --cpus="2.0" \
  -v $(pwd)/output:/app/output \
  textbook-parser:latest \
  python main.py --config config/default_config.yaml
```

## Troubleshooting

### Issue: Container build fails with "out of memory"

**Solution**: Increase Docker memory limit in Docker Desktop settings or use a smaller base image.

### Issue: Playwright browsers not installing

**Solution**: Ensure you're using the correct Dockerfile and Playwright version. Try:

```bash
docker run --rm -it textbook-parser:latest playwright install --force chromium
```

### Issue: Permission denied for output files

**Solution**: The container runs as user `parser` (UID 1000). Ensure output directory has correct permissions:

```bash
chmod 755 output
```

Or run container as root (not recommended):

```bash
docker run --rm -it --user root ...
```

### Issue: GPU not detected in container

**Solution**: Verify nvidia-docker is installed and working:

```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu20.04 nvidia-smi
```

### Issue: Network errors when retrieving images

**Solution**: If you're behind a proxy, configure Docker to use it:

```bash
docker run --rm -it \
  -e HTTP_PROXY=http://proxy.example.com:8080 \
  -e HTTPS_PROXY=http://proxy.example.com:8080 \
  textbook-parser:latest \
  python main.py --url "https://example.com/book"
```

### Debugging

Open a shell in the container:

```bash
# Interactive bash
./docker-run.sh bash

# Or manually
docker run --rm -it \
  -v $(pwd)/output:/app/output \
  --entrypoint /bin/bash \
  textbook-parser:latest
```

Check logs:

```bash
# For single container
docker logs <container-id>

# For multi-container
docker compose logs -f
docker compose logs retriever
docker compose logs ocr-engine
```

## Best Practices

1. **Use .dockerignore**: Exclude unnecessary files from build context
2. **Use specific tags**: Don't rely on `:latest` in production
3. **Scan for vulnerabilities**: Use `docker scan textbook-parser:latest`
4. **Keep images updated**: Rebuild regularly for security patches
5. **Use volumes for data**: Never store important data in containers
6. **Clean up**: Regularly prune unused images and containers

## Cleanup

Remove unused Docker resources:

```bash
# Remove all containers
docker compose down

# Remove images
docker rmi textbook-parser:latest
docker rmi textbook-parser:gpu

# Remove all multi-container images
docker compose down --rmi all

# Prune system (be careful!)
docker system prune -a
```

## Production Deployment

### Using Docker Swarm

```bash
docker swarm init
docker stack deploy -c docker compose.yml textbook-parser
```

### Using Kubernetes

Convert docker compose to Kubernetes manifests:

```bash
kompose convert -f docker compose.yml
kubectl apply -f .
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [nvidia-docker Documentation](https://github.com/NVIDIA/nvidia-docker)
- [Kubernetes Documentation](https://kubernetes.io/docs/)

## Support

For Docker-specific issues:

1. Check this guide first
2. Review Docker logs
3. Check existing GitHub issues
4. Create a new issue with:
   - Docker version (`docker --version`)
   - docker compose version
   - Full error message
   - Steps to reproduce
