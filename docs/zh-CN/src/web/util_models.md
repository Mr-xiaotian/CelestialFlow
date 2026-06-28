# util_models

> 📅 最后更新日期: 2026/06/28

## 作用

`celestialflow.web.util_models` 模块定义了 Web 模块使用的全部 Pydantic 数据模型，用于数据校验、序列化和 API 请求/响应类型约束。

## 模型列表

### StructureModel

任务结构数据模型，表示任务图的结构信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| `graph_id` | `str` | 图实例标识，默认 `""`；用于 Reporter 端 graph 上下文校验 |
| `structure` | `dict[str, Any]` | 结构快照字典，通常包含 `nodes`、`edges`、`source_nodes` |

### StatusModel

节点状态数据模型，表示各节点的运行状态。

| 字段 | 类型 | 说明 |
|------|------|------|
| `graph_id` | `str` | 图实例标识，默认 `""` |
| `timestamp` | `float` | 状态数据的时间戳（Unix） |
| `status` | `dict[str, dict[str, Any]]` | 节点名到状态字典的映射 |

### ErrorsModel

错误内容数据模型，包含完整的错误记录列表。

| 字段 | 类型 | 说明 |
|------|------|------|
| `graph_id` | `str` | 图实例标识，默认 `""` |
| `errors` | `list[dict[str, Any]]` | 错误记录列表，每项为错误字典；直接写入 SQLite 数据库 |

### AnalysisModel

任务分析数据模型。

| 字段 | 类型 | 说明 |
|------|------|------|
| `graph_id` | `str` | 图实例标识，默认 `""` |
| `analysis` | `dict[str, Any]` | 分析结果字典 |

### TaskInjectionModel

任务注入请求模型，用于向运行中的任务图动态插入新任务。

> 该模型继承自 `RootModel[dict[str, list[Any]]]`，请求体直接为 `{节点名: [任务列表]}` 格式的字典，不再包含 `node`/`task_datas`/`timestamp` 等独立字段。

| 根值类型 | 说明 |
|----------|------|
| `dict[str, list[Any]]` | 键为节点名称，值为该节点待注入的任务数据列表 |

**请求体示例：**

```json
{
  "StageA": [{"id": 1, "value": 42}, {"id": 2, "value": 99}],
  "StageB": [{"id": 3, "value": 55}]
}
```

### TerminationInjectionModel

终止符注入请求模型，用于向运行中的任务图注入终止目标节点。

> 该模型继承自 `RootModel[list[str]]`，请求体直接为节点名字符串列表，不再包含其他包装字段。

| 根值类型 | 说明 |
|----------|------|
| `list[str]` | 待注入终止符的节点名称列表 |

**请求体示例：**

```json
[
  "StageA",
  "StageB"
]
```

### DashboardConfigModel

仪表盘布局配置模型，定义前端面板卡片布局。

| 字段 | 类型 | 说明 |
|------|------|------|
| `left` | `list[str]` | 左侧面板要显示的卡片类型列表 |
| `middle` | `list[str]` | 中间面板要显示的卡片类型列表 |
| `right` | `list[str]` | 右侧面板要显示的卡片类型列表 |

### GlobalConfigModel

全局共享配置模型（嵌套于 `WebConfigModel.global_` 下）。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `theme` | `str` | — | UI 主题（如 `"light"`、`"dark"`） |
| `autoRefreshEnabled` | `bool` | `True` | 是否启用自动刷新 |
| `refreshInterval` | `int` | — | 页面数据刷新间隔（ms） |
| `language` | `str` | `"zh-CN"` | 界面语言 |

### DashboardPageConfigModel

仪表盘页面配置模型（嵌套于 `WebConfigModel.dashboard` 下）。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `historyLimit` | `int` | — | 历史记录数量上限 |
| `showStructureEdgeDelta` | `bool` | `False` | 是否显示结构图边增量 |
| `useTotalPendingInStatus` | `bool` | `False` | 节点等待参数是否使用全局估计 |
| `layout` | `DashboardConfigModel` | — | 仪表盘卡片三栏布局定义 |

### ErrorsPageConfigModel

错误页配置模型（嵌套于 `WebConfigModel.errors` 下）。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `pageSize` | `int` | `10` | 错误页每页条数 |
| `sortOrder` | `str` | `"newest"` | 默认排序方式（`"newest"` / `"oldest"`） |
| `jumpToInjectionAfterRetry` | `bool` | `True` | 任务重试后是否跳转到注入页 |

### InjectionPageConfigModel

注入页配置模型（嵌套于 `WebConfigModel.injection` 下）。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `showInjectableOnly` | `bool` | `True` | 是否仅显示可注入节点 |

### WebConfigModel

Web UI 全局配置模型（嵌套分组结构）。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `global_` | `GlobalConfigModel` | — | 全局共享配置（JSON 别名为 `"global"`） |
| `dashboard` | `DashboardPageConfigModel` | — | 仪表盘页面配置 |
| `errors` | `ErrorsPageConfigModel` | — | 错误页配置 |
| `injection` | `InjectionPageConfigModel` | `InjectionPageConfigModel()` | 注入页配置 |

配置采用嵌套分组结构：`theme`、`refreshInterval`、`language` 等位于 `GlobalConfigModel`（JSON 键为 `"global"`）；`historyLimit`、`showStructureEdgeDelta` 等位于 `DashboardPageConfigModel`；`pageSize`、`sortOrder` 等位于 `ErrorsPageConfigModel`。

## 使用示例

### 数据校验与序列化

```python
from celestialflow.web.util_models import (
    WebConfigModel, GlobalConfigModel, DashboardPageConfigModel,
    DashboardConfigModel, ErrorsPageConfigModel, InjectionPageConfigModel,
    TaskInjectionModel,
)

# --- WebConfigModel 使用 (嵌套结构) ---
config = WebConfigModel(
    global=GlobalConfigModel(
        theme="dark",
        autoRefreshEnabled=True,
        refreshInterval=5000,
        language="zh-CN",
    ),
    dashboard=DashboardPageConfigModel(
        historyLimit=20,
        showStructureEdgeDelta=False,
        useTotalPendingInStatus=False,
        layout=DashboardConfigModel(
            left=["mermaid"],
            middle=["status"],
            right=["progress"],
        ),
    ),
    errors=ErrorsPageConfigModel(
        pageSize=10,
        sortOrder="newest",
        jumpToInjectionAfterRetry=True,
    ),
    injection=InjectionPageConfigModel(
        showInjectableOnly=True,
    ),
)
print(f"主题: {config.global_.theme}")
print(f"仪表盘布局: {config.dashboard.layout.model_dump()}")

# 序列化为字典（by_alias=True 将 global_ 转为 "global"）
config_dict = config.model_dump(by_alias=True)

# 从字典创建
restored = WebConfigModel.model_validate(config_dict)

# --- TaskInjectionModel 使用 ---
injection = TaskInjectionModel(
    StageA=[{"id": 1, "value": 42}, {"id": 2, "value": 99}],
    StageB=[{"id": 3, "value": 55}],
)
print(f"注入节点数: {len(injection.root)}")
for node_name, tasks in injection.root.items():
    print(f"  {node_name}: {len(tasks)} 个任务")
```

> 注意：`TaskInjectionModel` 是 `RootModel[dict[str, list[Any]]]`，请求体直接为节点名到任务列表的映射字典，不再包装 `node`/`task_datas` 等字段。

### 错误数据处理

```python
from celestialflow.web.util_models import ErrorsModel

# 错误内容
content = ErrorsModel(
    graph_id="graph-001",
    errors=[
        {"error_type": "ValueError", "error_message": "Invalid input"},
        {"error_type": "TimeoutError", "error_message": "Connection lost"},
    ],
)
print(f"错误条数: {len(content.errors)}")
```
