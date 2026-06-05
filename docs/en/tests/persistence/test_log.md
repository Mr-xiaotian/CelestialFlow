# Log Persistence Tests (test_log.py)

> Last Updated: 2026/06/05

## Purpose
Validates that `LogInlet` and `LogSpout` asynchronously write graph-start, task-retry, and stage-start log events into a log file while preserving the corresponding level text.

## Coverage
- `start_graph()` writes a graph-start message.
- `task_retry()` writes a WARNING-level log with exception information.
- `start_stage()` writes a stage-start record.

## Key Scenarios
- Start `LogSpout` in a temporary directory.
- Send three kinds of log events: graph start, task retry, and stage start.
- Poll until the log file exists and contains key fragments such as `test message`, `hello world`, `INFO`, and `WARNING`.

## How to Run

```bash
pytest tests/persistence/test_log.py -v
pytest tests/persistence/test_log.py -k "log_persistence" -v
```

