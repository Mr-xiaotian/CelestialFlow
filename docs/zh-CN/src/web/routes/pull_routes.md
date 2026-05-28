# Pull 路由（GET）— `pull_routes`

> 📅 最后更新日期: 2026/05/28

## 作用

`pull_routes` 模块提供客户端**拉取**数据的全部 GET 端点。这些接口采用 **rev（版本号）守卫** 机制：当客户端传入已持有的 `known_rev` 与当前版本一致时，返回 `data: null` 以节省带宽；仅在数据变更时才返回完整数据体。

## 核心函数

### `register(router: APIRouter, server: TaskWebServer) -> None`

在给定的 `APIRouter` 上注册全部 8 个 GET 端点。

| 参数 | 类型 | 说明 |
|------|------|------|
| `router` | `APIRouter` | FastAPI 路由器实例 |
| `server` | `TaskWebServer` | 持有共享状态的 Web 服务器实例 |

---

## 端点

### 1. `GET /api/pull_config`

获取前端配置。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| — | — | — | 无参数 |

**返回：** `dict[str, Any]` — 完整的 `server.config` 字典。

```json
{
  "refreshInterval": "5",
  "dashboard": { "left": ["mermaid"], "middle": ["status"], ... },
  ...
}
```

---

### 2. `GET /api/pull_structure`

获取图结构数据（节点与边），支持 rev 守卫。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `known_rev` | `int` | `-1` | 客户端已知的版本号 |

**返回：**

| 字段 | 说明 |
|------|------|
| `rev` | 当前版本号 |
| `data` | 结构数据列表；若 `known_rev==rev` 则为 `null` |

```json
// 有更新
{"rev": 5, "data": [{"id": "n1", "type": "task", ...}]}
// 无更新
{"rev": 5, "data": null}
```

---

### 3. `GET /api/pull_status`

获取各节点的运行状态，支持 rev 守卫。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `known_rev` | `int` | `-1` | 客户端已知的版本号 |

**返回：**

| 字段 | 说明 |
|------|------|
| `rev` | 当前版本号 |
| `timestamp` | 状态时间戳（float） |
| `data` | 节点状态字典；无变化时为 `null` |

```json
{"rev": 3, "timestamp": 1716883200.5, "data": {"n1": "success", ...}}
```

---

### 4. `GET /api/pull_errors`

获取分页错误日志，支持节点/关键词过滤，支持 rev 守卫。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `known_rev` | `int` | `-1` | 客户端已知的版本号 |
| `page` | `int` | `1` | 页码（从 1 开始） |
| `page_size` | `int` | `10` | 每页条数 |
| `node` | `str` | `""` | 按节点名称过滤，空字符串不生效 |
| `keyword` | `str` | `""` | 按关键词过滤，空字符串不生效 |

**返回：**

| 字段 | 说明 |
|------|------|
| `rev` | 当前版本号 |
| `page` | 归一化后的页码 |
| `page_size` | 归一化后的每页大小 |
| `total` | 过滤后的总条数 |
| `total_pages` | 总页数 |
| `data` | 当前页错误列表；无变化时为 `null` |

```json
{
  "rev": 12, "page": 1, "page_size": 10,
  "total": 47, "total_pages": 5,
  "data": [{"ts": "...", "error_id": "...", "error_repr": "..."}, ...]
}
```

---

### 5. `GET /api/pull_analysis`

获取图拓扑分析信息，支持 rev 守卫。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `known_rev` | `int` | `-1` | 客户端已知的版本号 |

**返回：** `{"rev": int, "data": dict | None}`

```json
{"rev": 2, "data": {"root_count": 3, "max_depth": 5, ...}}
```

---

### 6. `GET /api/pull_summary`

获取全局任务汇总数据，支持 rev 守卫。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `known_rev` | `int` | `-1` | 客户端已知的版本号 |

**返回：** `{"rev": int, "data": dict | None}`

```json
{"rev": 1, "data": {"total": 42, "success": 38, "failed": 4, ...}}
```

---

### 7. `GET /api/pull_interval`

获取当前轮询间隔。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| — | — | — | 无参数 |

**返回：** `{"interval": float}` — 单位为秒。

```json
{"interval": 5.0}
```

---

### 8. `GET /api/pull_task_injection`

取出并清空当前待执行的注入任务队列。这是一个**一次性消费**端点：返回后队列清空，同一批任务不会被重复获取。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| — | — | — | 无参数 |

**返回：** `list[dict[str, Any]]`

```json
[{"task_id": "...", "params": {...}}, ...]
```

## 使用示例

```python
# 轮询拉取结构数据，仅在版本变化时处理
import requests

# 初始请求
resp = requests.get("http://localhost:8000/api/pull_structure")
data = resp.json()
known_rev = data["rev"]
if data["data"] is not None:
    render_structure(data["data"])

# 后续轮询
while True:
    resp = requests.get(
        "http://localhost:8000/api/pull_structure",
        params={"known_rev": known_rev}
    )
    data = resp.json()
    if data["data"] is not None:
        known_rev = data["rev"]
        render_structure(data["data"])
    time.sleep(5)
```
