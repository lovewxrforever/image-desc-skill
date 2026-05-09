"""
image-desc — Vision model image analysis via OpenAI-compatible APIs.

Supports: DashScope / OpenAI / Gemini / Ollama / OpenRouter / custom services
Dependencies: Python 3.8+, standard library only (no pip install required).
"""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PRESETS: dict[str, dict[str, str]] = {
    "dashscope": {
        "url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "model": "qwen3.5-flash",
    },
    "openai": {
        "url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o-mini",
    },
    "gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-2.5-flash",
    },
    "ollama": {
        "url": "http://localhost:11434/v1/chat/completions",
        "model": "llama3.2-vision:11b",
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "qwen/qwen2.5-vl-72b-instruct:free",
    },
}

_MIME_OVERRIDES: dict[str, str] = {
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
    ".ico": "image/x-icon",
    ".svg": "image/svg+xml",
}

_DEFAULT_MAX_TOKENS = 4096
_DEFAULT_MAX_IMAGE_MB = 20
_DEFAULT_TIMEOUT = 90
_DEFAULT_MAX_RETRIES = 2
_DEFAULT_PROMPT = "请详细描述这张图片的内容"


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def _load_config() -> dict[str, Any]:
    """Load user config from ``~/.image-desc/config.json``.

    Returns an empty dict if the file does not exist or is malformed.
    """
    config_path = Path.home() / ".image-desc" / "config.json"
    try:
        if config_path.exists():
            data = json.loads(config_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _resolve() -> dict[str, str]:
    """Resolve effective API configuration.

    Priority: environment variable > ``~/.image-desc/config.json`` > built-in default.

    Returns a dict with keys: ``api_url``, ``api_key``, ``model``.
    """
    config = _load_config()

    svc = (
        os.environ.get("VL_PROVIDER")
        or config.get("service", "")
        or ""
    )
    api_key = (
        os.environ.get("VL_API_KEY")
        or os.environ.get("DASHSCOPE_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or config.get("api_key", "")
        or ""
    )
    model = (
        os.environ.get("VL_MODEL")
        or os.environ.get("DASHSCOPE_VL_MODEL")
        or config.get("model", "")
        or ""
    )
    url_override = (
        os.environ.get("VL_BASE_URL")
        or config.get("base_url", "")
        or ""
    )

    if url_override:
        api_url = url_override.rstrip("/") + "/chat/completions"
    elif svc in _PRESETS:
        api_url = _PRESETS[svc]["url"]
        if not model:
            model = _PRESETS[svc]["model"]
    else:
        api_url = _PRESETS["dashscope"]["url"]
        if not model:
            model = _PRESETS["dashscope"]["model"]

    return {"api_url": api_url, "api_key": api_key, "model": model}


# ---------------------------------------------------------------------------
# Image encoding
# ---------------------------------------------------------------------------

def _mime_type(path: str) -> str:
    """Guess MIME type from file extension."""
    ext = Path(path).suffix.lower()
    if ext in _MIME_OVERRIDES:
        return _MIME_OVERRIDES[ext]
    mime, _ = mimetypes.guess_type(path)
    return mime or "application/octet-stream"


def encode_image(path: str, max_mb: int = _DEFAULT_MAX_IMAGE_MB) -> tuple[str, str]:
    """Read an image and return ``(mime_type, base64_data)``.

    Raises ``FileNotFoundError`` if the path does not exist.
    Raises ``ValueError`` if the image exceeds ``max_mb``.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Image not found: {path}")
    size_mb = p.stat().st_size / (1024 * 1024)
    if size_mb > max_mb:
        raise ValueError(f"Image too large: {size_mb:.1f}MB (limit {max_mb}MB)")
    mime = _mime_type(path)
    b64 = base64.b64encode(p.read_bytes()).decode()
    return mime, b64


# ---------------------------------------------------------------------------
# Core API call
# ---------------------------------------------------------------------------

def _call_api(
    image_path: str,
    prompt: str = _DEFAULT_PROMPT,
    *,
    provider: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    max_tokens: int = _DEFAULT_MAX_TOKENS,
    timeout: int = _DEFAULT_TIMEOUT,
    max_retries: int = _DEFAULT_MAX_RETRIES,
    max_image_mb: int = _DEFAULT_MAX_IMAGE_MB,
) -> str:
    """Send an image to a vision API and return the text response.

    All exceptions are caught internally — the function returns an error
    message string instead of raising.
    """
    cfg = _resolve()
    api_url = cfg["api_url"]
    api_key = cfg["api_key"]
    effective_model = cfg["model"]

    if provider:
        if provider in _PRESETS:
            api_url = (
                base_url.rstrip("/") + "/chat/completions"
                if base_url
                else _PRESETS[provider]["url"]
            )
            if not model:
                effective_model = _PRESETS[provider]["model"]
        else:
            api_url = _PRESETS["dashscope"]["url"]
            effective_model = _PRESETS["dashscope"]["model"]
    if model:
        effective_model = model
    if base_url:
        api_url = base_url.rstrip("/") + "/chat/completions"

    if not api_key:
        return (
            "API key not configured.\n\n"
            "To set up, run:\n"
            "  python scripts/configure.py\n\n"
            "Or set environment variables:\n"
            "  set VL_PROVIDER=dashscope & set VL_API_KEY=sk-...\n\n"
            "Or create ~/.image-desc/config.json:\n"
            '  {"service": "dashscope", "api_key": "sk-..."}'
        )

    mime, img_b64 = encode_image(image_path, max_mb=max_image_mb)

    body = json.dumps({
        "model": effective_model,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_b64}"}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    }).encode()

    last_error = ""
    for attempt in range(max_retries + 1):
        try:
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            req = Request(api_url, data=body, headers=headers)
            with urlopen(req, timeout=timeout) as resp:
                result = json.loads(resp.read())

            if "choices" not in result:
                return (
                    f"API returned unexpected response (model: {effective_model}):\n"
                    f"{json.dumps(result, ensure_ascii=False, indent=2)}"
                )
            return result["choices"][0]["message"]["content"]

        except HTTPError as e:
            err_body = e.read().decode(errors="replace")[:500]
            last_error = f"HTTP {e.code}: {err_body}"
            if e.code in (401, 403):
                break
        except (URLError, OSError) as e:
            last_error = f"Network error: {e}"
        except Exception as e:
            last_error = f"Unexpected error: {e}"

        if attempt < max_retries:
            time.sleep(attempt + 1)

    return (
        f"Request failed\n"
        f"  Endpoint: {api_url}\n"
        f"  Model: {effective_model}\n"
        f"  Reason: {last_error}"
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def describe(image_path: str, prompt: str | None = None, **kwargs: Any) -> str:
    """Describe an image. Returns the model's text response."""
    return _call_api(image_path, prompt or _DEFAULT_PROMPT, **kwargs)


def ask(image_path: str, question: str, **kwargs: Any) -> str:
    """Ask a specific question about an image."""
    return _call_api(image_path, question, **kwargs)


def extract_text(image_path: str, **kwargs: Any) -> str:
    """Extract all readable text from an image (OCR)."""
    prompt = "请逐行输出图片中的所有文字。如果图片中没有文字，请回答'未检测到文字'。"
    return _call_api(image_path, prompt, **kwargs)


def batch_process(
    paths: list[str],
    prompt: str = _DEFAULT_PROMPT,
    **kwargs: Any,
) -> list[dict[str, str]]:
    """Process multiple images with the same prompt.

    Returns a list of ``{"path": ..., "result": ...}`` dicts.
    """
    results: list[dict[str, str]] = []
    for p in paths:
        result = _call_api(p, prompt, **kwargs)
        results.append({"path": p, "result": result})
    return results


def compare(
    paths: list[str],
    question: str = "请比较这些图片，找出它们的主要差异和相似之处。",
    **kwargs: Any,
) -> str:
    """Send multiple images in a single API call with a comparison question.

    The API must support multi-image input (most modern vision models do).
    """
    if len(paths) < 2:
        return "At least 2 images are required for comparison."

    cfg = _resolve()
    api_url = cfg["api_url"]
    api_key = cfg["api_key"]
    effective_model = cfg["model"]

    if kwargs.get("provider"):
        provider = kwargs["provider"]
        if provider in _PRESETS:
            base_url = kwargs.get("base_url")
            api_url = (
                base_url.rstrip("/") + "/chat/completions"
                if base_url
                else _PRESETS[provider]["url"]
            )
            if not kwargs.get("model"):
                effective_model = _PRESETS[provider]["model"]
    if kwargs.get("model"):
        effective_model = kwargs["model"]
    if kwargs.get("base_url"):
        api_url = kwargs["base_url"].rstrip("/") + "/chat/completions"

    if not api_key:
        return "API key not configured. Run: python scripts/configure.py"

    content: list[dict[str, Any]] = []
    for p in paths:
        mime, img_b64 = encode_image(p, max_mb=kwargs.get("max_image_mb", _DEFAULT_MAX_IMAGE_MB))
        content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_b64}"}})
    content.append({"type": "text", "text": question})

    body = json.dumps({
        "model": effective_model,
        "max_tokens": kwargs.get("max_tokens", _DEFAULT_MAX_TOKENS),
        "messages": [{"role": "user", "content": content}],
    }).encode()

    timeout = kwargs.get("timeout", _DEFAULT_TIMEOUT)
    max_retries = kwargs.get("max_retries", _DEFAULT_MAX_RETRIES)

    last_error = ""
    for attempt in range(max_retries + 1):
        try:
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            req = Request(api_url, data=body, headers=headers)
            with urlopen(req, timeout=timeout) as resp:
                result = json.loads(resp.read())
            if "choices" not in result:
                return f"API returned unexpected response:\n{json.dumps(result, ensure_ascii=False, indent=2)}"
            return result["choices"][0]["message"]["content"]
        except HTTPError as e:
            err_body = e.read().decode(errors="replace")[:500]
            last_error = f"HTTP {e.code}: {err_body}"
            if e.code in (401, 403):
                break
        except (URLError, OSError) as e:
            last_error = f"Network error: {e}"
        except Exception as e:
            last_error = f"Unexpected error: {e}"
        if attempt < max_retries:
            time.sleep(attempt + 1)

    return (
        f"Request failed\n"
        f"  Endpoint: {api_url}\n"
        f"  Model: {effective_model}\n"
        f"  Reason: {last_error}"
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _print_help() -> None:
    print("""\
Usage: python image_desc.py <image-path> [prompt] [options]

Arguments:
  <image-path>            Path to the image file (required)
  [prompt]                Custom prompt (default: describes the image)

Options:
  --provider NAME         Service provider: dashscope / openai / gemini /
                          ollama / openrouter / custom
  --model NAME            Model name override
  --base-url URL          Custom API base URL
  --batch                 Process all images in a directory
  --compare               Compare 2+ images (pass multiple paths)
  --setup                 Interactive configuration guide
  --help, -h              Show this help message

Environment variables:
  VL_PROVIDER             Service provider name
  VL_API_KEY              API key
  VL_MODEL                Model name
  VL_BASE_URL             Custom base URL
  VL_MAX_TOKENS           Max tokens per response

Examples:
  # Default description
  python image_desc.py photo.jpg

  # Custom prompt
  python image_desc.py scan.png "Extract all text from this image"

  # Switch provider
  python image_desc.py photo.jpg --provider openai --model gpt-4o

  # Local Ollama
  python image_desc.py photo.jpg --provider ollama

  # Batch process a directory
  python image_desc.py --batch screenshots/ "Describe this screenshot"

  # Compare images
  python image_desc.py --compare img1.jpg img2.jpg "What's different?"
""")


def _print_setup() -> None:
    print("""\
Configuration Guide
===================

Edit ~/.image-desc/config.json or set environment variables.

1. DashScope (阿里云, recommended for China):
   URL: https://dashscope.console.aliyun.com -> API-KEY管理
   Config: {"service": "dashscope", "api_key": "sk-..."}

2. OpenAI:
   URL: https://platform.openai.com/api-keys
   Config: {"service": "openai", "api_key": "sk-proj-..."}

3. Gemini (free tier: 1500/day):
   URL: https://aistudio.google.com/apikey
   Config: {"service": "gemini", "api_key": "AIzaSy..."}

4. Ollama (local, free):
   Install Ollama, then: ollama pull llama3.2-vision:11b
   Config: {"service": "ollama"} (no API key needed)

5. OpenRouter (free models available):
   URL: https://openrouter.ai/keys
   Config: {"service": "openrouter", "api_key": "sk-or-v1-..."}

Or use environment variables (no config file needed):
  set VL_PROVIDER=dashscope
  set VL_API_KEY=sk-...
""")


def main() -> None:
    argv = sys.argv[1:]

    if not argv or "--help" in argv or "-h" in argv:
        _print_help()
        sys.exit(0 if not argv else 0)
    if "--setup" in argv:
        _print_setup()
        sys.exit(0)

    # Parse flags
    provider: str | None = None
    model: str | None = None
    base_url: str | None = None
    batch_mode = False
    compare_mode = False

    i = 0
    while i < len(argv):
        if argv[i] == "--provider" and i + 1 < len(argv):
            provider = argv[i + 1]
            del argv[i : i + 2]
        elif argv[i] == "--model" and i + 1 < len(argv):
            model = argv[i + 1]
            del argv[i : i + 2]
        elif argv[i] == "--base-url" and i + 1 < len(argv):
            base_url = argv[i + 1]
            del argv[i : i + 2]
        elif argv[i] == "--batch":
            batch_mode = True
            del argv[i : i + 1]
        elif argv[i] == "--compare":
            compare_mode = True
            del argv[i : i + 1]
        else:
            i += 1

    kwargs = {}
    if provider:
        kwargs["provider"] = provider
    if model:
        kwargs["model"] = model
    if base_url:
        kwargs["base_url"] = base_url

    if batch_mode:
        if not argv:
            print("Error: --batch requires a directory path or image paths")
            sys.exit(1)
        target = argv[0]
        prompt = argv[1] if len(argv) > 1 else _DEFAULT_PROMPT
        p = Path(target)
        if p.is_dir():
            image_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif"}
            paths = sorted(
                str(f) for f in p.iterdir() if f.suffix.lower() in image_exts
            )
            if not paths:
                print(f"No images found in {target}")
                sys.exit(1)
        else:
            paths = [target] + (argv[2:] if len(argv) > 2 else [])
        results = batch_process(paths, prompt, **kwargs)
        for r in results:
            print(f"=== {r['path']} ===")
            print(r["result"])
            print()

    elif compare_mode:
        if len(argv) < 2:
            print("Error: --compare requires at least 2 image paths")
            sys.exit(1)
        question = argv[2] if len(argv) > 2 else "请比较这些图片，找出它们的主要差异和相似之处。"
        result = compare(argv[:2], question, **kwargs)
        print(result)

    else:
        if not argv:
            _print_help()
            sys.exit(1)
        image_path = argv[0]
        prompt = argv[1] if len(argv) > 1 else _DEFAULT_PROMPT
        try:
            print(describe(image_path, prompt, **kwargs))
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
