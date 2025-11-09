#!/bin/bash
# Run script for Docker containers

set -e

echo "========================================"
echo "Textbook Parser - Docker Run Script"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Parse arguments
MODE=${1:-single}
shift || true

# Check if .env exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. API keys will not be available."
    echo "Copy .env.example to .env and add your API keys."
    echo ""
fi

if [ "$MODE" == "single" ]; then
    print_info "Running single container..."

    docker run --rm -it \
        -v "$(pwd)/output:/app/output" \
        -v "$(pwd)/config:/app/config" \
        -v "$(pwd)/.env:/app/.env" \
        textbook-parser:latest \
        python main.py "$@"

elif [ "$MODE" == "gpu" ]; then
    print_info "Running GPU-enabled container..."

    docker run --rm -it \
        --gpus all \
        -v "$(pwd)/output:/app/output" \
        -v "$(pwd)/config:/app/config" \
        -v "$(pwd)/.env:/app/.env" \
        textbook-parser:gpu \
        python main.py "$@"

elif [ "$MODE" == "multi" ]; then
    print_info "Running multi-container setup..."

    docker-compose --profile multi-container up "$@"

elif [ "$MODE" == "bash" ]; then
    print_info "Opening bash shell in container..."

    docker run --rm -it \
        -v "$(pwd)/output:/app/output" \
        -v "$(pwd)/config:/app/config" \
        -v "$(pwd)/.env:/app/.env" \
        --entrypoint /bin/bash \
        textbook-parser:latest

else
    echo "Usage: $0 [single|gpu|multi|bash] [args...]"
    echo ""
    echo "Modes:"
    echo "  single  - Run single container (default)"
    echo "  gpu     - Run GPU-enabled container"
    echo "  multi   - Run multi-container setup"
    echo "  bash    - Open bash shell in container"
    echo ""
    echo "Examples:"
    echo "  $0 single --url 'https://example.com/book' --title 'My Book'"
    echo "  $0 single --config config/example_georgian_book.yaml"
    echo "  $0 multi"
    echo "  $0 bash"
    exit 1
fi
