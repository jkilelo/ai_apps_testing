"""
Accessibility Audit Data Models.

Models for axe-core scan results, audit scoring, and session tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

from .test_session import TestSession


class ImpactLevel(str, Enum):
    """WCAG violation impact severity."""
    CRITICAL = "critical"
    SERIOUS = "serious"
    MODERATE = "moderate"
    MINOR = "minor"


@dataclass
class AxeViolationNode:
    """A single DOM node affected by a violation."""
    target: List[str]  # CSS selector path
    html: str  # HTML snippet of the element
    failure_summary: str  # Human-readable failure description


@dataclass
class AxeViolation:
    """A single axe-core violation rule with all affected nodes."""
    rule_id: str
    impact: ImpactLevel
    description: str
    help_url: str
    wcag_tags: List[str]
    nodes: List[AxeViolationNode]


@dataclass
class AxeScanResult:
    """Complete result from an axe-core automated scan."""
    url: str
    violations: List[AxeViolation]
    passes_count: int
    incomplete_count: int

    @property
    def total_violation_nodes(self) -> int:
        return sum(len(v.nodes) for v in self.violations)

    @property
    def critical_count(self) -> int:
        return sum(len(v.nodes) for v in self.violations if v.impact == ImpactLevel.CRITICAL)

    @property
    def serious_count(self) -> int:
        return sum(len(v.nodes) for v in self.violations if v.impact == ImpactLevel.SERIOUS)


@dataclass
class A11yCategoryScore:
    """Score for a single accessibility category."""
    category: str
    score: int  # 0-100
    issues_found: int


@dataclass
class A11yAuditScore:
    """Overall accessibility audit score."""
    overall_score: int  # 0-100
    grade: str  # A/B/C/D/F
    categories: List[A11yCategoryScore]
    total_violations: int


@dataclass
class A11yAuditSession:
    """Complete accessibility audit session with all data."""
    session_id: str
    url: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    axe_scan: Optional[AxeScanResult] = None
    behavioral_session: Optional[TestSession] = None
    audit_score: Optional[A11yAuditScore] = None
    html_report_path: Optional[str] = None
    json_report_path: Optional[str] = None
    output_directory: Optional[str] = None
