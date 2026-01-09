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

### Phase 1: Enhanced Streaming Terminal (Current)
- [x] Basic log streaming
- [ ] Color-coded message types (Goal, Action, Result, Error)
- [ ] Step progress indicator
- [ ] Collapsible step sections
- [ ] Auto-scroll with pause on hover

### Phase 2: Test Results Panel
- [ ] Summary cards (passed/failed/rate)
- [ ] Scenario list with expand/collapse
- [ ] Step-by-step breakdown
- [ ] Failure highlighting

### Phase 3: Artifacts Viewer
- [ ] Screenshot gallery with lightbox
- [ ] Generated code viewer with syntax highlighting
- [ ] HTML report embed/link
- [ ] Download buttons for all artifacts

### Phase 4: Advanced Features
- [ ] Video playback (GIF)
- [ ] Comparison views
- [ ] History/session browser
- [ ] Re-run capabilities

---

## File Locations

- Backend Service: `backend/ui_testing_agent/service.py`
- Models: `backend/ui_testing_agent/models/`
- Generators: `backend/ui_testing_agent/generators/`
- Streaming: `backend/advanced_browser_services/streaming_runner.py`
- Frontend Service: `services/geminiService.ts`
- Frontend UI: `apps/UIAutomator.tsx`
