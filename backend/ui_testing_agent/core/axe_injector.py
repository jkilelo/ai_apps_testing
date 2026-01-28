"""
Axe Injector - Automated accessibility scanning via axe-core.

Injects axe-core JavaScript into a Playwright page and runs
WCAG 2.x automated checks, returning structured violation data.
"""

import json
import logging
from typing import Any

from ..models.a11y_models import (
    AxeScanResult,
    AxeViolation,
    AxeViolationNode,
    ImpactLevel,
)

logger = logging.getLogger(__name__)

AXE_CDN_URL = "https://cdn.jsdelivr.net/npm/axe-core@4.10.2/axe.min.js"

AXE_RUN_OPTIONS = json.dumps({
    "runOnly": [
        "wcag2a",
        "wcag2aa",
        "wcag21a",
        "wcag21aa",
        "wcag22aa",
        "best-practice",
    ]
})


class AxeInjector:
    """Injects axe-core into a Playwright page and runs accessibility scans."""

    @staticmethod
    async def scan(page: Any, url: str) -> AxeScanResult:
        """
        Run an axe-core accessibility scan on the given page.

        Args:
            page: Playwright Page object
            url: URL to navigate to and scan

        Returns:
            AxeScanResult with all violations, passes, and incomplete counts
        """
        # Navigate to the target URL
        logger.info(f"[AxeInjector] Navigating to {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_load_state("networkidle", timeout=15000)

        # Inject axe-core from CDN
        logger.info("[AxeInjector] Injecting axe-core JS")
        await page.add_script_tag(url=AXE_CDN_URL)

        # Wait for axe to be available
        await page.wait_for_function("typeof window.axe !== 'undefined'", timeout=10000)

        # Run axe scan
        logger.info("[AxeInjector] Running axe.run()")
        raw_result = await page.evaluate(f"""
            async () => {{
                const result = await axe.run(document, {AXE_RUN_OPTIONS});
                return JSON.stringify({{
                    violations: result.violations,
                    passes_count: result.passes.length,
                    incomplete_count: result.incomplete.length,
                }});
            }}
        """)

        result_data = json.loads(raw_result)
        logger.info(
            f"[AxeInjector] Scan complete: {len(result_data['violations'])} violations, "
            f"{result_data['passes_count']} passes, {result_data['incomplete_count']} incomplete"
        )

        # Parse violations into models
        violations = []
        for v in result_data["violations"]:
            impact_str = (v.get("impact") or "minor").lower()
            try:
                impact = ImpactLevel(impact_str)
            except ValueError:
                impact = ImpactLevel.MINOR

            nodes = []
            for node in v.get("nodes", []):
                nodes.append(AxeViolationNode(
                    target=node.get("target", []),
                    html=node.get("html", ""),
                    failure_summary=node.get("failureSummary", ""),
                ))

            wcag_tags = [t for t in v.get("tags", []) if t.startswith("wcag") or t == "best-practice"]

            violations.append(AxeViolation(
                rule_id=v.get("id", "unknown"),
                impact=impact,
                description=v.get("description", ""),
                help_url=v.get("helpUrl", ""),
                wcag_tags=wcag_tags,
                nodes=nodes,
            ))

        return AxeScanResult(
            url=url,
            violations=violations,
            passes_count=result_data["passes_count"],
            incomplete_count=result_data["incomplete_count"],
        )

    @staticmethod
    def build_axe_summary(scan: AxeScanResult) -> str:
        """
        Build a human-readable summary of axe scan results for the AI agent.

        Args:
            scan: The axe scan result

        Returns:
            Summary string for inclusion in agent prompt
        """
        if not scan.violations:
            return "Axe-core automated scan found NO violations."

        lines = [
            f"Axe-core automated scan found {len(scan.violations)} violation rules "
            f"({scan.total_violation_nodes} total affected elements):",
            "",
        ]

        for v in sorted(scan.violations, key=lambda x: list(ImpactLevel).index(x.impact)):
            lines.append(
                f"  - [{v.impact.value.upper()}] {v.rule_id}: {v.description} "
                f"({len(v.nodes)} elements)"
            )

        lines.append("")
        lines.append(
            "These issues were already detected automatically. "
            "Focus your behavioral testing on issues that automated tools CANNOT catch: "
            "keyboard navigation, focus management, dynamic content announcements, "
            "and form interaction patterns."
        )

        return "\n".join(lines)
