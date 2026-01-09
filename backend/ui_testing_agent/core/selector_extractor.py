"""
Selector Extractor - Extracts multiple selector strategies from DOM elements.
"""

from typing import Optional, Any

from ..models.selector_info import SelectorInfo


class SelectorExtractor:
    """
    Extracts selector information from browser-use DOMInteractedElement.

    Provides multiple selector strategies for self-healing Playwright tests.
    """

    # Attributes to look for when extracting selectors
    SELECTOR_ATTRIBUTES = [
        'data-testid',
        'data-test',
        'data-cy',
        'data-selenium',
        'id',
        'name',
        'aria-label',
        'aria-labelledby',
        'placeholder',
        'title',
        'alt',
        'role',
        'type',
        'href',
        'class',
    ]

    def extract(self, element: Any) -> Optional[SelectorInfo]:
        """
        Extract SelectorInfo from a DOMInteractedElement.

        Args:
            element: DOMInteractedElement from browser-use BrowserStateHistory

        Returns:
            SelectorInfo with multiple selector strategies, or None if element is None
        """
        if element is None:
            return None

        # Handle both object and dict representations
        if hasattr(element, 'attributes'):
            attrs = element.attributes or {}
            node_name = getattr(element, 'node_name', None)
            node_value = getattr(element, 'node_value', None)
            xpath = getattr(element, 'x_path', None)
            element_hash = getattr(element, 'element_hash', None)
        elif isinstance(element, dict):
            attrs = element.get('attributes', {}) or {}
            node_name = element.get('node_name')
            node_value = element.get('node_value')
            xpath = element.get('x_path')
            element_hash = element.get('element_hash')
        else:
            return None

        return SelectorInfo(
            # Primary selectors
            data_testid=attrs.get('data-testid') or attrs.get('data-test'),
            element_id=attrs.get('id'),
            name=attrs.get('name'),
            aria_label=attrs.get('aria-label'),

            # Fallback selectors
            xpath=xpath,
            text_content=node_value if node_value else attrs.get('ax_name'),
            tag_name=node_name.lower() if node_name else None,
            classes=self._extract_classes(attrs.get('class')),

            # Additional
            role=attrs.get('role'),
            placeholder=attrs.get('placeholder'),
            href=attrs.get('href'),

            # Stability
            element_hash=element_hash,
        )

    def _extract_classes(self, class_string: Optional[str]) -> list[str]:
        """Extract list of classes from class attribute string."""
        if not class_string:
            return []
        return [c.strip() for c in class_string.split() if c.strip()]

    def extract_from_history_step(self, state: Any, action_index: int = 0) -> Optional[SelectorInfo]:
        """
        Extract selector from BrowserStateHistory's interacted_element list.

        Args:
            state: BrowserStateHistory from AgentHistory.state
            action_index: Index of the action to get element for

        Returns:
            SelectorInfo for the interacted element
        """
        if state is None:
            return None

        # Handle object or dict
        if hasattr(state, 'interacted_element'):
            elements = state.interacted_element
        elif isinstance(state, dict):
            elements = state.get('interacted_element', [])
        else:
            return None

        if not elements or action_index >= len(elements):
            return None

        element = elements[action_index]
        return self.extract(element)

    def build_playwright_selector(self, info: SelectorInfo, max_fallbacks: int = 4) -> str:
        """
        Build a single Playwright selector expression with fallbacks.

        This creates a selector that tries multiple strategies.
        """
        selectors = info.to_playwright_selectors()[:max_fallbacks]

        if len(selectors) == 1:
            return selectors[0]

        # For multiple selectors, use the first one as primary
        # The fallbacks will be handled by the helper method in generated code
        return selectors[0]

    def build_selector_list_code(
        self,
        info: SelectorInfo,
        max_fallbacks: int = 4
    ) -> str:
        """
        Build Python code for a list of fallback selectors.

        Returns code like: ['[data-testid="btn"]', '#submit', 'button:has-text("Submit")']
        """
        selectors = info.to_playwright_selectors()[:max_fallbacks]

        # Escape quotes properly for Python string
        escaped = []
        for sel in selectors:
            if '"' in sel:
                escaped.append(f"'{sel}'")
            else:
                escaped.append(f'"{sel}"')

        return f"[{', '.join(escaped)}]"
