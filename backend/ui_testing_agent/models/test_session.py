"""
Test session model - represents a complete exploratory testing session.
"""

from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

from .processed_step import ProcessedStep
from .test_scenario import TestScenario


class TestSession(BaseModel):
    """
    Complete test session with all data from exploratory testing.

    This is the main result object returned by UITestingService.
    """

    # === Session Identification ===
    session_id: str = Field(
        description="Unique session identifier"
    )
    task: str = Field(
        description="Original task/requirement given by user"
    )
    url: str = Field(
        description="Target URL that was tested"
    )

    # === Timing ===
    started_at: datetime = Field(
        description="When the testing session started"
    )
    completed_at: datetime = Field(
        description="When the testing session completed"
    )

    @property
    def duration_seconds(self) -> float:
        """Total session duration in seconds."""
        return (self.completed_at - self.started_at).total_seconds()

    # === Raw Data (from browser-use) ===
    raw_history: Optional[dict[str, Any]] = Field(
        default=None,
        description="Raw AgentHistoryList.model_dump() for debugging/replay"
    )

    # === Replay Recording (for LLM-free replay) ===
    replay_recording: Optional[Any] = Field(
        default=None,
        description="RecordedSession for offline replay without LLM. "
                    "Contains CSS selectors, XPath, stable hash for element matching."
    )
    replay_recording_path: Optional[str] = Field(
        default=None,
        description="Path to saved replay recording JSON file"
    )

    # === Processed Data ===
    steps: list[ProcessedStep] = Field(
        default_factory=list,
        description="All processed steps from execution"
    )
    scenarios: list[TestScenario] = Field(
        default_factory=list,
        description="Steps grouped into logical test scenarios"
    )

    # === Summary Statistics ===
    total_steps: int = Field(
        default=0,
        description="Total number of steps executed"
    )
    total_actions: int = Field(
        default=0,
        description="Total number of actions across all steps"
    )
    total_scenarios: int = Field(
        default=0,
        description="Number of test scenarios identified"
    )
    passed: int = Field(
        default=0,
        description="Number of scenarios that passed"
    )
    failed: int = Field(
        default=0,
        description="Number of scenarios that failed"
    )

    @property
    def pass_rate(self) -> float:
        """Calculate pass rate as percentage."""
        if self.total_scenarios == 0:
            return 0.0
        return (self.passed / self.total_scenarios) * 100

    # === Generated Artifact Paths ===
    playwright_code_path: Optional[str] = Field(
        default=None,
        description="Path to generated Playwright test file"
    )
    test_cases_path: Optional[str] = Field(
        default=None,
        description="Path to generated test cases file"
    )
    html_report_path: Optional[str] = Field(
        default=None,
        description="Path to generated HTML report"
    )
    json_report_path: Optional[str] = Field(
        default=None,
        description="Path to generated JSON report"
    )
    video_path: Optional[str] = Field(
        default=None,
        description="Path to video recording (GIF)"
    )
    screenshots_dir: Optional[str] = Field(
        default=None,
        description="Directory containing screenshots"
    )
    output_directory: Optional[str] = Field(
        default=None,
        description="Base output directory for this session"
    )

    # === Convenience Filename ===
    output_filename: str = Field(
        default="test_generated.py",
        description="Filename for generated Playwright tests"
    )

    def get_all_screenshots(self) -> list[str]:
        """Collect all screenshot paths from steps."""
        screenshots = []
        for step in self.steps:
            if step.screenshot_path:
                screenshots.append(step.screenshot_path)
        return screenshots

    def get_failed_scenarios(self) -> list[TestScenario]:
        """Get list of failed scenarios."""
        return [s for s in self.scenarios if not s.passed]

    def get_passed_scenarios(self) -> list[TestScenario]:
        """Get list of passed scenarios."""
        return [s for s in self.scenarios if s.passed]

    def to_summary_dict(self) -> dict:
        """Generate summary dictionary for reporting."""
        return {
            "session_id": self.session_id,
            "task": self.task,
            "url": self.url,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "duration_seconds": self.duration_seconds,
            "total_steps": self.total_steps,
            "total_actions": self.total_actions,
            "total_scenarios": self.total_scenarios,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": self.pass_rate,
            "artifacts": {
                "playwright_code": self.playwright_code_path,
                "test_cases": self.test_cases_path,
                "html_report": self.html_report_path,
                "json_report": self.json_report_path,
                "video": self.video_path,
                "replay_recording": self.replay_recording_path,
            },
        }

    def calculate_statistics(self):
        """Calculate and update statistics from steps and scenarios."""
        self.total_steps = len(self.steps)
        self.total_actions = sum(len(step.actions) for step in self.steps)
        self.total_scenarios = len(self.scenarios)
        self.passed = sum(1 for s in self.scenarios if s.passed)
        self.failed = sum(1 for s in self.scenarios if not s.passed)
