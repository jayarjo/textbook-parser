# Installation Guide

Detailed installation instructions for the Textbook Parser pipeline.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Python Installation](#python-installation)
3. [Tesseract OCR Setup](#tesseract-ocr-setup)
4. [Python Dependencies](#python-dependencies)
5. [Playwright Setup](#playwright-setup)
6. [GPU Support (Optional)](#gpu-support-optional)
7. [API Keys Configuration](#api-keys-configuration)
8. [Verification](#verification)
9. [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements
- **OS**: Linux (Ubuntu 20.04+), macOS (10.15+), or Windows 10+
- **RAM**: 8 GB (16 GB recommended for large books)
- **Storage**: 5 GB free space
- **Python**: 3.8 or higher

### Recommended Requirements
- **RAM**: 16 GB+
- **GPU**: NVIDIA GPU with CUDA support (for faster layout analysis)
- **Storage**: 10 GB+ for model caching

## Python Installation

### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install python3.9 python3.9-venv python3-pip
```

### macOS
```bash
# Using Homebrew
brew install python@3.9
```

### Windows
Download from [python.org](https://www.python.org/downloads/) and install.

## Tesseract OCR Setup

### Ubuntu/Debian
```bash
# Install Tesseract
sudo apt-get update
sudo apt-get install tesseract-ocr

# Install Georgian language pack
sudo apt-get install tesseract-ocr-kat

# Install additional languages
sudo apt-get install tesseract-ocr-eng tesseract-ocr-rus

# Verify installation
tesseract --version
tesseract --list-langs
```

### macOS
```bash
# Using Homebrew
brew install tesseract
brew install tesseract-lang

# Verify installation
tesseract --version
tesseract --list-langs
```

### Windows
1. Download installer from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run installer and note the installation path
3. Add to system PATH or set `TESSERACT_CMD` environment variable

```powershell
# Add to environment variables
setx TESSERACT_CMD "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

## Python Dependencies

### 1. Create Virtual Environment
```bash
cd textbook-parser
python3 -m venv venv
```

### 2. Activate Virtual Environment

**Linux/macOS:**
```bash
source venv/bin/activate
```

**Windows:**
```powershell
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### Alternative: Install Without LayoutParser

If you encounter issues with LayoutParser/Detectron2:

```bash
# Install without layout analysis dependencies
pip install playwright requests pillow pytesseract paddleocr \
    openai anthropic google-generativeai pydantic python-dotenv \
    tqdm loguru pyyaml pytest black
```

The pipeline will fall back to heuristic-based layout detection.

## Playwright Setup

### Install Playwright Browsers

```bash
# Install Chromium browser
playwright install chromium

# Or install all browsers
playwright install
```

### Verify Installation

```bash
playwright --version
```

## GPU Support (Optional)

For faster layout analysis with GPU acceleration:

### CUDA Installation (NVIDIA GPUs)

**Linux:**
```bash
# Check CUDA compatibility
nvidia-smi

# Install CUDA toolkit (example for CUDA 11.8)
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda-repo-ubuntu2004-11-8-local_11.8.0-520.61.05-1_amd64.deb
sudo dpkg -i cuda-repo-ubuntu2004-11-8-local_11.8.0-520.61.05-1_amd64.deb
sudo cp /var/cuda-repo-ubuntu2004-11-8-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get -y install cuda
```

### PyTorch with CUDA

```bash
# Install PyTorch with CUDA support
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Verify GPU Support

```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA device: {torch.cuda.get_device_name(0)}")
```

## API Keys Configuration

### 1. Create Environment File

```bash
cp .env.example .env
```

### 2. Add API Keys

Edit `.env` file:

```bash
# OpenAI (for GPT-4 Vision)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx

# Anthropic (for Claude with vision)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx

# Google AI (for Gemini)
GOOGLE_API_KEY=AIzaxxxxxxxxxxxxx
```

### 3. Get API Keys

- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic**: https://console.anthropic.com/
- **Google AI**: https://makersuite.google.com/app/apikey

## Verification

### Test Installation

```bash
# Test basic import
python -c "from src.pipeline import TextbookPipeline; print('✓ Installation successful')"

# Test Tesseract
tesseract --version

# Test Playwright
playwright --version

# Run example
python examples/test_modules.py
```

### Check Tesseract Languages

```bash
tesseract --list-langs
```

Should show:
```
List of available languages (3):
eng
kat
osd
```

## Troubleshooting

### Issue: Tesseract not found

**Solution:**
```bash
# Set environment variable
export TESSERACT_CMD=/usr/bin/tesseract

# Or add to .env file
echo "TESSERACT_CMD=/usr/bin/tesseract" >> .env
```

### Issue: LayoutParser installation fails

**Solution 1: Use CPU-only installation**
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install layoutparser
```

**Solution 2: Skip LayoutParser**
The pipeline will work with fallback heuristics.

### Issue: Playwright browser download fails

**Solution:**
```bash
# Clear cache and reinstall
rm -rf ~/.cache/ms-playwright
playwright install chromium --force
```

### Issue: Permission denied for Playwright

**Linux:**
```bash
sudo playwright install-deps chromium
```

### Issue: CUDA out of memory

**Solution:**
```bash
# Use CPU instead of GPU in config
device: "cpu"
```

### Issue: PaddleOCR import error

**Solution:**
```bash
# Install PaddlePaddle CPU version
pip install paddlepaddle==2.6.0
pip install paddleocr==2.7.0.3
```

## Next Steps

After successful installation:

1. Review [README.md](README.md) for usage instructions
2. Check example configurations in `config/`
3. Try running a simple example: `python examples/simple_usage.py`
4. Configure your first book in `config/my_book.yaml`

## Support

If you encounter issues not covered here:

1. Check existing GitHub issues
2. Review error logs in `textbook_parser.log`
3. Create a new issue with:
   - Your OS and version
   - Python version
   - Full error message
   - Steps to reproduce
