# AI Apps Testing Platform - Architecture

## Table of Contents

1. [System Overview](#1-system-overview)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Frontend Architecture](#3-frontend-architecture)
4. [Backend Architecture](#4-backend-architecture)
5. [BrowserFactory - Single Source of Truth](#5-browserfactory---single-source-of-truth)
6. [SSE Streaming Architecture](#6-sse-streaming-architecture)
7. [Agent Execution Flow](#7-agent-execution-flow)
8. [Data Flow Diagrams](#8-data-flow-diagrams)
9. [API Contract](#9-api-contract)
10. [File Organization](#10-file-organization)

---

## 1. System Overview

```
+===========================================================================+
|                        AI APPS TESTING PLATFORM                           |
|===========================================================================|
|                                                                           |
|    +------------------+         HTTP/SSE          +------------------+    |
|    |                  |<=========================>|                  |    |
|    |     FRONTEND     |        Port 8001          |     BACKEND      |    |
|    |   (React/Vite)   |                           |    (FastAPI)     |    |
|    |    Port 3000     |                           |                  |    |
|    +------------------+                           +------------------+    |
|                                                           |               |
|                                                           v               |
|                                               +-----------------------+   |
|                                               |   BROWSER AUTOMATION  |   |
|                                               |     (browser-use)     |   |
|                                               |     + Playwright      |   |
|                                               +-----------------------+   |
|                                                           |               |
|                                                           v               |
|                                               +-----------------------+   |
|                                               |      GEMINI LLM       |   |
|                                               |   (Google AI API)     |   |
|                                               +-----------------------+   |
|                                                                           |
+===========================================================================+
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | React 18 + TypeScript | UI Components |
| Build Tool | Vite | Development Server |
| Styling | Tailwind CSS | UI Styling |
| Backend | FastAPI (Python 3.11+) | REST API + SSE |
| Browser Automation | browser-use 0.11.x | AI Agent Framework |
| Browser Engine | Playwright | Chrome/Chromium Control |
| LLM Provider | Google Gemini | AI Decision Making |
| Streaming | Server-Sent Events | Real-time Updates |

---

## 2. High-Level Architecture

```
+============================================================================+
|                           SYSTEM ARCHITECTURE                              |
+============================================================================+

                              FRONTEND (Port 3000)
    +--------------------------------------------------------------------+
    |                                                                    |
    |   +-------------------+    +-------------------+                   |
    |   |   UIAutomator     |    |   SessionBrowser  |                   |
    |   |    Component      |    |    Component      |                   |
    |   +--------+----------+    +--------+----------+                   |
    |            |                        |                              |
    |            v                        v                              |
    |   +-------------------+    +-------------------+                   |
    |   |    LogViewer      |    | SessionComparison |                   |
    |   |    Component      |    |    Component      |                   |
    |   +--------+----------+    +--------+----------+                   |
    |            |                        |                              |
    |            +----------+-------------+                              |
    |                       |                                            |
    |                       v                                            |
    |            +---------------------+                                 |
    |            |   API Client Layer  |                                 |
    |            |  (HTTP + SSE Client)|                                 |
    |            +----------+----------+                                 |
    |                       |                                            |
    +--------------------------------------------------------------------+
                            |
                            | HTTP REST / SSE Stream
                            | Port 8001
                            v
    +--------------------------------------------------------------------+
    |                       BACKEND (Port 8001)                          |
    |                                                                    |
    |   +------------------------+                                       |
    |   |       main.py          |  <-- FastAPI Application              |
    |   |  (API Router Layer)    |                                       |
    |   +-----------+------------+                                       |
    |               |                                                    |
    |               v                                                    |
    |   +------------------------+                                       |
    |   |  StreamingAgentRunner  |  <-- Task Execution Engine            |
    |   +-----------+------------+                                       |
    |               |                                                    |
    |               v                                                    |
    |   +------------------------+                                       |
    |   |    BrowserFactory      |  <-- SINGLE SOURCE OF TRUTH           |
    |   |  (Browser Instantiation)|                                      |
    |   +-----------+------------+                                       |
    |               |                                                    |
    +--------------------------------------------------------------------+
                   |
                   v
    +--------------------------------------------------------------------+
    |                    EXTERNAL DEPENDENCIES                           |
    |                                                                    |
    |   +-----------------+      +------------------+                    |
    |   |   browser-use   |      |   Google Gemini  |                    |
    |   |  (Agent + CDP)  |      |      LLM API     |                    |
    |   +--------+--------+      +---------+--------+                    |
    |            |                         |                             |
    |            v                         |                             |
    |   +-----------------+                |                             |
    |   |   Playwright    |<---------------+                             |
    |   | (Chrome Driver) |                                              |
    |   +-----------------+                                              |
    |                                                                    |
    +--------------------------------------------------------------------+
```

---

## 3. Frontend Architecture

```
+============================================================================+
|                         FRONTEND COMPONENT TREE                            |
+============================================================================+

                            App.tsx
                               |
                               v
    +----------------------------------------------------------+
    |                     UIAutomator.tsx                       |
    |  +-----------------------------------------------------+  |
    |  |  +-------------+  +-------------+  +-------------+  |  |
    |  |  | Task Input  |  |   Mode      |  |  Controls   |  |  |
    |  |  |   Form      |  |  Selector   |  |  (Run/Stop) |  |  |
    |  |  +-------------+  +-------------+  +-------------+  |  |
    |  +-----------------------------------------------------+  |
    |                           |                               |
    |  +-----------------------------------------------------+  |
    |  |                    Main Content                     |  |
    |  |  +------------------+  +-------------------------+  |  |
    |  |  |                  |  |                         |  |  |
    |  |  |   LogViewer      |  |   TestResultsPanel      |  |  |
    |  |  |  (Streaming      |  |  (Summary + Steps)      |  |  |
    |  |  |   Terminal)      |  |                         |  |  |
    |  |  |                  |  |                         |  |  |
    |  |  +------------------+  +-------------------------+  |  |
    |  +-----------------------------------------------------+  |
    |                           |                               |
    |  +-----------------------------------------------------+  |
    |  |                 ArtifactsViewer                     |  |
    |  |  +------------+ +----------+ +--------+ +--------+  |  |
    |  |  |Screenshots | |  Code    | | Reports| |Downloads| |  |
    |  |  |  Gallery   | |  Viewer  | |  Tab   | |  Tab   |  |  |
    |  |  +------------+ +----------+ +--------+ +--------+  |  |
    |  +-----------------------------------------------------+  |
    +----------------------------------------------------------+
                               |
    +----------------------------------------------------------+
    |              Overlay Panels (Conditional)                 |
    |  +-------------------------+  +------------------------+  |
    |  |    SessionBrowser       |  |   SessionComparison    |  |
    |  |   (History Panel)       |  |   (Compare Panel)      |  |
    |  +-------------------------+  +------------------------+  |
    +----------------------------------------------------------+
```

### Frontend Components

| Component | Purpose |
|-----------|---------|
| `UIAutomator.tsx` | Main application container |
| `LogViewer.tsx` | Real-time streaming terminal |
| `TestResultsPanel.tsx` | Test summary and step display |
| `ArtifactsViewer.tsx` | Screenshots, code, reports viewer |
| `SessionBrowser.tsx` | Browse and reload past sessions |
| `SessionComparison.tsx` | Compare two test sessions |
| `Toast.tsx` | Notification toasts |
| `Sidebar.tsx` | Navigation sidebar |

---

## 4. Backend Architecture

```
+============================================================================+
|                          BACKEND LAYER DIAGRAM                             |
+============================================================================+

    +====================================================================+
    |                         main.py (FastAPI)                          |
    |====================================================================|
    |                                                                    |
    |   +-----------------------------+  +-----------------------------+ |
    |   |    SSE STREAMING ENDPOINTS  |  |    ARTIFACTS ENDPOINTS       | |
    |   +-----------------------------+  +-----------------------------+ |
    |   | POST /stream/basic-task     |  | GET /artifacts/{id}         | |
    |   | POST /stream/extract-data   |  | GET /artifacts/{id}/file/*  | |
    |   | POST /stream/research-topic |  | GET /artifacts/{id}/code    | |
    |   | POST /stream/compare-*      |  | GET /sessions               | |
    |   +-----------------------------+  +-----------------------------+ |
    |                                                                    |
    |   +------------------------------------------------------------+   |
    |   |               GLOBAL INSTANCE                               |   |
    |   +------------------------------------------------------------+   |
    |   | streaming_runner = get_streaming_runner()                   |   |
    |   +------------------------------------------------------------+   |
    |                                                                    |
    +====================================================================+
                            |
                            v
    +====================================================================+
    |                   SERVICE LAYER                                    |
    +====================================================================+

    +-------------------------------+
    |    StreamingAgentRunner       |
    |        (SSE Engine)           |
    +-------------------------------+
    |                               |
    | - create_session()            |
    | - run_basic_task()            |
    | - run_ui_testing_agent_task() |
    | - run_data_extraction()       |
    | - run_research()              |
    | - run_product_comparison()    |
    | - run_page_comparison()       |
    |                               |
    +---------------+---------------+
                    |
                    v
    +-------------------------------+     +-------------------------------+
    |       UITestingService        |     |       BrowserFactory          |
    |   (Artifact Generation)       |     |  (SINGLE SOURCE OF TRUTH)     |
    +-------------------------------+     +-------------------------------+
    |                               |     |                               |
    | - explore_and_test()          |     | - create() -> BrowserResult   |
    | - Generates:                  |     | - cleanup()                   |
    |   - Screenshots               |     | - get_agent_kwargs()          |
    |   - HTML/JSON Reports         |     |                               |
    |   - Playwright Tests          |     | Strategies:                   |
    |   - GIF Recording             |     | 1. browser_session_with_start |
    |                               |     | 2. browser_class              |
    +---------------+---------------+     | 3. context_manager            |
                    |                     | 4. agent_managed              |
                    v                     +-------------------------------+
    +-------------------------------+
    |        ExplorerAgent          |
    |   (browser-use wrapper)       |
    +-------------------------------+
    |                               |
    | - Injects QA system prompt    |
    | - Records all steps           |
    | - Processes into TestSession  |
    | - Uses BrowserFactory         |
    |                               |
    +-------------------------------+
```

### Key Backend Components

| Component | File | Purpose |
|-----------|------|---------|
| FastAPI App | `main.py` | HTTP/SSE endpoints |
| StreamingAgentRunner | `streaming_runner.py` | Task execution with SSE |
| BrowserFactory | `browser_factory.py` | Browser instantiation |
| UITestingService | `service.py` | Artifact generation |
| ExplorerAgent | `explorer_agent.py` | QA-focused browser-use wrapper |
| StepProcessor | `step_processor.py` | History processing |
| ReportGenerator | `report_generator.py` | HTML/JSON report generation |
| PlaywrightGenerator | `playwright_generator.py` | Test code generation |

---

## 5. BrowserFactory - Single Source of Truth

```
+============================================================================+
|                      BROWSER FACTORY ARCHITECTURE                          |
+============================================================================+

    All browser instantiation flows through BrowserFactory

    +--------------------------------------------------------------------+
    |                         BrowserFactory                              |
    +--------------------------------------------------------------------+
    |                                                                    |
    |   +------------------------------------------------------------+   |
    |   |              create(headless, config) -> BrowserResult      |   |
    |   +------------------------------------------------------------+   |
    |                               |                                    |
    |           +-------------------+-------------------+                |
    |           |                   |                   |                |
    |           v                   v                   v                |
    |   +---------------+   +---------------+   +---------------+        |
    |   | Strategy 1    |   | Strategy 2    |   | Strategy 3    |        |
    |   | BrowserSession|   | Browser Class |   | Context Mgr   |        |
    |   | + start()     |   | (Simple API)  |   | __aenter__    |        |
    |   +-------+-------+   +-------+-------+   +-------+-------+        |
    |           |                   |                   |                |
    |           | fail?             | fail?             | fail?          |
    |           +-------------------+-------------------+                |
    |                               |                                    |
    |                               v                                    |
    |                       +---------------+                            |
    |                       | Strategy 4    |                            |
    |                       | Agent Managed |                            |
    |                       | (No browser)  |                            |
    |                       +---------------+                            |
    |                                                                    |
    +--------------------------------------------------------------------+
                               |
                               v
    +--------------------------------------------------------------------+
    |                        BrowserResult                                |
    +--------------------------------------------------------------------+
    |  browser: Any              # BrowserSession | Browser | None       |
    |  browser_type: str         # "browser_session" | "browser" | ...   |
    |  strategy_used: str        # Which strategy succeeded              |
    +--------------------------------------------------------------------+
                               |
                               v
    +--------------------------------------------------------------------+
    |                     get_agent_kwargs(result)                        |
    +--------------------------------------------------------------------+
    |  Returns:                                                          |
    |  - {"browser_session": session} if browser_session type            |
    |  - {"browser": browser} if browser type                            |
    |  - {} if agent_managed                                             |
    +--------------------------------------------------------------------+
```

### Why BrowserFactory?

| Problem | Solution |
|---------|----------|
| CDP client not initialized errors | Graceful fallback to working strategy |
| Multiple instantiation patterns | Single source of truth |
| Inconsistent cleanup | Centralized `cleanup()` method |
| Hard to debug browser issues | One place for logging |

---

## 6. SSE Streaming Architecture

```
+============================================================================+
|                       SSE STREAMING FLOW                                   |
+============================================================================+

    FRONTEND                           BACKEND
    ========                           =======

    +------------------+               +---------------------------+
    |  React Component |               |    FastAPI Endpoint       |
    |  (UIAutomator)   |               |  POST /stream/basic-task  |
    +--------+---------+               +-------------+-------------+
             |                                       |
             |  1. POST request with task            |
             |-------------------------------------->|
             |                                       |
             |                         +-------------v-------------+
             |                         |  Create StreamingSession  |
             |                         +-------------+-------------+
             |                                       |
             |                         +-------------v-------------+
             |                         | Start Task (asyncio.task) |
             |                         +-------------+-------------+
             |                                       |
             |                         +-------------v-------------+
             |                         |  Return StreamingResponse |
             |<--------------------------------------|
             |                                       |
    +--------v---------+                             |
    | Open SSE Reader  |                             |
    +--------+---------+                             |
             |                                       |
             |         2. SSE Events (continuous)    |
             |<======================================|
             |                                       |
             |  data: {"type":"step_start",...}      |
             |<--------------------------------------|
             |                                       |
    +--------v---------+                             |
    |  Parse & Update  |                             |
    |  LogViewer UI    |                             |
    +--------+---------+                             |
             |                                       |
             |  data: {"type":"done",...}            |
             |<--------------------------------------|
             |                                       |
    +--------v---------+               +-------------v-------------+
    | onComplete()     |               |   cleanup_session()       |
    +------------------+               +---------------------------+
```

### StreamEvent Structure

```python
@dataclass
class StreamEvent:
    event_type: EventType    # step_start, step_action, done, etc.
    level: LogLevel          # info, success, warn, error, debug
    message: str             # Human-readable message
    timestamp: str           # ISO format datetime
    data: Optional[Dict]     # Additional structured data
    step_number: Optional    # Current step number
```

### Event Types

| Event | Description |
|-------|-------------|
| `step_start` | New step beginning |
| `step_thinking` | Agent's reasoning |
| `step_action` | Action being executed |
| `step_result` | Action outcome |
| `browser_state` | Current URL/title |
| `progress` | General progress |
| `error` | Error occurred |
| `done` | Task completed |

---

## 7. Agent Execution Flow

```
+============================================================================+
|                      COMPLETE AGENT EXECUTION FLOW                         |
+============================================================================+

    User Request: "Test the login functionality on example.com"

    [1] FRONTEND
    +-------------------------------------------------------------------+
    |  UIAutomator.tsx                                                  |
    |  User clicks "Run" -> POST /stream/basic-task                     |
    +-------------------------------------------------------------------+
                              |
                              v
    [2] FASTAPI ENDPOINT
    +-------------------------------------------------------------------+
    |  main.py: stream_basic_task()                                     |
    |  -> Creates StreamingSession                                      |
    |  -> Returns StreamingResponse                                     |
    +-------------------------------------------------------------------+
                              |
                              v
    [3] STREAMING RUNNER
    +-------------------------------------------------------------------+
    |  run_ui_testing_agent_task()                                      |
    |  1. Save metadata.json                                            |
    |  2. Create OutputConfig                                           |
    |  3. Create UITestingService                                       |
    |  4. Call service.explore_and_test()                               |
    +-------------------------------------------------------------------+
                              |
                              v
    [4] UI TESTING SERVICE
    +-------------------------------------------------------------------+
    |  explore_and_test(task, url, max_steps)                           |
    |  -> Creates ExplorerAgent                                         |
    |  -> Runs agent                                                    |
    |  -> Generates artifacts                                           |
    +-------------------------------------------------------------------+
                              |
                              v
    [5] EXPLORER AGENT
    +-------------------------------------------------------------------+
    |  ExplorerAgent.explore_and_test()                                 |
    |  1. BrowserFactory.create() -> Get browser                        |
    |  2. Build QA system prompt                                        |
    |  3. Create browser-use Agent                                      |
    |  4. agent.run(max_steps)                                          |
    |  5. Process history into TestSession                              |
    |  6. BrowserFactory.cleanup()                                      |
    +-------------------------------------------------------------------+
                              |
                              v
    [6] BROWSER-USE AGENT LOOP
    +-------------------------------------------------------------------+
    |  Step 1: [Think] Navigate to URL                                  |
    |          [Action] goto("https://example.com")                     |
    |          --> SSE: step_start, step_thinking, step_action          |
    |                                                                   |
    |  Step 2: [Think] Find login form                                  |
    |          [Action] click("Login button")                           |
    |          --> SSE: step_start, step_thinking, step_action          |
    |                                                                   |
    |  Step N: [Think] Task complete                                    |
    |          [Action] done("Login tested successfully")               |
    |          --> SSE: done                                            |
    +-------------------------------------------------------------------+
                              |
                              v
    [7] ARTIFACT GENERATION
    +-------------------------------------------------------------------+
    |  test_outputs/{session_id}/                                       |
    |  ├── metadata.json         # Task info                            |
    |  ├── raw_history.json      # Complete agent history               |
    |  ├── screenshots/          # Step screenshots                     |
    |  ├── reports/                                                     |
    |  │   ├── report.html       # Visual HTML report                   |
    |  │   └── report.json       # Machine-readable results             |
    |  ├── tests/                                                       |
    |  │   ├── test_*.py         # Generated Playwright tests           |
    |  │   └── conftest.py       # Pytest fixtures                      |
    |  └── agent_history.gif     # Recording video                      |
    +-------------------------------------------------------------------+
                              |
                              v
    [8] FRONTEND UPDATE
    +-------------------------------------------------------------------+
    |  LogViewer: Display each event in terminal                        |
    |  TestResultsPanel: Update statistics                              |
    |  ArtifactsViewer: Load screenshots, code, reports                 |
    +-------------------------------------------------------------------+
```

---

## 8. Data Flow Diagrams

### Request/Response Flow

```
    FRONTEND                    BACKEND                      BROWSER
    ========                    =======                      =======

    StreamingTask    -->    StreamingTask    -->    +---------------+
    Request                 Request                 | Agent.run()   |
    {                       {                       | - navigate    |
      task: string            task: str             | - click       |
      max_steps: number       max_steps: int        | - type        |
      headless: boolean       headless: bool        | - screenshot  |
    }                       }                       +---------------+
         |                        |                         |
         v                        v                         v
    StreamEvent      <--    StreamEvent      <--    AgentHistoryList
    {                       {                       {
      type: string            event_type              history: [...]
      level: string           level                 }
      message: string         message
      step?: number           step_number
      data?: object           data
    }                       }
```

### Artifact Generation Pipeline

```
    AgentHistoryList (from browser-use)
           |
           v
    +------------------+
    | StepProcessor    |  Extracts structured data
    +--------+---------+
             |
             v
    +------------------+
    | ProcessedStep[]  |  Normalized step data
    +--------+---------+
             |
    +--------+-----------------------------+
    |                  |                   |
    v                  v                   v
+----------+    +-------------+    +---------------+
|Screenshot|    |  Playwright |    |    Report     |
|  Saver   |    |  Generator  |    |   Generator   |
+----+-----+    +------+------+    +-------+-------+
     |                 |                   |
     v                 v                   v
screenshots/     tests/test_*.py    reports/report.html
                 tests/conftest.py  reports/report.json
```

---

## 9. API Contract

### SSE Streaming Endpoints

| Endpoint | Method | Request Body | Response |
|----------|--------|--------------|----------|
| `/stream/basic-task` | POST | `{task, max_steps, headless}` | SSE Stream |
| `/stream/extract-data` | POST | `{url, data_schema, max_items, max_steps, headless}` | SSE Stream |
| `/stream/research-topic` | POST | `{topic, depth, max_sources, max_steps, headless}` | SSE Stream |
| `/stream/compare-products` | POST | `{products[], aspects[], max_steps, headless}` | SSE Stream |
| `/stream/compare-pages` | POST | `{urls[], comparison_criteria, max_steps, headless}` | SSE Stream |

### Artifacts Endpoints

| Endpoint | Method | Response |
|----------|--------|----------|
| `/artifacts/{session_id}` | GET | `SessionArtifacts` |
| `/artifacts/{session_id}/file/{path}` | GET | File (binary) |
| `/artifacts/{session_id}/code` | GET | `{filename, content, path}` |
| `/sessions` | GET | `{sessions: SessionInfo[]}` |

### Response Models

```python
class SessionArtifacts:
    session_id: str
    output_directory: str
    artifacts: List[ArtifactInfo]
    html_report: Optional[str]
    json_report: Optional[str]
    playwright_code: Optional[str]
    screenshots: List[str]
    video: Optional[str]

class SessionInfo:
    session_id: str
    created_at: float  # timestamp
    has_report: bool
    task: Optional[str]
    max_steps: Optional[int]
```

---

## 10. File Organization

```
ai_apps_testing/
│
├── App.tsx                         # Main React app
├── index.html                      # HTML entry point
│
├── apps/
│   └── UIAutomator.tsx             # Main UI component
│
├── components/
│   ├── LogViewer.tsx               # Streaming terminal
│   ├── TestResultsPanel.tsx        # Test statistics
│   ├── ArtifactsViewer.tsx         # Screenshots, code, reports
│   ├── SessionBrowser.tsx          # History browser
│   ├── SessionComparison.tsx       # Compare sessions
│   ├── Sidebar.tsx                 # Navigation
│   └── Toast.tsx                   # Notifications
│
├── backend/
│   ├── main.py                     # FastAPI application
│   │
│   ├── advanced_browser_services/
│   │   ├── __init__.py             # Package exports
│   │   ├── base_service.py         # LLM + BaseAgentService
│   │   ├── streaming.py            # SSE infrastructure
│   │   └── streaming_runner.py     # StreamingAgentRunner
│   │
│   └── ui_testing_agent/
│       ├── __init__.py
│       ├── service.py              # UITestingService
│       ├── core/
│       │   ├── browser_factory.py  # BrowserFactory (SINGLE SOURCE OF TRUTH)
│       │   ├── explorer_agent.py   # ExplorerAgent
│       │   ├── step_processor.py   # History processor
│       │   └── selector_extractor.py
│       ├── generators/
│       │   ├── playwright_generator.py
│       │   └── report_generator.py
│       ├── models/
│       │   ├── output_config.py
│       │   ├── processed_step.py
│       │   ├── test_session.py
│       │   └── selector_info.py
│       └── prompts/
│           └── qa_engineer_prompt.py
│
├── test_outputs/                   # Generated artifacts
│   └── {session_id}/
│       ├── metadata.json
│       ├── raw_history.json
│       ├── screenshots/
│       ├── reports/
│       │   ├── report.html
│       │   └── report.json
│       ├── tests/
│       │   ├── test_*.py
│       │   └── conftest.py
│       └── agent_history.gif
│
└── docs/
    ├── ARCHITECTURE.md             # This document
    ├── ADVANCED_BROWSER_SERVICES.md
    └── CDP_GRACEFUL_FALLBACK_PLAN.md
```

---

## Summary

This architecture provides:

1. **Single Source of Truth** - BrowserFactory handles all browser instantiation
2. **Real-time Updates** - SSE streaming for live progress
3. **Artifact Generation** - Automated screenshots, reports, and Playwright tests
4. **Session Management** - History, comparison, and re-run capabilities
5. **Graceful Fallback** - Multiple browser initialization strategies

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| BrowserFactory pattern | Centralized browser creation with graceful fallback |
| SSE over WebSocket | Simpler, unidirectional, sufficient for progress updates |
| Streaming-first API | All tasks stream progress in real-time |
| Artifact persistence | All test runs saved for comparison and replay |
