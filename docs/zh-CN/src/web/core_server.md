# TaskWeb

> 📅 最后更新日期: 2026/05/23

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

用于 Web UI 获取最新数据。支持 `known_rev` 机制：若服务端数据版本未变，则返回 `data: null` 以节省带宽。

| 端点 | 返回结构 (data 字段) | 说明 |
|------|--------------------|------|
| `pull_config` | `WebConfigModel` | 获取主题、语言、刷新频率等全局配置 |
| `pull_structure`| `list[dict]` | 获取任务图的拓扑结构 |
| `pull_status` | `dict[tag, NodeStatus]` | 获取各节点的实时运行指标及统一时间戳 |
| `pull_errors` | `list[dict]` | 分页拉取错误日志 |
| `pull_analysis` | `dict` | 获取图的拓扑分析结果 (DAG, 层级等) |
| `pull_summary` | `{"total_remain": float}` | 获取图级总剩余时间估算 |
| `pull_task_injection` | `list[dict]` | 供 TaskGraph 拉取待注入的任务队列 |
| `pull_interval` | `{"interval": float}` | 获取 Reporter 推送间隔 |

### 推送接口 (POST /api/push_*)

主要由 `TaskReporter` 调用，用于上报后端运行状态。

| 端点 | 数据模型 | 说明 |
|------|---------|------|
| `push_config` | `WebConfigModel` | 由前端调用，保存用户设置 |
| `push_status` | `StatusModel` | 上报节点状态快照 + 当前时间戳 |
| `push_structure`| `StructureModel` | 上报图结构 |
| `push_analysis` | `AnalysisModel` | 上报分析数据 |
| `push_summary` | `SummaryModel` | 上报图级汇总信息 |
| `push_errors_meta` | `ErrorsMetaModel` | 推送错误元数据（支持缓存） |
| `push_errors_content`| `ErrorsContentModel`| 推送错误内容（支持缓存） |
| `push_injection_tasks` | `TaskInjectionModel` | 前端提交任务注入请求 |

## 数据模型 (Pydantic)

### StructureModel
```python
class StructureModel(BaseModel):
    items: list[dict[str, Any]]
```

### StatusModel
```python
class StatusModel(BaseModel):
    timestamp: float                 # 统一采样时间戳
    status: dict[str, dict[str, Any]] # 键为节点 Tag，值为 NodeStatus
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
    errors: list[dict[str, Any]]
    jsonl_path: str
    rev: int
```

### AnalysisModel
```python
class AnalysisModel(BaseModel):
    analysis: dict[str, Any]
```

### SummaryModel
```python
class SummaryModel(BaseModel):
    summary: dict[str, Any]
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
    theme: str                        # "light" | "dark"
    refreshInterval: int              # 轮询间隔 (ms)
    historyLimit: int                 # 前端历史保留长度
    language: str = "zh-CN"           # 界面语言
    errorPageSize: int = 10           # 错误日志分页大小
    showStructureEdgeDelta: bool = True # 结构图增量显示开关
    dashboard: DashboardConfigModel   # 仪表盘三栏布局定义

class DashboardConfigModel(BaseModel):
    left: list[str]    # 左栏卡片 key 列表
    middle: list[str]  # 中栏卡片 key 列表
    right: list[str]   # 右栏卡片 key 列表
```

## 配置管理

Web 服务的配置持久化保存在 `web/config.json`。

- `load_config()` — 启动时读取并通过 `WebConfigModel` 验证
- `save_config(config)` — 保存配置到 JSON 文件，线程安全（使用 `_config_lock`）
- `cal_interval(refresh_interval)` — 将毫秒刷新间隔转换为秒，范围限制在 `[1.0, 60.0]`
- **降级启动**: 若 `config.json` 加载失败，Web 服务会使用硬编码的默认值启动，确保监控界面始终可用。
- **同步机制**: 前端更新 `refreshInterval` 时，后端的 `report_interval` 会自动同步，从而影响 `TaskReporter` 的推送频率。

## 与 TaskGraph 集成

### 在 TaskGraph 中启用

```python
from celestialflow import TaskGraph

graph = TaskGraph()
graph.set_stages(stages=[stage_a])
graph.set_reporter(True, host="127.0.0.1", port=5005)
graph.start_graph(init_tasks)
```

### 数据流

```
TaskGraph                    TaskWeb                    Browser
    |                           |                          |
    |--- push_structure ------->|--- Dashboard ----------->|
    |--- push_status ---------->|                          |
    |--- push_analysis -------->|                          |
    |--- push_summary --------->|                          |
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