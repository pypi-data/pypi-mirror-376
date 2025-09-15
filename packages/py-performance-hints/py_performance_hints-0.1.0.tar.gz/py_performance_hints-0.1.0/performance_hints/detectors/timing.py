"""
Timing-based performance detector.
"""

from typing import Any, Callable, List, Tuple

from .base import BaseDetector, PerformanceIssue, IssueLevel


class TimingDetector(BaseDetector):
    """Detects functions that take longer than expected to execute."""
    
    def __init__(self, threshold_ms: float = 100.0, enabled: bool = True):
        super().__init__(enabled)
        self.threshold_ms = threshold_ms
        self._execution_history: List[float] = []
        self._max_history = 10  # Keep last 10 executions for analysis
    
    @property
    def pattern_name(self) -> str:
        return "slow_execution"
    
    def post_execute(
        self,
        func: Callable,
        args: Tuple[Any, ...],
        kwargs: dict,
        result: Any,
        execution_time_ms: float
    ) -> List[PerformanceIssue]:
        """Detect if function execution time exceeds threshold."""
        
        if not self.enabled:
            return []
        
        issues = []
        
        # Store execution time for trend analysis
        self._execution_history.append(execution_time_ms)
        if len(self._execution_history) > self._max_history:
            self._execution_history.pop(0)
        
        # Check if execution time exceeds threshold
        if execution_time_ms > self.threshold_ms:
            self._record_detection()
            
            # Determine severity based on how much it exceeds threshold
            if execution_time_ms > self.threshold_ms * 5:
                level = IssueLevel.CRITICAL
                title = f"Very slow execution: {execution_time_ms:.1f}ms"
            elif execution_time_ms > self.threshold_ms * 2:
                level = IssueLevel.WARNING
                title = f"Slow execution: {execution_time_ms:.1f}ms"
            else:
                level = IssueLevel.INFO
                title = f"Execution time above threshold: {execution_time_ms:.1f}ms"
            
            # Generate suggestions based on execution time
            suggestion = self._generate_suggestion(execution_time_ms, func)
            
            issue = PerformanceIssue(
                level=level,
                title=title,
                description=f"Function '{func.__name__}' took {execution_time_ms:.1f}ms "
                           f"to execute (threshold: {self.threshold_ms:.1f}ms)",
                suggestion=suggestion,
                execution_time_ms=execution_time_ms,
                pattern_type=self.pattern_name,
                details={
                    "threshold_ms": self.threshold_ms,
                    "actual_time_ms": execution_time_ms,
                    "function_name": func.__name__,
                    "avg_time_ms": self._get_average_time(),
                    "executions_tracked": len(self._execution_history)
                }
            )
            
            issues.append(issue)
        
        return issues
    
    def _generate_suggestion(self, execution_time_ms: float, func: Callable) -> str:
        """Generate performance improvement suggestions."""
        
        suggestions = []
        
        if execution_time_ms > 1000:  # > 1 second
            suggestions.append("Consider breaking this into smaller functions")
            suggestions.append("Look for blocking I/O operations that could be made async")
        elif execution_time_ms > 500:  # > 500ms
            suggestions.append("Profile this function to identify bottlenecks")
            suggestions.append("Consider caching results if function is called repeatedly")
        else:
            suggestions.append("Check for inefficient loops or data structures")
            suggestions.append("Consider optimizing algorithm complexity")
        
        # Add context-aware suggestions based on function characteristics
        if hasattr(func, '__code__'):
            code = func.__code__
            if 'open' in code.co_names:
                suggestions.append("Ensure file operations are optimized")
            if any(db_term in str(code.co_names).lower() for db_term in ['query', 'select', 'db']):
                suggestions.append("Consider optimizing database queries")
        
        return " • ".join(suggestions[:2])  # Return top 2 suggestions
    
    def _get_average_time(self) -> float:
        """Calculate average execution time from history."""
        if not self._execution_history:
            return 0.0
        return sum(self._execution_history) / len(self._execution_history)
    
    def get_stats(self) -> dict:
        """Get detector statistics."""
        return {
            "pattern_name": self.pattern_name,
            "threshold_ms": self.threshold_ms,
            "detections": self.detection_count,
            "avg_execution_time_ms": self._get_average_time(),
            "executions_tracked": len(self._execution_history),
            "recent_times_ms": self._execution_history.copy()
        }