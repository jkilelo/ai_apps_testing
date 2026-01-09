"""
Base Service Configuration

Provides core configuration for all advanced browser services including
LLM initialization and browser configuration.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Any, Dict
from dotenv import load_dotenv
from browser_use import ChatGoogle, Browser

load_dotenv()

# Default model to use across all services
DEFAULT_MODEL = "gemini-3-pro-preview"


def get_gemini_llm(model: str = DEFAULT_MODEL, temperature: float = 0.7):
    """
    Initialize and return a ChatGoogle LLM instance configured for browser-use.

    Args:
        model: The Gemini model to use (default: gemini-3-flash-preview)
        temperature: Creativity/randomness of responses (0.0-1.0)

    Returns:
        ChatGoogle instance configured for browser automation
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")

    return ChatGoogle(
        model=model,
        temperature=temperature,
    )


@dataclass
class BrowserConfig:
    """
    Configuration class for browser sessions.

    Attributes:
        headless: Run browser without visible window
        disable_security: Disable browser security features (use with caution)
        args: Additional command-line arguments for Chromium
        window_width: Browser window width in pixels
        window_height: Browser window height in pixels
        user_data_dir: Path to browser user data directory for persistent sessions
        allowed_domains: List of allowed domains (restricts navigation)
        profile_path: Path to browser profile directory for persistent sessions
    """
    headless: bool = False
    disable_security: bool = False
    args: list = field(default_factory=list)
    window_width: int = 1280
    window_height: int = 900
    user_data_dir: Optional[str] = None
    allowed_domains: Optional[list] = None
    profile_path: Optional[str] = None

    def create_browser(self) -> Browser:
        """Create a Browser instance with the configured settings."""
        kwargs: Dict[str, Any] = {
            "headless": self.headless,
            "disable_security": self.disable_security,
        }

        if self.args:
            kwargs["args"] = self.args

        if self.user_data_dir:
            kwargs["user_data_dir"] = self.user_data_dir
        elif self.profile_path:
            kwargs["user_data_dir"] = self.profile_path

        if self.allowed_domains:
            kwargs["allowed_domains"] = self.allowed_domains

        if self.window_width and self.window_height:
            kwargs["viewport"] = {"width": self.window_width, "height": self.window_height}

        return Browser(**kwargs)


class BaseAgentService:
    """
    Base class for all advanced agent services.

    Provides common functionality for browser automation agents.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        browser_config: Optional[BrowserConfig] = None,
    ):
        """
        Initialize the base agent service.

        Args:
            model: Gemini model to use
            temperature: LLM temperature setting
            browser_config: Browser configuration options
        """
        self.llm = get_gemini_llm(model=model, temperature=temperature)
        self.browser_config = browser_config or BrowserConfig()
        self.browser: Optional[Any] = None

    async def _ensure_browser(self) -> Any:
        """Ensure browser session is initialized."""
        if self.browser is None:
            self.browser = self.browser_config.create_browser()
        return self.browser

    async def close(self):
        """Clean up browser resources."""
        if self.browser:
            try:
                await self.browser.close()
            except Exception:
                pass  # Ignore cleanup errors
            self.browser = None
