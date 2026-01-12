"""
Explorer Agent - Main agent for exploratory UI testing.

Updated for browser-use 0.11.x API.
"""

import asyncio
import os
from datetime import datetime
from typing import Optional, Any
from uuid import uuid4

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Handle API key naming (GEMINI_API_KEY -> GOOGLE_API_KEY)
if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

from browser_use import Agent
from browser_use.agent.views import AgentHistoryList

from ..models.output_config import OutputConfig
from .browser_factory import BrowserFactory, BrowserResult
from ..models.processed_step import ProcessedStep
from ..models.test_session import TestSession
from .step_processor import StepProcessor
from ..prompts.qa_engineer_prompt import build_qa_system_prompt

# Import unified LLM factory (single source of truth - no circular imports)
from advanced_browser_services.llm_factory import get_llm, DEFAULT_MODEL


class ExplorerAgent:
    """
    Wraps browser-use Agent with QA-focused system prompt and recording.

    This agent:
    1. Injects a QA engineer mindset via system prompt
    2. Records all steps during execution
    3. Processes history into structured test session
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.5,
        headless: bool = False,
        output_config: Optional[OutputConfig] = None,
        step_callback: Optional[Any] = None,
        done_callback: Optional[Any] = None,
    ):
        """
        Initialize the explorer agent.

        Args:
            model: LLM model to use (default: gemini-2.0-flash)
            temperature: LLM temperature
            headless: Run browser without visible window
            output_config: Configuration for output generation
            step_callback: Optional async callback for step updates
            done_callback: Optional async callback for completion
        """
        self.model = model
        self.temperature = temperature
        self.headless = headless
        self.output_config = output_config or OutputConfig()
        self.step_callback = step_callback
        self.done_callback = done_callback

        self.llm = get_llm(model=model, temperature=temperature)
        self._browser_result: Optional[BrowserResult] = None

        # Processing
        self.step_processor = StepProcessor()
        self.recorded_steps: list[ProcessedStep] = []

        # Session tracking
        self.session_id: Optional[str] = None
        self.current_agent: Optional[Agent] = None

    async def explore_and_test(
        self,
        task: str,
        url: str,
        max_steps: int = 50,
        max_actions_per_step: int = 3,
    ) -> TestSession:
        """
        Main entry point: explore and test a URL based on a task.

        This method:
        1. Creates a browser-use Agent with QA-focused system prompt
        2. Executes the exploration/testing
        3. Processes the AgentHistoryList into a TestSession
        4. Returns the session (artifacts generated separately by generators)

        Args:
            task: High-level testing task description
            url: Target URL to test
            max_steps: Maximum agent steps
            max_actions_per_step: Maximum actions per LLM turn

        Returns:
            TestSession with all processed data
        """
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
        self.recorded_steps = []
        started_at = datetime.now()

        # Create browser using the factory (single source of truth)
        self._browser_result = await BrowserFactory.create(headless=self.headless)

        # Build QA-focused system prompt
        qa_prompt = build_qa_system_prompt(task=task, url=url)

        # Build agent kwargs with browser based on type
        agent_kwargs = {
            "task": f"Navigate to {url} and {task}",
            "llm": self.llm,
            "extend_system_message": qa_prompt,
            "register_new_step_callback": self._on_step,
            "register_done_callback": self._on_complete,
            "generate_gif": self.output_config.capture_video,
            "use_vision": True,
            "max_actions_per_step": max_actions_per_step,
        }

        # Add browser kwargs based on type from factory
        agent_kwargs.update(BrowserFactory.get_agent_kwargs(self._browser_result))

        # Create the agent with browser-use 0.11.x API
        agent = Agent(**agent_kwargs)
        self.current_agent = agent

        try:
            # Execute exploration and testing
            history: AgentHistoryList = await agent.run(max_steps=max_steps)

            # Process remaining steps (in case callback missed any)
            self._process_all_steps(history)

            completed_at = datetime.now()

            # Group steps into scenarios
            scenarios = self.step_processor.group_into_scenarios(self.recorded_steps)

            # Build session
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

            # Calculate statistics
            session.calculate_statistics()

            return session

        except Exception as e:
            # Return partial session on error
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

            # Add error to last scenario if possible
            if scenarios:
                scenarios[-1].passed = False
                scenarios[-1].failure_reason = str(e)

            raise

        finally:
            # Close browser session
            await self.close()

    async def _on_step(self, state, output, step_num: int):
        """
        Callback: Called after each agent step.

        browser-use 0.11.x signature: (BrowserStateSummary, AgentOutput, int)
        """
        # Invoke external callback if provided
        if self.step_callback:
            try:
                await self.step_callback(state, output, step_num)
            except Exception:
                pass  # Ignore callback errors to not break execution
        
        pass

    async def _on_complete(self, history: AgentHistoryList):
        """
        Callback: Called when agent completes.

        Ensures all steps are processed.
        """
        self._process_all_steps(history)

        # Invoke external callback if provided
        if self.done_callback:
            try:
                await self.done_callback(history)
            except Exception:
                pass

    def _process_all_steps(self, history: AgentHistoryList):
        """Process all steps from history, filling in any gaps."""
        if not history or not history.history:
            return

        for i, step in enumerate(history.history):
            if i >= len(self.recorded_steps):
                processed = self.step_processor.process_step(step, i)
                self.recorded_steps.append(processed)

    async def close(self):
        """Close the browser and cleanup resources."""
        if self._browser_result:
            await BrowserFactory.cleanup(self._browser_result)
            self._browser_result = None
