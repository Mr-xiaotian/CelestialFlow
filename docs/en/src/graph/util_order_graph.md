# src/celestialflow/graph/util_order_graph.py

> 📅 Last Updated: 2026/10/30

`graph/util_order_graph.py` provides the minimal graph structure `OrderGraph` along with a set of basic graph algorithms built around it.

This file's current role is to:

- Provide a lightweight, stably ordered graph structure for internal framework use.
- Carry part of the graph analysis capabilities to reduce coupling with third-party graph structures.
- Provide a unified graph analysis foundation for `TaskGraph` and tests.

## Main Capabilities

### Graph Structure

`OrderGraph` is a minimal ordered directed graph:

- Node order is stably preserved in registration order.
- Maintains both outgoing and incoming adjacency lists.
- Only supports "add node / add edge"; no removal operations are provided, so the key sets of `_in` and `_out` always stay in sync.
- `__repr__` outputs a summary of the form `OrderGraph(nodes=4, edges=4)`.

### Basic Operations

| Member | Signature | Description |
|--------|-----------|-------------|
| `add_node` | `(name: str) -> None` | Add a node; idempotent — does nothing if it already exists |
| `add_edge` | `(u: str, v: str) -> None` | Add a directed edge; automatically creates endpoint nodes and ignores duplicate edges |
| `nodes` | `-> list[str]` | Return all nodes in registration order (a copy) |
| `out_edges` | `-> dict[str, list[str]]` | **Reference view** of the outgoing adjacency list (shared with internal storage, callers must not modify) |
| `in_edges` | `-> dict[str, list[str]]` | **Reference view** of the incoming adjacency list (shared with internal storage, callers must not modify) |
| `successors` | `(name: str) -> tuple[str, ...]` | Return successors in insertion order; unknown nodes return an empty tuple |
| `predecessors` | `(name: str) -> tuple[str, ...]` | Return predecessors in insertion order; unknown nodes return an empty tuple |

### Graph Algorithms

| Function | Returns | Description |
|----------|---------|-------------|
| `in_degree(graph)` | `dict[str, int]` | In-degree of each node |
| `is_dag(graph)` | `bool` | Determine whether the graph is a DAG using Kahn's algorithm |
| `topo_sort(graph)` | `list[str] \| None` | Return the topological order from Kahn's peeling process; `None` if a cycle exists |
| `tarjan_scc(graph)` | `list[list[str]]` | Compute strongly connected components using Tarjan's algorithm with explicit stack frames simulating recursion |
| `node_to_scc_index(sccs)` | `dict[str, int]` | Node → SCC index mapping |
| `get_condensation(graph)` | `tuple[OrderGraph, list[list[str]]]` | Build the SCC condensation graph, with SCC nodes named `scc_0`, `scc_1`, … |
| `source_sccs(graph)` | `list[list[str]]` | SCCs with in-degree 0 in the condensation graph |
| `source_nodes(graph)` | `list[str]` | Extract one representative node (`scc[0]`) from each source SCC |
| `compute_node_levels(graph)` | `dict[str, int]` | Compute node levels; supports both DAGs and graphs with cycles |

## Design Notes

### Internal Storage

`OrderGraph` internally uses two adjacency lists (`_in: dict[str, list[str]]` and `_out: dict[str, list[str]]`) to jointly express the node set and the edge set. `add_node` / `add_edge` never remove nodes, and node iteration order is guaranteed by Python `dict` insertion order, so the node set and edge set always remain stable.

`add_edge(u, v)` calls `add_node` on both endpoints first, so "connect first, add nodes later" is valid usage; adding the same edge twice is ignored (checked via `v not in self._out[u]`), keeping the adjacency lists stable.

### Why preserve order

Graph analysis itself does not necessarily require a fixed iteration order, but inside the framework, a stable order generally helps with:

- Reproducible debug output.
- More stable test results.
- Level analysis and topological results that better reflect the registration order when the graph was built.

### Non-recursive Tarjan Implementation

`tarjan_scc()` uses explicit stack frames `frames: list[tuple[node, successors, next_pos]]` to simulate recursive DFS, avoiding Python's recursion limit (about 1000 levels by default) on deep-chain graphs. The output is fully equivalent to the recursive version, and the SCC list order is the reverse topological order of the condensation graph.

## Level Computation Notes

`compute_node_levels(graph)` works as follows:

1. First perform strongly connected component decomposition on the original graph.
2. Collapse each SCC into a single node in the condensation graph.
3. Perform topological propagation on this condensation DAG (`level[succ] = max(level[succ], level[node] + 1)`).
4. Map SCC levels back to the original nodes.

Therefore:

- Ordinary nodes in a DAG receive levels according to their longest predecessor path; source nodes have level `0`.
- In a graph with cycles, nodes in the same cycle share the same level.
- The condensation graph is necessarily a DAG by construction; if `topo_sort(cond) is None`, the function raises `ValueError("condensation graph must be a DAG")` (a defensive branch).

This level algorithm directly serves the current `TaskGraph` graph analysis process and no longer depends on external graph objects.

## Relationship with `TaskGraph`

During `_build_analysis()`, `TaskGraph` operates directly on `OrderGraph` to perform:

- Source node identification (`source_nodes()`)
- DAG check (`is_dag()`)
- Node level computation (`compute_node_levels()`, then aggregated into `{level: [node names]}` via `runtime.util_format.cluster_by_value_sorted`)

Note the semantic difference: this module's `is_dag(graph)` is a **module-level function** taking an `OrderGraph`; the member with the same name on `TaskGraph` is a **no-argument method** `graph.is_dag()`. Do not mix the two. `TaskGraph`'s analysis results use a "lazy + `_analysis_dirty` dirty flag" cache, so what is passed in here is always the complete `self.order_graph`.

## Usage Examples

### Basic Graph Construction

```python
from celestialflow.graph.util_order_graph import OrderGraph, is_dag, topo_sort

graph = OrderGraph()
graph.add_edge("A", "B")
graph.add_edge("A", "C")
graph.add_edge("B", "D")
graph.add_edge("C", "D")

print(graph.nodes)  # ['A', 'B', 'C', 'D']
print(graph.successors("A"))  # ('B', 'C')
print(graph.predecessors("D"))  # ('B', 'C')
print(is_dag(graph))  # True
print(topo_sort(graph))  # ['A', 'B', 'C', 'D']
print(graph)  # OrderGraph(nodes=4, edges=4)
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

print(sccs)  # the cyclic A/B/C are grouped into one SCC, D forms its own group
print(cond.nodes)  # ['scc_0', 'scc_1']
print(cond.out_edges)  # cross-SCC edges have been deduplicated
```

### Node Levels

```python
from celestialflow.graph.util_order_graph import OrderGraph, compute_node_levels

graph = OrderGraph()
graph.add_edge("Input", "Clean")
graph.add_edge("Clean", "Parse")
graph.add_edge("Parse", "Store")

levels = compute_node_levels(graph)
print(levels)  # Input=0, Clean=1, Parse=2, Store=3 (dict key order is not guaranteed to match registration order)
```

### Source Nodes and Cycles

```python
from celestialflow.graph.util_order_graph import (
    OrderGraph,
    compute_node_levels,
    source_nodes,
)

graph = OrderGraph()
graph.add_edge("A", "B")
graph.add_edge("B", "C")
graph.add_edge("C", "B")  # B <-> C forms a cycle

print(source_nodes(graph))  # ['A']
print(compute_node_levels(graph))  # A=0; B and C belong to the same cycle, both at level 1
```

## Usage Recommendations

- If you only need a lightweight graph structure and basic graph algorithms, prefer `OrderGraph`.
- If you need to stay consistent with `TaskGraph`'s current analysis logic, prefer the algorithm functions here.
- `out_edges` / `in_edges` return the internal dictionaries themselves; if you need to modify them, first make a copy with `dict(...)`.
- If you need to export a printable graph structure text, combine it with `render_structure_list` from `persist.util_render`.
