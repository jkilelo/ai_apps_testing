# Fix Windows console encoding for emoji support
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import json
import asyncio
import browsers_services
from advanced_browser_services.service_runner import AdvancedBrowserService
from advanced_browser_services.streaming_runner import get_streaming_runner, StreamingAgentRunner

load_dotenv()

app = FastAPI()

# Initialize advanced browser service
advanced_service = AdvancedBrowserService(headless=False)

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

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

class UIAutomatorRequest(BaseModel):
    instruction: str

from typing import List, Optional
from enum import Enum

class ActionStatus(str, Enum):
    done = "done"
    failed = "failed"

class UIStep(BaseModel):
    action: str
    status: ActionStatus

class UIAutomatorResponse(BaseModel):
    steps: List[UIStep]
    summary: str


# ============== Advanced Browser Service Models ==============

class ExtractDataRequest(BaseModel):
    url: str
    data_schema: dict
    max_items: Optional[int] = None
    max_steps: int = 40


class ResearchTopicRequest(BaseModel):
    topic: str
    depth: str = "moderate"  # shallow, moderate, deep
    max_sources: int = 5
    max_steps: int = 50


class CompareProductsRequest(BaseModel):
    products: List[str]
    aspects: List[str]
    max_steps: int = 60


class ParallelTask(BaseModel):
    id: str
    description: str
    max_steps: int = 25


class RunParallelTasksRequest(BaseModel):
    tasks: List[ParallelTask]
    max_concurrent: int = 3


class ComparePagesRequest(BaseModel):
    urls: List[str]
    comparison_criteria: str
    max_steps: int = 30


class TaskStep(BaseModel):
    action: str
    status: str


class TaskResultResponse(BaseModel):
    success: bool
    task_type: str
    summary: str
    data: dict
    steps: List[dict]
    error: Optional[str] = None


@app.post("/run-ui-automator")
async def run_ui_automator(request: UIAutomatorRequest):
    try:
        # Call the new browser-use based service
        result = await browsers_services.run_ui_automator(request.instruction)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== Advanced Browser Service Endpoints ==============

@app.post("/extract-data", response_model=TaskResultResponse)
async def extract_data(request: ExtractDataRequest):
    """Extract structured data from a web page."""
    try:
        result = await advanced_service.extract_data(
            url=request.url,
            data_schema=request.data_schema,
            max_items=request.max_items,
            max_steps=request.max_steps,
        )
        return TaskResultResponse(
            success=result.success,
            task_type=result.task_type,
            summary=result.summary,
            data=result.data,
            steps=result.steps,
            error=result.error,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/research-topic", response_model=TaskResultResponse)
async def research_topic(request: ResearchTopicRequest):
    """Research a topic and gather information from multiple sources."""
    try:
        result = await advanced_service.research_topic(
            topic=request.topic,
            depth=request.depth,
            max_sources=request.max_sources,
            max_steps=request.max_steps,
        )
        return TaskResultResponse(
            success=result.success,
            task_type=result.task_type,
            summary=result.summary,
            data=result.data,
            steps=result.steps,
            error=result.error,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compare-products", response_model=TaskResultResponse)
async def compare_products(request: CompareProductsRequest):
    """Compare multiple products across specified aspects."""
    try:
        result = await advanced_service.compare_products(
            products=request.products,
            aspects=request.aspects,
            max_steps=request.max_steps,
        )
        return TaskResultResponse(
            success=result.success,
            task_type=result.task_type,
            summary=result.summary,
            data=result.data,
            steps=result.steps,
            error=result.error,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/run-parallel-tasks")
async def run_parallel_tasks(request: RunParallelTasksRequest):
    """Run multiple browser tasks in parallel."""
    try:
        tasks = [
            {"id": t.id, "description": t.description, "max_steps": t.max_steps}
            for t in request.tasks
        ]
        results = await advanced_service.run_parallel_tasks(
            tasks=tasks,
            max_concurrent=request.max_concurrent,
        )
        return [
            TaskResultResponse(
                success=r.success,
                task_type=r.task_type,
                summary=r.summary,
                data=r.data,
                steps=r.steps,
                error=r.error,
            )
            for r in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compare-pages", response_model=TaskResultResponse)
async def compare_pages(request: ComparePagesRequest):
    """Compare content across multiple web pages using tabs."""
    try:
        result = await advanced_service.compare_pages(
            urls=request.urls,
            comparison_criteria=request.comparison_criteria,
            max_steps=request.max_steps,
        )
        return TaskResultResponse(
            success=result.success,
            task_type=result.task_type,
            summary=result.summary,
            data=result.data,
            steps=result.steps,
            error=result.error,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
            session_info = {
                "session_id": item.name,
                "created_at": item.stat().st_mtime,
                "has_report": report_json.exists(),
            }
            sessions.append(session_info)

    # Sort by creation time (newest first)
    sessions.sort(key=lambda x: x["created_at"], reverse=True)

    return {"sessions": sessions}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
