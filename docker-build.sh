#!/bin/bash
# Build script for Docker containers

set -e

echo "========================================"
echo "Textbook Parser - Docker Build Script"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Parse arguments
MODE=${1:-single}

if [ "$MODE" == "single" ]; then
    print_info "Building single all-in-one container..."

    docker build -t textbook-parser:latest \
        --target runtime \
        -f Dockerfile .

    print_success "Single container built successfully!"
    echo ""
    echo "To run:"
    echo "  docker run -v \$(pwd)/output:/app/output textbook-parser:latest python main.py --help"

elif [ "$MODE" == "gpu" ]; then
    print_info "Building GPU-enabled container..."

    docker build -t textbook-parser:gpu \
        --target gpu \
        -f Dockerfile .

    print_success "GPU container built successfully!"
    echo ""
    echo "To run:"
    echo "  docker run --gpus all -v \$(pwd)/output:/app/output textbook-parser:gpu python main.py --help"

elif [ "$MODE" == "multi" ]; then
    print_info "Building multi-container setup..."

    docker-compose build

    print_success "All service containers built successfully!"
    echo ""
    echo "To run:"
    echo "  docker-compose --profile multi-container up"

elif [ "$MODE" == "all" ]; then
    print_info "Building all container variants..."

    # Build single container
    print_info "Building single container..."
    docker build -t textbook-parser:latest \
        --target runtime \
        -f Dockerfile .
    print_success "Single container built"

    # Build GPU container
    print_info "Building GPU container..."
    docker build -t textbook-parser:gpu \
        --target gpu \
        -f Dockerfile .
    print_success "GPU container built"

    # Build multi-container setup
    print_info "Building multi-container setup..."
    docker-compose build
    print_success "Multi-container setup built"

    print_success "All containers built successfully!"

else
    print_error "Unknown mode: $MODE"
    echo ""
    echo "Usage: $0 [single|gpu|multi|all]"
    echo ""
    echo "Modes:"
    echo "  single  - Build single all-in-one container (default)"
    echo "  gpu     - Build GPU-enabled container"
    echo "  multi   - Build multi-container setup"
    echo "  all     - Build all variants"
    exit 1
fi

echo ""
print_success "Build complete!"
