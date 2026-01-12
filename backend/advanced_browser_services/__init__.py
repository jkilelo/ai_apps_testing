"""
Advanced Browser Services Package

This package provides streaming browser automation services built on top of browser-use,
using Google's Gemini model for AI-powered web automation with real-time SSE streaming.
"""

from .base_service import get_gemini_llm, BrowserConfig, BaseAgentService, DEFAULT_MODEL
from .streaming import (
    StreamingSession,
    StreamEvent,
    LogLevel,
    EventType,
    create_session,
    remove_session,
    get_session,
    create_step_callback,
    create_done_callback,
)
from .streaming_runner import StreamingAgentRunner, get_streaming_runner

__all__ = [
    # Base
    "get_gemini_llm",
    "BrowserConfig",
    "BaseAgentService",
    "DEFAULT_MODEL",
    # Streaming
    "StreamingSession",
    "StreamEvent",
    "LogLevel",
    "EventType",
    "create_session",
    "remove_session",
    "get_session",
    "create_step_callback",
    "create_done_callback",
    # Runner
    "StreamingAgentRunner",
    "get_streaming_runner",
]
