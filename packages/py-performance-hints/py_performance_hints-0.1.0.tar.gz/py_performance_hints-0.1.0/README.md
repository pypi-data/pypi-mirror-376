# py-performance-hints

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Development Status](https://img.shields.io/badge/status-alpha-orange.svg)](https://pypi.org/project/py-performance-hints/)

Intelligent performance bottleneck detection for Python developers. Get real-time hints about performance anti-patterns in your code during development.

## 🚀 Quick Start

### Installation

```bash
pip install py-performance-hints
```

### Basic Usage

```python
from performance_hints import monitor_performance

@monitor_performance
def slow_function():
    import time
    time.sleep(0.15)  # This will trigger a warning
    return "completed"

slow_function()
```

**Output:**

```
[14:32:15] Performance hints for slow_function()
──────────────────────────────────────────────
⚠️ Slow execution: 151.2ms
  Function 'slow_function' took 151.2ms to execute (threshold: 100.0ms)
  💡 Suggestion: Check for inefficient loops or data structures • Consider optimizing algorithm complexity

──────────────────────────────────────────────
Total execution time: 151.2ms
```

## 🎯 Features (Phase 1)

- **🔍 Timing Detection**: Automatically detects functions that exceed time thresholds
- **🎨 Beautiful Console Output**: Colored, formatted output with clear suggestions
- **⚙️ Configurable**: Customize thresholds and detection patterns
- **🪶 Lightweight**: Minimal overhead (< 5% performance impact)
- **📊 Smart Suggestions**: Context-aware performance improvement tips

## 📖 Usage Examples

### Custom Threshold

```python
@monitor_performance(threshold_ms=50)
def critical_function():
    # Will warn if execution takes > 50ms
    pass
```

### Global Configuration

```python
from performance_hints import configure

configure(
    threshold_ms=75,
    detect_patterns=['timing'],
    report_format='console'
)
```

### Selective Monitoring

```python
# Only monitor in development
@monitor_performance(enabled=DEBUG)
def production_function():
    pass

# Disable for specific functions
@monitor_performance(enabled=False)
def unmonitored_function():
    pass
```

## ⚙️ Configuration

### Environment Variables

```bash
export PERFORMANCE_HINTS_ENABLED=true
export PERFORMANCE_HINTS_THRESHOLD_MS=100
export PERFORMANCE_HINTS_PATTERNS=timing
export PERFORMANCE_HINTS_FORMAT=console
```

### Programmatic Configuration

```python
from performance_hints import configure

configure(
    enabled=True,
    threshold_ms=100,
    detect_patterns=['timing'],
    report_format='console'
)
```

## 🛠️ Development Status

**Current Status: Phase 1 (Alpha)**

### ✅ Implemented

- Basic timing detection
- Console reporter with colors
- Configuration system
- Decorator interface

### 🚧 Coming in Phase 2

- N+1 query detection
- Nested loop analysis
- Memory usage monitoring
- JSON output format
- CI/CD integration

### 🔮 Future Phases

- IDE integration
- Performance dashboard
- Machine learning suggestions

## 🧪 Testing

Run the examples:

```bash
cd examples
python basic_usage.py
```

## 📝 Requirements

- Python 3.8+
- No external dependencies for core functionality

## 🤝 Contributing

This project is in early development. Contributions welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🔄 Changelog

### v0.1.0 (Phase 1 - Alpha)

- Initial release
- Basic timing detection
- Console output
- Configuration system
- Decorator interface

---

**Note**: This library is in alpha stage. APIs may change between versions.
