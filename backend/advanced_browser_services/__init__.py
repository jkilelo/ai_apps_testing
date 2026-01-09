"""
Advanced Browser Services Package

This package provides advanced browser automation services built on top of browser-use,
using Google's Gemini 3 Flash Preview model for enhanced AI-powered web automation.

Features (non-redundant with browser-use):
- Multi-tab orchestration and comparison workflows
- Parallel agent execution with concurrency control
- Structured data extraction with schema support
- Web research framework with source tracking
"""

from .base_service import get_gemini_llm, BrowserConfig, BaseAgentService, DEFAULT_MODEL
from .multi_tab_agent import MultiTabAgent
from .parallel_agents import ParallelAgentRunner, AgentTask, AgentResult
from .data_extraction_agent import DataExtractionAgent
from .research_agent import ResearchAgent
from .service_runner import AdvancedBrowserService, TaskResult, run_browser_task

__all__ = [
    # Base
    "get_gemini_llm",
    "BrowserConfig",
    "BaseAgentService",
    "DEFAULT_MODEL",
    # Agents
    "MultiTabAgent",
    "ParallelAgentRunner",
    "AgentTask",
    "AgentResult",
    "DataExtractionAgent",
    "ResearchAgent",
    # Unified Service
    "AdvancedBrowserService",
    "TaskResult",
    "run_browser_task",
]
