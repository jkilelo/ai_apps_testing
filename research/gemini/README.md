# Gemini & Google GenAI Documentation

Comprehensive documentation for Google's Gemini AI models, SDKs, and developer tools as of January 2026.

## Contents

### Models
- [Gemini 3 Overview](./gemini-3-overview.md) - Model variants, capabilities, and benchmarks
- [Gemini 3 API Reference](./gemini-3-api-reference.md) - Parameters, thinking levels, configuration

### SDKs
- [SDK Quickstart](./sdk-quickstart.md) - Python installation, setup, basic usage
- [Advanced Features](./sdk-advanced-features.md) - Async, streaming, caching, files

### Developer Tools
- [Gemini CLI](./gemini-cli.md) - **NEW** Open-source terminal AI agent
- [ADK & Agent Builder](./adk-agent-builder.md) - **NEW** Multi-agent systems, A2A protocol
- [Function Calling & Tools](./function-calling.md) - Tool integration, code execution

### Media & Realtime
- [Image Generation](./image-generation.md) - Nano Banana Pro, text rendering
- [Media Generation](./media-generation.md) - **NEW** Veo 3.1, Imagen 3, Flow
- [Live API](./live-api.md) - **NEW** Real-time voice and video

## Quick Links

| Resource | URL |
|----------|-----|
| Google AI Studio | https://aistudio.google.com |
| Gemini API Docs | https://ai.google.dev/gemini-api/docs |
| Vertex AI | https://cloud.google.com/vertex-ai |
| GenAI SDK (Python) | https://github.com/googleapis/python-genai |
| GenAI SDK (JS/TS) | https://github.com/googleapis/js-genai |
| Gemini CLI | https://github.com/google-gemini/gemini-cli |
| ADK Docs | https://google.github.io/adk-docs |
| A2A Protocol | https://a2a-protocol.org |

## Latest Models (January 2026)

| Model | ID | Context | Pricing (MTok) |
|-------|-----|---------|----------------|
| Gemini 3 Pro | `gemini-3-pro-preview` | 1M | $2/$12 (≤200k) |
| Gemini 3 Flash | `gemini-3-flash-preview` | 1M | $0.50/$3 |
| Gemini 3 Pro Image | `gemini-3-pro-image-preview` | 65k | $2 + $0.13/img |
| Gemini 2.5 Flash | `gemini-2.5-flash` | 1M | $0.15/$0.60 |

**Note:** Gemini 2.0 Flash/Flash-Lite retiring March 3, 2026.

## Installation

### Python SDK
```bash
pip install google-genai
```

### JavaScript/TypeScript SDK
```bash
npm install @google/genai
```

### Gemini CLI
```bash
npm install -g @google/gemini-cli
# Free: 1,000 requests/day with personal Google account
```

## Quick Examples

### Basic Generation
```python
from google import genai

client = genai.Client(api_key='YOUR_API_KEY')
response = client.models.generate_content(
    model='gemini-3-flash-preview',
    contents='Explain quantum computing'
)
print(response.text)
```

### With Thinking
```python
from google.genai import types

response = client.models.generate_content(
    model='gemini-3-flash-preview',
    contents='Solve this complex math problem...',
    config=types.GenerateContentConfig(
        thinking_level='high'
    )
)
```

### Gemini CLI
```bash
gemini "fix the failing tests"
```

## Key Features (January 2026)

| Feature | Description |
|---------|-------------|
| **Gemini 3** | State-of-the-art reasoning, 1M context |
| **Thinking Levels** | Configurable reasoning depth |
| **Gemini CLI** | Open-source terminal agent (Apache 2.0) |
| **ADK** | Agent Development Kit (7M+ downloads) |
| **A2A Protocol** | Cross-agent communication standard |
| **Live API** | Real-time voice/video (24 languages) |
| **Veo 3.1** | Video generation with audio |
| **Flow** | AI filmmaking platform |
| **Batch API** | 50% discount, async processing |
| **Context Caching** | Cost optimization for large contexts |

## Platform Comparison

| Feature | AI Studio | Vertex AI |
|---------|-----------|-----------|
| Free tier | ✓ (training data used) | Pay-as-you-go |
| Enterprise features | Limited | Full |
| Agent Engine | ✗ | ✓ |
| SLA | ✗ | ✓ |
| Compliance | Basic | Full |

## Cost Optimization

| Method | Savings |
|--------|---------|
| Batch API | 50% |
| Context Caching | Up to 90% |
| Flash vs Pro | 75%+ |
| Low media resolution | ~67% |

## Model Retirement Timeline

| Model | Retirement Date |
|-------|-----------------|
| Gemini 2.0 Flash | March 3, 2026 |
| Gemini 2.0 Flash-Lite | March 3, 2026 |

**Action:** Migrate to `gemini-2.5-flash-lite` or newer.

## Important Dates

| Date | Event |
|------|-------|
| Nov 18, 2025 | Gemini 3 released |
| Jan 5, 2026 | Grounding billing starts |
| Jan 28, 2026 | Agent Engine services billing |
| Mar 3, 2026 | Gemini 2.0 retirement |

## Resources

- [Gemini 3 Announcement](https://blog.google/products/gemini/gemini-3/)
- [A2A Protocol Launch](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/)
- [Gemini CLI Announcement](https://blog.google/technology/developers/introducing-gemini-cli-open-source-ai-agent/)
- [Live API GA](https://cloud.google.com/blog/products/ai-machine-learning/build-voice-driven-applications-with-live-api)
