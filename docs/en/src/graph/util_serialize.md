# GraphSerialize

> 📅 Last Updated: 2026/05/28

`graph/util_serialize.py` handles TaskGraph structure serialization and text formatting.

## Main Capabilities

- `build_structure_graph(source_stages, out_edges, stage_dict)`: Recursively builds a structure JSON from a set of source nodes.
- `format_structure_list_from_graph(roots)`: Formats the structure JSON into a printable tree-style text.

## Usage Examples

The following examples demonstrate the usage of graph serialization and text formatting tools.

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

graph = TaskGraph()
graph.set_stages([s1, s2, s3])
graph.connect([s1], [s2])
graph.connect([s2], [s3])

# 2. Get source nodes
sources = graph.get_source_stages()
print(f"Source node count: {len(sources)}")

# 3. Build structure JSON
graph_json = build_structure_graph(
    source_stages=sources,
    out_edges=graph.out_edges,
    stage_dict=graph.stage_dict,
)
print(f"Structure JSON: {graph_json}")

# 4. Format as tree text
rendered = format_structure_list_from_graph(graph_json)
for line in rendered:
    print(line)

# Sample output:
# +-------------------------------------------+
# | Fetch::<lambda> (S:serial, E:serial)       |
# | ╘-->Parse::<lambda> (S:serial, E:serial)   |
# |     ╘-->Save::<lambda> (S:serial, E:serial)|
# +-------------------------------------------+
```

### Via TaskGraph Built-in Methods

`TaskGraph` provides convenient `get_structure_json()` and `get_structure_list()` methods:

```python
from celestialflow import TaskGraph, TaskStage

s1 = TaskStage("Step1", func=lambda x: x.upper())
s2 = TaskStage("Step2", func=lambda x: len(x))
s3 = TaskStage("Step3", func=lambda x: x * 10)

graph = TaskGraph()
graph.set_stages([s1, s2, s3])
graph.connect([s1], [s2])
graph.connect([s2], [s3])

# Get JSON graph structure
json_structure = graph.get_structure_json()
print("JSON Structure:")
import json
print(json.dumps(json_structure, indent=2, ensure_ascii=False))

# Get formatted tree text
tree_lines = graph.get_structure_list()
print("\nTree Structure:")
for line in tree_lines:
    print(line)
```

## Output Characteristics

- Supports cyclic/reference node marking (`is_ref`).
- Supports multi-source node (forest) structure output.
