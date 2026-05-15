# test_analysis.py Test Documentation

> 📅 Last Updated: 2026/05/15

## Test Objective

Validates the graph analysis utility functions in the `celestialflow.graph.util_analysis` module, including:
- NetworkX directed graph construction (`build_networkx_graph`)
- Node level computation (`compute_node_levels`), including DAG and cyclic graphs
- Source node discovery (`find_source_nodes`), including pure cycles and wheel topologies

## Test Scope

| Test Class | Test Count | Coverage |
|------------|-----------|----------|
| `TestBuildNetworkxGraph` | 3 | Linear graph, cyclic graph, isolated nodes |
| `TestComputeNodeLevels` | 5 | Linear DAG, fan-out DAG, single cycle, cycle+tail, disconnected graph |
| `TestFindSourceNodes` | 4 | Linear DAG, multiple sources, pure cycle, wheel topology |

### Key Test Case Details

#### `test_linear`
- **Objective**: Validate node count, edge count, and successor relationships for an A -> B -> C linear graph.
- **Assertions**: 3 nodes, 2 edges, A's successor is B.

#### `test_cycle`
- **Objective**: Validate correct construction of a cyclic graph (A -> B -> C -> A).
- **Assertions**: 3 nodes, 3 edges, C's successor includes A.

#### `test_isolated_node`
- **Objective**: Validate a graph with isolated nodes (no edges).
- **Assertions**: 2 nodes, 0 edges.

#### `test_fan_out_dag`
- **Objective**: Level computation for an A -> {B, C} -> D fan-out DAG.
- **Assertions**: A at level 0, B and C at level 1, D at level 2.

#### `test_single_cycle`
- **Objective**: In a pure cycle (A -> B -> C -> A), all nodes belong to the same SCC and share a level.
- **Assertions**: A, B, C have the same level.

#### `test_cycle_with_tail`
- **Objective**: Cycle (A -> B -> C -> A) with a tail (A -> D); D is one level higher than the cycle.
- **Assertions**: Cycle nodes share the same level, D is at cycle level + 1.

#### `test_disconnected`
- **Objective**: Two independent chains (A -> B, X -> Y) each start from level 0.

#### `test_pure_cycle` (FindSourceNodes)
- **Objective**: A pure cycle has no nodes with `in_degree=0`, but the entire SCC is returned as a source.
- **Assertions**: Returns 1 source, belonging to a cycle node.

#### `test_wheel_topology`
- **Objective**: Wheel topology (Center -> {R1, R2, R3}, R1 -> R2 -> R3 -> R1); Center is the only source.

## Dependencies

| Dependency | Description |
|------------|-------------|
| `pytest` | Test framework |
| `networkx` | Graph data structure |
| `celestialflow.graph.util_analysis` | `build_networkx_graph`, `compute_node_levels`, `find_source_nodes` |

## How to Run

```bash
pytest tests/test_analysis.py -v
```

All test cases are pure in-memory graph computations, execution time `< 100ms`.

## Related Files

- `src/celestialflow/graph/util_analysis.py`: Implementation under test
- `tests/test_graph.py`: Indirectly uses analysis functions in `TaskGraph` integration scenarios
