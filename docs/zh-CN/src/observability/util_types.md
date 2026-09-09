# observability/util_types.py

> 📅 最后更新日期: 2026/09/09

`observability/util_types.py` 定义了 `TaskReporter` 依赖的最小任务图协议接口 `ReporterTaskGraph` 与最小执行器协议接口 `ReporterTaskExecutor`。它们是 `Protocol` 类，使得 `TaskReporter` 无需导入具体的 `TaskGraph` / `BaseTaskNode` 类型即可声明依赖。

## 核心类型

### ReporterTaskGraph

`TaskReporter` 依赖的最小任务图接口协议。

```python
class ReporterTaskGraph(Protocol):
    """TaskReporter 依赖的最小任务图接口。"""

    @property
    def node_dict(self) -> Mapping[str, ReporterTaskExecutor]:
        """返回按名称索引的只读节点映射。"""
        ...

    def get_graph_id(self) -> str: ...

    def get_nodes(self) -> list[str]: ...

    def get_edges(self) -> dict[str, list[str]]: ...

    def get_source_nodes(self) -> list[str]: ...

    def get_lifecycle_path(self) -> Path: ...

    def get_graph_analysis(self) -> dict[str, Any]: ...

    def collect_runtime_snapshot(self) -> tuple[dict[str, Any], float]: ...
```

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `node_dict` | `Mapping[str, ReporterTaskExecutor]` | 返回按名称索引的只读节点映射（property） |
| `get_graph_id()` | `str` | 获取当前任务图的唯一标识 |
| `get_nodes()` | `list[str]` | 返回所有节点名称 |
| `get_edges()` | `dict[str, list[str]]` | 返回图结构中的边集合（`{from_name: [to_name, ...]}`） |
| `get_source_nodes()` | `list[str]` | 返回所有无上游输入的源节点名称 |
| `get_lifecycle_path()` | `Path` | 获取生命周期持久化文件路径 |
| `get_graph_analysis()` | `dict[str, Any]` | 获取图分析数据（拓扑信息等） |
| `collect_runtime_snapshot()` | `tuple[dict[str, Any], float]` | 收集最新运行时快照（按节点聚合的状态字典 + 采集时间戳） |

### ReporterTaskExecutor

`TaskReporter` 依赖的最小执行器（节点）接口协议。

```python
class ReporterTaskExecutor(Protocol):
    """TaskReporter 依赖的最小执行器接口。"""

    def put_task(self, task: Any) -> None: ...

    def put_signal(self) -> None: ...
```

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `put_task(task)` | `None` | 将单条任务注入节点输入队列（用于动态任务注入） |
| `put_signal()` | `None` | 向节点输入队列放入终止信号 |

## 使用示例

### TaskReporter 中的类型标注

```python
from celestialflow.observability.util_types import (
    ReporterTaskGraph,
    ReporterTaskExecutor,
)


# TaskReporter 使用 Protocol 定义依赖，避免循环引用
class TaskReporter:
    def __init__(
        self,
        host: str,
        port: int,
        task_graph: ReporterTaskGraph,  # 接受任何满足该协议的实例
    ) -> None: ...


# 满足 ReporterTaskExecutor 协议的最小实现示例
class MinimalExecutor:
    def put_task(self, task): ...

    def put_signal(self): ...
```

## 注意事项

- `ReporterTaskGraph` 与 `ReporterTaskExecutor` 都是 `typing.Protocol`，属于结构化类型（structural subtyping），任何实现了对应方法的类都会被类型检查器视为满足该协议。
- 使用 Protocol 设计避免了 `TaskReporter` 与 `TaskGraph` / `BaseTaskNode` 之间的循环依赖。
- 该文件被 `core_report.py` 导入使用。
