# Runtime Route Assembly Entry

> 📅 Last Updated: 2026/05/28

## Purpose

`__init__.py` (i.e., the `celestialflow.web.routes` package entry) is the assembly entry point for all Web API routes. It creates an `APIRouter` and registers both the **Pull** (data fetching) and **Push** (data pushing) sub-route modules, along with the root path page entry.

## Core Function

### `create_router(server: TaskWebServer) -> APIRouter`

Creates and returns a fully assembled `APIRouter` instance for mounting on a FastAPI application.

| Parameter | Type | Description |
|-----------|------|-------------|
| `server` | `TaskWebServer` | Task Web server instance; routes access data stores, configuration, and other shared state through this reference |

**Registered Routes:**

| Path | Method | Description |
|------|--------|-------------|
| `/` | `GET` | Page entry, returns `templates/index.html` |
| `/api/pull_*` | `GET` | All fetch endpoints registered by `pull_routes.register()` |
| `/api/push_*` | `POST` | All push endpoints registered by `push_routes.register()` |

**Registration Order:**

```
┌──────────────────────────────────────┐
│  APIRouter                           │
│                                      │
│  1. GET  /          (index.html)     │
│  2. GET  /api/pull_*                 │
│  3. POST /api/push_*                 │
└──────────────────────────────────────┘
```

All routes share the same `TaskWebServer` instance, so Push route updates are immediately reflected in Pull route responses.

## Usage Example

```python
from celestialflow.web.routes import create_router
from celestialflow.web.core_server import TaskWebServer

server = TaskWebServer(...)
router = create_router(server)

# Mount to FastAPI application
from fastapi import FastAPI
app = FastAPI()
app.include_router(router)
```
