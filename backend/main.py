# Fix Windows console encoding for emoji support
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
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

class ProfileDataRequest(BaseModel):
    fileName: str
    sampleData: str

class QualityCheckerRequest(BaseModel):
    data: str
    rules: str

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

class DataStats(BaseModel):
    rows: float
    columns: float
    missingValues: float
    duplicateRows: float

class ProfileDataResponse(BaseModel):
    stats: DataStats
    insights: List[str]
    anomalies: List[str]

class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class Violation(BaseModel):
    rule: str
    issue: str
    severity: Severity

class QualityCheckerResponse(BaseModel):
    violations: List[Violation]
    score: float


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

@app.post("/profile-data")
async def profile_data(request: ProfileDataRequest):
    try:
        prompt = f'Analyze this data sample from file "{request.fileName}":\n\n{request.sampleData}\n\nProvide a data profile report in JSON format including basic stats, AI-driven insights, and potential anomalies.'
        
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=ProfileDataResponse
            )
        )
        return response.parsed
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/check-data-quality")
async def check_data_quality(request: QualityCheckerRequest):
    try:
        prompt = f'Apply these quality rules: "{request.rules}" to this dataset snippet: "{request.data}". List all violations and suggestions.'
        
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=QualityCheckerResponse
            )
        )
        return response.parsed
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
