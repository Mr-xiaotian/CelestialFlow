# Web Test Configuration (conftest.py)

> Last Updated: 2026/05/23

## Purpose
Provides pytest fixtures for the web server and HTTP client used by the test cases under `tests/web`, simulating a realistic front-end/back-end interaction environment.

## Core Fixtures
- `web_server`:
  - **Function**: Initializes a `TaskWebServer` instance with default configuration.
  - **Scope**: Creates a fresh instance before each test function.
- `client`:
  - **Function**: Creates a synchronous HTTP client based on `FastAPI.testclient.TestClient`.
  - **Dependency**: Depends on the `web_server` fixture and accesses its internal `app` directly.

## Usage Example
```python
def test_api(client):
    response = client.get("/api/endpoint")
    assert response.status_code == 200
```

## Notes
- The tests use FastAPI's built-in `TestClient`, so no real port listener is started. Execution stays fast and avoids port conflicts.
- Related implementation: `src/celestialflow/web/core_server.py`.

