# tests/persistence/test_log.py

> 📅 Last Updated: 2026/09/24

## Purpose
Validates `LogInlet` and `LogSpout` from `celestialflow.persistence.core_log`, ensuring that graph lifecycle events (start/end), task retry events, and node startup events can be asynchronously batch-flushed to a log file with the correct log level markers preserved.

## Core Test Objects

| Class | Description |
|----|------|
| `LogInlet` | Initialized with `log_level='INFO'`, provides `graph_start()` / `task_retry()` / `graph_end()` / `node_start()` write methods |
| `LogSpout` | Background thread that batch-flushes records from the queue to a log file; the path is obtained via `spout.log_path` |

## Test Coverage Matrix

| Test Class | Case Count | Coverage Target |
|--------|--------|---------|
| `TestLogPersistence` | 1 | Full log lifecycle: graph_start → task_retry → graph_end → node_start, verifying the log file contains all content and level markers |

## Key Test Scenarios

### `test_log_persistence`

- `graph_start("test_graph", "thread", ['test message'])` writes a graph startup message (parameter order: graph name / graph mode / structure list).
- `task_retry('func', 'hello world', 1, ValueError('oops'), 0)` writes a WARNING-level log with exception information.
- `graph_end("test_graph", 1.0)` writes a graph end event and elapsed time.
- `node_start('stage', 1, 'parallel-4')` writes a node startup record (node name / task count / execution mode description).
- Uses `wait_until` to poll until the log file exists and contains key content such as 'test message' and 'hello world'.
- Ultimately asserts that the log file contains both `INFO` and `WARNING` level markers.

## How to Run

```bash
pytest tests/persistence/test_log.py -v
pytest tests/persistence/test_log.py -k "log_persistence" -v
```

## Notes

- Tests use `monkeypatch.chdir(tmp_path)` to switch the working directory, ensuring log files are written to the `logs/` directory under the temporary path.
- The specific log file path is obtained via the `spout.log_path` property.
- The related implementation is in `src/celestialflow/persistence/core_log.py`.

