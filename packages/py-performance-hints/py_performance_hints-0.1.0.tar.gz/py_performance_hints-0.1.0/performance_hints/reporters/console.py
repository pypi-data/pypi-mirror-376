"""
Console-based reporter for performance issues.
"""

import sys
from typing import Any, Callable, List
from datetime import datetime

from .base import BaseReporter
from ..detectors.base import PerformanceIssue, IssueLevel


class ConsoleReporter(BaseReporter):
    """Reports performance issues to console with colored output."""
    
    def __init__(self, enabled: bool = True, use_colors: bool = True):
        super().__init__(enabled)
        self.use_colors = use_colors and self._supports_color()
        
        # ANSI color codes
        self.colors = {
            'red': '\033[91m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'green': '\033[92m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'bold': '\033[1m',
            'reset': '\033[0m'
        }
        
        # Level color mapping
        self.level_colors = {
            IssueLevel.INFO: 'blue',
            IssueLevel.WARNING: 'yellow',
            IssueLevel.CRITICAL: 'red'
        }
        
        # Icons for different levels
        self.level_icons = {
            IssueLevel.INFO: 'ℹ️',
            IssueLevel.WARNING: '⚠️',
            IssueLevel.CRITICAL: '🚨'
        }
    
    def report(
        self, 
        func: Callable, 
        issues: List[PerformanceIssue], 
        execution_time_ms: float
    ) -> None:
        """Report performance issues to console."""
        
        if not self.enabled or not issues:
            return
        
        self._record_report()
        
        # Print header
        timestamp = datetime.now().strftime("%H:%M:%S")
        header = f"[{timestamp}] Performance hints for {func.__name__}()"
        
        print(f"\n{self._colorize(header, 'bold')}")
        print(f"{self._colorize('─' * len(header), 'cyan')}")
        
        # Print each issue
        for issue in issues:
            self._print_issue(issue)
        
        # Print summary
        print(f"{self._colorize('─' * len(header), 'cyan')}")
        total_time = f"Total execution time: {execution_time_ms:.1f}ms"
        print(f"{self._colorize(total_time, 'white')}\n")
    
    def _print_issue(self, issue: PerformanceIssue) -> None:
        """Print a single performance issue."""
        
        # Get level-specific formatting
        color = self.level_colors.get(issue.level, 'white')
        icon = self.level_icons.get(issue.level, '•')
        
        # Print title with icon
        title_line = f"{icon} {issue.title}"
        print(f"{self._colorize(title_line, color, bold=True)}")
        
        # Print description
        if issue.description:
            desc_lines = self._wrap_text(issue.description, indent=2)
            for line in desc_lines:
                print(f"  {self._colorize(line, 'white')}")
        
        # Print suggestion
        if issue.suggestion:
            print(f"  {self._colorize('💡 Suggestion:', 'green', bold=True)}")
            suggestion_lines = self._wrap_text(issue.suggestion, indent=4)
            for line in suggestion_lines:
                print(f"    {self._colorize(line, 'green')}")
        
        # Print additional details if available
        if issue.details and self._should_show_details():
            print(f"  {self._colorize('📊 Details:', 'cyan')}")
            for key, value in issue.details.items():
                if key not in ['function_name']:  # Skip redundant info
                    formatted_key = key.replace('_', ' ').title()
                    print(f"    {formatted_key}: {value}")
        
        print()  # Empty line between issues
    
    def _colorize(self, text: str, color: str, bold: bool = False) -> str:
        """Apply color to text if colors are enabled."""
        if not self.use_colors:
            return text
        
        color_code = self.colors.get(color, '')
        bold_code = self.colors['bold'] if bold else ''
        reset_code = self.colors['reset']
        
        return f"{bold_code}{color_code}{text}{reset_code}"
    
    def _wrap_text(self, text: str, width: int = 70, indent: int = 0) -> List[str]:
        """Wrap text to specified width with indentation."""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= width:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(' ' * indent + ' '.join(current_line))
                current_line = [word]
                current_length = len(word)
        
        if current_line:
            lines.append(' ' * indent + ' '.join(current_line))
        
        return lines
    
    def _supports_color(self) -> bool:
        """Check if the terminal supports color output."""
        return (
            hasattr(sys.stdout, 'isatty') and 
            sys.stdout.isatty() and 
            'TERM' in sys.__dict__.get('environ', {})
        )
    
    def _should_show_details(self) -> bool:
        """Determine if detailed information should be shown."""
        # Could be made configurable in the future
        return True