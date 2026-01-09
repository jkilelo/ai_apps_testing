# Advanced Browser Services - Feature Showcase

## Overview

The `backend/advanced_browser_services` package provides specialized browser automation capabilities that extend beyond browser-use's native features. This package focuses on value-added services like multi-tab orchestration, parallel execution, structured data extraction, and research with source tracking.

**Package Location:** `backend/advanced_browser_services/`

---

## Architecture

```
advanced_browser_services/
├── __init__.py              # Package exports
├── base_service.py          # Core configuration (LLM, BrowserConfig)
├── service_runner.py        # Unified API facade (AdvancedBrowserService)
├── streaming.py             # SSE streaming infrastructure
├── streaming_runner.py      # Streaming task execution
├── multi_tab_agent.py       # Multi-tab browser automation
├── parallel_agents.py       # Concurrent agent execution
├── research_agent.py        # Web research with citations
├── data_extraction_agent.py # Structured data scraping
└── test_agents.py           # Test suite
```

---

## 1. Base Service Configuration

**File:** `base_service.py`

### LLM Initialization

```python
from advanced_browser_services import get_gemini_llm, DEFAULT_MODEL

# Get configured Gemini LLM
llm = get_gemini_llm(model="gemini-3-pro-preview", temperature=0.7)
```

**Default Model:** `gemini-3-pro-preview`

### Browser Configuration

```python
from advanced_browser_services import BrowserConfig

# Create browser with custom settings
config = BrowserConfig(
    headless=False,           # Show browser window
    disable_security=False,   # Keep security enabled
    window_width=1280,        # Browser width
    window_height=900,        # Browser height
    user_data_dir=None,       # Persistent profile path
    allowed_domains=None,     # Domain whitelist
)

# Create browser instance
browser = config.create_browser()
```

### Base Agent Service

All specialized agents inherit from `BaseAgentService`:

```python
from advanced_browser_services import BaseAgentService

class CustomAgent(BaseAgentService):
    async def my_task(self):
        browser = await self._ensure_browser()
        # Use browser...
        await self.close()  # Cleanup
```

---

## 2. Unified Service Facade

**File:** `service_runner.py`

The `AdvancedBrowserService` provides a single entry point for all capabilities:

```python
from advanced_browser_services import AdvancedBrowserService

service = AdvancedBrowserService(
    model="gemini-3-pro-preview",
    temperature=0.7,
    headless=False
)
```

### Available Methods

| Method | Description |
|--------|-------------|
| `run_task()` | Basic browser automation |
| `extract_data()` | Structured data extraction |
| `research_topic()` | Web research with sources |
| `compare_products()` | Product comparison |
| `compare_pages()` | Multi-tab page comparison |
| `run_parallel_tasks()` | Concurrent task execution |

### TaskResult Structure

All methods return a unified `TaskResult`:

```python
@dataclass
class TaskResult:
    success: bool              # Task completed successfully
    task_type: str             # Type identifier
    summary: str               # Human-readable summary
    data: Dict[str, Any]       # Task-specific data
    steps: List[Dict]          # Execution steps
    error: Optional[str]       # Error message if failed
```

---

## 3. Multi-Tab Agent

**File:** `multi_tab_agent.py`

Enables automation across multiple browser tabs simultaneously.

### Use Cases
- Compare products across different websites
- Research topics from multiple sources
- Fill forms requiring data from other pages
- Monitor multiple dashboards

### Basic Usage

```python
from advanced_browser_services import MultiTabAgent

agent = MultiTabAgent(max_tabs=5)

result = await agent.run(
    task="Compare pricing between Amazon and Best Buy for iPhone 15",
    initial_urls=["https://amazon.com", "https://bestbuy.com"],
    max_steps=50
)
```

### Page Comparison

```python
result = await agent.compare_pages(
    urls=[
        "https://site-a.com/product",
        "https://site-b.com/product"
    ],
    comparison_criteria="price, shipping time, reviews",
    max_steps=30
)
```

### Response Structure

```python
{
    "steps": [...],           # Actions taken
    "summary": "...",         # Comparison results
    "success": True
}
```

---

## 4. Parallel Agent Runner

**File:** `parallel_agents.py`

Runs multiple independent browser agents concurrently with semaphore-controlled concurrency.

### Use Cases
- Scrape data from multiple websites simultaneously
- Perform the same task on different sites
- Research multiple topics at once
- Speed up batch operations

### Basic Usage

```python
from advanced_browser_services import ParallelAgentRunner, AgentTask

runner = ParallelAgentRunner(max_concurrent_agents=3)

tasks = [
    AgentTask(task_id="site1", description="Get price from amazon.com", max_steps=15),
    AgentTask(task_id="site2", description="Get price from walmart.com", max_steps=15),
    AgentTask(task_id="site3", description="Get price from target.com", max_steps=15),
]

results = await runner.run_parallel(tasks)
```

### Same Task on Multiple Sites

```python
results = await runner.run_same_task_on_sites(
    task_template="Go to {url} and find the contact email",
    urls=[
        "https://company-a.com",
        "https://company-b.com",
        "https://company-c.com"
    ],
    max_steps=20
)
```

### Batch Search

```python
results = await runner.batch_search(
    queries=["Python web scraping", "Playwright automation", "Browser agents"],
    search_engine="google",
    max_steps=15
)
```

### AgentResult Structure

```python
@dataclass
class AgentResult:
    task_id: str              # Task identifier
    success: bool             # Completed successfully
    summary: str              # Result summary
    steps: List[Dict]         # Actions taken
    error: Optional[str]      # Error if failed
```

---

## 5. Research Agent

**File:** `research_agent.py`

Specialized for web research with automatic note-taking and source tracking.

### Use Cases
- Market research
- Competitor analysis
- Topic deep-dives
- Fact-checking
- News monitoring

### Custom Research Tools

The agent includes built-in tools:

| Tool | Description |
|------|-------------|
| `add_research_note` | Record finding with source URL and confidence |
| `summarize_research` | Compile findings into summary |

### Research Topic

```python
from advanced_browser_services import ResearchAgent

agent = ResearchAgent()

result = await agent.research_topic(
    topic="Electric vehicle market trends 2024",
    depth="deep",              # shallow, moderate, deep
    max_sources=5,
    max_steps=50
)
```

**Response:**
```python
{
    "success": True,
    "topic": "Electric vehicle market trends 2024",
    "depth": "deep",
    "findings": [
        {
            "topic": "market_growth",
            "finding": "EV sales increased 35% YoY",
            "source": "https://...",
            "confidence": "high"
        },
        ...
    ],
    "sources": ["https://...", ...],
    "num_findings": 12,
    "num_sources": 5,
    "summary": "..."
}
```

### Product Comparison

```python
result = await agent.compare_products(
    products=["Tesla Model 3", "BMW i4", "Mercedes EQE"],
    comparison_aspects=["price", "range", "charging speed", "features"],
    max_steps=60
)
```

**Response:**
```python
{
    "success": True,
    "products": [...],
    "aspects": [...],
    "findings_by_product": {
        "Tesla Model 3": [...],
        "BMW i4": [...],
        "Mercedes EQE": [...]
    },
    "summary": "..."
}
```

### Fact Checking

```python
result = await agent.fact_check(
    claim="Python is the most popular programming language in 2024",
    num_sources=3,
    max_steps=40
)
```

**Response:**
```python
{
    "success": True,
    "claim": "...",
    "evidence_for": [...],
    "evidence_against": [...],
    "sources": [...],
    "verdict": "PARTIALLY TRUE: Python ranks #1 in TIOBE..."
}
```

---

## 6. Data Extraction Agent

**File:** `data_extraction_agent.py`

Specialized for extracting structured data from web pages with schema validation.

### Use Cases
- Scrape product information from e-commerce
- Extract contact details from directories
- Gather research data
- Monitor prices and availability

### Custom Extraction Tools

| Tool | Description |
|------|-------------|
| `store_extracted_item` | Save extracted data item as JSON |
| `extraction_complete` | Signal extraction finished |

### Basic Extraction

```python
from advanced_browser_services import DataExtractionAgent

agent = DataExtractionAgent(temperature=0.3)  # Low temp for consistency

result = await agent.extract(
    url="https://shop.example.com/products",
    data_schema={
        "name": "Product name",
        "price": "Price in USD",
        "rating": "Star rating out of 5",
        "reviews": "Number of reviews"
    },
    max_items=20,
    max_steps=40
)
```

**Response:**
```python
{
    "success": True,
    "url": "...",
    "items_extracted": 20,
    "data": [
        {"name": "Widget A", "price": "$29.99", "rating": "4.5", "reviews": "128"},
        {"name": "Widget B", "price": "$34.99", "rating": "4.2", "reviews": "89"},
        ...
    ],
    "summary": "Extraction completed"
}
```

### Extract to File

```python
result = await agent.extract_to_file(
    url="https://shop.example.com/products",
    data_schema={"name": "Name", "price": "Price"},
    output_file="./extracted_products.json",
    max_items=50
)
# Creates extracted_products.json with the data
```

### Multi-URL Extraction

```python
result = await agent.extract_from_multiple_urls(
    urls=[
        "https://shop-a.com/products",
        "https://shop-b.com/products",
        "https://shop-c.com/products"
    ],
    data_schema={"name": "Name", "price": "Price"},
    max_items_per_url=10,
    max_steps_per_url=30
)
```

**Response:**
```python
{
    "total_urls": 3,
    "successful_extractions": 3,
    "total_items": 30,
    "data": [...],  # Combined from all URLs
    "per_url_results": [...]
}
```

---

## 7. Streaming Infrastructure

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

### SSE Format

Events are serialized as:
```
data: {"type": "step_action", "level": "info", "message": "Clicking button", ...}\n\n
```

### StreamingSession Usage

```python
from advanced_browser_services.streaming import create_session, StreamingSession

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
    browser=browser,
    register_new_step_callback=create_step_callback(session),
    register_done_callback=create_done_callback(session),
)
```

---

## 8. Streaming Runner

**File:** `streaming_runner.py`

High-level runner that combines agents with SSE streaming.

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

### Available Streaming Methods

| Method | Description |
|--------|-------------|
| `run_basic_task()` | General browser automation |
| `run_data_extraction()` | Extract data with streaming |
| `run_research()` | Research with progress updates |
| `run_product_comparison()` | Compare products |
| `run_page_comparison()` | Compare pages |
| `run_ui_testing_agent_task()` | Full UI testing with artifacts |

### SSE Endpoint Integration

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.get("/stream/task")
async def stream_task(task: str):
    runner = get_streaming_runner()
    session = runner.create_session()

    async def event_generator():
        # Start task in background
        asyncio.create_task(runner.run_basic_task(session, task))

        # Stream events
        async for event in session.events():
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

---

## 9. Quick Reference

### Installation

The package requires:
- `browser-use` >= 0.11.x
- `langchain-google-genai`
- `playwright`
- `pydantic`
- `python-dotenv`

### Environment Variables

```bash
GEMINI_API_KEY=your_api_key_here
# or
GOOGLE_API_KEY=your_api_key_here
```

### Convenience Function

```python
from advanced_browser_services import run_browser_task

# Quick one-liner for simple tasks
result = await run_browser_task(
    task="Go to google.com and search for 'AI'",
    headless=True,
    max_steps=20
)
```

### Running Tests

```bash
cd backend
python -m advanced_browser_services.test_agents
```

---

## 10. API Endpoints (via main.py)

The FastAPI backend exposes these endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/stream/basic-task` | GET | Stream basic task execution |
| `/advanced/task` | POST | Run basic task |
| `/advanced/extract` | POST | Extract data |
| `/advanced/research` | POST | Research topic |
| `/advanced/compare-products` | POST | Compare products |
| `/advanced/parallel` | POST | Run parallel tasks |
| `/advanced/compare-pages` | POST | Compare pages |

---

## Summary

| Feature | Agent | Key Capability |
|---------|-------|----------------|
| Multi-Tab | `MultiTabAgent` | Work across multiple tabs |
| Parallel Execution | `ParallelAgentRunner` | Run agents concurrently |
| Research | `ResearchAgent` | Gather info with citations |
| Data Extraction | `DataExtractionAgent` | Structured scraping |
| Streaming | `StreamingAgentRunner` | Real-time SSE updates |
| Unified API | `AdvancedBrowserService` | Single entry point |
