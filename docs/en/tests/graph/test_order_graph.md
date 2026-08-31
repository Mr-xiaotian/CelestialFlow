# Graph Analysis Utility Tests (test_order_graph.py)

> 📅 Last Updated: 2026/08/31

## Purpose
Validates the basic graph analysis functions in `celestialflow.graph.util_order_graph`, including `OrderGraph` construction, level computation (`compute_node_levels`), source node lookup (`source_nodes`), SCC partitioning (`tarjan_scc`), and regression tests for iterative algorithms when depth exceeds Python's default recursion limit (approximately 1000).

## Core Test Objects
- `OrderGraph.from_edges` / `add_node` / `add_edge` / `successors`: Constructs and queries the ordered graph structure.
- `compute_node_levels`: Computes the logical levels of nodes in the graph (nodes within the same SCC share a level).
- `source_nodes`: Finds the entry nodes (source nodes) of the graph (returns one representative per SCC).
- `tarjan_scc`: Strongly connected component partitioning (iterative implementation).
- `DEEP = 5000`: A deep-chain/deep-ring size exceeding Python's default recursion limit, used to regression-test the iterative `tarjan_scc`.

## Test Coverage Matrix

| Test Class | Case Count | Coverage Target | Key Assertions |
|--------|--------|---------|---------|
| `TestBuildOrderGraph` | 3 | Linear chain / cyclic / isolated-node graph construction | Node count, total edges, `successors` adjacency direction are correct |
| `TestComputeNodeLevels` | 5 | Linear DAG, fan-out DAG, simple cycle, cycle with tail, disconnected graph | Levels increase monotonically, B/C are at the same level, nodes within a cycle share a level, tail is one level above the cycle, each connected component starts independently from 0 |
| `TestFindSourceNodes` | 4 | Linear DAG, multi-source, pure cycle, wheel topology | Source nodes have in-degree 0; pure-cycle SCC returns one representative; Center is the unique source |
| `TestDeepGraphRegression` | 3 | 5000-node deep chain / deep ring / full pipeline through TaskGraph | Deep-chain SCCs are all single points, no `RecursionError`; deep ring converges to a single SCC; `get_stages_summary` / `get_source_names` / `get_graph_analysis` work normally |
| **Total** | **15** | | |

## Key Test Flow

1. **Graph Construction** (`TestBuildOrderGraph`): Covers linear (A→B→C), cyclic (C→A closed), and isolated nodes, verifying the number of nodes and edges, and the adjacency direction.
2. **Level Computation** (`TestComputeNodeLevels`):
   - **DAG**: Linear chain levels increase monotonically; in fan-out, B and C are at the same level.
   - **Cyclic graph**: Nodes within an SCC share the same level; in a cycle with a tail, the tail node is one level above the cycle.
   - **Disconnected graph**: Each component starts computing independently from level 0.
3. **Source Node Lookup** (`TestFindSourceNodes`):
   - **DAG**: Returns nodes with in-degree 0 (can use `set` for order-independent assertions).
   - **Pure cycle**: Treats the SCC as a whole source and returns one representative.
   - **Wheel topology**: Center points to the ring, Center is the unique source.
4. **Deep-Graph Regression** (`TestDeepGraphRegression`):
   - Deep chain (5000 nodes): `tarjan_scc` produces all single-point SCCs, source node is `n0`, levels increase linearly to 4999.
   - Deep ring (5000 nodes): All nodes converge to a single SCC.
   - Deep chain through `TaskGraph` (`graph_mode="thread"`) full pipeline construction and analysis does not crash; `layersDict[4999] == ["n4999"]`, `get_stages_summary()` returns 5000 stages, `get_source_names() == ["n0"]`.

## Test Helper Functions
- `_make_graph(edges)`: Constructs a test graph from an edge definition (including implicitly appearing downstream nodes).
- `_make_chain(depth)`: Constructs a linear chain of `depth` nodes.
- `_make_ring(size)`: Constructs a closed ring of `size` nodes.

## Test Focus
- **OrderGraph Construction**: Ensures the internal ordered graph structure and adjacency relationships are correct.
- **Level Consistency**: Robustness of level computation under complex topologies such as cycles with tails.
- **SCC Handling**: Ensures circular references do not cause infinite loops or incorrect level/source node distribution.
- **Recursion Safety**: `tarjan_scc` was previously a recursive implementation; deep chains/rings would trigger `RecursionError`. After being changed to an iterative implementation, ultra-deep graphs should be able to complete analysis normally.

## How to Run

```bash
# Run all
pytest tests/graph/test_order_graph.py -v

# Run graph construction tests only
pytest tests/graph/test_order_graph.py::TestBuildOrderGraph -v

# Run level computation tests only
pytest tests/graph/test_order_graph.py::TestComputeNodeLevels -v

# Run source node lookup tests only
pytest tests/graph/test_order_graph.py::TestFindSourceNodes -v

# Run deep-graph regression tests only
pytest tests/graph/test_order_graph.py::TestDeepGraphRegression -v
```

## Performance Reference

| Test | Duration |
|------|------|
| `TestBuildOrderGraph` | < 0.1s (pure in-memory computation) |
| `TestComputeNodeLevels` | < 0.1s |
| `TestFindSourceNodes` | < 0.1s |
| `TestDeepGraphRegression` | ~1s (5000-node scale, pure in-memory computation) |

## Important Details
- Except for `TestDeepGraphRegression.test_deep_chain_through_taskgraph`, all tests are pure in-memory computation and execute very quickly.
- The deep-graph cases keep `DEEP` at 5000, balancing regression coverage with test duration.

## Notes
- Test code is located at `tests/graph/test_order_graph.py`; the corresponding implementation is at `src/celestialflow/graph/util_order_graph.py`.
