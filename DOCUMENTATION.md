# Textbook Parser - Complete Documentation Index

This is your guide to all documentation. Start here to find what you need.

## 🚀 Getting Started (Choose Your Path)

### Path 1: Docker User (Recommended) ⭐

**Best for:** Most users, production deployment

1. **[README.md](README.md)** - Start here for overview
2. **[MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md)** - Learn the commands (5 min read)
3. Run: `make quick-start`
4. **[QUICKSTART_API.md](QUICKSTART_API.md)** - Process your first book (10 min)

### Path 2: Developer/Contributor

**Best for:** Contributing code, customizing services

1. **[README.md](README.md)** - Understand the system
2. **[API.md](API.md)** - Learn the service interfaces
3. **[INSTALL.md](INSTALL.md)** - Set up development environment
4. Start coding!

### Path 3: Manual Installation User

**Best for:** No Docker, need fine-grained control

1. **[INSTALL.md](INSTALL.md)** - Complete installation guide
2. **[README.md](README.md#-installation-manual)** - Configuration
3. Run pipeline locally

---

## 📚 Documentation Overview

### Core Documentation

| Document | Size | Purpose | When to Read |
|----------|------|---------|--------------|
| **[README.md](README.md)** | 500 lines | Project overview, quick start | First document to read |
| **[API.md](API.md)** | 600 lines | REST API reference | Replacing services, API integration |
| **[DOCKER.md](DOCKER.md)** | 400 lines | Docker deployment guide | Docker setup, troubleshooting |
| **[MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md)** | 400 lines | Makefile commands | Daily operations |
| **[INSTALL.md](INSTALL.md)** | 300 lines | Installation instructions | Manual setup, troubleshooting |
| **[QUICKSTART_API.md](QUICKSTART_API.md)** | 380 lines | API quick start | Using multi-container setup |

### Configuration Files

| File | Purpose |
|------|---------|
| **[config/default_config.yaml](config/default_config.yaml)** | Default configuration template |
| **[config/example_georgian_book.yaml](config/example_georgian_book.yaml)** | Georgian textbook example |
| **[.env.example](.env.example)** | Environment variables template |

### Example Scripts

| File | Purpose |
|------|---------|
| **[examples/simple_usage.py](examples/simple_usage.py)** | Basic pipeline usage |
| **[examples/step_by_step.py](examples/step_by_step.py)** | Run individual steps |
| **[examples/test_modules.py](examples/test_modules.py)** | Test components |

---

## 🎯 Find What You Need

### "I want to..."

#### ...get started quickly
→ **[MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md)** → Run `make quick-start`

#### ...understand how it works
→ **[README.md](README.md)** → Architecture and Features sections

#### ...install without Docker
→ **[INSTALL.md](INSTALL.md)** → Complete installation guide

#### ...deploy to production
→ **[DOCKER.md](DOCKER.md)** → Production deployment section
→ **[MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md)** → Scaling commands

#### ...replace a service (e.g., use Google Vision instead of Tesseract)
→ **[API.md](API.md)** → OCR Engine Service section
→ **[QUICKSTART_API.md](QUICKSTART_API.md)** → Service replacement example

#### ...process my first book
→ **[QUICKSTART_API.md](QUICKSTART_API.md)** → Step-by-step guide
→ Or run: `make process URL="..." TITLE="..."`

#### ...debug an issue
→ **[MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md#troubleshooting)**
→ **[DOCKER.md](DOCKER.md#troubleshooting)**
→ **[INSTALL.md](INSTALL.md#troubleshooting)**

#### ...understand the API
→ **[API.md](API.md)** → Complete API reference
→ Or visit: `http://localhost:8000/docs` (Swagger UI)

#### ...scale services
→ **[MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md)** → Scaling section
→ Run: `make scale-ocr N=5`

#### ...configure the pipeline
→ **[README.md](README.md#-configuration)**
→ **[config/default_config.yaml](config/default_config.yaml)**

#### ...use with NotebookLM
→ **[README.md](README.md#-using-with-google-notebooklm)**
→ Output file: `output/notebook_export/notebooklm_instructions.md`

---

## 📖 Documentation by Topic

### Installation & Setup

- **[INSTALL.md](INSTALL.md)** - Detailed installation (all platforms)
- **[README.md](README.md#-installation-manual)** - Quick installation
- **[DOCKER.md](DOCKER.md)** - Docker setup

### Usage & Operations

- **[MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md)** - All make commands
- **[QUICKSTART_API.md](QUICKSTART_API.md)** - API operations
- **[README.md](README.md#-usage)** - Basic usage

### Configuration

- **[README.md](README.md#-configuration)** - Configuration overview
- **[config/default_config.yaml](config/default_config.yaml)** - Default settings
- **[config/example_georgian_book.yaml](config/example_georgian_book.yaml)** - Example
- **[.env.example](.env.example)** - Environment variables

### Architecture & API

- **[API.md](API.md)** - Complete API reference
- **[README.md](README.md#-pipeline-modules)** - Module overview
- **[README.md](README.md#️-architecture)** - System architecture

### Deployment

- **[DOCKER.md](DOCKER.md)** - Docker deployment
- **[MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md)** - Operations
- **[QUICKSTART_API.md](QUICKSTART_API.md)** - Multi-container setup

### Troubleshooting

- **[INSTALL.md](INSTALL.md#troubleshooting)** - Installation issues
- **[DOCKER.md](DOCKER.md#troubleshooting)** - Docker issues
- **[MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md#troubleshooting)** - Runtime issues
- **[README.md](README.md#️-troubleshooting)** - Common problems

### Development

- **[API.md](API.md#creating-alternative-implementations)** - Create custom services
- **[examples/](examples/)** - Example code
- **[README.md](README.md#-contributing)** - Contribution guide

---

## 🔍 Quick Reference Tables

### Commands by Task

| Task | Command | Documentation |
|------|---------|---------------|
| Start everything | `make quick-start` | [MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md) |
| Process a book | `make process URL="..." TITLE="..."` | [QUICKSTART_API.md](QUICKSTART_API.md) |
| Check health | `make health` | [MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md) |
| View logs | `make logs` | [MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md) |
| Scale OCR | `make scale-ocr N=5` | [MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md) |
| Stop services | `make down` | [MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md) |
| Open API docs | `make docs` | [API.md](API.md) |

### Services & Ports

| Service | Port | API Docs | Source Code |
|---------|------|----------|-------------|
| Orchestrator | 8000 | http://localhost:8000/docs | [src/api/orchestrator_service.py](src/api/orchestrator_service.py) |
| Retriever | 8001 | http://localhost:8001/docs | [src/api/retriever_service.py](src/api/retriever_service.py) |
| Layout Analyzer | 8002 | http://localhost:8002/docs | [src/api/layout_service.py](src/api/layout_service.py) |
| Image Processor | 8003 | http://localhost:8003/docs | [src/api/processor_service.py](src/api/processor_service.py) |
| OCR Engine | 8004 | http://localhost:8004/docs | [src/api/ocr_service.py](src/api/ocr_service.py) |
| Interpreter | 8005 | http://localhost:8005/docs | [src/api/interpreter_service.py](src/api/interpreter_service.py) |

### File Locations

| Type | Location | Purpose |
|------|----------|---------|
| Source code | `src/` | Python modules |
| API services | `src/api/` | REST API implementations |
| Configuration | `config/` | YAML config files |
| Examples | `examples/` | Example scripts |
| Docker files | `docker/` | Service Dockerfiles |
| Output | `output/` | Processing results |

---

## 🎓 Learning Path

### Beginner (< 1 hour)

1. Read **[README.md](README.md)** overview (10 min)
2. Read **[MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md)** introduction (10 min)
3. Run `make quick-start` (5 min)
4. Read **[QUICKSTART_API.md](QUICKSTART_API.md)** (15 min)
5. Process a test book (10 min)

### Intermediate (2-3 hours)

1. Complete Beginner path
2. Read **[API.md](API.md)** service interfaces (30 min)
3. Read **[DOCKER.md](DOCKER.md)** deployment guide (30 min)
4. Try scaling services (15 min)
5. Experiment with different configurations (30 min)
6. Review example scripts in `examples/` (30 min)

### Advanced (Full day)

1. Complete Intermediate path
2. Read **[API.md](API.md)** completely (1 hour)
3. Implement a custom service (2 hours)
4. Set up production deployment (1 hour)
5. Optimize for your use case (2 hours)
6. Contribute improvements (2 hours)

---

## 📊 Documentation Dependency Map

```
                    README.md
                    (Start Here)
                         |
        +----------------+----------------+
        |                |                |
    MAKEFILE_GUIDE   DOCKER.md      INSTALL.md
        |                |                |
        +-------+--------+--------+-------+
                |                 |
        QUICKSTART_API.md      API.md
                                  |
                          (Service Implementations)
```

**Reading order suggestion:**
1. README.md (overview)
2. MAKEFILE_GUIDE.md (operations) OR INSTALL.md (manual setup)
3. QUICKSTART_API.md (first book)
4. API.md (customization)
5. DOCKER.md (production)

---

## 🎯 Documentation Coverage

### Fully Documented ✅

- Installation (all platforms)
- Docker deployment (all modes)
- Makefile commands (all 50+)
- API endpoints (all services)
- Configuration options
- Troubleshooting
- Examples

### Coming Soon 🚧

- Video tutorials
- Interactive web UI
- Additional language guides
- Advanced customization examples

---

## 📞 Getting Help

### Before Asking Questions

1. **Search this index** - Find the right document
2. **Check troubleshooting** - Common issues documented
3. **Read examples** - See working code
4. **Review configurations** - Check example configs

### When You Need Help

1. **GitHub Issues** - Create detailed issue
2. **Documentation** - Link to specific doc sections
3. **Examples** - Share what you tried
4. **Logs** - Include error messages

---

## 🔄 Keeping Documentation Updated

All documentation is version controlled. When features change:

1. **Main features** → Update README.md
2. **New commands** → Update MAKEFILE_GUIDE.md
3. **API changes** → Update API.md
4. **Docker changes** → Update DOCKER.md
5. **Installation** → Update INSTALL.md

---

**Last Updated:** 2025-01-09
**Version:** 0.1.0
**Maintainer:** See GitHub contributors

---

**Quick Start:** `make help` or `make quick-start`
