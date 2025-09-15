"""
Basic functionality tests for py-performance-hints.
"""

import time
import pytest
from performance_hints import monitor_performance, configure
from performance_hints.detectors.timing import TimingDetector
from performance_hints.detectors.loops import LoopDetector
from performance_hints.detectors.base import IssueLevel


class TestTimingDetector:
    """Test timing detection functionality."""
    
    def test_slow_function_detection(self):
        """Test that slow functions are detected."""
        detector = TimingDetector(threshold_ms=50)
        
        def slow_function():
            time.sleep(0.1)  # 100ms
            return "slow"
        
        # Test detection
        issues = detector.post_execute(
            slow_function, (), {}, "slow", 100.0
        )
        
        assert len(issues) == 1
        assert issues[0].level == IssueLevel.WARNING
        assert "slow execution" in issues[0].title.lower()
        assert issues[0].execution_time_ms == 100.0
    
    def test_fast_function_no_detection(self):
        """Test that fast functions don't trigger warnings."""
        detector = TimingDetector(threshold_ms=100)
        
        def fast_function():
            return "fast"
        
        issues = detector.post_execute(
            fast_function, (), {}, "fast", 50.0
        )
        
        assert len(issues) == 0
    
    def test_critical_threshold(self):
        """Test critical threshold detection."""
        detector = TimingDetector(threshold_ms=50)
        
        def very_slow_function():
            time.sleep(0.3)
            return "very_slow"
        
        # 5x threshold = critical
        issues = detector.post_execute(
            very_slow_function, (), {}, "very_slow", 250.0
        )
        
        assert len(issues) == 1
        assert issues[0].level == IssueLevel.CRITICAL


class TestLoopDetector:
    """Test loop detection functionality."""
    
    def test_nested_loop_detection(self):
        """Test detection of nested loops."""
        detector = LoopDetector(max_nesting_level=1)
        
        def nested_function():
            result = []
            for i in range(3):
                for j in range(3):  # This creates nesting level 2
                    result.append(i + j)
            return result
        
        # Pre-analyze the function
        detector.pre_execute(nested_function, (), {})
        
        # Check post-execution detection
        issues = detector.post_execute(
            nested_function, (), {}, [], 10.0
        )
        
        assert len(issues) > 0
        # Should detect nesting issue
        nesting_issues = [issue for issue in issues if "nesting" in issue.title.lower()]
        assert len(nesting_issues) > 0
        assert nesting_issues[0].level in [IssueLevel.WARNING, IssueLevel.CRITICAL]
    
    def test_simple_loop_no_detection(self):
        """Test that simple loops don't trigger warnings."""
        detector = LoopDetector(max_nesting_level=2)
        
        def simple_function():
            result = []
            for i in range(5):
                result.append(i * 2)
            return result
        
        detector.pre_execute(simple_function, (), {})
        issues = detector.post_execute(
            simple_function, (), {}, [], 5.0
        )
        
        # Should not trigger nesting warnings (only level 1)
        nesting_issues = [issue for issue in issues if "nesting" in issue.title.lower()]
        assert len(nesting_issues) == 0


class TestDecoratorIntegration:
    """Test the main decorator functionality."""
    
    def test_decorator_basic_usage(self):
        """Test basic decorator usage."""
        
        @monitor_performance(threshold_ms=50)
        def test_function():
            time.sleep(0.08)  # Should trigger warning
            return "test"
        
        # This should run without errors
        result = test_function()
        assert result == "test"
    
    def test_decorator_without_parentheses(self):
        """Test decorator usage without parentheses."""
        
        @monitor_performance
        def test_function():
            return "test"
        
        result = test_function()
        assert result == "test"
    
    def test_decorator_with_nested_loops(self):
        """Test decorator with nested loops."""
        
        @monitor_performance(detect_patterns=['nested_loops'])
        def nested_function():
            result = []
            for i in range(2):
                for j in range(2):
                    result.append(i + j)
            return result
        
        result = nested_function()
        assert len(result) == 4
    
    def test_disabled_decorator(self):
        """Test that disabled decorators don't interfere."""
        
        @monitor_performance(enabled=False)
        def test_function():
            time.sleep(0.1)  # Should not be monitored
            return "test"
        
        result = test_function()
        assert result == "test"


class TestConfiguration:
    """Test configuration system."""
    
    def test_global_configuration(self):
        """Test global configuration changes."""
        
        # Set custom config
        configure(
            threshold_ms=25,
            detect_patterns=['timing'],
            enabled=True
        )
        
        from performance_hints.config.settings import get_settings
        settings = get_settings()
        
        assert settings.threshold_ms == 25
        assert settings.detect_patterns == ['timing']
        assert settings.enabled == True
    
    def test_environment_variables(self):
        """Test loading from environment variables."""
        import os
        
        # Set environment variable
        os.environ['PERFORMANCE_HINTS_THRESHOLD_MS'] = '75'
        
        # Force reload settings
        from performance_hints.config.settings import _load_settings
        settings = _load_settings()
        
        assert settings.threshold_ms == 75.0
        
        # Cleanup
        del os.environ['PERFORMANCE_HINTS_THRESHOLD_MS']


class TestReporting:
    """Test reporting functionality."""
    
    def test_console_reporter(self):
        """Test console reporter doesn't crash."""
        from performance_hints.reporters.console import ConsoleReporter
        from performance_hints.detectors.base import PerformanceIssue
        
        reporter = ConsoleReporter(use_colors=False)  # Disable colors for testing
        
        def dummy_function():
            pass
        
        issue = PerformanceIssue(
            level=IssueLevel.WARNING,
            title="Test Issue",
            description="This is a test issue",
            suggestion="Fix the test issue"
        )
        
        # Should not raise any exceptions
        reporter.report(dummy_function, [issue], 100.0)
        assert reporter.report_count == 1


def run_manual_tests():
    """Run manual tests to see actual output."""
    
    print("🧪 Running manual tests...\n")
    
    # Test 1: Timing detection
    print("1. Testing timing detection:")
    
    @monitor_performance(threshold_ms=50)
    def slow_test():
        time.sleep(0.1)
        return "slow"
    
    slow_test()
    
    # Test 2: Loop detection
    print("\n2. Testing loop detection:")
    
    @monitor_performance(detect_patterns=['nested_loops'])
    def loop_test():
        result = []
        for i in range(3):
            for j in range(3):
                result.append(i * j)
        return result
    
    loop_test()
    
    # Test 3: Both detections
    print("\n3. Testing combined detection:")
    
    @monitor_performance
    def combined_test():
        time.sleep(0.05)
        result = []
        for i in range(2):
            for j in range(2):
                for k in range(2):  # Triple nesting!
                    result.append(i + j + k)
                    time.sleep(0.001)
        return result
    
    combined_test()
    
    print("\n✅ Manual tests completed!")


if __name__ == "__main__":
    # Run pytest tests
    pytest.main([__file__, "-v"])
    
    # Also run manual tests to see output
    print("\n" + "="*50)
    run_manual_tests()