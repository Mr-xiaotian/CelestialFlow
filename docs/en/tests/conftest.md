# tests/conftest.py

> 📅 Last Updated: 2026/09/09

## Purpose
Serves as the root-level configuration file for the entire `tests/` directory, responsible for initializing the test environment, loading environment variables, and providing common test helper functions.

## Core Functionality

### Environment Variable Loading
- Automatically calls `dotenv.load_dotenv()` to ensure configuration from the `.env` file at the project root is available at test startup.

### Common Test Helper Functions

| Function | Purpose | Key Parameters |
|----------|---------|----------------|
| `wait_until(condition, *, timeout, interval, message)` | Polls until a condition becomes true, providing a unified synchronization pattern for background threads | `timeout=5.0`, `interval=0.05` |
| `assert_stays_true(condition, *, duration, interval, message)` | Continuously asserts that a condition remains true over a short duration | `duration=0.3`, `interval=0.05` |

> `wait_until` is commonly used to wait for a spout background thread to finish consuming. `assert_stays_true` is used to verify that a stopped spout no longer processes new records.

## Notes
- This file is automatically recognized by Pytest.
- This file does not define any `pytest.fixture`; it only provides the two test helper functions `wait_until` / `assert_stays_true` and `.env` loading logic. If you need to add a global-level fixture, it should be defined in this file.
