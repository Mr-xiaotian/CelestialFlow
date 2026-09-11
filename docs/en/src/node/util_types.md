# node/util_types.py

> 📅 Last Updated: 2026/09/09

`util_types.py` provides type aliases specific to the `node` module. It currently defines a single `AnyTaskNode` type alias, which is used by upper-layer structures such as `TaskGraph` to reference node objects in an "any node" form.

> The core types actually used at runtime — `TaskEnvelope` / `TaskInQueue` / `TaskOutQueue` / `TaskMetrics` / `TerminationSignal` / `CTreeEvent` / `ValueWrapper` — are not defined in this file; they are provided by `celestialflow.runtime` and `celestialflow.runtime.util_types` respectively. See `docs/en/src/runtime/__init__.md` for details.

## Public Types

### `AnyTaskNode`

```python
from typing import Any
from .core_node import BaseTaskNode

type AnyTaskNode = BaseTaskNode[Any, Any]
```

Meaning:

- A `BaseTaskNode` degenerated to "any input / any output";
- Used only at the static-type level, with no effect on actual runtime behavior;
- Mainly used in `TaskGraph`'s maintained `node_dict`, the public methods `connect` / `set_nodes`, and other locations that "do not care about specific types".

## Typical Usage

```python
from celestialflow.node.util_types import AnyTaskNode


def collect_names(nodes: list[AnyTaskNode]) -> list[str]:
    return [n.get_name() for n in nodes]
```

> `AnyTaskNode` performs only type erasure and introduces no extra runtime overhead; callers can still branch on specifics via `isinstance(n, TaskExecutor | TaskSplitter | TaskRouter)`.

## Notes

1. **Type alias, not part of the import list**: this file has no `__all__`, so you do not need to explicitly `import` from `celestialflow.node.util_types`; it can be accessed indirectly through `celestialflow.node`.
2. **Limited scope**: `AnyTaskNode` should not be used in "concrete node" positions; for example, the input parameter of `TaskExecutor[T, R]` should still use the generic version to avoid breaking static inference.
3. **Type cooperation with the `runtime` module**: `BaseTaskNode` internally uses the `runtime` module's `TaskEnvelope` / `TaskInQueue` / `TaskOutQueue` / `TaskMetrics` / `ValueWrapper` / `CTreeEvent` / `TerminationSignal` directly; see the corresponding documentation for details on these types.
