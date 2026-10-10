# tests/persist/test_log.py

> 📅 Last Updated: 2026/10/09

## Purpose
Validates `LogInlet` and `LogSpout` in `celestialflow.persist.core_log`, ensuring that graph lifecycle events (start / end), node start events, task retry events, and skip events can be asynchronously batch-flushed to a log file while preserving the correct log level markers.

## Core Test Objects

| Class / Object | Source | Description |
|-----------|------|------|
| `LogInlet` | `celestialflow.persist.core_log` | Initialized with `MetricsObserver` and `log_level`, provides event write methods such as `on_graph_start` / `on_task_retry` / `on_graph_end` / `on_node_start` / `on_task_skip` |
| `LogSpout` | `celestialflow.persist.core_log` | Background thread that batch-flushes records from the queue to a log file; the path is obtained via `spout.log_path` |
| `MetricsObserver` | `celestialflow.observer` | Provides node metrics for `LogInlet` to generate log content |
| Event types | `celestialflow.observer` | `GraphStartEvent` / `TaskRetryEvent` / `GraphEndEvent` / `NodeStartEvent` / `TaskSkipEvent` |

## Test Coverage Matrix

| Test Class | Case Count | Coverage Target |
|--------|--------|---------|
| `TestLogPersistence` | 2 | Full log lifecycle, skip log |

## Key Test Scenarios

### `test_log_persistence`

- Constructs `LogInlet(MetricsObserver(), log_level='INFO').bind_spout(spout)`, and `spout.start()` starts the background thread.
- Sequentially triggers `on_graph_start` (graph name / mode / structure list / node metadata), `on_task_retry` (carrying an exception → WARNING level), `on_graph_end`, `on_node_start`.
- Uses `wait_until` to poll until the log file exists and contains key content such as `| node |` and `hello world`.
- Finally asserts that the log file contains both `INFO` and `WARNING` level markers.

### `test_skip_log`

- Constructs `LogInlet(MetricsObserver(), log_level='SUCCESS').bind_spout(spout)`.
- Triggers `on_task_skip` (carrying the `[7->8*]` event ID range marker).
- Asserts that the log file contains `hello world`, `skipped`, `[7->8*]`, and the `SUCCESS` level marker.

## How to Run

```bash
pytest tests/persist/test_log.py -v
pytest tests/persist/test_log.py -k "log_persistence" -v
pytest tests/persist/test_log.py -k "skip" -v
```

## Notes

- Tests use `monkeypatch.chdir(tmp_path)` to switch the working directory, ensuring log files are written to the `logs/` directory under the temporary path.
- The specific log file path is obtained via the `spout.log_path` property.
- `LogInlet` binds to `LogSpout` via `bind_spout`; events are written asynchronously to the file through the queue.
- The related implementation is in `src/celestialflow/persist/core_log.py`.