# Claude Agent SDK

The Claude Agent SDK enables you to build AI agents that can autonomously read files, run commands, search the web, edit code, and more. It provides the same tools, agent loop, and context management that power Claude Code.

**Version:** 0.1.19 (January 2026)

## Installation

```bash
pip install claude-agent-sdk
```

**Requirements:** Python 3.10+

**Note:** The Claude Code CLI is automatically bundled - no separate installation required.

## Quick Start

### Simple Query

```python
import anyio
from claude_agent_sdk import query

async def main():
    async for message in query(prompt="What is 2 + 2?"):
        print(message)

anyio.run(main)
```

### With Options

```python
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

options = ClaudeAgentOptions(
    system_prompt="You are a helpful coding assistant",
    max_turns=5
)

async def main():
    async for message in query(prompt="Create a hello world script", options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)

anyio.run(main)
```

## ClaudeSDKClient

For bidirectional conversations with custom tools and hooks:

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

options = ClaudeAgentOptions(
    allowed_tools=["Read", "Write", "Bash"],
    permission_mode='acceptEdits'
)

async def main():
    async with ClaudeSDKClient(options=options) as client:
        await client.query("Create a Python script that prints hello world")
        async for msg in client.receive_response():
            print(msg)

anyio.run(main)
```

## Configuration Options

```python
from claude_agent_sdk import ClaudeAgentOptions
from pathlib import Path

options = ClaudeAgentOptions(
    # System behavior
    system_prompt="You are an expert Python developer",
    max_turns=10,

    # Tool permissions
    allowed_tools=["Read", "Write", "Bash", "Glob", "Grep"],
    permission_mode='acceptEdits',  # or 'ask'

    # Working directory
    cwd="/path/to/project",  # or Path("/path/to/project")

    # MCP servers (custom tools)
    mcp_servers={"name": server_config},

    # Hooks (deterministic processing)
    hooks={"PreToolUse": [...]},

    # Custom CLI path (optional)
    cli_path="/custom/path/to/claude"
)
```

### Permission Modes

| Mode | Description |
|------|-------------|
| `'acceptEdits'` | Auto-accept file edits |
| `'ask'` | Prompt for confirmation |

## Custom Tools

Define tools as Python functions using the `@tool` decorator:

```python
from claude_agent_sdk import tool, create_sdk_mcp_server, ClaudeAgentOptions, ClaudeSDKClient

@tool("add", "Add two numbers", {"a": float, "b": float})
async def add(args):
    result = args['a'] + args['b']
    return {
        "content": [
            {"type": "text", "text": f"Sum: {result}"}
        ]
    }

@tool("multiply", "Multiply two numbers", {"a": float, "b": float})
async def multiply(args):
    result = args['a'] * args['b']
    return {
        "content": [
            {"type": "text", "text": f"Product: {result}"}
        ]
    }

# Create SDK MCP server
calculator = create_sdk_mcp_server(
    name="calculator",
    version="1.0.0",
    tools=[add, multiply]
)

options = ClaudeAgentOptions(
    mcp_servers={"calc": calculator},
    allowed_tools=["mcp__calc__add", "mcp__calc__multiply"]
)

async def main():
    async with ClaudeSDKClient(options=options) as client:
        await client.query("What is 25 + 17?")
        async for msg in client.receive_response():
            print(msg)
```

### Benefits of SDK MCP Servers

- **No subprocess management** - runs in-process
- **Better performance** - no IPC overhead
- **Simpler deployment** - no external processes
- **Easier debugging** - same process context
- **Type safety** - Python type checking

## Hooks

Hooks provide deterministic processing at specific points in the agent loop:

### PreToolUse Hook

```python
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, HookMatcher

async def validate_bash_command(input_data, tool_use_id, context):
    """Block dangerous bash commands."""
    if input_data["tool_name"] != "Bash":
        return {}

    command = input_data["tool_input"].get("command", "")

    # Block dangerous patterns
    dangerous_patterns = ["rm -rf", "sudo", "chmod 777"]
    for pattern in dangerous_patterns:
        if pattern in command:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Blocked: contains '{pattern}'"
                }
            }
    return {}

options = ClaudeAgentOptions(
    allowed_tools=["Bash", "Read", "Write"],
    hooks={
        "PreToolUse": [
            HookMatcher(matcher="Bash", hooks=[validate_bash_command])
        ]
    }
)
```

### Hook Events

| Event | Description |
|-------|-------------|
| `PreToolUse` | Before tool execution |
| `PostToolUse` | After tool execution |
| `Stop` | Agent stopping |
| `SubagentStop` | Subagent stopping |
| `SessionStart` | Session beginning |
| `SessionEnd` | Session ending |

## External MCP Servers

### Stdio Transport

```python
options = ClaudeAgentOptions(
    mcp_servers={
        "external": {
            "type": "stdio",
            "command": "my-mcp-server",
            "args": ["--config", "config.json"]
        }
    }
)
```

### Mixed Servers

Combine in-process and external servers:

```python
options = ClaudeAgentOptions(
    mcp_servers={
        "internal": sdk_server,        # In-process SDK server
        "external": {                  # External subprocess
            "type": "stdio",
            "command": "external-mcp-server"
        }
    }
)
```

## Message Types

```python
from claude_agent_sdk import (
    AssistantMessage,
    UserMessage,
    SystemMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock
)

async for message in query(prompt="Hello"):
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                print(f"Text: {block.text}")
            elif isinstance(block, ToolUseBlock):
                print(f"Tool: {block.name}")
                print(f"Input: {block.input}")
```

## Error Handling

```python
from claude_agent_sdk import (
    ClaudeSDKError,       # Base error
    CLINotFoundError,     # Claude Code CLI not installed
    CLIConnectionError,   # Connection issues
    ProcessError,         # Process failed
    CLIJSONDecodeError    # JSON parsing issues
)

try:
    async for message in query(prompt="Hello"):
        print(message)
except CLINotFoundError:
    print("Claude Code CLI not found")
except ProcessError as e:
    print(f"Process failed with exit code: {e.exit_code}")
except CLIConnectionError as e:
    print(f"Connection error: {e}")
```

## Authentication

### Direct API

```bash
export ANTHROPIC_API_KEY="your-key"
```

### AWS Bedrock

```bash
export CLAUDE_CODE_USE_BEDROCK=1
export AWS_REGION="us-east-1"
```

### Google Vertex AI

```bash
export CLAUDE_CODE_USE_VERTEX=1
export GOOGLE_CLOUD_PROJECT="your-project"
```

### Microsoft Foundry

```bash
export CLAUDE_CODE_USE_FOUNDRY=1
```

## Agent Skills (December 2025)

Agent Skills are organized folders of instructions, scripts, and resources that agents can discover and load dynamically:

```
.claude/
  skills/
    code-review/
      instructions.md
      review-script.py
    deployment/
      instructions.md
      deploy.sh
```

Skills are supported across Claude.ai, Claude Code, and the Agent SDK.

## Available Built-in Tools

| Tool | Description |
|------|-------------|
| `Read` | Read files |
| `Write` | Write/edit files |
| `Bash` | Execute bash commands |
| `Glob` | Find files by pattern |
| `Grep` | Search file contents |
| `LS` | List directory contents |
| `Task` | Launch subagents |
| `WebFetch` | Fetch web content |
| `WebSearch` | Search the web |

## Complete Example

```python
import anyio
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    tool,
    create_sdk_mcp_server,
    HookMatcher,
    AssistantMessage,
    TextBlock
)

# Define custom tool
@tool("get_time", "Get the current time", {})
async def get_time(args):
    from datetime import datetime
    return {
        "content": [{"type": "text", "text": datetime.now().isoformat()}]
    }

# Create MCP server
time_server = create_sdk_mcp_server(
    name="time",
    version="1.0.0",
    tools=[get_time]
)

# Define hook
async def log_tool_use(input_data, tool_use_id, context):
    print(f"[LOG] Tool called: {input_data['tool_name']}")
    return {}

# Configure options
options = ClaudeAgentOptions(
    system_prompt="You are a helpful assistant with access to time.",
    max_turns=5,
    allowed_tools=["Read", "mcp__time__get_time"],
    mcp_servers={"time": time_server},
    hooks={
        "PreToolUse": [
            HookMatcher(matcher="*", hooks=[log_tool_use])
        ]
    }
)

async def main():
    async with ClaudeSDKClient(options=options) as client:
        await client.query("What time is it?")

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Assistant: {block.text}")

anyio.run(main)
```

## Migration from Claude Code SDK

The Claude Code SDK was renamed to Claude Agent SDK:

| Old (< 0.1.0) | New (≥ 0.1.0) |
|---------------|---------------|
| `claude-code-sdk` | `claude-agent-sdk` |
| `ClaudeCodeOptions` | `ClaudeAgentOptions` |
| `from claude_code_sdk import` | `from claude_agent_sdk import` |

## References

- [GitHub Repository](https://github.com/anthropics/claude-agent-sdk-python)
- [PyPI Package](https://pypi.org/project/claude-agent-sdk/)
- [Agent SDK Documentation](https://platform.claude.com/docs/en/agent-sdk/overview)
- [Building Agents Blog Post](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
- [Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
