"""
Unified Service Runner

Provides a simplified API for running various browser automation tasks
using the advanced browser services (non-redundant with browser-use).
"""

import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from .base_service import BrowserConfig, DEFAULT_MODEL
from .multi_tab_agent import MultiTabAgent
from .parallel_agents import ParallelAgentRunner, AgentTask
from .data_extraction_agent import DataExtractionAgent
from .research_agent import ResearchAgent


@dataclass
class TaskResult:
    """Unified result structure for all tasks."""
    success: bool
    task_type: str
    summary: str
    data: Dict[str, Any]
    steps: List[Dict[str, str]]
    error: Optional[str] = None


class AdvancedBrowserService:
    """
    Unified interface for advanced browser automation capabilities.

    This class provides a simplified API for browser automation tasks
    that ADD VALUE beyond browser-use's native capabilities:
    - Multi-tab orchestration
    - Parallel agent execution
    - Structured data extraction
    - Research with source tracking

    For basic tasks (forms, screenshots, sessions), use browser-use directly.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        headless: bool = False,
    ):
        """
        Initialize the advanced browser service.

        Args:
            model: Gemini model to use (default: gemini-3-flash-preview)
            temperature: LLM temperature setting
            headless: Run browser without visible window
        """
        self.model = model
        self.temperature = temperature
        self.browser_config = BrowserConfig(headless=headless)

    # ============== Basic Automation ==============

    async def run_task(
        self,
        task: str,
        max_steps: int = 30,
    ) -> TaskResult:
        """
        Run a basic browser automation task with multi-tab support.

        Args:
            task: Natural language description of the task
            max_steps: Maximum number of steps

        Returns:
            TaskResult with execution details
        """
        agent = MultiTabAgent(
            model=self.model,
            temperature=self.temperature,
            browser_config=self.browser_config,
        )

        result = await agent.run(task=task, max_steps=max_steps)

        return TaskResult(
            success=result.get("success", False),
            task_type="basic_task",
            summary=result.get("summary", ""),
            data=result,
            steps=result.get("steps", []),
            error=result.get("error"),
        )

    # ============== Data Extraction ==============

    async def extract_data(
        self,
        url: str,
        data_schema: Dict[str, str],
        max_items: Optional[int] = None,
        max_steps: int = 40,
    ) -> TaskResult:
        """
        Extract structured data from a web page.

        Args:
            url: URL to extract data from
            data_schema: Dictionary describing the data structure
                        e.g., {"name": "Product name", "price": "Price in USD"}
            max_items: Maximum number of items to extract
            max_steps: Maximum agent steps

        Returns:
            TaskResult with extracted data
        """
        agent = DataExtractionAgent(
            model=self.model,
            temperature=0.3,  # Lower for consistent extraction
            browser_config=self.browser_config,
        )

        result = await agent.extract(
            url=url,
            data_schema=data_schema,
            max_items=max_items,
            max_steps=max_steps,
        )

        return TaskResult(
            success=result.get("success", False),
            task_type="data_extraction",
            summary=result.get("summary", ""),
            data=result,
            steps=result.get("steps", []),
            error=result.get("error"),
        )

    # ============== Research ==============

    async def research_topic(
        self,
        topic: str,
        depth: str = "moderate",
        max_sources: int = 5,
        max_steps: int = 50,
    ) -> TaskResult:
        """
        Research a topic and gather information from multiple sources.

        Args:
            topic: Topic to research
            depth: "shallow", "moderate", or "deep"
            max_sources: Maximum sources to consult
            max_steps: Maximum agent steps

        Returns:
            TaskResult with research findings
        """
        agent = ResearchAgent(
            model=self.model,
            temperature=0.5,
            browser_config=self.browser_config,
        )

        result = await agent.research_topic(
            topic=topic,
            depth=depth,
            max_sources=max_sources,
            max_steps=max_steps,
        )

        return TaskResult(
            success=result.get("success", False),
            task_type="research",
            summary=result.get("summary", ""),
            data=result,
            steps=result.get("steps", []),
            error=result.get("error"),
        )

    async def compare_products(
        self,
        products: List[str],
        aspects: List[str],
        max_steps: int = 60,
    ) -> TaskResult:
        """
        Compare multiple products across specified aspects.

        Args:
            products: List of product names
            aspects: Aspects to compare (price, features, etc.)
            max_steps: Maximum agent steps

        Returns:
            TaskResult with comparison details
        """
        agent = ResearchAgent(
            model=self.model,
            temperature=0.5,
            browser_config=self.browser_config,
        )

        result = await agent.compare_products(
            products=products,
            comparison_aspects=aspects,
            max_steps=max_steps,
        )

        return TaskResult(
            success=result.get("success", False),
            task_type="product_comparison",
            summary=result.get("summary", ""),
            data=result,
            steps=result.get("steps", []),
            error=result.get("error"),
        )

    # ============== Parallel Execution ==============

    async def run_parallel_tasks(
        self,
        tasks: List[Dict[str, Any]],
        max_concurrent: int = 3,
    ) -> List[TaskResult]:
        """
        Run multiple tasks in parallel (unique to this package).

        Args:
            tasks: List of task dictionaries with 'id', 'description', and optional 'max_steps'
            max_concurrent: Maximum concurrent agents

        Returns:
            List of TaskResults
        """
        runner = ParallelAgentRunner(
            model=self.model,
            temperature=self.temperature,
            browser_config=self.browser_config,
            max_concurrent_agents=max_concurrent,
        )

        agent_tasks = [
            AgentTask(
                task_id=t.get("id", f"task_{i}"),
                description=t["description"],
                max_steps=t.get("max_steps", 25),
            )
            for i, t in enumerate(tasks)
        ]

        results = await runner.run_parallel(agent_tasks)

        return [
            TaskResult(
                success=r.success,
                task_type="parallel_task",
                summary=r.summary,
                data={"task_id": r.task_id, "steps": r.steps},
                steps=r.steps,
                error=r.error,
            )
            for r in results
        ]

    # ============== Multi-Tab ==============

    async def compare_pages(
        self,
        urls: List[str],
        comparison_criteria: str,
        max_steps: int = 30,
    ) -> TaskResult:
        """
        Compare content across multiple web pages using tabs.

        Args:
            urls: URLs to compare
            comparison_criteria: What to compare
            max_steps: Maximum agent steps

        Returns:
            TaskResult with comparison details
        """
        agent = MultiTabAgent(
            model=self.model,
            temperature=self.temperature,
            browser_config=self.browser_config,
        )

        result = await agent.compare_pages(
            urls=urls,
            comparison_criteria=comparison_criteria,
            max_steps=max_steps,
        )

        return TaskResult(
            success=result.get("success", False),
            task_type="page_comparison",
            summary=result.get("summary", ""),
            data=result,
            steps=result.get("steps", []),
            error=result.get("error"),
        )


# Convenience function for quick task execution
async def run_browser_task(
    task: str,
    model: str = DEFAULT_MODEL,
    headless: bool = False,
    max_steps: int = 30,
) -> Dict[str, Any]:
    """
    Quick helper function to run a browser automation task.

    Args:
        task: Natural language task description
        model: Gemini model to use
        headless: Run browser without visible window
        max_steps: Maximum steps

    Returns:
        Task execution results
    """
    service = AdvancedBrowserService(model=model, headless=headless)
    result = await service.run_task(task=task, max_steps=max_steps)

    return {
        "success": result.success,
        "summary": result.summary,
        "steps": result.steps,
        "error": result.error,
    }


if __name__ == "__main__":
    # Example usage
    async def demo():
        service = AdvancedBrowserService(headless=False)

        # Run a simple task
        result = await service.run_task(
            "Search Google for 'browser automation python' and tell me the top 3 results"
        )
        print(f"Task completed: {result.success}")
        print(f"Summary: {result.summary}")

    asyncio.run(demo())
