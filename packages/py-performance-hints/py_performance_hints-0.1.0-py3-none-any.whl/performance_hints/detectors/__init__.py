"""Detector modules for identifying performance patterns."""

from .base import BaseDetector, PerformanceIssue, IssueLevel
from .timing import TimingDetector
from .loops import LoopDetector

__all__ = [
    'BaseDetector', 
    'PerformanceIssue', 
    'IssueLevel',
    'TimingDetector', 
    'LoopDetector'
]