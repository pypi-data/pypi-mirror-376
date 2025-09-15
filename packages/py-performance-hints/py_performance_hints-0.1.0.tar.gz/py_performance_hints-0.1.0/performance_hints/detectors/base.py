"""
Base classes for performance detectors.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Tuple
from enum import Enum


class IssueLevel(Enum):
    """Severity levels for performance issues."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class PerformanceIssue:
    """Represents a detected performance issue."""
    
    level: IssueLevel
    title: str
    description: str
    suggestion: str
    execution_time_ms: Optional[float] = None
    pattern_type: Optional[str] = None
    details: Optional[dict] = None
    
    def __str__(self) -> str:
        return f"{self.level.value.upper()}: {self.title}"


class BaseDetector(ABC):
    """Base class for all performance detectors."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._detection_count = 0
    
    @property
    @abstractmethod
    def pattern_name(self) -> str:
        """Name of the pattern this detector identifies."""
        pass
    
    def pre_execute(
        self, 
        func: Callable, 
        args: Tuple[Any, ...], 
        kwargs: dict
    ) -> None:
        """
        Called before function execution.
        
        Args:
            func: The function being monitored
            args: Function arguments
            kwargs: Function keyword arguments
        """
        if not self.enabled:
            return
        # Override in subclasses if pre-execution analysis is needed
        pass
    
    @abstractmethod
    def post_execute(
        self,
        func: Callable,
        args: Tuple[Any, ...],
        kwargs: dict,
        result: Any,
        execution_time_ms: float
    ) -> List[PerformanceIssue]:
        """
        Called after function execution to detect performance issues.
        
        Args:
            func: The function that was executed
            args: Function arguments
            kwargs: Function keyword arguments  
            result: Function return value (None if exception occurred)
            execution_time_ms: Function execution time in milliseconds
            
        Returns:
            List of detected performance issues
        """
        pass
    
    def reset_stats(self) -> None:
        """Reset internal statistics."""
        self._detection_count = 0
    
    @property
    def detection_count(self) -> int:
        """Number of times this detector has found issues."""
        return self._detection_count
    
    def _record_detection(self) -> None:
        """Record that a detection occurred."""
        self._detection_count += 1