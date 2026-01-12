# Advanced Browser Services

## Overview

The `backend/advanced_browser_services` package provides streaming browser automation services built on top of `browser-use`, using Google's Gemini model for AI-powered web automation with real-time SSE streaming.

**Package Location:** `backend/advanced_browser_services/`

---

## Architecture

```
advanced_browser_services/
├── __init__.py              # Package exports
├── base_service.py          # LLM config + BaseAgentService (uses BrowserFactory)
├── streaming.py             # SSE streaming infrastructure
└── streaming_runner.py      # StreamingAgentRunner (main task executor)

ui_testing_agent/core/
└── browser_factory.py       # BrowserFactory - SINGLE SOURCE OF TRUTH for browsers
```

---

## 1. BrowserFactory - Single Source of Truth

**File:** `ui_testing_agent/core/browser_factory.py`

All browser instantiation MUST go through `BrowserFactory`. This ensures consistent initialization and handles CDP client issues gracefully.

### Why BrowserFactory?

- **Consistency**: All browser instances behave identically
- **Graceful Fallback**: Tries multiple strategies if one fails
- **Maintainability**: Bug fixes apply everywhere
- **Debuggability**: One place for logging and error handling

### Usage

```python
from ui_testing_agent.core.browser_factory import BrowserFactory, BrowserConfig

# Simple usage
result = await BrowserFactory.create(headless=True)

# With config
config = BrowserConfig(
    headless=True,
    window_width=1920,
    window_height=1080,
)
result = await BrowserFactory.create(config=config)

# Pass to Agent based on type
agent_kwargs = BrowserFactory.get_agent_kwargs(result)
agent = Agent(task=..., llm=..., **agent_kwargs)

# Cleanup
await BrowserFactory.cleanup(result)
```

### BrowserResult Structure

```python
@dataclass
class BrowserResult:
    browser: Any              # The browser/session object (or None)
    browser_type: str         # "browser_session" | "browser" | "agent_managed"
    strategy_used: str        # Which fallback strategy succeeded
```

### Fallback Strategies

| # | Strategy | Description |
|---|----------|-------------|
| 1 | `browser_session_with_start` | BrowserSession + explicit `start()` call |
| 2 | `browser_class` | Simple Browser class (proven to work) |
| 3 | `context_manager` | Async context manager pattern |
| 4 | `agent_managed` | Let Agent create its own browser |

---

## 2. Base Service Configuration

**File:** `base_service.py`

### LLM Initialization

```python
from advanced_browser_services import get_gemini_llm, DEFAULT_MODEL

# Get configured Gemini LLM
llm = get_gemini_llm(model="gemini-3-pro-preview", temperature=0.7)
```

**Default Model:** `gemini-3-pro-preview`

### BrowserConfig (Deprecated)

The `BrowserConfig` class in `base_service.py` is **deprecated**. Use `BrowserFactory` directly instead.

```python
# DEPRECATED - do not use
from advanced_browser_services import BrowserConfig
config = BrowserConfig(headless=False)
browser = config.create_browser()  # Raises DeprecationWarning

# CORRECT - use BrowserFactory
from ui_testing_agent.core.browser_factory import BrowserFactory
result = await BrowserFactory.create(headless=False)
```

### BaseAgentService

Base class for agent services. Uses `BrowserFactory` internally.

```python
from advanced_browser_services import BaseAgentService

class CustomAgent(BaseAgentService):
    async def my_task(self):
        browser_result = await self._ensure_browser()  # Uses BrowserFactory
        # Use browser_result.browser...
        await self.close()  # Cleanup via BrowserFactory
```

---

## 3. Streaming Infrastructure

**File:** `streaming.py`

Provides Server-Sent Events (SSE) streaming for real-time progress updates.

### Event Types

| Event | Level | Description |
|-------|-------|-------------|
| `step_start` | info | New step beginning |
| `step_thinking` | debug | Agent's reasoning |
| `step_action` | info | Action being executed |
| `step_result` | success/error | Action outcome |
| `browser_state` | info | Current URL/title |
| `progress` | info | General progress |
| `error` | error | Error occurred |
| `done` | success | Task completed |

### StreamEvent Structure

```python
@dataclass
class StreamEvent:
    event_type: EventType
    level: LogLevel
    message: str
    timestamp: str
    data: Optional[Dict]
    step_number: Optional[int]
```

### SSE Wire Format

```
data: {"type": "step_action", "level": "info", "message": "Clicking button", ...}\n\n
```

### StreamingSession Usage

```python
from advanced_browser_services.streaming import create_session

# Create session
session = create_session()

# Emit events
session.emit_info("Starting task...")
session.emit_step_start(1)
session.emit_action("click", {"element": "Submit button"})
session.emit_browser_state("https://example.com", "Example Page")
session.emit_done("Task completed", success=True)

# Stream events via SSE
async for event in session.events():
    yield event  # Send to client
```

### Creating Callbacks for browser-use Agent

```python
from advanced_browser_services.streaming import create_step_callback, create_done_callback

session = create_session()

agent = Agent(
    task="...",
    llm=llm,
    **BrowserFactory.get_agent_kwargs(browser_result),
    register_new_step_callback=create_step_callback(session),
    register_done_callback=create_done_callback(session),
)
```

---

## 4. Streaming Runner

**File:** `streaming_runner.py`

High-level runner that combines browser-use agents with SSE streaming.

### StreamingAgentRunner

```python
from advanced_browser_services import get_streaming_runner

runner = get_streaming_runner()
session = runner.create_session()

# Run task with streaming
result = await runner.run_basic_task(
    session=session,
    task="Search for Python tutorials",
    max_steps=30,
    headless=False
)
```

### Available Methods

| Method | Description |
|--------|-------------|
| `run_basic_task()` | General browser automation |
| `run_ui_testing_agent_task()` | Full UI testing with artifacts |
| `run_data_extraction()` | Extract data with streaming |
| `run_research()` | Research with progress updates |
| `run_product_comparison()` | Compare products |
| `run_page_comparison()` | Compare pages |

### Example: UI Testing Agent Task

```python
result = await runner.run_ui_testing_agent_task(
    session=session,
    task="Test the login functionality on example.com",
    max_steps=30,
    headless=False,
)
# Generates: screenshots, HTML report, Playwright tests
```

---

## 5. API Endpoints (via main.py)

The FastAPI backend exposes streaming SSE endpoints:

### SSE Streaming Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/stream/basic-task` | POST | Stream UI testing task execution |
| `/stream/extract-data` | POST | Extract data with streaming |
| `/stream/research-topic` | POST | Research topic with streaming |
| `/stream/compare-products` | POST | Compare products with streaming |
| `/stream/compare-pages` | POST | Compare pages with streaming |

### Artifacts Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/artifacts/{session_id}` | GET | List all artifacts for a session |
| `/artifacts/{session_id}/file/{path}` | GET | Serve a specific artifact file |
| `/artifacts/{session_id}/code` | GET | Get generated Playwright code |
| `/sessions` | GET | List all available sessions |

### Request Models

```python
# Basic Task
class StreamingTaskRequest:
    task: str
    max_steps: int = 30
    headless: bool = False

# Data Extraction
class StreamingExtractRequest:
    url: str
    data_schema: dict
    max_items: Optional[int] = None
    max_steps: int = 40
    headless: bool = False

# Research
class StreamingResearchRequest:
    topic: str
    depth: str = "moderate"
    max_sources: int = 5
    max_steps: int = 50
    headless: bool = False

# Product Comparison
class StreamingCompareProductsRequest:
    products: List[str]
    aspects: List[str]
    max_steps: int = 60
    headless: bool = False

# Page Comparison
class StreamingComparePagesRequest:
    urls: List[str]
    comparison_criteria: str
    max_steps: int = 30
    headless: bool = False
```

---

## 6. Quick Reference

### Installation Requirements

- `browser-use` >= 0.11.x
- `langchain-google-genai`
- `playwright`
- `pydantic`
- `python-dotenv`
- `fastapi`
- `uvicorn`

### Environment Variables

```bash
GEMINI_API_KEY=your_api_key_here
# or
GOOGLE_API_KEY=your_api_key_here
```

### Running the Backend

```bash
cd backend
python main.py
# or
uvicorn main:app --host 0.0.0.0 --port 8001
```

---

## Summary

| Component | File | Purpose |
|-----------|------|---------|
| BrowserFactory | `browser_factory.py` | Single source of truth for browser creation |
| BaseAgentService | `base_service.py` | Base class for agent services |
| StreamingSession | `streaming.py` | SSE event management |
| StreamingAgentRunner | `streaming_runner.py` | High-level task execution with streaming |
| FastAPI App | `main.py` | REST/SSE API endpoints |

The architecture is designed for simplicity and reliability:
1. **BrowserFactory** handles all browser initialization with graceful fallback
2. **StreamingAgentRunner** provides task execution with real-time updates
3. **SSE Streaming** enables live progress to the frontend
4. **Artifacts System** stores screenshots, reports, and generated tests
