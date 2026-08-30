# ReporterTaskGraph

> 📅 最后更新日期: 2026/08/26

`observability/util_types.py` 定义了 `TaskReporter` 依赖的任务图协议接口 `ReporterTaskGraph` 与任务阶段协议接口 `ReporterTaskStage`。它们是 `Protocol` 类，使得 `TaskReporter` 无需导入具体的 `TaskGraph` / `TaskStage` 类型即可声明依赖。

## 核心类型

### ReporterTaskGraph

`TaskReporter` 依赖的最小任务图接口协议。

```python
class ReporterTaskGraph(Protocol):
    """TaskReporter 依赖的最小任务图接口。"""

    @property
    def stage_dict(self) -> Mapping[str, ReporterTaskStage]:
        """返回按名称索引的只读节点映射。"""
        ...

    def collect_runtime_snapshot(self) -> None: ...

    def get_graph_id(self) -> str: ...

    def get_lifecycle_path(self) -> Path: ...

    def get_status_snapshot(self) -> dict[str, Any]: ...

    def get_structure_graph(self) -> dict[str, Any]: ...

    def get_graph_analysis(self) -> dict[str, Any]: ...
```

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `stage_dict` | `Mapping[str, ReporterTaskStage]` | 返回按名称索引的只读节点映射（property） |
| `collect_runtime_snapshot()` | `None` | 收集最新运行时快照 |
| `get_graph_id()` | `str` | 获取当前任务图的唯一标识 |
| `get_lifecycle_path()` | `Path` | 获取生命周期持久化文件路径 |
| `get_status_snapshot()` | `dict[str, Any]` | 获取运行状态快照（各 stage 计数等） |
| `get_structure_graph()` | `dict[str, Any]` | 获取图结构信息（节点与边） |
| `get_graph_analysis()` | `dict[str, Any]` | 获取图分析数据（拓扑信息等） |

### ReporterTaskStage

`TaskReporter` 依赖的最小任务阶段接口协议（仅当图通过 `stage_dict` 暴露阶段时使用）。

```python
class ReporterTaskStage(Protocol):
    """TaskReporter 依赖的最小任务阶段接口。"""

    def put_task(self, task: Any) -> None: ...

    def put_signal(self) -> None: ...
```

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `put_task(task)` | `None` | 将单条任务注入阶段输入队列（用于动态任务注入） |
| `put_signal()` | `None` | 向阶段输入队列放入终止信号 |

## 使用示例

### TaskReporter 中的类型标注

```python
from celestialflow.observability.util_types import (
    ReporterTaskGraph,
    ReporterTaskStage,
)


# TaskReporter 使用 Protocol 定义依赖，避免循环引用
class TaskReporter:
    def __init__(
        self,
        host: str,
        port: int,
        task_graph: ReporterTaskGraph,  # 接受任何满足该协议的实例
    ) -> None: ...


# 满足 ReporterTaskStage 协议的最小实现示例
class MinimalStage:
    def put_task(self, task): ...

    def put_signal(self): ...
```

## 注意事项

- `ReporterTaskGraph` 与 `ReporterTaskStage` 都是 `typing.Protocol`，属于结构化类型（structural subtyping），任何实现了对应方法的类都会被类型检查器视为满足该协议。
- 使用 Protocol 设计避免了 `TaskReporter` 与 `TaskGraph` / `TaskStage` 之间的循环依赖。
- 该文件被 `core_report.py` 导入使用。
