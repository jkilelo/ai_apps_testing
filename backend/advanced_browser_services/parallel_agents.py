"""
Parallel Agents Service

Run multiple browser agents simultaneously for parallel task execution.
Each agent operates in its own browser context.
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from browser_use import Agent, BrowserSession

from .base_service import get_gemini_llm, BrowserConfig, DEFAULT_MODEL


@dataclass
class AgentTask:
    """Represents a task to be executed by an agent."""
    task_id: str
    description: str
    max_steps: int = 25


@dataclass
class AgentResult:
    """Result from an agent execution."""
    task_id: str
    success: bool
    summary: str
    steps: List[Dict[str, Any]]
    error: Optional[str] = None


class ParallelAgentRunner:
    """
    Run multiple browser agents in parallel.

    Use cases:
    - Scrape data from multiple websites simultaneously
    - Perform the same task on different sites
    - Research multiple topics at once
    - Speed up batch operations
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        browser_config: Optional[BrowserConfig] = None,
        max_concurrent_agents: int = 3,
    ):
        """
        Initialize the parallel agent runner.

        Args:
            model: Gemini model to use
            temperature: LLM temperature setting
            browser_config: Browser configuration options
            max_concurrent_agents: Maximum number of agents running simultaneously
        """
        self.model = model
        self.temperature = temperature
        self.browser_config = browser_config or BrowserConfig()
        self.max_concurrent_agents = max_concurrent_agents

    async def _run_single_agent(self, task: AgentTask) -> AgentResult:
        """
        Run a single agent for a task.

        Args:
            task: The task to execute

        Returns:
            AgentResult with execution details
        """
        browser = None
        try:
            llm = get_gemini_llm(model=self.model, temperature=self.temperature)
            browser = self.browser_config.create_browser_session()

            agent = Agent(
                task=task.description,
                llm=llm,
                browser=browser,
            )

            history = await agent.run(max_steps=task.max_steps)

            steps = []
            for step in history.history:
                action_desc = "Processing..."
                if step.model_output and step.model_output.action:
                    action_names = [type(a).__name__ for a in step.model_output.action]
                    action_desc = ", ".join(action_names)
                steps.append({"action": action_desc, "status": "done"})

            final_result = history.final_result() or "Task completed successfully."

            return AgentResult(
                task_id=task.task_id,
                success=True,
                summary=final_result,
                steps=steps,
            )

        except Exception as e:
            return AgentResult(
                task_id=task.task_id,
                success=False,
                summary=f"Task failed: {str(e)}",
                steps=[],
                error=str(e),
            )
        finally:
            if browser:
                await browser.close()

    async def run_parallel(self, tasks: List[AgentTask]) -> List[AgentResult]:
        """
        Run multiple agent tasks in parallel.

        Args:
            tasks: List of tasks to execute

        Returns:
            List of AgentResult for each task
        """
        semaphore = asyncio.Semaphore(self.max_concurrent_agents)

        async def run_with_semaphore(task: AgentTask) -> AgentResult:
            async with semaphore:
                return await self._run_single_agent(task)

        results = await asyncio.gather(
            *[run_with_semaphore(task) for task in tasks],
            return_exceptions=False,
        )

        return list(results)

    async def run_same_task_on_sites(
        self,
        task_template: str,
        urls: List[str],
        max_steps: int = 25,
    ) -> List[AgentResult]:
        """
        Run the same task on multiple websites in parallel.

        Args:
            task_template: Task description template (use {url} for URL placeholder)
            urls: List of URLs to execute the task on
            max_steps: Maximum steps per agent

        Returns:
            List of results from each site
        """
        tasks = [
            AgentTask(
                task_id=f"site_{i}",
                description=task_template.replace("{url}", url),
                max_steps=max_steps,
            )
            for i, url in enumerate(urls)
        ]

        return await self.run_parallel(tasks)

    async def batch_search(
        self,
        queries: List[str],
        search_engine: str = "google",
        max_steps: int = 15,
    ) -> List[AgentResult]:
        """
        Perform multiple search queries in parallel.

        Args:
            queries: List of search queries
            search_engine: Search engine to use
            max_steps: Maximum steps per search

        Returns:
            List of search results
        """
        tasks = [
            AgentTask(
                task_id=f"search_{i}",
                description=f"Go to {search_engine}.com and search for: {query}. "
                           f"Return the top 5 results with titles and URLs.",
                max_steps=max_steps,
            )
            for i, query in enumerate(queries)
        ]

        return await self.run_parallel(tasks)
