# Makefile for Textbook Parser Pipeline
# Simplifies Docker operations and common tasks

.PHONY: help build-single build-multi build-gpu build-all up down logs clean test health

# Default target - show help
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

##@ General

help: ## Display this help message
	@echo "$(BLUE)Textbook Parser Pipeline - Makefile Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(YELLOW)<target>$(NC)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(BLUE)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(GREEN)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Docker Build

build-single: ## Build single all-in-one container
	@echo "$(YELLOW)Building single container...$(NC)"
	./docker-build.sh single
	@echo "$(GREEN)✓ Single container built$(NC)"

build-multi: ## Build all multi-container services
	@echo "$(YELLOW)Building multi-container services...$(NC)"
	./docker-build.sh multi
	@echo "$(GREEN)✓ All services built$(NC)"

build-gpu: ## Build GPU-enabled container
	@echo "$(YELLOW)Building GPU container...$(NC)"
	./docker-build.sh gpu
	@echo "$(GREEN)✓ GPU container built$(NC)"

build-all: ## Build all container variants (single, multi, gpu)
	@echo "$(YELLOW)Building all containers...$(NC)"
	./docker-build.sh all
	@echo "$(GREEN)✓ All containers built$(NC)"

rebuild: ## Rebuild all services from scratch (no cache)
	@echo "$(YELLOW)Rebuilding all services (no cache)...$(NC)"
	docker-compose build --no-cache
	@echo "$(GREEN)✓ Services rebuilt$(NC)"

##@ Docker Run

up: ## Start all multi-container services
	@echo "$(YELLOW)Starting all services...$(NC)"
	docker-compose --profile multi-container up

up-d: ## Start all services in detached mode
	@echo "$(YELLOW)Starting all services (detached)...$(NC)"
	docker-compose --profile multi-container up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@echo "Run 'make logs' to view logs"

down: ## Stop all services
	@echo "$(YELLOW)Stopping all services...$(NC)"
	docker-compose --profile multi-container down
	@echo "$(GREEN)✓ Services stopped$(NC)"

restart: ## Restart all services
	@echo "$(YELLOW)Restarting services...$(NC)"
	docker-compose --profile multi-container restart
	@echo "$(GREEN)✓ Services restarted$(NC)"

##@ Service Management

scale-ocr: ## Scale OCR service (usage: make scale-ocr N=3)
	@echo "$(YELLOW)Scaling OCR engine to $(N) instances...$(NC)"
	docker-compose --profile multi-container up -d --scale ocr-engine=$(N)

scale-interpreter: ## Scale interpreter service (usage: make scale-interpreter N=2)
	@echo "$(YELLOW)Scaling interpreter to $(N) instances...$(NC)"
	docker-compose --profile multi-container up -d --scale interpreter=$(N)

ps: ## Show running services
	@docker-compose ps

stats: ## Show resource usage statistics
	@docker stats

##@ Logs & Debugging

logs: ## View logs from all services
	docker-compose logs -f

logs-orchestrator: ## View orchestrator logs
	docker-compose logs -f orchestrator

logs-retriever: ## View retriever logs
	docker-compose logs -f retriever

logs-layout: ## View layout analyzer logs
	docker-compose logs -f layout-analyzer

logs-processor: ## View image processor logs
	docker-compose logs -f image-processor

logs-ocr: ## View OCR engine logs
	docker-compose logs -f ocr-engine

logs-interpreter: ## View interpreter logs
	docker-compose logs -f illustration-interpreter

shell-orchestrator: ## Open shell in orchestrator container
	docker exec -it orchestrator /bin/bash

shell-ocr: ## Open shell in OCR container
	docker exec -it ocr-engine /bin/bash

shell-retriever: ## Open shell in retriever container
	docker exec -it retriever /bin/bash

##@ Testing & Health

health: ## Check health of all services
	@echo "$(YELLOW)Checking service health...$(NC)"
	@echo ""
	@echo "$(BLUE)Orchestrator:$(NC)"
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "$(RED)✗ Not responding$(NC)"
	@echo ""
	@echo "$(BLUE)Retriever:$(NC)"
	@curl -s http://localhost:8001/health | python3 -m json.tool || echo "$(RED)✗ Not responding$(NC)"
	@echo ""
	@echo "$(BLUE)Layout Analyzer:$(NC)"
	@curl -s http://localhost:8002/health | python3 -m json.tool || echo "$(RED)✗ Not responding$(NC)"
	@echo ""
	@echo "$(BLUE)Image Processor:$(NC)"
	@curl -s http://localhost:8003/health | python3 -m json.tool || echo "$(RED)✗ Not responding$(NC)"
	@echo ""
	@echo "$(BLUE)OCR Engine:$(NC)"
	@curl -s http://localhost:8004/health | python3 -m json.tool || echo "$(RED)✗ Not responding$(NC)"
	@echo ""
	@echo "$(BLUE)Interpreter:$(NC)"
	@curl -s http://localhost:8005/health | python3 -m json.tool || echo "$(RED)✗ Not responding$(NC)"

test-ocr: ## Test OCR service with sample request
	@echo "$(YELLOW)Testing OCR service...$(NC)"
	@curl -X POST http://localhost:8004/health | python3 -m json.tool

docs: ## Open API documentation in browser
	@echo "$(YELLOW)Opening API documentation...$(NC)"
	@echo "Orchestrator: http://localhost:8000/docs"
	@echo "Retriever:    http://localhost:8001/docs"
	@echo "Layout:       http://localhost:8002/docs"
	@echo "Processor:    http://localhost:8003/docs"
	@echo "OCR:          http://localhost:8004/docs"
	@echo "Interpreter:  http://localhost:8005/docs"
	@command -v xdg-open >/dev/null 2>&1 && xdg-open http://localhost:8000/docs || \
	 command -v open >/dev/null 2>&1 && open http://localhost:8000/docs || \
	 echo "Please open http://localhost:8000/docs in your browser"

##@ Cleanup

clean: ## Stop services and remove containers
	@echo "$(YELLOW)Cleaning up containers...$(NC)"
	docker-compose --profile multi-container down
	@echo "$(GREEN)✓ Containers removed$(NC)"

clean-volumes: ## Remove containers and volumes (WARNING: deletes data)
	@echo "$(RED)WARNING: This will delete all data in volumes!$(NC)"
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose --profile multi-container down -v; \
		echo "$(GREEN)✓ Containers and volumes removed$(NC)"; \
	else \
		echo "Cancelled"; \
	fi

clean-images: ## Remove all built images
	@echo "$(YELLOW)Removing built images...$(NC)"
	docker-compose --profile multi-container down --rmi all
	@echo "$(GREEN)✓ Images removed$(NC)"

prune: ## Remove all unused Docker resources
	@echo "$(YELLOW)Pruning unused Docker resources...$(NC)"
	docker system prune -f
	@echo "$(GREEN)✓ Pruning complete$(NC)"

prune-all: ## Remove ALL unused Docker resources (WARNING: aggressive)
	@echo "$(RED)WARNING: This will remove all unused Docker resources!$(NC)"
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker system prune -a -f --volumes; \
		echo "$(GREEN)✓ Complete pruning finished$(NC)"; \
	else \
		echo "Cancelled"; \
	fi

##@ Development

install-deps: ## Install Python dependencies locally (for development)
	@echo "$(YELLOW)Installing Python dependencies...$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

format: ## Format Python code with black
	@echo "$(YELLOW)Formatting code...$(NC)"
	black src/
	@echo "$(GREEN)✓ Code formatted$(NC)"

lint: ## Lint Python code with flake8
	@echo "$(YELLOW)Linting code...$(NC)"
	flake8 src/ --max-line-length=100
	@echo "$(GREEN)✓ Linting complete$(NC)"

type-check: ## Type check with mypy
	@echo "$(YELLOW)Type checking...$(NC)"
	mypy src/
	@echo "$(GREEN)✓ Type checking complete$(NC)"

test: ## Run tests
	@echo "$(YELLOW)Running tests...$(NC)"
	pytest tests/
	@echo "$(GREEN)✓ Tests complete$(NC)"

##@ Quick Actions

quick-start: build-multi up-d health ## Build, start, and verify all services
	@echo "$(GREEN)✓ Pipeline ready! Services running at:$(NC)"
	@echo "  Orchestrator: http://localhost:8000/docs"
	@echo "  Use 'make logs' to view logs"
	@echo "  Use 'make health' to check status"

process: ## Process a book (usage: make process URL="https://..." TITLE="Book Title")
	@echo "$(YELLOW)Processing book: $(TITLE)$(NC)"
	@curl -X POST http://localhost:8000/pipeline \
		-H "Content-Type: application/json" \
		-d '{"book_url": "$(URL)", "book_title": "$(TITLE)"}' \
		| python3 -m json.tool

process-skip-retrieval: ## Process with existing images
	@echo "$(YELLOW)Processing with existing images...$(NC)"
	@curl -X POST http://localhost:8000/pipeline \
		-H "Content-Type: application/json" \
		-d '{"skip_retrieval": true, "book_title": "$(TITLE)"}' \
		| python3 -m json.tool

##@ Single Container (Alternative)

run-single: ## Run single container with book URL
	@echo "$(YELLOW)Running single container...$(NC)"
	./docker-run.sh single --url "$(URL)" --title "$(TITLE)"

run-single-config: ## Run single container with config file
	@echo "$(YELLOW)Running single container with config...$(NC)"
	./docker-run.sh single --config config/$(CONFIG)

##@ Information

version: ## Show version information
	@echo "$(BLUE)Textbook Parser Pipeline$(NC)"
	@echo "Version: 0.1.0"
	@echo ""
	@echo "Docker version:"
	@docker --version
	@echo ""
	@echo "Docker Compose version:"
	@docker-compose --version

status: ## Show comprehensive system status
	@echo "$(BLUE)System Status$(NC)"
	@echo ""
	@echo "$(YELLOW)Docker containers:$(NC)"
	@docker-compose ps
	@echo ""
	@echo "$(YELLOW)Docker images:$(NC)"
	@docker images | grep textbook-parser
	@echo ""
	@echo "$(YELLOW)Disk usage:$(NC)"
	@docker system df

ports: ## Show all exposed ports
	@echo "$(BLUE)Service Ports$(NC)"
	@echo "Orchestrator:      http://localhost:8000"
	@echo "Retriever:         http://localhost:8001"
	@echo "Layout Analyzer:   http://localhost:8002"
	@echo "Image Processor:   http://localhost:8003"
	@echo "OCR Engine:        http://localhost:8004"
	@echo "Interpreter:       http://localhost:8005"

##@ Examples

example-georgian: ## Process Georgian textbook example
	@echo "$(YELLOW)Processing Georgian textbook example...$(NC)"
	@curl -X POST http://localhost:8000/pipeline \
		-H "Content-Type: application/json" \
		-d '{"book_url": "https://example.com/georgian-book", "book_title": "Georgian History"}' \
		| python3 -m json.tool

example-ocr-only: ## Run OCR on existing cleaned images
	@echo "$(YELLOW)Running OCR on existing images...$(NC)"
	@curl -X POST http://localhost:8004/extract/batch \
		-H "Content-Type: application/json" \
		-d '{"image_dir": "/data/cleaned", "output_dir": "/data/text", "languages": ["kat", "eng"]}' \
		| python3 -m json.tool
