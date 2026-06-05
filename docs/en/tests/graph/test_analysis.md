# Graph Analysis Utility Tests (test_analysis.py)

> Last Updated: 2026/05/23

## Purpose
Validates the graph analysis helpers in `celestialflow.graph.util_analysis`, ensuring graph construction, level computation, and source-node lookup behave correctly.

## Key Test Objects
- `build_networkx_graph`: Converts an adjacency list into a NetworkX directed graph.
- `compute_node_levels`: Computes the logical level of each node in a graph.
- `find_source_nodes`: Finds the entry nodes, or source nodes, of a graph.

## Key Test Flow
1. **Graph construction tests**: Cover linear graphs, cyclic graphs, and isolated-node cases, verifying edge direction and node/edge counts.
2. **Level computation tests**:
   - **DAG**: Verifies increasing levels for linear chains and fan-out structures.
   - **Cyclic graphs**: Verifies that nodes within the same strongly connected component (SCC) share one logical level.
   - **Disconnected graphs**: Verifies that each connected component starts independently from level 0.
3. **Source-node lookup tests**:
   - **DAG**: Finds nodes whose in-degree is 0.
   - **Pure cycle**: Treats the SCC as a source and returns one representative node.
   - **Wheel topology**: Verifies that the center node is recognized as the only source.

## Test Focus
- **NetworkX integration**: Ensures internal structures are converted correctly.
- **Level consistency**: Checks robustness of level computation on complex topologies such as cycles with tails.
- **SCC handling**: Ensures cyclic references do not cause infinite loops or incorrect level layouts.

## How to Run

```bash
# Run all tests
pytest tests/graph/test_analysis.py -v

# Run graph construction tests only
pytest tests/graph/test_analysis.py::TestBuildNetworkxGraph -v

# Run level computation tests only
pytest tests/graph/test_analysis.py -k "levels" -v

# Run source-node tests only
pytest tests/graph/test_analysis.py -k "source" -v
```

## Performance Reference

| Test | Duration |
|------|----------|
| `TestBuildNetworkxGraph` | < 0.1s (in-memory only) |
| `TestComputeNodeLevels` | < 0.1s |
| `TestFindSourceNodes` | < 0.1s |

## Important Details
- Lightweight mock objects are used to simulate `Stage` and `Runtime`.
- All cases are in-memory computations, so execution is very fast.

## Notes
- The test code lives in `tests/graph/test_analysis.py`, and the implementation lives in `src/celestialflow/graph/util_analysis.py`.

