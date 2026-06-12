# GraphSerialize

> 📅 Last Updated: 2026/06/11

`graph/util_serialize.py` is responsible for TaskGraph structure serialization and text rendering.

## Main Capabilities

- `build_structure_graph(stage_dict, out_edges, source_stages)`: Build a structure JSON from a node dictionary, adjacency table, and source nodes.
  - **Params**: `stage_dict` (`dict[str, TaskStage]`) — node name → `TaskStage` mapping; `out_edges` (`dict[str, list[str]]`) — adjacency table; `source_stages` (`list[TaskStage]`) — list of source nodes (with in-degree 0).
  - **Returns**: `dict` — a JSON structure containing `nodes` (list of node dicts with id, name, mode, source, children) and `source_nodes` (list of source names).
- `format_structure_list_from_graph(structure)`: Format a structure JSON as printable tree-style text.
  - **Params**: `structure` (`dict`) — the structure JSON produced by `build_structure_graph`.
  - **Returns**: `list[str]` — formatted list of strings, each representing a line of the tree diagram with a border frame.

## Usage Examples

The following examples demonstrate usage of the graph serialization and text-rendering tools.

```python
from celestialflow import TaskGraph, TaskStage
from celestialflow.graph.util_serialize import (
    build_structure_graph,
    format_structure_list_from_graph,
)

# 1. Build a simple DAG graph
s1 = TaskStage("Fetch", func=lambda x: x)
s2 = TaskStage("Parse", func=lambda x: x * 2)
s3 = TaskStage("Save", func=lambda x: x + 1)

graph = TaskGraph(name="SerializeGraph")
graph.set_stages([s1, s2, s3])
graph.connect([s1], [s2])
graph.connect([s2], [s3])

# 2. Get source nodes
sources = graph.get_source_stages()
print(f"Source node count: {len(sources)}")

# 3. Build structure JSON
graph_json = build_structure_graph(
    stage_dict=graph.stage_dict,
    out_edges=graph.out_edges,
    source_stages=sources,
)
print(f"Structure JSON: {graph_json}")

# 4. Format as tree text
rendered = format_structure_list_from_graph(graph_json)
for line in rendered:
    print(line)

# Example output:
# +-------------------------------------------+
# | Fetch::<lambda> (S:serial, E:serial)       |
# | ╘-->Parse::<lambda> (S:serial, E:serial)   |
# |     ╘-->Save::<lambda> (S:serial, E:serial)|
# +-------------------------------------------+
```

### Via TaskGraph Built-in Methods

`TaskGraph` provides convenient `get_structure_graph()` and `get_structure_list()` methods:

```python
from celestialflow import TaskGraph, TaskStage

s1 = TaskStage("Step1", func=lambda x: x.upper())
s2 = TaskStage("Step2", func=lambda x: len(x))
s3 = TaskStage("Step3", func=lambda x: x * 10)

graph = TaskGraph(name="SerializeGraph2")
graph.set_stages([s1, s2, s3])
graph.connect([s1], [s2])
graph.connect([s2], [s3])

# Get JSON graph structure (dict)
structure = graph.get_structure_graph()
print("JSON structure:")
import json
print(json.dumps(structure, indent=2, ensure_ascii=False))

# Get formatted tree text
tree_lines = graph.get_structure_list()
print("\nTree structure:")
for line in tree_lines:
    print(line)
```

## Output Features

- Supports cycle/reference node marking (`[Ref]`).
- Supports multi-source (forest) structure output.
- Unconnected nodes (no parent nor in source node list) are also rendered as standalone tree roots.
