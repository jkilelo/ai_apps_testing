"""
Selector information model for element identification.
"""

from typing import Optional
from pydantic import BaseModel, Field


class SelectorInfo(BaseModel):
    """
    Multiple selector strategies for an element.

    Extracted from browser-use's DOMInteractedElement to enable
    self-healing selector fallbacks in generated Playwright code.
    """

    # Best selectors (prioritized)
    data_testid: Optional[str] = Field(
        default=None,
        description="data-testid or data-test attribute (most stable)"
    )
    element_id: Optional[str] = Field(
        default=None,
        description="Element id attribute"
    )
    name: Optional[str] = Field(
        default=None,
        description="Element name attribute (for form fields)"
    )
    aria_label: Optional[str] = Field(
        default=None,
        description="aria-label attribute (accessibility)"
    )

    # Fallback selectors
    xpath: Optional[str] = Field(
        default=None,
        description="Full XPath from browser-use (e.g., html/body/div[2]/button[1])"
    )
    text_content: Optional[str] = Field(
        default=None,
        description="Visible text content of element"
    )
    tag_name: Optional[str] = Field(
        default=None,
        description="HTML tag name (button, input, a, etc.)"
    )
    classes: list[str] = Field(
        default_factory=list,
        description="CSS classes on the element"
    )

    # Additional selectors
    role: Optional[str] = Field(
        default=None,
        description="ARIA role attribute"
    )
    placeholder: Optional[str] = Field(
        default=None,
        description="Placeholder text (for inputs)"
    )
    href: Optional[str] = Field(
        default=None,
        description="Link href (for anchors)"
    )

    # Stability metadata
    element_hash: Optional[int] = Field(
        default=None,
        description="Stable hash from browser-use for element identification"
    )

    def to_playwright_selectors(self) -> list[str]:
        """
        Generate prioritized list of Playwright selectors.

        Priority order:
        1. data-testid (most stable, test-specific)
        2. id (unique identifier)
        3. name (form fields)
        4. aria-label (accessibility)
        5. role + text (semantic)
        6. tag + text (for buttons/links)
        7. placeholder (for inputs)
        8. xpath (last resort)
        """
        selectors = []

        if self.data_testid:
            selectors.append(f'[data-testid="{self.data_testid}"]')

        if self.element_id:
            selectors.append(f'#{self.element_id}')

        if self.name:
            selectors.append(f'[name="{self.name}"]')

        if self.aria_label:
            selectors.append(f'[aria-label="{self.aria_label}"]')

        if self.role and self.text_content:
            # Playwright role selector
            selectors.append(f'role={self.role}[name="{self.text_content}"]')

        if self.text_content and self.tag_name in ['button', 'a']:
            selectors.append(f'{self.tag_name}:has-text("{self.text_content}")')

        if self.placeholder and self.tag_name == 'input':
            selectors.append(f'input[placeholder="{self.placeholder}"]')

        # XPath as last resort
        if self.xpath and len(selectors) < 3:
            selectors.append(f'xpath={self.xpath}')

        return selectors if selectors else ['SELECTOR_NOT_FOUND']

    def get_best_selector(self) -> str:
        """Get the single best selector for this element."""
        selectors = self.to_playwright_selectors()
        return selectors[0] if selectors else 'SELECTOR_NOT_FOUND'

    def get_description(self) -> str:
        """Get human-readable description of the element."""
        parts = []
        if self.tag_name:
            parts.append(self.tag_name)
        if self.text_content:
            parts.append(f'"{self.text_content}"')
        if self.aria_label:
            parts.append(f'[{self.aria_label}]')
        return ' '.join(parts) if parts else 'element'
