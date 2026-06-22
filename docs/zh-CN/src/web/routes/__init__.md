# Web 路由组装入口

> 📅 最后更新日期: 2026/06/22

## 作用

`__init__.py`（即 `celestialflow.web.routes` 包入口）是整个 Web API 路由的组装起点。它创建一个 `APIRouter` 并将 **Pull**（数据拉取）和 **Push**（数据推送）两个子路由模块注册进去，同时注册根路径的页面入口。

## 核心函数

### `create_router(server: TaskWebServer) -> APIRouter`

创建并返回一个组装完成的 `APIRouter` 实例，供 FastAPI 应用挂载。

| 参数 | 类型 | 说明 |
|------|------|------|
| `server` | `TaskWebServer` | 任务 Web 服务器实例，路由通过该引用访问数据存储、配置等共享状态 |

**注册的路由：**

| 路径 | 方法 | 说明 |
|------|------|------|
| `/` | `GET` | 页面入口，返回 `templates/index.html` |
| `/api/pull_*` | `GET` | 由 `pull_routes.register()` 注册的全部拉取端点 |
| `/api/push_*` | `POST` | 由 `push_routes.register(router, server, config_path)` 注册的全部推送端点 |

**注册顺序：**

```
┌──────────────────────────────────────┐
│  APIRouter                           │
│                                      │
│  1. GET  /          (index.html)     │
│  2. GET  /api/pull_*                 │
│  3. POST /api/push_*                 │
└──────────────────────────────────────┘
```

所有路由共享同一个 `TaskWebServer` 实例，因此 Push 路由更新数据后 Pull 路由即可返回最新状态。

## 使用示例

```python
from celestialflow.web.routes import create_router
from celestialflow.web.core_server import TaskWebServer

server = TaskWebServer(...)
router = create_router(server)

# 挂载到 FastAPI 应用
from fastapi import FastAPI
app = FastAPI()
app.include_router(router)
```
