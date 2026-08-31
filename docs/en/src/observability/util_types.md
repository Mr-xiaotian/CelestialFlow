# ReporterTaskGraph

> 📅 Last Updated: 2026/08/31

`observability/util_types.py` defines the task graph protocol interface `ReporterTaskGraph` and the task stage protocol interface `ReporterTaskStage` on which `TaskReporter` depends. They are `Protocol` classes, allowing `TaskReporter` to declare its dependency without importing concrete `TaskGraph` / `TaskStage` types.

## Core Types

### ReporterTaskGraph

The minimal task graph interface protocol that `TaskReporter` depends on.

```python
class ReporterTaskGraph(Protocol):
    """Minimum task graph interface required by TaskReporter."""

    @property
    def stage_dict(self) -> Mapping[str, ReporterTaskStage]:
        """Return a read-only mapping of nodes indexed by name."""
        ...

    def get_graph_id(self) -> str: ...

    def get_stages_summary(self) -> dict[str, dict[str, Any]]: ...

    def get_edges(self) -> dict[str, list[str]]: ...

    def get_source_names(self) -> list[str]: ...

    def get_lifecycle_path(self) -> Path: ...

    def get_graph_analysis(self) -> dict[str, Any]: ...

    def collect_runtime_snapshot(self) -> tuple[dict[str, Any], float]: ...
```

| Method | Return | Description |
|------|--------|------|
| `stage_dict` | `Mapping[str, ReporterTaskStage]` | Returns a read-only mapping of nodes indexed by name (property) |
| `get_graph_id()` | `str` | Get the unique identifier of the current task graph |
| `get_stages_summary()` | `dict[str, dict[str, Any]]` | Returns the summary of all stages (`name`, `func_name`, `execution_mode`, `max_workers`, etc.) |
| `get_edges()` | `dict[str, list[str]]` | Returns the edge set in the graph structure (`{from_name: [to_name, ...]}`) |
| `get_source_names()` | `list[str]` | Returns the names of all source stages with no upstream input |
| `get_lifecycle_path()` | `Path` | Get the path to the lifecycle persistence file |
| `get_graph_analysis()` | `dict[str, Any]` | Get graph analysis data (topology info, etc.) |
| `collect_runtime_snapshot()` | `tuple[dict[str, Any], float]` | Collect the latest runtime snapshot (per-stage aggregated status dict + collection timestamp) |

### ReporterTaskStage

The minimal task stage interface protocol that `TaskReporter` depends on (only used when the graph exposes stages via `stage_dict`).

```python
class ReporterTaskStage(Protocol):
    """Minimum task stage interface required by TaskReporter."""

    def put_task(self, task: Any) -> None: ...

    def put_signal(self) -> None: ...
```

| Method | Return | Description |
|------|--------|------|
| `put_task(task)` | `None` | Inject a single task into the stage's input queue (for dynamic task injection) |
| `put_signal()` | `None` | Put a termination signal into the stage's input queue |

## Usage Examples

### Type Annotation in TaskReporter

```python
from celestialflow.observability.util_types import (
    ReporterTaskGraph,
    ReporterTaskStage,
)


# TaskReporter uses Protocol to define dependencies, avoiding circular imports
class TaskReporter:
    def __init__(
        self,
        host: str,
        port: int,
        task_graph: ReporterTaskGraph,  # Accepts any instance satisfying the protocol
    ) -> None: ...


# Minimal implementation satisfying the ReporterTaskStage protocol
class MinimalStage:
    def put_task(self, task): ...

    def put_signal(self): ...
```

## Notes

- `ReporterTaskGraph` and `ReporterTaskStage` are both `typing.Protocol`, using structural subtyping — any class implementing the corresponding methods is recognized by the type checker as satisfying the protocol.
- Using the Protocol pattern avoids circular dependencies between `TaskReporter` and `TaskGraph` / `TaskStage`.
- This file is imported and used by `core_report.py`.
