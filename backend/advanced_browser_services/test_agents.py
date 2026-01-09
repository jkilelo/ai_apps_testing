"""
Test script for Advanced Browser Services

Tests all agents to confirm they work correctly with gemini-3-flash-preview model.
"""

import asyncio
import sys
import os
import io

# Fix Windows console encoding for Unicode/emoji support
if sys.platform == "win32":
    # Set console to UTF-8 mode
    os.system("chcp 65001 > nul 2>&1")
    # Reconfigure stdout/stderr to use UTF-8
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def test_imports():
    """Test that all modules can be imported."""
    print("\n" + "="*60)
    print("TEST: Importing all modules...")
    print("="*60)

    try:
        from advanced_browser_services import (
            get_gemini_llm,
            BrowserConfig,
            BaseAgentService,
            DEFAULT_MODEL,
            MultiTabAgent,
            ParallelAgentRunner,
            AgentTask,
            AgentResult,
            DataExtractionAgent,
            ResearchAgent,
            AdvancedBrowserService,
            TaskResult,
            run_browser_task,
        )
        print("[PASS] All imports successful")
        print(f"[INFO] DEFAULT_MODEL = {DEFAULT_MODEL}")
        return True
    except ImportError as e:
        print(f"[FAIL] Import error: {e}")
        return False


def test_llm_initialization():
    """Test that the Gemini LLM can be initialized."""
    print("\n" + "="*60)
    print("TEST: LLM Initialization...")
    print("="*60)

    try:
        from advanced_browser_services import get_gemini_llm, DEFAULT_MODEL

        llm = get_gemini_llm()
        print(f"[PASS] LLM initialized with model: {DEFAULT_MODEL}")
        print(f"[INFO] LLM type: {type(llm).__name__}")
        return True
    except Exception as e:
        print(f"[FAIL] LLM initialization error: {e}")
        return False


def test_browser_config():
    """Test BrowserConfig creation."""
    print("\n" + "="*60)
    print("TEST: BrowserConfig...")
    print("="*60)

    try:
        from advanced_browser_services import BrowserConfig

        config = BrowserConfig(headless=True)
        print(f"[PASS] BrowserConfig created: headless={config.headless}")

        browser = config.create_browser()
        print(f"[PASS] Browser created: {type(browser).__name__}")
        return True
    except Exception as e:
        print(f"[FAIL] BrowserConfig error: {e}")
        return False


async def test_multi_tab_agent():
    """Test MultiTabAgent with a simple task."""
    print("\n" + "="*60)
    print("TEST: MultiTabAgent...")
    print("="*60)

    try:
        from advanced_browser_services import MultiTabAgent
        from advanced_browser_services.base_service import BrowserConfig

        config = BrowserConfig(headless=True)
        agent = MultiTabAgent(browser_config=config)
        print("[PASS] MultiTabAgent instantiated")

        # Run a simple task
        result = await agent.run(
            task="Go to example.com and tell me the page title",
            max_steps=5
        )
        print(f"[PASS] Task completed: success={result.get('success', False)}")
        print(f"[INFO] Summary: {result.get('summary', 'N/A')[:100]}...")
        return result.get('success', False)
    except Exception as e:
        print(f"[FAIL] MultiTabAgent error: {e}")
        return False


async def test_data_extraction_agent():
    """Test DataExtractionAgent with a simple extraction."""
    print("\n" + "="*60)
    print("TEST: DataExtractionAgent...")
    print("="*60)

    try:
        from advanced_browser_services import DataExtractionAgent
        from advanced_browser_services.base_service import BrowserConfig

        config = BrowserConfig(headless=True)
        agent = DataExtractionAgent(browser_config=config)
        print("[PASS] DataExtractionAgent instantiated")

        # Run extraction on example.com
        result = await agent.extract(
            url="https://example.com",
            data_schema={"title": "Page title", "description": "Main content text"},
            max_steps=10
        )
        print(f"[PASS] Extraction completed: success={result.get('success', False)}")
        print(f"[INFO] Extracted data: {result.get('extracted_data', {})}")
        return result.get('success', False)
    except Exception as e:
        print(f"[FAIL] DataExtractionAgent error: {e}")
        return False


async def test_research_agent():
    """Test ResearchAgent with a simple research task."""
    print("\n" + "="*60)
    print("TEST: ResearchAgent...")
    print("="*60)

    try:
        from advanced_browser_services import ResearchAgent
        from advanced_browser_services.base_service import BrowserConfig

        config = BrowserConfig(headless=True)
        agent = ResearchAgent(browser_config=config)
        print("[PASS] ResearchAgent instantiated")

        # Run a simple research task
        result = await agent.research_topic(
            topic="Python programming language",
            depth="shallow",
            max_sources=1,
            max_steps=10
        )
        print(f"[PASS] Research completed: success={result.get('success', False)}")
        print(f"[INFO] Found {result.get('num_findings', 0)} findings from {result.get('num_sources', 0)} sources")
        return result.get('success', False)
    except Exception as e:
        print(f"[FAIL] ResearchAgent error: {e}")
        return False


async def test_advanced_browser_service():
    """Test the unified AdvancedBrowserService facade."""
    print("\n" + "="*60)
    print("TEST: AdvancedBrowserService (Unified Facade)...")
    print("="*60)

    try:
        from advanced_browser_services import AdvancedBrowserService

        service = AdvancedBrowserService(headless=True)
        print("[PASS] AdvancedBrowserService instantiated")

        # Run a simple task
        result = await service.run_task(
            task="Go to example.com and tell me what you see",
            max_steps=5
        )
        print(f"[PASS] Task completed: success={result.success}")
        print(f"[INFO] Task type: {result.task_type}")
        print(f"[INFO] Summary: {result.summary[:100] if result.summary else 'N/A'}...")
        return result.success
    except Exception as e:
        print(f"[FAIL] AdvancedBrowserService error: {e}")
        return False


async def test_parallel_agents():
    """Test ParallelAgentRunner with simple tasks."""
    print("\n" + "="*60)
    print("TEST: ParallelAgentRunner...")
    print("="*60)

    try:
        from advanced_browser_services import ParallelAgentRunner, AgentTask
        from advanced_browser_services.base_service import BrowserConfig

        config = BrowserConfig(headless=True)
        runner = ParallelAgentRunner(browser_config=config, max_concurrent_agents=2)
        print("[PASS] ParallelAgentRunner instantiated")

        # Run parallel tasks
        tasks = [
            AgentTask(task_id="task1", description="Go to example.com and get the title", max_steps=5),
            AgentTask(task_id="task2", description="Go to example.org and get the title", max_steps=5),
        ]

        results = await runner.run_parallel(tasks)
        success_count = sum(1 for r in results if r.success)
        print(f"[PASS] Parallel execution completed: {success_count}/{len(tasks)} tasks succeeded")
        for r in results:
            print(f"[INFO] Task {r.task_id}: success={r.success}")
        return success_count > 0
    except Exception as e:
        print(f"[FAIL] ParallelAgentRunner error: {e}")
        return False


async def run_all_tests():
    """Run all tests."""
    print("\n" + "#"*60)
    print("# ADVANCED BROWSER SERVICES - TEST SUITE")
    print("#"*60)

    results = {}

    # Synchronous tests
    results["imports"] = test_imports()
    if not results["imports"]:
        print("\n[FATAL] Import test failed. Cannot continue.")
        return results

    results["llm_init"] = test_llm_initialization()
    results["browser_config"] = test_browser_config()

    # Async tests - Core agents (only non-redundant with browser-use)
    results["multi_tab_agent"] = await test_multi_tab_agent()
    results["data_extraction"] = await test_data_extraction_agent()
    results["research_agent"] = await test_research_agent()
    results["advanced_service"] = await test_advanced_browser_service()
    results["parallel_agents"] = await test_parallel_agents()

    # Summary
    print("\n" + "#"*60)
    print("# TEST SUMMARY")
    print("#"*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, passed_test in results.items():
        status = "[PASS]" if passed_test else "[FAIL]"
        print(f"  {status} {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print("#"*60)

    return results


if __name__ == "__main__":
    asyncio.run(run_all_tests())
