"""
Streaming Agent Runner

Runs browser-use agents with real-time log streaming via SSE.
"""

import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from browser_use import Agent

from ui_testing_agent import UITestingService, OutputConfig
from .base_service import get_gemini_llm, BrowserConfig, DEFAULT_MODEL
from .streaming import (
    StreamingSession,
    create_step_callback,
    create_done_callback,
    create_session,
    remove_session,
    LogLevel,
    EventType,
)


@dataclass
class StreamingTaskConfig:
    """Configuration for a streaming task."""
    task: str
    max_steps: int = 30
    max_actions_per_step: int = 3
    use_vision: bool = True
    headless: bool = False


class StreamingAgentRunner:
    """
    Runs browser-use agents with streaming log output.

    Usage:
        runner = StreamingAgentRunner()
        session = runner.create_session()

        # Start task (non-blocking)
        asyncio.create_task(runner.run_task(session.session_id, config))

        # Stream events
        async for event in session.events():
            yield event  # Send via SSE
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
    ):
        self.model = model
        self.temperature = temperature
        self._sessions: Dict[str, StreamingSession] = {}

    def create_session(self) -> StreamingSession:
        """Create a new streaming session."""
        session = create_session()
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[StreamingSession]:
        """Get an active session."""
        return self._sessions.get(session_id)

    async def run_basic_task(
        self,
        session: StreamingSession,
        task: str,
        max_steps: int = 30,
        headless: bool = False,
    ) -> Dict[str, Any]:
        """
        Run a basic browser automation task with streaming.

        Args:
            session: The streaming session to emit events to
            task: Natural language task description
            max_steps: Maximum number of steps
            headless: Run browser without UI

        Returns:
            Final result dictionary
        """
        session.emit_info(f"Initializing browser automation...")
        session.emit_info(f"Task: {task}")

        browser = None
        try:
            # Initialize LLM
            llm = get_gemini_llm(model=self.model, temperature=self.temperature)
            session.emit_info(f"Using model: {self.model}")

            # Create browser config
            browser_config = BrowserConfig(headless=headless)
            browser = browser_config.create_browser()
            session.emit_info("Browser initialized")

            # Create agent with streaming callbacks
            agent = Agent(
                task=task,
                llm=llm,
                browser=browser,
                max_actions_per_step=3,
                register_new_step_callback=create_step_callback(session),
                register_done_callback=create_done_callback(session),
            )

            session.emit_info("Agent created, starting execution...")

            # Run agent
            history = await agent.run(max_steps=max_steps)

            # Extract results
            steps = []
            for step in history.history:
                action_desc = "Processing"
                if step.model_output and step.model_output.action:
                    action_names = [type(a).__name__ for a in step.model_output.action]
                    action_desc = ", ".join(action_names)
                steps.append({
                    "action": action_desc,
                    "status": "done"
                })

            final_result = history.final_result() or "Task completed"

            return {
                "success": True,
                "summary": final_result,
                "steps": steps,
                "total_steps": len(steps),
            }

        except Exception as e:
            session.emit_error(f"Task failed: {str(e)}")
            return {
                "success": False,
                "summary": f"Error: {str(e)}",
                "steps": [],
                "error": str(e),
            }

        finally:
            if browser:
                try:
                    await browser.close()
                    session.emit_info("Browser closed")
                except:
                    pass

    async def run_data_extraction(
        self,
        session: StreamingSession,
        url: str,
        data_schema: Dict[str, str],
        max_items: Optional[int] = None,
        max_steps: int = 40,
        headless: bool = False,
    ) -> Dict[str, Any]:
        """
        Run data extraction task with streaming.
        """
        session.emit_info(f"Starting data extraction from {url}")
        session.emit_info(f"Schema: {list(data_schema.keys())}")

        # Build extraction task
        schema_desc = ", ".join([f"{k}: {v}" for k, v in data_schema.items()])
        task = f"""
        Go to {url} and extract the following data:
        {schema_desc}

        Extract up to {max_items or 'all available'} items.
        Return the data in a structured format.
        """

        return await self.run_basic_task(session, task, max_steps, headless)

    async def run_research(
        self,
        session: StreamingSession,
        topic: str,
        depth: str = "moderate",
        max_sources: int = 5,
        max_steps: int = 50,
        headless: bool = False,
    ) -> Dict[str, Any]:
        """
        Run research task with streaming.
        """
        session.emit_info(f"Starting research on: {topic}")
        session.emit_info(f"Depth: {depth}, Max sources: {max_sources}")

        depth_instructions = {
            "shallow": "Do a quick search and summarize the top results.",
            "moderate": "Search multiple sources and provide a balanced overview.",
            "deep": "Thoroughly research from multiple authoritative sources, cross-reference information.",
        }

        task = f"""
        Research the topic: {topic}

        Instructions:
        - {depth_instructions.get(depth, depth_instructions['moderate'])}
        - Consult up to {max_sources} different sources
        - Take note of source URLs for citations
        - Synthesize findings into a comprehensive summary
        """

        return await self.run_basic_task(session, task, max_steps, headless)

    async def run_product_comparison(
        self,
        session: StreamingSession,
        products: List[str],
        aspects: List[str],
        max_steps: int = 60,
        headless: bool = False,
    ) -> Dict[str, Any]:
        """
        Run product comparison with streaming.
        """
        session.emit_info(f"Comparing products: {', '.join(products)}")
        session.emit_info(f"Aspects: {', '.join(aspects)}")

        task = f"""
        Compare the following products: {', '.join(products)}

        For each product, find and compare:
        {', '.join(aspects)}

        Create a comparison table and provide a recommendation.
        """

        return await self.run_basic_task(session, task, max_steps, headless)

    async def run_page_comparison(
        self,
        session: StreamingSession,
        urls: List[str],
        comparison_criteria: str,
        max_steps: int = 30,
        headless: bool = False,
    ) -> Dict[str, Any]:
        """
        Run page comparison with streaming.
        """
        session.emit_info(f"Comparing {len(urls)} pages")
        session.emit_info(f"Criteria: {comparison_criteria}")

        task = f"""
        Compare the following web pages:
        {chr(10).join(f'- {url}' for url in urls)}

        Focus on comparing: {comparison_criteria}

        Open each page (you can use multiple tabs) and create a detailed comparison.
        """

        return await self.run_basic_task(session, task, max_steps, headless)

    async def run_ui_testing_agent_task(
        self,
        session: StreamingSession,
        task: str,
        max_steps: int = 30,
        headless: bool = False,
    ) -> Dict[str, Any]:
        """
        Run the full UI Testing Agent with streaming.
        
        This uses the UITestingService which generates artifacts (tests, reports)
        in addition to performing the automation.
        """
        session.emit_info(f"Initializing UI Testing Agent...")
        session.emit_info(f"Task: {task}")
        
        # Setup output directory for this session
        output_dir = f"./test_outputs/{session.session_id}"
        
        config = OutputConfig(
            output_directory=output_dir,
            generate_playwright_code=True,
            generate_test_cases=True,
            generate_html_report=True,
            generate_json_report=True,
            save_screenshots=True,
            save_raw_history=True,
        )
        
        service = UITestingService(
            output_config=config,
            model=self.model,
            headless=headless,
        )
        
        try:
            # Create callbacks that emit to the stream
            step_callback = create_step_callback(session)
            done_callback = create_done_callback(session)
            
            session.emit_info("Starting exploration and testing...")
            
            # Run the service with callbacks
            result_session = await service.explore_and_test(
                task=task,
                url="about:blank", # Allow agent to navigate itself based on task, or could be extracted
                max_steps=max_steps,
                step_callback=step_callback,
                done_callback=done_callback
            )
            
            # Notify about artifacts
            session.emit_info(f"Artifacts generated in: {result_session.output_directory}")
            if result_session.html_report_path:
                session.emit_success(f"Report available: {result_session.html_report_path}")
            
            return {
                "success": True,
                "summary": "UI Testing Agent finished successfully",
                "output_directory": result_session.output_directory
            }
            
        except Exception as e:
            session.emit_error(f"UI Testing Agent failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def cleanup_session(self, session_id: str):
        """Clean up a completed session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
        remove_session(session_id)


# Global runner instance
_streaming_runner: Optional[StreamingAgentRunner] = None


def get_streaming_runner() -> StreamingAgentRunner:
    """Get or create the global streaming runner."""
    global _streaming_runner
    if _streaming_runner is None:
        _streaming_runner = StreamingAgentRunner()
    return _streaming_runner
