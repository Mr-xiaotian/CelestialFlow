# util_models

> 📅 最后更新日期: 2026/06/05

## 作用

`celestialflow.web.util_models` 模块定义了 Web 模块使用的全部 Pydantic 数据模型，用于数据校验、序列化和 API 请求/响应类型约束。

## 模型列表

### StructureModel

任务结构数据模型，表示任务图的结构信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| `structure` | `dict[str, Any]` | 结构快照字典，通常包含 `nodes`、`edges`、`source_nodes` |

### StatusModel

节点状态数据模型，表示各节点的运行状态。

| 字段 | 类型 | 说明 |
|------|------|------|
| `timestamp` | `float` | 状态数据的时间戳（Unix） |
| `status` | `dict[str, dict[str, Any]]` | 节点名到状态字典的映射 |

### ErrorsMetaModel

错误元数据模型，表示错误日志文件的元信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| `jsonl_path` | `str` | 错误日志 JSONL 文件路径 |
| `rev` | `int` | 错误日志当前修订/偏移量 |

### ErrorsContentModel

错误内容数据模型，包含完整的错误记录列表。

| 字段 | 类型 | 说明 |
|------|------|------|
| `errors` | `list[dict[str, Any]]` | 错误记录列表，每项为错误字典 |
| `jsonl_path` | `str` | 错误日志 JSONL 文件路径 |
| `rev` | `int` | 错误日志当前修订/偏移量 |

### AnalysisModel

任务分析数据模型。

| 字段 | 类型 | 说明 |
|------|------|------|
| `analysis` | `dict[str, Any]` | 分析结果字典 |

### TaskInjectionModel

任务注入请求模型，用于向运行中的任务图动态插入新任务。

| 字段 | 类型 | 说明 |
|------|------|------|
| `node` | `str` | 注入目标节点名称 |
| `task_datas` | `list[Any]` | 待注入的任务数据列表；后端要求必须为数组 |
| `timestamp` | `datetime` | 注入请求时间 |

### DashboardConfigModel

仪表盘布局配置模型，定义前端面板卡片布局。

| 字段 | 类型 | 说明 |
|------|------|------|
| `left` | `list[str]` | 左侧面板要显示的卡片类型列表 |
| `middle` | `list[str]` | 中间面板要显示的卡片类型列表 |
| `right` | `list[str]` | 右侧面板要显示的卡片类型列表 |

### WebConfigModel

Web UI 全局配置模型。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `theme` | `str` | — | UI 主题 |
| `autoRefreshEnabled` | `bool` | `True` | 是否启用自动刷新 |
| `refreshInterval` | `int` | — | 页面数据刷新间隔（ms） |
| `historyLimit` | `int` | — | 历史记录数量上限 |
| `language` | `str` | `"zh-CN"` | 界面语言 |
| `errorPageSize` | `int` | `10` | 错误页每页条数 |
| `errorSortOrder` | `str` | `"newest"` | 错误页排序方式 |
| `showStructureEdgeDelta` | `bool` | `True` | 是否显示结构图边 Delta |
| `dashboard` | `DashboardConfigModel` | — | 仪表盘布局配置（嵌套模型） |

## 使用示例

### 数据校验与序列化

```python
from celestialflow.web.util_models import WebConfigModel, DashboardConfigModel, TaskInjectionModel

# --- WebConfigModel 使用 ---
config = WebConfigModel(
    theme="dark",
    autoRefreshEnabled=True,
    refreshInterval=5,
    historyLimit=20,
    language="zh-CN",
    errorPageSize=10,
    errorSortOrder="newest",
    showStructureEdgeDelta=True,
    dashboard=DashboardConfigModel(
        left=["mermaid"],
        middle=["status"],
        right=["progress"],
    ),
)
print(f"主题: {config.theme}")
print(f"仪表盘布局: {config.dashboard.model_dump()}")

# 序列化为字典
config_dict = config.model_dump()

# 从字典创建
restored = WebConfigModel(**config_dict)

# --- TaskInjectionModel 使用 ---
from datetime import datetime

injection = TaskInjectionModel(
    node="StageA",
    task_datas=[{"id": 1, "value": 42}, {"id": 2, "value": 99}],
    timestamp=datetime.now(),
)
print(f"注入目标: {injection.node}, 任务数: {len(injection.task_datas)}")
```

> 注意：`TaskInjectionModel.task_datas` 当前是严格的 `list[Any]`。如果前端上传单个对象、字符串或数字，请先包装为数组，否则接口会返回 422。

### 错误数据处理

```python
from celestialflow.web.util_models import ErrorsContentModel, ErrorsMetaModel

# 错误元数据
meta = ErrorsMetaModel(jsonl_path="./fallback/2026-05-28/errors.jsonl", rev=150)
print(f"错误日志路径: {meta.jsonl_path}, 当前偏移: {meta.rev}")

# 错误内容
errors = ErrorsContentModel(
    errors=[
        {"error_type": "ValueError", "error_message": "Invalid input"},
        {"error_type": "TimeoutError", "error_message": "Connection lost"},
    ],
    jsonl_path="./fallback/2026-05-28/errors.jsonl",
    rev=152,
)
print(f"错误条数: {len(errors.errors)}")
```
