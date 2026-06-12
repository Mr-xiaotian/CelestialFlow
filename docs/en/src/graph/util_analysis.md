# GraphAnalysis

> 📅 Last Updated: 2026/06/11

`graph/util_analysis.py` provides graph analysis tools powered by `networkx`.

## Main Capabilities

- `build_networkx_graph(out_edges, stage_dict)`: Build a `networkx.DiGraph` from an adjacency table and Stage mapping.
  - **Params**: `out_edges` (`dict[str, list[str]]`) — per-node list of downstream node names; `stage_dict` (`dict[str, TaskStage]`) — node name → `TaskStage` mapping.
  - **Returns**: `networkx.DiGraph` — a directed graph with node attributes (name, execution_mode, stage_mode, func_name) attached.
- `compute_node_levels(G)`: Compute level partitioning for a directed graph (supports both DAG and cyclic graphs).
  - **Params**: `G` (`networkx.DiGraph`) — the directed graph.
  - **Returns**: `dict[str, int]` — `node -> level` mapping, where level 0 is the root. For cyclic graphs, uses a heuristic iterative approach.
- `find_source_nodes(G)`: Find source nodes in a directed graph (nodes with in-degree 0).
  - **Params**: `G` (`networkx.DiGraph`) — the directed graph.
  - **Returns**: `list[str]` — list of source node names.

## Usage Examples

The following examples demonstrate usage of each graph analysis tool function.

```python
import networkx as nx
from celestialflow import TaskGraph, TaskStage
from celestialflow.graph.util_analysis import (
    build_networkx_graph,
    compute_node_levels,
    find_source_nodes,
)

# 1. Build a TaskGraph with a DAG
s1 = TaskStage("A", func=lambda x: x + 1)
s2 = TaskStage("B", func=lambda x: x * 2)
s3 = TaskStage("C", func=lambda x: x - 1)
s4 = TaskStage("D", func=lambda x: x ** 2)

graph = TaskGraph(name="AnalysisGraph")
graph.set_stages([s1, s2, s3, s4])
graph.connect([s1], [s2])
graph.connect([s1], [s3])
graph.connect([s2], [s4])
graph.connect([s3], [s4])

# 2. Build networkx DiGraph
G = build_networkx_graph(graph.out_edges, graph.stage_dict)
print(f"Node count: {G.number_of_nodes()}")  # 4
print(f"Edge count: {G.number_of_edges()}")   # 4
print(f"Node attributes: {dict(G.nodes(data=True))}")

# 3. Compute node levels
levels = compute_node_levels(G)
print(f"Node levels: {levels}")
for node, lv in sorted(levels.items(), key=lambda x: x[1]):
    print(f"  Level {lv}: {node}")

# 4. Find source nodes (in-degree 0)
sources = find_source_nodes(G)
print(f"Source nodes: {sources}")  # ['A']
```

### Combined with TaskGraph's get_graph_analysis

```python
from celestialflow import TaskGraph, TaskStage

# Build graph, execute, then get analysis info
graph = TaskGraph(name="AnalysisGraph2")
s1 = TaskStage("X", func=lambda x: x)
s2 = TaskStage("Y", func=lambda x: x * 2)
graph.set_stages([s1, s2])
graph.connect([s1], [s2])

analysis = graph.get_graph_analysis()
print(f"Is DAG: {analysis['isDAG']}")       # True
print(f"Schedule mode: {analysis['scheduleMode']}")  # eager
print(f"Layer distribution: {analysis['layersDict']}")
print(f"Graph class name: {analysis['className']}")

# Get networkx graph
nx_graph = graph.get_networkx_graph()
print(f"Type: {type(nx_graph).__name__}")  # DiGraph
```

## Use Cases

- Determining whether the graph is a DAG after TaskGraph initialization.
- Generating layer information required for staged scheduling.
- Automatically identifying source nodes for task injection.
- Providing level data for topology visualization.
