# Graph Analysis Utility Tests (test_utilgraph.py)

> 📅 Last Updated: 2026/06/22

## Purpose
Validates the basic graph analysis functions in `celestialflow.graph.util_graph`, ensuring the accuracy of `OrderGraph` construction, level computation, and source-node lookup logic.

## Core Test Targets
- `OrderGraph.from_edges`: Converts an adjacency list into an `OrderGraph`.
- `compute_node_levels`: Computes the logical levels of nodes in the graph.
- `source_nodes`: Finds the entry nodes (source nodes) of the graph.

## Key Test Flow
1. **Graph construction tests**: Cover linear, cyclic, and isolated-node scenarios, verifying node/edge counts and directions.
2. **Level computation tests**:
   - **DAG**: Verifies level increases in linear chains and fan-out structures.
   - **Cyclic graph**: Verifies nodes within a strongly connected component (SCC) share the same level.
   - **Disconnected graph**: Verifies each connected component starts computing from level 0 independently.
3. **Source node lookup tests**:
   - **DAG**: Finds nodes with in-degree 0.
   - **Pure cycle**: Treats the SCC as a whole source and returns one representative.
   - **Wheel topology**: Verifies the center node is identified as the unique source.

## Test Focus
- **OrderGraph construction**: Ensures the internal ordered graph structure and adjacency relationships are correct.
- **Level consistency**: Robustness of level computation under complex topologies such as cycles with tails.
- **SCC handling**: Ensures circular references do not cause infinite loops or incorrect level distribution.

## How to Run

```bash
# Run all
pytest tests/graph/test_utilgraph.py -v

# Run graph construction tests only
pytest tests/graph/test_utilgraph.py::TestBuildOrderGraph -v

# Run level computation tests only
pytest tests/graph/test_utilgraph.py -k "levels" -v

# Run source node lookup tests only
pytest tests/graph/test_utilgraph.py -k "source" -v
```

## Performance Reference

| Test | Duration |
|------|------|
| `TestBuildOrderGraph` | < 0.1s (pure in-memory computation) |
| `TestComputeNodeLevels` | < 0.1s |
| `TestFindSourceNodes` | < 0.1s |

## Important Details
- All test cases are pure in-memory computations and execute very quickly.

## Notes
- Test code is located at `tests/graph/test_utilgraph.py`; the corresponding implementation is at `src/celestialflow/graph/util_graph.py`.
