# Push 路由（POST）— `push_routes`

> 📅 最后更新日期: 2026/05/28

## 作用

`push_routes` 模块提供 **Reporter（上报端）** 向服务端**推送**数据的全部 POST 端点。每次推送会更新对应的内存存储并递增版本号（`store_revs`），使客户端通过 Pull 路由感知到数据变化。错误数据支持**缓存命中**优化（path + rev 不变则跳过重加载）。

## 核心函数

### `register(router: APIRouter, server: TaskWebServer, config_path: str) -> None`

在给定的 `APIRouter` 上注册全部 8 个 POST 端点。

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
  "refreshInterval": "5",
  "dashboard": { "left": ["mermaid"], "middle": ["status"], "right": ["progress"] },
  ...
}
```

**逻辑：**
1. 将请求体反序列化为字典，更新 `server.config`
2. 根据 `refreshInterval` 值重新计算 `server.report_interval`
3. 调用 `save_config()` 将配置持久化到 `config_path`
4. 若保存成功返回 `{"ok": true}`，否则返回 HTTP 500

**返回：**
- 成功：`{"ok": true}`
- 失败：`{"ok": false, "error": "Failed to save config"}`（状态码 500）

---

### 2. `POST /api/push_structure`

更新图结构数据。

**请求体：** `StructureModel`（包含 `items` 字段）

**逻辑：**
1. 将 `data.items` 写入 `server.structure_store`
2. `server.store_revs["structure"]` 自增 1

**返回：** `{"ok": true}`

---

### 3. `POST /api/push_status`

更新各节点运行状态。

**请求体：** `StatusModel`（包含 `timestamp` 和 `status` 字段）

**逻辑：**
1. 更新 `server.status_timestamp`
2. 更新 `server.status_store`
3. `server.store_revs["status"]` 自增 1

**返回：** `{"ok": true}`

---

### 4. `POST /api/push_errors_meta`

通过 JSONL 文件路径和版本号加载错误日志，支持缓存命中。

**请求体：** `ErrorsMetaModel`

```json
{
  "rev": 5,
  "jsonl_path": "/var/log/celestialflow/errors.jsonl"
}
```

**逻辑：**

```
┌─────────────────────────────────────────┐
│  请求到达                                │
│     ↓                                    │
│  命中缓存？(path 且 rev 均未变)           │
│     ├─ 是 → 返回 {"cached": true}       │
│     └─ 否 →                             │
│          try:                            │
│            调用 load_jsonl_logs()       │
│            （在独立线程中读取 JSONL）    │
│            → 更新 error_store           │
│            → 更新缓存 (rev+path)        │
│            → store_revs["errors"] += 1  │
│            返回 {"cached": false}       │
│          except:                         │
│            返回 fallback=need_content   │
└─────────────────────────────────────────┘
```

**返回：**
- 缓存命中：`{"ok": true, "cached": true}`
- 加载成功：`{"ok": true, "cached": false}`
- 加载失败：`{"ok": false, "fallback": "need_content", "reason": "...", "msg": "..."}`

> **注意：** 加载失败时调用方应回退到 `push_errors_content` 直接发送错误内容。

---

### 5. `POST /api/push_errors_content`

直接接收错误日志列表并存储，支持缓存命中。

**请求体：** `ErrorsContentModel`

```json
{
  "rev": 5,
  "jsonl_path": "/var/log/celestialflow/errors.jsonl",
  "errors": [{"ts": "2026-05-28T10:00:00", "error_id": "...", ...}, ...]
}
```

**逻辑：**
- 命中缓存时跳过，直接返回 `{"cached": true}`
- 否则写入 `server.error_store` 并更新缓存和版本号

**返回：**
- 缓存命中：`{"ok": true, "cached": true}`
- 写入成功：`{"ok": true, "cached": false}`

---

### 6. `POST /api/push_analysis`

更新图拓扑分析信息。

**请求体：** `AnalysisModel`（包含 `analysis` 字段）

**逻辑：**
1. 更新 `server.analysis_store`
2. `server.store_revs["analysis"]` 自增 1

**返回：** `{"ok": true}`

---

### 7. `POST /api/push_summary`

更新全局任务汇总数据。

**请求体：** `SummaryModel`（包含 `summary` 字段）

**逻辑：**
1. 更新 `server.summary_store`
2. `server.store_revs["summary"]` 自增 1

**返回：** `{"ok": true}`

---

### 8. `POST /api/push_injection_tasks`

将前端提交的注入任务追加到待执行队列。

**请求体：** `TaskInjectionModel`

**逻辑：**
1. 持有 `task_injection_lock` 锁
2. 将 `data.model_dump(mode="json")` 追加到 `server.injection_tasks`
3. 释放锁

**返回：**
- 成功：`{"ok": true}`
- 失败：`{"ok": false, "msg": "任务注入失败: ..."}`（状态码 500）

---

## 使用示例

### Reporter 端推送状态与错误

```python
import requests

BASE = "http://localhost:8000"

# 推送节点状态
requests.post(f"{BASE}/api/push_status", json={
    "timestamp": 1716883200.5,
    "status": {"node_a": "running", "node_b": "success"}
})

# 推送错误日志（元信息模式：让服务端自行读取 JSONL）
resp = requests.post(f"{BASE}/api/push_errors_meta", json={
    "rev": 5,
    "jsonl_path": "/var/log/celestialflow/errors.jsonl"
})

# 若服务端读取失败，回退到直接发送内容
data = resp.json()
if not data["ok"] and data.get("fallback") == "need_content":
    requests.post(f"{BASE}/api/push_errors_content", json={
        "rev": 5,
        "jsonl_path": "/var/log/celestialflow/errors.jsonl",
        "errors": [
            {"ts": "2026-05-28T10:00:00", "error_id": "e1", ...}
        ]
    })

# 推送结构数据
requests.post(f"{BASE}/api/push_structure", json={
    "items": [{"id": "n1", "type": "task", "label": "MyTask"}]
})
```

### Web 前端保存配置

```javascript
const resp = await fetch("/api/push_config", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ refreshInterval: "10", dashboard: {...} })
});
const result = await resp.json();
console.log(result.ok ? "保存成功" : "保存失败");
```
