# GraphAnalysis

> 📅 Last Updated: 2026/05/15

`graph/util_analysis.py` provides graph analysis tools based on `networkx`.

## Main Capabilities

- `build_networkx_graph(out_edges, stage_runtime_dict)`: Builds a `networkx.DiGraph` from an adjacency list and stage runtime information.
- `compute_node_levels(G)`: Performs level partitioning on a directed graph (supports both DAGs and cyclic graphs), returning a `node -> level` mapping.
- `find_source_nodes(G)`: Finds source nodes in a directed graph (nodes with in-degree of 0), returning a list of source nodes.

## Use Cases

- Analyzing whether a TaskGraph is a DAG after initialization.
- Generating level information required for staged scheduling.
- Automatically identifying source nodes for task injection.
- Providing level data for topological visualization.
