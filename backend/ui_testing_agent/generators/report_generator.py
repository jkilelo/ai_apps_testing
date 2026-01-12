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
        """Generate CSS styles for the HTML report with Acme corporate branding."""
        return """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --acme-navy: #003B70;
            --acme-navy-light: #004d94;
            --acme-navy-dark: #002a52;
            --acme-red: #D9261C;
            --acme-red-light: #e54338;
            --acme-gray-50: #f8f9fa;
            --acme-gray-100: #f1f3f5;
            --acme-gray-200: #e9ecef;
            --acme-gray-300: #dee2e6;
            --acme-gray-400: #ced4da;
            --acme-gray-500: #adb5bd;
            --acme-gray-600: #6c757d;
            --acme-gray-700: #495057;
            --acme-gray-800: #343a40;
            --acme-gray-900: #212529;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--acme-gray-100);
            color: var(--acme-gray-900);
            line-height: 1.6;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 24px;
        }

        /* Header with Acme branding */
        .header {
            background: linear-gradient(135deg, var(--acme-navy) 0%, var(--acme-navy-light) 100%);
            color: white;
            padding: 32px;
            border-radius: 16px;
            margin-bottom: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 59, 112, 0.1), 0 2px 4px -1px rgba(0, 59, 112, 0.06);
        }

        .header-top {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 20px;
        }

        .header-logo {
            width: 48px;
            height: 48px;
            background: rgba(255,255,255,0.15);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
        }

        .header h1 {
            font-size: 1.5em;
            font-weight: 700;
            margin-bottom: 4px;
        }

        .header .subtitle {
            font-size: 0.85em;
            opacity: 0.8;
        }

        .header .meta {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            background: rgba(255,255,255,0.1);
            padding: 16px;
            border-radius: 12px;
            font-size: 0.85em;
        }

        .header .meta-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .header .meta-item i {
            width: 20px;
            opacity: 0.7;
        }

        .header .meta-label {
            opacity: 0.7;
            margin-right: 4px;
        }

        /* Summary Stats */
        .summary {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }

        @media (min-width: 768px) {
            .summary {
                grid-template-columns: repeat(4, 1fr);
            }
        }

        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid var(--acme-gray-200);
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }

        .stat-card .stat-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }

        .stat-card .stat-icon {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
        }

        .stat-card .label {
            font-size: 0.7em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--acme-gray-500);
        }

        .stat-card .value {
            font-size: 2em;
            font-weight: 700;
            line-height: 1;
        }

        .stat-card.total .stat-icon { background: rgba(0,59,112,0.1); color: var(--acme-navy); }
        .stat-card.total .value { color: var(--acme-navy); }

        .stat-card.passed .stat-icon { background: #dcfce7; color: #16a34a; }
        .stat-card.passed .value { color: #16a34a; }

        .stat-card.failed .stat-icon { background: #fee2e2; color: #dc2626; }
        .stat-card.failed .value { color: #dc2626; }

        .stat-card.rate .stat-icon { background: #dbeafe; color: #2563eb; }
        .stat-card.rate .value { color: #2563eb; }

        /* Scenarios */
        .scenarios-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
            padding: 0 4px;
        }

        .scenarios-header h2 {
            font-size: 1.1em;
            font-weight: 600;
            color: var(--acme-gray-800);
        }

        .scenarios-header .count {
            background: var(--acme-navy);
            color: white;
            padding: 2px 10px;
            border-radius: 20px;
            font-size: 0.75em;
            font-weight: 600;
        }

        .scenario {
            background: white;
            border-radius: 16px;
            margin-bottom: 16px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid var(--acme-gray-200);
        }

        .scenario-header {
            padding: 16px 20px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--acme-gray-100);
            transition: background 0.2s;
        }

        .scenario-header:hover {
            background-color: var(--acme-gray-50);
        }

        .scenario.passed .scenario-header {
            border-left: 4px solid #16a34a;
        }

        .scenario.failed .scenario-header {
            border-left: 4px solid #dc2626;
        }

        .scenario-title {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .scenario-id {
            font-size: 0.75em;
            font-weight: 600;
            color: var(--acme-gray-500);
            background: var(--acme-gray-100);
            padding: 4px 8px;
            border-radius: 6px;
        }

        .scenario-name {
            font-weight: 600;
            color: var(--acme-gray-800);
        }

        .status-badge {
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.75em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.03em;
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
            background: var(--acme-gray-50);
        }

        .scenario.expanded .scenario-content {
            display: block;
        }

        .scenario-meta {
            display: flex;
            gap: 24px;
            padding: 12px 16px;
            background: white;
            border-radius: 10px;
            margin-bottom: 16px;
            font-size: 0.85em;
        }

        .scenario-meta span {
            color: var(--acme-gray-600);
        }

        .scenario-meta strong {
            color: var(--acme-gray-800);
        }

        .steps-label {
            font-size: 0.85em;
            font-weight: 600;
            color: var(--acme-gray-700);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .step {
            padding: 16px;
            background: white;
            border-radius: 10px;
            margin-bottom: 12px;
            border-left: 3px solid var(--acme-gray-300);
        }

        .step.success { border-left-color: #16a34a; }
        .step.failure { border-left-color: #dc2626; }

        .step-header {
            font-weight: 600;
            font-size: 0.9em;
            color: var(--acme-gray-800);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .step-number {
            background: var(--acme-navy);
            color: white;
            width: 24px;
            height: 24px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75em;
            font-weight: 700;
        }

        .step-actions {
            font-size: 0.85em;
            color: var(--acme-gray-600);
        }

        .action {
            padding: 8px 0;
            display: flex;
            align-items: flex-start;
            gap: 10px;
            border-bottom: 1px solid var(--acme-gray-100);
        }

        .action:last-child {
            border-bottom: none;
        }

        .action-icon {
            width: 22px;
            height: 22px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.7em;
            flex-shrink: 0;
        }

        .action-icon.success {
            background: #dcfce7;
            color: #16a34a;
        }

        .action-icon.failure {
            background: #fee2e2;
            color: #dc2626;
        }

        .step-url {
            font-size: 0.75em;
            color: var(--acme-gray-500);
            margin-top: 12px;
            padding: 8px 12px;
            background: var(--acme-gray-50);
            border-radius: 6px;
            font-family: monospace;
            word-break: break-all;
        }

        .screenshot {
            max-width: 100%;
            margin-top: 16px;
            border-radius: 10px;
            border: 1px solid var(--acme-gray-200);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .failure-reason {
            background-color: #fee2e2;
            color: #991b1b;
            padding: 12px 16px;
            border-radius: 10px;
            margin: 12px 0;
            font-size: 0.85em;
            display: flex;
            align-items: flex-start;
            gap: 10px;
        }

        .failure-reason i {
            margin-top: 2px;
        }

        .expand-icon {
            color: var(--acme-gray-400);
            transition: transform 0.3s;
            font-size: 0.85em;
        }

        .scenario.expanded .expand-icon {
            transform: rotate(180deg);
        }

        .expand-btn {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        /* Footer */
        .footer {
            text-align: center;
            padding: 32px;
            color: var(--acme-gray-500);
            font-size: 0.8em;
        }

        .footer-brand {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            margin-bottom: 8px;
            color: var(--acme-navy);
            font-weight: 600;
        }

        @media (max-width: 768px) {
            .container {
                padding: 16px;
            }
            .header {
                padding: 20px;
            }
            .header h1 {
                font-size: 1.2em;
            }
            .header .meta {
                grid-template-columns: 1fr;
            }
            .stat-card {
                padding: 16px;
            }
            .stat-card .value {
                font-size: 1.5em;
            }
            .scenario-header {
                flex-wrap: wrap;
            }
            .scenario-meta {
                flex-wrap: wrap;
                gap: 12px;
            }
        }
    </style>"""

    def _generate_header(self, session: TestSession) -> str:
        """Generate report header with Acme branding."""
        return f"""
        <div class="header">
            <div class="header-top">
                <div class="header-logo">
                    <i class="fas fa-flask"></i>
                </div>
                <div>
                    <h1>Acme Browser Agent Report</h1>
                    <div class="subtitle">Automated UI Testing Results</div>
                </div>
            </div>
            <div class="meta">
                <div class="meta-item">
                    <i class="fas fa-tasks"></i>
                    <span class="meta-label">Task:</span> {session.task}
                </div>
                <div class="meta-item">
                    <i class="fas fa-globe"></i>
                    <span class="meta-label">URL:</span> {session.url}
                </div>
                <div class="meta-item">
                    <i class="fas fa-fingerprint"></i>
                    <span class="meta-label">Session:</span> {session.session_id[:20]}...
                </div>
                <div class="meta-item">
                    <i class="fas fa-clock"></i>
                    <span class="meta-label">Duration:</span> {session.duration_seconds:.1f}s
                </div>
            </div>
        </div>"""

    def _generate_summary(self, session: TestSession) -> str:
        """Generate summary statistics with Acme branding."""
        return f"""
        <div class="summary">
            <div class="stat-card total">
                <div class="stat-header">
                    <div class="stat-icon">
                        <i class="fas fa-list-check"></i>
                    </div>
                    <div class="label">Scenarios</div>
                </div>
                <div class="value">{session.total_scenarios}</div>
            </div>
            <div class="stat-card passed">
                <div class="stat-header">
                    <div class="stat-icon">
                        <i class="fas fa-check-circle"></i>
                    </div>
                    <div class="label">Passed</div>
                </div>
                <div class="value">{session.passed}</div>
            </div>
            <div class="stat-card failed">
                <div class="stat-header">
                    <div class="stat-icon">
                        <i class="fas fa-times-circle"></i>
                    </div>
                    <div class="label">Failed</div>
                </div>
                <div class="value">{session.failed}</div>
            </div>
            <div class="stat-card rate">
                <div class="stat-header">
                    <div class="stat-icon">
                        <i class="fas fa-chart-pie"></i>
                    </div>
                    <div class="label">Pass Rate</div>
                </div>
                <div class="value">{session.pass_rate:.0f}%</div>
            </div>
        </div>"""

    def _generate_scenarios(self, session: TestSession) -> str:
        """Generate scenario sections with Acme branding."""
        scenarios_html = []
        for scenario in session.scenarios:
            scenarios_html.append(self._generate_scenario(scenario))

        return f"""
        <div class="scenarios-header">
            <i class="fas fa-vial" style="color: var(--acme-navy);"></i>
            <h2>Test Scenarios</h2>
            <span class="count">{len(session.scenarios)}</span>
        </div>
        {"".join(scenarios_html)}"""

    def _generate_scenario(self, scenario: TestScenario) -> str:
        """Generate a single scenario section with Acme branding."""
        status_class = "passed" if scenario.passed else "failed"
        status_text = "PASSED" if scenario.passed else "FAILED"
        status_icon = "fa-check-circle" if scenario.passed else "fa-times-circle"

        steps_html = []
        for step in scenario.steps:
            steps_html.append(self._generate_step(step))

        failure_html = ""
        if scenario.failure_reason:
            failure_html = f"""
                <div class="failure-reason">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>{scenario.failure_reason}</span>
                </div>"""

        return f"""
        <div class="scenario {status_class}">
            <div class="scenario-header" onclick="toggleScenario(this)">
                <div class="scenario-title">
                    <span class="scenario-id">{scenario.scenario_id}</span>
                    <span class="scenario-name">{scenario.name}</span>
                </div>
                <div class="expand-btn">
                    <span class="status-badge {status_class}">
                        <i class="fas {status_icon}" style="margin-right: 4px;"></i>
                        {status_text}
                    </span>
                    <i class="fas fa-chevron-down expand-icon"></i>
                </div>
            </div>
            <div class="scenario-content">
                <div class="scenario-meta">
                    <span><i class="fas fa-tag" style="margin-right: 6px; opacity: 0.5;"></i> <strong>Type:</strong> {scenario.scenario_type}</span>
                    <span><i class="fas fa-stopwatch" style="margin-right: 6px; opacity: 0.5;"></i> <strong>Duration:</strong> {scenario.duration_ms or 0}ms</span>
                    <span><i class="fas fa-shoe-prints" style="margin-right: 6px; opacity: 0.5;"></i> <strong>Steps:</strong> {len(scenario.steps)}</span>
                </div>
                {failure_html}
                <div class="steps-label">
                    <i class="fas fa-list-ol"></i>
                    Execution Steps
                </div>
                {"".join(steps_html)}
            </div>
        </div>"""

    def _generate_step(self, step) -> str:
        """Generate a single step section with Acme branding."""
        status_class = "failure" if step.has_failure else "success"

        actions_html = []
        for action in step.actions:
            icon_class = "success" if action.success is not False else "failure"
            icon = "fa-check" if action.success is not False else "fa-times"
            actions_html.append(f"""
                <div class="action">
                    <div class="action-icon {icon_class}">
                        <i class="fas {icon}"></i>
                    </div>
                    <span>{action.get_description()}</span>
                </div>""")

        screenshot_html = ""
        if step.screenshot_path:
            # Try to embed screenshot as base64
            screenshot_html = self._embed_screenshot(step.screenshot_path)

        return f"""
            <div class="step {status_class}">
                <div class="step-header">
                    <span class="step-number">{step.step_number + 1}</span>
                    {step.goal or 'Execute actions'}
                </div>
                <div class="step-actions">
                    {"".join(actions_html)}
                </div>
                <div class="step-url">
                    <i class="fas fa-link" style="margin-right: 6px; opacity: 0.5;"></i>
                    {step.page_url}
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
        """Generate report footer with Acme branding."""
        return f"""
        <div class="footer">
            <div class="footer-brand">
                <i class="fas fa-flask"></i>
                Acme Browser Agent
            </div>
            <p>Session: {session.session_id[:20]}...</p>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
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
