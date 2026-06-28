# Pull 路由（GET）— `pull_routes`

> 📅 最后更新日期: 2026/06/28

## 作用

`pull_routes` 模块提供客户端**拉取**数据的全部 GET 端点。大部分接口采用 **rev（版本号）守卫** 机制：当客户端传入已持有的 `known_rev` 与当前版本一致时，返回 `data: null` 以节省带宽；仅在数据变更时才返回完整数据体。

## 核心函数

### `register(router: APIRouter, server: TaskWebServer) -> None`

在给定的 `APIRouter` 上注册全部 7 个 GET 端点。

| 参数 | 类型 | 说明 |
|------|------|------|
| `router` | `APIRouter` | FastAPI 路由器实例 |
| `server` | `TaskWebServer` | 持有共享状态的 Web 服务器实例 |

---

## 端点

### 1. `GET /api/pull_server_state`

返回 reporter 同步决策所需的服务端状态。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `graph_id` | `str` | `""` | Reporter 当前任务图实例的唯一标识 |

**返回：** `dict[str, Any]` — 包含 `interval`、`is_current_graph`、`has_structure`、`has_analysis`、`max_event_id_in_fail`。

```json
{
  "interval": 5.0,
  "is_current_graph": true,
  "has_structure": true,
  "has_analysis": false,
  "max_event_id_in_fail": null
}
```

---

### 2. `GET /api/pull_injection`

取出并清空当前待执行的注入任务队列。这是一个**一次性消费**端点：返回后队列清空，同一批任务不会被重复获取。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| — | — | — | 无参数 |

**返回：** `{"tasks": dict[str, list[Any]], "terminations": list[str]}` — 包含待注入任务队列与终止符节点列表。读取后队列与集合清空。

```json
{
  "tasks": {"StageA": [1, 2, 3], "StageB": [{"id": 4, "val": "x"}]},
  "terminations": ["StageA"]
}
```

> 注意：虽然当前实现使用 GET，但这个端点具有副作用，会在读取后清空任务队列与终止符集合；它更接近"消费接口"而不是纯查询接口。

---

### 3. `GET /api/pull_config`

获取前端配置。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| — | — | — | 无参数 |

**返回：** `dict[str, Any]` — 完整的 `server.config` 字典，包含 `global`、`dashboard`、`errors`、`injection` 分组。

---

### 4. `GET /api/pull_structure`

获取图结构数据（节点与边），支持 rev 守卫。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `known_rev` | `int` | `-1` | 客户端已知的版本号 |

**返回：** `{"rev": int, "data": dict | None}` — `data` 为结构字典（含 `nodes`/`edges`/`source_nodes`）；若 `known_rev==rev` 则为 `null`。

---

### 5. `GET /api/pull_status`

获取各节点的运行状态，支持 rev 守卫。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `known_rev` | `int` | `-1` | 客户端已知的版本号 |

**返回：** `{"rev": int, "timestamp": float, "data": dict | None}`

---

### 6. `GET /api/pull_errors`

获取分页错误日志，支持节点/关键词过滤，支持 rev 守卫。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `known_rev` | `int` | `-1` | 客户端已知的版本号 |
| `page` | `int` | `1` | 页码（从 1 开始） |
| `page_size` | `int` | `10` | 每页条数 |
| `node` | `str` | `""` | 按节点名称过滤，空字符串不生效 |
| `keyword` | `str` | `""` | 按关键词过滤，空字符串不生效 |
| `sort_order` | `str` | `"newest"` | 排序方式，仅支持 `newest` / `oldest` |

**返回：** `{"rev": int, "page": int, "page_size": int, "total": int, "total_pages": int, "sort_order": str, "data": list | None}`

---

### 7. `GET /api/pull_analysis`

获取图拓扑分析信息。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `known_rev` | `int` | `-1` | 客户端已知的版本号（当前版本始终返回完整数据） |

**返回：** `{"rev": int, "data": dict | None}` — 当尚未产生分析数据时 `data` 为 `None`。

> **注意**：`pull_analysis` 不检查 `known_rev`，每次均返回完整数据（若分析数据存在）。此行为与 `pull_status`/`pull_structure`/`pull_errors` 不同。

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
