# ReporterTaskGraph

> 📅 最后更新日期: 2026/06/18

`observability/util_types.py` 定义了 `TaskReporter` 依赖的任务图协议接口 `ReporterTaskGraph`。它是一个 `Protocol` 类，使得 `TaskReporter` 无需导入具体的 `TaskGraph` 类型即可声明依赖。

## 核心类型

### ReporterTaskGraph

`TaskReporter` 依赖的最小任务图接口协议。

```python
class ReporterTaskGraph(Protocol):
    """TaskReporter 依赖的最小任务图接口。"""

    def collect_runtime_snapshot(self) -> None: ...

    def get_graph_id(self) -> str: ...

    def put_stage_queue(
        self,
        tasks_dict: Mapping[str, Iterable[Any]],
        put_termination_signal: bool = True,
    ) -> None: ...

    def get_fallback_path(self) -> Path: ...

    def get_status_snapshot(self) -> dict[str, Any]: ...

    def get_structure_graph(self) -> dict[str, Any]: ...

    def get_graph_analysis(self) -> dict[str, Any]: ...
```

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `collect_runtime_snapshot()` | `None` | 收集最新运行时快照 |
| `get_graph_id()` | `str` | 获取当前任务图的唯一标识 |
| `put_stage_queue(tasks_dict, put_termination_signal)` | `None` | 将注入任务放入指定 stage 的队列 |
| `get_fallback_path()` | `Path` | 获取 fallback 持久化文件路径 |
| `get_status_snapshot()` | `dict[str, Any]` | 获取运行状态快照（各 stage 计数等） |
| `get_structure_graph()` | `dict[str, Any]` | 获取图结构信息（节点与边） |
| `get_graph_analysis()` | `dict[str, Any]` | 获取图分析数据（拓扑信息等） |

## 使用示例

### TaskReporter 中的类型标注

```python
from celestialflow.observability.util_types import ReporterTaskGraph

# TaskReporter 使用 Protocol 定义依赖，避免循环引用
class TaskReporter:
    def __init__(
        self,
        host: str,
        port: int,
        task_graph: ReporterTaskGraph,  # 接受任何满足该协议的实例
        log_inlet: LogInlet,
    ) -> None:
        ...
```

## 注意事项

- `ReporterTaskGraph` 是 `typing.Protocol`，属于结构化类型（structural subtyping），任何实现了这些方法的类都会被类型检查器视为满足该协议。
- 使用 Protocol 设计避免了 `TaskReporter` 与 `TaskGraph` 之间的循环依赖。
- 该文件被 `core_report.py` 导入使用。
