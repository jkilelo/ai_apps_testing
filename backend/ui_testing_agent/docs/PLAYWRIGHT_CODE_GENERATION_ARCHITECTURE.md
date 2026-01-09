# Playwright Code Generation Architecture

## Problem Statement

When the UI Testing Agent explores and tests a web application, it successfully executes actions (clicks, typing, navigation). **If the agent can execute an action, we have 100% of the information needed to replay that action offline.** However, the current implementation fails to generate working Playwright code because it:

1. Only captures partial action info (element index, not actual selectors)
2. Doesn't extract selector information from `interacted_element`
3. Generates comments instead of executable code

## Core Insight

When browser-use executes an action like clicking a button:

1. **The agent sees the page** - via accessibility tree with all elements
2. **The agent decides** - "click element at index 5"
3. **browser-use executes** - finds the actual DOM element, clicks it
4. **browser-use records** - stores the `interacted_element` with ALL its attributes

The `interacted_element` (DOMElementNode) contains:
- `xpath` - Full XPath to the element
- `attributes` - Dict with id, name, class, data-testid, aria-label, etc.
- `tag_name` - HTML tag (button, input, a, etc.)
- `text` - Text content
- `role` - ARIA role
- `is_visible`, `is_interactive` - State flags

**This is exactly what Playwright needs to locate elements!**

## Selector Priority (Most Reliable to Least)

1. **data-testid** - Specifically designed for testing, won't change
2. **id** - Unique identifier (but sometimes dynamic)
3. **name** - Good for form fields
4. **aria-label** - Accessibility attribute, stable
5. **role + text** - `getByRole('button', { name: 'Submit' })`
6. **text content** - `getByText('Click here')`
7. **CSS selector** - Can be brittle with class changes
8. **XPath** - Last resort, very brittle to DOM changes

## Architecture: Two-Phase Generation

### Phase 1: Rich Data Capture (During Agent Execution)

For each action the agent takes, capture:

```python
{
    "step_number": 1,
    "action_type": "click",  # click, input, navigate, scroll, etc.
    "action_params": {
        "index": 5,  # Original index (for reference only)
        "text": "playwright python testing"  # For input actions
    },
    "element": {
        # All selector options from interacted_element
        "xpath": "//button[@data-testid='search-btn']",
        "tag_name": "button",
        "attributes": {
            "id": "search-button",
            "data-testid": "search-btn",
            "aria-label": "Search",
            "class": "btn btn-primary",
            "name": null
        },
        "text": "Search",
        "role": "button"
    },
    "page_url": "https://www.google.com",
    "page_title": "Google",
    "success": true,
    "screenshot_path": "/path/to/screenshot.png"
}
```

### Phase 2: Playwright Code Generation (Post-Execution)

**Option A: Direct Template-Based Generation**

Map each action type to Playwright code using the captured selectors:

| Action Type | Playwright Code |
|-------------|-----------------|
| navigate | `page.goto(url)` |
| click | `page.click(selector)` or `page.get_by_role().click()` |
| input | `page.fill(selector, text)` |
| scroll | `page.mouse.wheel(0, delta)` |
| select | `page.select_option(selector, value)` |
| wait | `page.wait_for_timeout(ms)` |
| extract | `page.locator(selector).text_content()` (as assertion) |

Selector generation priority:
```python
def get_best_selector(element):
    attrs = element['attributes']

    # Priority 1: data-testid
    if attrs.get('data-testid'):
        return f'[data-testid="{attrs["data-testid"]}"]'

    # Priority 2: id
    if attrs.get('id'):
        return f'#{attrs["id"]}'

    # Priority 3: aria-label
    if attrs.get('aria-label'):
        return f'[aria-label="{attrs["aria-label"]}"]'

    # Priority 4: role + text (Playwright's getByRole)
    if element.get('role') and element.get('text'):
        return f'role={element["role"]}[name="{element["text"]}"]'

    # Priority 5: text content
    if element.get('text'):
        return f'text="{element["text"]}"'

    # Priority 6: name attribute (for inputs)
    if attrs.get('name'):
        return f'[name="{attrs["name"]}"]'

    # Priority 7: XPath (last resort)
    return f'xpath={element["xpath"]}'
```

**Option B: LLM-Assisted Code Generation (Recommended)**

Use a dedicated "Playwright Code Generator Agent" that:

1. Receives all captured action data
2. Has full Playwright API knowledge via system prompt
3. Generates clean, idiomatic Playwright code
4. **Immediately runs the generated code to verify it works**
5. If tests fail, analyzes the error and regenerates

This is more robust because the LLM can:
- Handle edge cases intelligently
- Generate better assertions
- Create readable, well-organized test code
- Self-correct when tests fail

## The Playwright Code Generator Agent

### Input
```json
{
    "task": "Test the search functionality",
    "url": "https://www.google.com",
    "steps": [
        {
            "action": "navigate",
            "url": "https://www.google.com"
        },
        {
            "action": "input",
            "selector_options": {
                "data_testid": null,
                "id": "APjFqb",
                "aria_label": "Search",
                "name": "q",
                "xpath": "//textarea[@name='q']",
                "text": null,
                "tag": "textarea",
                "role": "combobox"
            },
            "text": "playwright python testing"
        },
        {
            "action": "click",
            "selector_options": {
                "data_testid": null,
                "id": null,
                "aria_label": "Google Search",
                "name": "btnK",
                "xpath": "//input[@name='btnK']",
                "text": "Google Search",
                "tag": "input",
                "role": "button"
            }
        }
    ]
}
```

### System Prompt for Generator Agent
```
You are a Playwright test code generator. Given a sequence of browser actions
with element selector information, generate working Playwright-Python test code.

Rules:
1. Use the most reliable selector available (data-testid > id > aria-label > name > text > xpath)
2. Generate self-healing selectors with fallbacks when possible
3. Add appropriate waits for page loads and element visibility
4. Include assertions to verify actions succeeded
5. Organize code into clean pytest test functions
6. The code must run OFFLINE without any AI/LLM dependency

For each action, you have multiple selector options. Choose the most stable one.
```

### Output
```python
import pytest
from playwright.sync_api import Page, expect

class TestGoogleSearch:
    def test_search_playwright_python(self, page: Page):
        # Navigate to Google
        page.goto("https://www.google.com")

        # Enter search query
        search_box = page.get_by_role("combobox", name="Search")
        search_box.fill("playwright python testing")

        # Click search button
        page.get_by_role("button", name="Google Search").click()

        # Verify search results appear
        expect(page.locator("#search")).to_be_visible()
```

### Verification Loop

After generating code:

1. **Write code to temp file**
2. **Run with pytest**
3. **Check results**:
   - If PASS → Code is verified, save as final output
   - If FAIL → Feed error back to LLM, regenerate with fixes
4. **Max 3 iterations** to prevent infinite loops

## Implementation Components

### 1. EnhancedStepProcessor
Extracts rich action data from browser-use 0.11.x history:
- Action type and parameters
- Full element selector information from `interacted_element`
- Page URL and state
- Success/failure status

### 2. PlaywrightCodeGeneratorAgent
LLM-powered agent that:
- Receives captured action data
- Generates Playwright code
- Verifies by running tests
- Iterates on failures

### 3. SelectorExtractor (Enhanced)
Extracts all possible selectors from DOMElementNode:
- Prioritizes by reliability
- Handles special cases (dynamic IDs, etc.)
- Generates Playwright-specific selector syntax

### 4. TestRunner
Executes generated tests and captures results:
- Runs pytest programmatically
- Captures stdout/stderr
- Returns pass/fail status with details

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1: AGENT EXECUTION                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Browser-Use Agent ──► Executes Actions ──► Records History     │
│         │                                         │              │
│         ▼                                         ▼              │
│  ┌─────────────┐                         ┌──────────────┐       │
│  │ Agent sees  │                         │ For each     │       │
│  │ DOM tree    │                         │ action:      │       │
│  │ & decides   │                         │ - action_type│       │
│  │ on actions  │                         │ - element    │       │
│  └─────────────┘                         │ - url        │       │
│                                          │ - success    │       │
│                                          └──────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 PHASE 2: CODE GENERATION                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │ Rich Action    │───►│ Playwright Code │───►│ Generated    │ │
│  │ Data           │    │ Generator Agent │    │ Test Code    │ │
│  └────────────────┘    └─────────────────┘    └──────────────┘ │
│                                                      │          │
│                                                      ▼          │
│                                              ┌──────────────┐   │
│                                              │ Run Tests    │   │
│                                              │ (pytest)     │   │
│                                              └──────────────┘   │
│                                                      │          │
│                              ┌────────────────┬──────┴──────┐   │
│                              ▼                ▼             │   │
│                         ┌────────┐      ┌────────┐          │   │
│                         │ PASS   │      │ FAIL   │──────────┘   │
│                         │        │      │        │  (retry)     │
│                         └────────┘      └────────┘              │
│                              │                                   │
│                              ▼                                   │
│                    ┌─────────────────┐                          │
│                    │ VERIFIED CODE   │                          │
│                    │ (100% working)  │                          │
│                    └─────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

## Why This Works

1. **Complete Information**: We capture everything the agent knows about each element
2. **Multiple Selector Options**: If one selector fails, others can work
3. **Verification Loop**: Generated code is tested, not just written
4. **Self-Healing**: The LLM can fix issues and try alternative approaches
5. **Offline Replay**: Final code has zero AI dependency

## Success Criteria

The generated Playwright tests must:
1. ✅ Execute successfully without any LLM/AI
2. ✅ Reproduce the exact same actions the agent performed
3. ✅ Use stable selectors that survive minor UI changes
4. ✅ Include appropriate waits and assertions
5. ✅ Be verifiable by running them immediately after generation
