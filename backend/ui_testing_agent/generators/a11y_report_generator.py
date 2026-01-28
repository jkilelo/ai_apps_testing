"""
Accessibility Report Generator - Professional HTML and JSON reports for a11y audits.

Uses the same Acme branding (Inter, Font Awesome, navy variables) as ReportGenerator.
"""

import json
from datetime import datetime
from typing import Optional

from ..models.a11y_models import (
    A11yAuditSession,
    A11yAuditScore,
    A11yCategoryScore,
    AxeScanResult,
    AxeViolation,
    ImpactLevel,
)


class A11yReportGenerator:
    """Generates HTML and JSON accessibility audit reports."""

    def generate_html(self, session: A11yAuditSession) -> str:
        score = session.audit_score
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accessibility Audit: {session.url}</title>
    {self._styles()}
</head>
<body>
    <div class="container">
        {self._header(session)}
        {self._score_gauge(score)}
        {self._category_breakdown(score)}
        {self._violations_table(session.axe_scan)}
        {self._behavioral_findings(session)}
        {self._recommendations(session)}
        {self._footer(session)}
    </div>
    {self._scripts()}
</body>
</html>"""

    def generate_json(self, session: A11yAuditSession) -> str:
        score = session.audit_score
        report = {
            "report_type": "accessibility_audit",
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "session": {
                "id": session.session_id,
                "url": session.url,
                "started_at": session.started_at.isoformat(),
                "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            },
            "score": {
                "overall": score.overall_score if score else None,
                "grade": score.grade if score else None,
                "total_violations": score.total_violations if score else 0,
                "categories": [
                    {"category": c.category, "score": c.score, "issues": c.issues_found}
                    for c in (score.categories if score else [])
                ],
            },
            "axe_scan": self._axe_to_json(session.axe_scan) if session.axe_scan else None,
            "behavioral_summary": {
                "total_steps": session.behavioral_session.total_steps if session.behavioral_session else 0,
                "scenarios": session.behavioral_session.total_scenarios if session.behavioral_session else 0,
                "passed": session.behavioral_session.passed if session.behavioral_session else 0,
                "failed": session.behavioral_session.failed if session.behavioral_session else 0,
            } if session.behavioral_session else None,
        }
        return json.dumps(report, indent=2, default=str)

    def _axe_to_json(self, scan: AxeScanResult) -> dict:
        return {
            "url": scan.url,
            "total_violations": len(scan.violations),
            "total_affected_elements": scan.total_violation_nodes,
            "passes_count": scan.passes_count,
            "incomplete_count": scan.incomplete_count,
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "impact": v.impact.value,
                    "description": v.description,
                    "help_url": v.help_url,
                    "wcag_tags": v.wcag_tags,
                    "affected_elements": len(v.nodes),
                }
                for v in scan.violations
            ],
        }

    # ── HTML sections ────────────────────────────────────────────

    def _header(self, session: A11yAuditSession) -> str:
        return f"""
        <div class="header">
            <div class="header-top">
                <div class="header-logo">
                    <i class="fas fa-universal-access"></i>
                </div>
                <div>
                    <h1>Accessibility Audit Report</h1>
                    <div class="subtitle">WCAG 2.2 Compliance Assessment</div>
                </div>
            </div>
            <div class="meta">
                <div class="meta-item">
                    <i class="fas fa-globe"></i>
                    <span class="meta-label">URL:</span> {session.url}
                </div>
                <div class="meta-item">
                    <i class="fas fa-fingerprint"></i>
                    <span class="meta-label">Session:</span> {session.session_id[:20]}...
                </div>
                <div class="meta-item">
                    <i class="fas fa-calendar"></i>
                    <span class="meta-label">Date:</span> {session.started_at.strftime('%Y-%m-%d %H:%M')}
                </div>
                <div class="meta-item">
                    <i class="fas fa-clock"></i>
                    <span class="meta-label">Duration:</span> {self._duration(session)}
                </div>
            </div>
        </div>"""

    def _duration(self, session: A11yAuditSession) -> str:
        if session.completed_at and session.started_at:
            secs = (session.completed_at - session.started_at).total_seconds()
            return f"{secs:.1f}s"
        return "N/A"

    def _score_gauge(self, score: Optional[A11yAuditScore]) -> str:
        if not score:
            return ""
        s = score.overall_score
        grade = score.grade
        color = self._score_color(s)
        return f"""
        <div class="score-section">
            <div class="score-gauge" style="--score-color: {color};">
                <svg viewBox="0 0 200 120" class="gauge-svg">
                    <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none"
                          stroke="#e9ecef" stroke-width="16" stroke-linecap="round"/>
                    <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none"
                          stroke="{color}" stroke-width="16" stroke-linecap="round"
                          stroke-dasharray="{s * 2.51} 251"
                          class="gauge-fill"/>
                    <text x="100" y="80" text-anchor="middle"
                          font-size="36" font-weight="700" fill="{color}">{s}</text>
                    <text x="100" y="100" text-anchor="middle"
                          font-size="14" fill="#6c757d">/100</text>
                </svg>
                <div class="grade-badge" style="background: {color};">{grade}</div>
            </div>
            <div class="score-summary">
                <span class="violations-count">{score.total_violations} violations found</span>
            </div>
        </div>"""

    def _score_color(self, score: int) -> str:
        if score >= 90:
            return "#16a34a"
        if score >= 80:
            return "#65a30d"
        if score >= 70:
            return "#ca8a04"
        if score >= 60:
            return "#ea580c"
        return "#dc2626"

    def _category_breakdown(self, score: Optional[A11yAuditScore]) -> str:
        if not score or not score.categories:
            return ""
        bars = []
        for cat in score.categories:
            color = self._score_color(cat.score)
            bars.append(f"""
                <div class="category-row">
                    <div class="category-label">{cat.category}</div>
                    <div class="category-bar-track">
                        <div class="category-bar-fill" style="width:{cat.score}%; background:{color};"></div>
                    </div>
                    <div class="category-score" style="color:{color};">{cat.score}</div>
                    <div class="category-issues">{cat.issues_found} issues</div>
                </div>""")
        return f"""
        <div class="section">
            <h2><i class="fas fa-chart-bar"></i> Category Breakdown</h2>
            <div class="category-chart">{"".join(bars)}</div>
        </div>"""

    def _violations_table(self, scan: Optional[AxeScanResult]) -> str:
        if not scan or not scan.violations:
            return """
            <div class="section">
                <h2><i class="fas fa-check-circle" style="color:#16a34a;"></i> No Automated Violations Found</h2>
                <p>The axe-core automated scan did not detect any WCAG violations.</p>
            </div>"""

        sorted_violations = sorted(
            scan.violations,
            key=lambda v: list(ImpactLevel).index(v.impact),
        )

        rows = []
        for v in sorted_violations:
            badge_cls = f"impact-{v.impact.value}"
            rows.append(f"""
                <tr>
                    <td><span class="impact-badge {badge_cls}">{v.impact.value.upper()}</span></td>
                    <td><code>{v.rule_id}</code></td>
                    <td>{v.description}</td>
                    <td>{len(v.nodes)}</td>
                    <td><a href="{v.help_url}" target="_blank" rel="noopener">Learn more</a></td>
                </tr>""")

        return f"""
        <div class="section">
            <h2><i class="fas fa-exclamation-triangle"></i> Violations ({len(scan.violations)} rules, {scan.total_violation_nodes} elements)</h2>
            <table class="violations-table">
                <thead>
                    <tr>
                        <th>Impact</th>
                        <th>Rule</th>
                        <th>Description</th>
                        <th>Elements</th>
                        <th>Help</th>
                    </tr>
                </thead>
                <tbody>{"".join(rows)}</tbody>
            </table>
        </div>"""

    def _behavioral_findings(self, session: A11yAuditSession) -> str:
        if not session.behavioral_session:
            return """
            <div class="section">
                <h2><i class="fas fa-keyboard"></i> Behavioral Testing</h2>
                <p>Behavioral testing was skipped for this audit.</p>
            </div>"""

        bs = session.behavioral_session
        scenario_items = []
        for scenario in bs.scenarios:
            status_cls = "passed" if scenario.passed else "failed"
            status_icon = "fa-check-circle" if scenario.passed else "fa-times-circle"
            status_text = "PASS" if scenario.passed else "FAIL"
            scenario_items.append(f"""
                <div class="finding {status_cls}">
                    <div class="finding-status">
                        <i class="fas {status_icon}"></i> {status_text}
                    </div>
                    <div class="finding-detail">
                        <strong>{scenario.name}</strong>
                        {f'<p class="finding-reason">{scenario.failure_reason}</p>' if scenario.failure_reason else ''}
                    </div>
                </div>""")

        return f"""
        <div class="section">
            <h2><i class="fas fa-keyboard"></i> Behavioral Findings ({bs.passed} passed, {bs.failed} failed)</h2>
            <div class="findings-list">{"".join(scenario_items) if scenario_items else '<p>No behavioral scenarios recorded.</p>'}</div>
        </div>"""

    def _recommendations(self, session: A11yAuditSession) -> str:
        recs = []
        if session.axe_scan:
            if session.axe_scan.critical_count > 0:
                recs.append("Fix all critical violations immediately — these block access for users with disabilities.")
            if session.axe_scan.serious_count > 0:
                recs.append("Address serious violations as high priority — these significantly impair usability.")
            contrast_violations = [v for v in session.axe_scan.violations if "contrast" in v.rule_id.lower()]
            if contrast_violations:
                recs.append("Review color contrast ratios across the site. Ensure 4.5:1 for normal text, 3:1 for large text.")
            if any("label" in v.rule_id.lower() for v in session.axe_scan.violations):
                recs.append("Ensure all form inputs have visible, associated labels.")
            if any("alt" in v.rule_id.lower() for v in session.axe_scan.violations):
                recs.append("Add descriptive alt text to all informative images.")

        if not recs:
            recs.append("Continue monitoring accessibility with each release.")
            recs.append("Consider regular manual testing with screen readers (NVDA, VoiceOver).")

        items = "".join(f"<li>{r}</li>" for r in recs)
        return f"""
        <div class="section">
            <h2><i class="fas fa-lightbulb"></i> Recommendations</h2>
            <ul class="recommendations">{items}</ul>
        </div>"""

    def _footer(self, session: A11yAuditSession) -> str:
        return f"""
        <div class="footer">
            <div class="footer-brand">
                <i class="fas fa-universal-access"></i>
                Acme Accessibility Auditor
            </div>
            <p>Session: {session.session_id[:20]}...</p>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>"""

    # ── Styles & Scripts ─────────────────────────────────────────

    def _styles(self) -> str:
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
            --acme-gray-50: #f8f9fa;
            --acme-gray-100: #f1f3f5;
            --acme-gray-200: #e9ecef;
            --acme-gray-300: #dee2e6;
            --acme-gray-500: #adb5bd;
            --acme-gray-600: #6c757d;
            --acme-gray-700: #495057;
            --acme-gray-800: #343a40;
            --acme-gray-900: #212529;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--acme-gray-100);
            color: var(--acme-gray-900);
            line-height: 1.6;
        }

        .container { max-width: 1200px; margin: 0 auto; padding: 24px; }

        /* Header */
        .header {
            background: linear-gradient(135deg, var(--acme-navy) 0%, var(--acme-navy-light) 100%);
            color: white; padding: 32px; border-radius: 16px; margin-bottom: 24px;
            box-shadow: 0 4px 6px -1px rgba(0,59,112,0.1);
        }
        .header-top { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
        .header-logo {
            width: 48px; height: 48px; background: rgba(255,255,255,0.15);
            border-radius: 12px; display: flex; align-items: center;
            justify-content: center; font-size: 24px;
        }
        .header h1 { font-size: 1.5em; font-weight: 700; margin-bottom: 4px; }
        .header .subtitle { font-size: 0.85em; opacity: 0.8; }
        .header .meta {
            display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;
            background: rgba(255,255,255,0.1); padding: 16px; border-radius: 12px; font-size: 0.85em;
        }
        .header .meta-item { display: flex; align-items: center; gap: 8px; }
        .header .meta-item i { width: 20px; opacity: 0.7; }
        .header .meta-label { opacity: 0.7; margin-right: 4px; }

        /* Score Gauge */
        .score-section {
            background: white; border-radius: 16px; padding: 32px;
            margin-bottom: 24px; text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid var(--acme-gray-200);
        }
        .score-gauge { position: relative; display: inline-block; }
        .gauge-svg { width: 240px; height: 150px; }
        .gauge-fill { transition: stroke-dasharray 1s ease-out; }
        .grade-badge {
            display: inline-block; color: white; font-size: 1.5em; font-weight: 700;
            padding: 6px 20px; border-radius: 12px; margin-top: 8px;
        }
        .score-summary { margin-top: 12px; color: var(--acme-gray-600); }

        /* Sections */
        .section {
            background: white; border-radius: 16px; padding: 24px;
            margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid var(--acme-gray-200);
        }
        .section h2 {
            font-size: 1.1em; font-weight: 600; color: var(--acme-gray-800);
            margin-bottom: 16px; display: flex; align-items: center; gap: 10px;
        }
        .section h2 i { color: var(--acme-navy); }

        /* Category Bars */
        .category-row {
            display: grid; grid-template-columns: 160px 1fr 50px 80px;
            align-items: center; gap: 12px; padding: 10px 0;
            border-bottom: 1px solid var(--acme-gray-100);
        }
        .category-row:last-child { border-bottom: none; }
        .category-label { font-weight: 500; font-size: 0.9em; }
        .category-bar-track {
            height: 12px; background: var(--acme-gray-200); border-radius: 6px; overflow: hidden;
        }
        .category-bar-fill {
            height: 100%; border-radius: 6px; transition: width 0.8s ease-out;
        }
        .category-score { font-weight: 700; text-align: right; }
        .category-issues { font-size: 0.8em; color: var(--acme-gray-600); }

        /* Violations Table */
        .violations-table { width: 100%; border-collapse: collapse; font-size: 0.9em; }
        .violations-table th {
            text-align: left; padding: 10px 12px; background: var(--acme-gray-50);
            font-weight: 600; color: var(--acme-gray-700); border-bottom: 2px solid var(--acme-gray-200);
        }
        .violations-table td {
            padding: 10px 12px; border-bottom: 1px solid var(--acme-gray-100);
            vertical-align: top;
        }
        .violations-table code {
            background: var(--acme-gray-100); padding: 2px 6px; border-radius: 4px;
            font-size: 0.85em;
        }
        .violations-table a { color: var(--acme-navy); text-decoration: none; }
        .violations-table a:hover { text-decoration: underline; }

        .impact-badge {
            display: inline-block; padding: 3px 10px; border-radius: 12px;
            font-size: 0.75em; font-weight: 600; text-transform: uppercase;
        }
        .impact-critical { background: #fee2e2; color: #991b1b; }
        .impact-serious { background: #ffedd5; color: #9a3412; }
        .impact-moderate { background: #fef9c3; color: #854d0e; }
        .impact-minor { background: #f0fdf4; color: #166534; }

        /* Findings */
        .findings-list { display: flex; flex-direction: column; gap: 10px; }
        .finding {
            display: flex; gap: 14px; padding: 14px 16px; border-radius: 10px;
            align-items: flex-start;
        }
        .finding.passed { background: #f0fdf4; border-left: 4px solid #16a34a; }
        .finding.failed { background: #fef2f2; border-left: 4px solid #dc2626; }
        .finding-status { font-weight: 600; flex-shrink: 0; white-space: nowrap; }
        .finding.passed .finding-status { color: #16a34a; }
        .finding.failed .finding-status { color: #dc2626; }
        .finding-detail strong { display: block; margin-bottom: 2px; }
        .finding-reason { font-size: 0.85em; color: var(--acme-gray-600); margin-top: 4px; }

        /* Recommendations */
        .recommendations { list-style: none; }
        .recommendations li {
            padding: 10px 0 10px 28px; position: relative;
            border-bottom: 1px solid var(--acme-gray-100); font-size: 0.9em;
        }
        .recommendations li:last-child { border-bottom: none; }
        .recommendations li::before {
            content: '\\f0eb'; font-family: 'Font Awesome 6 Free'; font-weight: 900;
            position: absolute; left: 0; color: #ca8a04;
        }

        /* Footer */
        .footer {
            text-align: center; padding: 32px; color: var(--acme-gray-500); font-size: 0.8em;
        }
        .footer-brand {
            display: flex; align-items: center; justify-content: center; gap: 8px;
            margin-bottom: 8px; color: var(--acme-navy); font-weight: 600;
        }

        @media (max-width: 768px) {
            .container { padding: 16px; }
            .header { padding: 20px; }
            .header .meta { grid-template-columns: 1fr; }
            .category-row { grid-template-columns: 1fr; gap: 4px; }
            .violations-table { display: block; overflow-x: auto; }
        }
    </style>"""

    def _scripts(self) -> str:
        return """
    <script>
        // Animate gauge on load
        document.addEventListener('DOMContentLoaded', () => {
            document.querySelectorAll('.gauge-fill').forEach(el => {
                const dash = el.getAttribute('stroke-dasharray');
                el.setAttribute('stroke-dasharray', '0 251');
                requestAnimationFrame(() => {
                    requestAnimationFrame(() => {
                        el.setAttribute('stroke-dasharray', dash);
                    });
                });
            });
        });
    </script>"""
