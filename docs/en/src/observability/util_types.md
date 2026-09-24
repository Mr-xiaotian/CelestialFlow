# src/celestialflow/observability/util_types.py

> 📅 Last Updated: 2026/09/24

`observability/util_types.py` defines the minimal task graph protocol interface `ReporterTaskGraph` and the minimal node protocol interface `ReporterTaskNode` on which `TaskReporter` depends. They are `Protocol` classes, allowing `TaskReporter` to declare its dependency without importing the concrete `TaskGraph` / `BaseTaskNode` types.

## Core Types

### ReporterTaskGraph

The minimal task graph interface protocol that `TaskReporter` depends on.

```python
class ReporterTaskGraph(Protocol):
    """Minimum task graph interface required by TaskReporter."""

    @property
    def node_dict(self) -> Mapping[str, ReporterTaskNode]:
        """Return a read-only mapping of nodes indexed by name."""
        ...

    def get_graph_id(self) -> str: ...

    def get_nodes(self) -> list[str]: ...

    def get_node_meta(self) -> dict[str, dict[str, Any]]: ...

    def get_edges(self) -> dict[str, list[str]]: ...

    def get_source_nodes(self) -> list[str]: ...

    def get_lifecycle_path(self) -> Path: ...

    def get_graph_analysis(self) -> dict[str, Any]: ...
```

| Method | Return | Description |
|--------|--------|-------------|
| `node_dict` | `Mapping[str, ReporterTaskNode]` | Returns a read-only mapping of nodes indexed by name (property) |
| `get_graph_id()` | `str` | Get the unique identifier of the current task graph |
| `get_nodes()` | `list[str]` | Returns the names of all nodes |
| `get_node_meta()` | `dict[str, dict[str, Any]]` | Returns each node's build-time metadata (`class_name` / `execution_mode` / `max_workers`), reported once along with the graph metadata |
| `get_edges()` | `dict[str, list[str]]` | Returns the edge set in the graph structure (`{from_name: [to_name, ...]}`) |
| `get_source_nodes()` | `list[str]` | Returns the names of all source nodes with no upstream input |
| `get_lifecycle_path()` | `Path` | Get the path to the lifecycle persistence file |
| `get_graph_analysis()` | `dict[str, Any]` | Get graph analysis data (topology info, etc.) |

### ReporterTaskNode

The minimal node interface protocol that `TaskReporter` depends on.

```python
class ReporterTaskNode(Protocol):
    """Minimum node interface required by TaskReporter."""

    def put_task(self, task: Any) -> None: ...

    def put_signal(self) -> None: ...

    def get_meta(self) -> dict[str, Any]: ...

    def get_snapshot(self) -> dict[str, Any]: ...
```

| Method | Return | Description |
|--------|--------|-------------|
| `put_task(task)` | `None` | Inject a single task into the node's input queue (for dynamic task injection) |
| `put_signal()` | `None` | Put a termination signal into the node's input queue |
| `get_meta()` | `dict[str, Any]` | Returns the node's build-time metadata (`class_name` / `execution_mode` / `max_workers`) |
| `get_snapshot()` | `dict[str, Any]` | Returns the node's runtime snapshot (status, counts, elapsed, upstream/downstream counts) |

## Usage Examples

### Type Annotation in TaskReporter

```python
from celestialflow.observability.util_types import (
    ReporterTaskGraph,
    ReporterTaskNode,
)


# TaskReporter uses Protocol to define dependencies, avoiding circular imports
class TaskReporter:
    def __init__(
        self,
        host: str,
        port: int,
        task_graph: ReporterTaskGraph,  # Accepts any instance satisfying the protocol
    ) -> None: ...


# Minimal implementation satisfying the ReporterTaskNode protocol
class MinimalNode:
    def put_task(self, task): ...

    def put_signal(self): ...
```

## Notes

- `ReporterTaskGraph` and `ReporterTaskNode` are both `typing.Protocol`, using structural subtyping — any class implementing the corresponding methods is recognized by the type checker as satisfying the protocol.
- Using the Protocol pattern avoids circular dependencies between `TaskReporter` and `TaskGraph` / `BaseTaskNode`.
- This file is imported and used by `core_report.py`.
