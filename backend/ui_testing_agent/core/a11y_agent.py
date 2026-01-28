"""
Accessibility Agent - Behavioral accessibility testing agent.

Mirrors ExplorerAgent with accessibility-focused system prompt.
Optionally reuses a browser session from Phase 1 (axe scan).
"""

import os
from datetime import datetime
from typing import Optional, Any
from uuid import uuid4

from dotenv import load_dotenv

load_dotenv()

if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

from browser_use import Agent
from browser_use.agent.views import AgentHistoryList

from ..models.output_config import OutputConfig
from .browser_factory import BrowserFactory, BrowserResult
from ..models.processed_step import ProcessedStep
from ..models.test_session import TestSession
from .step_processor import StepProcessor
from ..prompts.a11y_auditor_prompt import build_a11y_system_prompt
from .browser_use_replay import BrowserUseRecorder, RecordedSession

from advanced_browser_services.llm_factory import get_llm, DEFAULT_MODEL


class A11yAgent:
    """
    Wraps browser-use Agent with accessibility auditor system prompt and recording.

    Mirrors ExplorerAgent with 3 differences:
    1. Uses build_a11y_system_prompt() instead of build_qa_system_prompt()
    2. Accepts optional browser_result param to share browser from Phase 1
    3. Only closes browser if it created it (_owns_browser flag)
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.5,
        headless: bool = False,
        output_config: Optional[OutputConfig] = None,
        step_callback: Optional[Any] = None,
        done_callback: Optional[Any] = None,
        browser_result: Optional[BrowserResult] = None,
        cdp_url: Optional[str] = None,
    ):
        self.model = model
        self.temperature = temperature
        self.headless = headless
        self.output_config = output_config or OutputConfig()
        self.step_callback = step_callback
        self.done_callback = done_callback
        self.cdp_url = cdp_url

        self.llm = get_llm(model=model, temperature=temperature)
        self._browser_result: Optional[BrowserResult] = browser_result
        self._owns_browser: bool = browser_result is None
        self._recorder: Optional[BrowserUseRecorder] = None
        self._recorded_session: Optional[RecordedSession] = None

        self.step_processor = StepProcessor()
        self.recorded_steps: list[ProcessedStep] = []

        self.session_id: Optional[str] = None
        self.current_agent: Optional[Agent] = None

    async def run_behavioral(
        self,
        url: str,
        axe_summary: str,
        max_steps: int = 40,
        max_actions_per_step: int = 3,
    ) -> TestSession:
        """
        Run behavioral accessibility testing on the given URL.

        Args:
            url: Target URL to test
            axe_summary: Summary of Phase 1 axe scan results
            max_steps: Maximum agent steps
            max_actions_per_step: Maximum actions per LLM turn

        Returns:
            TestSession with behavioral test results
        """
        self.session_id = f"a11y_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
        self.recorded_steps = []
        self._recorded_session = None
        started_at = datetime.now()
        task = f"Perform behavioral accessibility audit of {url}"

        # Create browser if not provided
        if self._browser_result is None:
            if self.cdp_url:
                # Connect to pre-launched Chrome via CDP (avoids subprocess issues on Windows)
                from browser_use.browser.session import BrowserSession
                from browser_use.browser.profile import BrowserProfile
                browser_profile = BrowserProfile(
                    cdp_url=self.cdp_url,
                    headless=self.headless,
                )
                browser_session = BrowserSession(browser_profile=browser_profile)
                self._browser_result = BrowserResult(
                    browser=browser_session,
                    browser_type="browser_session",
                    strategy_used="cdp_url",
                )
            else:
                self._browser_result = await BrowserFactory.create(headless=self.headless)
            self._owns_browser = True

        # Attach recorder
        if self._browser_result.browser_type in ("browser_session", "browser") and self._browser_result.browser:
            self._recorder = BrowserUseRecorder(
                session_id=self.session_id,
                task=task,
                initial_url=url,
            )
            await self._recorder.attach(self._browser_result.browser)

        # Build accessibility-focused system prompt
        a11y_prompt = build_a11y_system_prompt(url=url, axe_summary=axe_summary)

        # Build agent kwargs
        agent_kwargs = {
            "task": f"Navigate to {url} and perform a behavioral accessibility audit",
            "llm": self.llm,
            "extend_system_message": a11y_prompt,
            "register_new_step_callback": self._on_step,
            "register_done_callback": self._on_complete,
            "generate_gif": self.output_config.capture_video,
            "use_vision": True,
            "max_actions_per_step": max_actions_per_step,
        }

        agent_kwargs.update(BrowserFactory.get_agent_kwargs(self._browser_result))

        agent = Agent(**agent_kwargs)
        self.current_agent = agent

        try:
            history: AgentHistoryList = await agent.run(max_steps=max_steps)

            if self._recorder and self._recorder._is_recording:
                self._recorded_session = self._recorder.detach()

            self._process_all_steps(history)

            completed_at = datetime.now()
            scenarios = self.step_processor.group_into_scenarios(self.recorded_steps)

            session = TestSession(
                session_id=self.session_id,
                task=task,
                url=url,
                started_at=started_at,
                completed_at=completed_at,
                raw_history=history.model_dump() if hasattr(history, 'model_dump') else None,
                steps=self.recorded_steps,
                scenarios=scenarios,
            )
            session.replay_recording = self._recorded_session
            session.calculate_statistics()
            return session

        except Exception:
            completed_at = datetime.now()
            scenarios = self.step_processor.group_into_scenarios(self.recorded_steps)

            session = TestSession(
                session_id=self.session_id,
                task=task,
                url=url,
                started_at=started_at,
                completed_at=completed_at,
                steps=self.recorded_steps,
                scenarios=scenarios,
            )
            session.calculate_statistics()

            if scenarios:
                scenarios[-1].passed = False
                scenarios[-1].failure_reason = "Agent error during behavioral testing"

            raise

        finally:
            await self.close()

    async def _on_step(self, state, output, step_num: int):
        if self.step_callback:
            try:
                await self.step_callback(state, output, step_num)
            except Exception:
                pass

    async def _on_complete(self, history: AgentHistoryList):
        self._process_all_steps(history)
        if self.done_callback:
            try:
                await self.done_callback(history)
            except Exception:
                pass

    def _process_all_steps(self, history: AgentHistoryList):
        if not history or not history.history:
            return
        for i, step in enumerate(history.history):
            if i >= len(self.recorded_steps):
                processed = self.step_processor.process_step(step, i)
                self.recorded_steps.append(processed)

    async def close(self):
        """Close browser only if this agent created it."""
        if self._owns_browser and self._browser_result:
            await BrowserFactory.cleanup(self._browser_result)
            self._browser_result = None
