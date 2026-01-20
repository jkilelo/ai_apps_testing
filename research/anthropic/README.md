# Anthropic Claude Documentation

Comprehensive documentation for Claude models, SDKs, and capabilities as of January 2026.

## Contents

### Models
- [Claude Models Overview](./claude-models.md) - Opus 4.5, Sonnet 4.5, Haiku 4.5
- [Extended Thinking](./extended-thinking.md) - Enhanced reasoning, budgets, preservation

### SDKs & Tools
- [Anthropic SDK](./anthropic-sdk.md) - Python SDK for Claude API
- [Agent SDK](./agent-sdk.md) - Build autonomous AI agents
- [Claude Code](./claude-code.md) - Agentic coding CLI

### Capabilities
- [Tool Use & Structured Outputs](./tool-use.md) - Function calling, JSON schemas
- [Citations & Files API](./citations-files-api.md) - **NEW** Document grounding, file management
- [Voice & Realtime](./voice-realtime.md) - **NEW** Voice mode, streaming
- [Prompt Caching](./prompt-caching.md) - 90% cost reduction
- [MCP](./mcp.md) - Model Context Protocol
- [Admin API](./admin-api.md) - **NEW** Usage tracking, cost monitoring

## Quick Links

| Resource | URL |
|----------|-----|
| Claude API Docs | https://platform.claude.com/docs |
| Claude Code Docs | https://code.claude.com/docs |
| Python SDK | https://github.com/anthropics/anthropic-sdk-python |
| TypeScript SDK | https://github.com/anthropics/anthropic-sdk-typescript |
| Agent SDK (Python) | https://github.com/anthropics/claude-agent-sdk-python |
| Agent SDK (TypeScript) | https://github.com/anthropics/claude-agent-sdk-typescript |
| MCP Spec | https://modelcontextprotocol.io |
| Console | https://console.anthropic.com |

## Latest Models (January 2026)

| Model | ID | Context | Pricing (MTok) |
|-------|-----|---------|----------------|
| Opus 4.5 | `claude-opus-4-5-20251101` | 200k | $5/$25 |
| Sonnet 4.5 | `claude-sonnet-4-5-20250929` | 200k | $3/$15 |
| Haiku 4.5 | `claude-haiku-4-5-20251001` | 200k | $1/$5 |

## Installation

### Python SDK
```bash
pip install anthropic
```

### TypeScript SDK
```bash
npm install @anthropic-ai/sdk
```

### Agent SDK
```bash
pip install claude-agent-sdk
# or
npm install @anthropic-ai/claude-agent-sdk
```

### Claude Code
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

## Quick Examples

### Basic Message
```python
from anthropic import Anthropic

client = Anthropic()
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.content[0].text)
```

### Extended Thinking
```python
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=16000,
    thinking={"type": "enabled", "budget_tokens": 10000},
    messages=[{"role": "user", "content": "Prove Fermat's Last Theorem"}]
)
```

### With Citations
```python
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    messages=[{
        "role": "user",
        "content": [
            {"type": "document", "source": {...}, "citations": {"enabled": True}},
            {"type": "text", "text": "Summarize this document"}
        ]
    }]
)
```

### Agent SDK
```python
from claude_agent_sdk import query
import anyio

async def main():
    async for msg in query(prompt="Fix the failing tests"):
        print(msg)

anyio.run(main)
```

## Key Features (January 2026)

| Feature | Description |
|---------|-------------|
| **Opus 4.5** | Most intelligent model, thinking preservation |
| **Sonnet 4.5** | Best coding model, 61.4% OSWorld |
| **Extended Thinking** | Up to 128k thinking budget |
| **Citations** | Document grounding with 0% hallucinations |
| **Files API** | 350MB uploads, 365-day retention |
| **Voice Mode** | 38 input languages, 14 TTS voices |
| **Web Search** | $10/1k searches, Brave-powered |
| **Code Execution** | Sandboxed Bash, 50 free hrs/day |
| **Memory Tool** | Persistent cross-session memory |
| **MCP** | 75+ connectors (Linux Foundation) |
| **Agent SDK** | Custom tools, hooks, MCP servers |
| **Structured Outputs** | Guaranteed JSON schemas (beta) |
| **Batches** | 50% discount, 10k requests/batch |

## Cost Optimization

| Method | Savings |
|--------|---------|
| Prompt Caching (read) | 90% |
| Message Batches | 50% |
| Haiku vs Sonnet | 67% |
| Sonnet vs Opus | 80% |
| Combined strategies | 95%+ |

## Beta Features

| Feature | Beta Header |
|---------|-------------|
| Structured Outputs | `structured-outputs-2025-11-13` |
| Code Execution | `code-execution-2025-08-25` |
| Memory Tool | `context-management-2025-06-27` |
| Files API | `files-api-2025-04-14` |
| Computer Use | `computer-use-2025-01-24` |
| Web Search | `web-search-2025-03-05` |

## Platform Availability

| Feature | Anthropic API | Bedrock | Vertex AI |
|---------|---------------|---------|-----------|
| All models | ✓ | ✓ | ✓ |
| Extended thinking | ✓ | ✓ | ✓ |
| Citations | ✓ | ✓ | ✓ |
| Files API | ✓ | ✓ | Coming |
| Web Search | ✓ | Coming | ✓ |
| Memory Tool | ✓ | ✓ | ✓ |

## Safety & Alignment

- **Constitutional AI**: Dynamic principles, RLAIF
- **10B+ fuzz tests**: Adversarial robustness
- **Level 3 safety**: Opus 4 classification
- **SynthID**: AI content watermarking (media)

## Important Notes

- All models: 200k context window
- Extended thinking: All 4.x models
- Legacy SDK deprecated: Use `anthropic` package
- MCP: Linux Foundation (Dec 2025)
- Structured outputs: Beta (Nov 2025)

## Resources

- [Claude 4 Announcement](https://www.anthropic.com/news/claude-4)
- [Opus 4.5 Announcement](https://www.anthropic.com/news/claude-opus-4-5)
- [Sonnet 4.5 Announcement](https://www.anthropic.com/news/claude-sonnet-4-5)
- [Citations API](https://claude.com/blog/introducing-citations-api)
- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
