# Advanced Browser Services - Architecture Design

## Table of Contents

1. [System Overview](#1-system-overview)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Frontend Architecture](#3-frontend-architecture)
4. [Backend Architecture](#4-backend-architecture)
5. [Service Layer Design](#5-service-layer-design)
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
    |            |   geminiService.ts  |  <-- API Client Layer           |
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
    |       +-------+-------+                                            |
    |       |               |                                            |
    |       v               v                                            |
    |   +--------+    +-------------+                                    |
    |   |Advanced|    | Streaming   |                                    |
    |   |Browser |    | Runner      |                                    |
    |   |Service |    | (SSE)       |                                    |
    |   +---+----+    +------+------+                                    |
    |       |                |                                           |
    |       +-------+--------+                                           |
    |               |                                                    |
    |               v                                                    |
    |   +---------------------+                                          |
    |   | advanced_browser_   |                                          |
    |   |     services/       |  <-- Service Layer                       |
    |   +----------+----------+                                          |
    |              |                                                     |
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

### Frontend Service Layer

```
+============================================================================+
|                       geminiService.ts - API CLIENT                        |
+============================================================================+

    +-----------------------------------------------------------------+
    |                      SYNCHRONOUS APIs                            |
    |  (Request/Response - Returns complete result)                    |
    +-----------------------------------------------------------------+
    |                                                                  |
    |   runUIAutomator()      POST /run-ui-automator                   |
    |   extractData()         POST /extract-data                       |
    |   researchTopic()       POST /research-topic                     |
    |   compareProducts()     POST /compare-products                   |
    |   runParallelTasks()    POST /run-parallel-tasks                 |
    |   comparePages()        POST /compare-pages                      |
    |                                                                  |
    +-----------------------------------------------------------------+

    +-----------------------------------------------------------------+
    |                      STREAMING APIs (SSE)                        |
    |  (Real-time events via Server-Sent Events)                       |
    +-----------------------------------------------------------------+
    |                                                                  |
    |   streamBasicTask()         POST /stream/basic-task              |
    |   streamExtractData()       POST /stream/extract-data            |
    |   streamResearchTopic()     POST /stream/research-topic          |
    |   streamCompareProducts()   POST /stream/compare-products        |
    |   streamComparePages()      POST /stream/compare-pages           |
    |                                                                  |
    |   createStreamingConnection()  <-- Core SSE Handler              |
    |      |                                                           |
    |      +-- Handles: data: {json}\n\n format                        |
    |      +-- Parses: StreamingEvent objects                          |
    |      +-- Detects: 'done' event for completion                    |
    |      +-- Returns: cleanup() function for abort                   |
    |                                                                  |
    +-----------------------------------------------------------------+

    +-----------------------------------------------------------------+
    |                      ARTIFACTS APIs                              |
    |  (Session data and generated files)                              |
    +-----------------------------------------------------------------+
    |                                                                  |
    |   getSessionArtifacts()     GET /artifacts/{session_id}          |
    |   getArtifactUrl()          GET /artifacts/{id}/file/{path}      |
    |   getPlaywrightCode()       GET /artifacts/{id}/code             |
    |   listSessions()            GET /sessions                        |
    |                                                                  |
    +-----------------------------------------------------------------+
```

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
    |   |     REST API ENDPOINTS      |  |    SSE STREAMING ENDPOINTS  | |
    |   +-----------------------------+  +-----------------------------+ |
    |   | POST /run-ui-automator      |  | POST /stream/basic-task     | |
    |   | POST /extract-data          |  | POST /stream/extract-data   | |
    |   | POST /research-topic        |  | POST /stream/research-topic | |
    |   | POST /compare-products      |  | POST /stream/compare-*      | |
    |   | POST /run-parallel-tasks    |  +-----------------------------+ |
    |   | POST /compare-pages         |                                  |
    |   +-----------------------------+  +-----------------------------+ |
    |                                    |    ARTIFACTS ENDPOINTS       | |
    |   +-----------------------------+  +-----------------------------+ |
    |   |    GLOBAL INSTANCES         |  | GET /artifacts/{id}         | |
    |   +-----------------------------+  | GET /artifacts/{id}/file/*  | |
    |   | advanced_service            |  | GET /artifacts/{id}/code    | |
    |   |   = AdvancedBrowserService()|  | GET /sessions               | |
    |   |                             |  +-----------------------------+ |
    |   | streaming_runner            |                                  |
    |   |   = get_streaming_runner()  |                                  |
    |   +-----------------------------+                                  |
    |                                                                    |
    +====================================================================+
                            |
                            v
    +====================================================================+
    |                   SERVICE LAYER COMPONENTS                         |
    +====================================================================+

    +---------------------------+     +-------------------------------+
    |   AdvancedBrowserService  |     |    StreamingAgentRunner       |
    |       (Facade)            |     |        (SSE Engine)           |
    +---------------------------+     +-------------------------------+
    |                           |     |                               |
    | - run_task()              |     | - create_session()            |
    | - extract_data()          |     | - run_basic_task()            |
    | - research_topic()        |     | - run_data_extraction()       |
    | - compare_products()      |     | - run_research()              |
    | - compare_pages()         |     | - run_product_comparison()    |
    | - run_parallel_tasks()    |     | - run_page_comparison()       |
    |                           |     | - run_ui_testing_agent_task() |
    +-------------+-------------+     +---------------+---------------+
                  |                                   |
                  +----------------+------------------+
                                   |
                                   v
    +====================================================================+
    |                    SPECIALIZED AGENTS                              |
    +====================================================================+

    +-----------------+  +-------------------+  +----------------------+
    |  MultiTabAgent  |  |  ParallelAgent    |  |   ResearchAgent      |
    |                 |  |     Runner        |  |                      |
    +-----------------+  +-------------------+  +----------------------+
    | - run()         |  | - run_parallel()  |  | - research_topic()   |
    | - compare_pages |  | - run_same_task   |  | - compare_products() |
    |                 |  |   _on_sites()     |  | - fact_check()       |
    |                 |  | - batch_search()  |  |                      |
    +-----------------+  +-------------------+  +----------------------+
           |                    |                        |
           +--------------------+------------------------+
                               |
                               v
    +-----------------+  +-------------------------------------------+
    | DataExtraction  |  |              BaseAgentService             |
    |     Agent       |  +-------------------------------------------+
    +-----------------+  | - llm: ChatGoogle                         |
    | - extract()     |  | - browser_config: BrowserConfig           |
    | - extract_to    |  | - browser: Browser                        |
    |   _file()       |  | - _ensure_browser()                       |
    | - extract_from  |  | - close()                                 |
    |   _multiple_    |  +-------------------------------------------+
    |   urls()        |               ^
    +-----------------+               |
                                      |
    +====================================================================+
    |                       BASE CONFIGURATION                           |
    +====================================================================+

    +----------------------------+    +--------------------------------+
    |      get_gemini_llm()      |    |        BrowserConfig           |
    +----------------------------+    +--------------------------------+
    | Creates ChatGoogle         |    | - headless: bool               |
    | instance with:             |    | - disable_security: bool       |
    | - model name               |    | - window_width/height: int     |
    | - temperature              |    | - user_data_dir: str           |
    | - API key from env         |    | - allowed_domains: list        |
    +----------------------------+    | - create_browser() -> Browser  |
                                      +--------------------------------+
```

---

## 5. Service Layer Design

```
+============================================================================+
|                      SERVICE INHERITANCE HIERARCHY                         |
+============================================================================+

                            +-------------------+
                            | BaseAgentService  |
                            +-------------------+
                            | # llm             |
                            | # browser_config  |
                            | # browser         |
                            +-------------------+
                            | + _ensure_browser |
                            | + close()         |
                            +--------+----------+
                                     |
            +------------------------+------------------------+
            |                        |                        |
            v                        v                        v
    +---------------+      +------------------+      +------------------+
    | MultiTabAgent |      |  ResearchAgent   |      | DataExtraction   |
    +---------------+      +------------------+      |     Agent        |
    | + max_tabs    |      | + tools          |      +------------------+
    +---------------+      | + _research_notes|      | + tools          |
    | + run()       |      | + _sources       |      | + _extracted_    |
    | + compare_    |      +------------------+      |   data           |
    |   pages()     |      | + research_topic |      +------------------+
    +---------------+      | + compare_       |      | + extract()      |
                           |   products()     |      | + extract_to_    |
                           | + fact_check()   |      |   file()         |
                           +------------------+      | + extract_from_  |
                                                     |   multiple_urls()|
                                                     +------------------+


+============================================================================+
|                         PARALLEL AGENT RUNNER                              |
+============================================================================+

    +-----------------------------------------------------------------------+
    |                        ParallelAgentRunner                            |
    +-----------------------------------------------------------------------+
    |                                                                       |
    |    +-------------+      +--------------+      +-------------+         |
    |    |  AgentTask  |      |  AgentTask   |      |  AgentTask  |         |
    |    | task_id: 1  |      | task_id: 2   |      | task_id: 3  |         |
    |    +------+------+      +------+-------+      +------+------+         |
    |           |                    |                     |                |
    |           +--------------------+---------------------+                |
    |                                |                                      |
    |                                v                                      |
    |                   +------------------------+                          |
    |                   |  asyncio.Semaphore(3)  |  <-- max_concurrent      |
    |                   +------------------------+                          |
    |                                |                                      |
    |           +--------------------+---------------------+                |
    |           |                    |                     |                |
    |           v                    v                     v                |
    |    +------------+       +------------+        +------------+          |
    |    | Browser 1  |       | Browser 2  |        | Browser 3  |          |
    |    | + Agent 1  |       | + Agent 2  |        | + Agent 3  |          |
    |    +-----+------+       +-----+------+        +-----+------+          |
    |          |                    |                     |                 |
    |          v                    v                     v                 |
    |    +------------+       +------------+        +------------+          |
    |    |AgentResult |       |AgentResult |        |AgentResult |          |
    |    +------------+       +------------+        +------------+          |
    |                                                                       |
    |    Results collected via asyncio.gather()                             |
    +-----------------------------------------------------------------------+
```

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
             |                         |  session = create_session |
             |                         +-------------+-------------+
             |                                       |
             |                         +-------------v-------------+
             |                         | Start Task (asyncio.task) |
             |                         | run_ui_testing_agent_task |
             |                         +-------------+-------------+
             |                                       |
             |                         +-------------v-------------+
             |                         |  Return StreamingResponse |
             |                         |  media_type=text/event-   |
             |                         |           stream          |
             |<--------------------------------------|
             |                                       |
    +--------v---------+                             |
    | Open SSE Reader  |                             |
    | response.body.   |                             |
    |   getReader()    |                             |
    +--------+---------+                             |
             |                                       |
             |         2. SSE Events (continuous)    |
             |<======================================|
             |                                       |
             |  data: {"type":"step_start",...}\n\n  |
             |<--------------------------------------|
             |                                       |
    +--------v---------+                             |
    |  Parse & Dispatch|                             |
    |  onEvent(data)   |                             |
    +--------+---------+                             |
             |                                       |
             |  data: {"type":"step_action",...}\n\n |
             |<--------------------------------------|
             |                                       |
    +--------v---------+                             |
    | Update LogViewer |                             |
    | Add log entry    |                             |
    +--------+---------+                             |
             |                                       |
             |  data: {"type":"done",...}\n\n        |
             |<--------------------------------------|
             |                                       |
    +--------v---------+               +-------------v-------------+
    | onComplete()     |               |   cleanup_session()       |
    | Close connection |               |   Remove from registry    |
    +------------------+               +---------------------------+
```

### StreamEvent Structure

```
+============================================================================+
|                          STREAM EVENT TYPES                                |
+============================================================================+

    +------------------------------------------------------------------+
    |                      StreamEvent (Dataclass)                      |
    +------------------------------------------------------------------+
    |  event_type: EventType    # Type of event                        |
    |  level: LogLevel          # Severity (info/success/warn/error)   |
    |  message: str             # Human-readable message               |
    |  timestamp: str           # ISO format datetime                  |
    |  data: Optional[Dict]     # Additional structured data           |
    |  step_number: Optional    # Current step number                  |
    +------------------------------------------------------------------+

    EVENT TYPES                          LOG LEVELS
    ===========                          ==========

    +----------------+                   +-----------+
    | step_start     | New step begins   | info      |
    | step_thinking  | Agent reasoning   | success   |
    | step_action    | Action executing  | warn      |
    | step_result    | Action outcome    | error     |
    | browser_state  | URL/title update  | debug     |
    | progress       | General progress  +-----------+
    | error          | Error occurred    |
    | done           | Task completed    |
    +----------------+

    SSE WIRE FORMAT
    ===============

    data: {"type":"step_start","level":"info","message":"Starting step 1","timestamp":"2024-01-09T10:30:00","step":1}\n\n
    data: {"type":"step_action","level":"info","message":"Executing: click","timestamp":"2024-01-09T10:30:01","step":1,"data":{"action":"click","params":{"element":"button"}}}\n\n
    data: {"type":"done","level":"success","message":"Task completed","timestamp":"2024-01-09T10:30:30","data":{"success":true,"total_steps":5}}\n\n
```

### Callback Integration with browser-use

```
+============================================================================+
|                    BROWSER-USE CALLBACK INTEGRATION                        |
+============================================================================+

    +---------------------+
    |   browser-use       |
    |      Agent          |
    +----------+----------+
               |
               | Agent.run(max_steps=30)
               |
               v
    +----------+----------+
    |   For each step:    |
    |   1. Think          |
    |   2. Decide action  |
    |   3. Execute        |
    +----------+----------+
               |
               | register_new_step_callback
               |
               v
    +------------------------------+
    |  create_step_callback()      |
    +------------------------------+
    |                              |
    |  async def step_callback(    |
    |      browser_state,          |  <-- Current page state
    |      agent_output,           |  <-- Agent's decision
    |      step_num                |  <-- Step number
    |  ):                          |
    |      session.emit_step_start |
    |      session.emit_browser_   |
    |              state           |
    |      session.emit_thinking   |
    |      session.emit_action     |
    |                              |
    +------------------------------+
               |
               | On completion
               v
    +------------------------------+
    |  create_done_callback()      |
    +------------------------------+
    |                              |
    |  async def done_callback(    |
    |      history                 |  <-- Full AgentHistoryList
    |  ):                          |
    |      session.emit_done(      |
    |          summary,            |
    |          success             |
    |      )                       |
    |                              |
    +------------------------------+
```

---

## 7. Agent Execution Flow

```
+============================================================================+
|                      COMPLETE AGENT EXECUTION FLOW                         |
+============================================================================+

    User Request: "Search Google for Python tutorials"

    [1] FRONTEND
    +-----------------------------------------------------------------+
    |  UIAutomator.tsx                                                |
    |  +-----------------------------------------------------------+  |
    |  |  User clicks "Run" button                                 |  |
    |  |  handleRunTask() called                                   |  |
    |  |  streamBasicTask(task, onEvent, onError, onComplete)      |  |
    |  +-----------------------------------------------------------+  |
    +-----------------------------------------------------------------+
                              |
                              v
    [2] HTTP REQUEST
    +-----------------------------------------------------------------+
    |  POST /stream/basic-task                                        |
    |  Content-Type: application/json                                 |
    |  Body: {"task": "Search Google...", "max_steps": 30}            |
    +-----------------------------------------------------------------+
                              |
                              v
    [3] FASTAPI ENDPOINT (main.py)
    +-----------------------------------------------------------------+
    |  @app.post("/stream/basic-task")                                |
    |  async def stream_basic_task(request):                          |
    |      session = streaming_runner.create_session()                |
    |      return StreamingResponse(event_generator())                |
    +-----------------------------------------------------------------+
                              |
                              v
    [4] STREAMING RUNNER
    +-----------------------------------------------------------------+
    |  run_ui_testing_agent_task()                                    |
    |  +-----------------------------------------------------------+  |
    |  |  1. Save metadata.json (task, timestamp)                  |  |
    |  |  2. Create OutputConfig (screenshots, reports, etc.)      |  |
    |  |  3. Create UITestingService                               |  |
    |  |  4. Create step/done callbacks                            |  |
    |  |  5. Call service.explore_and_test()                       |  |
    |  +-----------------------------------------------------------+  |
    +-----------------------------------------------------------------+
                              |
                              v
    [5] UI TESTING SERVICE (explorer_agent.py)
    +-----------------------------------------------------------------+
    |  explore_and_test(task, url, max_steps)                         |
    |  +-----------------------------------------------------------+  |
    |  |  1. Create BrowserProfile(headless=False)                 |  |
    |  |  2. Create BrowserSession                                 |  |
    |  |  3. Build QA system prompt                                |  |
    |  |  4. Create browser-use Agent                              |  |
    |  |  5. agent.run(max_steps=30)                               |  |
    |  +-----------------------------------------------------------+  |
    +-----------------------------------------------------------------+
                              |
                              v
    [6] BROWSER-USE AGENT LOOP
    +-----------------------------------------------------------------+
    |                                                                 |
    |  +-- Step 1 ------------------------------------------------+   |
    |  |  [Think] "I need to go to Google and search"             |   |
    |  |  [Action] navigate_to("https://google.com")              |   |
    |  |  --> Callback: emit step_start, step_thinking, action    |   |
    |  +----------------------------------------------------------+   |
    |                              |                                  |
    |  +-- Step 2 ------------------------------------------------+   |
    |  |  [Think] "Page loaded, I see search box"                 |   |
    |  |  [Action] type_text("Python tutorials")                  |   |
    |  |  --> Callback: emit step_start, step_thinking, action    |   |
    |  +----------------------------------------------------------+   |
    |                              |                                  |
    |  +-- Step N ------------------------------------------------+   |
    |  |  [Think] "Task complete, found results"                  |   |
    |  |  [Action] done("Found 10 Python tutorial results")       |   |
    |  |  --> Callback: emit done                                 |   |
    |  +----------------------------------------------------------+   |
    |                                                                 |
    +-----------------------------------------------------------------+
                              |
                              v
    [7] ARTIFACT GENERATION
    +-----------------------------------------------------------------+
    |  test_outputs/{session_id}/                                     |
    |  +-----------------------------------------------------------+  |
    |  |  metadata.json         # Task info                        |  |
    |  |  raw_history.json      # Complete agent history           |  |
    |  |  screenshots/          # Step screenshots                 |  |
    |  |  reports/report.html   # Visual HTML report               |  |
    |  |  reports/report.json   # Machine-readable results         |  |
    |  |  tests/test_*.py       # Generated Playwright tests       |  |
    |  |  agent_history.gif     # Recording video                  |  |
    |  +-----------------------------------------------------------+  |
    +-----------------------------------------------------------------+
                              |
                              v
    [8] SSE EVENTS (Real-time to Frontend)
    +-----------------------------------------------------------------+
    |  data: {"type":"step_start","step":1,...}                       |
    |  data: {"type":"step_thinking","message":"I need to...",...}    |
    |  data: {"type":"step_action","message":"Navigating...",...}     |
    |  data: {"type":"browser_state","data":{"url":"google.com"}}     |
    |  ...                                                            |
    |  data: {"type":"done","data":{"success":true,"output_dir":...}} |
    +-----------------------------------------------------------------+
                              |
                              v
    [9] FRONTEND UPDATE
    +-----------------------------------------------------------------+
    |  LogViewer: Display each event in terminal                      |
    |  TestResultsPanel: Update statistics                            |
    |  ArtifactsViewer: Load screenshots, code, reports               |
    +-----------------------------------------------------------------+
```

---

## 8. Data Flow Diagrams

### Request/Response Flow

```
+============================================================================+
|                        DATA TRANSFORMATION FLOW                            |
+============================================================================+

    FRONTEND                    BACKEND                      BROWSER
    ========                    =======                      =======

    TypeScript                  Python                       CDP/Playwright
    Interface                   Pydantic Model               Actions
    ----------                  --------------               -------

    StreamingBasic    -->    StreamingTask    -->    +---------------+
    TaskParams               Request                 | Agent.run()   |
    {                        {                       | - navigate    |
      task: string             task: str             | - click       |
      max_steps: number        max_steps: int        | - type        |
      headless: boolean        headless: bool        | - screenshot  |
    }                        }                       +---------------+
         |                        |                         |
         v                        v                         v
    StreamingEvent  <--    StreamEvent      <--    AgentHistoryList
    {                      {                       {
      type: string           event_type            history: [
      level: string          level                   {model_output,
      message: string        message                  state,
      timestamp: string      timestamp                result}
      step?: number          step_number           ]
      data?: object          data                  }
    }                      }
         |                        |                         |
         v                        v                         v
    UI Components         TestSession              test_outputs/
    - LogViewer           - steps[]                - screenshots/
    - TestResults         - scenarios[]            - reports/
    - Artifacts           - statistics             - tests/
```

### Artifact Generation Pipeline

```
+============================================================================+
|                     ARTIFACT GENERATION PIPELINE                           |
+============================================================================+

    AgentHistoryList (from browser-use)
           |
           v
    +------------------+
    | StepProcessor    |  Extracts structured data from history
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
step_001.png     (pytest format)    reports/report.json
step_002.png
...              +-------------+
                 | conftest.py |
                 +-------------+

    All artifacts saved to: ./test_outputs/{session_id}/
```

---

## 9. API Contract

```
+============================================================================+
|                           API ENDPOINT REFERENCE                           |
+============================================================================+

    +=======================================================================+
    |                        REST ENDPOINTS                                  |
    +=======================================================================+

    POST /run-ui-automator
    ├── Request:  { instruction: string }
    └── Response: { steps: [], summary: string }

    POST /extract-data
    ├── Request:  { url, data_schema, max_items?, max_steps }
    └── Response: TaskResultResponse

    POST /research-topic
    ├── Request:  { topic, depth, max_sources, max_steps }
    └── Response: TaskResultResponse

    POST /compare-products
    ├── Request:  { products[], aspects[], max_steps }
    └── Response: TaskResultResponse

    POST /run-parallel-tasks
    ├── Request:  { tasks[], max_concurrent }
    └── Response: TaskResultResponse[]

    POST /compare-pages
    ├── Request:  { urls[], comparison_criteria, max_steps }
    └── Response: TaskResultResponse

    +=======================================================================+
    |                      STREAMING ENDPOINTS (SSE)                        |
    +=======================================================================+

    POST /stream/basic-task
    ├── Request:  { task, max_steps, headless }
    └── Response: text/event-stream (StreamingEvent[])

    POST /stream/extract-data
    ├── Request:  { url, data_schema, max_items?, max_steps, headless }
    └── Response: text/event-stream

    POST /stream/research-topic
    ├── Request:  { topic, depth, max_sources, max_steps, headless }
    └── Response: text/event-stream

    POST /stream/compare-products
    ├── Request:  { products[], aspects[], max_steps, headless }
    └── Response: text/event-stream

    POST /stream/compare-pages
    ├── Request:  { urls[], comparison_criteria, max_steps, headless }
    └── Response: text/event-stream

    +=======================================================================+
    |                       ARTIFACTS ENDPOINTS                              |
    +=======================================================================+

    GET /artifacts/{session_id}
    └── Response: SessionArtifacts

    GET /artifacts/{session_id}/file/{path}
    └── Response: FileResponse (binary)

    GET /artifacts/{session_id}/code
    └── Response: { filename, content, path }

    GET /sessions
    └── Response: { sessions: SessionInfo[] }

    +=======================================================================+
    |                      RESPONSE MODELS                                   |
    +=======================================================================+

    TaskResultResponse:
    {
        success: boolean
        task_type: string
        summary: string
        data: object
        steps: [{ action: string, status: string }]
        error?: string
    }

    SessionArtifacts:
    {
        session_id: string
        output_directory: string
        artifacts: ArtifactInfo[]
        html_report?: string
        json_report?: string
        playwright_code?: string
        screenshots: string[]
        video?: string
    }

    SessionInfo:
    {
        session_id: string
        created_at: number (timestamp)
        has_report: boolean
        task?: string
        max_steps?: number
    }
```

---

## 10. File Organization

```
+============================================================================+
|                          PROJECT FILE STRUCTURE                            |
+============================================================================+

ai_apps_testing/
│
├── frontend/
│   ├── services/
│   │   └── geminiService.ts        # API client (REST + SSE)
│   │
│   ├── components/
│   │   ├── LogViewer.tsx           # Streaming terminal
│   │   ├── TestResultsPanel.tsx    # Test statistics
│   │   ├── ArtifactsViewer.tsx     # Screenshots, code, reports
│   │   ├── SessionBrowser.tsx      # History browser
│   │   └── SessionComparison.tsx   # Compare sessions
│   │
│   ├── apps/
│   │   └── UIAutomator.tsx         # Main UI component
│   │
│   └── types.ts                    # TypeScript interfaces
│
├── backend/
│   ├── main.py                     # FastAPI application
│   │
│   ├── advanced_browser_services/
│   │   ├── __init__.py             # Package exports
│   │   ├── base_service.py         # LLM + BrowserConfig
│   │   ├── service_runner.py       # AdvancedBrowserService facade
│   │   ├── streaming.py            # SSE infrastructure
│   │   ├── streaming_runner.py     # Streaming task runner
│   │   ├── multi_tab_agent.py      # Multi-tab automation
│   │   ├── parallel_agents.py      # Concurrent execution
│   │   ├── research_agent.py       # Web research
│   │   ├── data_extraction_agent.py# Data scraping
│   │   └── test_agents.py          # Test suite
│   │
│   ├── ui_testing_agent/
│   │   ├── __init__.py
│   │   ├── service.py              # UITestingService
│   │   ├── core/
│   │   │   ├── explorer_agent.py   # Main ExplorerAgent
│   │   │   ├── step_processor.py   # History processor
│   │   │   └── selector_extractor.py
│   │   ├── generators/
│   │   │   ├── playwright_generator.py
│   │   │   └── report_generator.py
│   │   ├── models/
│   │   │   ├── output_config.py
│   │   │   ├── processed_step.py
│   │   │   ├── test_session.py
│   │   │   └── selector_info.py
│   │   └── prompts/
│   │       └── qa_engineer_prompt.py
│   │
│   └── browsers_services.py        # Legacy browser service
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
    ├── CDP_CLIENT_FIX_OPTIONS.md
    └── UI_TESTING_AGENT_OUTPUTS.md
```

---

## Summary

This architecture provides:

1. **Separation of Concerns** - Frontend handles UI, backend handles automation
2. **Real-time Updates** - SSE streaming for live progress
3. **Specialized Agents** - Different agents for different tasks
4. **Parallel Execution** - Run multiple browsers concurrently
5. **Artifact Generation** - Automated test code and reports
6. **Session Management** - History, comparison, and re-run capabilities

The system is designed to be extensible - new agent types can be added by inheriting from `BaseAgentService` and registering new endpoints in `main.py`.
