"""
Playwright Generator - Transforms recorded test sessions into executable Playwright-Python code.
"""

import re
from datetime import datetime
from typing import Optional

from ..models.test_session import TestSession
from ..models.test_scenario import TestScenario
from ..models.processed_step import ProcessedStep
from ..models.processed_action import ProcessedAction
from ..models.output_config import OutputConfig
from ..core.selector_extractor import SelectorExtractor


class PlaywrightGenerator:
    """
    Generates executable Playwright-Python test code from recorded test sessions.

    The generated code:
    - Is self-contained and runs without any LLM
    - Uses pytest as the test framework
    - Includes self-healing selector fallbacks
    - Has proper docstrings and comments
    """

    def __init__(self, config: Optional[OutputConfig] = None):
        """
        Initialize the Playwright generator.

        Args:
            config: Output configuration options
        """
        self.config = config or OutputConfig()
        self.selector_extractor = SelectorExtractor()

    def generate(self, session: TestSession) -> str:
        """
        Generate complete Playwright pytest file from a test session.

        Args:
            session: TestSession with recorded steps and scenarios

        Returns:
            Complete Python test file as string
        """
        parts = [
            self._generate_header(session),
            self._generate_imports(),
            self._generate_conftest_note(),
            self._generate_helper_class(),
        ]

        # Generate test class for each scenario
        for scenario in session.scenarios:
            parts.append(self._generate_test_class(scenario, session))

        return "\n\n".join(parts)

    def _generate_header(self, session: TestSession) -> str:
        """Generate file header with metadata."""
        return f'''"""
Auto-generated Playwright tests from UI Testing Agent exploratory session.

Original Task: {session.task}
Target URL: {session.url}
Session ID: {session.session_id}
Generated: {datetime.now().isoformat()}

Test Results:
- Total Scenarios: {session.total_scenarios}
- Passed: {session.passed}
- Failed: {session.failed}
- Pass Rate: {session.pass_rate:.1f}%

Run with:
    pytest {session.output_filename} -v
    pytest {session.output_filename} -v --headed  # To see browser

This code runs OFFLINE without any LLM dependency.
"""'''

    def _generate_imports(self) -> str:
        """Generate import statements."""
        return '''import pytest
from playwright.sync_api import Page, expect, Browser, BrowserContext
from typing import List, Optional
import re'''

    def _generate_conftest_note(self) -> str:
        """Generate note about conftest.py requirement."""
        return '''
# NOTE: This test requires a conftest.py with browser fixtures.
# If you don't have one, add this to conftest.py in the same directory:
#
# import pytest
# from playwright.sync_api import sync_playwright
#
# @pytest.fixture(scope="session")
# def browser():
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=True)
#         yield browser
#         browser.close()
#
# @pytest.fixture(scope="function")
# def page(browser):
#     context = browser.new_context()
#     page = context.new_page()
#     yield page
#     context.close()
'''

    def _generate_helper_class(self) -> str:
        """Generate helper class with self-healing methods."""
        if not self.config.include_selector_fallbacks:
            return ''

        return '''
class SelfHealingHelpers:
    """
    Helper methods for self-healing element selection.

    These methods try multiple selectors until one works,
    providing resilience against UI changes.
    """

    @staticmethod
    def click_with_fallback(
        page: Page,
        selectors: List[str],
        description: str = "element",
        timeout: int = 5000
    ) -> None:
        """
        Click an element, trying multiple selectors until one works.

        Args:
            page: Playwright page object
            selectors: List of selectors to try (in priority order)
            description: Human-readable element description for error messages
            timeout: Timeout per selector attempt in milliseconds
        """
        last_error = None
        for selector in selectors:
            try:
                page.click(selector, timeout=timeout)
                return
            except Exception as e:
                last_error = e
                continue
        raise Exception(f"Could not find {description}. Tried: {selectors}. Last error: {last_error}")

    @staticmethod
    def fill_with_fallback(
        page: Page,
        selectors: List[str],
        value: str,
        description: str = "input field",
        timeout: int = 5000
    ) -> None:
        """
        Fill an input, trying multiple selectors until one works.

        Args:
            page: Playwright page object
            selectors: List of selectors to try
            value: Value to fill
            description: Human-readable element description
            timeout: Timeout per selector attempt
        """
        last_error = None
        for selector in selectors:
            try:
                page.fill(selector, value, timeout=timeout)
                return
            except Exception as e:
                last_error = e
                continue
        raise Exception(f"Could not find {description}. Tried: {selectors}. Last error: {last_error}")

    @staticmethod
    def get_element_with_fallback(
        page: Page,
        selectors: List[str],
        description: str = "element",
        timeout: int = 5000
    ):
        """
        Get a locator for an element, trying multiple selectors.

        Returns the first locator that finds an element.
        """
        for selector in selectors:
            try:
                locator = page.locator(selector)
                locator.wait_for(timeout=timeout)
                return locator
            except Exception:
                continue
        raise Exception(f"Could not find {description}. Tried: {selectors}")'''

    def _generate_test_class(self, scenario: TestScenario, session: TestSession) -> str:
        """Generate a test class for a scenario."""
        class_name = self._to_class_name(scenario.name)
        method_name = self._to_method_name(scenario.name)

        # Generate test method body
        test_body = self._generate_test_body(scenario)

        # Determine base class
        base_class = "(SelfHealingHelpers)" if self.config.include_selector_fallbacks else ""

        return f'''
class Test{class_name}{base_class}:
    """
    Test Scenario: {scenario.name}
    Type: {scenario.scenario_type}
    Original Result: {"PASSED" if scenario.passed else "FAILED"}
    {f"Failure Reason: {scenario.failure_reason}" if scenario.failure_reason else ""}

    Generated from exploratory testing session: {session.session_id}
    """

    def test_{method_name}(self, page: Page):
        """
        {scenario.description}

        Steps:
        {self._format_steps_docstring(scenario.steps)}
        """
{test_body}'''

    def _generate_test_body(self, scenario: TestScenario) -> str:
        """Generate the test method body from scenario steps."""
        lines = []
        indent = "        "  # 8 spaces for method body

        for step in scenario.steps:
            # Add goal as comment
            if step.goal and self.config.include_comments:
                lines.append(f"{indent}# {step.goal}")

            # Generate code for each action
            for action in step.actions:
                action_code = self._action_to_code(action, indent)
                if action_code:
                    lines.append(action_code)

            # Add blank line between steps
            lines.append("")

        # Remove trailing blank line
        while lines and lines[-1] == "":
            lines.pop()

        return "\n".join(lines) if lines else f"{indent}pass  # No actions recorded"

    def _action_to_code(self, action: ProcessedAction, indent: str) -> Optional[str]:
        """Convert a ProcessedAction to Playwright code."""

        if action.action_type == 'navigate':
            url = action.action_params.get('url', '')
            return f'{indent}page.goto("{url}")'

        elif action.action_type == 'clickelement':
            return self._generate_click_code(action, indent)

        elif action.action_type == 'inputtext':
            return self._generate_input_code(action, indent)

        elif action.action_type == 'scroll':
            direction = 'down' if action.action_params.get('down', True) else 'up'
            pages = action.action_params.get('pages', 1)
            pixels = int(pages * 500)
            if direction == 'down':
                return f'{indent}page.mouse.wheel(0, {pixels})'
            else:
                return f'{indent}page.mouse.wheel(0, -{pixels})'

        elif action.action_type == 'sendkeys':
            keys = action.action_params.get('keys', '')
            return f'{indent}page.keyboard.press("{keys}")'

        elif action.action_type == 'wait':
            seconds = action.action_params.get('seconds', 3)
            return f'{indent}page.wait_for_timeout({seconds * 1000})'

        elif action.action_type == 'goback':
            return f'{indent}page.go_back()'

        elif action.action_type == 'search':
            query = action.action_params.get('query', '')
            engine = action.action_params.get('engine', 'google')
            if engine == 'google':
                return f'{indent}page.goto("https://www.google.com/search?q={query}")'
            elif engine == 'duckduckgo':
                return f'{indent}page.goto("https://duckduckgo.com/?q={query}")'
            else:
                return f'{indent}page.goto("https://www.bing.com/search?q={query}")'

        elif action.action_type == 'extract':
            # Convert to assertion/verification comment
            if action.extracted_content:
                content = action.extracted_content[:100].replace('"', '\\"')
                return f'{indent}# Verified content: "{content}..."'
            return None

        elif action.action_type == 'selectdropdownoption':
            return self._generate_select_code(action, indent)

        elif action.action_type == 'done':
            success = action.action_params.get('success', True)
            text = action.action_params.get('text', '')[:80]
            return f'{indent}# Test {"completed successfully" if success else "failed"}: {text}'

        elif action.action_type == 'screenshot':
            return f'{indent}page.screenshot()'

        else:
            # Unknown action type - add as comment
            return f'{indent}# {action.action_type}: {str(action.action_params)[:60]}'

    def _generate_click_code(self, action: ProcessedAction, indent: str) -> str:
        """Generate click code with optional fallback selectors."""
        if not action.selector_info:
            index = action.action_params.get('index', 0)
            return f'{indent}# Click element at index {index} (selector not recorded)'

        if self.config.include_selector_fallbacks:
            selectors = action.selector_info.to_playwright_selectors()
            max_sel = self.config.max_selectors_per_element
            selectors = selectors[:max_sel]

            if len(selectors) > 1:
                selector_list = self._format_selector_list(selectors)
                description = action.selector_info.get_description()
                return f'{indent}self.click_with_fallback(page, {selector_list}, "{description}")'

        selector = action.selector_info.get_best_selector()
        return f'{indent}page.click("{selector}")'

    def _generate_input_code(self, action: ProcessedAction, indent: str) -> str:
        """Generate input/fill code with optional fallback selectors."""
        text = action.action_params.get('text', '')

        if not action.selector_info:
            index = action.action_params.get('index', 0)
            return f'{indent}# Fill input at index {index}: "{text}" (selector not recorded)'

        if self.config.include_selector_fallbacks:
            selectors = action.selector_info.to_playwright_selectors()
            max_sel = self.config.max_selectors_per_element
            selectors = selectors[:max_sel]

            if len(selectors) > 1:
                selector_list = self._format_selector_list(selectors)
                description = action.selector_info.get_description()
                return f'{indent}self.fill_with_fallback(page, {selector_list}, "{text}", "{description}")'

        selector = action.selector_info.get_best_selector()
        return f'{indent}page.fill("{selector}", "{text}")'

    def _generate_select_code(self, action: ProcessedAction, indent: str) -> str:
        """Generate dropdown select code."""
        option_text = action.action_params.get('text', '')

        if not action.selector_info:
            index = action.action_params.get('index', 0)
            return f'{indent}# Select "{option_text}" from dropdown at index {index}'

        selector = action.selector_info.get_best_selector()
        return f'{indent}page.select_option("{selector}", label="{option_text}")'

    def _format_selector_list(self, selectors: list[str]) -> str:
        """Format a list of selectors as Python code."""
        formatted = []
        for sel in selectors:
            # Escape properly based on quotes in selector
            if '"' in sel and "'" not in sel:
                formatted.append(f"'{sel}'")
            elif "'" in sel and '"' not in sel:
                formatted.append(f'"{sel}"')
            else:
                # Escape double quotes
                escaped = sel.replace('"', '\\"')
                formatted.append(f'"{escaped}"')
        return f"[{', '.join(formatted)}]"

    def _format_steps_docstring(self, steps: list[ProcessedStep]) -> str:
        """Format steps for docstring."""
        lines = []
        for i, step in enumerate(steps, 1):
            if step.goal:
                lines.append(f"        {i}. {step.goal}")
            else:
                for action in step.actions:
                    lines.append(f"        {i}. {action.get_description()}")
        return "\n".join(lines) if lines else "        (no steps recorded)"

    def _to_class_name(self, name: str) -> str:
        """Convert scenario name to valid Python class name."""
        # Remove special characters
        clean = re.sub(r'[^a-zA-Z0-9\s]', '', name)
        # Convert to PascalCase
        words = clean.split()
        return ''.join(word.capitalize() for word in words) or 'GeneratedTest'

    def _to_method_name(self, name: str) -> str:
        """Convert scenario name to valid Python method name."""
        # Remove special characters
        clean = re.sub(r'[^a-zA-Z0-9\s]', '', name)
        # Convert to snake_case
        words = clean.lower().split()
        return '_'.join(words) or 'generated_test'

    def generate_conftest(self) -> str:
        """Generate a conftest.py file for the tests."""
        return '''"""
Pytest configuration for generated Playwright tests.
"""

import pytest
from playwright.sync_api import sync_playwright, Browser, Page


@pytest.fixture(scope="session")
def browser():
    """Create a browser instance for the test session."""
    with sync_playwright() as p:
        # Use chromium by default, can be changed to firefox or webkit
        browser = p.chromium.launch(
            headless=True,  # Set to False for debugging
            slow_mo=100,    # Slow down for visibility (remove for speed)
        )
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def context(browser: Browser):
    """Create a new browser context for each test."""
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        ignore_https_errors=True,
    )
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context):
    """Create a new page for each test."""
    page = context.new_page()
    yield page
    page.close()


# Optional: Add command line option for headed mode
def pytest_addoption(parser):
    parser.addoption(
        "--headed",
        action="store_true",
        default=False,
        help="Run tests in headed mode (visible browser)"
    )


@pytest.fixture(scope="session")
def headed(request):
    return request.config.getoption("--headed")
'''
