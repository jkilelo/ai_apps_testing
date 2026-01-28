"""
Accessibility Audit Service - Orchestrates two-phase accessibility auditing.

Phase 1: axe-core automated scanning (AxeInjector) — uses Playwright directly
Phase 2: AI behavioral testing (A11yAgent) — uses browser-use Agent
Scoring: Weighted deduction model producing 0-100 score
Report:  Professional HTML + JSON output

Note: Both phases run in separate threads with their own event loops because
asyncio.create_subprocess_exec doesn't work with uvicorn's event loop on Windows.
"""

import asyncio
import concurrent.futures
import logging
import os
import sys
from datetime import datetime
from typing import Optional, Any
from uuid import uuid4

from .models.a11y_models import (
    A11yAuditSession,
    A11yAuditScore,
    A11yCategoryScore,
    AxeScanResult,
    ImpactLevel,
)
from .models.output_config import OutputConfig
from .models.test_session import TestSession
from .core.axe_injector import AxeInjector
from .core.a11y_agent import A11yAgent
from .generators.a11y_report_generator import A11yReportGenerator

from advanced_browser_services.llm_factory import DEFAULT_MODEL

logger = logging.getLogger(__name__)


class AccessibilityAuditService:
    """
    Two-phase accessibility audit orchestrator.

    Phase 1: Uses Playwright directly to inject axe-core and scan
    Phase 2: Uses browser-use Agent for behavioral a11y testing
    """

    def __init__(
        self,
        output_config: Optional[OutputConfig] = None,
        model: str = DEFAULT_MODEL,
        headless: bool = False,
    ):
        self.output_config = output_config or OutputConfig()
        self.model = model
        self.headless = headless
        self.report_generator = A11yReportGenerator()

    async def run_audit(
        self,
        url: str,
        max_steps: int = 40,
        skip_behavioral: bool = False,
        step_callback: Optional[Any] = None,
        done_callback: Optional[Any] = None,
    ) -> A11yAuditSession:
        """
        Run a full accessibility audit (Phase 1 + optional Phase 2).

        Args:
            url: Target URL to audit
            max_steps: Max steps for behavioral agent
            skip_behavioral: If True, only run Phase 1 (axe scan)
            step_callback: Optional streaming callback
            done_callback: Optional completion callback

        Returns:
            A11yAuditSession with scores, violations, and report paths
        """
        session_id = f"a11y_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
        started_at = datetime.now()

        audit_session = A11yAuditSession(
            session_id=session_id,
            url=url,
            started_at=started_at,
        )

        try:
            # ── Phase 1: Automated axe-core scan (Playwright directly) ──
            logger.info("[A11yService] Phase 1: Running axe-core scan")
            axe_scan = await self._run_axe_scan(url)
            audit_session.axe_scan = axe_scan
            logger.info(
                f"[A11yService] Phase 1 complete: {len(axe_scan.violations)} violations, "
                f"{axe_scan.total_violation_nodes} affected elements"
            )

            # ── Phase 2: Behavioral testing (browser-use Agent) ──────
            behavioral_session: Optional[TestSession] = None
            if not skip_behavioral:
                logger.info("[A11yService] Phase 2: Running behavioral testing")
                axe_summary = AxeInjector.build_axe_summary(axe_scan)

                behavioral_session = await self._run_behavioral(
                    url=url,
                    axe_summary=axe_summary,
                    max_steps=max_steps,
                    step_callback=step_callback,
                    done_callback=done_callback,
                )
                audit_session.behavioral_session = behavioral_session
                logger.info(
                    f"[A11yService] Phase 2 complete: "
                    f"{behavioral_session.passed}/{behavioral_session.total_scenarios} passed"
                )

            # ── Scoring ───────────────────────────────────────────────
            audit_session.audit_score = self._compute_score(axe_scan, behavioral_session)
            audit_session.completed_at = datetime.now()

            # ── Generate reports ──────────────────────────────────────
            self._generate_reports(audit_session)

            return audit_session

        except Exception as e:
            logger.error(f"[A11yService] Audit failed: {e}")
            audit_session.completed_at = datetime.now()
            # Still try to compute partial score
            if audit_session.axe_scan:
                audit_session.audit_score = self._compute_score(
                    audit_session.axe_scan, audit_session.behavioral_session
                )
                self._generate_reports(audit_session)
            raise

    async def _run_behavioral(
        self,
        url: str,
        axe_summary: str,
        max_steps: int,
        step_callback: Optional[Any],
        done_callback: Optional[Any],
    ) -> TestSession:
        """
        Run behavioral accessibility testing.

        On Windows, browser-use internally calls asyncio.create_subprocess_exec
        to launch Chrome, which fails under uvicorn's event loop. We work around
        this by pre-launching Chrome via subprocess.Popen and passing the CDP URL
        to browser-use so it connects to the already-running browser.
        """
        chrome_process = None
        try:
            if sys.platform == "win32":
                # Pre-launch Chrome and get CDP URL
                cdp_url, chrome_process = await self._launch_chrome_for_cdp(
                    headless=self.headless
                )
                logger.info(f"[A11yService] Pre-launched Chrome at {cdp_url}")

                agent = A11yAgent(
                    model=self.model,
                    headless=self.headless,
                    output_config=self.output_config,
                    step_callback=step_callback,
                    done_callback=done_callback,
                    cdp_url=cdp_url,
                )
            else:
                agent = A11yAgent(
                    model=self.model,
                    headless=self.headless,
                    output_config=self.output_config,
                    step_callback=step_callback,
                    done_callback=done_callback,
                )

            return await agent.run_behavioral(
                url=url,
                axe_summary=axe_summary,
                max_steps=max_steps,
            )
        finally:
            if chrome_process:
                try:
                    chrome_process.terminate()
                    chrome_process.wait(timeout=5)
                except Exception:
                    try:
                        chrome_process.kill()
                    except Exception:
                        pass

    @staticmethod
    async def _launch_chrome_for_cdp(headless: bool = False) -> tuple:
        """
        Launch Chrome via subprocess.Popen (works on any event loop) and
        return (cdp_url, process).
        """
        import subprocess
        import socket
        import time
        import json as json_mod
        from urllib.request import urlopen

        # Find a free port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            port = s.getsockname()[1]

        # Find Chrome executable
        chrome_paths = [
            os.path.join(os.environ.get("PROGRAMFILES", ""), "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "Application", "chrome.exe"),
        ]

        chrome_exe = None
        for p in chrome_paths:
            if os.path.exists(p):
                chrome_exe = p
                break

        if not chrome_exe:
            # Try Chromium from Playwright
            pw_browsers = os.path.join(
                os.environ.get("LOCALAPPDATA", ""), "ms-playwright"
            )
            if os.path.exists(pw_browsers):
                for d in sorted(os.listdir(pw_browsers), reverse=True):
                    if d.startswith("chromium"):
                        candidate = os.path.join(pw_browsers, d, "chrome-win", "chrome.exe")
                        if os.path.exists(candidate):
                            chrome_exe = candidate
                            break

        if not chrome_exe:
            raise FileNotFoundError("Could not find Chrome or Chromium executable")

        args = [
            chrome_exe,
            f"--remote-debugging-port={port}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-networking",
            "--disable-default-apps",
            "--disable-extensions",
            "--disable-sync",
            "--disable-translate",
            f"--user-data-dir={os.path.join(os.environ.get('TEMP', '/tmp'), f'chrome_a11y_{port}')}",
        ]
        if headless:
            args.append("--headless=new")

        logger.info(f"[A11yService] Launching Chrome on port {port}")
        process = subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Wait for Chrome to be ready
        cdp_url = None
        for _ in range(30):  # up to 15 seconds
            time.sleep(0.5)
            try:
                resp = urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2)
                data = json_mod.loads(resp.read())
                cdp_url = data.get("webSocketDebuggerUrl")
                if cdp_url:
                    break
            except Exception:
                continue

        if not cdp_url:
            process.terminate()
            raise RuntimeError(f"Chrome did not start on port {port}")

        return cdp_url, process

    async def _run_axe_scan(self, url: str) -> AxeScanResult:
        """
        Run axe-core scan using Playwright sync API in a thread.

        asyncio.create_subprocess_exec doesn't work with uvicorn's event loop
        on Windows, so we run Playwright in a separate thread with the sync API.
        """
        def _run_sync():
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                try:
                    page = browser.new_page()
                    return self._run_axe_sync(page, url)
                finally:
                    browser.close()

        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, _run_sync)

    @staticmethod
    def _run_axe_sync(page, url: str) -> AxeScanResult:
        """Synchronous version of axe scan for thread execution."""
        import json as json_mod
        from .core.axe_injector import AXE_CDN_URL, AXE_RUN_OPTIONS
        from .models.a11y_models import AxeViolation, AxeViolationNode, ImpactLevel

        logger.info(f"[AxeInjector] Navigating to {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=15000)

        logger.info("[AxeInjector] Injecting axe-core JS")
        page.add_script_tag(url=AXE_CDN_URL)
        page.wait_for_function("typeof window.axe !== 'undefined'", timeout=10000)

        logger.info("[AxeInjector] Running axe.run()")
        raw_result = page.evaluate(f"""
            async () => {{
                const result = await axe.run(document, {AXE_RUN_OPTIONS});
                return JSON.stringify({{
                    violations: result.violations,
                    passes_count: result.passes.length,
                    incomplete_count: result.incomplete.length,
                }});
            }}
        """)

        result_data = json_mod.loads(raw_result)
        logger.info(
            f"[AxeInjector] Scan complete: {len(result_data['violations'])} violations, "
            f"{result_data['passes_count']} passes, {result_data['incomplete_count']} incomplete"
        )

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

    # ── Scoring ───────────────────────────────────────────────────

    # Per-node deduction weights by impact
    IMPACT_DEDUCTIONS = {
        ImpactLevel.CRITICAL: 15,
        ImpactLevel.SERIOUS: 10,
        ImpactLevel.MODERATE: 5,
        ImpactLevel.MINOR: 2,
    }

    BEHAVIORAL_FAIL_DEDUCTION = 8

    # Category mapping: rule_id substring → category name
    CATEGORY_MAP = {
        "contrast": "Color Contrast",
        "color": "Color Contrast",
        "keyboard": "Keyboard Navigation",
        "focus": "Keyboard Navigation",
        "tabindex": "Keyboard Navigation",
        "aria": "ARIA",
        "role": "ARIA",
        "label": "Forms",
        "input": "Forms",
        "select": "Forms",
        "form": "Forms",
        "heading": "Semantics",
        "landmark": "Semantics",
        "list": "Semantics",
        "table": "Semantics",
        "region": "Semantics",
        "img": "Media",
        "video": "Media",
        "audio": "Media",
        "alt": "Media",
        "object": "Media",
    }

    ALL_CATEGORIES = [
        "Color Contrast",
        "Keyboard Navigation",
        "ARIA",
        "Forms",
        "Semantics",
        "Media",
    ]

    def _compute_score(
        self,
        axe_scan: AxeScanResult,
        behavioral_session: Optional[TestSession],
    ) -> A11yAuditScore:
        """Compute weighted 0-100 accessibility score."""

        # ── Per-category issue tracking ─────────────────────────
        category_issues: dict[str, int] = {c: 0 for c in self.ALL_CATEGORIES}
        category_deductions: dict[str, float] = {c: 0.0 for c in self.ALL_CATEGORIES}

        total_deductions = 0.0

        # Axe violations
        for v in axe_scan.violations:
            cat = self._categorize_rule(v.rule_id)
            node_count = len(v.nodes)
            deduction = self.IMPACT_DEDUCTIONS.get(v.impact, 2) * node_count
            total_deductions += deduction
            category_issues[cat] += node_count
            category_deductions[cat] += deduction

        # Behavioral failures
        total_violations = axe_scan.total_violation_nodes
        if behavioral_session:
            failed_count = behavioral_session.failed or 0
            total_deductions += failed_count * self.BEHAVIORAL_FAIL_DEDUCTION
            total_violations += failed_count
            # Distribute behavioral failures into Keyboard Navigation bucket
            category_issues["Keyboard Navigation"] += failed_count
            category_deductions["Keyboard Navigation"] += failed_count * self.BEHAVIORAL_FAIL_DEDUCTION

        overall = max(0, int(100 - total_deductions))

        # Category scores (independent)
        categories = []
        for cat_name in self.ALL_CATEGORIES:
            cat_score = max(0, int(100 - category_deductions[cat_name]))
            categories.append(A11yCategoryScore(
                category=cat_name,
                score=cat_score,
                issues_found=category_issues[cat_name],
            ))

        grade = self._score_to_grade(overall)

        return A11yAuditScore(
            overall_score=overall,
            grade=grade,
            categories=categories,
            total_violations=total_violations,
        )

    def _categorize_rule(self, rule_id: str) -> str:
        rule_lower = rule_id.lower()
        for substring, category in self.CATEGORY_MAP.items():
            if substring in rule_lower:
                return category
        return "Semantics"  # default bucket

    @staticmethod
    def _score_to_grade(score: int) -> str:
        if score >= 90:
            return "A"
        if score >= 80:
            return "B"
        if score >= 70:
            return "C"
        if score >= 60:
            return "D"
        return "F"

    # ── Report generation ─────────────────────────────────────────

    def _generate_reports(self, session: A11yAuditSession):
        """Generate HTML and JSON reports and save to disk."""
        output_dir = self.output_config.output_directory
        reports_dir = os.path.join(output_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)

        session.output_directory = output_dir

        # HTML report
        html_content = self.report_generator.generate_html(session)
        html_path = os.path.join(reports_dir, "a11y_report.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        session.html_report_path = html_path
        logger.info(f"[A11yService] HTML report: {html_path}")

        # JSON report
        json_content = self.report_generator.generate_json(session)
        json_path = os.path.join(reports_dir, "a11y_report.json")
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json_content)
        session.json_report_path = json_path
        logger.info(f"[A11yService] JSON report: {json_path}")
