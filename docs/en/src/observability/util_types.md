# ReporterTaskGraph

> 📅 Last Updated: 2026/06/18

`observability/util_types.py` defines the task graph protocol interface `ReporterTaskGraph` that `TaskReporter` depends on. It is a `Protocol` class, allowing `TaskReporter` to declare its dependency without importing the concrete `TaskGraph` type.

## Core Types

### ReporterTaskGraph

The minimal task graph interface protocol that `TaskReporter` depends on.

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

| Method | Return Type | Description |
|------|--------|------|
| `collect_runtime_snapshot()` | `None` | Collects the latest runtime snapshot |
| `get_graph_id()` | `str` | Gets the current task graph's unique identifier |
| `put_stage_queue(tasks_dict, put_termination_signal)` | `None` | Puts injected tasks into the specified stage's queue |
| `get_fallback_path()` | `Path` | Gets the fallback persistence file path |
| `get_status_snapshot()` | `dict[str, Any]` | Gets the runtime status snapshot (per-stage counts, etc.) |
| `get_structure_graph()` | `dict[str, Any]` | Gets graph structure information (nodes and edges) |
| `get_graph_analysis()` | `dict[str, Any]` | Gets graph analysis data (topology info, etc.) |

## Usage Example

### Type Annotation in TaskReporter

```python
from celestialflow.observability.util_types import ReporterTaskGraph

# TaskReporter uses Protocol to define dependencies, avoiding circular imports
class TaskReporter:
    def __init__(
        self,
        host: str,
        port: int,
        task_graph: ReporterTaskGraph,  # Accepts any instance satisfying the protocol
        log_inlet: LogInlet,
    ) -> None:
        ...
```

## Notes

- `ReporterTaskGraph` is a `typing.Protocol`, which uses structural subtyping — any class implementing these methods will be recognized by the type checker as satisfying the protocol.
- Using the Protocol pattern avoids circular dependencies between `TaskReporter` and `TaskGraph`.
- This file is imported and used by `core_report.py`.
