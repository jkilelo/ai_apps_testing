"""
Streaming Service for Browser Automation

Provides Server-Sent Events (SSE) streaming of browser-use agent logs
to enable real-time progress updates in the frontend.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import AsyncGenerator, Optional, Dict, Any, Callable, Awaitable
from dataclasses import dataclass, field, asdict
from enum import Enum


class LogLevel(str, Enum):
    """Log severity levels."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warn"
    ERROR = "error"
    DEBUG = "debug"


class EventType(str, Enum):
    """Types of streaming events."""
    STEP_START = "step_start"
    STEP_THINKING = "step_thinking"
    STEP_ACTION = "step_action"
    STEP_RESULT = "step_result"
    BROWSER_STATE = "browser_state"
    ERROR = "error"
    DONE = "done"
    PROGRESS = "progress"


@dataclass
class StreamEvent:
    """A single streaming event."""
    event_type: EventType
    level: LogLevel
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    data: Optional[Dict[str, Any]] = None
    step_number: Optional[int] = None

    def to_sse(self) -> str:
        """Convert to SSE format."""
        event_data = {
            "type": self.event_type.value,
            "level": self.level.value,
            "message": self.message,
            "timestamp": self.timestamp,
            "step": self.step_number,
        }
        if self.data:
            event_data["data"] = self.data

        # SSE format: data: {json}\n\n
        return f"data: {json.dumps(event_data)}\n\n"


class StreamingSession:
    """
    Manages a streaming session for a browser automation task.

    Collects events from browser-use callbacks and provides them
    as an async generator for SSE streaming.
    """

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self._queue: asyncio.Queue[StreamEvent] = asyncio.Queue()
        self._is_running = True
        self._step_count = 0

    def emit(
        self,
        event_type: EventType,
        message: str,
        level: LogLevel = LogLevel.INFO,
        data: Optional[Dict[str, Any]] = None,
    ):
        """Emit an event to the stream."""
        event = StreamEvent(
            event_type=event_type,
            level=level,
            message=message,
            data=data,
            step_number=self._step_count,
        )
        self._queue.put_nowait(event)

    def emit_info(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Emit an info event."""
        self.emit(EventType.PROGRESS, message, LogLevel.INFO, data)

    def emit_success(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Emit a success event."""
        self.emit(EventType.PROGRESS, message, LogLevel.SUCCESS, data)

    def emit_error(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Emit an error event."""
        self.emit(EventType.ERROR, message, LogLevel.ERROR, data)

    def emit_step_start(self, step_num: int):
        """Emit step start event."""
        self._step_count = step_num
        self.emit(
            EventType.STEP_START,
            f"Starting step {step_num}",
            LogLevel.INFO,
        )

    def emit_thinking(self, thinking: str):
        """Emit agent thinking event."""
        self.emit(
            EventType.STEP_THINKING,
            thinking[:200] + "..." if len(thinking) > 200 else thinking,
            LogLevel.DEBUG,
            {"full_thinking": thinking}
        )

    def emit_action(self, action_name: str, action_params: Optional[Dict] = None):
        """Emit action event."""
        self.emit(
            EventType.STEP_ACTION,
            f"Executing: {action_name}",
            LogLevel.INFO,
            {"action": action_name, "params": action_params}
        )

    def emit_browser_state(self, url: str, title: str):
        """Emit browser state update."""
        self.emit(
            EventType.BROWSER_STATE,
            f"Page: {title[:50]}..." if len(title) > 50 else f"Page: {title}",
            LogLevel.INFO,
            {"url": url, "title": title}
        )

    def emit_done(self, summary: str, success: bool = True):
        """Emit task completion event."""
        self.emit(
            EventType.DONE,
            summary,
            LogLevel.SUCCESS if success else LogLevel.ERROR,
            {"success": success, "total_steps": self._step_count}
        )
        self._is_running = False

    async def events(self) -> AsyncGenerator[str, None]:
        """
        Async generator that yields SSE-formatted events.

        Use this with FastAPI's StreamingResponse.
        """
        while self._is_running or not self._queue.empty():
            try:
                event = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=30.0  # Heartbeat timeout
                )
                yield event.to_sse()
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                yield ": heartbeat\n\n"
            except Exception as e:
                yield StreamEvent(
                    event_type=EventType.ERROR,
                    level=LogLevel.ERROR,
                    message=f"Stream error: {str(e)}"
                ).to_sse()
                break

        # Final done event if not already sent
        if self._is_running:
            self._is_running = False
            yield StreamEvent(
                event_type=EventType.DONE,
                level=LogLevel.INFO,
                message="Stream ended"
            ).to_sse()

    def close(self):
        """Close the streaming session."""
        self._is_running = False


def create_step_callback(session: StreamingSession):
    """
    Create a browser-use step callback that streams events.

    Returns a callback compatible with Agent's register_new_step_callback.
    """
    async def step_callback(browser_state, agent_output, step_num: int):
        """Called after each agent step."""
        session.emit_step_start(step_num)

        # Emit browser state
        if browser_state:
            session.emit_browser_state(
                url=getattr(browser_state, 'url', 'Unknown'),
                title=getattr(browser_state, 'title', 'Unknown')
            )

        # Emit thinking
        if agent_output and agent_output.thinking:
            session.emit_thinking(agent_output.thinking)

        # Emit next goal
        if agent_output and agent_output.next_goal:
            session.emit_info(f"Goal: {agent_output.next_goal}")

        # Emit actions
        if agent_output and agent_output.action:
            for action in agent_output.action:
                action_name = type(action).__name__
                # Try to get action params if available
                action_params = None
                if hasattr(action, 'model_dump'):
                    try:
                        action_params = action.model_dump(exclude_none=True)
                    except:
                        pass
                session.emit_action(action_name, action_params)

        # Emit any browser errors
        if browser_state and hasattr(browser_state, 'browser_errors'):
            for error in browser_state.browser_errors:
                session.emit_error(f"Browser error: {error}")

    return step_callback


def create_done_callback(session: StreamingSession):
    """
    Create a browser-use done callback that streams completion.

    Returns a callback compatible with Agent's register_done_callback.
    """
    async def done_callback(history):
        """Called when agent completes."""
        final_result = None
        success = True

        if hasattr(history, 'final_result'):
            final_result = history.final_result()

        if hasattr(history, 'is_successful'):
            success = history.is_successful()

        session.emit_done(
            summary=final_result or "Task completed",
            success=success
        )

    return done_callback


# Session registry for managing active streaming sessions
_active_sessions: Dict[str, StreamingSession] = {}


def get_session(session_id: str) -> Optional[StreamingSession]:
    """Get an active streaming session."""
    return _active_sessions.get(session_id)


def create_session() -> StreamingSession:
    """Create and register a new streaming session."""
    session = StreamingSession()
    _active_sessions[session.session_id] = session
    return session


def remove_session(session_id: str):
    """Remove a streaming session."""
    if session_id in _active_sessions:
        _active_sessions[session_id].close()
        del _active_sessions[session_id]
