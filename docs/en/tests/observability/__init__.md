# observability Test Package

> 📅 Last Updated: 2026/06/18

## Purpose
`tests/observability/` covers runtime state observation and task injection/reporting mechanisms, ensuring `BaseObserver` lifecycle callbacks and `TaskReporter` task injection and error push behavior meet expectations.

## Included Test Files
- `test_observer.py`: Covers Observer lifecycle callbacks, multi-observer support, and dynamic management.
- `test_reporter_injection.py`: Covers `TaskReporter._pull_and_inject_tasks()` node-mapping injection and logging logic.

## How to Run

```bash
pytest tests/observability -v
pytest tests/observability/test_observer.py -v
pytest tests/observability/test_reporter_injection.py -v
```
