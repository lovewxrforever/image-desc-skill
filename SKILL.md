---
name: image-desc-skill
description: >-
  Vision language model integration skill. Describe images, extract text (OCR),
  ask questions about image content, batch process images, compare multiple
  images. Supports DashScope, OpenAI, Gemini, Ollama, OpenRouter, and custom
  OpenAI-compatible endpoints.
activation: /image-desc-skill
license: MIT
metadata:
  author: agent-skill-creator
  version: 1.0.0
  created: 2026-05-10
  last_reviewed: 2026-05-10
  review_interval_days: 90
  provenance:
    maintainer: agent-skill-creator
    source_references:
      - E:\skill\image-desc\image_desc.py
  dependencies:
    - url: https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
      name: DashScope API
      type: api
    - url: https://api.openai.com/v1/chat/completions
      name: OpenAI API
      type: api
    - url: https://generativelanguage.googleapis.com/v1beta/openai/chat/completions
      name: Google Gemini API
      type: api
    - url: https://openrouter.ai/api/v1/chat/completions
      name: OpenRouter API
      type: api
  schema_expectations:
    - url: https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
      method: POST
      expected_keys:
        - choices
        - choices[].message
        - choices[].message.content
    - url: https://api.openai.com/v1/chat/completions
      method: POST
      expected_keys:
        - choices
        - choices[].message
        - choices[].message.content
---
# /image-desc-skill — Vision Model Image Analysis

You are an expert in vision-language models and API integration. Your job is to
analyze images using OpenAI-compatible vision APIs, handling multiple providers,
error conditions, and various analysis modes.

## Trigger

User invokes `/image-desc-skill` followed by their input:

```
/image-desc-skill Describe this image: path/to/photo.jpg
/image-desc-skill What text is in this image? scan.png
/image-desc-skill Compare these two images: img1.jpg img2.jpg
/image-desc-skill Set up API key for DashScope
/image-desc-skill Process all images in the screenshots/ folder
```

## Configuration

The skill reads configuration in this priority order (higher wins):
1. Environment variables: `VL_PROVIDER`, `VL_API_KEY`, `VL_MODEL`, `VL_BASE_URL`
2. Config file: `~/.image-desc/config.json`
3. Script defaults

### Supported Providers

| Provider     | Default Model        | Notes                    |
|-------------|----------------------|--------------------------|
| dashscope   | qwen3.5-flash        | Best for Chinese users   |
| openai      | gpt-4o-mini          | Best quality, paid       |
| gemini      | gemini-2.5-flash     | 1500 free requests/day   |
| ollama      | llama3.2-vision:11b  | Local, free, needs GPU   |
| openrouter  | qwen/qwen2.5-vl-72b-instruct:free | Free tier available |
| custom      | (user-specified)     | Any OpenAI-compatible API |

## Workflows

### 1. describe — General image description

Analyze what is in an image. Default prompt: "请详细描述这张图片的内容" (detailed Chinese description).

**Input**: Image path, optional custom prompt
**Output**: Text description from the vision model

### 2. ask — Specific question about an image

Ask a targeted question about image content (OCR, object detection, layout analysis, etc.).

**Input**: Image path + question
**Output**: Answer from the vision model

### 3. extract-text — OCR from image

Extract all readable text from an image.

**Input**: Image path
**Output**: Extracted text content

### 4. batch — Process multiple images

Apply the same prompt to multiple images sequentially.

**Input**: Directory path or multiple file paths + prompt
**Output**: Results for each image (labeled by filename)

### 5. compare — Multi-image analysis

Send multiple images in one API call with a comparison prompt.

**Input**: 2+ image paths + comparison question
**Output**: Comparative analysis

### 6. configure — Interactive setup

Guide the user through API key configuration for any provider.

**Input**: Provider name (optional)
**Output**: Configuration instructions / config file creation

## Usage

```python
# Python API
from scripts.image_desc import describe, ask, extract_text, batch_process, compare

# Describe an image
result = describe("photo.jpg")
print(result)

# Ask a specific question
result = ask("scan.png", "提取图片中的所有文字")

# Compare two images
result = compare(["design-v1.png", "design-v2.png"], "比较这两个设计的差异")
```

```bash
# Command line
python scripts/image_desc.py photo.jpg
python scripts/image_desc.py scan.png "提取图片中的所有文字"
python scripts/image_desc.py --batch screenshots/ "描述这些截图"
python scripts/image_desc.py --compare img1.jpg img2.jpg "有什么不同？"

# Provider/model flags
python scripts/image_desc.py photo.jpg --provider openai --model gpt-4o
python scripts/image_desc.py photo.jpg --provider ollama

# Configuration wizard
python scripts/configure.py
python scripts/configure.py --provider dashscope
```

## Error Handling

When the user encounters an error:

1. **Missing API key**: Guide them to run `python scripts/configure.py` or set `VL_API_KEY`
2. **Image not found**: Verify the path exists and is accessible
3. **Image too large**: Max 20MB per image; suggest resizing
4. **API error**: Check provider endpoint, auth, and model availability
5. **Network error**: Suggest retry or switching providers

## Action Plan

When a user says "/image-desc-skill <something>":

1. Parse the intent (describe, ask, extract-text, batch, compare, configure)
2. If no API key configured, check `~/.image-desc/config.json` or env vars
3. Run the appropriate workflow
4. Display results clearly; on error, provide actionable guidance
