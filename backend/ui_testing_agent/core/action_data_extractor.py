"""
Action Data Extractor - Extracts rich action data from browser-use 0.11.x history.

This module captures ALL information needed to replay actions offline:
- Action type and parameters
- Full element selector information from interacted_element
- Page URL and state
- Success/failure status
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ElementSelectors:
    """All possible selectors for an element, in priority order."""

    # Priority 1: data-testid (most reliable)
    data_testid: Optional[str] = None

    # Priority 2: id (unique but sometimes dynamic)
    element_id: Optional[str] = None

    # Priority 3: aria-label (accessibility, stable)
    aria_label: Optional[str] = None

    # Priority 4: name attribute (good for form fields)
    name: Optional[str] = None

    # Priority 5: role (for getByRole)
    role: Optional[str] = None

    # Priority 6: text/value (for getByText)
    text: Optional[str] = None
    value: Optional[str] = None

    # Priority 7: title attribute
    title: Optional[str] = None

    # Priority 8: placeholder (for inputs)
    placeholder: Optional[str] = None

    # Priority 9: CSS class (can be brittle)
    css_class: Optional[str] = None

    # Priority 10: XPath (last resort)
    xpath: Optional[str] = None

    # Additional info
    tag_name: Optional[str] = None
    element_type: Optional[str] = None  # input type

    def get_best_playwright_selector(self) -> str:
        """Return the most reliable Playwright selector."""

        # Priority 1: data-testid
        if self.data_testid:
            return f'[data-testid="{self.data_testid}"]'

        # Priority 2: id
        if self.element_id:
            return f'#{self.element_id}'

        # Priority 3: aria-label
        if self.aria_label:
            return f'[aria-label="{self.aria_label}"]'

        # Priority 4: name
        if self.name:
            return f'[name="{self.name}"]'

        # Priority 5: role + text/value (getByRole style)
        if self.role and (self.text or self.value):
            name = self.text or self.value
            return f'role={self.role}[name="{name}"]'

        # Priority 6: text content
        if self.text:
            return f'text="{self.text}"'

        # Priority 7: title
        if self.title:
            return f'[title="{self.title}"]'

        # Priority 8: placeholder
        if self.placeholder:
            return f'[placeholder="{self.placeholder}"]'

        # Priority 9: XPath
        if self.xpath:
            return f'xpath={self.xpath}'

        return ""

    def get_fallback_selectors(self, max_count: int = 4) -> list[str]:
        """Return multiple selector options for self-healing."""
        selectors = []

        if self.data_testid:
            selectors.append(f'[data-testid="{self.data_testid}"]')
        if self.element_id:
            selectors.append(f'#{self.element_id}')
        if self.aria_label:
            selectors.append(f'[aria-label="{self.aria_label}"]')
        if self.name:
            selectors.append(f'[name="{self.name}"]')
        if self.role and (self.text or self.value):
            name = self.text or self.value
            selectors.append(f'role={self.role}[name="{name}"]')
        if self.text and not (self.role and self.text):
            selectors.append(f'text="{self.text}"')
        if self.title:
            selectors.append(f'[title="{self.title}"]')
        if self.xpath:
            selectors.append(f'xpath={self.xpath}')

        return selectors[:max_count]


@dataclass
class ExtractedAction:
    """Complete action data extracted from browser-use history."""

    # Action info
    action_type: str  # navigate, click, input, scroll, etc.
    action_params: dict[str, Any] = field(default_factory=dict)

    # Element selectors (if applicable)
    selectors: Optional[ElementSelectors] = None

    # Context
    page_url: str = ""
    page_title: str = ""

    # Result
    success: bool = True
    error: Optional[str] = None
    extracted_content: Optional[str] = None

    # Metadata
    step_number: int = 0
    action_index: int = 0  # Index within step (for multi-action steps)

    def to_playwright_code(self) -> str:
        """Convert this action to Playwright code."""

        if self.action_type == "navigate":
            url = self.action_params.get("url", "")
            return f'page.goto("{url}")'

        elif self.action_type == "click":
            if self.selectors:
                selector = self.selectors.get_best_playwright_selector()
                if selector:
                    return f'page.click("{selector}")'
            return f'# Click action - selector not captured'

        elif self.action_type == "input":
            text = self.action_params.get("text", "")
            # Escape quotes in text
            text = text.replace('"', '\\"')
            if self.selectors:
                selector = self.selectors.get_best_playwright_selector()
                if selector:
                    return f'page.fill("{selector}", "{text}")'
            return f'# Input action - selector not captured'

        elif self.action_type == "scroll":
            direction = self.action_params.get("direction", "down")
            amount = self.action_params.get("amount", 500)
            if direction == "down":
                return f'page.mouse.wheel(0, {amount})'
            else:
                return f'page.mouse.wheel(0, -{amount})'

        elif self.action_type == "select_option":
            option = self.action_params.get("option", "")
            if self.selectors:
                selector = self.selectors.get_best_playwright_selector()
                if selector:
                    return f'page.select_option("{selector}", "{option}")'
            return f'# Select option - selector not captured'

        elif self.action_type == "wait":
            seconds = self.action_params.get("seconds", 1)
            return f'page.wait_for_timeout({int(seconds * 1000)})'

        elif self.action_type == "go_back":
            return 'page.go_back()'

        elif self.action_type == "extract":
            # Convert to assertion/verification
            query = self.action_params.get("query", "")
            if self.extracted_content:
                # Generate a soft assertion
                content_preview = self.extracted_content[:50].replace('"', '\\"')
                return f'# Verified: {query}\n        # Content: "{content_preview}..."'
            return f'# Extract: {query}'

        elif self.action_type == "done":
            success = self.action_params.get("success", True)
            text = self.action_params.get("text", "")[:80]
            return f'# Test {"completed" if success else "failed"}: {text}'

        else:
            return f'# Unknown action: {self.action_type}'


class ActionDataExtractor:
    """
    Extracts rich action data from browser-use AgentHistoryList.

    This is the key component that captures ALL information needed
    to replay actions offline in Playwright.
    """

    def extract_all_actions(self, history) -> list[ExtractedAction]:
        """
        Extract all actions from the agent history.

        Args:
            history: Either AgentHistoryList object or raw dict from model_dump()

        Returns a flat list of ExtractedAction with full selector info.
        """
        all_actions = []

        # Handle both object and dict formats
        if history is None:
            return all_actions

        # Get the history list
        if hasattr(history, 'history'):
            history_list = history.history
        elif isinstance(history, dict) and 'history' in history:
            history_list = history['history']
        else:
            return all_actions

        if not history_list:
            return all_actions

        for step_idx, step in enumerate(history_list):
            step_actions = self._extract_step_actions(step, step_idx)
            all_actions.extend(step_actions)

        return all_actions

    def _extract_step_actions(
        self, step, step_number: int
    ) -> list[ExtractedAction]:
        """Extract all actions from a single step (supports both object and dict)."""
        actions = []

        # Get model_output - handle both object and dict
        if hasattr(step, 'model_output'):
            model_output = step.model_output
        elif isinstance(step, dict):
            model_output = step.get('model_output')
        else:
            return actions

        if not model_output:
            return actions

        # Get actions list from model_output
        if hasattr(model_output, 'action'):
            action_list = model_output.action
        elif isinstance(model_output, dict):
            action_list = model_output.get('action', [])
        else:
            return actions

        if not action_list:
            return actions

        # Get state (contains interacted elements)
        if hasattr(step, 'state'):
            state = step.state
        elif isinstance(step, dict):
            state = step.get('state')
        else:
            state = None

        # Get interacted_elements from state
        interacted_elements = []
        if state:
            if hasattr(state, 'interacted_element'):
                interacted_elements = state.interacted_element or []
            elif isinstance(state, dict):
                interacted_elements = state.get('interacted_element', []) or []

        # Get results (contains success/error info)
        if hasattr(step, 'result'):
            results = step.result or []
        elif isinstance(step, dict):
            results = step.get('result', []) or []
        else:
            results = []

        # Process each action
        for action_idx, action_model in enumerate(action_list):
            # Parse action type and params
            action_type, action_params = self._parse_action_model(action_model)

            # Get corresponding interacted element
            element = None
            if interacted_elements and action_idx < len(interacted_elements):
                element = interacted_elements[action_idx]

            # Get corresponding result
            result = None
            if results and action_idx < len(results):
                result = results[action_idx]

            # Extract selectors from element
            selectors = self._extract_selectors(element) if element else None

            # Get URL and title from state
            page_url = ""
            page_title = ""
            if state:
                if hasattr(state, 'url'):
                    page_url = state.url or ""
                elif isinstance(state, dict):
                    page_url = state.get('url', "") or ""
                if hasattr(state, 'title'):
                    page_title = state.title or ""
                elif isinstance(state, dict):
                    page_title = state.get('title', "") or ""

            # Get result info
            success = True
            error = None
            extracted_content = None
            if result:
                if hasattr(result, 'success'):
                    success = result.success if result.success is not None else True
                elif isinstance(result, dict):
                    success = result.get('success', True) if result.get('success') is not None else True
                if hasattr(result, 'error'):
                    error = result.error
                elif isinstance(result, dict):
                    error = result.get('error')
                if hasattr(result, 'extracted_content'):
                    extracted_content = result.extracted_content
                elif isinstance(result, dict):
                    extracted_content = result.get('extracted_content')

            # Build ExtractedAction
            extracted = ExtractedAction(
                action_type=action_type,
                action_params=action_params,
                selectors=selectors,
                page_url=page_url,
                page_title=page_title,
                success=success,
                error=error,
                extracted_content=extracted_content,
                step_number=step_number,
                action_index=action_idx,
            )

            actions.append(extracted)

        return actions

    def _parse_action_model(self, action_model) -> tuple[str, dict]:
        """Parse ActionModel to get action type and parameters."""

        # ActionModel is a dynamic pydantic model
        # It has the action name as a key with params as value
        # e.g., {"click": {"index": 5}} or {"input": {"index": 1, "text": "hello"}}

        if hasattr(action_model, "model_dump"):
            action_dict = action_model.model_dump()
        elif hasattr(action_model, "dict"):
            action_dict = action_model.dict()
        else:
            action_dict = dict(action_model) if action_model else {}

        # Find the action key (it's the only key that's not a metadata field)
        for key, value in action_dict.items():
            if isinstance(value, dict):
                return key, value

        # Fallback
        return "unknown", action_dict

    def _extract_selectors(self, element) -> ElementSelectors:
        """Extract all possible selectors from DOMInteractedElement (object or dict)."""

        selectors = ElementSelectors()

        if element is None:
            return selectors

        # Get attributes dict - handle both object and dict
        attrs = {}
        if hasattr(element, "attributes") and element.attributes:
            attrs = element.attributes
        elif isinstance(element, dict):
            attrs = element.get("attributes", {}) or {}

        # Extract all selector options
        selectors.data_testid = attrs.get("data-testid")
        selectors.element_id = attrs.get("id")
        selectors.aria_label = attrs.get("aria-label")
        selectors.name = attrs.get("name")
        selectors.role = attrs.get("role")
        selectors.title = attrs.get("title")
        selectors.placeholder = attrs.get("placeholder")
        selectors.value = attrs.get("value")
        selectors.css_class = attrs.get("class")
        selectors.element_type = attrs.get("type")

        # Get tag name
        if hasattr(element, "node_name"):
            selectors.tag_name = element.node_name
        elif isinstance(element, dict):
            selectors.tag_name = element.get("node_name")

        # Get text content
        if hasattr(element, "node_value") and element.node_value:
            selectors.text = element.node_value
        elif isinstance(element, dict) and element.get("node_value"):
            selectors.text = element.get("node_value")

        # Get XPath
        if hasattr(element, "x_path"):
            selectors.xpath = element.x_path
        elif isinstance(element, dict):
            selectors.xpath = element.get("x_path")

        return selectors
