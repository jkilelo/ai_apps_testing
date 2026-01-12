"""
Base Service Configuration

Provides core configuration for all advanced browser services including
LLM initialization and browser configuration.

NOTE: Browser instantiation should use BrowserFactory from ui_testing_agent.core.
The BrowserConfig class here is DEPRECATED - use BrowserFactory.BrowserConfig instead.
"""

import os
import warnings
from dataclasses import dataclass, field
from typing import Optional, Any, Dict
from dotenv import load_dotenv
# Import BrowserFactory as the single source of truth
from ui_testing_agent.core.browser_factory import (
    BrowserFactory,
    BrowserResult,
    BrowserConfig as FactoryBrowserConfig,
)

load_dotenv()

# Import LLM factory (single source of truth - no circular imports)
from .llm_factory import get_llm, get_gemini_llm, DEFAULT_MODEL


@dataclass
class BrowserConfig:
    """
    DEPRECATED: Use BrowserFactory from ui_testing_agent.core instead.

    This class is kept for backwards compatibility but will be removed in a future version.
    All browser instantiation should go through BrowserFactory.create().
    """
    headless: bool = False
    disable_security: bool = False
    args: list = field(default_factory=list)
    window_width: int = 1280
    window_height: int = 900
    user_data_dir: Optional[str] = None
    allowed_domains: Optional[list] = None
    profile_path: Optional[str] = None

    async def create_browser_async(self) -> BrowserResult:
        """
        Create a browser using BrowserFactory (single source of truth).

        Returns:
            BrowserResult from BrowserFactory
        """
        warnings.warn(
            "BrowserConfig.create_browser_async() is deprecated. "
            "Use BrowserFactory.create() directly instead.",
            DeprecationWarning,
            stacklevel=2
        )
        config = FactoryBrowserConfig(
            headless=self.headless,
            disable_security=self.disable_security,
            extra_args=self.args,
            window_width=self.window_width,
            window_height=self.window_height,
        )
        return await BrowserFactory.create(config=config)

    def create_browser(self):
        """
        DEPRECATED: This synchronous method cannot be used with BrowserFactory.

        Use create_browser_async() or BrowserFactory.create() instead.
        """
        raise DeprecationWarning(
            "BrowserConfig.create_browser() is deprecated and no longer works. "
            "Use 'await BrowserFactory.create()' instead. "
            "Browser instantiation must go through BrowserFactory (single source of truth)."
        )


class BaseAgentService:
    """
    Base class for all advanced agent services.

    Provides common functionality for browser automation agents.
    Uses BrowserFactory as the single source of truth for browser instantiation.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        headless: bool = False,
    ):
        """
        Initialize the base agent service.

        Args:
            model: Gemini model to use
            temperature: LLM temperature setting
            headless: Run browser without visible window
        """
        self.llm = get_llm(model=model, temperature=temperature)
        self.headless = headless
        self._browser_result: Optional[BrowserResult] = None

    async def _ensure_browser(self) -> BrowserResult:
        """
        Ensure browser is initialized using BrowserFactory.

        Returns:
            BrowserResult from BrowserFactory
        """
        if self._browser_result is None:
            self._browser_result = await BrowserFactory.create(headless=self.headless)
        return self._browser_result

    async def close(self):
        """Clean up browser resources using BrowserFactory."""
        if self._browser_result:
            await BrowserFactory.cleanup(self._browser_result)
            self._browser_result = None
