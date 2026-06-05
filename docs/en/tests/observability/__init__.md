# observability Test Package

> Last Updated: 2026/06/05

## Purpose
`tests/observability/` covers runtime status reporting and the observation pipeline, ensuring observer components such as `TaskReporter` can stably pull graph status and expose it externally.

## Included Test Files
- `test_reporter.py`: Covers reporter startup, shutdown, polling, and exception paths.

## How to Run

```bash
pytest tests/observability -v
pytest tests/observability/test_reporter.py -v
```

