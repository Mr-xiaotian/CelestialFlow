# TaskWeb

TaskWeb 模块提供了一个基于 FastAPI 的轻量级 Web 服务器，用于实时监控和管理任务图的运行。

## 启动方式

### 命令行启动

```bash
# 默认监听 0.0.0.0:5000
celestialflow-web

# 指定端口
celestialflow-web --port 5005

# 指定主机和端口
celestialflow-web --host 127.0.0.1 --port 5005

# 指定日志级别
celestialflow-web --log-level debug
```

### 命令行参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--host` | `0.0.0.0` | 监听地址 |
| `--port` | `5000` | 监听端口 |
| `--log-level` | `info` | 日志级别 (critical/error/warning/info/debug/trace) |

### 代码中启动

```python
from celestialflow import TaskWebServer

server = TaskWebServer(host="127.0.0.1", port=5005, log_level="info")
server.start_server()
```

## 功能界面

访问 `http://localhost:5000` (或指定端口) 可看到 Web UI。

### 主要面板

| 面板 | 功能 |
|------|------|
| **Dashboard** | 任务图的实时状态概览（结构可视化（Mermaid 图）、节点数、成功/失败/积压任务数、折线图） |
| **Errors** | 实时错误日志列表 |
| **Task Injection** | 通过 Web 界面动态注入任务 |

### 主题支持

- 支持日间/夜间主题切换
- 主题设置持久化保存至后端 `config.json`

## API 接口

TaskWeb 提供了一系列 RESTful API 供 `TaskReporter` 调用和前端使用。所有接口均以 `/api/` 为前缀，拉取接口使用 `pull_` 命名，推送接口使用 `push_` 命名。

### 拉取数据 (GET)

| 端点 | 说明 |
|------|------|
| `GET /api/pull_config` | 获取前端配置（主题、刷新间隔、仪表盘布局等） |
| `GET /api/pull_structure` | 获取图结构 |
| `GET /api/pull_status` | 获取节点运行状态 |
| `GET /api/pull_errors` | 获取错误日志 |
| `GET /api/pull_topology` | 获取拓扑数据 |
| `GET /api/pull_summary` | 获取概要统计 |
| `GET /api/pull_history` | 获取各节点任务处理历史（用于折线图） |
| `GET /api/pull_interval` | 获取 Reporter 推送间隔 |
| `GET /api/pull_history_limit` | 获取历史记录最大保留条数 |
| `GET /api/pull_task_injection` | 获取待注入的任务（供 TaskGraph 拉取） |

### 推送数据 (POST)

| 端点 | 说明 |
|------|------|
| `POST /api/push_config` | 保存前端配置 |
| `POST /api/push_structure` | 推送图结构 |
| `POST /api/push_status` | 推送节点状态 |
| `POST /api/push_errors_meta` | 推送错误元数据（支持缓存） |
| `POST /api/push_errors_content` | 推送错误内容（支持缓存） |
| `POST /api/push_topology` | 推送拓扑数据 |
| `POST /api/push_summary` | 推送概要统计 |
| `POST /api/push_history` | 推送各节点历史数据 |
| `POST /api/push_injection_tasks` | 注入任务（供前端推送，TaskGraph 拉取） |

## 数据模型

### StructureModel

```python
class StructureModel(BaseModel):
    items: list[dict[str, Any]]
```

### StatusModel

```python
class StatusModel(BaseModel):
    status: dict[str, dict]
```

### ErrorsMetaModel

```python
class ErrorsMetaModel(BaseModel):
    jsonl_path: str  # JSONL 文件路径
    rev: int         # 版本号（用于缓存判断）
```

### ErrorsContentModel

```python
class ErrorsContentModel(BaseModel):
    errors: list[dict]
    jsonl_path: str
    rev: int
```

### TopologyModel

```python
class TopologyModel(BaseModel):
    topology: dict[str, Any]
```

### SummaryModel

```python
class SummaryModel(BaseModel):
    summary: dict[str, Any]
```

### HistoryModel

```python
class HistoryModel(BaseModel):
    history: dict[str, list[dict]]
    # key: 节点 tag；value: [{timestamp, tasks_processed}, ...]
```

### TaskInjectionModel

```python
class TaskInjectionModel(BaseModel):
    node: str             # 目标节点标签
    task_datas: list[Any] # 任务数据列表
    timestamp: datetime   # 时间戳
```

### WebConfigModel

```python
class WebConfigModel(BaseModel):
    theme: str                        # "light" 或 "dark"
    refreshInterval: int              # 刷新间隔（毫秒）
    historyLimit: int                 # 历史记录最大保留条数
    dashboard: DashboardConfigModel   # 仪表盘布局配置
    cards: dict[str, CardConfigModel] # 各卡片标题配置

class DashboardConfigModel(BaseModel):
    left: list[str]    # 左栏卡片 key 列表
    middle: list[str]  # 中栏卡片 key 列表
    right: list[str]   # 右栏卡片 key 列表

class CardConfigModel(BaseModel):
    title: str         # 卡片标题
```

## 配置管理

Web 服务的配置持久化保存在 `web/config.json`。

- `load_config()` — 启动时读取并通过 `WebConfigModel` 验证
- `save_config(config)` — 保存配置到 JSON 文件，线程安全（使用 `_config_lock`）
- `cal_interval(refresh_interval)` — 将毫秒刷新间隔转换为秒，范围限制在 `[1.0, 60.0]`

前端通过 `push_config` 更新配置时，`report_interval` 也会同步更新。

## 与 TaskGraph 集成

### 在 TaskGraph 中启用

```python
from celestialflow import TaskGraph

graph = TaskGraph([stage_a])
graph.set_reporter(True, host="127.0.0.1", port=5005)
graph.start_graph(init_tasks)
```

### 数据流

```
TaskGraph                    TaskWeb                    Browser
    |                           |                          |
    |--- push_structure ------->|--- Dashboard ----------->|
    |--- push_status ---------->|                          |
    |--- push_topology -------->|                          |
    |--- push_summary --------->|                          |
    |--- push_history --------->|                          |
    |                           |                          |
    |--- push_errors_meta ----->|---- Errors ------------->|
    |--- push_errors_content -->|                          |
    |                           |                          |
    |<-- pull_task_injection ---|<--- Inject Tasks --------|
    |<-- pull_interval ---------|<--- Web Config ----------|
    |                           |                          |
```

## 错误处理

### 缓存机制

`push_errors_meta` 和 `push_errors_content` 支持基于 `(jsonl_path, rev)` 的缓存：

- 如果路径和版本号均未变化，返回 `{"ok": true, "cached": true}`，不重新读取文件
- 否则重新加载数据并更新 `_errors_meta_path` / `_errors_meta_rev`

### 优雅降级

当无法读取 JSONL 文件时，`push_errors_meta` 返回 fallback 指示：

```json
{
    "ok": false,
    "fallback": "need_content",
    "reason": "FileNotFoundError",
    "msg": "File not found"
}
```

客户端收到此响应后，改用 `push_errors_content` 直接传递错误内容。

### 任务注入并发安全

`injection_tasks` 列表由 `_task_injection_lock` 保护，`push_injection_tasks` 写入和 `pull_task_injection` 读取（含清除）均在锁内操作，避免竞态。

## 注意事项

1. **端口冲突**: 确保指定端口未被占用。
2. **防火墙**: 如需远程访问，请配置防火墙规则。
3. **HTTPS**: 生产环境建议使用反向代理（如 Nginx）添加 HTTPS。
4. **认证**: 当前版本无内置认证，生产环境建议添加认证层。
