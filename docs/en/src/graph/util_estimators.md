# GraphEstimators

> 📅 Last Updated: 2026/08/31

`graph/util_estimators.py` provides a function for estimating the global number of pending tasks based on a task graph (DAG).

## Main Function

### calc_global_pending

```python
def calc_global_pending(
    graph: OrderGraph,
    processed_map: dict[str, int],
    pending_map: dict[str, int],
) -> dict[str, int]: ...
```

Estimates the global number of pending tasks per node based on the task graph (DAG). The estimate is conservative / congestion-amplified.

#### Core Idea

1. Each node's "seen tasks" is defined as `seen = processed + pending`.
2. A downstream node's current seen tasks are assumed to come equally from all of its upstream nodes (the multi-upstream equal-contribution assumption).
3. Use topological order to recursively estimate each node's "expected total input tasks `total`" on the DAG, and compute the amplification factor `scale` from it.
4. The expected remaining task count is at least the currently observed pending count.

#### Algorithm Characteristics

- **Multi-upstream equal-contribution assumption**: does not distinguish the true output proportions of different upstream nodes.
- **Conservative estimate**: uses `processed` as the amplification baseline, which produces a larger estimate when the system is in an early stage or experiencing heavy backlog.
- **Input requirement**: the task graph must be a directed acyclic graph (DAG); otherwise, a `ValueError` is raised.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `graph` | `OrderGraph` | Task dependency graph; node names must match the keys in the maps |
| `processed_map` | `dict[str, int]` | Number of completed tasks per node |
| `pending_map` | `dict[str, int]` | Number of currently remaining tasks per node |

#### Return Value

`dict[str, int]` — the expected number of pending tasks per node.

## Usage Example

```python
from celestialflow.graph.util_order_graph import OrderGraph
from celestialflow.graph.util_estimators import calc_global_pending

# Build a simple DAG: A -> B -> C
graph = OrderGraph.from_edges({"A": ["B"], "B": ["C"]}, ("A", "B", "C"))

# Input observation data
processed_map = {"A": 100, "B": 50, "C": 10}
pending_map = {"A": 0, "B": 50, "C": 90}

result = calc_global_pending(graph, processed_map, pending_map)
for node, pending in result.items():
    print(f"Node {node}: {pending} tasks expected to be pending")
```

## Purpose

- Called by `TaskGraph.collect_runtime_snapshot()` to provide DAG-aware global remaining task estimates for the monitoring panel.
- Helps identify potential congestion nodes.
