# OrderGraph and Graph Algorithm Utilities

> 📅 Last Updated: 2026/08/31

`graph/util_order_graph.py` provides the minimal graph structure `OrderGraph` along with a set of basic graph algorithms built around it.

This file's current role is to:

- Provide a lightweight, stably ordered graph structure for internal framework use.
- Carry part of the graph analysis capabilities to reduce coupling with third-party graph structures.
- Provide a unified graph analysis foundation for `TaskGraph`, runtime estimation, and tests.

## Main Capabilities

### Graph Structure

- `OrderGraph`
  - A minimal ordered directed graph.
  - Node order is stably preserved in registration order.
  - Maintains both outgoing and incoming adjacency lists.

### Basic Operations

- `add_node(name)`: add a node; idempotent.
- `add_edge(u, v)`: add a directed edge; automatically creates endpoint nodes and deduplicates.
- `nodes`: returns all nodes in registration order.
- `out_edges`: returns a view of the outgoing adjacency list (**shared with internal storage, callers should not modify it**).
- `in_edges`: returns a view of the incoming adjacency list (**shared with internal storage, callers should not modify it**).
- `successors(name)`: returns successor nodes.
- `predecessors(name)`: returns predecessor nodes.
- `has_node(name)`: checks whether a node exists.
- `from_edges(out_edges, stage_names=None)`: build an `OrderGraph` from an adjacency map.

### Graph Algorithms

- `in_degree(graph)`: compute the in-degree of each node.
- `is_dag(graph)`: use Kahn's algorithm to check whether it is a DAG.
- `topo_sort(graph)`: return topological order; returns `None` if a cycle exists.
- `tarjan_scc(graph)`: compute strongly connected components using Tarjan's algorithm.
- `node_to_scc_index(sccs)`: build a node-to-SCC-index mapping.
- `get_condensation(graph)`: build the SCC condensation graph.
- `source_sccs(graph)`: return the SCCs whose in-degree is 0 in the condensation graph.
- `source_nodes(graph)`: extract one representative node from each source SCC.
- `compute_node_levels(graph)`: compute node levels, supporting both DAGs and graphs with cycles.

## Design Notes

### Why not `list`

`OrderGraph` uses `dict[str, None]` internally for `_nodes` rather than `list[str]`, because it needs to satisfy two things at once:

- Fast node existence checks.
- Stable node iteration order.

With a `list`, deduplication and existence checks are both linear; with a regular `set`, existence checks are fast but order is unstable. `dict` is effectively an "ordered set" here, which fits this scenario better.

### Why preserve order

Graph analysis itself does not necessarily require a fixed iteration order, but inside the framework, a stable order generally helps with:

- Reproducible debug output.
- More stable test results.
- Level analysis and topological results that better reflect the registration order when the graph was built.

## Level Computation Notes

`compute_node_levels(graph)` works as follows:

1. First perform strongly connected component decomposition on the original graph.
2. Collapse each SCC into a single node in the condensation graph.
3. Perform topological propagation on the condensation DAG.
4. Map SCC levels back to the original nodes.

Therefore:

- Ordinary nodes in a DAG receive levels according to their longest predecessor path.
- In a graph with cycles, nodes in the same cycle share the same level.

This level algorithm directly serves the current `TaskGraph` graph analysis process and no longer depends on external graph objects.

## Relationship with `TaskGraph`

`TaskGraph` currently performs the following directly on `OrderGraph` during `_build_analysis()`:

- Source node identification.
- DAG check.
- Node level computation.
- Topological and predecessor traversal required for runtime global pending estimation.

## Usage Examples

### Basic Graph Construction

```python
from celestialflow.graph.util_order_graph import OrderGraph, is_dag, topo_sort

graph = OrderGraph()
graph.add_edge("A", "B")
graph.add_edge("A", "C")
graph.add_edge("B", "D")
graph.add_edge("C", "D")

print(graph.nodes)  # ('A', 'B', 'C', 'D')
print(graph.successors("A"))  # ('B', 'C')
print(graph.predecessors("D"))  # ('B', 'C')
print(is_dag(graph))  # True
print(topo_sort(graph))  # ['A', 'B', 'C', 'D']
```

### Strongly Connected Components and Condensation

```python
from celestialflow.graph.util_order_graph import (
    OrderGraph,
    get_condensation,
    tarjan_scc,
)

graph = OrderGraph()
graph.add_edge("A", "B")
graph.add_edge("B", "C")
graph.add_edge("C", "A")
graph.add_edge("C", "D")

sccs = tarjan_scc(graph)
cond, _ = get_condensation(graph)

print(sccs)
print(cond.nodes)
print(cond.out_edges)
```

### Node Levels

```python
from celestialflow.graph.util_order_graph import OrderGraph, compute_node_levels

graph = OrderGraph()
graph.add_edge("Input", "Clean")
graph.add_edge("Clean", "Parse")
graph.add_edge("Parse", "Store")

levels = compute_node_levels(graph)
print(levels)
```

## Usage Recommendations

- If you only need a lightweight graph structure and basic graph algorithms, prefer `OrderGraph`.
- If you need to stay consistent with `TaskGraph`'s current analysis logic, prefer the algorithm functions here.
- If you need to export a printable graph structure, continue to combine it with `util_render.py`.
