"""
py-performance-hints: Intelligent performance bottleneck detection for Python developers.
"""

__version__ = "0.1.0"

from .decorators import monitor_performance
from .config.settings import configure

__all__ = [
    "monitor_performance",
    "configure",
    "__version__",
]