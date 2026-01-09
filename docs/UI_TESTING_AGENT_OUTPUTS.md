# UI Testing Agent - Outputs & Reports Reference

## Overview

The UI Testing Agent (`backend/ui_testing_agent`) provides comprehensive outputs for browser automation testing, including real-time streaming, generated artifacts, and structured data models.

---

## 1. Real-time Streaming Events (SSE)

Streamed during execution via `/stream/basic-task` endpoint.

### Event Types

| Event Type | Level | Description | Use Case |
|------------|-------|-------------|----------|
| `step_start` | info | New step beginning | Show step number, update progress |
| `step_thinking` | debug | Agent's reasoning | Display AI thinking process |
| `step_action` | info | Action being executed | Show current action (click, type, etc.) |
| `step_result` | success/error | Action outcome | Show success/failure with details |
| `browser_state` | info | Current browser state | Display URL, page title |
| `progress` | info | Overall progress | Update progress bar |
| `error` | error | Error messages | Show in red, alert user |
| `done` | success | Task completion | Final summary, show results |

### Event Data Structure

```typescript
interface StreamingEvent {
    type: 'step_start' | 'step_thinking' | 'step_action' | 'step_result' | 'browser_state' | 'error' | 'done' | 'progress';
    level: 'info' | 'success' | 'warn' | 'error' | 'debug';
    message: string;
    timestamp: string;
    step?: number;
    data?: Record<string, unknown>;
}
```

---

## 2. Generated Artifacts (Files)

All artifacts are saved to `./test_outputs/{session_id}/`

| Artifact | Location | Format | Description |
|----------|----------|--------|-------------|
| Playwright Tests | `tests/test_*.py` | Python | Self-healing test code with fallback selectors |
| Conftest | `tests/conftest.py` | Python | Pytest fixtures for Playwright |
| Test Cases | `test_cases.{json\|yaml\|md\|feature}` | Multiple | Formal test documentation |
| HTML Report | `reports/report.html` | HTML | Visual report with embedded screenshots |
| JSON Report | `reports/report.json` | JSON | Machine-readable test results |
| Screenshots | `screenshots/step_XXX.png` | PNG | Per-step screenshots |
| Raw History | `raw_history.json` | JSON | Complete AgentHistoryList for debugging |
| Video | `agent_history.gif` | GIF | Recording of the test session |

---

## 3. TestSession Data Model

The main result object returned by `UITestingService.explore_and_test()`.

```
TestSession
├── session_id: string          # Unique identifier
├── task: string                # Original task description
├── url: string                 # Target URL tested
│
├── Timing
│   ├── started_at: datetime
│   ├── completed_at: datetime
│   └── duration_seconds: float
│
├── Statistics
│   ├── total_steps: int
│   ├── total_actions: int
│   ├── total_scenarios: int
│   ├── passed: int
│   ├── failed: int
│   └── pass_rate: float (%)
│
├── steps: ProcessedStep[]
│   ├── step_number: int
│   ├── thinking: string        # Agent's internal reasoning
│   ├── goal: string            # Agent's stated goal
│   ├── evaluation: string      # Evaluation of previous step
│   ├── memory: string          # Agent's context
│   ├── actions: ProcessedAction[]
│   │   ├── action_type: string (click, input, navigate, etc.)
│   │   ├── action_params: dict
│   │   ├── selector_info: SelectorInfo
│   │   │   ├── css_selector: string
│   │   │   ├── xpath: string
│   │   │   ├── text_content: string
│   │   │   ├── aria_label: string
│   │   │   └── role: string
│   │   ├── success: boolean
│   │   ├── error: string
│   │   └── extracted_content: string
│   ├── page_url: string
│   ├── page_title: string
│   ├── screenshot_path: string
│   ├── timestamp: float
│   └── duration_ms: int
│
├── scenarios: TestScenario[]
│   ├── scenario_id: string
│   ├── name: string
│   ├── description: string
│   ├── scenario_type: string   # happy_path, validation, error_handling, edge_case
│   ├── steps: ProcessedStep[]
│   ├── passed: boolean
│   ├── failure_reason: string
│   ├── failure_step: int
│   ├── screenshots: string[]
│   ├── start_url: string
│   ├── end_url: string
│   └── duration_ms: int
│
└── Artifact Paths
    ├── playwright_code_path: string
    ├── test_cases_path: string
    ├── html_report_path: string
    ├── json_report_path: string
    ├── video_path: string
    ├── screenshots_dir: string
    └── output_directory: string
```

---

## 4. OutputConfig Options

Configurable via `OutputConfig` class in `models/output_config.py`.

### Code Generation
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `generate_playwright_code` | bool | true | Generate Playwright-Python tests |
| `playwright_style` | "pytest" \| "unittest" | "pytest" | Test framework style |
| `include_selector_fallbacks` | bool | true | Self-healing fallback selectors |
| `include_comments` | bool | true | Descriptive comments in code |
| `max_selectors_per_element` | int | 4 | Max fallback selectors |

### Documentation
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `generate_test_cases` | bool | true | Generate test documentation |
| `test_case_format` | "json" \| "yaml" \| "markdown" \| "gherkin" | "json" | Documentation format |
| `group_scenarios` | bool | true | Group steps into scenarios |

### Reports
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `generate_html_report` | bool | true | Visual HTML report |
| `generate_json_report` | bool | true | Machine-readable JSON |

### Evidence
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `capture_video` | bool | true | GIF recording |
| `save_screenshots` | bool | true | Per-step screenshots |
| `save_raw_history` | bool | true | Debug JSON dump |

### Output Location
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `output_directory` | string | "./test_outputs" | Base output directory |
| `create_session_subdir` | bool | true | Create timestamped subdirs |

---

## 5. Frontend UI Components Mapping

| UI Component | Data Source | Priority |
|--------------|-------------|----------|
| **Execution Terminal** | SSE events (real-time) | P0 - Core |
| **Progress Indicator** | step/max_steps from events | P0 - Core |
| **Test Results Summary** | passed/failed/pass_rate | P1 - Essential |
| **Scenario List** | scenarios[] with status | P1 - Essential |
| **Step Timeline** | steps[] with actions | P2 - Enhanced |
| **Screenshot Gallery** | screenshots from dir | P2 - Enhanced |
| **Code Viewer** | playwright_code_path content | P2 - Enhanced |
| **HTML Report** | iframe or link to report | P2 - Enhanced |
| **Video Player** | GIF from video_path | P3 - Nice-to-have |
| **Download Panel** | All artifact paths | P3 - Nice-to-have |

---

## 6. Implementation Phases

### Phase 1: Enhanced Streaming Terminal - COMPLETED
- [x] Basic log streaming
- [x] Color-coded message types (Goal, Action, Result, Error)
- [x] Step progress indicator (gradient progress bar)
- [x] Collapsible step sections (Grouped view mode)
- [x] Auto-scroll with pause on hover
- [x] View mode toggle (Stream / Grouped)
- [x] Footer stats (events, steps, errors, success count)

### Phase 2: Test Results Panel - COMPLETED
- [x] Summary cards (Steps, Passed, Failed, Pass Rate)
- [x] Step list with expand/collapse
- [x] Action breakdown per step
- [x] Failure highlighting (red background, error messages)
- [x] Running state indicator with progress bar
- [x] Output directory display

### Phase 3: Artifacts Viewer - COMPLETED
- [x] Screenshot gallery with lightbox
- [x] Generated code viewer with syntax highlighting
- [x] HTML report embed/link
- [x] Download buttons for all artifacts
- [x] GIF/Video playback in Reports tab

### Phase 4: Advanced Features - IN PROGRESS
- [ ] Comparison views
- [x] History/session browser
- [x] Re-run capabilities

---

## 7. Changelog

### v1.1.0 - Enhanced Streaming Terminal (Phase 1)
**Date:** 2026-01-09

**Files Changed:**
- `types.ts` - Added `LogLevel`, `EventType` types; Extended `ExecutionLog` interface
- `components/LogViewer.tsx` - Complete rewrite with enhanced features
- `apps/UIAutomator.tsx` - Updated event handling to pass full metadata

**New Features:**
1. **Color-Coded Event Types** with icons:
   | Event | Color | Icon | Label |
   |-------|-------|------|-------|
   | step_start | Purple | flag | STEP |
   | step_thinking | Cyan | brain | GOAL |
   | step_action | Amber | bolt | ACTION |
   | step_result | Green | check-circle | RESULT |
   | browser_state | Blue | globe | BROWSER |
   | progress | Gray | spinner | INFO |
   | error | Red | exclamation-triangle | ERROR |
   | done | Green | trophy | DONE |

2. **Progress Bar** - Gradient bar (blue→purple) showing step progress
3. **View Modes** - Toggle between Stream (real-time) and Grouped (by step)
4. **Auto-Scroll Control** - Toggle button, auto-pauses when user scrolls up
5. **Footer Stats** - Total events, steps, error count, success count
6. **Step Counter** - Shows "Step X/Y" in terminal header

### v1.2.0 - Test Results Panel (Phase 2)
**Date:** 2026-01-09

**Files Changed:**
- `components/TestResultsPanel.tsx` - New component for displaying test results
- `apps/UIAutomator.tsx` - Integrated TestResultsPanel, removed old renderResult

**New Features:**
1. **Summary Cards** - Four stat cards showing:
   - Total Steps (blue)
   - Passed Steps (green)
   - Failed Steps (red)
   - Pass Rate % (color-coded by threshold)

2. **Running State Indicator**
   - "Running..." badge when task is in progress
   - Progress bar showing current step / max steps
   - "Completed" or "Failed" badge when done

3. **Step Breakdown List**
   - Collapsible step entries
   - Step number and goal display
   - Action count per step
   - Pass/fail icon for each step

4. **Expanded Step Details**
   - List of actions with bolt icons
   - Error messages highlighted in red box
   - Failure steps have pink background

5. **Footer Stats**
   - Total actions count
   - Output directory path (when available)

### v1.3.0 - Artifacts Viewer (Phase 3)
**Date:** 2026-01-09

**Files Changed:**
- `components/ArtifactsViewer.tsx` - New component for viewing generated artifacts
- `services/geminiService.ts` - Added artifacts API functions
- `backend/main.py` - Added artifacts endpoints
- `backend/advanced_browser_services/streaming.py` - Added session_id to done event
- `backend/advanced_browser_services/streaming_runner.py` - Emit done event with output_directory
- `apps/UIAutomator.tsx` - Integrated ArtifactsViewer component

**New Features:**
1. **Screenshot Gallery**
   - Grid layout of step screenshots
   - Lightbox modal with keyboard navigation (arrow keys, escape)
   - Step number overlay on each thumbnail

2. **Code Viewer**
   - Syntax-highlighted Playwright Python code
   - Copy to clipboard button
   - Download code file button
   - Filename display in header

3. **Reports Tab**
   - Embedded HTML report iframe
   - Open in new tab button
   - JSON report download
   - GIF recording playback

4. **Downloads Tab**
   - Full list of all artifacts
   - File type icons and colors
   - File size display
   - Individual download buttons

**Backend Endpoints Added:**
- `GET /artifacts/{session_id}` - List all session artifacts
- `GET /artifacts/{session_id}/file/{path}` - Serve individual artifact files
- `GET /artifacts/{session_id}/code` - Get Playwright code content
- `GET /sessions` - List all test sessions

### v1.4.0 - Session History & Re-run (Phase 4)
**Date:** 2026-01-09

**Files Changed:**
- `components/SessionBrowser.tsx` - New component for browsing past test sessions
- `apps/UIAutomator.tsx` - Added header with history toggle button
- `backend/advanced_browser_services/streaming_runner.py` - Save task metadata
- `backend/main.py` - Return task info in sessions list
- `services/geminiService.ts` - Extended SessionInfo with task fields

**New Features:**
1. **Session History Browser**
   - List all past test sessions with timestamps
   - Session status indicators (has report, pending)
   - Click to view session artifacts
   - Refresh button to reload sessions
   - Task preview for each session

2. **Re-run Capabilities**
   - Task stored in session metadata.json
   - Re-run button on sessions with stored tasks
   - Loads task back into input and switches to basic mode

3. **UI Header**
   - Added "UI Automator" title
   - Toggle button for session history panel

---

## 8. File Locations

- Backend Service: `backend/ui_testing_agent/service.py`
- Models: `backend/ui_testing_agent/models/`
- Generators: `backend/ui_testing_agent/generators/`
- Streaming: `backend/advanced_browser_services/streaming_runner.py`
- Streaming Events: `backend/advanced_browser_services/streaming.py`
- Main API: `backend/main.py`
- Frontend Service: `services/geminiService.ts`
- Frontend UI: `apps/UIAutomator.tsx`
- Log Viewer: `components/LogViewer.tsx`
- Results Panel: `components/TestResultsPanel.tsx`
- Artifacts Viewer: `components/ArtifactsViewer.tsx`
- Session Browser: `components/SessionBrowser.tsx`
