"""
UI Testing Agent - Exploratory UI testing with automated artifact generation.

This package provides:
1. ExplorerAgent - AI-powered exploratory testing using browser-use
2. PlaywrightGenerator - Generates offline-runnable Playwright-Python tests
3. TestCaseGenerator - Generates formal test case documentation
4. ReportGenerator - Generates HTML/JSON reports

The "inverted" testing flow:
    1. Explore & Test Live - AI agent explores and tests the application
    2. Record Everything - All actions, results, and screenshots captured
    3. Generate Artifacts - Code, test cases, and reports generated afterward

Usage:
    from ui_testing_agent import UITestingService, OutputConfig

    # Configure outputs
    config = OutputConfig(
        output_directory="./test_outputs",
        generate_playwright_code=True,
        generate_test_cases=True,
        generate_html_report=True,
    )

    # Create service and run
    service = UITestingService(output_config=config)

    result = await service.explore_and_test(
        task="Test the login functionality with valid and invalid credentials",
        url="https://example.com/login"
    )

    # Access results
    print(f"Passed: {result.passed}/{result.total_scenarios}")
    print(f"Playwright tests: {result.playwright_code_path}")
    print(f"HTML report: {result.html_report_path}")

Quick usage:
    from ui_testing_agent import run_ui_test

    result = await run_ui_test(
        task="Test the checkout flow",
        url="https://shop.example.com",
        output_dir="./outputs"
    )
"""

# Main service
from .service import UITestingService, run_ui_test

# Models - public API
from .models.output_config import OutputConfig
from .models.test_session import TestSession
from .models.test_scenario import TestScenario
from .models.processed_step import ProcessedStep
from .models.processed_action import ProcessedAction
from .models.selector_info import SelectorInfo

# Core components
from .core.explorer_agent import ExplorerAgent, DEFAULT_MODEL
from .core.browser_factory import (
    BrowserFactory,
    BrowserResult,
    BrowserConfig,
    BrowserInitializationError,
)

# Generators
from .generators.playwright_generator import PlaywrightGenerator
from .generators.test_case_generator import TestCaseGenerator
from .generators.report_generator import ReportGenerator

__version__ = "0.1.0"

__all__ = [
    # Main entry points
    "UITestingService",
    "run_ui_test",

    # Configuration
    "OutputConfig",
    "DEFAULT_MODEL",

    # Data models
    "TestSession",
    "TestScenario",
    "ProcessedStep",
    "ProcessedAction",
    "SelectorInfo",

    # Core components
    "ExplorerAgent",

    # Browser Factory (Single Source of Truth)
    "BrowserFactory",
    "BrowserResult",
    "BrowserConfig",
    "BrowserInitializationError",

    # Generators
    "PlaywrightGenerator",
    "TestCaseGenerator",
    "ReportGenerator",
]
