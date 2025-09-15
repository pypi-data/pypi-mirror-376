"""
Base reporter class for outputting performance issues.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, List

from ..detectors.base import PerformanceIssue


class BaseReporter(ABC):
    """Base class for all performance issue reporters."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._report_count = 0
    
    @abstractmethod
    def report(
        self, 
        func: Callable, 
        issues: List[PerformanceIssue], 
        execution_time_ms: float
    ) -> None:
        """
        Report performance issues for a function.
        
        Args:
            func: The function that had issues
            issues: List of detected performance issues
            execution_time_ms: Function execution time in milliseconds
        """
        pass
    
    def _record_report(self) -> None:
        """Record that a report was generated."""
        self._report_count += 1
    
    @property
    def report_count(self) -> int:
        """Number of reports generated."""
        return self._report_count
    
    def reset_stats(self) -> None:
        """Reset reporter statistics."""
        self._report_count = 0