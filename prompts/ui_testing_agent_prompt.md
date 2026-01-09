# Exploratory UI Testing Agent - Implementation Request

## Core Concept: Inverted Testing Flow

**This is NOT traditional test automation.** We're inverting the process:

```
TRADITIONAL (NOT THIS):
  Define Tests → Write Code → Execute → Report

OUR APPROACH (THIS):
  Explore & Test Live → Record Everything → Generate All Artifacts After
```

The agent acts like a **senior QA engineer doing exploratory testing**:
1. Receives high-level requirement
2. Navigates to the target, discovers testable elements/flows
3. Immediately tests while exploring (no pre-written scripts)
4. Records every action, assertion, and result in real-time
5. **AFTER completion**: Generates test cases, Playwright code, reports from recordings

---

## Browser-Use Capabilities to Leverage

### Built-in History System (USE THIS - DON'T REBUILD)

Browser-use already captures comprehensive execution history:

```python
# After agent.run(), history contains everything:
history: AgentHistoryList = await agent.run(max_steps=50)

# Each step in history.history contains:
for step in history.history:
    step.model_output      # AgentOutput: thinking, action list, memory
    step.result            # list[ActionResult]: success, error, extracted_content
    step.state             # BrowserStateHistory: url, title, tabs, screenshot_path
    step.metadata          # StepMetadata: timing info
```

### AgentHistory Structure (Per Step):
```python
class AgentHistory:
    model_output: AgentOutput | None   # LLM decision
    result: list[ActionResult]         # Execution results
    state: BrowserStateHistory         # Browser snapshot
    metadata: StepMetadata | None      # Timing

# AgentOutput contains:
class AgentOutput:
    thinking: str | None               # Internal reasoning
    evaluation_previous_goal: str      # Assessment of previous step
    memory: str                        # Agent's context
    next_goal: str                     # Next planned action
    action: list[ActionModel]          # Actions to execute

# ActionResult contains:
class ActionResult:
    is_done: bool | None               # Task completion flag
    success: bool | None               # Success status
    extracted_content: str | None      # Data extracted
    error: str | None                  # Error if failed

# BrowserStateHistory contains:
class BrowserStateHistory:
    url: str                           # Current page URL
    title: str                         # Page title
    tabs: list[TabInfo]                # All open tabs
    interacted_element: list[DOMInteractedElement | None]  # Elements clicked
    screenshot_path: str | None        # Path to screenshot PNG
```

### Rich Element Information (For Selector Extraction):
```python
class DOMInteractedElement:
    node_name: str                     # Tag: BUTTON, INPUT, A
    attributes: dict[str, str]         # id, class, name, data-testid, etc.
    x_path: str                        # Full XPath: html/body/div[2]/button[1]
    element_hash: int                  # Stable hash across reloads
    bounds: DOMRect                    # Position: x, y, width, height
    node_value: str                    # Text content
```

### Built-in Callbacks (For Real-Time Recording):
```python
agent = Agent(
    task=task,
    llm=llm,
    browser=browser,
    # USE THESE for real-time recording:
    register_new_step_callback=on_step,      # Called after each step
    register_done_callback=on_complete,       # Called when finished
    generate_gif=True,                        # Auto-record video
)
```

### Built-in Actions (Complete List):
```python
# Navigation
SearchAction(query: str, engine: str = 'duckduckgo')
NavigateAction(url: str, new_tab: bool = False)
GoBackAction()

# Interaction
ClickElementAction(index: int | coordinate_x/y)
InputTextAction(index: int, text: str, clear: bool = True)
UploadFileAction(index: int, path: str)

# Scrolling & Keys
ScrollAction(down: bool = True, pages: float = 1.0)
SendKeysAction(keys: str)  # "Enter", "Escape", "Control+a"
FindTextAction(text: str)  # Scroll to text

# Dropdowns
GetDropdownOptionsAction(index: int)
SelectDropdownOptionAction(index: int, text: str)

# Tabs
SwitchTabAction(tab_id: str)
CloseTabAction(tab_id: str)

# Data & Completion
ExtractAction(query: str, extract_links: bool = False)
DoneAction(text: str, success: bool = True)
ScreenshotAction()
WaitAction(seconds: int = 3)

# Files
WriteFileAction(file_name: str, content: str)
ReadFileAction(file_name: str)

# JavaScript
EvaluateAction(code: str)
```

---

## Implementation Architecture

```
backend/ui_testing_agent/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── test_scenario.py          # TestScenario, TestAssertion
│   ├── execution_session.py      # TestSession wrapping AgentHistoryList
│   └── output_config.py          # OutputConfig
├── core/
│   ├── __init__.py
│   ├── explorer_agent.py         # Main agent with QA-focused system prompt
│   ├── step_processor.py         # Processes AgentHistory → structured data
│   └── selector_extractor.py     # Extracts selectors from DOMInteractedElement
├── generators/
│   ├── __init__.py
│   ├── playwright_generator.py   # AgentHistoryList → Playwright code
│   ├── test_case_generator.py    # AgentHistoryList → formal test cases
│   └── report_generator.py       # HTML/JSON reports
├── service.py                    # Main UITestingService facade
└── prompts/
    └── qa_engineer_prompt.py     # System prompt for QA behavior
```

---

## Key Implementation Details

### 1. Explorer Agent (Wraps browser-use Agent)

```python
from browser_use import Agent, Browser
from browser_use.browser.session import BrowserSession
from langchain_google_genai import ChatGoogleGenerativeAI

class ExplorerAgent:
    """
    Wraps browser-use Agent with QA-focused system prompt and recording.
    """

    def __init__(
        self,
        model: str = "gemini-3-flash-preview",
        headless: bool = False,
        output_config: OutputConfig = None,
    ):
        self.llm = ChatGoogleGenerativeAI(model=model, temperature=0.5)
        self.browser = Browser(headless=headless)
        self.output_config = output_config or OutputConfig()
        self.recorded_steps: list[ProcessedStep] = []

    async def explore_and_test(
        self,
        task: str,
        url: str,
        max_steps: int = 50,
    ) -> TestSession:
        """
        Main entry: explore, test, then generate artifacts.
        """
        # QA-focused system prompt extension
        qa_system_prompt = self._build_qa_system_prompt(task, url)

        agent = Agent(
            task=f"Navigate to {url} and {task}",
            llm=self.llm,
            browser=self.browser,
            extend_system_message=qa_system_prompt,
            register_new_step_callback=self._on_step,
            register_done_callback=self._on_complete,
            generate_gif=self.output_config.capture_video,
            use_vision=True,
            max_actions_per_step=3,
        )

        # Execute exploration and testing
        history: AgentHistoryList = await agent.run(max_steps=max_steps)

        # Process history into structured test session
        session = self._process_history(history)

        # Generate all artifacts AFTER execution
        await self._generate_artifacts(session)

        return session

    def _build_qa_system_prompt(self, task: str, url: str) -> str:
        """System prompt that makes the agent think like a QA engineer."""
        return f"""
You are a Senior QA Engineer performing exploratory testing.

TARGET: {url}
TASK: {task}

TESTING APPROACH:
1. First, explore the page to understand what "{task}" involves
2. Identify all testable scenarios:
   - Happy path (main success flow)
   - Validation errors (empty fields, invalid inputs)
   - Edge cases (special characters, long text, boundary values)
   - Error handling (network issues, server errors)

3. For EACH scenario you test:
   - State what you're testing before doing it
   - Perform the actions
   - VERIFY the expected outcome (use extract to check results)
   - Note if it passed or failed

4. After testing a scenario, explicitly state:
   "SCENARIO [name]: [PASSED/FAILED] - [reason]"

5. Test at least:
   - 1 happy path scenario
   - 1-2 validation/error scenarios
   - Any edge cases relevant to the functionality

IMPORTANT:
- Actually VERIFY outcomes, don't just perform actions
- Use extract to check for success/error messages
- Test with both valid AND invalid data
- Document what you observe at each step
"""

    async def _on_step(self, agent: Agent):
        """Callback: process each step in real-time."""
        if agent.history.history:
            latest = agent.history.history[-1]
            processed = self._process_step(latest)
            self.recorded_steps.append(processed)

    def _process_step(self, step: AgentHistory) -> ProcessedStep:
        """Extract structured data from AgentHistory."""
        actions = []
        for i, action in enumerate(step.model_output.action if step.model_output else []):
            result = step.result[i] if i < len(step.result) else None

            # Extract selector info from interacted element
            interacted = (step.state.interacted_element[i]
                         if step.state.interacted_element and i < len(step.state.interacted_element)
                         else None)

            selector_info = self._extract_selectors(interacted) if interacted else None

            actions.append(ProcessedAction(
                action_type=type(action).__name__.replace('Action', '').lower(),
                action_params=action.model_dump() if hasattr(action, 'model_dump') else {},
                selector_info=selector_info,
                success=result.success if result else None,
                error=result.error if result else None,
                extracted_content=result.extracted_content if result else None,
            ))

        return ProcessedStep(
            step_number=step.metadata.step_number if step.metadata else len(self.recorded_steps),
            thinking=step.model_output.thinking if step.model_output else None,
            goal=step.model_output.next_goal if step.model_output else None,
            actions=actions,
            page_url=step.state.url,
            page_title=step.state.title,
            screenshot_path=step.state.screenshot_path,
            timestamp=step.metadata.step_start_time if step.metadata else None,
            duration_ms=int(step.metadata.duration_seconds * 1000) if step.metadata else None,
        )

    def _extract_selectors(self, element: DOMInteractedElement) -> SelectorInfo:
        """Extract multiple selector strategies from interacted element."""
        attrs = element.attributes or {}

        return SelectorInfo(
            # Best selectors first
            data_testid=attrs.get('data-testid') or attrs.get('data-test'),
            element_id=attrs.get('id'),
            name=attrs.get('name'),
            aria_label=attrs.get('aria-label'),

            # Fallback selectors
            xpath=element.x_path,
            text_content=element.node_value,
            tag_name=element.node_name.lower(),
            classes=attrs.get('class', '').split() if attrs.get('class') else [],

            # For playwright text selectors
            role=attrs.get('role'),

            # Stability hash
            element_hash=element.element_hash,
        )
```

### 2. Playwright Code Generator

```python
class PlaywrightGenerator:
    """
    Transforms recorded test session into executable Playwright-Python code.
    """

    def generate(self, session: TestSession) -> str:
        """Generate complete pytest file from session."""

        scenarios = self._group_into_scenarios(session.steps)

        code_parts = [
            self._generate_header(session),
            self._generate_imports(),
            self._generate_fixtures(),
            self._generate_helper_methods(),
        ]

        for scenario in scenarios:
            code_parts.append(self._generate_test_method(scenario))

        return "\n\n".join(code_parts)

    def _generate_header(self, session: TestSession) -> str:
        return f'''"""
Auto-generated Playwright tests from exploratory testing session.

Original Task: {session.task}
Target URL: {session.url}
Executed: {session.started_at.isoformat()}
Result: {session.passed}/{session.total_scenarios} scenarios passed

Run with: pytest {session.output_filename} -v
"""'''

    def _generate_imports(self) -> str:
        return '''import pytest
from playwright.sync_api import Page, expect
from typing import List'''

    def _generate_fixtures(self) -> str:
        return '''
@pytest.fixture(scope="function")
def page(browser):
    """Create a new page for each test."""
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()'''

    def _generate_helper_methods(self) -> str:
        return '''
class TestHelpers:
    """Helper methods for self-healing selectors."""

    @staticmethod
    def click_with_fallback(page: Page, selectors: List[str], description: str):
        """Try multiple selectors until one works."""
        for selector in selectors:
            try:
                page.click(selector, timeout=5000)
                return
            except Exception:
                continue
        raise Exception(f"Could not find element: {description}")

    @staticmethod
    def fill_with_fallback(page: Page, selectors: List[str], value: str, description: str):
        """Try multiple selectors for input fields."""
        for selector in selectors:
            try:
                page.fill(selector, value, timeout=5000)
                return
            except Exception:
                continue
        raise Exception(f"Could not find input: {description}")'''

    def _generate_test_method(self, scenario: TestScenario) -> str:
        """Generate a single test method from a scenario."""
        method_name = self._to_method_name(scenario.name)
        steps_code = []

        for step in scenario.steps:
            step_code = self._action_to_playwright(step)
            if step_code:
                # Add comment with original goal
                if step.goal:
                    steps_code.append(f"        # {step.goal}")
                steps_code.append(f"        {step_code}")

        return f'''
class Test{self._to_class_name(scenario.name)}(TestHelpers):
    """
    Scenario: {scenario.name}
    Result: {'PASSED' if scenario.passed else 'FAILED'}
    {f'Failure: {scenario.failure_reason}' if scenario.failure_reason else ''}
    """

    def test_{method_name}(self, page: Page):
{chr(10).join(steps_code)}'''

    def _action_to_playwright(self, step: ProcessedStep) -> str:
        """Convert a recorded action to Playwright code."""
        for action in step.actions:
            selectors = self._build_selector_list(action.selector_info)

            if action.action_type == 'navigate':
                url = action.action_params.get('url', '')
                return f'page.goto("{url}")'

            elif action.action_type == 'clickelement':
                if len(selectors) == 1:
                    return f'page.click("{selectors[0]}")'
                else:
                    return f'self.click_with_fallback(page, {selectors}, "{action.selector_info.text_content or "element"}")'

            elif action.action_type == 'inputtext':
                text = action.action_params.get('text', '')
                if len(selectors) == 1:
                    return f'page.fill("{selectors[0]}", "{text}")'
                else:
                    return f'self.fill_with_fallback(page, {selectors}, "{text}", "input field")'

            elif action.action_type == 'extract':
                # Convert to assertion if it was verification
                if step.extracted_content:
                    return f'# Verified: {step.extracted_content[:100]}'

            elif action.action_type == 'done':
                success = action.action_params.get('success', True)
                text = action.action_params.get('text', '')
                return f'# Test completed: {"PASSED" if success else "FAILED"} - {text[:100]}'

        return None

    def _build_selector_list(self, info: SelectorInfo) -> list[str]:
        """Build prioritized list of selectors for self-healing."""
        selectors = []

        # Priority order: data-testid > id > name > aria-label > text > xpath
        if info.data_testid:
            selectors.append(f'[data-testid="{info.data_testid}"]')

        if info.element_id:
            selectors.append(f'#{info.element_id}')

        if info.name:
            selectors.append(f'[name="{info.name}"]')

        if info.aria_label:
            selectors.append(f'[aria-label="{info.aria_label}"]')

        if info.text_content and info.tag_name in ['button', 'a']:
            selectors.append(f'{info.tag_name}:has-text("{info.text_content}")')

        if info.role and info.text_content:
            selectors.append(f'role={info.role}[name="{info.text_content}"]')

        # XPath as last resort
        if info.xpath and len(selectors) < 3:
            selectors.append(f'xpath={info.xpath}')

        return selectors if selectors else ['SELECTOR_NOT_FOUND']
```

### 3. Data Models

```python
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

class SelectorInfo(BaseModel):
    """Multiple selector strategies for an element."""
    data_testid: Optional[str] = None
    element_id: Optional[str] = None
    name: Optional[str] = None
    aria_label: Optional[str] = None
    xpath: Optional[str] = None
    text_content: Optional[str] = None
    tag_name: Optional[str] = None
    classes: list[str] = []
    role: Optional[str] = None
    element_hash: Optional[int] = None

class ProcessedAction(BaseModel):
    """Single action extracted from AgentHistory."""
    action_type: str
    action_params: dict
    selector_info: Optional[SelectorInfo] = None
    success: Optional[bool] = None
    error: Optional[str] = None
    extracted_content: Optional[str] = None

class ProcessedStep(BaseModel):
    """Processed step with all relevant data."""
    step_number: int
    thinking: Optional[str] = None
    goal: Optional[str] = None
    actions: list[ProcessedAction]
    page_url: str
    page_title: str
    screenshot_path: Optional[str] = None
    timestamp: Optional[float] = None
    duration_ms: Optional[int] = None

class TestScenario(BaseModel):
    """A logical test scenario grouped from steps."""
    scenario_id: str
    name: str
    description: str
    steps: list[ProcessedStep]
    passed: bool
    failure_reason: Optional[str] = None
    screenshots: list[str] = []

class TestSession(BaseModel):
    """Complete test session with all data."""
    session_id: str
    task: str
    url: str
    started_at: datetime
    completed_at: datetime

    # Raw data (from browser-use)
    raw_history: dict  # AgentHistoryList.model_dump()

    # Processed data
    steps: list[ProcessedStep]
    scenarios: list[TestScenario]

    # Summary
    total_scenarios: int
    passed: int
    failed: int

    # Generated artifacts paths
    playwright_code_path: Optional[str] = None
    report_path: Optional[str] = None
    output_filename: str = "test_generated.py"

class OutputConfig(BaseModel):
    """User-configurable output options."""
    # Code generation
    generate_playwright_code: bool = True
    playwright_style: Literal["pytest", "unittest"] = "pytest"
    include_selector_fallbacks: bool = True

    # Test documentation
    generate_test_cases: bool = True
    test_case_format: Literal["json", "yaml", "markdown"] = "json"

    # Reports
    generate_html_report: bool = True
    generate_json_report: bool = True

    # Evidence
    capture_video: bool = True  # Uses browser-use generate_gif

    # Output location
    output_directory: str = "./test_outputs"
```

### 4. Main Service Facade

```python
class UITestingService:
    """
    Main entry point for exploratory UI testing.

    Usage:
        service = UITestingService(output_config=OutputConfig())
        result = await service.explore_and_test(
            task="Test the 'Send a gift' functionality",
            url="https://gyvver.com"
        )
        print(f"Playwright tests: {result.playwright_code_path}")
    """

    def __init__(
        self,
        output_config: OutputConfig = None,
        model: str = "gemini-2.0-flash",
        headless: bool = False,
    ):
        self.output_config = output_config or OutputConfig()
        self.model = model
        self.headless = headless

    async def explore_and_test(
        self,
        task: str,
        url: str,
        max_steps: int = 50,
    ) -> TestSession:
        """
        Execute exploratory testing and generate all artifacts.

        1. Create ExplorerAgent with QA-focused prompt
        2. Run exploration and testing
        3. Process AgentHistoryList into TestSession
        4. Generate Playwright code, reports, test cases
        5. Return session with all artifact paths
        """
        agent = ExplorerAgent(
            model=self.model,
            headless=self.headless,
            output_config=self.output_config,
        )

        session = await agent.explore_and_test(
            task=task,
            url=url,
            max_steps=max_steps,
        )

        return session
```

---

## The Flow Visualized

```
┌─────────────────────────────────────────────────────────────────┐
│  USER INPUT                                                      │
│  task = "Test the 'Send a gift' functionality"                  │
│  url = "https://gyvver.com"                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  BROWSER-USE AGENT EXECUTION                                     │
│  • QA-focused system prompt injected via extend_system_message  │
│  • register_new_step_callback captures each step                │
│  • generate_gif=True records video                              │
│  • Agent explores, tests, verifies using built-in actions       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENT HISTORY (Built-in - Just Use It!)                        │
│  AgentHistoryList contains per step:                            │
│  • model_output.action → What actions were taken                │
│  • result → Success/failure, extracted content                  │
│  • state.interacted_element → Element info with xpath, attrs    │
│  • state.screenshot_path → Screenshot for evidence              │
│  • metadata → Timing information                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  POST-EXECUTION ARTIFACT GENERATION                              │
│  From AgentHistoryList, generate:                               │
│  • Playwright code (with self-healing selectors from xpath/attrs)│
│  • Test cases (from steps + verification results)               │
│  • HTML/JSON reports (from full session data)                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  OUTPUT FILES                                                    │
│  ./test_outputs/gyvver_gift/                                    │
│  ├── tests/test_send_gift.py      # Runnable Playwright tests   │
│  ├── test_cases/cases.json        # Formal test documentation   │
│  ├── reports/report.html          # Visual report               │
│  ├── recording.gif                # Video (from generate_gif)   │
│  └── session.json                 # Full session data           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Points: What to Build vs What to Use

### USE FROM BROWSER-USE (Don't Rebuild):
- ✅ `Agent` class for execution
- ✅ `AgentHistoryList` for complete history
- ✅ `register_new_step_callback` for real-time recording
- ✅ `generate_gif` for video recording
- ✅ `DOMInteractedElement` for element info (xpath, attributes)
- ✅ `BrowserStateHistory` for page state and screenshots
- ✅ All built-in actions (Click, Input, Navigate, Extract, etc.)

### BUILD NEW:
- 🔨 `ExplorerAgent` - Wrapper with QA-focused system prompt
- 🔨 `PlaywrightGenerator` - Transform history → Playwright code
- 🔨 `TestCaseGenerator` - Transform history → formal test cases
- 🔨 `ReportGenerator` - HTML/JSON reports
- 🔨 `SelectorExtractor` - Extract multiple selectors from `DOMInteractedElement`
- 🔨 Data models for processed steps and scenarios

---

## Acceptance Criteria

- [ ] Uses browser-use Agent with `extend_system_message` for QA behavior
- [ ] Uses `register_new_step_callback` for real-time step processing
- [ ] Extracts selectors from `DOMInteractedElement.attributes` and `x_path`
- [ ] Generates working Playwright-Python code from `AgentHistoryList`
- [ ] Generated code includes self-healing selector fallbacks
- [ ] Groups steps into logical test scenarios (happy path, error cases)
- [ ] Produces HTML report with screenshots from `BrowserStateHistory`
- [ ] All models use Pydantic v2

---

## Deliverables

1. All source files in `backend/ui_testing_agent/`
2. Working `service.py` with `UITestingService` class
3. `PlaywrightGenerator` that produces runnable pytest code
4. Example usage script

Start with the models, then `ExplorerAgent`, then generators. The key insight is: **browser-use already records everything - you just need to transform its output into the desired artifacts.**
