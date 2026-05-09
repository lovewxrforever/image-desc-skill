"""
image-desc configuration wizard.

Guides the user through setting up API keys for vision providers
and writes the config to ``~/.image-desc/config.json``.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

CONFIG_DIR = Path.home() / ".image-desc"
CONFIG_PATH = CONFIG_DIR / "config.json"

PROVIDERS = {
    "dashscope": {
        "name": "DashScope (阿里云)",
        "desc": "国内首选，便宜，中文理解强",
        "url": "https://dashscope.console.aliyun.com",
        "key_hint": "sk-",
        "default_model": "qwen3.5-flash",
    },
    "openai": {
        "name": "OpenAI",
        "desc": "效果最好，较贵",
        "url": "https://platform.openai.com/api-keys",
        "key_hint": "sk-proj-",
        "default_model": "gpt-4o-mini",
    },
    "gemini": {
        "name": "Google Gemini",
        "desc": "免费额度大（1500次/天），需科学上网",
        "url": "https://aistudio.google.com/apikey",
        "key_hint": "AIzaSy",
        "default_model": "gemini-2.5-flash",
    },
    "ollama": {
        "name": "Ollama (本地)",
        "desc": "免费，无需联网，需 GPU",
        "url": "https://ollama.com/download",
        "key_hint": None,
        "default_model": "llama3.2-vision:11b",
    },
    "openrouter": {
        "name": "OpenRouter",
        "desc": "API 聚合站，有免费模型",
        "url": "https://openrouter.ai/keys",
        "key_hint": "sk-or-v1-",
        "default_model": "qwen/qwen2.5-vl-72b-instruct:free",
    },
}


def _read_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _write_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Config saved to: {CONFIG_PATH}")


def _list_providers() -> None:
    print("\nSupported providers:\n")
    for key, info in PROVIDERS.items():
        model_info = f"  Default model: {info['default_model']}"
        key_info = f"  Key prefix: {info['key_hint']}" if info["key_hint"] else "  No API key needed"
        print(f"  [{key}] {info['name']}")
        print(f"  {info['desc']}")
        print(f"  Register: {info['url']}")
        print(model_info)
        print(key_info)
        print()


def _interactive_setup(provider_name: str | None = None) -> None:
    config = _read_config()

    if provider_name and provider_name not in PROVIDERS:
        print(f"Unknown provider: {provider_name}")
        _list_providers()
        sys.exit(1)

    if not provider_name:
        _list_providers()
        print("Enter the provider name (or leave empty for dashscope):")
        provider_name = input("  Provider: ").strip().lower()
        if not provider_name:
            provider_name = "dashscope"
        if provider_name not in PROVIDERS:
            print(f"Unknown provider: {provider_name}")
            sys.exit(1)

    info = PROVIDERS[provider_name]
    print(f"\nConfiguring: {info['name']}")

    config["service"] = provider_name

    if info["key_hint"]:
        current_key = config.get("api_key", "")
        prompt_text = f"  API Key (prefix: {info['key_hint']})"
        if current_key:
            prompt_text += f" [current: {current_key[:8]}...]"
        print(f"  Get your key at: {info['url']}")
        key = input(f"  {prompt_text}: ").strip()
        if key:
            config["api_key"] = key
    else:
        config.pop("api_key", None)

    current_model = config.get("model", "")
    model_prompt = f"  Model [default: {info['default_model']}]"
    if current_model:
        model_prompt += f" [current: {current_model}]"
    model = input(f"  {model_prompt}: ").strip()
    if model:
        config["model"] = model
    elif "model" in config and not current_model:
        config["model"] = info["default_model"]

    custom_url = input("  Custom base URL (optional, or leave empty): ").strip()
    if custom_url:
        config["base_url"] = custom_url
    else:
        config.pop("base_url", None)

    _write_config(config)
    print(f"\nDone! Provider '{provider_name}' configured successfully.")
    print(f"You can now run: python scripts/image_desc.py <image-path>")


def _env_var_guide() -> None:
    print("""
Environment Variable Configuration
===================================

Set these in your terminal profile (~/.bashrc, ~/.zshrc, or system env):

  # Windows (PowerShell)
  $env:VL_PROVIDER = "dashscope"
  $env:VL_API_KEY = "sk-..."
  $env:VL_MODEL = "qwen3.5-flash"

  # Linux / macOS
  export VL_PROVIDER="dashscope"
  export VL_API_KEY="sk-..."
  export VL_MODEL="qwen3.5-flash"

You can also use provider-specific env vars:
  DASHSCOPE_API_KEY    - DashScope only
  OPENAI_API_KEY       - OpenAI only
""")


def main() -> None:
    print("=" * 56)
    print("  image-desc Configuration Wizard")
    print("=" * 56)

    args = sys.argv[1:]

    if "--list" in args:
        _list_providers()
        return
    if "--env" in args:
        _env_var_guide()
        return

    provider = None
    for i, arg in enumerate(args):
        if arg == "--provider" and i + 1 < len(args):
            provider = args[i + 1]
        elif arg == "--interactive" or arg == "-i":
            pass  # default mode is interactive

    if "--non-interactive" in args or "-y" in args:
        # Quick setup with defaults
        provider = provider or "dashscope"
        _interactive_setup(provider)
    else:
        _interactive_setup(provider)


if __name__ == "__main__":
    main()
