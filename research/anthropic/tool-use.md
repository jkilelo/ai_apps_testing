# Tool Use & Structured Outputs

Claude can interact with external systems through tool use (function calling) and generate guaranteed-valid structured outputs.

## Tool Use Overview

Claude doesn't execute tools directly. Instead:
1. Claude signals intent to use a tool
2. Your code executes the tool
3. You send the result back to Claude
4. Claude formulates a response

## Basic Tool Use

### Define Tools
```python
import anthropic

client = anthropic.Anthropic()

tools = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City and state, e.g., San Francisco, CA"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature unit"
                }
            },
            "required": ["location"]
        }
    }
]
```

### Make Request
```python
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "What's the weather in NYC?"}]
)

# Check for tool use
for block in response.content:
    if block.type == "tool_use":
        print(f"Tool: {block.name}")
        print(f"Input: {block.input}")
        # Execute your function here
```

### Return Tool Result
```python
# After executing the tool
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=tools,
    messages=[
        {"role": "user", "content": "What's the weather in NYC?"},
        {"role": "assistant", "content": response.content},
        {
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use_block.id,
                "content": "72°F, sunny"
            }]
        }
    ]
)
```

## @beta_tool Decorator

Simplify tool definition with decorators:

```python
from anthropic import Anthropic, beta_tool

client = Anthropic()

@beta_tool
def get_stock_price(ticker: str) -> str:
    """Get the current stock price.

    Args:
        ticker: Stock ticker symbol (e.g., AAPL)

    Returns:
        Current stock price as a string
    """
    # Your implementation
    return f"${get_price(ticker)}"

runner = client.beta.messages.tool_runner(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[get_stock_price],
    messages=[{"role": "user", "content": "What's Apple's stock price?"}]
)

for message in runner:
    print(message)
```

## Built-in Tools

### Computer Use (Beta)
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
        }
    ],
    messages=[{"role": "user", "content": "Click the search button"}],
    betas=["computer-use-2025-01-24"]
)
```

### Text Editor
```python
{
    "type": "text_editor_20250728",
    "name": "str_replace_based_edit_tool"
}
```

### Bash
```python
{
    "type": "bash_20250124",
    "name": "bash"
}
```

### Web Search
```python
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[{"type": "web_search_20250305", "name": "web_search"}],
    messages=[{"role": "user", "content": "What's the latest AI news?"}]
)
```

**Pricing:** $10 per 1,000 searches

### Code Execution
```python
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[{"type": "code_execution_20250522", "name": "code_execution"}],
    messages=[{"role": "user", "content": "Calculate fibonacci(20)"}]
)
```

**Pricing:** 50 free hours/day, then $0.05/hour

## Structured Outputs (Beta)

**Released:** November 14, 2025

Guarantees API responses match your JSON schema using constrained decoding.

### Enable Structured Outputs
Add beta header:
```python
# Using extra_headers
response = client.messages.create(
    ...,
    extra_headers={"anthropic-beta": "structured-outputs-2025-11-13"}
)
```

### JSON Outputs Mode

For data extraction:

```python
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    output_format={
        "type": "json_schema",
        "json_schema": {
            "name": "movie_review",
            "schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "rating": {"type": "number", "minimum": 0, "maximum": 10},
                    "summary": {"type": "string"}
                },
                "required": ["title", "rating", "summary"]
            }
        }
    },
    messages=[{"role": "user", "content": "Review the movie Inception"}],
    extra_headers={"anthropic-beta": "structured-outputs-2025-11-13"}
)

# response.content[0].text is guaranteed-valid JSON
import json
review = json.loads(response.content[0].text)
```

### Strict Tool Use Mode

Guarantees tool parameters match schema:

```python
tools = [
    {
        "name": "create_user",
        "description": "Create a new user",
        "strict": True,  # Enable strict mode
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string", "format": "email"},
                "age": {"type": "integer", "minimum": 0}
            },
            "required": ["name", "email"]
        }
    }
]

response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "Create user John at john@example.com"}],
    extra_headers={"anthropic-beta": "structured-outputs-2025-11-13"}
)
# tool_use.input will exactly match the schema
```

### Combining Both
```python
# JSON outputs: What Claude says (response format)
# Strict tools: How Claude calls functions (parameter validation)
# Can use together for complete type safety
```

### Performance Notes
- First request with new schema: 100-300ms overhead (grammar compilation)
- Cached for 24 hours after first use
- No performance impact on subsequent requests

## Fine-Grained Tool Streaming

Stream tool parameters without buffering:

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "..."}]
) as stream:
    for event in stream:
        if event.type == "content_block_delta":
            if event.delta.type == "input_json_delta":
                print(event.delta.partial_json, end="")
```

**Supported Models:** Sonnet 4.5, Haiku 4.5, Sonnet 4, Opus 4

## Tool Choice

Control how Claude uses tools:

```python
# Auto (default) - Claude decides
tool_choice={"type": "auto"}

# Any - Must use a tool
tool_choice={"type": "any"}

# Specific tool
tool_choice={"type": "tool", "name": "get_weather"}

# None - No tools
tool_choice={"type": "none"}
```

## Parallel Tool Use

Claude can call multiple tools simultaneously:

```python
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[weather_tool, stock_tool],
    messages=[{"role": "user", "content": "Weather in NYC and Apple stock price?"}]
)

# response.content may contain multiple tool_use blocks
tool_calls = [b for b in response.content if b.type == "tool_use"]
# Execute all and return results
```

## Best Practices

### 1. Clear Descriptions
```python
{
    "name": "search_database",
    "description": "Search the product database. Returns up to 10 results. Use for finding specific products by name, category, or ID.",
    ...
}
```

### 2. Validate Inputs
```python
def execute_tool(name: str, input: dict):
    if name == "delete_file":
        if not input.get("confirm"):
            raise ValueError("Confirmation required")
    # Execute...
```

### 3. Handle Errors Gracefully
```python
{
    "type": "tool_result",
    "tool_use_id": "...",
    "is_error": True,
    "content": "Database connection failed. Please try again."
}
```

### 4. Use Strict Mode for Safety
Enable `strict: true` for tools with critical schemas.

## Vision + Tools

Combine image analysis with tools:

```python
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[chart_analysis_tool],
    messages=[{
        "role": "user",
        "content": [
            {"type": "image", "source": {"type": "base64", ...}},
            {"type": "text", "text": "Analyze this chart and save insights"}
        ]
    }]
)
```

## Message Batches + Tools

Use tools in batch processing:

```python
batch = client.messages.batches.create(
    requests=[
        {
            "custom_id": "req-1",
            "params": {
                "model": "claude-sonnet-4-5-20250929",
                "max_tokens": 1024,
                "tools": tools,
                "messages": [...]
            }
        },
        ...
    ]
)
```

## References

- [Tool Use Documentation](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use)
- [Structured Outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
- [Computer Use](https://platform.claude.com/docs/en/computer-use)
