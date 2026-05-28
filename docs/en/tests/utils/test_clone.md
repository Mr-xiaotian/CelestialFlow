# Clone Utility Tests (test_clone.py)

> 📅 Last Updated: 2026/05/28

## Purpose

Validates the three clone functions in `celestialflow.utils.util_clone`: `clone_executor`, `clone_stage`, and `clone_graph`, ensuring that deep-copied objects have attributes identical to the originals and are independent of each other.

## Core Test Targets

- `clone_executor`: Copies a `TaskExecutor`, preserving `name`, `func`, `execution_mode`.
- `clone_stage`: Copies a `TaskStage`, preserving `name`, `func`, `execution_mode`, `stage_mode`.
- `clone_graph`: Copies a `TaskGraph`, preserving the complete DAG structure (nodes, edges, `schedule_mode`), with nodes independent of each other.

## Key Test Scenarios

### `clone_executor`
- Cloned `name` / `func` / `execution_mode` are identical to the original
- Clone returns a different object (`is not` check)
- Modifying the clone's `execution_mode` does not affect the original

### `clone_stage`
- Cloned `name` / `func` / `execution_mode` / `stage_mode` are identical to the original
- Clone returns a different object
- Modifying the clone's `execution_mode` does not affect the original stage

### `clone_graph`
- Simple DAG (A→B→C): cloned source nodes, NetworkX node set, and edge set are all identical
- `schedule_mode` is correctly preserved
- Modifying a node's `execution_mode` in the cloned graph does not affect the corresponding node in the original graph

## How to Run

```bash
# Run all
pytest tests/utils/test_clone.py -v

# Executor clone tests only
pytest tests/utils/test_clone.py -k "executor" -v

# Stage clone tests only
pytest tests/utils/test_clone.py -k "stage" -v

# Graph clone tests only
pytest tests/utils/test_clone.py -k "graph" -v
```

## Performance Reference

| Test Class | Duration |
|------------|----------|
| `TestUtilClone` | ~0.1s |

## Key Details

- When cloning a graph, node and edge consistency is verified via the NetworkX graph; accessing source nodes also triggers `_build_analysis`.
- The `clone_graph` test constructs a directed acyclic graph `A → B → C` to verify graph structure integrity.

## Notes

- The clone utilities are used internally by `benchmark_graph` to replicate graph structures for independent execution across different mode combinations.
- Related implementation is in `src/celestialflow/utils/util_clone.py`.
