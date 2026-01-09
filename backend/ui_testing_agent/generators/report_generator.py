"""
Report Generator - Generates HTML and JSON reports from recorded test sessions.
"""

import json
import base64
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..models.test_session import TestSession
from ..models.test_scenario import TestScenario
from ..models.output_config import OutputConfig


class ReportGenerator:
    """
    Generates visual HTML reports and machine-readable JSON reports.

    The HTML report includes:
    - Session summary
    - Scenario details with pass/fail status
    - Screenshots embedded inline
    - Step-by-step execution details
    """

    def __init__(self, config: OutputConfig = None):
        """
        Initialize the report generator.

        Args:
            config: Output configuration options
        """
        self.config = config or OutputConfig()

    def generate_html(self, session: TestSession) -> str:
        """
        Generate an HTML report from a test session.

        Args:
            session: TestSession with recorded scenarios

        Returns:
            Complete HTML document as string
        """
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Report: {session.task}</title>
    {self._generate_styles()}
</head>
<body>
    <div class="container">
        {self._generate_header(session)}
        {self._generate_summary(session)}
        {self._generate_scenarios(session)}
        {self._generate_footer(session)}
    </div>
    {self._generate_scripts()}
</body>
</html>"""

    def generate_json(self, session: TestSession) -> str:
        """
        Generate a JSON report from a test session.

        Args:
            session: TestSession with recorded scenarios

        Returns:
            JSON report as string
        """
        report = {
            "report_type": "ui_testing_agent",
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "session": {
                "id": session.session_id,
                "task": session.task,
                "url": session.url,
                "started_at": session.started_at.isoformat(),
                "completed_at": session.completed_at.isoformat(),
                "duration_seconds": session.duration_seconds,
            },
            "summary": {
                "total_scenarios": session.total_scenarios,
                "passed": session.passed,
                "failed": session.failed,
                "pass_rate": session.pass_rate,
                "total_steps": session.total_steps,
                "total_actions": session.total_actions,
            },
            "scenarios": [
                self._scenario_to_json(scenario)
                for scenario in session.scenarios
            ],
            "artifacts": {
                "playwright_code": session.playwright_code_path,
                "test_cases": session.test_cases_path,
                "html_report": session.html_report_path,
                "video": session.video_path,
                "screenshots_dir": session.screenshots_dir,
            }
        }
        return json.dumps(report, indent=2, default=str)

    def _scenario_to_json(self, scenario: TestScenario) -> dict:
        """Convert scenario to JSON-serializable dict."""
        return {
            "id": scenario.scenario_id,
            "name": scenario.name,
            "type": scenario.scenario_type,
            "passed": scenario.passed,
            "failure_reason": scenario.failure_reason,
            "duration_ms": scenario.duration_ms,
            "steps": [
                {
                    "number": step.step_number,
                    "goal": step.goal,
                    "actions": [
                        {
                            "type": action.action_type,
                            "success": action.success,
                            "error": action.error,
                        }
                        for action in step.actions
                    ],
                    "page_url": step.page_url,
                    "has_failure": step.has_failure,
                }
                for step in scenario.steps
            ],
            "screenshots": scenario.screenshots,
        }

    def _generate_styles(self) -> str:
        """Generate CSS styles for the HTML report."""
        return """
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background-color: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
        }

        .header h1 {
            font-size: 1.8em;
            margin-bottom: 10px;
        }

        .header .meta {
            opacity: 0.9;
            font-size: 0.9em;
        }

        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }

        .stat-card .value {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .stat-card .label {
            color: #666;
            font-size: 0.9em;
        }

        .stat-card.passed .value { color: #22c55e; }
        .stat-card.failed .value { color: #ef4444; }
        .stat-card.rate .value { color: #3b82f6; }

        .scenario {
            background: white;
            border-radius: 10px;
            margin-bottom: 20px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .scenario-header {
            padding: 20px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #eee;
        }

        .scenario-header:hover {
            background-color: #f9f9f9;
        }

        .scenario.passed .scenario-header {
            border-left: 4px solid #22c55e;
        }

        .scenario.failed .scenario-header {
            border-left: 4px solid #ef4444;
        }

        .scenario-title {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 500;
        }

        .status-badge.passed {
            background-color: #dcfce7;
            color: #166534;
        }

        .status-badge.failed {
            background-color: #fee2e2;
            color: #991b1b;
        }

        .scenario-content {
            padding: 20px;
            display: none;
        }

        .scenario.expanded .scenario-content {
            display: block;
        }

        .step {
            padding: 15px;
            border-left: 3px solid #ddd;
            margin-left: 20px;
            margin-bottom: 15px;
        }

        .step.success { border-left-color: #22c55e; }
        .step.failure { border-left-color: #ef4444; }

        .step-header {
            font-weight: 500;
            margin-bottom: 10px;
        }

        .step-actions {
            font-size: 0.9em;
            color: #666;
        }

        .action {
            padding: 5px 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .action-icon {
            width: 20px;
            text-align: center;
        }

        .screenshot {
            max-width: 100%;
            margin-top: 15px;
            border-radius: 5px;
            border: 1px solid #ddd;
        }

        .failure-reason {
            background-color: #fee2e2;
            color: #991b1b;
            padding: 10px 15px;
            border-radius: 5px;
            margin-top: 10px;
            font-size: 0.9em;
        }

        .footer {
            text-align: center;
            padding: 30px;
            color: #666;
            font-size: 0.85em;
        }

        .expand-icon {
            transition: transform 0.3s;
        }

        .scenario.expanded .expand-icon {
            transform: rotate(180deg);
        }

        @media (max-width: 768px) {
            .summary {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>"""

    def _generate_header(self, session: TestSession) -> str:
        """Generate report header."""
        return f"""
        <div class="header">
            <h1>🧪 UI Testing Report</h1>
            <div class="meta">
                <strong>Task:</strong> {session.task}<br>
                <strong>URL:</strong> {session.url}<br>
                <strong>Session:</strong> {session.session_id}<br>
                <strong>Duration:</strong> {session.duration_seconds:.1f} seconds
            </div>
        </div>"""

    def _generate_summary(self, session: TestSession) -> str:
        """Generate summary statistics."""
        return f"""
        <div class="summary">
            <div class="stat-card">
                <div class="value">{session.total_scenarios}</div>
                <div class="label">Total Scenarios</div>
            </div>
            <div class="stat-card passed">
                <div class="value">{session.passed}</div>
                <div class="label">Passed</div>
            </div>
            <div class="stat-card failed">
                <div class="value">{session.failed}</div>
                <div class="label">Failed</div>
            </div>
            <div class="stat-card rate">
                <div class="value">{session.pass_rate:.0f}%</div>
                <div class="label">Pass Rate</div>
            </div>
        </div>"""

    def _generate_scenarios(self, session: TestSession) -> str:
        """Generate scenario sections."""
        scenarios_html = []
        for scenario in session.scenarios:
            scenarios_html.append(self._generate_scenario(scenario))
        return "\n".join(scenarios_html)

    def _generate_scenario(self, scenario: TestScenario) -> str:
        """Generate a single scenario section."""
        status_class = "passed" if scenario.passed else "failed"
        status_text = "PASSED" if scenario.passed else "FAILED"

        steps_html = []
        for step in scenario.steps:
            steps_html.append(self._generate_step(step))

        failure_html = ""
        if scenario.failure_reason:
            failure_html = f'<div class="failure-reason">❌ {scenario.failure_reason}</div>'

        return f"""
        <div class="scenario {status_class}">
            <div class="scenario-header" onclick="toggleScenario(this)">
                <div class="scenario-title">
                    <span>{scenario.scenario_id}</span>
                    <strong>{scenario.name}</strong>
                </div>
                <div style="display: flex; align-items: center; gap: 15px;">
                    <span class="status-badge {status_class}">{status_text}</span>
                    <span class="expand-icon">▼</span>
                </div>
            </div>
            <div class="scenario-content">
                <p><strong>Type:</strong> {scenario.scenario_type}</p>
                <p><strong>Duration:</strong> {scenario.duration_ms or 0}ms</p>
                {failure_html}
                <h4 style="margin: 20px 0 10px;">Steps</h4>
                {"".join(steps_html)}
            </div>
        </div>"""

    def _generate_step(self, step) -> str:
        """Generate a single step section."""
        status_class = "failure" if step.has_failure else "success"

        actions_html = []
        for action in step.actions:
            icon = "✅" if action.success is not False else "❌"
            actions_html.append(f"""
                <div class="action">
                    <span class="action-icon">{icon}</span>
                    <span>{action.get_description()}</span>
                </div>""")

        screenshot_html = ""
        if step.screenshot_path:
            # Try to embed screenshot as base64
            screenshot_html = self._embed_screenshot(step.screenshot_path)

        return f"""
            <div class="step {status_class}">
                <div class="step-header">Step {step.step_number + 1}: {step.goal or 'Execute actions'}</div>
                <div class="step-actions">
                    {"".join(actions_html)}
                </div>
                <div class="step-meta" style="font-size: 0.8em; color: #999; margin-top: 10px;">
                    URL: {step.page_url}
                </div>
                {screenshot_html}
            </div>"""

    def _embed_screenshot(self, path: str) -> str:
        """Embed screenshot as base64 image."""
        try:
            filepath = Path(path)
            if filepath.exists():
                with open(filepath, "rb") as f:
                    data = base64.b64encode(f.read()).decode()
                return f'<img class="screenshot" src="data:image/png;base64,{data}" alt="Screenshot">'
        except Exception:
            pass
        return f'<p class="screenshot-link">Screenshot: {path}</p>'

    def _generate_footer(self, session: TestSession) -> str:
        """Generate report footer."""
        return f"""
        <div class="footer">
            <p>Generated by UI Testing Agent</p>
            <p>Session: {session.session_id} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>"""

    def _generate_scripts(self) -> str:
        """Generate JavaScript for interactivity."""
        return """
    <script>
        function toggleScenario(header) {
            const scenario = header.parentElement;
            scenario.classList.toggle('expanded');
        }

        // Expand failed scenarios by default
        document.querySelectorAll('.scenario.failed').forEach(s => s.classList.add('expanded'));
    </script>"""
