# Prompt Caching

Prompt caching reduces costs by up to 90% and latency by up to 85% for long prompts by allowing you to cache and reuse prompt prefixes.

## Overview

When enabled, the system:
1. Checks if a prompt prefix is already cached
2. Uses the cached version if found (cache hit)
3. Otherwise processes the full prompt and caches the prefix (cache miss)

**Status:** Generally Available on Anthropic API, Preview on Bedrock and Vertex AI

## Supported Models

| Model | Minimum Cacheable Tokens |
|-------|-------------------------|
| Claude Opus 4.5 | 4,096 |
| Claude Opus 4.1 | 1,024 |
| Claude Opus 4 | 1,024 |
| Claude Sonnet 4.5 | 1,024 |
| Claude Sonnet 4 | 1,024 |
| Claude Haiku 4.5 | 4,096 |
| Claude Haiku 3.5 | 2,048 |
| Claude Haiku 3 | 2,048 |

## Pricing

| Model | Base Input | 5m Cache Write | 1h Cache Write | Cache Read |
|-------|------------|----------------|----------------|------------|
| Opus 4.5 | $5/MTok | $6.25/MTok | $10/MTok | $0.50/MTok |
| Sonnet 4.5 | $3/MTok | $3.75/MTok | $6/MTok | $0.30/MTok |
| Haiku 4.5 | $1/MTok | $1.25/MTok | $2/MTok | $0.10/MTok |

**Pricing Multipliers:**
- 5-minute cache write: 1.25x base input
- 1-hour cache write: 2x base input
- Cache read: 0.1x base input (90% savings!)

## Basic Implementation

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": "You are a helpful assistant."
        },
        {
            "type": "text",
            "text": "<entire contents of a large document>",
            "cache_control": {"type": "ephemeral"}  # Cache this!
        }
    ],
    messages=[
        {"role": "user", "content": "Summarize the document."}
    ]
)

print(response.usage)
# cache_creation_input_tokens: 50000 (first request)
# cache_read_input_tokens: 0

# Second request with same prefix
response2 = client.messages.create(...)
print(response2.usage)
# cache_creation_input_tokens: 0
# cache_read_input_tokens: 50000 (cache hit!)
```

## Cache TTL Options

### 5-Minute Cache (Default)
```python
"cache_control": {"type": "ephemeral"}
# or explicitly:
"cache_control": {"type": "ephemeral", "ttl": "5m"}
```

### 1-Hour Cache
```python
"cache_control": {"type": "ephemeral", "ttl": "1h"}
```

**When to use 1-hour cache:**
- Requests arrive less frequently than every 5 minutes
- Agentic workflows taking >5 minutes
- Long conversations with infrequent responses
- Latency-sensitive applications

## What Can Be Cached

| Content Type | Cacheable |
|-------------|-----------|
| Tool definitions | ✓ |
| System messages | ✓ |
| User/assistant messages | ✓ |
| Images & documents | ✓ |
| Tool use & results | ✓ |
| Thinking blocks | ✓ (automatically, not directly) |
| Citations sub-blocks | ✗ (cache parent block) |
| Empty text blocks | ✗ |

## Cache Breakpoints

You can define up to **4 cache breakpoints** using `cache_control`.

### Single Breakpoint (Most Common)
```python
system=[
    {"type": "text", "text": "Instructions..."},
    {"type": "text", "text": "Large context...", "cache_control": {"type": "ephemeral"}}
]
```

### Multiple Breakpoints
```python
# Breakpoint 1: Tools (rarely change)
tools=[
    {...},
    {..., "cache_control": {"type": "ephemeral"}}  # Cache all tools
]

# Breakpoint 2: System instructions (rarely change)
system=[
    {"type": "text", "text": "Instructions...", "cache_control": {"type": "ephemeral"}},
    # Breakpoint 3: RAG context (changes daily)
    {"type": "text", "text": "Documents...", "cache_control": {"type": "ephemeral"}}
]

# Breakpoint 4: Conversation history
messages=[
    ...,
    {"role": "user", "content": [..., {"type": "text", "text": "...", "cache_control": {"type": "ephemeral"}}]}
]
```

## Cache Invalidation

| Change | Tools Cache | System Cache | Messages Cache |
|--------|-------------|--------------|----------------|
| Tool definitions | ✗ | ✗ | ✗ |
| Web search toggle | ✓ | ✗ | ✗ |
| Citations toggle | ✓ | ✗ | ✗ |
| Tool choice | ✓ | ✓ | ✗ |
| Images | ✓ | ✓ | ✗ |
| Thinking parameters | ✓ | ✓ | ✗ |

## Monitoring Cache Performance

```python
response = client.messages.create(...)

usage = response.usage
print(f"Cache read: {usage.cache_read_input_tokens}")
print(f"Cache write: {usage.cache_creation_input_tokens}")
print(f"Uncached input: {usage.input_tokens}")

# Total input = cache_read + cache_creation + input_tokens
total = usage.cache_read_input_tokens + usage.cache_creation_input_tokens + usage.input_tokens
```

**Note:** `input_tokens` only includes tokens *after* the last cache breakpoint.

## Multi-Turn Conversation Caching

```python
# Turn 1
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    system=[{"type": "text", "text": "...", "cache_control": {"type": "ephemeral"}}],
    messages=[
        {"role": "user", "content": "First question"}
    ]
)

# Turn 2 - cache the growing conversation
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    system=[{"type": "text", "text": "...", "cache_control": {"type": "ephemeral"}}],
    messages=[
        {"role": "user", "content": "First question"},
        {"role": "assistant", "content": response.content[0].text},
        {"role": "user", "content": [
            {"type": "text", "text": "Second question", "cache_control": {"type": "ephemeral"}}
        ]}
    ]
)
```

## Caching with Extended Thinking

Thinking blocks are cached automatically when passed back in tool use flows:

```python
# Request 1
response = client.messages.create(
    thinking={"type": "enabled", "budget_tokens": 10000},
    tools=[...],
    messages=[{"role": "user", "content": "Use tool X"}]
)
# Response: [thinking_block] + [tool_use block]

# Request 2 - thinking block automatically cached
response = client.messages.create(
    thinking={"type": "enabled", "budget_tokens": 10000},
    tools=[...],
    messages=[
        {"role": "user", "content": "Use tool X"},
        {"role": "assistant", "content": [thinking_block, tool_use_block]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "...", "content": "result"},
            # Adding cache_control here
        ]}
    ]
)
```

**Note:** Non-tool-result user messages invalidate thinking block caches.

## Best Practices

1. **Place static content first** - Tools, system instructions, large contexts
2. **Cache stable content** - Instructions, documents, tool definitions
3. **Use breakpoints strategically** - Separate content that changes at different rates
4. **Monitor cache hits** - Track `cache_read_input_tokens` to optimize
5. **Avoid caching user input** - Variable content reduces cache hits

## Use Cases

| Use Case | Approach |
|----------|----------|
| Document Q&A | Cache entire document in system |
| Coding assistant | Cache codebase context |
| Conversational agents | Cache system + incrementally cache conversation |
| Tool-heavy agents | Cache tool definitions |
| RAG applications | Cache retrieved documents |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No cache hits | Ensure identical content up to breakpoint |
| Cache expired | Requests within 5 min (or 1 hour) |
| Too few tokens | Meet minimum threshold (1024-4096) |
| `tool_choice` changed | Keep consistent between requests |
| Images added/removed | Keep image presence consistent |

## References

- [Prompt Caching Documentation](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Prompt Caching Cookbook](https://platform.claude.com/cookbook/misc-prompt-caching)
