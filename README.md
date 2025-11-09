# Textbook Parser: Illustrated Book Text Extraction & AI Summarization Pipeline

A comprehensive automated pipeline that extracts text and contextual meaning from illustrated book images to generate summaries, quizzes, and educational reports through Google Notebook integration.

---

## 📚 Documentation

**Quick Links:**
- **[Makefile Guide](MAKEFILE_GUIDE.md)** - Complete command reference (recommended starting point)
- **[API Documentation](API.md)** - REST API reference for all services
- **[Docker Guide](DOCKER.md)** - Complete Docker deployment documentation
- **[API Quick Start](QUICKSTART_API.md)** - Get started with multi-container setup
- **[Installation Guide](INSTALL.md)** - Detailed installation instructions

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Architecture](#️-architecture)
- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Docker Quick Start (Recommended)](#-docker-recommended)
  - [Using Makefile (Easiest)](#quick-start-with-makefile-easiest)
  - [Using Scripts](#quick-start-with-scripts)
  - [Docker Options](#docker-options)
- [Manual Installation](#-installation-manual)
- [Usage](#-usage)
  - [Quick Start](#quick-start)
  - [Using Configuration Files](#using-configuration-files)
  - [Run Specific Steps](#run-specific-steps)
- [Output Structure](#-output-structure)
- [Configuration](#-configuration)
- [Using with Google NotebookLM](#-using-with-google-notebooklm)
- [Pipeline Modules](#-pipeline-modules)
- [Testing](#-testing)
- [Troubleshooting](#️-troubleshooting)
- [Performance](#-performance)
- [Contributing](#-contributing)
- [License](#-license)
- [Acknowledgments](#-acknowledgments)
- [Support](#-support)
- [Roadmap](#️-roadmap)

---

## 🎯 Overview

This system solves the challenge of extracting meaningful content from image-only book pages (e.g., from Google Drive, Calameo, or embedded viewers) with non-standard, illustration-heavy layouts. It combines:

- **Automated image retrieval** via browser automation
- **Intelligent layout analysis** to separate text from illustrations
- **High-accuracy OCR** optimized for Georgian and multilingual text
- **AI-powered illustration interpretation** using vision-language models
- **Google NotebookLM integration** for generating educational content

## 🏗️ Architecture

```
Book URL → Image Retriever (Playwright)
         → Layout Analyzer (LayoutParser + Detectron2)
         → Image Processor (Illustration Masking)
         → OCR Engine (Tesseract/PaddleOCR)
         → Illustration Interpreter (GPT-4V/Claude/Gemini)
         → Google Notebook Integration
         → Educational Content (Summaries, Quizzes, Audio)
```

## ✨ Features

- **Multi-source retrieval**: Works with Calameo, Google Drive, custom viewers
- **Layout-aware processing**: Intelligently separates text from images
- **Georgian language support**: Optimized for Georgian (ქართული) text extraction
- **Vision AI integration**: Generates descriptions and educational context for illustrations
- **NotebookLM ready**: Exports content in formats compatible with Google NotebookLM
- **Modular architecture**: Run individual pipeline steps or the complete workflow
- **Configurable**: YAML-based configuration with sensible defaults

## 📋 Prerequisites

### System Requirements

- Python 3.8+ OR Docker
- Tesseract OCR (for text extraction) - included in Docker image
- Playwright browsers (for web automation) - included in Docker image

### API Keys (Optional but Recommended)

- **OpenAI API key** (for GPT-4 Vision illustration interpretation)
- **Anthropic API key** (alternative: Claude with vision)
- **Google AI API key** (alternative: Gemini Pro Vision)

## 🐳 Docker (Recommended)

**Prefer Docker?** Skip the manual installation and use our Docker containers!

### Quick Start with Makefile (Easiest!)

```bash
# Build and start everything
make quick-start

# Process a book
make process URL="https://example.com/book" TITLE="My Book"

# View logs
make logs

# Stop services
make down
```

**📖 See [MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md) for all Makefile commands**

### Quick Start with Scripts

```bash
# Build the container
./docker-build.sh single

# Run with your book URL
./docker-run.sh single --url "https://example.com/book" --title "My Book"

# Or use a configuration file
./docker-run.sh single --config config/example_georgian_book.yaml
```

### Docker Options

We provide **three deployment options**:

1. **Single Container** (recommended) - All-in-one, easy to use
   ```bash
   make build-single
   ./docker-run.sh single --url "https://example.com/book"
   ```

2. **Multi-Container** - Production setup with service isolation
   ```bash
   make build-multi
   make up-d
   make health
   ```

3. **GPU-Enabled** - Faster processing with GPU acceleration
   ```bash
   make build-gpu
   ./docker-run.sh gpu --config config/my_book.yaml
   ```

### 📖 Docker Documentation

- **[DOCKER.md](DOCKER.md)** - Complete Docker deployment guide (400+ lines)
  - Single vs multi-container comparison
  - GPU support
  - Production deployment
  - Troubleshooting

- **[API.md](API.md)** - REST API documentation (600+ lines)
  - All service endpoints
  - Request/response schemas
  - How to replace services with alternatives
  - Example implementations

- **[QUICKSTART_API.md](QUICKSTART_API.md)** - API quick start guide
  - Start services
  - Process books via API
  - Service replacement examples
  - Common workflows

- **[MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md)** - Makefile command reference
  - All 50+ make commands
  - Real-world examples
  - Development workflows
  - Production deployment

## 🚀 Installation (Manual)

> **Note:** For detailed installation instructions, see **[INSTALL.md](INSTALL.md)**

### 1. Clone the Repository

```bash
git clone <repository-url>
cd textbook-parser
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Tesseract OCR

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-kat tesseract-ocr-eng
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

### 5. Install Playwright Browsers

```bash
playwright install chromium
```

### 6. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env and add your API keys
```

## 📖 Usage

### Quick Start

Process a book from URL:

```bash
python main.py --url "https://example.com/book" --title "My Textbook"
```

### Using Configuration Files

```bash
python main.py --config config/example_georgian_book.yaml
```

### Run Specific Steps

```bash
# Only extract text (assumes images already retrieved)
python main.py --config config.yaml --step ocr --skip-retrieval

# Only interpret illustrations
python main.py --config config.yaml --step interpret
```

### Advanced Options

```bash
# Custom OCR engine and languages
python main.py --url "URL" --ocr-engine paddleocr --languages kat eng rus

# Skip illustration interpretation (faster)
python main.py --url "URL" --skip-interpretation

# Verbose logging
python main.py --url "URL" -v
```

## 📁 Output Structure

```
output/
├── images/              # Retrieved book page images
├── cleaned/             # Images with illustrations masked (for OCR)
├── text/                # Extracted text files
│   ├── page_001.txt
│   ├── page_002.txt
│   └── book_full.txt    # Combined text
├── illustrations/       # Cropped illustration images
├── metadata/            # Analysis results
│   ├── layout_analysis.json
│   ├── ocr_metadata.json
│   └── illustration_descriptions.json
├── notebook_export/     # Google NotebookLM exports
│   ├── notebook_source.md
│   ├── study_guide.md
│   └── notebooklm_instructions.md
└── pipeline_summary.json
```

## 🔧 Configuration

### Configuration File Structure

See example configurations:
- **[config/default_config.yaml](config/default_config.yaml)** - Default settings
- **[config/example_georgian_book.yaml](config/example_georgian_book.yaml)** - Georgian textbook example

Available options:

```yaml
book_url: "https://example.com/book"
book_title: "My Textbook"
output_dir: "output"

retriever:
  headless: true
  timeout: 30000

layout_analyzer:
  model_name: "lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config"
  confidence_threshold: 0.5
  device: "cpu"

ocr:
  engine: "tesseract"
  languages: ["kat", "eng"]
  confidence_threshold: 60.0

illustration_interpreter:
  provider: "openai"
  model: "gpt-4-vision-preview"
```

### Environment Variables

```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
```

## 🎓 Using with Google NotebookLM

After running the pipeline:

1. Navigate to `output/notebook_export/`
2. Upload `notebook_source.md` to [Google NotebookLM](https://noteboomlm.google.com)
3. Use prompts like:
   - "Create a comprehensive summary of this textbook"
   - "Generate 20 multiple-choice questions"
   - "Generate an audio overview"

The pipeline automatically generates:
- `notebook_source.md` - Main content for NotebookLM
- `study_guide.md` - Pre-formatted study guide
- `notebooklm_instructions.md` - Detailed usage instructions

## 🔍 Pipeline Modules

### 1. Image Retriever
- **Technology**: Playwright browser automation
- **Strategies**: Network interception, screenshots, direct download
- **Features**: Retry logic, lazy-load handling, rate limiting

### 2. Layout Analyzer
- **Technology**: LayoutParser + Detectron2
- **Detects**: Text blocks, illustrations, captions, titles, tables
- **Fallback**: Heuristic-based detection when models unavailable

### 3. Image Processor
- **Operations**: Illustration masking, cropping, enhancement
- **Features**: Deskewing, noise removal, contrast adjustment

### 4. OCR Engine
- **Engines**: Tesseract (default), PaddleOCR
- **Languages**: Georgian (kat), English (eng), Russian (rus), and more
- **Post-processing**: Text cleanup, hyphen removal, formatting

### 5. Illustration Interpreter
- **Providers**: OpenAI GPT-4V, Anthropic Claude, Google Gemini
- **Generates**: Captions, descriptions, tags, educational context
- **Context-aware**: Uses book metadata for better interpretation

### 6. Notebook Integration
- **Formats**: Markdown, JSON, structured text
- **Features**: Study guides, quiz prompts, summary templates
- **Compatible**: Google NotebookLM, general LLM tools

## 🧪 Testing

### Example Scripts

See the `examples/` directory:
- **[examples/simple_usage.py](examples/simple_usage.py)** - Basic pipeline usage
- **[examples/step_by_step.py](examples/step_by_step.py)** - Run steps individually
- **[examples/test_modules.py](examples/test_modules.py)** - Test individual modules

### Run Individual Modules

```python
from src.ocr_engine import OCREngine
from pathlib import Path

ocr = OCREngine(engine="tesseract", languages=["kat", "eng"])
result = ocr.extract_text(Path("test_image.png"))
print(result.text)
```

## 🛠️ Troubleshooting

> **Note:** For comprehensive troubleshooting, see:
> - **[INSTALL.md](INSTALL.md#troubleshooting)** - Installation issues
> - **[DOCKER.md](DOCKER.md#troubleshooting)** - Docker-specific issues
> - **[MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md#troubleshooting)** - Makefile issues

### Common Issues

#### Tesseract not found
```bash
# Set TESSERACT_CMD environment variable
export TESSERACT_CMD=/usr/local/bin/tesseract
```

### LayoutParser installation issues
```bash
# Install with specific PyTorch version
pip install torch==2.1.2 torchvision==0.16.2
pip install layoutparser[layoutmodels]
```

### Playwright browser issues
```bash
# Reinstall browsers
playwright install --force chromium
```

### Low OCR accuracy
- Ensure Georgian language pack is installed: `tesseract --list-langs`
- Try PaddleOCR: `--ocr-engine paddleocr`
- Adjust confidence threshold in config

## 📊 Performance

| Books Processed | Pages | Time (avg) | Accuracy |
|----------------|-------|------------|----------|
| 10+ | 50-500 | 2-10 min | >90% OCR |

*Performance varies based on:*
- Network speed (for retrieval)
- Hardware (CPU vs GPU for layout analysis)
- Image quality
- Text complexity

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- Additional OCR engine support
- Custom layout models for specific book types
- Enhanced Georgian text post-processing
- Direct Google NotebookLM API integration (when available)

## 📄 License

MIT License - see LICENSE file

## 🙏 Acknowledgments

- [LayoutParser](https://layout-parser.github.io/) for document layout analysis
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for text extraction
- [Playwright](https://playwright.dev/) for browser automation
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) for multilingual OCR

## 📧 Support

For issues and questions:
- **Create an issue** on GitHub
- **Check documentation:**
  - [INSTALL.md](INSTALL.md) - Installation help
  - [DOCKER.md](DOCKER.md) - Docker troubleshooting
  - [API.md](API.md) - API reference
  - [MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md) - Makefile commands
- **Review examples** in `examples/` directory
- **Check configurations** in `config/` directory

## 🗺️ Roadmap

- [ ] Direct Google NotebookLM API integration
- [ ] Web UI for easier usage
- [ ] Batch processing multiple books
- [ ] Custom fine-tuned layout models for Georgian texts
- [ ] Integration with Whisper for audio narration
- [ ] Semantic linking between text and illustrations
- [ ] Export to EPUB, Markdown, knowledge graphs
- [ ] Support for handwritten text recognition

---

**Built with ❤️ for educational content extraction and AI-powered learning**
