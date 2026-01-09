"""
Processed step model - represents a single step from AgentHistory.
"""

from typing import Optional
from pydantic import BaseModel, Field

from .processed_action import ProcessedAction


class ProcessedStep(BaseModel):
    """
    Processed step with all relevant data from browser-use AgentHistory.

    Each step represents one LLM turn, which may contain multiple actions.
    """

    step_number: int = Field(
        description="Step index in the execution sequence (0-based)"
    )

    # LLM reasoning (from AgentOutput)
    thinking: Optional[str] = Field(
        default=None,
        description="Agent's internal reasoning (if use_thinking=True)"
    )
    goal: Optional[str] = Field(
        default=None,
        description="Agent's stated goal for this step (next_goal)"
    )
    evaluation: Optional[str] = Field(
        default=None,
        description="Agent's evaluation of the previous step"
    )
    memory: Optional[str] = Field(
        default=None,
        description="Agent's context/memory"
    )

    # Actions executed in this step
    actions: list[ProcessedAction] = Field(
        default_factory=list,
        description="Actions executed in this step (may be multiple)"
    )

    # Page state (from BrowserStateHistory)
    page_url: str = Field(
        description="Current page URL after actions"
    )
    page_title: str = Field(
        description="Current page title"
    )
    screenshot_path: Optional[str] = Field(
        default=None,
        description="Path to screenshot PNG file"
    )

    # Timing (from StepMetadata)
    timestamp: Optional[float] = Field(
        default=None,
        description="Unix timestamp when step started"
    )
    duration_ms: Optional[int] = Field(
        default=None,
        description="Step execution duration in milliseconds"
    )

    # Scenario detection helpers
    is_scenario_start: bool = Field(
        default=False,
        description="Whether this step starts a new test scenario"
    )
    scenario_name: Optional[str] = Field(
        default=None,
        description="Detected scenario name if this is a scenario boundary"
    )

    @property
    def has_failure(self) -> bool:
        """Check if any action in this step failed."""
        return any(
            action.success is False or action.error is not None
            for action in self.actions
        )

    @property
    def has_extraction(self) -> bool:
        """Check if any action extracted content."""
        return any(
            action.extracted_content is not None
            for action in self.actions
        )

    @property
    def is_done_step(self) -> bool:
        """Check if this step contains a done action."""
        return any(action.action_type == 'done' for action in self.actions)

    def get_extracted_content(self) -> Optional[str]:
        """Get combined extracted content from all actions."""
        extracts = [
            action.extracted_content
            for action in self.actions
            if action.extracted_content
        ]
        return '\n'.join(extracts) if extracts else None

    def get_errors(self) -> list[str]:
        """Get all errors from this step."""
        return [
            action.error
            for action in self.actions
            if action.error
        ]

    def to_playwright_code_lines(self) -> list[str]:
        """Convert all actions in this step to Playwright code lines."""
        lines = []

        # Add goal as comment
        if self.goal:
            lines.append(f"# {self.goal}")

        for action in self.actions:
            code = action.to_playwright_code()
            if code:
                lines.append(code)

        return lines
