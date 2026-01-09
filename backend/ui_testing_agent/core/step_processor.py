"""
Step Processor - Processes browser-use AgentHistory into structured data.
"""

import re
from typing import Any, Optional

from ..models.processed_action import ProcessedAction
from ..models.processed_step import ProcessedStep
from ..models.test_scenario import TestScenario
from .selector_extractor import SelectorExtractor


class StepProcessor:
    """
    Processes browser-use AgentHistory steps into structured models.

    Handles:
    - Extracting actions from AgentOutput
    - Mapping results to actions
    - Extracting selectors from interacted elements
    - Detecting scenario boundaries
    """

    # Patterns for detecting scenario boundaries in agent's thinking/goals
    SCENARIO_PATTERNS = [
        r'(?:test|testing|verify|check|scenario)\s*[:\-]?\s*(.+)',
        r'(?:happy|error|edge|validation)\s+(?:path|case|scenario)',
        r'SCENARIO\s+\[?([^\]]+)\]?',
        r'now\s+(?:testing|trying|checking)\s+(.+)',
    ]

    def __init__(self):
        self.selector_extractor = SelectorExtractor()

    def process_step(self, history_step: Any, step_index: int) -> ProcessedStep:
        """
        Process a single AgentHistory step into ProcessedStep.

        Args:
            history_step: AgentHistory from browser-use
            step_index: Index of this step in the sequence

        Returns:
            ProcessedStep with all extracted data
        """
        # Extract model output data
        model_output = self._get_attr(history_step, 'model_output')
        thinking = self._get_attr(model_output, 'thinking') if model_output else None
        next_goal = self._get_attr(model_output, 'next_goal') if model_output else None
        evaluation = self._get_attr(model_output, 'evaluation_previous_goal') if model_output else None
        memory = self._get_attr(model_output, 'memory') if model_output else None

        # Extract actions and results
        actions = self._get_attr(model_output, 'action') if model_output else []
        results = self._get_attr(history_step, 'result') or []

        # Extract state data
        state = self._get_attr(history_step, 'state')
        page_url = self._get_attr(state, 'url') or '' if state else ''
        page_title = self._get_attr(state, 'title') or '' if state else ''
        screenshot_path = self._get_attr(state, 'screenshot_path') if state else None
        interacted_elements = self._get_attr(state, 'interacted_element') if state else []

        # Extract metadata
        metadata = self._get_attr(history_step, 'metadata')
        timestamp = self._get_attr(metadata, 'step_start_time') if metadata else None
        duration = self._get_attr(metadata, 'duration_seconds') if metadata else None

        # Process each action
        processed_actions = []
        for i, action in enumerate(actions or []):
            result = results[i] if i < len(results or []) else None
            interacted = interacted_elements[i] if i < len(interacted_elements or []) else None

            processed_action = self._process_action(action, result, interacted)
            processed_actions.append(processed_action)

        # Detect scenario boundary
        is_scenario_start, scenario_name = self._detect_scenario_boundary(
            thinking, next_goal, evaluation
        )

        return ProcessedStep(
            step_number=step_index,
            thinking=thinking,
            goal=next_goal,
            evaluation=evaluation,
            memory=memory,
            actions=processed_actions,
            page_url=page_url,
            page_title=page_title,
            screenshot_path=screenshot_path,
            timestamp=timestamp,
            duration_ms=int(duration * 1000) if duration else None,
            is_scenario_start=is_scenario_start,
            scenario_name=scenario_name,
        )

    def _process_action(
        self,
        action: Any,
        result: Any,
        interacted_element: Any
    ) -> ProcessedAction:
        """Process a single action into ProcessedAction."""
        # Get action type from class name
        action_type = type(action).__name__.replace('Action', '').lower() if action else 'unknown'

        # Get action params
        if hasattr(action, 'model_dump'):
            action_params = action.model_dump()
        elif hasattr(action, '__dict__'):
            action_params = action.__dict__
        elif isinstance(action, dict):
            action_params = action
        else:
            action_params = {}

        # Extract selector info
        selector_info = self.selector_extractor.extract(interacted_element)

        # Extract element index from action params
        element_index = action_params.get('index')

        # Extract result data
        success = self._get_attr(result, 'success') if result else None
        error = self._get_attr(result, 'error') if result else None
        extracted_content = self._get_attr(result, 'extracted_content') if result else None

        # Determine if this is an assertion
        is_assertion = action_type == 'extract' and extracted_content is not None

        return ProcessedAction(
            action_type=action_type,
            action_params=action_params,
            selector_info=selector_info,
            element_index=element_index,
            success=success,
            error=error,
            extracted_content=extracted_content,
            is_assertion=is_assertion,
            assertion_description=self._get_attr(action_params, 'query') if is_assertion else None,
        )

    def _detect_scenario_boundary(
        self,
        thinking: Optional[str],
        goal: Optional[str],
        evaluation: Optional[str]
    ) -> tuple[bool, Optional[str]]:
        """
        Detect if this step starts a new test scenario.

        Returns:
            Tuple of (is_scenario_start, scenario_name)
        """
        text_to_check = ' '.join(filter(None, [thinking, goal, evaluation]))

        if not text_to_check:
            return False, None

        text_lower = text_to_check.lower()

        # Check for explicit scenario markers
        if 'scenario' in text_lower:
            # Try to extract scenario name
            match = re.search(r'SCENARIO\s+\[?([^\]:\n]+)\]?', text_to_check, re.IGNORECASE)
            if match:
                return True, match.group(1).strip()

        # Check for common test type markers
        for marker in ['happy path', 'error case', 'edge case', 'validation', 'negative test']:
            if marker in text_lower:
                return True, marker.title()

        # Check for "now testing" patterns
        match = re.search(
            r'(?:now|going to|will)\s+(?:test|try|check|verify)\s+(.+?)(?:\.|$)',
            text_to_check,
            re.IGNORECASE
        )
        if match:
            return True, match.group(1).strip()[:50]

        return False, None

    def group_into_scenarios(self, steps: list[ProcessedStep]) -> list[TestScenario]:
        """
        Group processed steps into logical test scenarios.

        Uses scenario boundaries detected during step processing,
        plus heuristics for grouping related steps.
        """
        if not steps:
            return []

        scenarios = []
        current_steps = []
        current_name = "Initial Exploration"
        scenario_count = 0

        for step in steps:
            # Check if this step starts a new scenario
            if step.is_scenario_start and step.scenario_name:
                # Save previous scenario if it has steps
                if current_steps:
                    scenario_count += 1
                    scenarios.append(self._create_scenario(
                        f"TST-{scenario_count:03d}",
                        current_name,
                        current_steps
                    ))
                    current_steps = []

                current_name = step.scenario_name

            current_steps.append(step)

            # Also split on "done" actions
            if step.is_done_step:
                scenario_count += 1
                scenarios.append(self._create_scenario(
                    f"TST-{scenario_count:03d}",
                    current_name,
                    current_steps
                ))
                current_steps = []
                current_name = "Continued Testing"

        # Don't forget the last scenario
        if current_steps:
            scenario_count += 1
            scenarios.append(self._create_scenario(
                f"TST-{scenario_count:03d}",
                current_name,
                current_steps
            ))

        return scenarios

    def _create_scenario(
        self,
        scenario_id: str,
        name: str,
        steps: list[ProcessedStep]
    ) -> TestScenario:
        """Create a TestScenario from a group of steps."""
        # Determine if scenario passed or failed
        passed = True
        failure_reason = None
        failure_step = None

        for step in steps:
            if step.has_failure:
                passed = False
                failure_reason = step.get_errors()[0] if step.get_errors() else "Unknown error"
                failure_step = step.step_number
                break

        # Check for explicit pass/fail in done actions
        for step in steps:
            for action in step.actions:
                if action.action_type == 'done':
                    passed = action.action_params.get('success', True)
                    if not passed:
                        failure_reason = action.action_params.get('text', 'Test failed')

        # Collect screenshots
        screenshots = [s.screenshot_path for s in steps if s.screenshot_path]

        # Calculate duration
        durations = [s.duration_ms for s in steps if s.duration_ms]
        total_duration = sum(durations) if durations else None

        # Determine scenario type
        name_lower = name.lower()
        if 'happy' in name_lower or 'success' in name_lower:
            scenario_type = 'happy_path'
        elif 'error' in name_lower or 'invalid' in name_lower or 'validation' in name_lower:
            scenario_type = 'validation'
        elif 'edge' in name_lower or 'boundary' in name_lower:
            scenario_type = 'edge_case'
        else:
            scenario_type = 'general'

        return TestScenario(
            scenario_id=scenario_id,
            name=name,
            description=f"Testing: {name}",
            scenario_type=scenario_type,
            steps=steps,
            passed=passed,
            failure_reason=failure_reason,
            failure_step=failure_step,
            screenshots=screenshots,
            start_url=steps[0].page_url if steps else None,
            end_url=steps[-1].page_url if steps else None,
            duration_ms=total_duration,
        )

    def _get_attr(self, obj: Any, attr: str) -> Any:
        """Safely get attribute from object or dict."""
        if obj is None:
            return None
        if hasattr(obj, attr):
            return getattr(obj, attr)
        if isinstance(obj, dict):
            return obj.get(attr)
        return None
