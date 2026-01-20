# Model Context Protocol (MCP)

MCP is an open standard for AI systems to integrate with external tools, systems, and data sources. Created by Anthropic in November 2024 and donated to the Linux Foundation in December 2025.

## Overview

MCP provides a universal interface for:
- Reading files and data
- Executing functions
- Handling contextual prompts
- Connecting to external services

**Status:** Industry standard adopted by Anthropic, OpenAI, Google, and Microsoft

## Key Milestones

| Date | Event |
|------|-------|
| Nov 2024 | MCP introduced by Anthropic |
| Mar 2025 | OpenAI adopts MCP |
| Apr 2025 | Google announces Gemini MCP support |
| May 2025 | Microsoft/GitHub join steering committee |
| Nov 2025 | Spec v2025-11-25 with async, stateless mode |
| Dec 2025 | Donated to Agentic AI Foundation (Linux Foundation) |

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   AI Client     │────▶│   MCP Server    │────▶│  External       │
│   (Claude)      │◀────│                 │◀────│  Service        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │
        │    MCP Protocol       │
        │    (JSON-RPC 2.0)     │
        └───────────────────────┘
```

## Transport Types

### Stdio (Most Common)
Spawns subprocess, communicates via stdin/stdout:
```json
{
  "type": "stdio",
  "command": "my-mcp-server",
  "args": ["--config", "config.json"]
}
```

### SSE (Server-Sent Events)
HTTP-based streaming:
```json
{
  "type": "sse",
  "url": "https://example.com/mcp/sse"
}
```

### HTTP
Standard HTTP requests:
```json
{
  "type": "http",
  "url": "https://example.com/mcp"
}
```

## Official MCP Servers

Anthropic provides pre-built servers for:

| Server | Description |
|--------|-------------|
| GitHub | Repository access, issues, PRs |
| Google Drive | File access and search |
| Slack | Channel messaging |
| Postgres | Database queries |
| Puppeteer | Browser automation |
| Git | Version control operations |
| Filesystem | Local file operations |

**Directory:** 75+ connectors available via Claude's MCP directory

## Using MCP in Claude Code

### Project Configuration
`.mcp.json` in project root:
```json
{
  "servers": {
    "github": {
      "type": "stdio",
      "command": "mcp-server-github",
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "postgres": {
      "type": "stdio",
      "command": "mcp-server-postgres",
      "args": ["--connection-string", "postgresql://..."]
    }
  }
}
```

### User Configuration
`~/.claude/mcp.json` for global servers.

## Using MCP in Agent SDK

### External MCP Server
```python
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

options = ClaudeAgentOptions(
    mcp_servers={
        "github": {
            "type": "stdio",
            "command": "mcp-server-github"
        }
    },
    allowed_tools=["mcp__github__search_repositories"]
)

async with ClaudeSDKClient(options=options) as client:
    await client.query("Find popular Python ML repos")
```

### In-Process SDK Server
```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("query_db", "Query the database", {"sql": str})
async def query_db(args):
    result = await run_query(args["sql"])
    return {"content": [{"type": "text", "text": str(result)}]}

db_server = create_sdk_mcp_server(
    name="database",
    version="1.0.0",
    tools=[query_db]
)

options = ClaudeAgentOptions(
    mcp_servers={"db": db_server},
    allowed_tools=["mcp__db__query_db"]
)
```

### Mixed Configuration
```python
options = ClaudeAgentOptions(
    mcp_servers={
        "internal": sdk_server,        # In-process
        "external": {                  # Subprocess
            "type": "stdio",
            "command": "external-mcp-server"
        }
    }
)
```

## MCP Server Development

### Basic Server Structure (Python)
```python
from mcp import Server, Tool
from mcp.types import TextContent

server = Server("my-server")

@server.tool("my_tool")
async def my_tool(query: str) -> list[TextContent]:
    """Tool description for Claude."""
    result = process(query)
    return [TextContent(type="text", text=result)]

if __name__ == "__main__":
    server.run()
```

### Tool Schema
```python
@server.tool(
    name="search",
    description="Search the knowledge base",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "limit": {"type": "integer", "default": 10}
        },
        "required": ["query"]
    }
)
async def search(query: str, limit: int = 10):
    ...
```

## MCP SDK Downloads

| Language | Monthly Downloads |
|----------|------------------|
| Python | 50M+ |
| TypeScript | 47M+ |

## Spec Features (v2025-11-25)

| Feature | Description |
|---------|-------------|
| Asynchronous Operations | Non-blocking tool execution |
| Stateless Mode | Simpler server implementations |
| Server Identity | Authentication and verification |
| Community Registry | Discover MCP servers |

## Best Practices

1. **Use official servers** when available for reliability
2. **SDK servers for simple tools** - No subprocess overhead
3. **External servers for complex integrations** - Isolation, different languages
4. **Validate tool inputs** - Security at the MCP boundary
5. **Handle errors gracefully** - Return meaningful error messages

## Security Considerations

- MCP servers run with the permissions of the host process
- Validate and sanitize all inputs
- Use environment variables for secrets
- Consider network isolation for sensitive servers
- Audit tool access patterns

## Integration Points

| Platform | MCP Support |
|----------|-------------|
| Claude.ai | ✓ |
| Claude Code | ✓ |
| Claude Agent SDK | ✓ |
| Anthropic API | Via tools |
| OpenAI | ✓ (Agents SDK) |
| Google Gemini | Announced |
| Windows 11 | Preview |

## References

- [MCP Specification](https://modelcontextprotocol.io/specification/2025-11-25)
- [MCP Introduction](https://www.anthropic.com/news/model-context-protocol)
- [Agentic AI Foundation](https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation)
- [MCP Servers Directory](https://github.com/modelcontextprotocol/servers)
