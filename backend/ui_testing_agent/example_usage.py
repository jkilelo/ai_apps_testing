"""
Example usage of the UI Testing Agent.

This script demonstrates how to use the UI Testing Agent to perform
exploratory testing on a web application and generate all artifacts.

Prerequisites:
    pip install browser-use langchain-google-genai playwright pydantic pyyaml
    playwright install chromium
    export GOOGLE_API_KEY="your-api-key"

Usage:
    python -m ui_testing_agent.example_usage
"""

import asyncio
from ui_testing_agent import UITestingService, OutputConfig, run_ui_test


async def example_basic():
    """Basic usage example with default settings."""
    print("=" * 60)
    print("Basic Usage Example")
    print("=" * 60)

    result = await run_ui_test(
        task="Test the search functionality",
        url="https://www.google.com",
        output_dir="./test_outputs/basic_test",
        max_steps=10,
    )

    print(f"\nResults:")
    print(f"  Scenarios: {result.total_scenarios}")
    print(f"  Passed: {result.passed}")
    print(f"  Failed: {result.failed}")
    print(f"  Pass Rate: {result.pass_rate:.1f}%")
    print(f"\nArtifacts:")
    print(f"  Playwright Tests: {result.playwright_code_path}")
    print(f"  HTML Report: {result.html_report_path}")


async def example_custom_config():
    """Example with custom configuration."""
    print("=" * 60)
    print("Custom Configuration Example")
    print("=" * 60)

    # Configure what artifacts to generate
    config = OutputConfig(
        output_directory="./test_outputs/custom_test",
        # Playwright code generation
        generate_playwright_code=True,
        include_selector_fallbacks=True,  # Self-healing selectors
        max_selectors_per_element=4,
        # Test case documentation
        generate_test_cases=True,
        test_case_format="markdown",  # json, yaml, markdown, gherkin
        # Reports
        generate_html_report=True,
        generate_json_report=True,
        # Screenshots and video
        save_screenshots=True,
        capture_video=True,
        # Raw data
        save_raw_history=True,
    )

    # Create service with custom config
    service = UITestingService(
        output_config=config,
        model="gemini-3-flash-preview",  # Or any supported model
        headless=False,  # Show browser window
    )

    # Run exploratory testing
    result = await service.explore_and_test(
        task="Test the login form with valid and invalid credentials",
        url="https://example.com/login",
        max_steps=30,
        max_actions_per_step=3,
    )

    # Access all generated artifacts
    print(f"\nGenerated Artifacts:")
    print(f"  Output Directory: {result.output_directory}")
    print(f"  Playwright Code: {result.playwright_code_path}")
    print(f"  Test Cases: {result.test_cases_path}")
    print(f"  HTML Report: {result.html_report_path}")
    print(f"  JSON Report: {result.json_report_path}")
    print(f"  Screenshots: {result.screenshots_dir}")
    print(f"  Video: {result.video_path}")

    return result


async def example_access_scenarios():
    """Example showing how to access scenario data."""
    print("=" * 60)
    print("Accessing Scenario Data Example")
    print("=" * 60)

    result = await run_ui_test(
        task="Test adding items to cart",
        url="https://shop.example.com",
        output_dir="./test_outputs/scenario_example",
        max_steps=20,
    )

    # Iterate through scenarios
    for scenario in result.scenarios:
        status = "PASSED" if scenario.passed else "FAILED"
        print(f"\n{scenario.scenario_id}: {scenario.name} [{status}]")
        print(f"  Type: {scenario.scenario_type}")
        print(f"  Duration: {scenario.duration_ms}ms")

        if scenario.failure_reason:
            print(f"  Failure: {scenario.failure_reason}")

        # Access steps within scenario
        for step in scenario.steps:
            print(f"  Step {step.step_number}: {step.goal}")
            for action in step.actions:
                icon = "OK" if action.success else "FAIL"
                print(f"    [{icon}] {action.get_description()}")


if __name__ == "__main__":
    # Run the basic example
    asyncio.run(example_basic())
