# src/celestialflow/observer/core_metrics.py

> 📅 Last Updated: 2026/10/09

`core_metrics.py` defines the **graph-level metrics observer** `MetricsObserver`. It simultaneously plays the two roles of "write model" and "read-only view": as an observer it writes each node's counts, status, and run start time from events, and it exposes an immutable `NodeMetrics` snapshot through a read-only view.

## MetricsObserver

```python
class MetricsObserver(Observer):
    def __init__(self) -> None: ...

    def on_node_start(self, event: NodeStartEvent) -> None: ...
    def on_node_end(self, event: NodeEndEvent) -> None: ...
    def on_task_input(self, event: TaskInputEvent) -> None: ...
    def on_task_success(self, event: TaskSuccessEvent) -> None: ...
    def on_task_fail(self, event: TaskFailEvent) -> None: ...
    def on_task_skip(self, event: TaskSkipEvent) -> None: ...

    def get_node_metrics(self, node: str) -> NodeMetrics | None: ...
    def get_graph_metrics(self) -> dict[str, NodeMetrics]: ...
```

A single instance serves one run scope: the entire task graph, or a single independently running node.

## Event Write Logic

`MetricsObserver` only cares about the following events to maintain metrics:

| Event | Write Behavior |
|------|---------|
| `on_node_start` | Set the node status to `RUNNING` and record the wall-clock start time |
| `on_node_end` | Set the node status to `STOPPED` |
| `on_task_input` | Distinguish the source: when `from_node is None`, accumulate the external-injection count; otherwise accumulate both the receiver's upstream count and the source's downstream count |
| `on_task_success` | Accumulate the node's success count |
| `on_task_fail` | Accumulate the node's fail count |
| `on_task_skip` | Accumulate the node's skip count |

A storage cell is **created on demand** (`_ensure`, idempotent) with the first event, and edge counts are also written incrementally by the actual task flow, so it does not depend on graph-construction structure events; an upstream delivery writes both the receiver's upstream count and the source's downstream count, so no counter objects need to be shared between nodes, and no per-node-type specialized statistics logic is needed.

## Read-Only View

Reads are exposed through the `runtime.util_types.MetricsView` protocol, returning an immutable `NodeMetrics` snapshot:

- `get_node_metrics(node)`: get the metrics snapshot of a single node; returns `None` when the node is not registered.
- `get_graph_metrics()`: return the metrics snapshots of all nodes in the graph (`{node: NodeMetrics}`).

`NodeMetrics` is a read-only DTO (in `runtime.util_types`), with the following fields:

| Field | Description |
|------|------|
| `node` | Node name |
| `status` | Node lifecycle status (`NodeStatus`) |
| `start_time` | Wall-clock time (seconds) when the node entered the running state; `0.0` when not started |
| `external_input` | Externally injected task count |
| `upstream_input` | Upstream-provided task count |
| `input_total` | Total input (external injection + upstream-provided) |
| `succeeded` / `failed` / `skipped` | Success / fail / skip task counts |
| `processed` | Processed count (success + fail + skip) |
| `pending` | Pending count (`max(0, input_total - processed)`) |
| `upstream_counts` / `downstream_counts` | Task count mappings of each upstream / downstream node |

## Usage Example

```python
from celestialflow.observer import ObserverHub, MetricsObserver


metrics = MetricsObserver()
hub = ObserverHub()
hub.add_observer(metrics)

# ... task graph runs ...

for node_name, nm in metrics.get_graph_metrics().items():
    print(node_name, nm.succeeded, nm.failed, nm.skipped, nm.pending)
```

## Relationship with Node / Assembly

- `BaseTaskNode` **no longer** holds counts and `TaskMetrics` itself; node counts are uniformly maintained by `MetricsObserver` based on events.
- During assembly (`assembly/core_run.py`), a `MetricsObserver` is created and registered into the node's `ObserverHub`; its read-only view is cross-provided to `LogInlet` and the snapshot handler for use.

## Notes

1. **Single-scope instance**: one `MetricsObserver` serves one run scope, avoiding count cross-talk from reuse across different graphs / nodes.
2. **Thread safety**: all internal storage access is under the protection of `_lock`.
3. **Structure is event-driven**: it does not depend on graph-construction structure events; any node can establish its storage cell as soon as a task event appears.