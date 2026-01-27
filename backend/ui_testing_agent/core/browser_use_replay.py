"""
Browser-Use Replay System - Offline Regression Testing Without LLM

DESIGN PRINCIPLE: Maximum reuse of browser-use's existing capabilities.
We only build custom logic where browser-use provides no solution.

Browser-use capabilities we USE:
    Recording:
        - generate_css_selector_for_element(node) -> CSS selector
        - node.xpath -> XPath path
        - node.compute_stable_hash() -> SHA256 hash (filters dynamic classes)
        - node.backend_node_id -> CDP backend node ID
        - node.absolute_position -> coordinates
        - node.attributes -> all attributes
        - node.ax_node -> accessibility info

    Replay:
        - browser_session.get_index_by_id(id) -> find by ID
        - browser_session.get_index_by_class(class) -> find by class
        - browser_session.get_dom_element_at_coordinates(x, y) -> find by coordinates
        - browser_session.get_selector_map() -> iterate DOM
        - browser_session.cdp_client -> CSS/XPath evaluation via CDP

Custom logic we BUILD (only where browser-use has gaps):
    - CSS selector evaluation via CDP DOM.querySelector
    - XPath evaluation via CDP DOM.performSearch
    - Hash-based matching (iterate + compute_stable_hash())
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Supported action types."""
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    SEND_KEYS = "send_keys"
    GO_BACK = "go_back"
    GO_FORWARD = "go_forward"
    REFRESH = "refresh"
    WAIT = "wait"
    UPLOAD_FILE = "upload_file"
    SELECT_DROPDOWN = "select_dropdown"


@dataclass
class ElementFingerprint:
    """
    Element identification data captured during recording.

    ALL data is extracted using browser-use's built-in methods:
        - css_selector: from generate_css_selector_for_element()
        - xpath: from node.xpath
        - stable_hash: from node.compute_stable_hash()
        - backend_node_id: from node.backend_node_id
        - coordinates: from node.absolute_position
        - attributes: from node.attributes
    """
    # PRIMARY: Browser-use generated identifiers
    css_selector: Optional[str] = None  # From generate_css_selector_for_element()
    xpath: Optional[str] = None  # From node.xpath
    stable_hash: Optional[int] = None  # From node.compute_stable_hash()
    backend_node_id: Optional[int] = None  # From node.backend_node_id

    # SECONDARY: Key attributes for fallback matching
    # (Extracted from node.attributes, used with browser_session.get_index_by_id/class)
    id: Optional[str] = None
    data_testid: Optional[str] = None
    aria_label: Optional[str] = None
    name: Optional[str] = None
    placeholder: Optional[str] = None
    href: Optional[str] = None
    role: Optional[str] = None

    # STRUCTURAL: Tag and text for verification
    tag_name: Optional[str] = None
    text_content: Optional[str] = None  # From node.ax_node.name
    classes: List[str] = field(default_factory=list)

    # COORDINATE FALLBACK: For browser_session.get_dom_element_at_coordinates()
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None

    # DEBUG: Index at recording time
    recorded_index: Optional[int] = None

    @classmethod
    def from_node(cls, node: Any, index: Optional[int] = None) -> "ElementFingerprint":
        """
        Extract fingerprint using browser-use's built-in methods.

        Uses:
            - browser_use.dom.utils.generate_css_selector_for_element()
            - node.xpath property
            - node.compute_stable_hash() method
            - node.backend_node_id
            - node.absolute_position
            - node.attributes
            - node.ax_node
        """
        if node is None:
            return cls()

        # Import browser-use's CSS selector generator
        try:
            from browser_use.dom.utils import generate_css_selector_for_element
            css_selector = generate_css_selector_for_element(node)
        except Exception as e:
            logger.debug(f"Could not generate CSS selector: {e}")
            css_selector = None

        # Get XPath using browser-use's property
        xpath = None
        try:
            xpath = getattr(node, "xpath", None)
        except Exception as e:
            logger.debug(f"Could not get xpath: {e}")

        # Get stable hash using browser-use's method
        stable_hash = None
        try:
            if hasattr(node, "compute_stable_hash"):
                stable_hash = node.compute_stable_hash()
        except Exception as e:
            logger.debug(f"Could not compute stable hash: {e}")

        # Get backend_node_id
        backend_node_id = getattr(node, "backend_node_id", None)

        # Get attributes dict
        attrs: Dict[str, str] = {}
        if hasattr(node, "attributes"):
            attrs = node.attributes or {}
        elif isinstance(node, dict):
            attrs = node.get("attributes", {}) or {}

        # Extract position from absolute_position
        x = y = width = height = None
        pos = getattr(node, "absolute_position", None)
        if pos is None and isinstance(node, dict):
            pos = node.get("absolute_position")
        if pos:
            x = getattr(pos, "x", None)
            y = getattr(pos, "y", None)
            width = getattr(pos, "width", None)
            height = getattr(pos, "height", None)
            if x is None and isinstance(pos, dict):
                x = pos.get("x")
                y = pos.get("y")
                width = pos.get("width")
                height = pos.get("height")

        # Extract text content from accessibility node
        text_content = None
        ax_node = getattr(node, "ax_node", None)
        if ax_node is None and isinstance(node, dict):
            ax_node = node.get("ax_node")
        if ax_node:
            text_content = getattr(ax_node, "name", None) or getattr(ax_node, "description", None)
            if text_content is None and isinstance(ax_node, dict):
                text_content = ax_node.get("name") or ax_node.get("description")

        # Get tag name
        tag_name = getattr(node, "tag_name", None)
        if tag_name is None:
            node_name = getattr(node, "node_name", None)
            if node_name is None and isinstance(node, dict):
                node_name = node.get("node_name", "")
            tag_name = (node_name or "").lower()

        # Get role from ax_node
        role = attrs.get("role")
        if not role and ax_node:
            role = getattr(ax_node, "role", None)
            if role is None and isinstance(ax_node, dict):
                role = ax_node.get("role")

        return cls(
            # Primary: browser-use generated
            css_selector=css_selector,
            xpath=xpath,
            stable_hash=stable_hash,
            backend_node_id=backend_node_id,
            # Secondary: key attributes
            id=attrs.get("id"),
            data_testid=attrs.get("data-testid"),
            aria_label=attrs.get("aria-label"),
            name=attrs.get("name"),
            placeholder=attrs.get("placeholder"),
            href=attrs.get("href"),
            role=role,
            # Structural
            tag_name=tag_name,
            text_content=text_content,
            classes=(attrs.get("class", "") or "").split() if attrs.get("class") else [],
            # Coordinates
            x=x,
            y=y,
            width=width,
            height=height,
            # Debug
            recorded_index=index,
        )


@dataclass
class RecordedAction:
    """A single recorded action with all data needed for replay."""
    action_type: ActionType
    timestamp: str
    step_number: int = 0

    # Element fingerprint (for element-based actions)
    element: Optional[ElementFingerprint] = None

    # Action-specific parameters
    url: Optional[str] = None  # navigate
    text: Optional[str] = None  # type
    is_sensitive: bool = False  # type
    clear_before_type: bool = True  # type
    direction: Optional[str] = None  # scroll
    scroll_amount: Optional[int] = None  # scroll
    keys: Optional[str] = None  # send_keys
    wait_seconds: Optional[float] = None  # wait
    file_path: Optional[str] = None  # upload
    dropdown_option: Optional[str] = None  # select_dropdown
    new_tab: bool = False  # navigate


@dataclass
class RecordedSession:
    """Complete recorded session for replay."""
    session_id: str
    task: str
    initial_url: str
    recorded_at: str
    browser_use_version: str = ""
    actions: List[RecordedAction] = field(default_factory=list)

    def save(self, path: str) -> None:
        """Save session to JSON file."""
        data = {
            "session_id": self.session_id,
            "task": self.task,
            "initial_url": self.initial_url,
            "recorded_at": self.recorded_at,
            "browser_use_version": self.browser_use_version,
            "actions": [
                {
                    "action_type": a.action_type.value,
                    "timestamp": a.timestamp,
                    "step_number": a.step_number,
                    "element": asdict(a.element) if a.element else None,
                    "url": a.url,
                    "text": "[SENSITIVE]" if a.is_sensitive else a.text,
                    "is_sensitive": a.is_sensitive,
                    "clear_before_type": a.clear_before_type,
                    "direction": a.direction,
                    "scroll_amount": a.scroll_amount,
                    "keys": a.keys,
                    "wait_seconds": a.wait_seconds,
                    "file_path": a.file_path,
                    "dropdown_option": a.dropdown_option,
                    "new_tab": a.new_tab,
                }
                for a in self.actions
            ]
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved recording to {path}")

    @classmethod
    def load(cls, path: str) -> "RecordedSession":
        """Load session from JSON file."""
        with open(path) as f:
            data = json.load(f)

        actions = []
        for a in data.get("actions", []):
            element = None
            if a.get("element"):
                e = a["element"]
                element = ElementFingerprint(
                    # Primary: browser-use generated
                    css_selector=e.get("css_selector"),
                    xpath=e.get("xpath"),
                    stable_hash=e.get("stable_hash"),
                    backend_node_id=e.get("backend_node_id"),
                    # Secondary: key attributes
                    id=e.get("id"),
                    data_testid=e.get("data_testid"),
                    aria_label=e.get("aria_label"),
                    name=e.get("name"),
                    placeholder=e.get("placeholder"),
                    href=e.get("href"),
                    role=e.get("role"),
                    # Structural
                    tag_name=e.get("tag_name"),
                    text_content=e.get("text_content"),
                    classes=e.get("classes", []),
                    # Coordinates
                    x=e.get("x"),
                    y=e.get("y"),
                    width=e.get("width"),
                    height=e.get("height"),
                    # Debug
                    recorded_index=e.get("recorded_index"),
                )

            actions.append(RecordedAction(
                action_type=ActionType(a["action_type"]),
                timestamp=a["timestamp"],
                step_number=a.get("step_number", 0),
                element=element,
                url=a.get("url"),
                text=a.get("text"),
                is_sensitive=a.get("is_sensitive", False),
                clear_before_type=a.get("clear_before_type", True),
                direction=a.get("direction"),
                scroll_amount=a.get("scroll_amount"),
                keys=a.get("keys"),
                wait_seconds=a.get("wait_seconds"),
                file_path=a.get("file_path"),
                dropdown_option=a.get("dropdown_option"),
                new_tab=a.get("new_tab", False),
            ))

        return cls(
            session_id=data["session_id"],
            task=data["task"],
            initial_url=data["initial_url"],
            recorded_at=data["recorded_at"],
            browser_use_version=data.get("browser_use_version", ""),
            actions=actions,
        )


class ElementMatcher:
    """
    Matches recorded element fingerprints to current DOM elements.

    DESIGN: Maximize use of browser-use's built-in methods.

    Matching strategy (in order):
        1. browser_session.get_index_by_id() - browser-use built-in
        2. CSS selector via CDP DOM.querySelector - uses browser-use's cdp_client
        3. Stable hash matching - iterate + browser-use's compute_stable_hash()
        4. XPath via CDP - uses browser-use's cdp_client
        5. Attribute matching - iterate selector_map
        6. browser_session.get_dom_element_at_coordinates() - browser-use built-in
    """

    @classmethod
    async def find_match(
        cls,
        fingerprint: ElementFingerprint,
        browser_session: Any,
    ) -> Optional[tuple[int, Any]]:
        """
        Find matching element using browser-use's capabilities.

        Args:
            fingerprint: Recorded element attributes
            browser_session: Active browser-use BrowserSession

        Returns:
            (index, node) tuple if found, None otherwise
        """
        if fingerprint is None:
            return None

        # Strategy 1: Use browser_session.get_index_by_id() - BROWSER-USE BUILT-IN
        if fingerprint.id:
            try:
                idx = await browser_session.get_index_by_id(fingerprint.id)
                if idx is not None:
                    selector_map = await browser_session.get_selector_map()
                    if idx in selector_map:
                        logger.debug(f"Matched by ID (browser-use): {fingerprint.id}")
                        return (idx, selector_map[idx])
            except Exception as e:
                logger.debug(f"get_index_by_id failed: {e}")

        # Strategy 2: CSS Selector via CDP - uses browser-use's cdp_client
        if fingerprint.css_selector:
            try:
                match = await cls._find_by_css_selector(fingerprint.css_selector, browser_session)
                if match:
                    logger.debug(f"Matched by CSS selector: {fingerprint.css_selector}")
                    return match
            except Exception as e:
                logger.debug(f"CSS selector match failed: {e}")

        # Strategy 3: Stable hash matching - uses browser-use's compute_stable_hash()
        if fingerprint.stable_hash is not None:
            try:
                match = await cls._find_by_stable_hash(fingerprint.stable_hash, browser_session)
                if match:
                    logger.debug(f"Matched by stable hash: {fingerprint.stable_hash}")
                    return match
            except Exception as e:
                logger.debug(f"Stable hash match failed: {e}")

        # Strategy 4: XPath via CDP - uses browser-use's cdp_client
        if fingerprint.xpath:
            try:
                match = await cls._find_by_xpath(fingerprint.xpath, browser_session)
                if match:
                    logger.debug(f"Matched by XPath: {fingerprint.xpath}")
                    return match
            except Exception as e:
                logger.debug(f"XPath match failed: {e}")

        # Strategy 5: Attribute matching - iterate selector_map
        selector_map = await browser_session.get_selector_map()
        if selector_map:
            # Try data-testid
            if fingerprint.data_testid:
                match = cls._find_by_attribute(selector_map, "data-testid", fingerprint.data_testid)
                if match:
                    logger.debug(f"Matched by data-testid: {fingerprint.data_testid}")
                    return match

            # Try aria-label
            if fingerprint.aria_label:
                match = cls._find_by_attribute(selector_map, "aria-label", fingerprint.aria_label)
                if match:
                    logger.debug(f"Matched by aria-label: {fingerprint.aria_label}")
                    return match

            # Try name + tag
            if fingerprint.name and fingerprint.tag_name:
                match = cls._find_by_name_and_tag(selector_map, fingerprint.name, fingerprint.tag_name)
                if match:
                    logger.debug(f"Matched by name+tag: {fingerprint.name}")
                    return match

            # Try placeholder
            if fingerprint.placeholder:
                match = cls._find_by_attribute(selector_map, "placeholder", fingerprint.placeholder)
                if match:
                    logger.debug(f"Matched by placeholder: {fingerprint.placeholder}")
                    return match

            # Try href for links
            if fingerprint.href and fingerprint.tag_name == "a":
                match = cls._find_by_attribute(selector_map, "href", fingerprint.href)
                if match:
                    logger.debug(f"Matched by href: {fingerprint.href}")
                    return match

            # Try text content + tag
            if fingerprint.text_content and fingerprint.tag_name:
                match = cls._find_by_tag_and_text(selector_map, fingerprint.tag_name, fingerprint.text_content)
                if match:
                    logger.debug(f"Matched by tag+text: {fingerprint.tag_name}, {fingerprint.text_content}")
                    return match

        # Strategy 6: Coordinates - BROWSER-USE BUILT-IN
        if fingerprint.x is not None and fingerprint.y is not None:
            try:
                # Calculate center point
                center_x = int(fingerprint.x + (fingerprint.width or 0) / 2)
                center_y = int(fingerprint.y + (fingerprint.height or 0) / 2)

                node = await browser_session.get_dom_element_at_coordinates(center_x, center_y)
                if node:
                    # Verify tag matches
                    node_tag = getattr(node, "tag_name", None) or getattr(node, "node_name", "").lower()
                    if not fingerprint.tag_name or node_tag.lower() == fingerprint.tag_name.lower():
                        # Find index in selector_map
                        selector_map = await browser_session.get_selector_map()
                        for idx, n in selector_map.items():
                            if getattr(n, "backend_node_id", None) == getattr(node, "backend_node_id", None):
                                logger.debug(f"Matched by coordinates (browser-use): ({center_x}, {center_y})")
                                return (idx, n)
            except Exception as e:
                logger.debug(f"Coordinate match failed: {e}")

        logger.warning(f"No match found for element: css={fingerprint.css_selector}, id={fingerprint.id}, tag={fingerprint.tag_name}")
        return None

    @classmethod
    async def _find_by_css_selector(
        cls,
        css_selector: str,
        browser_session: Any,
    ) -> Optional[tuple[int, Any]]:
        """
        Find element by CSS selector using browser-use's CDP client.

        This uses browser-use's cdp_client to evaluate CSS selectors.
        """
        try:
            cdp_session = await browser_session.get_or_create_cdp_session()
            session_id = cdp_session.session_id

            # Get document root
            doc_result = await browser_session.cdp_client.send.DOM.getDocument(
                params={"depth": 0},
                session_id=session_id,
            )
            root_node_id = doc_result.get("root", {}).get("nodeId")

            if not root_node_id:
                return None

            # Query selector
            query_result = await browser_session.cdp_client.send.DOM.querySelector(
                params={"nodeId": root_node_id, "selector": css_selector},
                session_id=session_id,
            )
            node_id = query_result.get("nodeId")

            if not node_id or node_id == 0:
                return None

            # Get backend_node_id for this node
            describe_result = await browser_session.cdp_client.send.DOM.describeNode(
                params={"nodeId": node_id},
                session_id=session_id,
            )
            backend_node_id = describe_result.get("node", {}).get("backendNodeId")

            if not backend_node_id:
                return None

            # Find in selector_map
            selector_map = await browser_session.get_selector_map()
            for idx, node in selector_map.items():
                if getattr(node, "backend_node_id", None) == backend_node_id:
                    return (idx, node)

        except Exception as e:
            logger.debug(f"CSS selector evaluation failed: {e}")

        return None

    @classmethod
    async def _find_by_xpath(
        cls,
        xpath: str,
        browser_session: Any,
    ) -> Optional[tuple[int, Any]]:
        """
        Find element by XPath using browser-use's CDP client.
        """
        try:
            cdp_session = await browser_session.get_or_create_cdp_session()
            session_id = cdp_session.session_id

            # Get document root
            doc_result = await browser_session.cdp_client.send.DOM.getDocument(
                params={"depth": 0},
                session_id=session_id,
            )
            root_node_id = doc_result.get("root", {}).get("nodeId")

            if not root_node_id:
                return None

            # Perform XPath search
            search_result = await browser_session.cdp_client.send.DOM.performSearch(
                params={"query": xpath, "includeUserAgentShadowDOM": False},
                session_id=session_id,
            )
            search_id = search_result.get("searchId")
            result_count = search_result.get("resultCount", 0)

            if not search_id or result_count == 0:
                return None

            try:
                # Get first result
                results = await browser_session.cdp_client.send.DOM.getSearchResults(
                    params={"searchId": search_id, "fromIndex": 0, "toIndex": 1},
                    session_id=session_id,
                )
                node_ids = results.get("nodeIds", [])

                if not node_ids:
                    return None

                node_id = node_ids[0]

                # Get backend_node_id
                describe_result = await browser_session.cdp_client.send.DOM.describeNode(
                    params={"nodeId": node_id},
                    session_id=session_id,
                )
                backend_node_id = describe_result.get("node", {}).get("backendNodeId")

                if not backend_node_id:
                    return None

                # Find in selector_map
                selector_map = await browser_session.get_selector_map()
                for idx, node in selector_map.items():
                    if getattr(node, "backend_node_id", None) == backend_node_id:
                        return (idx, node)

            finally:
                # Clean up search
                try:
                    await browser_session.cdp_client.send.DOM.discardSearchResults(
                        params={"searchId": search_id},
                        session_id=session_id,
                    )
                except Exception:
                    pass

        except Exception as e:
            logger.debug(f"XPath evaluation failed: {e}")

        return None

    @classmethod
    async def _find_by_stable_hash(
        cls,
        target_hash: int,
        browser_session: Any,
    ) -> Optional[tuple[int, Any]]:
        """
        Find element by stable hash using browser-use's compute_stable_hash().
        """
        selector_map = await browser_session.get_selector_map()

        for idx, node in selector_map.items():
            try:
                if hasattr(node, "compute_stable_hash"):
                    node_hash = node.compute_stable_hash()
                    if node_hash == target_hash:
                        return (idx, node)
            except Exception:
                continue

        return None

    @classmethod
    def _find_by_attribute(
        cls,
        selector_map: Dict[int, Any],
        attr_name: str,
        attr_value: str
    ) -> Optional[tuple[int, Any]]:
        """Find element by exact attribute match."""
        for idx, node in selector_map.items():
            attrs = getattr(node, "attributes", {}) or {}
            if isinstance(node, dict):
                attrs = node.get("attributes", {}) or {}
            if attrs.get(attr_name) == attr_value:
                return (idx, node)
        return None

    @classmethod
    def _find_by_name_and_tag(
        cls,
        selector_map: Dict[int, Any],
        name: str,
        tag: str
    ) -> Optional[tuple[int, Any]]:
        """Find element by name attribute and tag name."""
        for idx, node in selector_map.items():
            node_tag = getattr(node, "tag_name", None) or getattr(node, "node_name", "").lower()
            if isinstance(node, dict):
                node_tag = node.get("tag_name") or node.get("node_name", "").lower()
            if node_tag.lower() == tag.lower():
                attrs = getattr(node, "attributes", {}) or {}
                if isinstance(node, dict):
                    attrs = node.get("attributes", {}) or {}
                if attrs.get("name") == name:
                    return (idx, node)
        return None

    @classmethod
    def _find_by_tag_and_text(
        cls,
        selector_map: Dict[int, Any],
        tag: str,
        text: str
    ) -> Optional[tuple[int, Any]]:
        """Find element by tag name and text content."""
        text_lower = text.lower()
        for idx, node in selector_map.items():
            node_tag = getattr(node, "tag_name", None) or getattr(node, "node_name", "").lower()
            if isinstance(node, dict):
                node_tag = node.get("tag_name") or node.get("node_name", "").lower()
            if node_tag.lower() == tag.lower():
                # Get text from ax_node
                ax_node = getattr(node, "ax_node", None)
                if isinstance(node, dict):
                    ax_node = node.get("ax_node")
                if ax_node:
                    node_text = getattr(ax_node, "name", None)
                    if isinstance(ax_node, dict):
                        node_text = ax_node.get("name")
                    if node_text and text_lower in node_text.lower():
                        return (idx, node)
        return None


class BrowserUseRecorder:
    """
    Records browser-use actions by subscribing to the event bus.

    Uses browser-use's from_node() to capture:
        - CSS selector (generate_css_selector_for_element)
        - XPath (node.xpath)
        - Stable hash (node.compute_stable_hash)
        - All attributes
        - Coordinates
    """

    def __init__(self, session_id: str, task: str, initial_url: str):
        self.session_id = session_id
        self.task = task
        self.initial_url = initial_url

        self._session: Optional[RecordedSession] = None
        self._browser_session: Any = None
        self._is_recording = False
        self._step_counter = 0
        self._lock = asyncio.Lock()

    async def attach(self, browser_session: Any) -> None:
        """Attach to browser session and start recording."""
        if self._is_recording:
            raise RuntimeError("Already recording")

        self._browser_session = browser_session

        # Get browser-use version
        try:
            import browser_use
            version = getattr(browser_use, "__version__", "unknown")
        except Exception:
            version = "unknown"

        self._session = RecordedSession(
            session_id=self.session_id,
            task=self.task,
            initial_url=self.initial_url,
            recorded_at=datetime.now().isoformat(),
            browser_use_version=version,
        )

        # Import event types
        from browser_use.browser.events import (
            NavigateToUrlEvent,
            ClickElementEvent,
            TypeTextEvent,
            ScrollEvent,
            SendKeysEvent,
            GoBackEvent,
            GoForwardEvent,
            RefreshEvent,
            WaitEvent,
            UploadFileEvent,
            SelectDropdownOptionEvent,
        )

        # Subscribe to events
        event_bus = browser_session.event_bus
        event_bus.on(NavigateToUrlEvent, self._on_navigate)
        event_bus.on(ClickElementEvent, self._on_click)
        event_bus.on(TypeTextEvent, self._on_type)
        event_bus.on(ScrollEvent, self._on_scroll)
        event_bus.on(SendKeysEvent, self._on_send_keys)
        event_bus.on(GoBackEvent, self._on_go_back)
        event_bus.on(GoForwardEvent, self._on_go_forward)
        event_bus.on(RefreshEvent, self._on_refresh)
        event_bus.on(WaitEvent, self._on_wait)
        event_bus.on(UploadFileEvent, self._on_upload)
        event_bus.on(SelectDropdownOptionEvent, self._on_select_dropdown)

        self._is_recording = True
        logger.info(f"Recording started: {self.session_id}")

    def detach(self) -> RecordedSession:
        """Stop recording and return session."""
        if not self._is_recording or self._session is None:
            raise RuntimeError("Not recording")

        self._is_recording = False
        session = self._session
        self._session = None
        self._browser_session = None

        logger.info(f"Recording stopped: {len(session.actions)} actions captured")
        return session

    async def _record(self, action: RecordedAction) -> None:
        """Record an action."""
        if not self._session:
            return
        async with self._lock:
            self._step_counter += 1
            action.step_number = self._step_counter
            self._session.actions.append(action)
            logger.debug(f"Recorded: {action.action_type.value} (step {action.step_number})")

    def _get_element_index(self, node: Any) -> Optional[int]:
        """Try to get element index from browser session's selector map."""
        if not self._browser_session:
            return None
        try:
            selector_map = self._browser_session._cached_selector_map
            if selector_map and hasattr(node, "backend_node_id"):
                for idx, n in selector_map.items():
                    if hasattr(n, "backend_node_id") and n.backend_node_id == node.backend_node_id:
                        return idx
        except Exception:
            pass
        return None

    # Event handlers
    async def _on_navigate(self, event: Any) -> None:
        await self._record(RecordedAction(
            action_type=ActionType.NAVIGATE,
            timestamp=datetime.now().isoformat(),
            url=event.url,
            new_tab=getattr(event, "new_tab", False),
        ))

    async def _on_click(self, event: Any) -> None:
        idx = self._get_element_index(event.node)
        await self._record(RecordedAction(
            action_type=ActionType.CLICK,
            timestamp=datetime.now().isoformat(),
            element=ElementFingerprint.from_node(event.node, idx),
        ))

    async def _on_type(self, event: Any) -> None:
        idx = self._get_element_index(event.node)
        await self._record(RecordedAction(
            action_type=ActionType.TYPE,
            timestamp=datetime.now().isoformat(),
            element=ElementFingerprint.from_node(event.node, idx),
            text=event.text,
            is_sensitive=getattr(event, "is_sensitive", False),
            clear_before_type=getattr(event, "clear", True),
        ))

    async def _on_scroll(self, event: Any) -> None:
        node = getattr(event, "node", None)
        idx = self._get_element_index(node) if node else None
        await self._record(RecordedAction(
            action_type=ActionType.SCROLL,
            timestamp=datetime.now().isoformat(),
            element=ElementFingerprint.from_node(node, idx) if node else None,
            direction=event.direction,
            scroll_amount=event.amount,
        ))

    async def _on_send_keys(self, event: Any) -> None:
        await self._record(RecordedAction(
            action_type=ActionType.SEND_KEYS,
            timestamp=datetime.now().isoformat(),
            keys=event.keys,
        ))

    async def _on_go_back(self, _event: Any) -> None:
        await self._record(RecordedAction(
            action_type=ActionType.GO_BACK,
            timestamp=datetime.now().isoformat(),
        ))

    async def _on_go_forward(self, _event: Any) -> None:
        await self._record(RecordedAction(
            action_type=ActionType.GO_FORWARD,
            timestamp=datetime.now().isoformat(),
        ))

    async def _on_refresh(self, _event: Any) -> None:
        await self._record(RecordedAction(
            action_type=ActionType.REFRESH,
            timestamp=datetime.now().isoformat(),
        ))

    async def _on_wait(self, event: Any) -> None:
        await self._record(RecordedAction(
            action_type=ActionType.WAIT,
            timestamp=datetime.now().isoformat(),
            wait_seconds=min(event.seconds, event.max_seconds),
        ))

    async def _on_upload(self, event: Any) -> None:
        idx = self._get_element_index(event.node)
        await self._record(RecordedAction(
            action_type=ActionType.UPLOAD_FILE,
            timestamp=datetime.now().isoformat(),
            element=ElementFingerprint.from_node(event.node, idx),
            file_path=event.file_path,
        ))

    async def _on_select_dropdown(self, event: Any) -> None:
        idx = self._get_element_index(event.node)
        await self._record(RecordedAction(
            action_type=ActionType.SELECT_DROPDOWN,
            timestamp=datetime.now().isoformat(),
            element=ElementFingerprint.from_node(event.node, idx),
            dropdown_option=event.text,
        ))


@dataclass
class ReplayResult:
    """Result of a replay execution."""
    success: bool
    actions_total: int
    actions_succeeded: int
    actions_failed: int
    failed_steps: List[int] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0


class BrowserUseReplayer:
    """
    Replays recorded sessions using browser-use's execution layer.

    Uses browser-use for:
        - Event dispatching (all actions go through event_bus)
        - Element finding (via ElementMatcher which uses browser-use methods)
        - DOM state management (get_selector_map, get_browser_state_summary)
    """

    def __init__(
        self,
        on_step_start: Optional[Callable[[int, RecordedAction], None]] = None,
        on_step_complete: Optional[Callable[[int, bool, Optional[str]], None]] = None,
    ):
        self.on_step_start = on_step_start
        self.on_step_complete = on_step_complete

    async def replay(
        self,
        session: RecordedSession,
        browser_session: Any,
        stop_on_failure: bool = False,
        sensitive_data: Optional[Dict[str, str]] = None,
    ) -> ReplayResult:
        """
        Replay a recorded session.

        Args:
            session: The recorded session to replay
            browser_session: An active browser-use BrowserSession
            stop_on_failure: Stop replay if any action fails
            sensitive_data: Dict mapping sensitive field names to actual values

        Returns:
            ReplayResult with success/failure details
        """
        import time
        start_time = time.time()

        sensitive_data = sensitive_data or {}

        succeeded = 0
        failed = 0
        failed_steps = []
        errors = []

        logger.info(f"Starting replay: {session.session_id} ({len(session.actions)} actions)")

        for action in session.actions:
            step = action.step_number

            if self.on_step_start:
                self.on_step_start(step, action)

            try:
                await self._execute_action(
                    action=action,
                    browser_session=browser_session,
                    sensitive_data=sensitive_data,
                )
                succeeded += 1

                if self.on_step_complete:
                    self.on_step_complete(step, True, None)

            except Exception as e:
                failed += 1
                failed_steps.append(step)
                error_msg = f"Step {step} ({action.action_type.value}): {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

                if self.on_step_complete:
                    self.on_step_complete(step, False, str(e))

                if stop_on_failure:
                    break

        duration = time.time() - start_time
        success = failed == 0

        result = ReplayResult(
            success=success,
            actions_total=len(session.actions),
            actions_succeeded=succeeded,
            actions_failed=failed,
            failed_steps=failed_steps,
            errors=errors,
            duration_seconds=duration,
        )

        logger.info(
            f"Replay complete: {succeeded}/{len(session.actions)} succeeded "
            f"in {duration:.2f}s"
        )

        return result

    async def _execute_action(
        self,
        action: RecordedAction,
        browser_session: Any,
        sensitive_data: Dict[str, str],
    ) -> None:
        """Execute a single action using browser-use's event system."""

        # Import event types
        from browser_use.browser.events import (
            NavigateToUrlEvent,
            ClickElementEvent,
            TypeTextEvent,
            ScrollEvent,
            SendKeysEvent,
            GoBackEvent,
            GoForwardEvent,
            RefreshEvent,
            WaitEvent,
            UploadFileEvent,
            SelectDropdownOptionEvent,
        )

        event_bus = browser_session.event_bus

        if action.action_type == ActionType.NAVIGATE:
            event = NavigateToUrlEvent(url=action.url or "", new_tab=action.new_tab)
            await event_bus.dispatch(event)

        elif action.action_type == ActionType.CLICK:
            node = await self._find_element(action.element, browser_session)
            event = ClickElementEvent(node=node)
            await event_bus.dispatch(event)

        elif action.action_type == ActionType.TYPE:
            node = await self._find_element(action.element, browser_session)
            text = action.text
            if action.is_sensitive and text == "[SENSITIVE]":
                for key in [action.element.name if action.element else None,
                           action.element.id if action.element else None,
                           "password", "secret"]:
                    if key and key in sensitive_data:
                        text = sensitive_data[key]
                        break
            event = TypeTextEvent(
                node=node,
                text=text or "",
                clear=action.clear_before_type,
                is_sensitive=action.is_sensitive,
            )
            await event_bus.dispatch(event)

        elif action.action_type == ActionType.SCROLL:
            node = None
            if action.element:
                try:
                    node = await self._find_element(action.element, browser_session)
                except Exception:
                    pass
            # Validate direction is one of the allowed literals
            direction = action.direction or "down"
            if direction not in ("up", "down", "left", "right"):
                direction = "down"
            from typing import cast, Literal
            event = ScrollEvent(
                node=node,
                direction=cast(Literal["up", "down", "left", "right"], direction),
                amount=action.scroll_amount or 300,
            )
            await event_bus.dispatch(event)

        elif action.action_type == ActionType.SEND_KEYS:
            event = SendKeysEvent(keys=action.keys or "")
            await event_bus.dispatch(event)

        elif action.action_type == ActionType.GO_BACK:
            event = GoBackEvent()
            await event_bus.dispatch(event)

        elif action.action_type == ActionType.GO_FORWARD:
            event = GoForwardEvent()
            await event_bus.dispatch(event)

        elif action.action_type == ActionType.REFRESH:
            event = RefreshEvent()
            await event_bus.dispatch(event)

        elif action.action_type == ActionType.WAIT:
            event = WaitEvent(seconds=action.wait_seconds or 1.0)
            await event_bus.dispatch(event)

        elif action.action_type == ActionType.UPLOAD_FILE:
            node = await self._find_element(action.element, browser_session)
            event = UploadFileEvent(node=node, file_path=action.file_path or "")
            await event_bus.dispatch(event)

        elif action.action_type == ActionType.SELECT_DROPDOWN:
            node = await self._find_element(action.element, browser_session)
            event = SelectDropdownOptionEvent(node=node, text=action.dropdown_option or "")
            await event_bus.dispatch(event)

        else:
            raise ValueError(f"Unknown action type: {action.action_type}")

    async def _find_element(
        self,
        fingerprint: Optional[ElementFingerprint],
        browser_session: Any,
        max_retries: int = 5,
        retry_delay: float = 1.0,
    ) -> Any:
        """
        Find element using browser-use's capabilities with retry logic.

        Uses ElementMatcher which leverages:
            - browser_session.get_index_by_id()
            - browser_session.get_dom_element_at_coordinates()
            - browser_session.cdp_client for CSS/XPath
            - node.compute_stable_hash() for hash matching
        """
        if fingerprint is None:
            raise ValueError("No element fingerprint provided")

        for attempt in range(max_retries):
            # Refresh DOM state using browser-use's method
            await browser_session.get_browser_state_summary(cached=False)

            # Use ElementMatcher which wraps browser-use capabilities
            match = await ElementMatcher.find_match(fingerprint, browser_session)

            if match is not None:
                idx, node = match
                logger.debug(f"Found element at index {idx} (attempt {attempt + 1})")
                return node

            # Element not found, wait and retry
            if attempt < max_retries - 1:
                logger.debug(
                    f"Element not found (attempt {attempt + 1}/{max_retries}), "
                    f"waiting {retry_delay}s..."
                )
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 1.5, 5.0)

        # All retries exhausted
        raise ValueError(
            f"Could not find element matching: "
            f"css={fingerprint.css_selector}, "
            f"id={fingerprint.id}, "
            f"tag={fingerprint.tag_name}"
        )
