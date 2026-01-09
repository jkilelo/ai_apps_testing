"""
Test scenario model - represents a logical test case grouped from steps.
"""

from typing import Optional
from pydantic import BaseModel, Field

from .processed_step import ProcessedStep


class TestScenario(BaseModel):
    """
    A logical test scenario grouped from execution steps.

    Scenarios are detected by analyzing agent's goals and thinking:
    - Happy path scenarios
    - Validation/error scenarios
    - Edge case scenarios
    """

    scenario_id: str = Field(
        description="Unique identifier for this scenario"
    )
    name: str = Field(
        description="Human-readable scenario name"
    )
    description: str = Field(
        default="",
        description="Detailed description of what this scenario tests"
    )
    scenario_type: str = Field(
        default="general",
        description="Type: happy_path, validation, error_handling, edge_case"
    )

    # Steps that make up this scenario
    steps: list[ProcessedStep] = Field(
        default_factory=list,
        description="Ordered steps in this scenario"
    )

    # Result
    passed: bool = Field(
        default=False,
        description="Whether the scenario passed"
    )
    failure_reason: Optional[str] = Field(
        default=None,
        description="Reason for failure if failed"
    )
    failure_step: Optional[int] = Field(
        default=None,
        description="Step number where failure occurred"
    )

    # Evidence
    screenshots: list[str] = Field(
        default_factory=list,
        description="Paths to screenshots for this scenario"
    )
    start_url: Optional[str] = Field(
        default=None,
        description="URL at scenario start"
    )
    end_url: Optional[str] = Field(
        default=None,
        description="URL at scenario end"
    )

    # Timing
    duration_ms: Optional[int] = Field(
        default=None,
        description="Total duration of scenario in milliseconds"
    )

    @property
    def step_count(self) -> int:
        """Number of steps in this scenario."""
        return len(self.steps)

    @property
    def action_count(self) -> int:
        """Total number of actions across all steps."""
        return sum(len(step.actions) for step in self.steps)

    def collect_screenshots(self) -> list[str]:
        """Collect all screenshots from steps."""
        screenshots = []
        for step in self.steps:
            if step.screenshot_path:
                screenshots.append(step.screenshot_path)
        return screenshots

    def to_gherkin(self) -> str:
        """Convert scenario to Gherkin format."""
        lines = [
            f"Scenario: {self.name}",
        ]

        if self.description:
            lines.append(f"  # {self.description}")

        for i, step in enumerate(self.steps):
            prefix = "Given" if i == 0 else "And" if i < len(self.steps) - 1 else "Then"

            if step.goal:
                lines.append(f"  {prefix} {step.goal}")
            else:
                for action in step.actions:
                    lines.append(f"  {prefix} {action.get_description()}")

        return '\n'.join(lines)

    def to_test_case_dict(self) -> dict:
        """Convert to test case dictionary format."""
        return {
            "test_id": self.scenario_id,
            "test_name": self.name,
            "description": self.description,
            "type": self.scenario_type,
            "status": "passed" if self.passed else "failed",
            "failure_reason": self.failure_reason,
            "steps": [
                {
                    "step_number": step.step_number,
                    "goal": step.goal,
                    "actions": [
                        {
                            "type": action.action_type,
                            "description": action.get_description(),
                            "success": action.success,
                            "error": action.error,
                        }
                        for action in step.actions
                    ],
                    "page_url": step.page_url,
                }
                for step in self.steps
            ],
            "duration_ms": self.duration_ms,
            "screenshots": self.screenshots,
        }
