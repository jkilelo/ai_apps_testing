"""
Test Case Generator - Generates formal test case documentation from recorded sessions.
"""

import json
import yaml
from datetime import datetime
from typing import Literal

from ..models.test_session import TestSession
from ..models.test_scenario import TestScenario
from ..models.output_config import OutputConfig


class TestCaseGenerator:
    """
    Generates formal test case documentation from recorded test sessions.

    Supports multiple output formats:
    - JSON: Machine-readable format
    - YAML: Human-readable structured format
    - Markdown: Documentation-friendly format
    - Gherkin: BDD-style format
    """

    def __init__(self, config: OutputConfig = None):
        """
        Initialize the test case generator.

        Args:
            config: Output configuration options
        """
        self.config = config or OutputConfig()

    def generate(
        self,
        session: TestSession,
        format: Literal["json", "yaml", "markdown", "gherkin"] = None
    ) -> str:
        """
        Generate test case documentation in the specified format.

        Args:
            session: TestSession with recorded scenarios
            format: Output format (uses config if not specified)

        Returns:
            Test case documentation as string
        """
        format = format or self.config.test_case_format

        if format == "json":
            return self._generate_json(session)
        elif format == "yaml":
            return self._generate_yaml(session)
        elif format == "markdown":
            return self._generate_markdown(session)
        elif format == "gherkin":
            return self._generate_gherkin(session)
        else:
            return self._generate_json(session)

    def _generate_json(self, session: TestSession) -> str:
        """Generate JSON format test cases."""
        data = {
            "metadata": {
                "session_id": session.session_id,
                "task": session.task,
                "url": session.url,
                "generated_at": datetime.now().isoformat(),
                "executed_at": session.started_at.isoformat(),
                "duration_seconds": session.duration_seconds,
            },
            "summary": {
                "total_scenarios": session.total_scenarios,
                "passed": session.passed,
                "failed": session.failed,
                "pass_rate": session.pass_rate,
            },
            "test_cases": [
                self._scenario_to_test_case(scenario)
                for scenario in session.scenarios
            ]
        }
        return json.dumps(data, indent=2, default=str)

    def _generate_yaml(self, session: TestSession) -> str:
        """Generate YAML format test cases."""
        data = {
            "metadata": {
                "session_id": session.session_id,
                "task": session.task,
                "url": session.url,
                "generated_at": datetime.now().isoformat(),
            },
            "summary": {
                "total_scenarios": session.total_scenarios,
                "passed": session.passed,
                "failed": session.failed,
            },
            "test_cases": [
                self._scenario_to_test_case(scenario)
                for scenario in session.scenarios
            ]
        }
        return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)

    def _generate_markdown(self, session: TestSession) -> str:
        """Generate Markdown format test cases."""
        lines = [
            f"# Test Cases: {session.task}",
            "",
            "## Metadata",
            "",
            f"- **Session ID**: {session.session_id}",
            f"- **Target URL**: {session.url}",
            f"- **Executed**: {session.started_at.isoformat()}",
            f"- **Duration**: {session.duration_seconds:.1f} seconds",
            "",
            "## Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Scenarios | {session.total_scenarios} |",
            f"| Passed | {session.passed} |",
            f"| Failed | {session.failed} |",
            f"| Pass Rate | {session.pass_rate:.1f}% |",
            "",
            "## Test Cases",
            "",
        ]

        for scenario in session.scenarios:
            lines.extend(self._scenario_to_markdown(scenario))
            lines.append("")

        return "\n".join(lines)

    def _generate_gherkin(self, session: TestSession) -> str:
        """Generate Gherkin/BDD format test cases."""
        lines = [
            f"Feature: {session.task}",
            f"  As a user",
            f"  I want to test {session.task}",
            f"  So that I can verify the functionality works correctly",
            "",
            f"  Background:",
            f"    Given I am on {session.url}",
            "",
        ]

        for scenario in session.scenarios:
            lines.extend(self._scenario_to_gherkin(scenario))
            lines.append("")

        return "\n".join(lines)

    def _scenario_to_test_case(self, scenario: TestScenario) -> dict:
        """Convert a scenario to test case dictionary."""
        return {
            "test_id": scenario.scenario_id,
            "name": scenario.name,
            "description": scenario.description,
            "type": scenario.scenario_type,
            "status": "passed" if scenario.passed else "failed",
            "failure_reason": scenario.failure_reason,
            "preconditions": [
                f"User is on {scenario.start_url}" if scenario.start_url else "User has browser open"
            ],
            "steps": [
                {
                    "step_number": i + 1,
                    "action": step.goal or self._summarize_actions(step),
                    "expected_result": self._infer_expected_result(step),
                    "actual_result": self._get_actual_result(step),
                    "status": "passed" if not step.has_failure else "failed",
                }
                for i, step in enumerate(scenario.steps)
            ],
            "postconditions": [
                f"User is on {scenario.end_url}" if scenario.end_url else "Test completed"
            ],
            "duration_ms": scenario.duration_ms,
            "screenshots": scenario.screenshots,
        }

    def _scenario_to_markdown(self, scenario: TestScenario) -> list[str]:
        """Convert a scenario to Markdown format."""
        status_emoji = "✅" if scenario.passed else "❌"
        lines = [
            f"### {status_emoji} {scenario.scenario_id}: {scenario.name}",
            "",
            f"**Type**: {scenario.scenario_type}",
            f"**Status**: {'PASSED' if scenario.passed else 'FAILED'}",
        ]

        if scenario.failure_reason:
            lines.append(f"**Failure Reason**: {scenario.failure_reason}")

        lines.extend([
            "",
            "#### Steps",
            "",
            "| # | Action | Expected | Actual | Status |",
            "|---|--------|----------|--------|--------|",
        ])

        for i, step in enumerate(scenario.steps, 1):
            action = (step.goal or self._summarize_actions(step))[:40]
            expected = self._infer_expected_result(step)[:30]
            actual = self._get_actual_result(step)[:30]
            status = "✅" if not step.has_failure else "❌"
            lines.append(f"| {i} | {action} | {expected} | {actual} | {status} |")

        return lines

    def _scenario_to_gherkin(self, scenario: TestScenario) -> list[str]:
        """Convert a scenario to Gherkin format."""
        lines = [
            f"  Scenario: {scenario.name}",
        ]

        if scenario.description:
            lines.append(f"    # {scenario.description}")

        for i, step in enumerate(scenario.steps):
            keyword = "Given" if i == 0 else "When" if i < len(scenario.steps) - 1 else "Then"

            if step.goal:
                lines.append(f"    {keyword} {step.goal}")
            else:
                for action in step.actions:
                    lines.append(f"    {keyword} {action.get_description()}")
                    keyword = "And"

        return lines

    def _summarize_actions(self, step) -> str:
        """Summarize actions in a step."""
        if not step.actions:
            return "No actions"
        descriptions = [action.get_description() for action in step.actions]
        return "; ".join(descriptions[:3])

    def _infer_expected_result(self, step) -> str:
        """Infer expected result from step data."""
        if step.is_done_step:
            return "Test completes"

        for action in step.actions:
            if action.action_type == 'navigate':
                return "Page loads"
            elif action.action_type == 'clickelement':
                return "Element responds"
            elif action.action_type == 'inputtext':
                return "Text entered"
            elif action.action_type == 'extract':
                return "Content verified"

        return "Action succeeds"

    def _get_actual_result(self, step) -> str:
        """Get actual result from step data."""
        if step.has_failure:
            errors = step.get_errors()
            return errors[0][:50] if errors else "Failed"

        extracted = step.get_extracted_content()
        if extracted:
            return extracted[:50]

        return "Success"
