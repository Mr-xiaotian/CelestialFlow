# Clone Utility Tests (test_clone.py)

> 📅 Last Updated: 2026/09/09

## Purpose

Validates the `clone_executor` and `clone_graph` clone functions in `celestialflow.benchmark.util_clone`, ensuring that after deep copying, the new objects have the same properties as the originals and are independent of each other. The "graph node" series of cases cover the `clone_executor` reuse semantics in the graph node context.

## Core Test Objects

- `clone_executor`: Copies `TaskExecutor`, preserving `name`, `func`, and `execution_mode`; it also applies to `TaskExecutor` instances used as graph nodes.
- `clone_graph`: Copies `TaskGraph`, preserving the complete DAG structure (nodes, edges) and `graph_mode`, with nodes independent of each other.

## Key Test Scenarios

### `clone_executor`
- After cloning, `name` / `func` / `execution_mode` match the original
- The clone is a different object (`is not` check)
- Modifying the clone's `execution_mode` does not affect the original

### `clone_executor` as a graph node (`graph node`)
- After cloning, `name` / `func` / `execution_mode` match the original node
- The clone is a different object
- Modifying the clone's `execution_mode` does not affect the original node

### `clone_graph`
- Simple DAG (A→B→C): after cloning, source nodes, `OrderGraph` node set, and out-edge adjacency list are all consistent
- Modifying a node's `execution_mode` in the cloned graph does not affect the corresponding node in the original graph
- The default local event client should remain instance-independent after cloning.
- For a graph with a `TaskReporter`, the cloned graph should bind a new reporter instance (`cloned.reporter.task_graph is cloned`)

## Test Coverage Matrix

| Test Function | Coverage Goal |
|----------|----------|
| `test_clone_executor_same_attributes` | Key attributes match after cloning |
| `test_clone_executor_different_object` | Clone returns a new object |
| `test_clone_executor_independent` | Modifying the clone does not affect the original executor |
| `test_clone_graph_node_same_attributes` | When used as a graph node, `clone_executor` preserves the core attributes |
| `test_clone_graph_node_different_object` | When used as a graph node, the clone returns an independent object |
| `test_clone_graph_node_independent` | When used as a graph node, modifying the clone does not affect the original node |
| `test_clone_graph_structure` | DAG structure, source nodes, `OrderGraph` nodes and edges are consistent |
| `test_clone_graph_independent` | Modifying nodes in the cloned graph does not affect the original graph |
| `test_clone_graph_creates_independent_local_event_client` | Local event client instances are independent |
| `test_clone_graph_rebinds_task_reporter_to_cloned_graph` | A graph with a `TaskReporter` binds a new reporter instance after cloning |

## How to Run

```bash
# Run all
pytest tests/benchmark/test_clone.py -v

# Run executor clone tests only
pytest tests/benchmark/test_clone.py -k "executor" -v

# Run graph node / graph clone tests only
pytest tests/benchmark/test_clone.py -k "graph" -v
```

## Performance Reference

| Test Class | Duration |
|--------|------|
| `TestUtilClone` | ~0.1s |

## Important Details

- After cloning a graph, the `OrderGraph` returned via `get_order_graph()` is used to verify node set and out-edge adjacency consistency; accessing `get_source_nodes()` also triggers `_build_analysis` on the cloned graph.
- `clone_graph` tests construct a directed acyclic graph `A → B → C` to verify graph structural integrity.
- The `LocalEventClient` independence verification ensures the cloned graph has an independent event bus, preventing runtime state interference between instances.
- For a graph with a `TaskReporter`, after cloning the graph should bind a new reporter instance; `cloned.reporter.task_graph` points to the cloned graph.
- The `# 运行方式` comment at the end of the file matches the `pytest` commands above for easy copy-and-run.

## Notes

- Clone utilities are used internally by `benchmark_graph` to duplicate graph structures for independent execution with different mode combinations.
- Related implementation is in `src/celestialflow/benchmark/util_clone.py`.
