"""
Browser Factory - Single Source of Truth for Browser Instantiation.

This module is the ONLY place where browsers should be instantiated.
All code that needs a browser MUST use BrowserFactory.create().

This ensures:
- Consistent browser initialization across the application
- Graceful fallback when one strategy fails
- Centralized logging and error handling
- Single point of maintenance for browser-related issues
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Optional, List, Dict

from browser_use import Browser

logger = logging.getLogger(__name__)


class BrowserInitializationError(Exception):
    """Raised when all browser initialization strategies fail."""
    pass


@dataclass
class BrowserResult:
    """
    Result from browser factory initialization.

    Attributes:
        browser: The browser/session object (or None for agent-managed)
        browser_type: Type indicator - "browser_session" | "browser" | "agent_managed"
        strategy_used: Name of the strategy that succeeded
    """
    browser: Any
    browser_type: str  # "browser_session" | "browser" | "agent_managed"
    strategy_used: str


@dataclass
class BrowserConfig:
    """
    Configuration options for browser instantiation.

    Attributes:
        headless: Run browser without visible window
        disable_security: Disable browser security features (use with caution)
        extra_args: Additional command-line arguments for Chromium
        window_width: Browser window width in pixels
        window_height: Browser window height in pixels
    """
    headless: bool = False
    disable_security: bool = False
    extra_args: List[str] = field(default_factory=list)
    window_width: int = 1280
    window_height: int = 900


class BrowserFactory:
    """
    Factory for creating browsers with graceful fallback.

    THIS IS THE SINGLE SOURCE OF TRUTH FOR BROWSER INSTANTIATION.

    All code that needs a browser MUST use this factory. Do not instantiate
    Browser, BrowserSession, or any browser-related class directly elsewhere.

    The factory tries multiple initialization strategies in order until one
    succeeds, handling the CDP client initialization issues gracefully.

    Usage:
        # Simple usage
        result = await BrowserFactory.create(headless=True)

        # With config
        config = BrowserConfig(headless=True, window_width=1920)
        result = await BrowserFactory.create(config=config)

        # Pass to Agent based on type
        if result.browser_type == "browser_session":
            agent = Agent(..., browser_session=result.browser)
        elif result.browser_type == "browser":
            agent = Agent(..., browser=result.browser)
        else:
            agent = Agent(...)  # agent-managed

        # Cleanup
        await BrowserFactory.cleanup(result)
    """

    # Strategy order - tried in sequence until one succeeds
    STRATEGIES = [
        "browser_session_with_start",
        "browser_class",
        "context_manager",
        "agent_managed",
    ]

    @classmethod
    async def create(
        cls,
        headless: bool = False,
        config: Optional[BrowserConfig] = None,
        preferred_strategy: Optional[str] = None,
    ) -> BrowserResult:
        """
        Create a browser using the first working strategy.

        This is the main entry point for browser creation. It tries multiple
        strategies in order until one succeeds.

        Args:
            headless: Run browser without visible window (ignored if config provided)
            config: Full browser configuration (overrides headless param)
            preferred_strategy: Optional specific strategy to try first

        Returns:
            BrowserResult with browser object and type information

        Raises:
            BrowserInitializationError: If all strategies fail
        """
        # Build config
        if config is None:
            config = BrowserConfig(headless=headless)

        # Determine strategy order
        strategies = cls.STRATEGIES.copy()
        if preferred_strategy and preferred_strategy in strategies:
            strategies.remove(preferred_strategy)
            strategies.insert(0, preferred_strategy)

        # Check for environment override
        env_strategy = os.getenv("BROWSER_STRATEGY")
        if env_strategy and env_strategy in strategies:
            strategies.remove(env_strategy)
            strategies.insert(0, env_strategy)
            logger.info(f"Using environment-specified strategy: {env_strategy}")

        failed_strategies: List[str] = []
        last_error: Optional[Exception] = None

        for strategy_name in strategies:
            logger.info(f"Attempting browser initialization with strategy: {strategy_name}")

            try:
                result = await cls._execute_strategy(strategy_name, config)
                if result:
                    logger.info(f"Browser initialized successfully using strategy: {strategy_name}")
                    return result
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Strategy {strategy_name} failed: {error_msg}")
                failed_strategies.append(f"{strategy_name}: {error_msg}")
                last_error = e
                continue

        # All strategies failed
        error_msg = (
            "Failed to initialize browser. Tried strategies:\n"
            + "\n".join(f"  - {s}" for s in failed_strategies)
            + "\n\nPlease check browser-use installation and Chrome/Chromium availability."
        )
        logger.error(error_msg)
        raise BrowserInitializationError(error_msg) from last_error

    @classmethod
    async def _execute_strategy(cls, strategy_name: str, config: BrowserConfig) -> Optional[BrowserResult]:
        """Execute a specific initialization strategy."""
        if strategy_name == "browser_session_with_start":
            return await cls._try_browser_session_with_start(config)
        elif strategy_name == "browser_class":
            return await cls._try_browser_class(config)
        elif strategy_name == "context_manager":
            return await cls._try_context_manager(config)
        elif strategy_name == "agent_managed":
            return cls._get_agent_managed()
        else:
            raise ValueError(f"Unknown strategy: {strategy_name}")

    @staticmethod
    async def _try_browser_session_with_start(config: BrowserConfig) -> BrowserResult:
        """
        Strategy 1: BrowserSession with explicit start() call.

        This is the recommended fix for browser-use 0.11.x where BrowserSession
        requires explicit initialization before CDP operations work.
        """
        try:
            from browser_use.browser.session import BrowserSession
            from browser_use.browser.profile import BrowserProfile
        except ImportError as e:
            raise ImportError(f"browser-use BrowserSession not available: {e}")

        browser_profile = BrowserProfile(headless=config.headless)
        browser_session = BrowserSession(browser_profile=browser_profile)

        # This is the key fix - explicitly start the session to initialize CDP
        if hasattr(browser_session, 'start'):
            await browser_session.start()
        else:
            raise AttributeError("BrowserSession does not have start() method")

        return BrowserResult(
            browser=browser_session,
            browser_type="browser_session",
            strategy_used="browser_session_with_start"
        )

    @staticmethod
    async def _try_browser_class(config: BrowserConfig) -> BrowserResult:
        """
        Strategy 2: Use Browser class directly.

        This is simpler and proven to work. The Browser class handles
        initialization internally.
        """
        kwargs: Dict[str, Any] = {
            "headless": config.headless,
        }

        if config.disable_security:
            kwargs["disable_security"] = True

        if config.extra_args:
            kwargs["extra_chromium_args"] = config.extra_args

        browser = Browser(**kwargs)

        return BrowserResult(
            browser=browser,
            browser_type="browser",
            strategy_used="browser_class"
        )

    @staticmethod
    async def _try_context_manager(config: BrowserConfig) -> BrowserResult:
        """
        Strategy 3: Use async context manager if supported.

        Note: This returns a session that was entered via __aenter__.
        Cleanup MUST call __aexit__ or use BrowserFactory.cleanup().
        """
        try:
            from browser_use.browser.session import BrowserSession
            from browser_use.browser.profile import BrowserProfile
        except ImportError as e:
            raise ImportError(f"browser-use BrowserSession not available: {e}")

        browser_profile = BrowserProfile(headless=config.headless)
        browser_session = BrowserSession(browser_profile=browser_profile)

        # Check if context manager is supported
        if not hasattr(browser_session, '__aenter__'):
            raise NotImplementedError("BrowserSession does not support async context manager")

        # Enter the context
        await browser_session.__aenter__()

        return BrowserResult(
            browser=browser_session,
            browser_type="browser_session",
            strategy_used="context_manager"
        )

    @staticmethod
    def _get_agent_managed() -> BrowserResult:
        """
        Strategy 4: Let Agent manage browser internally.

        This is the simplest but least controllable option. The Agent
        will create and manage its own browser instance.

        Pros: Simple, always works
        Cons: No control over headless, viewport, etc.
        """
        logger.info("Using agent-managed browser (no external browser instance)")
        return BrowserResult(
            browser=None,
            browser_type="agent_managed",
            strategy_used="agent_managed"
        )

    @staticmethod
    async def cleanup(result: BrowserResult) -> None:
        """
        Clean up browser resources based on type.

        This method handles cleanup for all browser types correctly.
        Always call this when done with the browser.

        Args:
            result: The BrowserResult to clean up
        """
        if not result or not result.browser:
            return

        try:
            if result.browser_type == "browser_session":
                if result.strategy_used == "context_manager":
                    # Exit the context manager properly
                    await result.browser.__aexit__(None, None, None)
                else:
                    # Use stop() for regular session
                    if hasattr(result.browser, 'stop'):
                        await result.browser.stop()
            elif result.browser_type == "browser":
                # Browser class uses close()
                if hasattr(result.browser, 'close'):
                    await result.browser.close()

            logger.debug(f"Browser cleanup completed (strategy: {result.strategy_used})")

        except Exception as e:
            logger.warning(f"Error during browser cleanup: {e}")

    @staticmethod
    def get_agent_kwargs(result: BrowserResult) -> Dict[str, Any]:
        """
        Get the appropriate kwargs to pass to Agent based on browser type.

        Usage:
            result = await BrowserFactory.create()
            agent = Agent(task=..., llm=..., **BrowserFactory.get_agent_kwargs(result))

        Args:
            result: The BrowserResult from create()

        Returns:
            Dict with either browser_session=, browser=, or empty dict
        """
        if result.browser_type == "browser_session":
            return {"browser_session": result.browser}
        elif result.browser_type == "browser":
            return {"browser": result.browser}
        else:
            # agent_managed - return empty dict, Agent will create its own
            return {}
