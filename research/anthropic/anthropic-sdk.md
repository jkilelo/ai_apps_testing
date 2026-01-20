# Anthropic Python SDK

The official Python SDK for accessing the Claude API. Version 0.76.0 (January 2026).

## Installation

```bash
pip install anthropic
```

Optional extras:
```bash
pip install anthropic[aiohttp]      # Async HTTP support
pip install anthropic[bedrock]      # AWS Bedrock integration
pip install anthropic[vertex]       # Google Vertex AI integration
```

**Requirements:** Python 3.9+

## Client Setup

### Basic Setup

```python
from anthropic import Anthropic

# Using environment variable ANTHROPIC_API_KEY
client = Anthropic()

# Explicit API key
client = Anthropic(api_key="your-api-key")
```

### AWS Bedrock

```python
from anthropic import AnthropicBedrock

client = AnthropicBedrock(
    aws_profile='your-profile',
    aws_region='us-east-1'
)

response = client.messages.create(
    model="anthropic.claude-sonnet-4-5-20250929-v1:0",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Google Vertex AI

```python
from anthropic import AnthropicVertex

client = AnthropicVertex()

response = client.messages.create(
    model="claude-sonnet-4@20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Basic Usage

### Simple Message

```python
from anthropic import Anthropic

client = Anthropic()

message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Explain recursion in programming"}
    ]
)

print(message.content[0].text)
```

### With System Prompt

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    system="You are a helpful coding assistant. Be concise.",
    messages=[
        {"role": "user", "content": "How do I read a file in Python?"}
    ]
)
```

### Multi-turn Conversation

```python
messages = [
    {"role": "user", "content": "What is Python?"},
    {"role": "assistant", "content": "Python is a high-level programming language..."},
    {"role": "user", "content": "What are its main uses?"}
]

response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=messages
)
```

## Async Support

```python
import asyncio
from anthropic import AsyncAnthropic

client = AsyncAnthropic()

async def main():
    message = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(message.content[0].text)

asyncio.run(main())
```

## Streaming

### Synchronous Streaming

```python
stream = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a story"}],
    stream=True
)

for event in stream:
    if event.type == "content_block_delta":
        print(event.delta.text, end="", flush=True)
```

### Stream Helper

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a poem"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)

    # Get final message
    final_message = stream.get_final_message()
```

### Async Streaming

```python
async with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
) as stream:
    async for text in stream.text_stream:
        print(text, end="", flush=True)
```

## Tool Use (Function Calling)

### Using the @beta_tool Decorator

```python
import json
from anthropic import Anthropic, beta_tool

client = Anthropic()

@beta_tool
def get_weather(location: str) -> str:
    """Get the current weather for a location.

    Args:
        location: The city and state, e.g. San Francisco, CA

    Returns:
        Weather information as JSON string
    """
    return json.dumps({
        "location": location,
        "temperature": "72°F",
        "condition": "Sunny"
    })

runner = client.beta.messages.tool_runner(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[get_weather],
    messages=[{"role": "user", "content": "What's the weather in NYC?"}]
)

for message in runner:
    print(message)
```

### Manual Tool Definition

```python
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[
        {
            "name": "get_stock_price",
            "description": "Get the current stock price for a ticker symbol",
            "input_schema": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., AAPL)"
                    }
                },
                "required": ["ticker"]
            }
        }
    ],
    messages=[{"role": "user", "content": "What's Apple's stock price?"}]
)

# Check if tool use was requested
for block in response.content:
    if block.type == "tool_use":
        print(f"Tool: {block.name}")
        print(f"Input: {block.input}")
```

## Extended Thinking

Enable enhanced reasoning for complex tasks:

```python
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=16000,
    thinking={
        "type": "enabled",
        "budget_tokens": 10000
    },
    messages=[{"role": "user", "content": "Prove that there are infinitely many primes"}]
)

for block in response.content:
    if block.type == "thinking":
        print(f"Thinking: {block.thinking[:200]}...")
    elif block.type == "text":
        print(f"Answer: {block.text}")
```

### Streaming with Thinking

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=16000,
    thinking={"type": "enabled", "budget_tokens": 10000},
    messages=[{"role": "user", "content": "Solve this problem..."}]
) as stream:
    for event in stream:
        if event.type == "content_block_delta":
            if event.delta.type == "thinking_delta":
                print(f"[Thinking] {event.delta.thinking}", end="")
            elif event.delta.type == "text_delta":
                print(event.delta.text, end="")
```

## Computer Use (Beta)

```python
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[
        {
            "type": "computer_20250124",
            "name": "computer",
            "display_width_px": 1920,
            "display_height_px": 1080,
            "display_number": 1
        },
        {
            "type": "text_editor_20250728",
            "name": "str_replace_based_edit_tool"
        },
        {
            "type": "bash_20250124",
            "name": "bash"
        }
    ],
    messages=[{"role": "user", "content": "Take a screenshot of the desktop"}],
    betas=["computer-use-2025-01-24"]
)
```

## Message Batches

For high-volume processing:

```python
# Create batch
batch = client.messages.batches.create(
    requests=[
        {
            "custom_id": "request-1",
            "params": {
                "model": "claude-sonnet-4-5-20250929",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello"}]
            }
        },
        {
            "custom_id": "request-2",
            "params": {
                "model": "claude-sonnet-4-5-20250929",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "World"}]
            }
        }
    ]
)

# Get results
for entry in client.messages.batches.results(batch.id):
    if entry.result.type == "succeeded":
        print(f"{entry.custom_id}: {entry.result.message.content[0].text}")
```

## Token Counting

```python
count = client.messages.count_tokens(
    model="claude-sonnet-4-5-20250929",
    messages=[{"role": "user", "content": "Hello, world!"}]
)

print(f"Input tokens: {count.input_tokens}")

# After a response
response = client.messages.create(...)
print(f"Usage: {response.usage}")
# Usage(input_tokens=25, output_tokens=150)
```

## Error Handling

```python
import anthropic

try:
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello"}]
    )
except anthropic.APIConnectionError as e:
    print(f"Connection failed: {e.__cause__}")
except anthropic.RateLimitError as e:
    print("Rate limited - implement backoff")
except anthropic.APIStatusError as e:
    print(f"API error {e.status_code}: {e.message}")
```

## Configuration

### Retries

```python
# Global retry configuration
client = Anthropic(max_retries=5)

# Per-request retry
client.with_options(max_retries=10).messages.create(...)
```

### Timeouts

```python
# Global timeout (default: 10 minutes)
client = Anthropic(timeout=30.0)

# Per-request timeout
client.with_options(timeout=60.0).messages.create(...)
```

### Logging

```bash
export ANTHROPIC_LOG=info    # Info level
export ANTHROPIC_LOG=debug   # Debug level
```

## Raw Response Access

```python
response = client.messages.with_raw_response.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
)

print(response.headers.get("x-request-id"))
message = response.parse()
print(message.content[0].text)
```

## Pagination

```python
# Auto-pagination
for batch in client.messages.batches.list(limit=20):
    print(batch.id)

# Async pagination
async for batch in client.messages.batches.list(limit=20):
    print(batch.id)
```

## HTTP Client Configuration

```python
import httpx
from anthropic import Anthropic, DefaultHttpxClient

client = Anthropic(
    http_client=DefaultHttpxClient(
        proxy="http://proxy.example.com:8080",
        transport=httpx.HTTPTransport(local_address="0.0.0.0")
    )
)
```

## Context Manager

```python
with Anthropic() as client:
    response = client.messages.create(...)
# Resources automatically cleaned up
```

## References

- [GitHub Repository](https://github.com/anthropics/anthropic-sdk-python)
- [PyPI Package](https://pypi.org/project/anthropic/)
- [API Documentation](https://platform.claude.com/docs)
