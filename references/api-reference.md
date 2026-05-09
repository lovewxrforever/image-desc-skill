# image-desc-skill API Reference

This document details the API endpoints, request/response formats, and
configuration options for each supported provider.

## OpenAI-Compatible API Format

All providers use the OpenAI chat completions format:

```
POST /v1/chat/completions
Content-Type: application/json
Authorization: Bearer <api-key>

{
  "model": "model-name",
  "max_tokens": 4096,
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,<b64>"}},
        {"type": "text", "text": "Describe this image"}
      ]
    }
  ]
}
```

Response:
```json
{
  "choices": [
    {
      "message": {
        "content": "This image shows..."
      }
    }
  ]
}
```

## Provider Details

### DashScope (阿里云)

- **Endpoint**: `https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions`
- **Models**: qwen3.5-flash (default), qwen-plus, qwen-max, qwen-vl-max
- **Auth**: Bearer token (sk-...)
- **Notes**: Fast and cheap for Chinese content. No VPN needed in China.
- **Console**: https://dashscope.console.aliyun.com

### OpenAI

- **Endpoint**: `https://api.openai.com/v1/chat/completions`
- **Models**: gpt-4o-mini (default), gpt-4o, gpt-4.1-mini
- **Auth**: Bearer token (sk-proj-...)
- **Notes**: Best quality. Requires international access.
- **Console**: https://platform.openai.com/api-keys

### Google Gemini

- **Endpoint**: `https://generativelanguage.googleapis.com/v1beta/openai/chat/completions`
- **Models**: gemini-2.5-flash (default), gemini-2.5-pro
- **Auth**: Bearer token (AIzaSy...)
- **Notes**: 1500 free requests/day. Requires VPN in China.
- **Console**: https://aistudio.google.com/apikey

### Ollama (Local)

- **Endpoint**: `http://localhost:11434/v1/chat/completions`
- **Models**: llama3.2-vision:11b (default), qwen2-vl:7b, minicpm-v:8b
- **Auth**: None required
- **Notes**: Fully offline. Requires GPU for good performance.
- **Install**: https://ollama.com/download

### OpenRouter

- **Endpoint**: `https://openrouter.ai/api/v1/chat/completions`
- **Models**: qwen/qwen2.5-vl-72b-instruct:free (default), claude-sonnet-4-6
- **Auth**: Bearer token (sk-or-v1-...)
- **Notes**: Aggregates many providers. Free models available.
- **Console**: https://openrouter.ai/keys

## Configuration File Format

Location: `~/.image-desc/config.json`

```json
{
  "service": "dashscope",
  "api_key": "sk-...",
  "model": "qwen3.5-flash",
  "base_url": ""
}
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| VL_PROVIDER | Service provider name |
| VL_API_KEY | API key |
| VL_MODEL | Model name |
| VL_BASE_URL | Custom API base URL |
| VL_MAX_TOKENS | Max tokens (default: 4096) |
| DASHSCOPE_API_KEY | DashScope-specific key fallback |
| OPENAI_API_KEY | OpenAI-specific key fallback |
| DASHSCOPE_VL_MODEL | DashScope model fallback |

## Image Size Limits

- Default max: 20MB per image
- Supported formats: JPEG, PNG, WebP, BMP, TIFF, GIF, ICO, SVG
- Images are base64 encoded and sent inline in the request body

## Error Codes

| HTTP Code | Meaning | Handling |
|-----------|---------|----------|
| 401 | Unauthorized (bad key) | Stop retry, prompt reconfiguration |
| 403 | Forbidden | Stop retry, check permissions |
| 429 | Rate limited | Auto-retry with backoff |
| 500+ | Server error | Auto-retry with backoff |
| Timeout | Network issue | Auto-retry with backoff |
