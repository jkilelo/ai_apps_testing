# Fix Windows console encoding for emoji support
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from pathlib import Path
from dotenv import load_dotenv
import json
import asyncio
from advanced_browser_services.streaming_runner import get_streaming_runner

load_dotenv()

app = FastAPI()

# Initialize streaming runner
streaming_runner = get_streaming_runner()

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from typing import List, Optional


# ============== SSE Streaming Endpoints ==============

class StreamingTaskRequest(BaseModel):
    """Request for streaming task."""
    task: str
    max_steps: int = 30
    headless: bool = False


class StreamingExtractRequest(BaseModel):
    """Request for streaming data extraction."""
    url: str
    data_schema: dict
    max_items: Optional[int] = None
    max_steps: int = 40
    headless: bool = False


class StreamingResearchRequest(BaseModel):
    """Request for streaming research."""
    topic: str
    depth: str = "moderate"
    max_sources: int = 5
    max_steps: int = 50
    headless: bool = False


class StreamingCompareProductsRequest(BaseModel):
    """Request for streaming product comparison."""
    products: List[str]
    aspects: List[str]
    max_steps: int = 60
    headless: bool = False


class StreamingComparePagesRequest(BaseModel):
    """Request for streaming page comparison."""
    urls: List[str]
    comparison_criteria: str
    max_steps: int = 30
    headless: bool = False


@app.post("/stream/basic-task")
async def stream_basic_task(request: StreamingTaskRequest):
    """
    Run a basic browser automation task with SSE streaming.

    Returns a Server-Sent Events stream with real-time progress updates.
    """
    session = streaming_runner.create_session()

    async def event_generator():
        # Start the task in background
        task_coro = streaming_runner.run_ui_testing_agent_task(
            session=session,
            task=request.task,
            max_steps=request.max_steps,
            headless=request.headless,
        )

        # Run task and stream events concurrently
        task = asyncio.create_task(task_coro)

        try:
            async for event in session.events():
                yield event
        finally:
            if not task.done():
                task.cancel()
            streaming_runner.cleanup_session(session.session_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@app.post("/stream/extract-data")
async def stream_extract_data(request: StreamingExtractRequest):
    """
    Extract data with SSE streaming.
    """
    session = streaming_runner.create_session()

    async def event_generator():
        task_coro = streaming_runner.run_data_extraction(
            session=session,
            url=request.url,
            data_schema=request.data_schema,
            max_items=request.max_items,
            max_steps=request.max_steps,
            headless=request.headless,
        )

        task = asyncio.create_task(task_coro)

        try:
            async for event in session.events():
                yield event
        finally:
            if not task.done():
                task.cancel()
            streaming_runner.cleanup_session(session.session_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.post("/stream/research-topic")
async def stream_research_topic(request: StreamingResearchRequest):
    """
    Research a topic with SSE streaming.
    """
    session = streaming_runner.create_session()

    async def event_generator():
        task_coro = streaming_runner.run_research(
            session=session,
            topic=request.topic,
            depth=request.depth,
            max_sources=request.max_sources,
            max_steps=request.max_steps,
            headless=request.headless,
        )

        task = asyncio.create_task(task_coro)

        try:
            async for event in session.events():
                yield event
        finally:
            if not task.done():
                task.cancel()
            streaming_runner.cleanup_session(session.session_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.post("/stream/compare-products")
async def stream_compare_products(request: StreamingCompareProductsRequest):
    """
    Compare products with SSE streaming.
    """
    session = streaming_runner.create_session()

    async def event_generator():
        task_coro = streaming_runner.run_product_comparison(
            session=session,
            products=request.products,
            aspects=request.aspects,
            max_steps=request.max_steps,
            headless=request.headless,
        )

        task = asyncio.create_task(task_coro)

        try:
            async for event in session.events():
                yield event
        finally:
            if not task.done():
                task.cancel()
            streaming_runner.cleanup_session(session.session_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.post("/stream/compare-pages")
async def stream_compare_pages(request: StreamingComparePagesRequest):
    """
    Compare pages with SSE streaming.
    """
    session = streaming_runner.create_session()

    async def event_generator():
        task_coro = streaming_runner.run_page_comparison(
            session=session,
            urls=request.urls,
            comparison_criteria=request.comparison_criteria,
            max_steps=request.max_steps,
            headless=request.headless,
        )

        task = asyncio.create_task(task_coro)

        try:
            async for event in session.events():
                yield event
        finally:
            if not task.done():
                task.cancel()
            streaming_runner.cleanup_session(session.session_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# ============== Artifacts Endpoints ==============

# Base directory for test outputs
TEST_OUTPUTS_DIR = Path("./test_outputs")


class ArtifactInfo(BaseModel):
    """Information about a single artifact."""
    name: str
    type: str  # 'file' or 'directory'
    path: str
    size: Optional[int] = None
    url: str


class SessionArtifacts(BaseModel):
    """All artifacts for a session."""
    session_id: str
    output_directory: str
    artifacts: List[ArtifactInfo]
    html_report: Optional[str] = None
    json_report: Optional[str] = None
    playwright_code: Optional[str] = None
    screenshots: List[str] = []
    video: Optional[str] = None


@app.get("/artifacts/{session_id}", response_model=SessionArtifacts)
async def get_session_artifacts(session_id: str):
    """
    Get list of all artifacts for a session.
    """
    session_dir = TEST_OUTPUTS_DIR / session_id

    if not session_dir.exists():
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    artifacts = []
    html_report = None
    json_report = None
    playwright_code = None
    screenshots = []
    video = None

    # Walk through session directory
    for item in session_dir.rglob("*"):
        if item.is_file():
            rel_path = item.relative_to(session_dir)
            artifact_url = f"/artifacts/{session_id}/file/{rel_path.as_posix()}"

            artifact = ArtifactInfo(
                name=item.name,
                type="file",
                path=str(rel_path),
                size=item.stat().st_size,
                url=artifact_url,
            )
            artifacts.append(artifact)

            # Categorize artifacts
            if item.name == "report.html":
                html_report = artifact_url
            elif item.name == "report.json":
                json_report = artifact_url
            elif item.suffix == ".py" and item.name.startswith("test_"):
                playwright_code = artifact_url
            elif item.suffix == ".png":
                screenshots.append(artifact_url)
            elif item.suffix == ".gif":
                video = artifact_url

    return SessionArtifacts(
        session_id=session_id,
        output_directory=str(session_dir),
        artifacts=artifacts,
        html_report=html_report,
        json_report=json_report,
        playwright_code=playwright_code,
        screenshots=sorted(screenshots),
        video=video,
    )


@app.get("/artifacts/{session_id}/file/{file_path:path}")
async def get_artifact_file(session_id: str, file_path: str):
    """
    Serve a specific artifact file.
    """
    file_full_path = TEST_OUTPUTS_DIR / session_id / file_path

    if not file_full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not file_full_path.is_file():
        raise HTTPException(status_code=400, detail="Not a file")

    # Determine media type
    suffix = file_full_path.suffix.lower()
    media_types = {
        ".html": "text/html",
        ".json": "application/json",
        ".py": "text/x-python",
        ".png": "image/png",
        ".gif": "image/gif",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".md": "text/markdown",
        ".yaml": "text/yaml",
        ".yml": "text/yaml",
        ".feature": "text/plain",
    }
    media_type = media_types.get(suffix, "application/octet-stream")

    # Files that should display inline (not trigger download)
    inline_types = {".html", ".png", ".gif", ".jpg", ".jpeg"}

    if suffix in inline_types:
        # Don't set filename for inline content - allows iframe/img display
        return FileResponse(
            path=file_full_path,
            media_type=media_type,
        )
    else:
        # Set filename for downloadable files
        return FileResponse(
            path=file_full_path,
            media_type=media_type,
            filename=file_full_path.name,
        )


@app.get("/artifacts/{session_id}/code")
async def get_playwright_code(session_id: str):
    """
    Get the generated Playwright code content.
    """
    session_dir = TEST_OUTPUTS_DIR / session_id / "tests"

    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Tests directory not found")

    # Find the test file
    test_files = list(session_dir.glob("test_*.py"))
    if not test_files:
        raise HTTPException(status_code=404, detail="No test file found")

    test_file = test_files[0]
    content = test_file.read_text(encoding="utf-8")

    return {
        "filename": test_file.name,
        "content": content,
        "path": str(test_file.relative_to(TEST_OUTPUTS_DIR)),
    }


@app.get("/sessions")
async def list_sessions():
    """
    List all available test sessions.
    """
    if not TEST_OUTPUTS_DIR.exists():
        return {"sessions": []}

    sessions = []
    for item in TEST_OUTPUTS_DIR.iterdir():
        if item.is_dir():
            # Get session info
            report_json = item / "reports" / "report.json"
            metadata_file = item / "metadata.json"

            session_info = {
                "session_id": item.name,
                "created_at": item.stat().st_mtime,
                "has_report": report_json.exists(),
                "task": None,
                "max_steps": None,
            }

            # Read metadata if available
            if metadata_file.exists():
                try:
                    metadata = json.loads(metadata_file.read_text())
                    session_info["task"] = metadata.get("task")
                    session_info["max_steps"] = metadata.get("max_steps")
                    if metadata.get("created_at"):
                        # Use metadata timestamp if available
                        from datetime import datetime
                        dt = datetime.fromisoformat(metadata["created_at"])
                        session_info["created_at"] = dt.timestamp()
                except Exception:
                    pass

            sessions.append(session_info)

    # Sort by creation time (newest first)
    sessions.sort(key=lambda x: x["created_at"], reverse=True)

    return {"sessions": sessions}


# ============== Replay Endpoints (using BrowserUseReplayer) ==============

from ui_testing_agent.core.browser_use_replay import (
    BrowserUseReplayer,
    RecordedSession,
)


class ReplayRequest(BaseModel):
    """Request for replay operation."""
    headless: bool = True
    stop_on_failure: bool = False
    sensitive_data: Optional[dict] = None  # For filling in [SENSITIVE] fields


class ReplayResponse(BaseModel):
    """Response model for replay result."""
    success: bool
    session_id: str
    actions_total: int
    actions_succeeded: int
    actions_failed: int
    failed_steps: List[int] = []
    errors: List[str] = []
    duration_seconds: float = 0.0


class ReplaySessionInfo(BaseModel):
    """Info about a session available for replay."""
    session_id: str
    task: str
    initial_url: str
    recorded_at: str
    action_count: int
    recording_path: str


def _find_replay_recording(session_dir: Path) -> Optional[Path]:
    """Find replay recording file in session directory."""
    # Check exact file names first
    candidates = [
        session_dir / "replay_recording.json",
        session_dir / "recording.json",
        session_dir / "recorded_session.json",
    ]
    for path in candidates:
        if path.exists():
            return path

    # Also search for pattern-based names (replay_recording_*.json)
    for path in session_dir.glob("replay_recording_*.json"):
        return path

    return None


@app.get("/replay/sessions")
async def list_replay_sessions():
    """
    List all sessions that have replay recordings available.

    Only returns sessions with valid replay_recording.json files.
    """
    if not TEST_OUTPUTS_DIR.exists():
        return {"sessions": [], "total": 0}

    sessions = []
    for item in TEST_OUTPUTS_DIR.iterdir():
        if not item.is_dir():
            continue

        recording_path = _find_replay_recording(item)
        if not recording_path:
            continue

        try:
            # Load session to get metadata
            recorded = RecordedSession.load(str(recording_path))
            # Use directory name as session_id (for API lookups)
            sessions.append(ReplaySessionInfo(
                session_id=item.name,  # Use directory name, not recording's internal ID
                task=recorded.task,
                initial_url=recorded.initial_url,
                recorded_at=recorded.recorded_at,
                action_count=len(recorded.actions),
                recording_path=str(recording_path),
            ))
        except Exception:
            # Skip invalid recordings
            continue

    # Sort by recorded_at (newest first)
    sessions.sort(key=lambda x: x.recorded_at, reverse=True)

    return {"sessions": sessions, "total": len(sessions)}


@app.get("/replay/{session_id}/info")
async def get_replay_info(session_id: str):
    """
    Get detailed info about a replay recording.

    Returns session metadata and action summary without running the replay.
    """
    session_dir = TEST_OUTPUTS_DIR / session_id
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    recording_path = _find_replay_recording(session_dir)
    if not recording_path:
        raise HTTPException(
            status_code=404,
            detail=f"No replay recording found for session: {session_id}"
        )

    try:
        recorded = RecordedSession.load(str(recording_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load recording: {e}")

    # Summarize actions by type
    action_summary = {}
    for action in recorded.actions:
        action_type = action.action_type.value
        action_summary[action_type] = action_summary.get(action_type, 0) + 1

    return {
        "session_id": recorded.session_id,
        "task": recorded.task,
        "initial_url": recorded.initial_url,
        "recorded_at": recorded.recorded_at,
        "browser_use_version": recorded.browser_use_version,
        "action_count": len(recorded.actions),
        "action_summary": action_summary,
        "actions": [
            {
                "step": a.step_number,
                "type": a.action_type.value,
                "url": a.url,
                "text": "[SENSITIVE]" if a.is_sensitive else a.text,
                "element_selector": a.element.css_selector if a.element else None,
            }
            for a in recorded.actions
        ],
    }


@app.post("/replay/{session_id}", response_model=ReplayResponse)
async def run_replay(session_id: str, request: Optional[ReplayRequest] = None):
    """
    Run a deterministic replay for a session.

    This replays recorded actions WITHOUT using an LLM - pure browser automation.
    Uses browser-use's event system for reliable element finding.

    Args:
        session_id: The session to replay
        request: Optional configuration (headless mode, stop on failure, sensitive data)

    Returns:
        ReplayResponse with success/failure details
    """
    request = request or ReplayRequest()

    session_dir = TEST_OUTPUTS_DIR / session_id
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    recording_path = _find_replay_recording(session_dir)
    if not recording_path:
        raise HTTPException(
            status_code=404,
            detail=f"No replay recording found for session: {session_id}"
        )

    # Load the recorded session
    try:
        recorded = RecordedSession.load(str(recording_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load recording: {e}")

    # Create browser using the factory (single source of truth)
    from ui_testing_agent.core.browser_factory import BrowserFactory, BrowserConfig

    browser_result = await BrowserFactory.create(
        config=BrowserConfig(headless=request.headless, disable_security=True)
    )
    if browser_result.browser is None:
        raise HTTPException(status_code=500, detail="Could not create browser for replay")

    browser_session = browser_result.browser

    # browser_class strategy defers start() to the caller
    if browser_result.strategy_used == "browser_class":
        await browser_session.start()

    try:
        # Create replayer and run
        replayer = BrowserUseReplayer()
        replay_result = await replayer.replay(
            session=recorded,
            browser_session=browser_session,
            stop_on_failure=request.stop_on_failure,
            sensitive_data=request.sensitive_data,
        )

        return ReplayResponse(
            success=replay_result.success,
            session_id=session_id,
            actions_total=replay_result.actions_total,
            actions_succeeded=replay_result.actions_succeeded,
            actions_failed=replay_result.actions_failed,
            failed_steps=replay_result.failed_steps,
            errors=replay_result.errors,
            duration_seconds=replay_result.duration_seconds,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Replay failed: {e}")

    finally:
        await BrowserFactory.cleanup(browser_result)


@app.post("/stream/replay/{session_id}")
async def stream_replay(session_id: str, request: Optional[ReplayRequest] = None):
    """
    Run replay with SSE streaming progress updates.

    Streams real-time progress as each action executes.
    """
    request = request or ReplayRequest()

    session_dir = TEST_OUTPUTS_DIR / session_id
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    recording_path = _find_replay_recording(session_dir)
    if not recording_path:
        raise HTTPException(
            status_code=404,
            detail=f"No replay recording found for session: {session_id}"
        )

    # Load the recorded session
    try:
        recorded = RecordedSession.load(str(recording_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load recording: {e}")

    async def event_generator():
        from ui_testing_agent.core.browser_factory import BrowserFactory, BrowserConfig

        browser_result = await BrowserFactory.create(
            config=BrowserConfig(headless=request.headless, disable_security=True)
        )
        if browser_result.browser is None:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Could not create browser for replay'})}\n\n"
            return

        browser_session = browser_result.browser

        # browser_class strategy defers start() to the caller
        if browser_result.strategy_used == "browser_class":
            await browser_session.start()

        try:
            # Progress tracking via callbacks
            progress_events = asyncio.Queue()

            def on_step_start(step: int, action):
                asyncio.get_event_loop().call_soon_threadsafe(
                    progress_events.put_nowait,
                    {
                        "type": "step_start",
                        "step": step,
                        "action_type": action.action_type.value,
                        "total": len(recorded.actions),
                    }
                )

            def on_step_complete(step: int, success: bool, error: Optional[str]):
                asyncio.get_event_loop().call_soon_threadsafe(
                    progress_events.put_nowait,
                    {
                        "type": "step_complete",
                        "step": step,
                        "success": success,
                        "error": error,
                    }
                )

            replayer = BrowserUseReplayer(
                on_step_start=on_step_start,
                on_step_complete=on_step_complete,
            )

            # Run replay in background
            async def run_replay_task():
                result = await replayer.replay(
                    session=recorded,
                    browser_session=browser_session,
                    stop_on_failure=request.stop_on_failure,
                    sensitive_data=request.sensitive_data,
                )
                await progress_events.put({"type": "complete", "result": result})

            task = asyncio.create_task(run_replay_task())

            # Send initial event
            yield f"data: {json.dumps({'type': 'started', 'session_id': session_id, 'total_actions': len(recorded.actions)})}\n\n"

            # Stream progress events
            while True:
                try:
                    event = await asyncio.wait_for(progress_events.get(), timeout=60.0)

                    if event["type"] == "complete":
                        result = event["result"]
                        final_data = {
                            "type": "complete",
                            "success": result.success,
                            "actions_total": result.actions_total,
                            "actions_succeeded": result.actions_succeeded,
                            "actions_failed": result.actions_failed,
                            "failed_steps": result.failed_steps,
                            "errors": result.errors,
                            "duration_seconds": result.duration_seconds,
                        }
                        yield f"data: {json.dumps(final_data)}\n\n"
                        break
                    else:
                        yield f"data: {json.dumps(event)}\n\n"

                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        finally:
            await BrowserFactory.cleanup(browser_result)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
