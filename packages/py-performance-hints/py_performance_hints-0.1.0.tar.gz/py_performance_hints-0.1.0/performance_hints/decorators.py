"""
Core decorator implementation for performance monitoring.
"""

import functools
import time
from typing import Any, Callable, List, Optional, TypeVar, Union

from .detectors.timing import TimingDetector
from .detectors.loops import LoopDetector
from .reporters.console import ConsoleReporter
from .config.settings import get_settings

F = TypeVar('F', bound=Callable[..., Any])


def monitor_performance(
    func: Optional[F] = None,
    *,
    detect_patterns: Optional[List[str]] = None,
    threshold_ms: Optional[float] = None,
    enabled: bool = True,
    report_format: str = "console"
) -> Union[F, Callable[[F], F]]:
    """
    Decorator to monitor function performance and detect anti-patterns.
    
    Args:
        func: The function to monitor (when used without parentheses)
        detect_patterns: List of patterns to detect ['timing', 'nested_loops']
        threshold_ms: Time threshold in milliseconds to trigger warnings
        enabled: Whether monitoring is enabled
        report_format: Output format ('console', 'json', 'silent')
    
    Example:
        @monitor_performance
        def slow_function():
            time.sleep(0.1)
        
        @monitor_performance(detect_patterns=['timing'], threshold_ms=50)
        def another_function():
            pass
    """
    
    def decorator(f: F) -> F:
        if not enabled:
            return f
            
        settings = get_settings()
        
        # Use provided values or fall back to settings
        patterns = detect_patterns or settings.detect_patterns
        threshold = threshold_ms or settings.threshold_ms
        
        # Initialize detectors based on patterns
        detectors = []
        if 'timing' in patterns:
            detectors.append(TimingDetector(threshold_ms=threshold))
        if 'nested_loops' in patterns:
            detectors.append(LoopDetector())
            
        # Initialize reporter
        if report_format == 'console':
            reporter = ConsoleReporter()
        else:
            reporter = ConsoleReporter()  # Default for Phase 1
        
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Pre-execution analysis
            for detector in detectors:
                detector.pre_execute(f, args, kwargs)
            
            # Execute function with timing
            start_time = time.perf_counter()
            try:
                result = f(*args, **kwargs)
                execution_time = (time.perf_counter() - start_time) * 1000  # ms
                
                # Post-execution analysis
                issues = []
                for detector in detectors:
                    detector_issues = detector.post_execute(
                        f, args, kwargs, result, execution_time
                    )
                    issues.extend(detector_issues)
                
                # Report issues if any found
                if issues:
                    reporter.report(f, issues, execution_time)
                    
                return result
                
            except Exception as e:
                execution_time = (time.perf_counter() - start_time) * 1000
                # Still run detectors even on exception
                for detector in detectors:
                    try:
                        detector.post_execute(f, args, kwargs, None, execution_time)
                    except:
                        pass  # Don't let detector errors mask original exception
                raise
        
        # Store metadata for introspection
        wrapper._performance_hints_enabled = True  # type: ignore
        wrapper._performance_hints_patterns = patterns  # type: ignore
        
        return wrapper  # type: ignore
    
    # Handle both @monitor_performance and @monitor_performance() syntax
    if func is None:
        return decorator
    else:
        return decorator(func)