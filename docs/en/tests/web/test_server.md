# Web Service API Tests (test_server.py)

> 📅 Last Updated: 2026/06/11

## Purpose
Validates the RESTful API provided by `celestialflow.web.core_server`, ensuring the web dashboard can correctly display graph state, pull configuration, inject tasks, and browse error logs, while also verifying snapshot data isolation.

## Core Test Target
- `TaskWebServer`: A monitoring and interaction server built on FastAPI.

## Key Test Scenarios

### Snapshot Isolation
- `test_store_snapshot_methods_return_isolated_copies`: Validates that the server's snapshot API methods return deep copies; modifying the return value does not affect the internal store.

### Static Asset Rendering
- `test_index_page`: Validates that the homepage `/` correctly returns an HTML page containing the `dashboard` container.

### Config Pull
- `test_config_api`: Validates that runtime parameters needed by the frontend (refresh frequency, theme, etc.) can be correctly fetched.

### Status Sync (Rev Mechanism)
- `test_status_push_pull`:
  - Validates that `push_status` successfully saves a snapshot.
  - Validates that `pull_status` supports incremental updates: when `known_rev` matches the server's current revision, empty data is returned to save bandwidth.

### Task Injection
- `test_task_injection`: Validates that tasks injected via the POST endpoint are correctly staged and consumed by the scheduler via the GET endpoint; consumed tasks are cleared.
- `test_task_injection_overwrites_tasklist_per_node`: Validates that a new push updates the task list per-node rather than appending.
- `test_task_injection_requires_tasklist_mapping`: Validates that an invalid payload (non-list value) returns 422.

### Error Management
- `test_errors_pagination`:
  - Validates batch push of error records.
  - Validates pagination logic: checks `total_pages`, `total`, and current-page data count.
  - Validates per-node (`node`) filtering logic.
  - Validates keyword (`keyword`) filtering logic.
  - Validates sort order (`sort_order`): supports both `newest` and `oldest`.

## Test Focus
- **Rev version control**: Ensures efficient frontend refresh logic, avoiding redundant data transfer.
- **Pagination accuracy**: Validates offset calculation when the backend processes error records.
- **Task consistency**: Ensures injected tasks are correctly cleared after being pulled and consumed, preventing duplicate processing.
- **Snapshot isolation**: Ensures that data fetched by the frontend does not become inconsistent due to internal state mutations.

## How to Run

```bash
# Run all
pytest tests/web/test_server.py -v

# Run status sync tests only
pytest tests/web/test_server.py -k "status" -v

# Run task injection tests only
pytest tests/web/test_server.py -k "injection" -v

# Run error management tests only
pytest tests/web/test_server.py -k "errors" -v

# Run config pull tests only
pytest tests/web/test_server.py -k "config" -v
```

## Important Details
- Uses `FastAPI TestClient` for simulated requests; no real listening port is started.
- Snapshot isolation tests directly operate on the `web_server` fixture (provided by `conftest.py`), while other tests use the `client` fixture.
- Tests create a fresh server instance before each test function.

## Notes
- The Web service is the visualization window for CelestialFlow.
- Related implementation is in `src/celestialflow/web/core_server.py`.
