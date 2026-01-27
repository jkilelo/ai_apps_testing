"""
Advanced Browser Services Package

This package provides streaming browser automation services built on top of browser-use,
using Google's Gemini model for AI-powered web automation with real-time SSE streaming.
"""

from .llm_factory import get_llm, DEFAULT_MODEL
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


# Lazy import to avoid circular dependency with ui_testing_agent
def __getattr__(name):
    if name == "StreamingAgentRunner":
        from .streaming_runner import StreamingAgentRunner
        return StreamingAgentRunner
    elif name == "get_streaming_runner":
        from .streaming_runner import get_streaming_runner
        return get_streaming_runner
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # LLM
    "get_llm",
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
