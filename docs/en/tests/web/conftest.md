# Web Test Configuration (conftest.py)

> 📅 Last Updated: 2026/05/23

## Purpose
Provides Pytest fixtures (web server and HTTP client) for test cases under the `tests/web` directory, simulating a real frontend-backend interaction environment.

## Core Fixtures
- `web_server`:
  - **Function**: Initializes a default-configured `TaskWebServer` instance.
  - **Scope**: Creates a new instance before each test function.
- `client`:
  - **Function**: Creates a synchronous HTTP client based on `FastAPI.testclient.TestClient`.
  - **Dependency**: Depends on the `web_server` fixture, directly accessing its internal `app` instance.

## Usage Example
```python
def test_api(client):
    response = client.get("/api/endpoint")
    assert response.status_code == 200
```

## Notes
- Tests use FastAPI's built-in `TestClient`, which does not actually start a listening port — execution is efficient and there is no port-conflict risk.
- Related implementation is in `src/celestialflow/web/core_server.py`.
