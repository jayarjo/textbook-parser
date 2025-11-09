# Makefile Quick Reference

This guide shows you how to use the Makefile for common operations.

## 📋 View All Commands

```bash
make help
```

This shows all available commands organized by category.

## 🚀 Quick Start

### Start Everything in One Command

```bash
make quick-start
```

This will:
1. Build all multi-container services
2. Start them in detached mode
3. Check health of all services
4. Show you the URLs

### Build & Start Manually

```bash
# Build all services
make build-multi

# Start services (interactive logs)
make up

# OR start in background
make up-d

# Check health
make health
```

## 🔨 Common Workflows

### 1. Development Workflow

```bash
# First time setup
make build-multi         # Build containers
make up-d               # Start services
make health             # Verify they're running
make docs               # Open API documentation

# Make code changes, then rebuild specific service
docker compose build ocr-engine
docker compose restart ocr-engine

# View logs
make logs-ocr

# Stop when done
make down
```

### 2. Process a Book

```bash
# Make sure services are running
make up-d

# Process a book
make process URL="https://example.com/book" TITLE="My Book"

# Or with existing images
make process-skip-retrieval TITLE="My Book"

# View the results
make shell-orchestrator
# Inside container:
ls /data/text/
cat /data/text/book_full.txt
```

### 3. Test Individual Services

```bash
# Start services
make up-d

# Check health of all services
make health

# Test OCR specifically
make test-ocr

# View OCR logs
make logs-ocr

# Open shell in OCR container for debugging
make shell-ocr
```

### 4. Scale for Production

```bash
# Start services
make up-d

# Scale OCR to 5 instances (for heavy load)
make scale-ocr N=5

# Scale interpreter to 3 instances
make scale-interpreter N=3

# Check resource usage
make stats

# View all running containers
make ps
```

## 📚 Command Categories

### Docker Build

```bash
make build-single       # Build single all-in-one container
make build-multi        # Build multi-container services
make build-gpu          # Build GPU-enabled container
make build-all          # Build everything
make rebuild            # Rebuild from scratch (no cache)
```

### Docker Run

```bash
make up                 # Start services (interactive)
make up-d               # Start services (detached/background)
make down               # Stop all services
make restart            # Restart all services
```

### Service Management

```bash
make scale-ocr N=3              # Scale OCR to 3 instances
make scale-interpreter N=2      # Scale interpreter to 2 instances
make ps                         # Show running containers
make stats                      # Show resource usage
```

### Logs & Debugging

```bash
# View logs
make logs                       # All services
make logs-orchestrator          # Orchestrator only
make logs-ocr                   # OCR only
make logs-retriever             # Retriever only
make logs-layout                # Layout analyzer only
make logs-processor             # Image processor only
make logs-interpreter           # Interpreter only

# Open shell in containers
make shell-orchestrator         # Orchestrator container
make shell-ocr                  # OCR container
make shell-retriever            # Retriever container
```

### Testing & Health

```bash
make health             # Check health of all services
make test-ocr           # Test OCR service
make docs               # Open API documentation
```

### Cleanup

```bash
make clean              # Stop and remove containers
make clean-volumes      # Remove containers AND volumes (deletes data!)
make clean-images       # Remove all built images
make prune              # Remove unused Docker resources
make prune-all          # Aggressive cleanup (use with caution)
```

### Development

```bash
make install-deps       # Install Python dependencies locally
make format             # Format code with black
make lint               # Lint code with flake8
make type-check         # Type check with mypy
make test               # Run tests
```

### Information

```bash
make version            # Show version info
make status             # Show system status
make ports              # Show all service ports
```

## 🎯 Real-World Examples

### Example 1: Process a Georgian History Book

```bash
# Start services
make up-d

# Wait for services to be ready (check health)
make health

# Process the book
make process \
  URL="https://example.com/georgian-history-book" \
  TITLE="Georgian Medieval History"

# View logs to monitor progress
make logs-orchestrator

# When done, check the results
make shell-orchestrator
ls /data/text/
cat /data/text/book_full.txt
cat /data/notebook_export/notebook_source.md
```

### Example 2: Develop Custom OCR Service

```bash
# Start all services except OCR
make up-d

# Stop the default OCR service
docker compose stop ocr-engine

# Build and run your custom OCR
cd custom-services/my-ocr
docker build -t my-custom-ocr .
docker run -d --name ocr-engine \
  --network textbook-parser_parser-network \
  -v textbook-parser_shared-data:/data \
  -p 8004:8004 \
  my-custom-ocr

# Test it
make test-ocr

# View logs
docker logs -f ocr-engine

# When working, update docker compose.yml to use it permanently
```

### Example 3: Batch Process Multiple Books

```bash
# Start services with scaled OCR
make up-d
make scale-ocr N=5

# Process first book
make process URL="https://example.com/book1" TITLE="Book 1"

# Process second book (while first is running)
make process URL="https://example.com/book2" TITLE="Book 2"

# Monitor all services
make stats

# View logs
make logs
```

### Example 4: Debug OCR Issues

```bash
# Start services
make up-d

# Check OCR health
curl http://localhost:8004/health

# View OCR logs
make logs-ocr

# Open shell in OCR container
make shell-ocr

# Inside container, test Tesseract
tesseract --version
tesseract --list-langs

# Test OCR on a sample image
cd /data/cleaned
tesseract page_001.png output -l kat+eng
cat output.txt

# Exit and check API
exit
curl -X POST http://localhost:8004/extract \
  -H "Content-Type: application/json" \
  -d '{"image_path": "/data/cleaned/page_001.png", "languages": ["kat", "eng"]}'
```

### Example 5: Production Deployment

```bash
# Build everything
make build-multi

# Start with production scaling
make up-d
make scale-ocr N=10
make scale-interpreter N=3

# Monitor resources
make stats

# Check health regularly
watch -n 5 'make health'

# View aggregated logs
make logs > pipeline.log &

# Process books via API
for i in {1..100}; do
  make process URL="https://example.com/book$i" TITLE="Book $i"
done
```

## 💡 Tips & Tricks

### Tip 1: Run Commands in Background

```bash
# Start in background
make up-d

# View logs anytime
make logs

# Check status
make ps
```

### Tip 2: Selective Service Restart

```bash
# Restart just one service after code changes
docker compose restart ocr-engine

# Or rebuild and restart
docker compose build ocr-engine
docker compose restart ocr-engine
```

### Tip 3: Quick Health Check Loop

```bash
# Continuously monitor health
watch -n 10 'make health'
```

### Tip 4: Export Logs to File

```bash
# Export all logs
make logs > pipeline-logs.txt

# Export specific service logs
make logs-ocr > ocr-logs.txt
```

### Tip 5: Clean Start

```bash
# Complete fresh start
make down
make clean
make build-multi
make up-d
make health
```

## 🔧 Troubleshooting

### Problem: `make: command not found`

**Solution**: Install make:

```bash
# Ubuntu/Debian
sudo apt-get install make

# macOS
xcode-select --install

# Already installed on most Linux systems
```

### Problem: Services won't start

```bash
# Check logs
make logs

# Rebuild from scratch
make rebuild
make up-d

# Check for port conflicts
make ports
netstat -tulpn | grep -E '800[0-5]'
```

### Problem: Health check fails

```bash
# Wait a bit for services to initialize
sleep 10
make health

# Check individual service
docker compose logs ocr-engine

# Restart problematic service
docker compose restart ocr-engine
```

### Problem: Out of disk space

```bash
# Remove unused resources
make prune

# More aggressive cleanup
make clean-images
make prune-all
```

## 📖 Related Documentation

- **[API.md](API.md)** - Complete API reference
- **[DOCKER.md](DOCKER.md)** - Docker deployment guide
- **[QUICKSTART_API.md](QUICKSTART_API.md)** - API quick start
- **[README.md](README.md)** - Main documentation

## 🎓 Learning Path

1. **Start here**: `make help`
2. **Quick test**: `make quick-start`
3. **Process a book**: `make process URL="..." TITLE="..."`
4. **Explore APIs**: `make docs`
5. **Debug issues**: `make logs-<service>`
6. **Scale up**: `make scale-ocr N=5`

---

**Pro Tip**: Type `make` followed by Tab twice to see all available commands (if your shell supports it).
