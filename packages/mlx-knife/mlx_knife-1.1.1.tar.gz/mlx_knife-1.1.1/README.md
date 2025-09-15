# <img src="https://github.com/mzau/mlx-knife/raw/main/broke-logo.png" alt="BROKE Logo" width="60" style="vertical-align: middle;"> MLX Knife

<p align="center">
  <img src="https://github.com/mzau/mlx-knife/raw/main/mlxk-demo.gif" alt="MLX Knife Demo" width="1000">
</p>

A lightweight, ollama-like CLI for managing and running MLX models on Apple Silicon. **CLI-only tool designed for personal, local use** - perfect for individual developers and researchers working with MLX models.

> **Note**: MLX Knife is designed as a command-line interface tool only. While some internal functions are accessible via Python imports, only CLI usage is officially supported.

**Current Version**: 1.1.1 (September 2025) - **STABLE RELEASE** 🚀
- Features in 1.1.1 — MXFP4 support and GPT-OSS reasoning models:
  - Full MXFP4 quantization support (MLX ≥0.29.0, MLX-LM ≥0.27.0),
  - GPT-OSS reasoning model formatting with `--hide-reasoning` flag,
  - Enhanced quantization display in `show` command,
  - Tested with `gpt-oss-20b-MXFP4-Q8` from mlx-community.
  - Details: see CHANGELOG.md. Install with `pip install mlx-knife`.
- **Reliable Test System**: 166/166 tests passing across Python 3.9–3.13  
- **Python 3.9-3.13**: Full compatibility verified across all Python versions
- **Key Issues Resolved**: Issues #21, #22, #23 fixed and thoroughly tested

[![GitHub Release](https://img.shields.io/github/v/release/mzau/mlx-knife)](https://github.com/mzau/mlx-knife/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Apple Silicon](https://img.shields.io/badge/Apple%20Silicon-M1%2FM2%2FM3-green.svg)](https://support.apple.com/en-us/HT211814)
[![MLX](https://img.shields.io/badge/MLX-Latest-orange.svg)](https://github.com/ml-explore/mlx)
[![Tests](https://img.shields.io/badge/tests-166%2F166%20passing-brightgreen.svg)](#testing)

## Features

### Core Functionality
- **List & Manage Models**: Browse your HuggingFace cache with MLX-specific filtering
- **Model Information**: Detailed model metadata including quantization info
- **Download Models**: Pull models from HuggingFace with progress tracking
- **Run Models**: Native MLX execution with streaming and chat modes
- **Health Checks**: Verify model integrity and completeness
- **Cache Management**: Clean up and organize your model storage

### Local Server & Web Interface
- **OpenAI-Compatible API**: Local REST API with `/v1/chat/completions`, `/v1/completions`, `/v1/models`
- **Web Chat Interface**: Built-in HTML chat interface with markdown rendering  
- **Single-User Design**: Optimized for personal use, not multi-user production environments
- **Conversation Context**: Full chat history maintained for follow-up questions
- **Streaming Support**: Real-time token streaming via Server-Sent Events
- **Configurable Limits**: Set default max tokens via `--max-tokens` parameter
- **Model Hot-Swapping**: Switch between models per conversation
- **Tool Integration**: Compatible with OpenAI-compatible clients (Cursor IDE, etc.)

### Run Experience
- **Direct MLX Integration**: Models load and run natively without subprocess overhead
- **Real-time Streaming**: Watch tokens generate with proper spacing and formatting
- **Interactive Chat**: Full conversational mode with history tracking
- **Memory Insights**: See GPU memory usage after model loading and generation
- **Dynamic Stop Tokens**: Automatic detection and filtering of model-specific stop tokens
- **Customizable Generation**: Control temperature, max_tokens, top_p, and repetition penalty
- **Context-Managed Memory**: Context manager pattern ensures automatic cleanup and prevents memory leaks
- **Exception-Safe**: Robust error handling with guaranteed resource cleanup

## Installation

### Via PyPI (Recommended)
```bash
pip install mlx-knife
```

### Requirements
- macOS with Apple Silicon (M1/M2/M3)
- Python 3.9+ (native macOS version or newer)
- 8GB+ RAM recommended + RAM to run LLM

### Python Compatibility
MLX Knife has been comprehensively tested and verified on:

✅ **Python 3.9.6** (native macOS) - Primary target  
✅ **Python 3.10-3.13** - Fully compatible  

All versions include full MLX model execution testing with real models.

### Install from Source

```bash
# Clone the repository
git clone https://github.com/mzau/mlx-knife.git
cd mlx-knife

# Install in development mode
pip install -e .

# Or install normally
pip install .

# Install with development tools (ruff, mypy, tests)
pip install -e ".[dev,test]"
```

### Install Dependencies Only

```bash
pip install -r requirements.txt
```

## Quick Start

### CLI Usage
```bash
# List all MLX models in your cache
mlxk list

# Show detailed info about a model
mlxk show Phi-3-mini-4k-instruct-4bit

# Download a new model
mlxk pull mlx-community/Mistral-7B-Instruct-v0.3-4bit

# Run a model with a prompt
mlxk run Phi-3-mini "What is the capital of France?"

# GPT-OSS reasoning model with formatted output
mlxk run gpt-oss-20b-MXFP4-Q8 "Explain quantum computing"

# Hide reasoning steps, show only final answer (GPT-OSS models)
mlxk run gpt-oss-20b-MXFP4-Q8 "What is 2+2?" --hide-reasoning

# Start interactive chat
mlxk run Phi-3-mini

# Check model health
mlxk health
```

### Web Chat Interface

MLX Knife includes a built-in web interface for easy model interaction:

```bash
# Start the OpenAI-compatible API server
mlxk server --port 8000 --max-tokens 4000

# Get web chat interface from GitHub
curl -O https://raw.githubusercontent.com/mzau/mlx-knife/main/simple_chat.html

# Open web chat interface in your browser
open simple_chat.html
```

**Features:**
- **No installation required** - Pure HTML/CSS/JS
- **Real-time streaming** - Watch tokens appear as they're generated
- **Model selection** - Choose any MLX model from your cache
- **Conversation history** - Full context for follow-up questions
- **Markdown rendering** - Proper formatting for code, lists, tables
- **Mobile-friendly** - Responsive design works on all devices

### Local API Server Integration

The MLX Knife server provides OpenAI-compatible endpoints for **local development and personal use**:

```bash
# Start local server (single-user, no authentication)
mlxk server --host 127.0.0.1 --port 8000

# Test with curl
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"model": "Phi-3-mini-4k-instruct-4bit", "messages": [{"role": "user", "content": "Hello!"}]}'

# Integration with development tools (community-tested):
# - Cursor IDE: Set API URL to http://localhost:8000/v1
# - LibreChat: Configure as custom OpenAI endpoint  
# - Open WebUI: Add as local OpenAI-compatible API
# - SillyTavern: Add as OpenAI API with custom URL
```

**Note**: Tool integrations are community-tested. Some tools may require specific configuration or have compatibility limitations. Please report issues via GitHub.

## Command Reference

### Available Commands

#### `list` - Browse Models
```bash
mlxk list                    # Show chat-capable MLX models (strict view)
mlxk list --verbose          # Show MLX models with full paths
mlxk list --all              # Show all models with framework and TYPE
mlxk list --all --verbose    # All models with full paths
mlxk list --health           # Include health status
mlxk list Phi-3              # Filter by model name
mlxk list --verbose Phi-3    # Show detailed info (same as show)
```

#### `show` - Model Details
```bash
mlxk show <model>            # Display model information
mlxk show <model> --files    # Include file listing
mlxk show <model> --config   # Show config.json content
```

#### `pull` - Download Models
```bash
mlxk pull <model>            # Download from HuggingFace
mlxk pull <org>/<model>      # Full model path
```

#### `run` - Execute Models
```bash
mlxk run <model> "prompt"              # Single prompt (minimal output)
mlxk run <model> "prompt" --verbose    # Show loading, memory, and stats
mlxk run <model>                       # Interactive chat
mlxk run <model> "prompt" --no-stream  # Batch output
mlxk run <model> --max-tokens 1000     # Custom length
mlxk run <model> --temperature 0.9     # Higher creativity
mlxk run <model> --no-chat-template    # Raw completion mode
mlxk run <model> --hide-reasoning      # Hide reasoning (GPT-OSS models only)
```

#### `rm` - Remove Models
```bash
mlxk rm <model>              # Delete model with cache cleanup confirmation  
mlxk rm <model>@<hash>       # Delete specific version (removes entire model)
mlxk rm <model> --force      # Skip confirmations, auto-cleanup cache files
```

**Features:**
- Removes entire model directory (not just snapshots)
- Cleans up orphaned HuggingFace lock files  
- Handles corrupted models gracefully
- Smart prompting (only asks about cache cleanup if needed)

#### `health` - Check Integrity
```bash
mlxk health                  # Check all models
mlxk health <model>          # Check specific model
```

#### `server` - Start API Server
```bash
mlxk server                           # Start on localhost:8000
mlxk server --port 8001               # Custom port
mlxk server --host 0.0.0.0 --port 8000  # Allow external access
mlxk server --max-tokens 4000         # Set default max tokens (default: 2000)
mlxk server --reload                  # Development mode with auto-reload
```

### Command Aliases
After installation, these commands are equivalent:
- `mlxk` (recommended)
- `mlx-knife`
- `mlx_knife`

## Configuration

### Cache Location
By default, models are stored in `~/.cache/huggingface/hub`. Configure with:

```bash
# Set custom cache location
export HF_HOME="/path/to/your/cache"

# Example: External SSD
export HF_HOME="/Volumes/ExternalSSD/models"
```

### Model Name Expansion
Short names are automatically expanded for MLX models:
- `Phi-3-mini-4k-instruct-4bit` → `mlx-community/Phi-3-mini-4k-instruct-4bit`
- Models already containing `/` are used as-is

## Advanced Usage

### Generation Parameters

```bash
# Creative writing (high temperature, diverse output)
mlxk run Mistral-7B "Write a story" --temperature 0.9 --top-p 0.95

# Precise tasks (low temperature, focused output)
mlxk run Phi-3-mini "Extract key points" --temperature 0.3 --top-p 0.9

# Long-form generation
mlxk run Mixtral-8x7B "Explain quantum computing" --max-tokens 2000

# Reduce repetition
mlxk run model "prompt" --repetition-penalty 1.2
```

### Working with Specific Commits

```bash
# Use specific model version
mlxk show model@commit_hash
mlxk run model@commit_hash "prompt"
```

### Non-MLX Model Handling

The tool automatically detects framework compatibility:
```bash
# Attempting to run PyTorch model
mlxk run bert-base-uncased
# Error: Model bert-base-uncased is not MLX-compatible (Framework: PyTorch)!
# Use MLX-Community models: https://huggingface.co/mlx-community
```

## Troubleshooting

### Model Not Found
```bash
# If model isn't found, try full path
mlxk pull mlx-community/Model-Name-4bit

# List available models
mlxk list --all
```

### Performance Issues
- Ensure sufficient RAM for model size
- Close other applications to free memory
- Use smaller quantized models (4-bit recommended)

### Streaming Issues
- Some models may have spacing issues - this is handled automatically
- Use `--no-stream` for batch output if needed

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## Security

For security concerns, please see [SECURITY.md](SECURITY.md) or contact us at broke@gmx.eu.

MLX Knife runs entirely locally - no data is sent to external servers except when downloading models from HuggingFace.

## License

MIT License - see [LICENSE](LICENSE) file for details

Copyright (c) 2025 The BROKE team 🦫

## Sponsors

<div align="left" style="display: flex; flex-wrap: wrap; gap: 8px; align-items: center;">
  <a href="https://github.com/tileshq" title="Tiles Launcher" style="display:inline-flex; align-items:center; gap:8px; text-decoration:none;">
    <img src="https://github.com/tileshq.png" alt="Tiles Launcher" width="48" style="width:48px; height:auto; max-width:100%;">
    <span><strong>Tiles Launcher</strong></span>
  </a>
</div>

## Acknowledgments

- Built for Apple Silicon using the [MLX framework](https://github.com/ml-explore/mlx)
- Models hosted by the [MLX Community](https://huggingface.co/mlx-community) on HuggingFace
- Inspired by [ollama](https://ollama.ai)'s user experience

---

<p align="center">
  <b>Made with ❤️ by The BROKE team <img src="broke-logo.png" alt="BROKE Logo" width="30" style="vertical-align: middle;"></b><br>
  <i>Version 1.1.1 | September 2025</i><br>
  <a href="https://github.com/mzau/broke-cluster">🔮 Next: BROKE Cluster for multi-node deployments</a>
</p>
