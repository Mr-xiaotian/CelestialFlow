# tests/conftest.py

> 📅 Last Updated: 2026/11/13

## Purpose
Serves as the root-level configuration file for the entire `tests/` directory, responsible for loading environment variables and providing common test helper functions, unifying the way tests access background thread synchronization, running-node metric observers, and lifecycle databases.

## Core Functionality

### Environment Variable Loading
- Automatically calls `dotenv.load_dotenv()` to ensure configuration from the `.env` file at the project root is available at test startup.

### Common Test Helper Functions

| Function | Purpose | Key Parameters / Behavior |
|------|------|----------|
| `metrics_of(node)` | Retrieves the `MetricsObserver` on the node hub, for assertions reading metrics | Calls `node.observers.find(MetricsObserver)`; throws `AssertionError` when not registered |
| `lifecycle_db_of(target)` | Retrieves the lifecycle database path from the target's hub | Calls `target.get_observers()` for a task graph and reads `target.observers` for a node, then `find(LifecycleObserver)` and returns its `db_path`; throws `AssertionError` when not registered or not started (`db_path is None`) |
| `wait_until(condition, *, timeout, interval, message)` | Polls until a condition becomes true, providing a unified synchronization pattern for background threads | `timeout=5.0`, `interval=0.05`; checks once more after the timeout and calls `pytest.fail(message)` if still not satisfied |
| `assert_stays_true(condition, *, duration, interval, message)` | Continuously asserts that a condition remains true over a short duration | `duration=0.3`, `interval=0.05`; any sampling point that fails calls `pytest.fail(message)` |

> **Note**: Nodes no longer hold `metrics` / `lifecycle` fields themselves; the relevant observers are registered by the runtime entry point on `node.observers`. `ObserverHub.find()` first searches the current level and then recurses into nested hubs, so graph-level observers injected at graph runtime can also be found by `metrics_of(graph)` / `lifecycle_db_of(graph)`.

> `wait_until` is commonly used to wait for a spout background thread to finish consuming or for lifecycle / log to be written to disk; `assert_stays_true` is used to verify that a stopped spout no longer processes new records.

## Notes
- This file is automatically recognized by Pytest as a root-level `conftest.py`.
- This file does not define any `pytest.fixture`; it only provides the four test helper functions `metrics_of` / `lifecycle_db_of` / `wait_until` / `assert_stays_true` and `.env` loading logic. If you need to add a global-level fixture, it should be defined in this file.
- `lifecycle_db_of` requires that `LifecycleObserver` has already been initialized via `start()`; otherwise `db_path` is `None` and the assertion fails.