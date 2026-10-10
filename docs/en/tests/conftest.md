# tests/conftest.py

> 📅 Last Updated: 2026/10/09

## Purpose
Serves as the root-level configuration file for the entire `tests/` directory, responsible for loading environment variables and providing common test helper functions, unifying the way background thread synchronization and running-node metric observer access are handled in tests.

## Core Functionality

### Environment Variable Loading
- Automatically calls `dotenv.load_dotenv()` to ensure configuration from the `.env` file at the project root is available at test startup.

### Common Test Helper Functions

| Function | Purpose | Key Parameters |
|------|------|----------|
| `metrics_of(node)` | Retrieves the `MetricsObserver` metric observer from the running node's `observers` hub snapshot, for assertions reading node metrics | Iterates `node.observers._snapshot()`; throws `AssertionError` when not found |
| `wait_until(condition, *, timeout, interval, message)` | Polls until a condition becomes true, providing a unified synchronization pattern for background threads | `timeout=5.0`, `interval=0.05` |
| `assert_stays_true(condition, *, duration, interval, message)` | Continuously asserts that a condition remains true over a short duration | `duration=0.3`, `interval=0.05` |

> **Note**: The node itself no longer holds a `metrics` field. After the refactor, the metric observer is registered by the runtime entry point on `node.observers`, and `metrics_of()` retrieves that observer from the hub snapshot for test assertions (e.g., `metrics_of(executor).get_node_metrics(executor.get_name()).succeeded`).

> `wait_until` is commonly used to wait for a spout background thread to finish consuming. `assert_stays_true` is used to verify that a stopped spout no longer processes new records.

## Notes
- This file is automatically recognized by Pytest.
- This file does not define any `pytest.fixture`; it only provides the three test helper functions `metrics_of` / `wait_until` / `assert_stays_true` and `.env` loading logic. If you need to add a global-level fixture, it should be defined in this file.