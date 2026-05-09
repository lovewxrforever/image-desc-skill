# image-desc-skill — Vision Model Image Analysis

Analyze images using vision-language models from multiple providers. Supports
DashScope, OpenAI, Gemini, Ollama, OpenRouter, and any OpenAI-compatible API.

## Features

- **Describe**: Get detailed descriptions of image contents
- **Ask**: Ask specific questions about images (OCR, object detection, etc.)
- **Extract Text**: OCR — pull text from images
- **Batch**: Process multiple images with the same prompt
- **Compare**: Analyze differences between multiple images
- **Configure**: Interactive setup wizard for API keys

## Installation

### Claude Code

```bash
# Clone directly to the skills directory
git clone <repo-url> ~/.claude/skills/image-desc-skill

# Or use the installer
cd image-desc-skill
./install.sh
```

### VS Code Copilot

```bash
git clone <repo-url> .github/skills/image-desc-skill
```

### Cursor

```bash
git clone <repo-url> .cursor/rules/image-desc-skill
```

### Other Platforms

```bash
./install.sh --platform <platform>
```

See supported platforms: `./install.sh --help`

## Usage

Open a new session and type:

```
/image-desc-skill Describe this image: photo.jpg
/image-desc-skill What text is in this image? scan.png
/image-desc-skill Compare these two: design-v1.png design-v2.png
/image-desc-skill Set up API key
```

### Command Line

```bash
# Describe an image
python scripts/image_desc.py photo.jpg

# Custom prompt
python scripts/image_desc.py scan.png "Extract all text"

# Switch provider
python scripts/image_desc.py photo.jpg --provider openai --model gpt-4o

# Batch process directory
python scripts/image_desc.py --batch screenshots/ "Describe this"

# Compare images
python scripts/image_desc.py --compare img1.jpg img2.jpg "Differences?"

# Configuration wizard
python scripts/configure.py
```

### Python API

```python
from scripts.image_desc import describe, ask, extract_text, batch_process, compare

result = describe("photo.jpg")
text = extract_text("scan.png")
results = batch_process(["img1.jpg", "img2.jpg"], "Describe each")
diff = compare(["v1.png", "v2.png"], "What changed?")
```

## Configuration

Priority: **Environment variables** > `~/.image-desc/config.json` > defaults

### Quick Setup

```bash
python scripts/configure.py
```

### Manual Config

Edit `~/.image-desc/config.json`:

```json
{
  "service": "dashscope",
  "api_key": "sk-...",
  "model": "qwen3.5-flash"
}
```

### Environment Variables

```bash
# Windows (PowerShell)
$env:VL_PROVIDER = "dashscope"
$env:VL_API_KEY = "sk-..."

# Linux / macOS
export VL_PROVIDER="dashscope"
export VL_API_KEY="sk-..."
```

## Supported Providers

| Provider | Default Model | Notes |
|----------|--------------|-------|
| DashScope | qwen3.5-flash | Best for China, cheap |
| OpenAI | gpt-4o-mini | Best quality, paid |
| Gemini | gemini-2.5-flash | 1500 free/day |
| Ollama | llama3.2-vision:11b | Local, free |
| OpenRouter | qwen/qwen2.5-vl-72b-instruct:free | Free tier |
| Custom | user-specified | Any OpenAI-compatible API |

## Requirements

- Python 3.8+
- Standard library only (no pip install required)
- An API key for your chosen provider (except Ollama)

## License

MIT
