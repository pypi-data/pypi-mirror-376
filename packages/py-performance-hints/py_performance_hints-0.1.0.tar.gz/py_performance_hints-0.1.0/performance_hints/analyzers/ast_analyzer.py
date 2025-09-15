"""
AST analysis utilities for detecting code patterns.
"""

import ast
import inspect
from typing import Any, Callable, List, Dict, Optional, Set
from dataclasses import dataclass


@dataclass
class LoopInfo:
    """Information about a detected loop."""
    type: str  # 'for', 'while', 'comprehension'
    line_number: int
    nesting_level: int
    parent_loops: List['LoopInfo']
    variable_name: Optional[str] = None
    iterable_name: Optional[str] = None


@dataclass
class FunctionAnalysis:
    """Analysis results for a function."""
    function_name: str
    total_lines: int
    loop_info: List[LoopInfo]
    max_nesting_level: int
    has_nested_loops: bool
    complexity_score: float


class ASTAnalyzer:
    """Analyzes Python AST to detect performance patterns."""
    
    def __init__(self):
        self.current_nesting_level = 0
        self.loop_stack: List[LoopInfo] = []
        self.found_loops: List[LoopInfo] = []
    
    def analyze_function(self, func: Callable) -> Optional[FunctionAnalysis]:
        """
        Analyze a function's AST for performance patterns.
        
        Args:
            func: Function to analyze
            
        Returns:
            FunctionAnalysis object or None if analysis fails
        """
        try:
            # Get function source code
            source = inspect.getsource(func)
            tree = ast.parse(source)
            
            # Reset state
            self._reset_state()
            
            # Visit all nodes in the AST
            self.visit(tree)
            
            # Calculate complexity metrics
            max_nesting = max([loop.nesting_level for loop in self.found_loops], default=0)
            has_nested = any(loop.nesting_level > 1 for loop in self.found_loops)
            complexity = self._calculate_complexity_score()
            
            return FunctionAnalysis(
                function_name=func.__name__,
                total_lines=len(source.splitlines()),
                loop_info=self.found_loops.copy(),
                max_nesting_level=max_nesting,
                has_nested_loops=has_nested,
                complexity_score=complexity
            )
            
        except (OSError, TypeError, SyntaxError):
            # Can't analyze this function (built-in, C extension, etc.)
            return None
    
    def visit(self, node: ast.AST) -> None:
        """Visit AST nodes recursively."""
        method_name = f'visit_{node.__class__.__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        visitor(node)
    
    def visit_For(self, node: ast.For) -> None:
        """Visit for loop nodes."""
        self._enter_loop('for', node)
        self.generic_visit(node)
        self._exit_loop()
    
    def visit_While(self, node: ast.While) -> None:
        """Visit while loop nodes."""
        self._enter_loop('while', node)
        self.generic_visit(node)
        self._exit_loop()
    
    def visit_ListComp(self, node: ast.ListComp) -> None:
        """Visit list comprehension nodes."""
        self._analyze_comprehension('list_comp', node)
        self.generic_visit(node)
    
    def visit_SetComp(self, node: ast.SetComp) -> None:
        """Visit set comprehension nodes."""
        self._analyze_comprehension('set_comp', node)
        self.generic_visit(node)
    
    def visit_DictComp(self, node: ast.DictComp) -> None:
        """Visit dict comprehension nodes."""
        self._analyze_comprehension('dict_comp', node)
        self.generic_visit(node)
    
    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        """Visit generator expression nodes."""
        self._analyze_comprehension('generator', node)
        self.generic_visit(node)
    
    def generic_visit(self, node: ast.AST) -> None:
        """Generic visit method for other nodes."""
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        self.visit(item)
            elif isinstance(value, ast.AST):
                self.visit(value)
    
    def _enter_loop(self, loop_type: str, node: ast.AST) -> None:
        """Enter a new loop context."""
        self.current_nesting_level += 1
        
        # Extract loop information
        variable_name = None
        iterable_name = None
        
        if loop_type == 'for' and isinstance(node, ast.For):
            if isinstance(node.target, ast.Name):
                variable_name = node.target.id
            iterable_name = self._get_node_name(node.iter)
        
        loop_info = LoopInfo(
            type=loop_type,
            line_number=getattr(node, 'lineno', 0),
            nesting_level=self.current_nesting_level,
            parent_loops=self.loop_stack.copy(),
            variable_name=variable_name,
            iterable_name=iterable_name
        )
        
        self.loop_stack.append(loop_info)
        self.found_loops.append(loop_info)
    
    def _exit_loop(self) -> None:
        """Exit current loop context."""
        if self.current_nesting_level > 0:
            self.current_nesting_level -= 1
        if self.loop_stack:
            self.loop_stack.pop()
    
    def _analyze_comprehension(self, comp_type: str, node: ast.AST) -> None:
        """Analyze comprehension expressions for nested patterns."""
        # Count nested generators in comprehensions
        generators = []
        if hasattr(node, 'generators'):
            generators = node.generators
        
        nesting_level = len(generators)
        if nesting_level > 1:
            loop_info = LoopInfo(
                type=comp_type,
                line_number=getattr(node, 'lineno', 0),
                nesting_level=nesting_level,
                parent_loops=self.loop_stack.copy()
            )
            self.found_loops.append(loop_info)
    
    def _get_node_name(self, node: ast.AST) -> Optional[str]:
        """Extract name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_node_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            return node.func.id
        return None
    
    def _calculate_complexity_score(self) -> float:
        """Calculate a complexity score based on loop nesting."""
        if not self.found_loops:
            return 0.0
        
        score = 0.0
        for loop in self.found_loops:
            # Exponential penalty for deeper nesting
            nesting_penalty = 2 ** (loop.nesting_level - 1)
            
            # Different weights for different loop types
            type_weights = {
                'for': 1.0,
                'while': 1.2,  # While loops can be more problematic
                'list_comp': 0.8,  # Comprehensions are generally faster
                'set_comp': 0.8,
                'dict_comp': 0.8,
                'generator': 0.6,  # Generators are lazy
            }
            
            type_weight = type_weights.get(loop.type, 1.0)
            score += nesting_penalty * type_weight
        
        return score
    
    def _reset_state(self) -> None:
        """Reset analyzer state."""
        self.current_nesting_level = 0
        self.loop_stack.clear()
        self.found_loops.clear()


# Utility functions for common analysis tasks

def has_nested_loops(func: Callable) -> bool:
    """Check if function has nested loops."""
    analyzer = ASTAnalyzer()
    analysis = analyzer.analyze_function(func)
    return analysis.has_nested_loops if analysis else False


def get_loop_complexity(func: Callable) -> float:
    """Get loop complexity score for function."""
    analyzer = ASTAnalyzer()
    analysis = analyzer.analyze_function(func)
    return analysis.complexity_score if analysis else 0.0


def analyze_function_loops(func: Callable) -> Optional[FunctionAnalysis]:
    """Convenience function to analyze function loops."""
    analyzer = ASTAnalyzer()
    return analyzer.analyze_function(func)