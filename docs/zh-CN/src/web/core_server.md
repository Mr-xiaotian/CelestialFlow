# TaskWebServer（core_server）

> 📅 最后更新日期: 2026/06/28

TaskWeb 模块提供了一个基于 FastAPI 的轻量级 Web 服务器，用于实时监控和管理任务图的运行。它充当了 `TaskReporter` (后端) 与 Web UI (前端) 之间的中转站。

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

### CLI 入口

`core_server.py` 还提供了命令行入口函数：

- `parse_args()` — 解析 `--host`、`--port`、`--log-level` 参数；`--log-level` 限制为 `critical` / `error` / `warning` / `info` / `debug` / `trace`。
- `main_entry()` — 根据解析后的参数构造 `TaskWebServer` 并调用 `start_server()`。

命令行工具 `celestialflow-web` 即由 `main_entry` 注册而来。

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

## API 接口 (RESTful)

TaskWeb 提供了一系列 RESTful API 供 `TaskReporter` 调用和前端使用。所有接口均以 `/api/` 为前缀，拉取接口使用 `pull_` 命名，推送接口使用 `push_` 命名。

### 拉取接口 (GET /api/pull_*)

用于 Web UI 获取最新数据。大部分拉取接口（`pull_status`、`pull_structure`、`pull_errors`、`pull_analysis`）支持 `known_rev` 机制：若服务端数据版本未变，则返回 `data: null` 以节省带宽。`pull_config`、`pull_injection`、`pull_server_state` 不使用 `known_rev` 机制，每次均返回完整数据。

| 端点 | 返回结构 (data 字段) | 说明 |
|------|--------------------|------|
| `pull_config` | `dict` | 获取主题、语言、刷新频率等全局配置 |
| `pull_structure`| `dict[str, Any]` | 获取任务图的拓扑结构（含 nodes/edges/source_nodes） |
| `pull_status` | `dict[str, dict[str, Any]]` | 获取各节点的实时运行指标及统一时间戳 |
| `pull_errors` | `list[dict]` | 分页拉取错误日志，支持节点/关键词过滤与排序 |
| `pull_analysis` | `dict[str, Any]` | 获取图的拓扑分析结果 |
| `pull_injection` | `{"tasks": dict[str, list[Any]], "terminations": list[str]}` | 供 TaskGraph 拉取待注入的任务队列与终止符（任务按节点名分组，读取后清空） |
| `pull_server_state` | `dict[str, Any]` | 获取 Reporter 同步所需的服务端状态（interval/is_current_graph/has_structure/max_event_id_in_fail） |

### 推送接口 (POST /api/push_*)

主要由 `TaskReporter` 调用，用于上报后端运行状态。

| 端点 | 数据模型 | 说明 |
|------|---------|------|
| `push_config` | `WebConfigModel` | 由前端调用，保存用户设置 |
| `push_status` | `StatusModel` | 上报节点状态快照 + 当前时间戳 |
| `push_structure`| `StructureModel` | 上报图结构 |
| `push_analysis` | `AnalysisModel` | 上报分析数据 |
| `push_errors` | `ErrorsModel` | 直接推送错误内容并写入 SQLite |
| `push_injection_tasks` | `TaskInjectionModel` | 前端提交任务注入请求 |
| `push_injection_terminations` | `TerminationInjectionModel` | 前端提交终止符注入请求 |

## 数据模型 (Pydantic)

> 完整模型定义见 `util_models.md`，此处仅列出核心字段。

### StructureModel

```python
class StructureModel(BaseModel):
    graph_id: str = ""  # 图实例标识，用于 Reporter 端 graph 上下文校验
    structure: dict[str, Any]  # 结构快照，包含 nodes、edges、source_nodes
```

### StatusModel

```python
class StatusModel(BaseModel):
    graph_id: str = ""                    # 图实例标识
    timestamp: float                      # 统一采样时间戳
    status: dict[str, dict[str, Any]]     # 键为节点名，值为节点状态字典
```

### ErrorsModel

```python
class ErrorsModel(BaseModel):
    graph_id: str = ""              # 图实例标识
    errors: list[dict[str, Any]]    # 错误记录列表，直接写入 SQLite 数据库
```

### AnalysisModel

```python
class AnalysisModel(BaseModel):
    graph_id: str = ""        # 图实例标识
    analysis: dict[str, Any]  # 分析结果字典
```

### TaskInjectionModel

```python
class TaskInjectionModel(RootModel[dict[str, list[Any]]]):
    """任务注入请求模型，格式为 {node_name: [tasklist]}。"""
```

> 请求体直接为节点名到任务列表的映射。示例：
> `{"StageA": [task1, task2], "StageB": [task3]}`

### TerminationInjectionModel

```python
class TerminationInjectionModel(RootModel[list[str]]):
    """终止符注入请求模型，格式为 [node_name, ...]。"""
```

> 请求体直接为节点名列表。示例：
> `["StageA", "StageB"]`

### WebConfigModel

配置采用嵌套分组结构。

```python
class GlobalConfigModel(BaseModel):
    theme: str
    autoRefreshEnabled: bool = True
    refreshInterval: int
    language: str = "zh-CN"

class DashboardConfigModel(BaseModel):
    left: list[str]
    middle: list[str]
    right: list[str]

class DashboardPageConfigModel(BaseModel):
    historyLimit: int
    showStructureEdgeDelta: bool = False
    useTotalPendingInStatus: bool = False
    layout: DashboardConfigModel

class ErrorsPageConfigModel(BaseModel):
    pageSize: int = 10
    sortOrder: str = "newest"
    jumpToInjectionAfterRetry: bool = True

class InjectionPageConfigModel(BaseModel):
    showInjectableOnly: bool = True

class WebConfigModel(BaseModel):
    global_: GlobalConfigModel = Field(alias="global")
    dashboard: DashboardPageConfigModel
    errors: ErrorsPageConfigModel
    injection: InjectionPageConfigModel = Field(default_factory=InjectionPageConfigModel)
```

## 配置管理

Web 服务的配置持久化保存在 `web/config.json`。

- `load_config()` — 启动时读取并通过 `WebConfigModel` 验证；若 `config.json` 不存在，直接抛出 `ConfigurationError`，不会使用硬编码默认值启动。
- `save_config(config, config_path)` — 保存配置到 JSON 文件，线程安全（由上层 `push_config` 路由中的 `config_lock` 保证）
- `cal_interval(refresh_interval)` — 将毫秒刷新间隔转换为秒，范围限制在 `[1.0, 60.0]`
- **同步机制**: 前端更新 `refreshInterval` 时，后端的 `report_interval` 会自动同步，从而影响 `TaskReporter` 的推送频率。

## 与 TaskGraph 集成

### 在 TaskGraph 中启用

```python
from celestialflow import TaskGraph, TaskStage


def process(x: int) -> int:
    return x * 2


stage_a = TaskStage("StageA", process, execution_mode="thread")
graph = TaskGraph(name="DemoGraph")
graph.set_stages(stages=[stage_a])
graph.set_reporter(True, host="127.0.0.1", port=5005)
init_tasks = {stage_a.get_name(): [1, 2, 3]}
graph.start_graph(init_tasks)
```

### 数据流

```
TaskGraph                         TaskWeb                    Browser
    |                                |                          |
    |--- push_structure ------------>|--- Dashboard ----------->|
    |--- push_status --------------->|                          |
    |--- push_analysis ------------->|                          |
    |                                |                          |
    |--- push_errors --------------->|---- Errors ------------->|
    |                                |                          |
    |<-- pull_injection -------------|<--- Inject Tasks --------|
    |<-- pull_server_state ----------|<--- Reporter Sync -------|
    |                                |                          |
```

## 错误处理

### SQLite 持久化

错误记录通过 `append_records` 直接写入 SQLite 数据库，支持高效的查询与分页。

### 任务注入并发安全

`injection_tasks` 字典与 `injection_terminations` 集合由 `task_injection_lock` 保护，`push_injection_tasks` / `push_injection_terminations` 写入和 `pull_injection` 读取（含清除）均在锁内操作，避免竞态。任务注入采用**覆盖**语义：相同节点名的新任务会覆盖旧任务列表；终止符注入采用**集合**语义：重复节点名会被去重。

## 注意事项

1. **端口冲突**: 确保指定端口未被占用。
2. **防火墙**: 如需远程访问，请配置防火墙规则。
3. **HTTPS**: 生产环境建议使用反向代理（如 Nginx）添加 HTTPS。
4. **认证**: 当前版本无内置认证，生产环境建议添加认证层。