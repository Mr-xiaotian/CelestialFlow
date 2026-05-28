# GraphAnalysis

> 📅 Last Updated: 2026/05/28

`graph/util_analysis.py` provides graph analysis tools based on `networkx`.

## Main Capabilities

- `build_networkx_graph(out_edges, stage_dict)`: Builds a `networkx.DiGraph` from an adjacency list and Stage mapping.
- `compute_node_levels(G)`: Performs level partitioning on a directed graph (supports both DAGs and cyclic graphs), returning a `node -> level` mapping.
- `find_source_nodes(G)`: Finds source nodes in a directed graph (nodes with in-degree of 0), returning a list of source nodes.

## Usage Examples

The following examples demonstrate the usage of each graph analysis function.

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

graph = TaskGraph()
graph.set_stages([s1, s2, s3, s4])
graph.connect([s1], [s2])
graph.connect([s1], [s3])
graph.connect([s2], [s4])
graph.connect([s3], [s4])

# 2. Build networkx DiGraph
G = build_networkx_graph(graph.out_edges, graph.stage_dict)
print(f"Nodes: {G.number_of_nodes()}")  # 4
print(f"Edges: {G.number_of_edges()}")  # 4
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

### Integration with TaskGraph.get_graph_analysis

```python
from celestialflow import TaskGraph, TaskStage

# Build graph and get analysis info after execution
graph = TaskGraph()
s1 = TaskStage("X", func=lambda x: x)
s2 = TaskStage("Y", func=lambda x: x * 2)
graph.set_stages([s1, s2])
graph.connect([s1], [s2])

analysis = graph.get_graph_analysis()
print(f"Is DAG: {analysis['isDAG']}")  # True
print(f"Schedule mode: {analysis['scheduleMode']}")  # eager
print(f"Layer distribution: {analysis['layersDict']}")
print(f"Adjacency list: {analysis['out_edges']}")

# Get networkx graph
nx_graph = graph.get_networkx_graph()
print(f"Type: {type(nx_graph).__name__}")  # DiGraph
```

## Use Cases

- Analyzing whether a TaskGraph is a DAG after initialization.
- Generating level information required for staged scheduling.
- Automatically identifying source nodes for task injection.
- Providing level data for topological visualization.
