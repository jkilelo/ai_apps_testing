"""
Output configuration model for controlling artifact generation.
"""

from typing import Literal
from pydantic import BaseModel, Field


class OutputConfig(BaseModel):
    """
    User-configurable output options for the UI Testing Agent.

    Controls what artifacts are generated after exploratory testing.
    """

    # === Code Generation ===
    generate_playwright_code: bool = Field(
        default=True,
        description="Generate Playwright-Python test code"
    )
    playwright_style: Literal["pytest", "unittest"] = Field(
        default="pytest",
        description="Test framework style for generated code"
    )
    include_selector_fallbacks: bool = Field(
        default=True,
        description="Include self-healing fallback selectors in generated code"
    )
    include_comments: bool = Field(
        default=True,
        description="Include descriptive comments in generated code"
    )

    # === Test Documentation ===
    generate_test_cases: bool = Field(
        default=True,
        description="Generate formal test case documentation"
    )
    test_case_format: Literal["json", "yaml", "markdown", "gherkin"] = Field(
        default="json",
        description="Format for test case documentation"
    )

    # === Reports ===
    generate_html_report: bool = Field(
        default=True,
        description="Generate visual HTML report with screenshots"
    )
    generate_json_report: bool = Field(
        default=True,
        description="Generate machine-readable JSON report"
    )

    # === Evidence/Artifacts ===
    capture_video: bool = Field(
        default=True,
        description="Capture video recording (uses browser-use generate_gif)"
    )
    save_screenshots: bool = Field(
        default=True,
        description="Save screenshots to output directory"
    )
    save_raw_history: bool = Field(
        default=True,
        description="Save raw AgentHistoryList as JSON"
    )

    # === Output Location ===
    output_directory: str = Field(
        default="./test_outputs",
        description="Base directory for all output artifacts"
    )
    create_session_subdir: bool = Field(
        default=True,
        description="Create timestamped subdirectory for each session"
    )

    # === Code Generation Options ===
    max_selectors_per_element: int = Field(
        default=4,
        description="Maximum fallback selectors per element"
    )
    group_scenarios: bool = Field(
        default=True,
        description="Group steps into logical test scenarios"
    )

    def get_output_path(self, session_id: str) -> str:
        """Get the output path for a session."""
        import os
        if self.create_session_subdir:
            return os.path.join(self.output_directory, session_id)
        return self.output_directory
