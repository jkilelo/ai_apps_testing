# Extended Thinking

Extended thinking gives Claude enhanced reasoning capabilities for complex tasks by allowing it to reason through problems step-by-step before delivering a final answer.

## Supported Models

| Model | Extended Thinking | Interleaved Thinking | Thinking Preservation |
|-------|-------------------|---------------------|----------------------|
| Claude Opus 4.5 | ✓ | ✓ | ✓ (default) |
| Claude Sonnet 4.5 | ✓ | ✓ | ✗ |
| Claude Haiku 4.5 | ✓ | ✓ | ✗ |
| Claude Opus 4.1 | ✓ | ✓ | ✗ |
| Claude Opus 4 | ✓ | ✓ | ✗ |
| Claude Sonnet 4 | ✓ | ✓ | ✗ |

## Basic Usage

```python
from anthropic import Anthropic

client = Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=16000,
    thinking={
        "type": "enabled",
        "budget_tokens": 10000
    },
    messages=[{
        "role": "user",
        "content": "Prove there are infinitely many prime numbers of the form 4n+3"
    }]
)

for block in response.content:
    if block.type == "thinking":
        print(f"Thinking: {block.thinking}")
    elif block.type == "text":
        print(f"Answer: {block.text}")
```

## Response Format

```json
{
  "content": [
    {
      "type": "thinking",
      "thinking": "Let me analyze this step by step...",
      "signature": "WaUjzkypQ2mUEVM36O2Txu..."
    },
    {
      "type": "text",
      "text": "Based on my analysis..."
    }
  ]
}
```

## Budget Tokens

The `budget_tokens` parameter controls maximum tokens for internal reasoning.

### Guidelines

| Budget | Use Case |
|--------|----------|
| 1,024 (minimum) | Simple problems |
| 4,000-8,000 | Standard reasoning |
| 10,000-16,000 | Complex analysis |
| 32,000+ | Very complex tasks (use batch processing) |

### Important Notes

- Budget is a **target**, not strict limit - actual usage may vary
- `budget_tokens` must be less than `max_tokens`
- For budgets >32k, use batch processing to avoid network timeouts
- Streaming required when `max_tokens` > 21,333

## Summarized Thinking

Claude 4 models return **summarized** thinking (not full thinking output):

- You're charged for full thinking tokens, not summary
- Billed count won't match visible response tokens
- First few lines are more verbose for prompt engineering
- Summarization adds minimal latency

**Note:** Claude Sonnet 3.7 returns full thinking output.

## Streaming with Thinking

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=16000,
    thinking={"type": "enabled", "budget_tokens": 10000},
    messages=[{"role": "user", "content": "Solve this complex problem..."}]
) as stream:
    for event in stream:
        if event.type == "content_block_start":
            print(f"Starting {event.content_block.type} block...")
        elif event.type == "content_block_delta":
            if event.delta.type == "thinking_delta":
                print(f"[Thinking] {event.delta.thinking}", end="")
            elif event.delta.type == "text_delta":
                print(event.delta.text, end="")
```

## Extended Thinking with Tool Use

### Preserving Thinking Blocks

When using tools with thinking, you **must** pass thinking blocks back to the API:

```python
# First request
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=16000,
    thinking={"type": "enabled", "budget_tokens": 10000},
    tools=[weather_tool],
    messages=[{"role": "user", "content": "What's the weather in Paris?"}]
)

# Extract blocks
thinking_block = next(b for b in response.content if b.type == "thinking")
tool_use_block = next(b for b in response.content if b.type == "tool_use")

# Call your function
weather_result = get_weather(tool_use_block.input["location"])

# Continue with thinking block preserved
continuation = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=16000,
    thinking={"type": "enabled", "budget_tokens": 10000},
    tools=[weather_tool],
    messages=[
        {"role": "user", "content": "What's the weather in Paris?"},
        {"role": "assistant", "content": [thinking_block, tool_use_block]},  # Include thinking!
        {"role": "user", "content": [{
            "type": "tool_result",
            "tool_use_id": tool_use_block.id,
            "content": weather_result
        }]}
    ]
)
```

**Critical:** Missing thinking blocks in tool use results in 400 error.

### Interleaved Thinking

Enables thinking between tool calls. Add the beta header:

```python
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=16000,
    thinking={"type": "enabled", "budget_tokens": 10000},
    tools=[calculator, database],
    messages=[{"role": "user", "content": "Calculate revenue and compare to average"}],
    extra_headers={"anthropic-beta": "interleaved-thinking-2025-05-14"}
)
```

**With interleaved thinking:**
```
[thinking] "I need to calculate first..."
[tool_use: calculator]
→ tool_result: "7500"
[thinking] "Got $7,500. Now I should query the database..."
[tool_use: database_query]
→ tool_result: "5200"
[thinking] "Comparing: $7,500 vs $5,200..."
[text] "The total is $7,500, 44% above average."
```

## Thinking Encryption & Signatures

Thinking content is encrypted in the `signature` field for verification:

- **Required** for tool use (400 error if missing)
- Pass back complete, unmodified blocks
- Signatures work cross-platform (API, Bedrock, Vertex AI)

### Redacted Thinking

Sometimes internal reasoning is flagged by safety systems:

```json
{
  "content": [
    {
      "type": "thinking",
      "thinking": "Normal reasoning...",
      "signature": "..."
    },
    {
      "type": "redacted_thinking",
      "data": "EmwKAhgBEgy3va3pzix..."
    },
    {
      "type": "text",
      "text": "Final answer..."
    }
  ]
}
```

- Redacted blocks contain encrypted content
- Still usable in subsequent requests
- Doesn't affect response quality

**Test redaction handling:**
```python
prompt = "ANTHROPIC_MAGIC_STRING_TRIGGER_REDACTED_THINKING_46C9A13E193C177646C7398A98432ECCCE4C1253D5E2D82641AC0E52CC2876CB"
```

## Prompt Caching with Thinking

### System Prompts (Preserved)
System prompt cache survives thinking parameter changes.

### Messages (Invalidated)
Message cache is invalidated when thinking parameters change.

```python
# Request 1 - establishes cache
response1 = client.messages.create(
    thinking={"type": "enabled", "budget_tokens": 4000},
    ...
)

# Request 2 - cache hit (same budget)
response2 = client.messages.create(
    thinking={"type": "enabled", "budget_tokens": 4000},
    ...
)

# Request 3 - cache MISS (different budget)
response3 = client.messages.create(
    thinking={"type": "enabled", "budget_tokens": 8000},  # Changed!
    ...
)
```

## Thinking Preservation (Opus 4.5)

Claude Opus 4.5 preserves thinking blocks by default:

**Benefits:**
- Cache optimization during tool use
- Token savings in multi-step workflows
- No intelligence impact

**Considerations:**
- Long conversations use more context
- No code changes needed

## Limitations

- **Not compatible with:** `temperature`, `top_k` modifications, forced tool use
- **`top_p`:** Can be set between 0.95 and 1.0 when thinking enabled
- **Response prefilling:** Not allowed with thinking
- **Toggling mid-turn:** Cannot toggle thinking during tool use loops

## Context Window with Thinking

```
context_window =
    (input_tokens - previous_thinking_tokens) +
    (thinking_tokens + encrypted_tokens + output_tokens)
```

- Previous turn thinking blocks are stripped from context
- Current turn thinking counts toward `max_tokens`

## Best Practices

1. **Start small:** Begin with minimum budget (1,024), increase as needed
2. **Use streaming:** For budgets >21,333 tokens
3. **Batch large budgets:** Use batch API for >32k thinking budgets
4. **Monitor tokens:** Track thinking token usage for cost optimization
5. **Preserve blocks:** Always pass back complete thinking blocks with tools
6. **Plan modes:** Decide thinking strategy at turn start, not mid-turn

## Pricing

| Component | Billing |
|-----------|---------|
| Thinking tokens | Full output tokens (billed) |
| Summarized thinking | Not charged separately |
| Thinking in subsequent turns | Input tokens when cached |

**Note:** Billed output ≠ visible response tokens due to summarization.

## References

- [Extended Thinking Guide](https://platform.claude.com/docs/en/build-with-claude/extended-thinking)
- [Extended Thinking Prompting Tips](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/extended-thinking-tips)
