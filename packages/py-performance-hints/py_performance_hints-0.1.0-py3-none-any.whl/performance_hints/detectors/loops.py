"""
Loop-based performance detector for identifying inefficient nested loops.
"""

from typing import Any, Callable, List, Tuple

from .base import BaseDetector, PerformanceIssue, IssueLevel
from ..analyzers.ast_analyzer import ASTAnalyzer, FunctionAnalysis


class LoopDetector(BaseDetector):
    """Detects performance issues related to loop nesting and complexity."""
    
    def __init__(
        self, 
        max_nesting_level: int = 2,
        complexity_threshold: float = 4.0,
        enabled: bool = True
    ):
        super().__init__(enabled)
        self.max_nesting_level = max_nesting_level
        self.complexity_threshold = complexity_threshold
        self.analyzer = ASTAnalyzer()
        self._analysis_cache = {}  # Cache analysis results
    
    @property
    def pattern_name(self) -> str:
        return "nested_loops"
    
    def pre_execute(
        self, 
        func: Callable, 
        args: Tuple[Any, ...], 
        kwargs: dict
    ) -> None:
        """Analyze function before execution to detect loop patterns."""
        if not self.enabled:
            return
        
        # Cache the analysis result to avoid re-analyzing on each call
        func_id = id(func)
        if func_id not in self._analysis_cache:
            analysis = self.analyzer.analyze_function(func)
            self._analysis_cache[func_id] = analysis
    
    def post_execute(
        self,
        func: Callable,
        args: Tuple[Any, ...],
        kwargs: dict,
        result: Any,
        execution_time_ms: float
    ) -> List[PerformanceIssue]:
        """Detect loop-related performance issues."""
        
        if not self.enabled:
            return []
        
        issues = []
        func_id = id(func)
        analysis = self._analysis_cache.get(func_id)
        
        if not analysis or not analysis.loop_info:
            return issues
        
        # Check for excessive nesting
        if analysis.max_nesting_level > self.max_nesting_level:
            issues.append(self._create_nesting_issue(func, analysis, execution_time_ms))
            self._record_detection()
        
        # Check for high complexity
        if analysis.complexity_score > self.complexity_threshold:
            issues.append(self._create_complexity_issue(func, analysis, execution_time_ms))
            self._record_detection()
        
        # Check for specific problematic patterns
        pattern_issues = self._detect_specific_patterns(func, analysis, execution_time_ms)
        issues.extend(pattern_issues)
        
        return issues
    
    def _create_nesting_issue(
        self, 
        func: Callable, 
        analysis: FunctionAnalysis, 
        execution_time_ms: float
    ) -> PerformanceIssue:
        """Create issue for excessive loop nesting."""
        
        # Find the most deeply nested loop
        deepest_loop = max(analysis.loop_info, key=lambda x: x.nesting_level)
        
        level = IssueLevel.CRITICAL if analysis.max_nesting_level >= 4 else IssueLevel.WARNING
        
        title = f"Deep loop nesting detected: {analysis.max_nesting_level} levels"
        
        description = (
            f"Function '{func.__name__}' contains loops nested {analysis.max_nesting_level} "
            f"levels deep (line {deepest_loop.line_number}). This can lead to O(n^{analysis.max_nesting_level}) "
            "time complexity and poor performance with larger datasets."
        )
        
        suggestion = self._generate_nesting_suggestion(analysis)
        
        return PerformanceIssue(
            level=level,
            title=title,
            description=description,
            suggestion=suggestion,
            execution_time_ms=execution_time_ms,
            pattern_type=self.pattern_name,
            details={
                "max_nesting_level": analysis.max_nesting_level,
                "complexity_score": analysis.complexity_score,
                "total_loops": len(analysis.loop_info),
                "deepest_loop_line": deepest_loop.line_number,
                "deepest_loop_type": deepest_loop.type,
                "function_lines": analysis.total_lines
            }
        )
    
    def _create_complexity_issue(
        self, 
        func: Callable, 
        analysis: FunctionAnalysis, 
        execution_time_ms: float
    ) -> PerformanceIssue:
        """Create issue for high loop complexity."""
        
        level = IssueLevel.WARNING if analysis.complexity_score < 8.0 else IssueLevel.CRITICAL
        
        title = f"High loop complexity: {analysis.complexity_score:.1f}"
        
        description = (
            f"Function '{func.__name__}' has high loop complexity score "
            f"({analysis.complexity_score:.1f}). This indicates multiple nested loops "
            "that could cause performance issues with larger inputs."
        )
        
        suggestion = self._generate_complexity_suggestion(analysis)
        
        return PerformanceIssue(
            level=level,
            title=title,
            description=description,
            suggestion=suggestion,
            execution_time_ms=execution_time_ms,
            pattern_type="loop_complexity",
            details={
                "complexity_score": analysis.complexity_score,
                "total_loops": len(analysis.loop_info),
                "max_nesting_level": analysis.max_nesting_level,
                "function_lines": analysis.total_lines
            }
        )
    
    def _detect_specific_patterns(
        self, 
        func: Callable, 
        analysis: FunctionAnalysis, 
        execution_time_ms: float
    ) -> List[PerformanceIssue]:
        """Detect specific problematic loop patterns."""
        
        issues = []
        
        # Pattern 1: Multiple consecutive loops that could be combined
        consecutive_loops = self._find_consecutive_loops(analysis)
        if len(consecutive_loops) >= 2:
            issues.append(self._create_consecutive_loops_issue(
                func, consecutive_loops, execution_time_ms
            ))
        
        # Pattern 2: Nested comprehensions (can be inefficient)
        nested_comps = [loop for loop in analysis.loop_info 
                       if 'comp' in loop.type and loop.nesting_level > 1]
        if nested_comps:
            issues.append(self._create_nested_comprehension_issue(
                func, nested_comps, execution_time_ms
            ))
        
        return issues
    
    def _find_consecutive_loops(self, analysis: FunctionAnalysis) -> List:
        """Find loops that might be consecutive and could be combined."""
        # Simple heuristic: loops at the same nesting level within a few lines
        consecutive = []
        loops_by_level = {}
        
        for loop in analysis.loop_info:
            level = loop.nesting_level
            if level not in loops_by_level:
                loops_by_level[level] = []
            loops_by_level[level].append(loop)
        
        # Look for loops at level 1 that are close together
        if 1 in loops_by_level and len(loops_by_level[1]) >= 2:
            level_1_loops = sorted(loops_by_level[1], key=lambda x: x.line_number)
            for i in range(len(level_1_loops) - 1):
                current = level_1_loops[i]
                next_loop = level_1_loops[i + 1]
                if next_loop.line_number - current.line_number < 10:  # Within 10 lines
                    consecutive.extend([current, next_loop])
        
        return consecutive
    
    def _create_consecutive_loops_issue(
        self, 
        func: Callable, 
        loops: List, 
        execution_time_ms: float
    ) -> PerformanceIssue:
        """Create issue for consecutive loops that might be combined."""
        
        return PerformanceIssue(
            level=IssueLevel.INFO,
            title=f"Consecutive loops detected: {len(loops)} loops",
            description=(
                f"Function '{func.__name__}' contains consecutive loops that might "
                "be combined for better performance. Multiple passes over the same "
                "data can be inefficient."
            ),
            suggestion=(
                "Consider combining consecutive loops that iterate over the same data • "
                "Use single loop with multiple operations • "
                "Consider using zip() for parallel iteration"
            ),
            execution_time_ms=execution_time_ms,
            pattern_type="consecutive_loops"
        )
    
    def _create_nested_comprehension_issue(
        self, 
        func: Callable, 
        comps: List, 
        execution_time_ms: float
    ) -> PerformanceIssue:
        """Create issue for nested comprehensions."""
        
        return PerformanceIssue(
            level=IssueLevel.INFO,
            title="Nested comprehensions detected",
            description=(
                f"Function '{func.__name__}' contains nested comprehensions which "
                "can be memory-intensive and hard to read for complex operations."
            ),
            suggestion=(
                "Consider breaking complex comprehensions into regular loops • "
                "Use itertools for complex iterations • "
                "Consider generator expressions for memory efficiency"
            ),
            execution_time_ms=execution_time_ms,
            pattern_type="nested_comprehensions"
        )
    
    def _generate_nesting_suggestion(self, analysis: FunctionAnalysis) -> str:
        """Generate suggestions for reducing loop nesting."""
        
        suggestions = []
        
        if analysis.max_nesting_level >= 4:
            suggestions.append("Break this function into smaller functions")
            suggestions.append("Consider using itertools.product() for cartesian products")
        elif analysis.max_nesting_level == 3:
            suggestions.append("Try to flatten nested loops using itertools")
            suggestions.append("Consider using list comprehensions where appropriate")
        else:
            suggestions.append("Look for opportunities to use built-in functions")
            suggestions.append("Consider using pandas operations for data processing")
        
        # Add specific suggestions based on loop patterns
        loop_types = [loop.type for loop in analysis.loop_info]
        if 'while' in loop_types:
            suggestions.append("Review while loop conditions for early termination")
        
        return " • ".join(suggestions[:2])
    
    def _generate_complexity_suggestion(self, analysis: FunctionAnalysis) -> str:
        """Generate suggestions for reducing loop complexity."""
        
        suggestions = [
            "Profile this function to identify the real bottlenecks",
            "Consider using numpy/pandas for vectorized operations",
            "Look for opportunities to cache intermediate results",
            "Consider using generators to reduce memory usage",
            "Break complex loops into separate functions"
        ]
        
        return " • ".join(suggestions[:2])
    
    def clear_cache(self) -> None:
        """Clear the analysis cache."""
        self._analysis_cache.clear()
    
    def get_stats(self) -> dict:
        """Get detector statistics."""
        return {
            "pattern_name": self.pattern_name,
            "max_nesting_level": self.max_nesting_level,
            "complexity_threshold": self.complexity_threshold,
            "detections": self.detection_count,
            "cached_functions": len(self._analysis_cache)
        }