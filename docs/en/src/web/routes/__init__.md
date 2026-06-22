# Web Route Assembly Entry

> 📅 Last Updated: 2026/06/22

## Purpose

`__init__.py` (i.e. the `celestialflow.web.routes` package entry) is the assembly starting point for the entire Web API routing. It creates an `APIRouter` and registers both the **Pull** (data fetch) and **Push** (data push) sub-route modules into it, while also registering the root path page entry.

## Core Function

### `create_router(server: TaskWebServer) -> APIRouter`

Creates and returns an assembled `APIRouter` instance for the FastAPI application to mount.

| Parameter | Type | Description |
|-----------|------|-------------|
| `server` | `TaskWebServer` | Task web server instance; routes access shared state such as data stores and configuration through this reference |

**Registered routes:**

| Path | Method | Description |
|------|--------|-------------|
| `/` | `GET` | Page entry, returns `templates/index.html` |
| `/api/pull_*` | `GET` | All pull endpoints registered by `pull_routes.register()` |
| `/api/push_*` | `POST` | All push endpoints registered by `push_routes.register(router, server, config_path)` |

**Registration order:**

```
┌──────────────────────────────────────┐
│  APIRouter                           │
│                                      │
│  1. GET  /          (index.html)     │
│  2. GET  /api/pull_*                 │
│  3. POST /api/push_*                 │
└──────────────────────────────────────┘
```

All routes share the same `TaskWebServer` instance, so after Push routes update data, Pull routes can immediately return the latest state.

## Usage Example

```python
from celestialflow.web.routes import create_router
from celestialflow.web.core_server import TaskWebServer

server = TaskWebServer(...)
router = create_router(server)

# Mount to FastAPI app
from fastapi import FastAPI
app = FastAPI()
app.include_router(router)
```
