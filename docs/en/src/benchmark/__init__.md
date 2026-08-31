# Benchmark Module

> 📅 Last Updated: 2026/08/26

Provides executor/task graph cloning and benchmarking capabilities. This module sits at the top of the dependency chain — it may depend on other modules, but should not be depended on by them.

## Submodules

| File | Description |
|------|-------------|
| `util_benchmark.py` | Performance benchmarking for executors and task graphs |
| `util_clone.py` | Cloning utilities for executors, nodes, and task graphs |

## Exported Symbols

`benchmark/__init__.py` contains only the module docstring: it neither defines `__all__` nor includes any import, so the subpackage itself exports no symbols (`from celestialflow.benchmark import ...` will raise `ImportError`). The relevant functions are exposed in two ways:

- `benchmark_executor` and `benchmark_graph` are collectively exported by the top-level package entry `celestialflow/__init__.py` and can be imported directly via `from celestialflow import ...`.
- All 5 functions can also be imported on demand via their submodule path.

| Symbol | Definition Location | Recommended Import | Description |
|------|---------|-------------|------|
| `benchmark_executor` | `util_benchmark.py` | `from celestialflow import benchmark_executor` | Multi-mode benchmarking for sync/async `TaskExecutor` |
| `benchmark_graph` | `util_benchmark.py` | `from celestialflow import benchmark_graph` | Multi-mode benchmarking for the entire `TaskGraph` |
| `clone_executor` | `util_clone.py` | `from celestialflow.benchmark.util_clone import clone_executor` | Clone a `TaskExecutor` instance |
| `clone_stage` | `util_clone.py` | `from celestialflow.benchmark.util_clone import clone_stage` | Clone a `TaskStage` node |
| `clone_graph` | `util_clone.py` | `from celestialflow.benchmark.util_clone import clone_graph` | Clone a complete `TaskGraph` (with connection relationships) |

> Note: `clone_executor` / `clone_stage` / `clone_graph` are not in the top-level package entry's `__all__` and are only used internally by `util_benchmark` or imported on demand.

## Usage Example

```python
from celestialflow import TaskGraph, TaskStage
from celestialflow.benchmark.util_clone import clone_graph


def double(x: int) -> int:
    return x * 2


# Clone the task graph for state-isolated testing
graph = TaskGraph(name="Demo")
stage_a = TaskStage("A", double)
stage_b = TaskStage("B", double)
graph.set_stages([stage_a, stage_b])
graph.connect([stage_a], [stage_b])

cloned = clone_graph(graph)
print(f"Original graph node count: {len(graph.stage_dict)}")
print(f"Cloned graph node count: {len(cloned.stage_dict)}")
```

## Module Dependency Relationships

```mermaid
graph TD
    subgraph benchmark
        UB["util_benchmark"]
        UC["util_clone"]
    end

    subgraph stage
        S["TaskExecutor / TaskStage"]
    end

    subgraph graph
        G["TaskGraph"]
    end

    subgraph runtime
        R["format_table / clone_event_client"]
    end

    subgraph observability
        O["ReporterProtocol / TaskReporter"]
    end

    UB --> UC
    UB --> S
    UB --> G
    UB --> R
    UC --> S
    UC --> G
    UC --> O
```

## Notes

- **Cloning mechanism**: All cloning operations are implemented by constructing new instances and copying key parameters, so the original and cloned objects are completely independent.
- **State isolation**: Each run in benchmarking uses a cloned object to avoid state contamination that could affect test results.
- **Function references**: Cloning only copies function references, not the functions themselves.
- **Async requirement**: `benchmark_executor` and `benchmark_graph` are both async functions and must be called with `await` or via `asyncio.run`.
