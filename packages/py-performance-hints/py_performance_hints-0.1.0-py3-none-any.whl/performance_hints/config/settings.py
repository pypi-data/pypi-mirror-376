"""
Configuration management for performance hints.
"""

import os
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Settings:
    """Configuration settings for performance monitoring."""
    
    # Detection settings
    enabled: bool = True
    detect_patterns: List[str] = None
    threshold_ms: float = 100.0
    
    # Reporting settings
    report_format: str = "console"
    output_file: Optional[str] = None
    
    # Performance settings
    max_overhead_percent: float = 5.0
    sampling_rate: float = 1.0  # 1.0 = monitor every call
    
    def __post_init__(self):
        if self.detect_patterns is None:
            self.detect_patterns = ['timing', 'nested_loops']


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the current settings instance."""
    global _settings
    if _settings is None:
        _settings = _load_settings()
    return _settings


def configure(**kwargs) -> None:
    """
    Configure performance monitoring settings.
    
    Args:
        enabled: Enable/disable monitoring
        detect_patterns: List of patterns to detect
        threshold_ms: Time threshold for warnings
        report_format: Output format
        **kwargs: Other settings
        
    Example:
        configure(
            enabled=True,
            detect_patterns=['timing'],
            threshold_ms=50
        )
    """
    global _settings
    
    current = get_settings()
    
    # Update settings with provided values
    new_settings = Settings(
        enabled=kwargs.get('enabled', current.enabled),
        detect_patterns=kwargs.get('detect_patterns', current.detect_patterns),
        threshold_ms=kwargs.get('threshold_ms', current.threshold_ms),
        report_format=kwargs.get('report_format', current.report_format),
        output_file=kwargs.get('output_file', current.output_file),
        max_overhead_percent=kwargs.get('max_overhead_percent', current.max_overhead_percent),
        sampling_rate=kwargs.get('sampling_rate', current.sampling_rate),
    )
    
    _settings = new_settings


def _load_settings() -> Settings:
    """Load settings from environment variables or defaults."""
    
    # Load from environment variables
    enabled = os.getenv('PERFORMANCE_HINTS_ENABLED', 'true').lower() == 'true'
    
    patterns_str = os.getenv('PERFORMANCE_HINTS_PATTERNS', 'timing,nested_loops')
    detect_patterns = [p.strip() for p in patterns_str.split(',') if p.strip()]
    
    threshold_ms = float(os.getenv('PERFORMANCE_HINTS_THRESHOLD_MS', '100'))
    
    report_format = os.getenv('PERFORMANCE_HINTS_FORMAT', 'console')
    
    return Settings(
        enabled=enabled,
        detect_patterns=detect_patterns,
        threshold_ms=threshold_ms,
        report_format=report_format,
    )