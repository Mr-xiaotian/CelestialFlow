# Log Persistence Tests (test_log.py)

> 📅 Last Updated: 2026/06/05

## Purpose
Validates that `LogInlet` and `LogSpout` can asynchronously write log events such as graph startup, task retry, and node startup to a log file, preserving the corresponding level text.

## Coverage Points
- `start_graph()` writes a graph startup message.
- `task_retry()` writes a WARNING-level log with exception information.
- `start_stage()` writes a node startup record.

## Key Scenarios
- Start `LogSpout` in a temporary directory.
- Send three types of log events: graph startup, task retry, and node startup.
- Poll to check that the log file exists and contains key content such as `test message`, `hello world`, `INFO`, and `WARNING`.

## How to Run

```bash
pytest tests/persistence/test_log.py -v
pytest tests/persistence/test_log.py -k "log_persistence" -v
```
