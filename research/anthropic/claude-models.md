# Claude Models Overview

This document covers the latest Claude model family as of January 2026, including the Claude 4 and 4.5 series.

## Current Models

### Claude Opus 4.5 (November 24, 2025)

The most intelligent Claude model, optimized for complex reasoning and analysis.

| Specification | Value |
|---------------|-------|
| Model ID | `claude-opus-4-5-20251101` |
| Context Window | 200,000 tokens |
| Max Output | 128,000 tokens |
| Input Price | $5/MTok |
| Output Price | $25/MTok |

**Key Capabilities:**
- State-of-the-art reasoning and analysis
- Extended thinking with thinking block preservation
- Computer use with zoom action (`computer_20251124`)
- 67% lower cost than Opus 4

### Claude Sonnet 4.5 (September 29, 2025)

The best coding model in the world. Optimal balance of intelligence, speed, and cost.

| Specification | Value |
|---------------|-------|
| Model ID | `claude-sonnet-4-5-20250929` |
| Context Window | 200,000 tokens |
| Max Output | 128,000 tokens |
| Input Price (≤200k) | $3/MTok |
| Output Price (≤200k) | $15/MTok |
| Input Price (>200k) | $6/MTok |
| Output Price (>200k) | $22.50/MTok |

**Key Capabilities:**
- #1 on OSWorld benchmark (61.4%)
- Best model for building complex agents
- Best model for computer use
- Substantial gains in reasoning and math

### Claude Haiku 4.5

Fastest and most cost-efficient model with near-frontier coding quality.

| Specification | Value |
|---------------|-------|
| Model ID | `claude-haiku-4-5-20251001` |
| Context Window | 200,000 tokens |
| Max Output | 128,000 tokens |
| Input Price | $1/MTok |
| Output Price | $5/MTok |

**Key Capabilities:**
- Matches Sonnet 4 on coding benchmarks
- Surpasses Sonnet 4 on some computer-use tasks
- Ideal for high-volume, latency-sensitive applications

## Legacy Models

### Claude Opus 4.1 (August 5, 2025)
- Model ID: `claude-opus-4-1-20250805`
- Focus: Agentic tasks, real-world coding, reasoning
- Pricing: $15/$75 per MTok

### Claude Sonnet 4 (May 22, 2025)
- Model ID: `claude-sonnet-4-20250514`
- Benchmarks: 72.7% on SWE-bench
- Pricing: $3/$15 per MTok

### Claude Opus 4 (May 22, 2025)
- Model ID: `claude-opus-4-20250514`
- Benchmarks: 72.5% SWE-bench, 43.2% Terminal-bench
- Classified as "Level 3" safety risk
- Pricing: $15/$75 per MTok

## Benchmarks Comparison

| Model | SWE-bench | OSWorld | GPQA Diamond |
|-------|-----------|---------|--------------|
| Opus 4.5 | - | - | 93.8% (Deep Think) |
| Sonnet 4.5 | - | 61.4% | 91.9% |
| Sonnet 4 | 72.7% | 42.2% | - |
| Opus 4 | 72.5% | - | - |

## Extended Thinking Support

All 4.x models support extended thinking:

| Model | Thinking | Interleaved Thinking | Thinking Preservation |
|-------|----------|---------------------|----------------------|
| Opus 4.5 | ✓ | ✓ | ✓ (default) |
| Sonnet 4.5 | ✓ | ✓ | ✗ |
| Haiku 4.5 | ✓ | ✓ | ✗ |
| Opus 4.1 | ✓ | ✓ | ✗ |
| Opus 4 | ✓ | ✓ | ✗ |
| Sonnet 4 | ✓ | ✓ | ✗ |

## Computer Use Tool Versions

| Model | Tool Version | Beta Header |
|-------|--------------|-------------|
| Opus 4.5 | `computer_20251124` | `computer-use-2025-01-24` |
| All others | `computer_20250124` | `computer-use-2025-01-24` |

## Model Selection Guide

| Use Case | Recommended Model |
|----------|-------------------|
| Complex reasoning, research | Opus 4.5 |
| Production coding, agents | Sonnet 4.5 |
| High-volume, cost-sensitive | Haiku 4.5 |
| Simple tasks, chatbots | Haiku 4.5 |
| Computer automation | Sonnet 4.5 / Opus 4.5 |

## Prompt Caching Pricing

| Model | Cache Write | Cache Read |
|-------|-------------|------------|
| Opus 4.5 | $6.25/MTok | $0.50/MTok |
| Sonnet 4.5 (≤200k) | $3.75/MTok | $0.30/MTok |
| Sonnet 4.5 (>200k) | $7.50/MTok | $0.60/MTok |
| Haiku 4.5 | $1.25/MTok | $0.10/MTok |

## Additional Features Pricing

| Feature | Price |
|---------|-------|
| Web Search | $10 per 1,000 searches |
| Code Execution | 50 free hours/day, then $0.05/hour |

## API Usage

```python
from anthropic import Anthropic

client = Anthropic()

# Using the latest Sonnet
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    messages=[
        {"role": "user", "content": "Explain quantum computing"}
    ]
)

# Using shorthand (resolves to latest)
response = client.messages.create(
    model="claude-sonnet-4-5",  # Resolves to claude-sonnet-4-5-20250929
    max_tokens=4096,
    messages=[...]
)
```

## References

- [Claude 4 Announcement](https://www.anthropic.com/news/claude-4)
- [Claude Opus 4.5 Announcement](https://www.anthropic.com/news/claude-opus-4-5)
- [Claude Sonnet 4.5 Announcement](https://www.anthropic.com/news/claude-sonnet-4-5)
- [Models Documentation](https://platform.claude.com/docs/en/about-claude/models/overview)
