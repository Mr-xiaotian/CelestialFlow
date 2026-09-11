# node Module

> 📅 Last Updated: 2026/09/09

## Purpose

The `celestialflow.node` package exposes the full public API of the node layer. It re-exports `TaskExecutor`, `TaskSplitter`, and `TaskRouter` from the `core_nodes` module, providing three types of pipeline components—execution, splitting, and routing—that can be directly used as graph nodes in the task graph.

> This module's docstring still retains the historical name "CelestialFlow 阶段模块" and may continue to be kept.

## Public Exported Symbols (`__all__`)

```python
from celestialflow.node import (
    TaskExecutor,  # General task executor
    TaskSplitter,  # 1→N task splitter
    TaskRouter,  # Conditional router
)
```

Complete `__all__`:

```python
__all__ = [
    "TaskExecutor",
    "TaskRouter",
    "TaskSplitter",
]
```

> ⚠️ `BaseTaskNode` and `TaskDispatch` are **not** in `__all__`; they are internal abstractions used internally by `TaskExecutor` / `TaskSplitter` / `TaskRouter` during construction. External code should not depend on them directly.

## Three Core Node Classes

| Exported Symbol | Source Module | Parent Class | Purpose |
|---------|-------|------|------|
| `TaskExecutor` | `core_nodes` | `BaseTaskNode[T, R]` | General task executor, mapping a single input to a single result |
| `TaskSplitter` | `core_nodes` | `BaseTaskNode[Iterable[TItem], Iterable[RItem]]` | Splitter, splitting a single task into multiple sub-tasks (1→N) |
| `TaskRouter` | `core_nodes` | `BaseTaskNode[T, tuple[str, T]]` | Router, distributing tasks to different downstream based on user-defined `router` function |

## Usage Examples

### TaskExecutor — Execute a group of tasks independently

```python
from celestialflow.node import TaskExecutor


def double(x: int) -> int:
    return x * 2


executor = TaskExecutor("Doubler", func=double, execution_mode="serial")
executor.run([1, 2, 3, 4, 5])

for task, result in executor.get_success_pairs():
    print(f"{task} -> {result}")
```

### TaskSplitter — Split a collection into multiple sub-tasks

```python
from celestialflow.node import TaskSplitter

# Split a string into individual characters
splitter = TaskSplitter("CharSplitter")

# Pair with downstream TaskGraph:
# graph.connect([splitter], [downstream])
# splitter.run([["abc", "de"]])
```

### TaskRouter — Route to different downstream based on conditions

```python
from celestialflow.node import TaskRouter


def by_length(text: str) -> str:
    return "LongPath" if len(text) > 5 else "ShortPath"


router = TaskRouter("LengthRouter", router=by_length)
# graph.connect([router], [long_node, short_node])
```

## Relationship with Other Modules

- **`core_node`**: Defines the base class `BaseTaskNode` and internal scheduler `TaskDispatch`, which serve as the runtime skeleton for all nodes.
- **`core_nodes`**: Provides the three public node classes.
- **`runtime`**: Nodes depend on `TaskEnvelope` / `TaskInQueue` / `TaskOutQueue` / `TaskMetrics` for queue and metrics communication.
- **`observability`**: Reports execution progress via `BaseObserver`.
- **`persistence`**: Persists task lifecycle and logs via `LifecycleInlet` / `LogInlet`.

## Notes

1. **Base classes are not public API**: `BaseTaskNode` and `TaskDispatch` do not appear in `__all__`. If custom node behavior is needed, please inherit from `TaskExecutor` and override `process_task_success` / `get_binding_counter`.
2. **Entry layer consistency**: The above three symbols can also be `import`ed directly from the top-level `celestialflow` package entry (`docs/en/src/__init__.md`).
3. **Lifecycle**: All nodes' `start()` / `start_async()` are one-time calls; after execution completes, a new instance should be created rather than resetting for reuse.
