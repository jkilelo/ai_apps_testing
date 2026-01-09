"""
Processed action model - represents a single action from AgentHistory.
"""

from typing import Optional, Any
from pydantic import BaseModel, Field

from .selector_info import SelectorInfo


class ProcessedAction(BaseModel):
    """
    Single action extracted and processed from browser-use AgentHistory.

    This represents one atomic action (click, fill, navigate, etc.)
    with all relevant metadata for code generation.
    """

    action_type: str = Field(
        description="Action type: click, input, navigate, scroll, extract, done, etc."
    )
    action_params: dict[str, Any] = Field(
        default_factory=dict,
        description="Original action parameters from browser-use"
    )

    # Element targeting
    selector_info: Optional[SelectorInfo] = Field(
        default=None,
        description="Selector information extracted from DOMInteractedElement"
    )
    element_index: Optional[int] = Field(
        default=None,
        description="Original element index used by browser-use"
    )

    # Execution result
    success: Optional[bool] = Field(
        default=None,
        description="Whether the action succeeded"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if action failed"
    )
    extracted_content: Optional[str] = Field(
        default=None,
        description="Content extracted (for extract actions)"
    )

    # For assertions
    is_assertion: bool = Field(
        default=False,
        description="Whether this action represents a verification/assertion"
    )
    assertion_description: Optional[str] = Field(
        default=None,
        description="What was being verified (for code generation comments)"
    )

    def to_playwright_code(self) -> Optional[str]:
        """
        Convert this action to Playwright Python code.

        Returns None if action type is not supported for code generation.
        """
        if self.action_type == 'navigate':
            url = self.action_params.get('url', '')
            return f'page.goto("{url}")'

        elif self.action_type == 'clickelement':
            if self.selector_info:
                selector = self.selector_info.get_best_selector()
                return f'page.click("{selector}")'
            return None

        elif self.action_type == 'inputtext':
            text = self.action_params.get('text', '')
            if self.selector_info:
                selector = self.selector_info.get_best_selector()
                return f'page.fill("{selector}", "{text}")'
            return None

        elif self.action_type == 'scroll':
            direction = 'down' if self.action_params.get('down', True) else 'up'
            pages = self.action_params.get('pages', 1)
            return f'# Scroll {direction} {pages} page(s)'

        elif self.action_type == 'sendkeys':
            keys = self.action_params.get('keys', '')
            return f'page.keyboard.press("{keys}")'

        elif self.action_type == 'wait':
            seconds = self.action_params.get('seconds', 3)
            return f'page.wait_for_timeout({seconds * 1000})'

        elif self.action_type == 'goback':
            return 'page.go_back()'

        elif self.action_type == 'extract':
            query = self.action_params.get('query', '')
            if self.extracted_content:
                return f'# Extracted: {self.extracted_content[:100]}...'
            return f'# Extract: {query}'

        elif self.action_type == 'done':
            success = self.action_params.get('success', True)
            text = self.action_params.get('text', '')[:100]
            return f'# Test {"PASSED" if success else "FAILED"}: {text}'

        elif self.action_type == 'selectdropdownoption':
            text = self.action_params.get('text', '')
            if self.selector_info:
                selector = self.selector_info.get_best_selector()
                return f'page.select_option("{selector}", label="{text}")'
            return None

        return None

    def get_description(self) -> str:
        """Get human-readable description of this action."""
        if self.action_type == 'navigate':
            return f"Navigate to {self.action_params.get('url', 'URL')}"
        elif self.action_type == 'clickelement':
            elem = self.selector_info.get_description() if self.selector_info else 'element'
            return f"Click {elem}"
        elif self.action_type == 'inputtext':
            text = self.action_params.get('text', '')[:30]
            return f"Type '{text}'"
        elif self.action_type == 'extract':
            return f"Extract: {self.action_params.get('query', 'content')[:50]}"
        elif self.action_type == 'done':
            return f"Complete: {'Success' if self.action_params.get('success') else 'Failed'}"
        else:
            return f"{self.action_type}: {str(self.action_params)[:50]}"
