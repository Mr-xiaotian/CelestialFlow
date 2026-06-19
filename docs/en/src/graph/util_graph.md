# OrderGraph and Graph Algorithm Utilities

> 📅 Last Updated: 2026/06/18

`graph/util_graph.py` provides the minimal graph structure `OrderGraph` plus a set of foundational graph algorithms used inside CelestialFlow.

## Main Capabilities

- `OrderGraph`
  - Minimal ordered directed graph
  - Stable node iteration order
  - Maintains both outgoing and incoming adjacency
- `in_degree(graph)`
  - Computes indegree for every node
- `is_dag(graph)`
  - Checks whether the graph is a DAG via Kahn's algorithm
- `topo_sort(graph)`
  - Returns a topological order when the graph is a DAG
- `tarjan_scc(graph)`
  - Computes strongly connected components with Tarjan's algorithm
- `get_condensation(graph)`
  - Builds the SCC condensation graph
- `source_nodes(graph)`
  - Returns one representative node from each source SCC
- `compute_node_levels(graph)`
  - Computes node levels for both DAG and cyclic graphs

## Design Notes

- `_nodes` uses `dict[str, None]` rather than `list[str]` so the graph can keep stable insertion order while preserving fast existence checks.
- The implementation is intentionally lightweight and in-memory only.
- The same graph structure is reused by `TaskGraph` analysis and runtime pending estimation.

## Relationship with `TaskGraph`

`TaskGraph` now uses `OrderGraph` directly during `_build_analysis()` to perform:

- source node discovery
- DAG detection
- node level computation

The runtime estimator also uses `OrderGraph` for DAG-aware pending propagation.

## Example

```python
from celestialflow.graph.util_graph import OrderGraph, compute_node_levels, source_nodes

graph = OrderGraph.from_edges(
    {"A": ["B", "C"], "B": ["D"], "C": ["D"]},
    ("A", "B", "C", "D"),
)

print(graph.nodes)
print(source_nodes(graph))
print(compute_node_levels(graph))
```
