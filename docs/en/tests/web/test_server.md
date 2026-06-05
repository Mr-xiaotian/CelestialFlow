# Web Service API Tests (test_server.py)

> Last Updated: 2026/05/23

## Purpose
Validates the RESTful API provided by `celestialflow.web.core_server`, ensuring the web dashboard can correctly display graph state, fetch configuration, inject tasks, and browse error logs.

## Key Test Objects
- `TaskWebServer`: Monitoring and interaction server implemented with FastAPI.

## Key Test Flow
1. **Static resource rendering**: Verifies that `/` returns an HTML page containing the `dashboard` container.
2. **Status synchronization (Rev mechanism)**:
   - Verifies that `push_status` stores snapshots correctly.
   - Verifies that `pull_status` supports incremental updates: when `known_rev` matches the current server revision, it returns empty data to save bandwidth.
3. **Task injection**: Verifies that tasks posted through the POST API are staged correctly and then consumed by the scheduler through the GET API.
4. **Error management**:
   - Verifies batch pushing of error records.
   - Verifies pagination logic, including `total_pages` and the current page size.
   - Verifies filtering logic so errors can be filtered by stage name.
5. **Configuration fetching**: Verifies that runtime parameters needed by the front end, such as refresh interval and theme, can be retrieved correctly.

## Test Focus
- **Rev version control**: Ensures the front-end refresh logic stays efficient and avoids redundant transfer.
- **Pagination accuracy**: Verifies offset calculations when the backend handles many error records.
- **Task consistency**: Ensures injected tasks are cleared after being fetched for consumption so they are not processed twice.

## How to Run

```bash
# Run all tests
pytest tests/web/test_server.py -v

# Run status synchronization tests only
pytest tests/web/test_server.py -k "status" -v
pytest tests/web/test_server.py -k "rev" -v

# Run task-injection tests only
pytest tests/web/test_server.py -k "inject" -v

# Run error-management tests only
pytest tests/web/test_server.py -k "error" -v

# Run configuration-fetch tests only
pytest tests/web/test_server.py -k "config" -v
```

## Performance Reference

| Test | Duration |
|------|----------|
| `TestTaskWebServer` | ~0.5s (mock HTTP requests) |

## Important Details
- Uses `FastAPI TestClient` for mocked requests.
- Task-injection tests use `datetime.now().isoformat()` to simulate realistic timestamps.

## Notes
- The web service is the visualization window of CelestialFlow.
- Related implementation: `src/celestialflow/web/core_server.py`.

