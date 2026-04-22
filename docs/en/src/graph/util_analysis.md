# GraphAnalysis

`graph/util_analysis.py` provides graph analysis tools based on `networkx`.

## Main Capabilities

- `format_networkx_graph(structure_graph)`: Converts a serialized structure JSON into a `networkx.DiGraph`.
- `compute_node_levels(G)`: Performs level partitioning on a DAG and returns a `node -> level` mapping.

## Use Cases

- Analyze whether the graph is a DAG after TaskGraph initialization.
- Generate layer information required for staged scheduling.
- Provide level data for topological visualization.
