# Graph Analysis Utility Tests (test_analysis.py)

> 📅 Last Updated: 2026/05/23

## Purpose
Verifies the graph analysis utility functions in the `celestialflow.graph.util_analysis` module, ensuring the accuracy of graph construction, level computation, and source node lookup logic.

## Core Test Objects
- `build_networkx_graph`: Converts an adjacency list into a NetworkX directed graph.
- `compute_node_levels`: Computes the logical level of each node in the graph.
- `find_source_nodes`: Finds the entry nodes (source nodes) of the graph.

## Key Test Flow
1. **Graph Construction Tests**: Covers linear, cyclic, and isolated-node scenarios, verifying node count, edge count, and direction.
2. **Level Computation Tests**:
   - **DAG**: Verifies increasing levels for linear chain and fan-out structures.
   - **Cyclic Graph**: Verifies that nodes within a strongly connected component (SCC) share the same level.
   - **Disconnected Graph**: Verifies that each connected component starts independently from Level 0.
3. **Source Node Lookup Tests**:
   - **DAG**: Finds nodes with indegree 0.
   - **Pure Cycle**: Treats the SCC as a whole as the source, returning one representative.
   - **Wheel Topology**: Verifies that the center node is identified as the sole source.

## Test Focus
- **NetworkX Integration**: Ensures correct internal data structure conversion.
- **Level Consistency**: Robustness of level computation under complex topologies (e.g., cycle with a tail).
- **SCC Handling**: Ensures circular references do not cause infinite loops or incorrect level distribution.

## How to Run

```bash
# Run all
pytest tests/graph/test_analysis.py -v

# Graph construction tests only
pytest tests/graph/test_analysis.py::TestBuildNetworkxGraph -v

# Level computation tests only
pytest tests/graph/test_analysis.py -k "levels" -v

# Source node lookup tests only
pytest tests/graph/test_analysis.py -k "source" -v
```

## Performance Reference

| Test | Duration |
|------|----------|
| `TestBuildNetworkxGraph` | < 0.1s (pure in-memory computation) |
| `TestComputeNodeLevels` | < 0.1s |
| `TestFindSourceNodes` | < 0.1s |

## Important Details
- Uses lightweight Mock objects to simulate `Stage` and `Runtime` environments.
- All test cases are pure in-memory computations with extremely fast execution.

## Notes
- The test code is located at `tests/graph/test_analysis.py`, and the corresponding implementation is at `src/celestialflow/graph/util_analysis.py`.
