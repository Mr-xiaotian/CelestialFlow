# RuntimeEstimators

> 📅 Last Updated: 2026/06/11

`runtime/util_estimators.py` provides runtime time-consumption estimation functions.

## Main Functions

- `calc_remaining(processed, pending, elapsed)`: Estimates the remaining time for a node.
  - **Params**: `processed` (`int`) — number of processed tasks; `pending` (`int`) — number of pending tasks; `elapsed` (`float`) — elapsed time in seconds.
  - **Returns**: `float` — estimated remaining time in seconds. Returns `0.0` when `processed` is 0.
- `calc_elapsed(status, last_elapsed, last_pending, interval)`: Accumulates elapsed time by status.
  - **Params**: `status` (`StageStatus`) — current stage status; `last_elapsed` (`float`) — previous elapsed time; `last_pending` (`int`) — previous pending count; `interval` (`float`) — collection interval in seconds.
  - **Returns**: `float` — updated elapsed time. When status is `STOPPED` or `last_pending` is 0, returns `last_elapsed` unchanged.
- `calc_global_pending(G, processed_map, pending_map)`: Estimates global pending task count based on DAG and observed metrics.
  - **Params**: `G` (`networkx.DiGraph`) — the directed graph; `processed_map` (`dict[str, int]`) — per-node processed count; `pending_map` (`dict[str, int]`) — per-node pending count.
  - **Returns**: `dict[str, int]` — per-node estimated global pending count. Uses a conservative traversal strategy starting from leaf nodes.

## Usage Examples

The following examples demonstrate usage of `RemainingTimeEstimator` related functions.

### calc_remaining: Estimate Node Remaining Time

```python
from celestialflow.runtime.util_estimators import calc_remaining

# 80 processed, 20 remaining, 40 seconds elapsed
remaining = calc_remaining(
    processed=80,
    pending=20,
    elapsed=40.0,
)
print(f"Estimated remaining time: {remaining:.2f} seconds")  # 10.0 seconds (20/80 * 40)

# Returns 0 when no processed data
remaining_zero = calc_remaining(processed=0, pending=100, elapsed=10.0)
print(f"No historical data: {remaining_zero} seconds")  # 0
```

### calc_elapsed: Accumulate Elapsed Time by Status

```python
from celestialflow.runtime.util_types import StageStatus
from celestialflow.runtime.util_estimators import calc_elapsed

# Node is running, 30 seconds elapsed previously, 5 pending, 2-second collection interval
elapsed = calc_elapsed(
    status=StageStatus.RUNNING,
    last_elapsed=30.0,
    last_pending=5,
    interval=2.0,
)
print(f"Updated elapsed time: {elapsed:.1f} seconds")  # 32.0 (30 + 2)

# Node has stopped, elapsed time no longer increases
elapsed_stopped = calc_elapsed(
    status=StageStatus.STOPPED,
    last_elapsed=50.0,
    last_pending=0,
    interval=2.0,
)
print(f"Stopped node: {elapsed_stopped:.1f} seconds")  # 50.0 (no longer increasing)
```

### calc_global_pending: Estimate Global Pending Task Count Based on DAG

```python
import networkx as nx
from celestialflow.runtime.util_estimators import calc_global_pending

# Build a simple DAG: A -> B -> C
G = nx.DiGraph()
G.add_edge("A", "B")
G.add_edge("B", "C")

# Input observed data
processed_map = {"A": 100, "B": 50, "C": 10}
pending_map = {"A": 0, "B": 50, "C": 90}

result = calc_global_pending(G, processed_map, pending_map)
for node, pending in result.items():
    print(f"Node {node}: estimated {pending} pending tasks")
```

## Use Cases

- Driving monitoring dashboard ETA display.
- Assisting in identifying potential congested nodes.
