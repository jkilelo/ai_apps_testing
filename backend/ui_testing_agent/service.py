"""
UI Testing Service - Main entry point for exploratory UI testing.
"""

import os
import shutil
from typing import Optional, Any

from .models.output_config import OutputConfig
from .models.test_session import TestSession
from .core.explorer_agent import ExplorerAgent, DEFAULT_MODEL
from .generators.playwright_generator import PlaywrightGenerator
from .generators.verified_playwright_generator import VerifiedPlaywrightGenerator
from .generators.test_case_generator import TestCaseGenerator
from .generators.report_generator import ReportGenerator


class UITestingService:
    """
    Main entry point for exploratory UI testing.

    This service orchestrates:
    1. ExplorerAgent - Performs exploratory testing
    2. PlaywrightGenerator - Generates offline-runnable test code
    3. TestCaseGenerator - Generates formal test documentation
    4. ReportGenerator - Generates HTML/JSON reports

    Usage:
        service = UITestingService(output_config=OutputConfig())

        result = await service.explore_and_test(
            task="Test the 'Send a gift' functionality",
            url="https://example.com"
        )

        print(f"Results: {result.passed}/{result.total_scenarios} passed")
        print(f"Playwright tests: {result.playwright_code_path}")
        print(f"HTML report: {result.html_report_path}")
    """

    def __init__(
        self,
        output_config: Optional[OutputConfig] = None,
        model: str = DEFAULT_MODEL,
        headless: bool = False,
    ):
        """
        Initialize the UI Testing Service.

        Args:
            output_config: Configuration for output generation
            model: LLM model to use (default: gemini-2.0-flash)
            headless: Run browser without visible window
        """
        self.output_config = output_config or OutputConfig()
        self.model = model
        self.headless = headless

        # Initialize generators
        self.playwright_generator = PlaywrightGenerator(self.output_config)
        self.verified_playwright_generator = VerifiedPlaywrightGenerator(self.output_config)
        self.test_case_generator = TestCaseGenerator(self.output_config)
        self.report_generator = ReportGenerator(self.output_config)

    async def explore_and_test(
        self,
        task: str,
        url: str,
        max_steps: int = 50,
        max_actions_per_step: int = 3,
        step_callback: Optional[Any] = None,
        done_callback: Optional[Any] = None,
    ) -> TestSession:
        """
        Execute exploratory testing and generate all artifacts.

        This is the main method that:
        1. Creates an ExplorerAgent with QA-focused prompt
        2. Runs exploration and testing on the target URL
        3. Processes the results into a TestSession
        4. Generates all configured artifacts (code, reports, etc.)
        5. Returns the session with paths to all generated files

        Args:
            task: High-level testing task description
            url: Target URL to test
            max_steps: Maximum agent steps
            max_actions_per_step: Maximum actions per LLM turn
            step_callback: Optional callback for streaming events
            done_callback: Optional callback for streaming completion

        Returns:
            TestSession with all processed data and artifact paths
        """
        # Create explorer agent
        agent = ExplorerAgent(
            model=self.model,
            headless=self.headless,
            output_config=self.output_config,
            step_callback=step_callback,
            done_callback=done_callback,
        )

        try:
            # Execute exploration and testing
            session = await agent.explore_and_test(
                task=task,
                url=url,
                max_steps=max_steps,
                max_actions_per_step=max_actions_per_step,
            )

            # Generate all artifacts
            await self._generate_artifacts(session)

            return session

        finally:
            await agent.close()

    async def _generate_artifacts(self, session: TestSession):
        """Generate all configured output artifacts."""
        # Create output directory
        output_dir = self._ensure_output_directory(session.session_id)
        session.output_directory = output_dir

        # Generate Playwright code
        if self.output_config.generate_playwright_code:
            try:
                playwright_path = self._generate_playwright(session, output_dir)
                session.playwright_code_path = playwright_path
                session.output_filename = os.path.basename(playwright_path)
                print(f"[UITestingService] Generated Playwright code: {playwright_path}")
            except Exception as e:
                print(f"[UITestingService] ERROR generating Playwright code: {e}")
                import traceback
                traceback.print_exc()

        # Generate test cases
        if self.output_config.generate_test_cases:
            test_cases_path = self._generate_test_cases(session, output_dir)
            session.test_cases_path = test_cases_path

        # Generate HTML report
        if self.output_config.generate_html_report:
            html_path = self._generate_html_report(session, output_dir)
            session.html_report_path = html_path

        # Generate JSON report
        if self.output_config.generate_json_report:
            json_path = self._generate_json_report(session, output_dir)
            session.json_report_path = json_path

        # Save raw history
        if self.output_config.save_raw_history and session.raw_history:
            history_path = self._save_raw_history(session, output_dir)

        # Copy screenshots
        if self.output_config.save_screenshots:
            screenshots_dir = self._copy_screenshots(session, output_dir)
            session.screenshots_dir = screenshots_dir

        # Generate conftest.py if Playwright code was generated
        if self.output_config.generate_playwright_code:
            self._generate_conftest(output_dir)

    def _ensure_output_directory(self, session_id: str) -> str:
        """Create output directory structure."""
        base_dir = self.output_config.output_directory

        if self.output_config.create_session_subdir:
            output_dir = os.path.join(base_dir, session_id)
        else:
            output_dir = base_dir

        # Create subdirectories
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "tests"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "reports"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "screenshots"), exist_ok=True)

        return output_dir

    def _generate_playwright(self, session: TestSession, output_dir: str) -> str:
        """Generate Playwright test code using the verified generator."""

        # Use verified generator when we have raw history (preferred)
        if session.raw_history:
            # Pass raw dict directly - the extractor handles both object and dict formats
            code = self.verified_playwright_generator.generate_from_history(
                history=session.raw_history,  # Pass raw dict, not validated model
                task=session.task,
                url=session.url,
                session_id=session.session_id,
            )
        else:
            # Fallback to basic generator
            code = self.playwright_generator.generate(session)

        # Create filename from task
        safe_task = "".join(c if c.isalnum() else "_" for c in session.task[:30])
        filename = f"test_{safe_task}_{session.session_id[-8:]}.py"

        filepath = os.path.join(output_dir, "tests", filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)

        return filepath

    def _generate_conftest(self, output_dir: str):
        """Generate conftest.py for pytest fixtures."""
        conftest_code = self.playwright_generator.generate_conftest()
        filepath = os.path.join(output_dir, "tests", "conftest.py")

        # Only create if doesn't exist
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(conftest_code)

    def _generate_test_cases(self, session: TestSession, output_dir: str) -> str:
        """Generate test case documentation."""
        content = self.test_case_generator.generate(session)

        ext = self.output_config.test_case_format
        if ext == "gherkin":
            ext = "feature"

        filepath = os.path.join(output_dir, f"test_cases.{ext}")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath

    def _generate_html_report(self, session: TestSession, output_dir: str) -> str:
        """Generate HTML report."""
        html = self.report_generator.generate_html(session)

        filepath = os.path.join(output_dir, "reports", "report.html")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

        return filepath

    def _generate_json_report(self, session: TestSession, output_dir: str) -> str:
        """Generate JSON report."""
        json_content = self.report_generator.generate_json(session)

        filepath = os.path.join(output_dir, "reports", "report.json")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(json_content)

        return filepath

    def _save_raw_history(self, session: TestSession, output_dir: str) -> str:
        """Save raw AgentHistoryList as JSON."""
        import json

        filepath = os.path.join(output_dir, "raw_history.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(session.raw_history, f, indent=2, default=str)

        return filepath

    def _copy_screenshots(self, session: TestSession, output_dir: str) -> str:
        """Copy screenshots to output directory."""
        screenshots_dir = os.path.join(output_dir, "screenshots")

        for step in session.steps:
            if step.screenshot_path and os.path.exists(step.screenshot_path):
                filename = f"step_{step.step_number:03d}.png"
                dest = os.path.join(screenshots_dir, filename)
                try:
                    shutil.copy2(step.screenshot_path, dest)
                except Exception:
                    pass  # Ignore copy errors

        return screenshots_dir


# Convenience function for quick usage
async def run_ui_test(
    task: str,
    url: str,
    output_dir: str = "./test_outputs",
    model: str = DEFAULT_MODEL,
    headless: bool = False,
    max_steps: int = 50,
) -> TestSession:
    """
    Quick helper function to run UI testing.

    Args:
        task: Testing task description
        url: Target URL
        output_dir: Output directory for artifacts
        model: LLM model to use
        headless: Run browser headlessly
        max_steps: Maximum agent steps

    Returns:
        TestSession with all results
    """
    config = OutputConfig(output_directory=output_dir)
    service = UITestingService(
        output_config=config,
        model=model,
        headless=headless,
    )

    return await service.explore_and_test(
        task=task,
        url=url,
        max_steps=max_steps,
    )
