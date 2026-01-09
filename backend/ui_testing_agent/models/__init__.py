"""
Data models for UI Testing Agent.
"""

from .selector_info import SelectorInfo
from .processed_action import ProcessedAction
from .processed_step import ProcessedStep
from .test_scenario import TestScenario
from .test_session import TestSession
from .output_config import OutputConfig

__all__ = [
    "SelectorInfo",
    "ProcessedAction",
    "ProcessedStep",
    "TestScenario",
    "TestSession",
    "OutputConfig",
]
