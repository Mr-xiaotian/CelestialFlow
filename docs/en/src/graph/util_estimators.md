# GraphEstimators

> 📅 Last Updated: 2026/09/16

`graph/util_estimators.py` provides a function for estimating the global number of pending tasks based on a task graph (DAG).

## Main Function

### calc_global_pending

```python
def calc_global_pending(
    graph: OrderGraph,
    processed_map: dict[str, int],
    pending_map: dict[str, int],
    downstream_map: dict[str, dict[str, int]],
) -> dict[str, int]: ...
```

Estimates the global number of pending tasks per node based on the task graph (DAG). The estimate is conservative / congestion-amplified.

#### Core Idea

1. Each node's "seen tasks" is defined as `seen = processed + pending`.
2. Maintain an independent amplification factor `scale[u][w]` for each upstream-downstream pair, representing the expected output that upstream `u` sends to downstream `w`:

   ```
   scale[u][w] = total_u * output_u->w / max(1, proc_u)
   ```

   The output ratio `output_u->w / proc_u` is derived from a single snapshot of `u` itself (consistent with `proc_u`), which avoids the influence of cross-node snapshot timing skew.
3. Recursively estimate each node's "expected total input tasks `total`":

   ```
   total_v = external_v + sum(scale[u][v] for u in preds(v))
   ```

   where `external_v = max(0, seen_v - sum(output_u->v))` is the number of externally injected tasks, which is not amplified by upstream factors.
4. The expected remaining task count is `max(pending_v, total_v - processed_v)`, i.e. at least the currently observed pending count.

#### Algorithm Characteristics

- **Per-downstream independent amplification**: each downstream is amplified independently according to its true output ratio from the upstream; fan-out splitting and splitter multiplication are recorded explicitly.
- **Single-side output ratio**: the output ratio is computed from the sender's own snapshot, so the factor is naturally 0 when `proc = 0`, preventing pathological amplification.
- **Conservative estimate**: upstream backlog is explicitly amplified to downstream, suitable for monitoring, alerting, or bottleneck identification.
- **Input requirement**: the task graph must be a directed acyclic graph (DAG); otherwise, a `ValueError` is raised.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `graph` | `OrderGraph` | Task dependency graph; node names must match the keys in the maps |
| `processed_map` | `dict[str, int]` | Number of completed tasks per node |
| `pending_map` | `dict[str, int]` | Number of currently remaining tasks per node |
| `downstream_map` | `dict[str, dict[str, int]]` | Number of tasks actually sent to each downstream per node, shaped `{node: {downstream_name: count}}`; missing nodes or downstreams are treated as 0 |

#### Return Value

`dict[str, int]` — the expected number of pending tasks per node.

## Usage Example

```python
from celestialflow.graph.util_order_graph import OrderGraph
from celestialflow.graph.util_estimators import calc_global_pending

# Build a simple DAG: A -> B -> C
graph = OrderGraph()
for u, v in [("A", "B"), ("B", "C")]:
    graph.add_edge(u, v)

# Input observation data
processed_map = {"A": 100, "B": 50, "C": 10}
pending_map = {"A": 0, "B": 50, "C": 90}

# Number of tasks actually sent to each downstream
downstream_map = {"A": {"B": 100}, "B": {"C": 50}}

result = calc_global_pending(graph, processed_map, pending_map, downstream_map)
for node, pending in result.items():
    print(f"Node {node}: {pending} tasks expected to be pending")
```

## Purpose

- Called by `TaskGraph.collect_runtime_snapshot()` to provide DAG-aware global remaining task estimates for the monitoring panel.
- Helps identify potential congestion nodes.