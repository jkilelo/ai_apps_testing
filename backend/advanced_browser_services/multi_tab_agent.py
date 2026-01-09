"""
Multi-Tab Agent Service

Provides browser automation with multi-tab support for complex workflows
that require working across multiple browser tabs simultaneously.
"""

import asyncio
from typing import Optional, List, Dict, Any
from browser_use import Agent, BrowserSession
from browser_use.agent.views import AgentHistoryList

from .base_service import BaseAgentService, BrowserConfig, DEFAULT_MODEL


class MultiTabAgent(BaseAgentService):
    """
    Agent that can work across multiple browser tabs.

    Use cases:
    - Compare products across different websites
    - Research topics from multiple sources
    - Fill forms that require data from other pages
    - Monitor multiple dashboards
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        browser_config: Optional[BrowserConfig] = None,
        max_tabs: int = 5,
    ):
        """
        Initialize the multi-tab agent.

        Args:
            model: Gemini model to use
            temperature: LLM temperature setting
            browser_config: Browser configuration options
            max_tabs: Maximum number of tabs to allow
        """
        super().__init__(model, temperature, browser_config)
        self.max_tabs = max_tabs

    async def run(
        self,
        task: str,
        initial_urls: Optional[List[str]] = None,
        max_steps: int = 50,
    ) -> Dict[str, Any]:
        """
        Execute a multi-tab browsing task.

        Args:
            task: The task description for the agent
            initial_urls: Optional list of URLs to open in tabs before starting
            max_steps: Maximum number of steps the agent can take

        Returns:
            Dictionary containing steps taken and final result
        """
        browser = await self._ensure_browser()

        # Build enhanced task with multi-tab context
        enhanced_task = f"""
        You have access to multiple browser tabs. You can:
        - Open new tabs when needed
        - Switch between tabs to gather information
        - Compare content across tabs

        Task: {task}

        Note: You can have up to {self.max_tabs} tabs open at once.
        """

        agent = Agent(
            task=enhanced_task,
            llm=self.llm,
            browser=browser,
            max_actions_per_step=5,
        )

        try:
            history: AgentHistoryList = await agent.run(max_steps=max_steps)

            steps = []
            for step in history.history:
                action_desc = "Processing..."
                if step.model_output and step.model_output.action:
                    action_names = [type(a).__name__ for a in step.model_output.action]
                    action_desc = ", ".join(action_names)

                steps.append({
                    "action": action_desc,
                    "status": "done"
                })

            final_result = history.final_result() or "Task completed successfully."

            return {
                "steps": steps,
                "summary": final_result,
                "success": True,
            }
        except Exception as e:
            return {
                "steps": [],
                "summary": str(e),
                "success": False,
                "error": str(e),
            }
        finally:
            await self.close()

    async def compare_pages(
        self,
        urls: List[str],
        comparison_criteria: str,
        max_steps: int = 30,
    ) -> Dict[str, Any]:
        """
        Compare content across multiple web pages.

        Args:
            urls: List of URLs to compare
            comparison_criteria: What to compare (e.g., "prices", "features", "reviews")
            max_steps: Maximum steps for the agent

        Returns:
            Comparison results
        """
        if len(urls) > self.max_tabs:
            raise ValueError(f"Cannot compare more than {self.max_tabs} URLs at once")

        task = f"""
        Compare the following URLs based on: {comparison_criteria}

        URLs to compare:
        {chr(10).join(f"- {url}" for url in urls)}

        Open each URL in a separate tab, analyze the content, and provide
        a detailed comparison based on the specified criteria.
        """

        return await self.run(task=task, initial_urls=urls, max_steps=max_steps)
