# Clone Utility Tests (test_clone.py)

> 📅 Last Updated: 2026/05/28

## Purpose

Validates the three clone functions in `celestialflow.utils.util_clone` — `clone_executor`, `clone_stage`, and `clone_graph` — ensuring that after deep copying, the new objects have the same properties as the originals and are independent of each other.

## Core Test Targets

- `clone_executor`: Copies `TaskExecutor`, preserving `name`, `func`, and `execution_mode`.
- `clone_stage`: Copies `TaskStage`, preserving `name`, `func`, `execution_mode`, and `stage_mode`.
- `clone_graph`: Copies `TaskGraph`, preserving the complete DAG structure (nodes, edges, `schedule_mode`), with nodes independent of each other.

## Key Test Scenarios

### `clone_executor`
- After cloning, `name` / `func` / `execution_mode` match the original
- The clone is a different object (`is not` check)
- Modifying the clone's `execution_mode` does not affect the original

### `clone_stage`
- After cloning, `name` / `func` / `execution_mode` / `stage_mode` match the original
- The clone is a different object
- Modifying the clone's `execution_mode` does not affect the original stage

### `clone_graph`
- Simple DAG (A→B→C): after cloning, source node, NetworkX node set, and edge set are all consistent
- `schedule_mode` is correctly preserved
- Modifying a node's `execution_mode` in the cloned graph does not affect the corresponding node in the original graph

## How to Run

```bash
# Run all
pytest tests/utils/test_clone.py -v

# Run executor clone tests only
pytest tests/utils/test_clone.py -k "executor" -v

# Run stage clone tests only
pytest tests/utils/test_clone.py -k "stage" -v

# Run graph clone tests only
pytest tests/utils/test_clone.py -k "graph" -v
```

## Performance Reference

| Test Class | Duration |
|--------|------|
| `TestUtilClone` | ~0.1s |

## Important Details

- When cloning a graph, node and edge consistency is verified via the NetworkX graph; accessing the source node also triggers `_build_analysis`.
- `clone_graph` tests construct a directed acyclic graph `A → B → C` to verify graph structural integrity.

## Notes

- Clone utilities are used internally by `benchmark_graph` to duplicate graph structures for independent execution with different mode combinations.
- Related implementation is in `src/celestialflow/utils/util_clone.py`.
