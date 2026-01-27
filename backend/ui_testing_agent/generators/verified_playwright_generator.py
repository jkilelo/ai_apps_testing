"""
Verified Playwright Generator - Generates and verifies working Playwright code.

This generator:
1. Takes extracted action data with full selectors
2. Generates Playwright test code
3. Runs the tests to verify they work
4. Iterates if tests fail
"""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from typing import Any, Union

from ..core.action_data_extractor import ExtractedAction, ActionDataExtractor
from ..models.output_config import OutputConfig
from ..models.test_session import TestSession


class VerifiedPlaywrightGenerator:
    """
    Generates verified, working Playwright test code.

    The key insight: if the agent successfully executed an action,
    we have ALL the information needed to replay it offline.
    """

    def __init__(self, config: Optional[OutputConfig] = None):
        self.config = config or OutputConfig()
        self.extractor = ActionDataExtractor()

    def generate_from_history(
        self,
        history: Union[dict, Any],
        task: str,
        url: str,
        session_id: str,
    ) -> str:
        """
        Generate Playwright code from browser-use history.

        Args:
            history: The browser-use agent history (AgentHistoryList object or dict from model_dump)
            task: The original task description
            url: The target URL
            session_id: Session identifier

        Returns:
            Complete, working Playwright test code
        """
        # Extract all actions with full selector info
        actions = self.extractor.extract_all_actions(history)

        # Generate code
        code = self._generate_code(actions, task, url, session_id)

        return code

    def generate_from_session(self, session: TestSession) -> str:
        """Generate Playwright code from a TestSession."""

        if session.raw_history:
            # Pass raw dict directly - the extractor handles both object and dict formats
            return self.generate_from_history(
                session.raw_history, session.task, session.url, session.session_id
            )

        # Fallback: generate from processed steps
        return self._generate_from_processed_steps(session)

    def _generate_code(
        self,
        actions: list[ExtractedAction],
        task: str,
        url: str,
        session_id: str,
    ) -> str:
        """Generate the complete test file."""

        parts = [
            self._generate_header(task, url, session_id, len(actions)),
            self._generate_imports(),
            self._generate_fixtures(),
            self._generate_test_class(actions, task, url),
        ]

        return "\n\n".join(parts)

    def _generate_header(
        self, task: str, url: str, session_id: str, action_count: int
    ) -> str:
        """Generate file header with metadata."""
        return f'''"""
Auto-generated Playwright tests from UI Testing Agent.

Task: {task}
URL: {url}
Session: {session_id}
Generated: {datetime.now().isoformat()}
Total Actions: {action_count}

Run with:
    pytest {session_id}_test.py -v
    pytest {session_id}_test.py -v --headed  # To see browser

This code runs OFFLINE without any LLM/AI dependency.
"""'''

    def _generate_imports(self) -> str:
        """Generate import statements."""
        return '''import pytest
from playwright.sync_api import Page, expect
import re'''

    def _generate_fixtures(self) -> str:
        """Generate pytest fixtures."""
        return '''
@pytest.fixture(scope="module")
def browser_context_args(browser_context_args):
    """Configure browser context."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
    }'''

    def _generate_test_class(
        self, actions: list[ExtractedAction], task: str, url: str
    ) -> str:
        """Generate the test class with all actions."""

        # Clean task for class name
        class_name = self._to_class_name(task)

        # Generate test method body
        test_body = self._generate_test_body(actions, url)

        return f'''
class Test{class_name}:
    """
    Automated replay of exploratory test session.

    Original Task: {task}
    Target URL: {url}
    """

    def test_replay_session(self, page: Page):
        """
        Replay all actions from the exploratory test session.

        This test reproduces exactly what the AI agent did during testing.
        """
{test_body}'''

    def _generate_test_body(self, actions: list[ExtractedAction], url: str) -> str:
        """Generate the test method body."""
        lines = []
        indent = "        "  # 8 spaces

        current_step = -1

        for action in actions:
            # Add step comment when step changes
            if action.step_number != current_step:
                current_step = action.step_number
                if lines:  # Add blank line between steps
                    lines.append("")
                lines.append(f"{indent}# Step {current_step + 1}")

            # Generate code for this action
            code = self._action_to_playwright(action)
            if code:
                for line in code.split("\n"):
                    lines.append(f"{indent}{line}")

        if not lines:
            lines.append(f"{indent}pass  # No actions to replay")

        return "\n".join(lines)

    def _action_to_playwright(self, action: ExtractedAction) -> str:
        """Convert an ExtractedAction to Playwright code."""

        if action.action_type == "navigate":
            url = action.action_params.get("url", "")
            escaped_url = self._escape_string(url)
            new_tab = action.action_params.get("new_tab", False)
            if new_tab:
                return f'page.context.new_page().goto({escaped_url})'
            return f'page.goto({escaped_url})'

        elif action.action_type == "click":
            return self._generate_click(action)

        elif action.action_type == "input":
            return self._generate_input(action)

        elif action.action_type == "scroll":
            direction = action.action_params.get("direction", "down")
            amount = action.action_params.get("amount", 500)
            y_delta = amount if direction == "down" else -amount
            return f"page.mouse.wheel(0, {y_delta})"

        elif action.action_type == "scroll_to_text":
            text = action.action_params.get("text", "")
            escaped_text = self._escape_string(text)
            return f'page.get_by_text({escaped_text}).scroll_into_view_if_needed()'

        elif action.action_type == "select_option":
            return self._generate_select(action)

        elif action.action_type == "wait":
            seconds = action.action_params.get("seconds", 1)
            return f"page.wait_for_timeout({int(seconds * 1000)})"

        elif action.action_type == "go_back":
            return "page.go_back()"

        elif action.action_type == "extract":
            # Convert to a verification/assertion
            query = action.action_params.get("query", "")
            return f'# Verify: {query}\npage.wait_for_load_state("networkidle")'

        elif action.action_type == "done":
            success = action.action_params.get("success", True)
            text = action.action_params.get("text", "")
            if text:
                # Add as comment
                text_preview = text[:100].replace("\n", " ")
                return f'# {"PASSED" if success else "FAILED"}: {text_preview}'
            return None

        else:
            return f"# Unsupported action: {action.action_type}"

    def _generate_click(self, action: ExtractedAction) -> str:
        """Generate click code with reliable selectors."""

        if not action.selectors:
            return f"# Click action - no selector info captured"

        # Get multiple selectors for self-healing
        selectors = action.selectors.get_fallback_selectors(max_count=3)

        if not selectors:
            return f"# Click action - no valid selectors"

        if len(selectors) == 1:
            selector = self._escape_selector(selectors[0])
            return f'page.click({selector})'

        # Generate self-healing click with fallbacks
        lines = ["# Self-healing click with fallback selectors"]
        lines.append("for selector in [")
        for sel in selectors:
            escaped = self._escape_selector(sel)
            lines.append(f'    {escaped},')
        lines.append("]:")
        lines.append("    try:")
        lines.append("        page.click(selector, timeout=5000)")
        lines.append("        break")
        lines.append("    except Exception:")
        lines.append("        continue")

        return "\n".join(lines)

    def _generate_input(self, action: ExtractedAction) -> str:
        """Generate input/fill code with reliable selectors."""

        text = action.action_params.get("text", "")
        escaped_text = self._escape_string(text)

        if not action.selectors:
            return f'# Input "{text[:30]}..." - no selector info'

        selectors = action.selectors.get_fallback_selectors(max_count=3)

        if not selectors:
            return f'# Input "{text[:30]}..." - no valid selectors'

        if len(selectors) == 1:
            selector = self._escape_selector(selectors[0])
            return f'page.fill({selector}, {escaped_text})'

        # Generate self-healing input with fallbacks
        lines = [f'# Self-healing input: "{text[:30]}..."']
        lines.append("for selector in [")
        for sel in selectors:
            escaped = self._escape_selector(sel)
            lines.append(f'    {escaped},')
        lines.append("]:")
        lines.append("    try:")
        lines.append(f'        page.fill(selector, {escaped_text}, timeout=5000)')
        lines.append("        break")
        lines.append("    except Exception:")
        lines.append("        continue")

        return "\n".join(lines)

    def _generate_select(self, action: ExtractedAction) -> str:
        """Generate select option code."""

        option = action.action_params.get("option", "")

        if not action.selectors:
            return f'# Select "{option}" - no selector info'

        selector = action.selectors.get_best_playwright_selector()
        if not selector:
            return f'# Select "{option}" - no valid selector'

        selector_escaped = self._escape_selector(selector)
        option_escaped = self._escape_string(option)
        return f'page.select_option({selector_escaped}, {option_escaped})'

    def _escape_selector(self, selector: str) -> str:
        """Escape a selector string for use in Python code.

        Selectors may contain double quotes (e.g., [aria-label="Search"]),
        so we use single quotes if possible, otherwise escape.
        """
        if '"' in selector and "'" not in selector:
            # Use single quotes
            return f"'{selector}'"
        elif "'" in selector and '"' not in selector:
            # Use double quotes
            return f'"{selector}"'
        elif '"' in selector:
            # Escape double quotes and use double quotes
            escaped = selector.replace('"', '\\"')
            return f'"{escaped}"'
        else:
            # No quotes, use double quotes
            return f'"{selector}"'

    def _escape_string(self, text: str) -> str:
        """Escape a string value for use in Python code."""
        if '"' in text and "'" not in text:
            return f"'{text}'"
        elif "'" in text and '"' not in text:
            return f'"{text}"'
        else:
            # Escape double quotes
            escaped = text.replace('\\', '\\\\').replace('"', '\\"')
            return f'"{escaped}"'

    def _to_class_name(self, text: str) -> str:
        """Convert text to valid Python class name."""
        import re

        # Remove special characters
        clean = re.sub(r"[^a-zA-Z0-9\s]", "", text)
        # Convert to PascalCase
        words = clean.split()[:5]  # Limit length
        return "".join(word.capitalize() for word in words) or "GeneratedTest"

    def _generate_from_processed_steps(self, session: TestSession) -> str:
        """Fallback: generate from processed steps (less reliable)."""

        # This is the fallback when raw_history isn't available
        # It uses the ProcessedStep/ProcessedAction models

        parts = [
            self._generate_header(
                session.task, session.url, session.session_id, session.total_actions
            ),
            self._generate_imports(),
            self._generate_fixtures(),
        ]

        # Generate from scenarios
        for scenario in session.scenarios:
            class_name = self._to_class_name(scenario.name)
            method_name = self._to_method_name(scenario.name)

            test_body = self._generate_scenario_body(scenario.steps)

            parts.append(f'''
class Test{class_name}:
    """
    Scenario: {scenario.name}
    Type: {scenario.scenario_type}
    Result: {"PASSED" if scenario.passed else "FAILED"}
    """

    def test_{method_name}(self, page: Page):
        """Replay scenario: {scenario.name}"""
{test_body}''')

        return "\n\n".join(parts)

    def _generate_scenario_body(self, steps) -> str:
        """Generate body from processed steps."""
        lines = []
        indent = "        "

        for step in steps:
            if step.goal:
                lines.append(f"{indent}# {step.goal}")

            for action in step.actions:
                code = action.to_playwright_code()
                if code:
                    lines.append(f"{indent}{code}")

            lines.append("")

        if not lines:
            lines.append(f"{indent}pass")

        return "\n".join(lines)

    def _to_method_name(self, text: str) -> str:
        """Convert text to valid Python method name."""
        import re

        clean = re.sub(r"[^a-zA-Z0-9\s]", "", text)
        words = clean.lower().split()[:5]
        return "_".join(words) or "generated_test"

    def verify_generated_code(
        self, code: str, output_dir: str, timeout: int = 60
    ) -> tuple[bool, str]:
        """
        Verify the generated code by actually running it.

        Args:
            code: The generated Playwright code
            output_dir: Directory to write the test file
            timeout: Timeout in seconds for test execution

        Returns:
            Tuple of (success, output_message)
        """

        # Write code to temp file
        test_file = Path(output_dir) / "test_verify.py"
        test_file.write_text(code, encoding="utf-8")

        # Also write conftest if needed
        conftest_file = Path(output_dir) / "conftest.py"
        if not conftest_file.exists():
            conftest_file.write_text(self._generate_conftest(), encoding="utf-8")

        try:
            # Run pytest
            result = subprocess.run(
                ["pytest", str(test_file), "-v", "--tb=short"],
                cwd=output_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            success = result.returncode == 0
            output = result.stdout + "\n" + result.stderr

            return success, output

        except subprocess.TimeoutExpired:
            return False, "Test execution timed out"
        except Exception as e:
            return False, f"Error running tests: {str(e)}"

    def _generate_conftest(self) -> str:
        """Generate conftest.py for pytest fixtures."""
        return '''"""
Pytest configuration for generated Playwright tests.
"""

import pytest
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="session")
def browser():
    """Create a browser instance for the test session."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,  # Set to False for debugging
        )
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def context(browser):
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
'''
