# Agent Development Kit (ADK) & Vertex AI Agent Builder

Google's comprehensive platform for building, deploying, and scaling AI agents in production.

## Agent Development Kit (ADK)

ADK is an open-source framework for building sophisticated multi-agent systems.

**Status:** Preview (7M+ downloads)

### Installation

```bash
pip install google-adk
```

### Supported Languages
- Python
- Java
- Go (new in 2025)

### Basic Agent (Under 100 Lines)

```python
from google.adk import Agent, tool

@tool
def get_weather(location: str) -> str:
    """Get weather for a location."""
    return f"Weather in {location}: 72°F, sunny"

agent = Agent(
    model="gemini-3-flash",
    tools=[get_weather],
    instructions="You are a helpful assistant."
)

response = agent.run("What's the weather in NYC?")
print(response)
```

### Multi-Agent Systems

```python
from google.adk import Agent, Orchestrator

research_agent = Agent(
    name="researcher",
    model="gemini-3-pro",
    instructions="Research topics thoroughly."
)

writer_agent = Agent(
    name="writer",
    model="gemini-3-flash",
    instructions="Write clear, concise content."
)

orchestrator = Orchestrator(
    agents=[research_agent, writer_agent],
    workflow="research -> writer"
)

result = orchestrator.run("Write an article about quantum computing")
```

### Protocol Support

| Protocol | Description |
|----------|-------------|
| **MCP** | Model Context Protocol for tool integration |
| **A2A** | Agent2Agent for cross-agent communication |

## Agent2Agent (A2A) Protocol

Universal communication standard for AI agents across different frameworks.

**Status:** v0.3 (150+ organizations)
**Governance:** Linux Foundation (donated June 2025)

### Key Capabilities

1. **Capability Discovery**: Agent Cards in JSON format
2. **Task Management**: Defined lifecycle states
3. **Agent Collaboration**: Context and instruction sharing
4. **UX Negotiation**: Adapts to different UI capabilities

### A2A vs MCP

| Feature | A2A | MCP |
|---------|-----|-----|
| Focus | Agent-to-agent communication | Tools and data sources |
| Scope | Inter-agent collaboration | Model-tool integration |
| Relationship | Complementary | Complementary |

### Resources
- Official docs: https://a2a-protocol.org/latest/
- GitHub: https://github.com/a2aproject/A2A

## Vertex AI Agent Builder

Enterprise platform for deploying and managing AI agents.

### Components

| Component | Description |
|-----------|-------------|
| **Agent Engine** | Runtime for deploying, scaling, managing agents |
| **Agent Designer** | Low-code visual interface for orchestration |
| **Agent Garden** | Library of sample agents and tools |

### Agent Designer Features

- Visual canvas for orchestrating agents and subagents
- Test agents directly in the interface
- Export to ADK for code-level refinement

### One-Command Deployment

```bash
# Deploy from ADK CLI
adk deploy --project=my-project

# No full GCP account needed (Gmail + 90-day trial)
```

### Pricing (Starting Jan 28, 2026)

| Service | Pricing |
|---------|---------|
| Agent Engine Runtime | Per-request |
| Sessions | Per-session |
| Memory Bank | Per-operation |
| Code Execution | Per-execution |

## Agent Engine Services

### Sessions & Memory

```python
from google.adk import Agent, MemoryBank

agent = Agent(
    model="gemini-3-flash",
    memory=MemoryBank(
        type="persistent",
        retention_days=30
    )
)

# Memory persists across sessions
session = agent.create_session(user_id="user123")
session.run("Remember my name is John")
# Later...
session.run("What's my name?")  # Returns "John"
```

### Code Execution

Sandboxed Python execution with persistent state:
- Files up to 100MB
- Multi-step coding tasks
- Data analysis workflows

## Best Practices

1. **Start with ADK** for prototyping
2. **Use Agent Designer** for visual orchestration
3. **Deploy to Agent Engine** for production
4. **Implement A2A** for multi-vendor agent ecosystems
5. **Leverage MCP** for tool integration

## References

- [ADK Overview](https://docs.cloud.google.com/agent-builder/agent-development-kit/overview)
- [Vertex AI Agent Builder](https://cloud.google.com/products/agent-builder)
- [A2A Protocol](https://a2a-protocol.org/)
- [Agent Engine Docs](https://docs.cloud.google.com/agent-builder/agent-engine)
