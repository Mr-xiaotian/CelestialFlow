# Push 路由（POST）— `push_routes`

> 📅 最后更新日期: 2026/06/28

## 作用

`push_routes` 模块提供 **Reporter（上报端）** 向服务端**推送**数据的全部 POST 端点。每次推送会更新对应的内存存储并递增版本号（`store_revs`），使客户端通过 Pull 路由感知到数据变化。所有 reporter 端推送均需携带 `graph_id`，服务端会校验是否为当前 graph 实例。

## 核心函数

### `register(router: APIRouter, server: TaskWebServer, config_path: str) -> None`

在给定的 `APIRouter` 上注册全部 7 个 POST 端点。

| 参数 | 类型 | 说明 |
|------|------|------|
| `router` | `APIRouter` | FastAPI 路由器实例 |
| `server` | `TaskWebServer` | 持有共享状态的 Web 服务器实例 |
| `config_path` | `str` | 配置文件的磁盘路径，用于持久化保存配置 |

---

## 端点

### 1. `POST /api/push_config`

保存前端配置并更新轮询间隔。

**请求体：** `WebConfigModel`

```json
{
  "global": {
    "theme": "dark",
    "autoRefreshEnabled": true,
    "refreshInterval": 5000,
    "language": "zh-CN"
  },
  "dashboard": {
    "historyLimit": 20,
    "showStructureEdgeDelta": false,
    "useTotalPendingInStatus": false,
    "layout": { "left": ["mermaid"], "middle": ["status"], "right": ["progress"] }
  },
  "errors": {
    "pageSize": 10,
    "sortOrder": "newest",
    "jumpToInjectionAfterRetry": true
  },
  "injection": {
    "showInjectableOnly": true
  }
}
```

**逻辑：**
1. 将请求体反序列化为字典，更新 `server.config`
2. 根据 `refreshInterval` 值重新计算 `server.report_interval`
3. 调用 `save_config()` 将配置持久化到 `config_path`
4. 若保存成功返回 `{"ok": true}`，否则返回 HTTP 500

> 注意：当前实现会先更新内存中的 `server.config` 与 `server.report_interval`，再尝试落盘；如果 `save_config()` 失败，请求虽然返回 500，但进程内配置已经变更。

**返回：**
- 成功：`{"ok": true}`
- 失败：`{"ok": false, "error": "Failed to save config"}`（状态码 500）

---

### 2. `POST /api/push_structure`

更新图结构数据。

**请求体：** `StructureModel`（包含 `graph_id` 和 `structure` 字段）

```json
{
  "graph_id": "graph-001",
  "structure": {
    "nodes": {"n1": {"label": "MyTask"}},
    "edges": {"n1": []},
    "source_nodes": ["n1"]
  }
}
```

**逻辑：**
1. 校验 `data.graph_id` 是否为当前 graph 上下文，不匹配则返回 `{"ok": false}`
2. 将 `data.structure` 原子写入 `server.structure_store`
3. `server.store_revs["structure"]` 自增 1

**返回：** `{"ok": true}` 或 `{"ok": false}`

---

### 3. `POST /api/push_status`

更新各节点运行状态。

**请求体：** `StatusModel`（包含 `graph_id`、`timestamp` 和 `status` 字段）

```json
{
  "graph_id": "graph-001",
  "timestamp": 1716883200.5,
  "status": {"node_a": "running", "node_b": "success"}
}
```

**逻辑：**
1. 校验 `data.graph_id` 是否为当前 graph 上下文
2. 更新 `server.status_timestamp` 和 `server.status_store`
3. `server.store_revs["status"]` 自增 1

**返回：** `{"ok": true}` 或 `{"ok": false}`

---

### 4. `POST /api/push_errors`

直接接收错误日志列表并写入 SQLite。

**请求体：** `ErrorsModel`（包含 `graph_id` 和 `errors` 字段）

```json
{
  "graph_id": "graph-001",
  "errors": [
    {"ts": "2026-06-18T10:00:00", "error_id": "e1", "error_type": "ValueError", "error_message": "..."}
  ]
}
```

**逻辑：**
1. 校验 `data.graph_id` 是否为当前 graph 上下文
2. 调用 `append_records` 将错误写入 SQLite 数据库
3. `server.store_revs["errors"]` 自增 1

**返回：** `{"ok": true}` 或 `{"ok": false}`

---

### 5. `POST /api/push_analysis`

更新图拓扑分析信息。

**请求体：** `AnalysisModel`（包含 `graph_id` 和 `analysis` 字段）

```json
{
  "graph_id": "graph-001",
  "analysis": {"root_count": 3, "max_depth": 5}
}
```

**逻辑：**
1. 校验 `data.graph_id` 是否为当前 graph 上下文
2. 更新 `server.analysis_store`
3. `server.store_revs["analysis"]` 自增 1

**返回：** `{"ok": true}` 或 `{"ok": false}`

---

### 6. `POST /api/push_injection_tasks`

将前端提交的注入任务写入到待执行队列。

**请求体：** `TaskInjectionModel`（`RootModel[dict[str, list[Any]]]`）

```json
{
  "StageA": [1, 2, 3],
  "StageB": [{"id": 4, "val": "x"}]
}
```

**逻辑：**
1. 持有 `task_injection_lock` 锁
2. 遍历 `data.root`，以 `{node_name: task_list}` 方式写入 `server.injection_tasks`
3. 释放锁

> 注意：请求体直接为 `{节点名: [任务列表]}` 格式的字典，不再包装 `node`/`task_datas`/`timestamp` 字段。每个节点名对应的任务列表会**覆盖**该节点已有的待注入任务（而非追加）。

**返回：**
- 成功：`{"ok": true}`
- 失败：`{"ok": false, "msg": "任务注入失败: ..."}`（状态码 500）

---

### 7. `POST /api/push_injection_terminations`

将前端提交的终止符注入目标追加到待执行集合。

**请求体：** `TerminationInjectionModel`（`RootModel[list[str]]`）

```json
[
  "StageA",
  "StageB"
]
```

> 注意：请求体直接为节点名字符串列表，每个节点名会被加入服务端的终止符集合；重复节点名会自动去重（集合语义）。

**逻辑：**
1. 持有 `task_injection_lock` 锁
2. 遍历 `data.root`，将节点名加入 `server.injection_terminations` 集合
3. 释放锁

**返回：**
- 成功：`{"ok": true}`
- 失败：`{"ok": false, "msg": "终止符注入失败: ..."}`（状态码 500）

---

## 使用示例

### Reporter 端推送状态与错误

```python
import requests

BASE = "http://localhost:8000"

# 推送节点状态
requests.post(f"{BASE}/api/push_status", json={
    "graph_id": "graph-001",
    "timestamp": 1716883200.5,
    "status": {
        "node_a": {"state": "running", "pending": 0},
        "node_b": {"state": "success", "pending": 0}
    }
})

# 推送错误日志
requests.post(f"{BASE}/api/push_errors", json={
    "graph_id": "graph-001",
    "errors": [
        {"ts": "2026-06-18T10:00:00", "error_id": "e1", "error_type": "ValueError", "error_message": "Invalid input"}
    ]
})

# 推送结构数据
requests.post(f"{BASE}/api/push_structure", json={
    "graph_id": "graph-001",
    "structure": {
        "nodes": {"n1": {"label": "MyTask"}},
        "edges": {"n1": []},
        "source_nodes": ["n1"],
    }
})
```

### Web 前端保存配置

```javascript
const resp = await fetch("/api/push_config", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    global: {
      theme: "dark",
      autoRefreshEnabled: true,
      refreshInterval: 10000,
      language: "zh-CN",
    },
    dashboard: {
      historyLimit: 20,
      showStructureEdgeDelta: false,
      useTotalPendingInStatus: false,
      layout: { left: ["mermaid"], middle: ["status"], right: ["progress"] }
    },
    errors: {
      pageSize: 10,
      sortOrder: "newest",
      jumpToInjectionAfterRetry: true,
    },
    injection: {
      showInjectableOnly: true,
    },
  })
});
const result = await resp.json();
console.log(result.ok ? "保存成功" : "保存失败");
```
