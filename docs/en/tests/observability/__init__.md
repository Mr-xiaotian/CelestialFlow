# observability Test Package

> 📅 Last Updated: 2026/06/11

## Purpose
`tests/observability/` covers runtime state observation and task injection mechanisms, ensuring `BaseObserver`/`CallbackObserver` lifecycle callbacks and `TaskReporter` task injection behavior meet expectations.

## Included Test Files
- `test_observer.py`: Covers Observer lifecycle callbacks, multi-observer support, dynamic management, and CallbackObserver.
- `test_reporter_injection.py`: Covers `TaskReporter._pull_and_inject_tasks()` node-mapping injection and logging logic.

## How to Run

```bash
pytest tests/observability -v
pytest tests/observability/test_observer.py -v
pytest tests/observability/test_reporter_injection.py -v
```
