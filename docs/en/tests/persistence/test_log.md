# Log Persistence Tests (test_log.py)

> 📅 Last Updated: 2026/06/18

## Purpose
Validates `LogInlet` and `LogSpout` from `celestialflow.persistence.core_log`, ensuring that graph lifecycle events (start/end), task retry events, and node startup events can be asynchronously batch-flushed to a log file with the correct log level markers preserved.

## Core Test Objects

| Class | Description |
|----|------|
| `LogInlet` | Initialized with `log_level='INFO'`, provides `start_graph()` / `task_retry()` / `end_graph()` / `start_stage()` write methods |
| `LogSpout` | Background thread that batch-flushes records from the queue to a log file |

## Test Coverage Matrix

| Test Class | Case Count | Coverage Target |
|--------|--------|---------|
| `TestLogPersistence` | 1 | Full log lifecycle: start_graph → task_retry → end_graph → start_stage, verifying the log file contains all content and level markers |

## Key Test Scenarios

### `test_log_persistence`

- `start_graph("test_graph", ['test message'])` writes a graph startup message
- `task_retry('func', 'hello world', 1, ValueError('oops'), 0, 1)` writes a WARNING-level log with exception information
- `end_graph("test_graph", 1.0)` writes a graph end event
- `start_stage('stage', 'normal', 'parallel-4')` writes a node startup record
- Uses `wait_until` to poll until the log file exists and contains key content such as 'test message' and 'hello world'
- Ultimately asserts that the log file contains both `INFO` and `WARNING` level markers

## How to Run

```bash
pytest tests/persistence/test_log.py -v
pytest tests/persistence/test_log.py -k "log_persistence" -v
```

## Notes

- Tests use `monkeypatch.chdir(tmp_path)` to switch the working directory, ensuring log files are written to a temporary path
- The specific log file path is obtained via the `spout.log_path` property
- The related implementation is in `src/celestialflow/persistence/core_log.py`
