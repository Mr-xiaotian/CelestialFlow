# GraphRender

> 📅 Last Updated: 2026/09/09

`graph/util_render.py` provides a utility for rendering graph structures as framed, tree-shaped text lists. It is called directly by `TaskGraph.get_structure_list()` to visualize the task graph topology in logs / CLI output.

## Main Capabilities

- `render_structure_list(nodes, edges, source_nodes)`: generate a framed, tree-shaped text list from a node name list, the adjacency map, and the source node list.

## render_structure_list

```python
def render_structure_list(
    nodes: list[str],
    edges: dict[str, list[str]],
    source_nodes: list[str],
) -> list[str]: ...
```

### Rendering Rules

- Expand into a tree-shaped text starting from `source_nodes` as roots, following the `edges` adjacency map.
- Cyclic or shared-subgraph nodes are expanded only once; re-occurrences are marked with ` [Ref]`.
- Isolated nodes not reached from any root are appended at the end.
- Root nodes do not draw connectors; child nodes use the `╞-->` / `╘-->` connectors.
- Uses an **explicit-stack iterative DFS** with pre-order traversal to avoid hitting Python's recursion limit (default ~1000 levels) on deep chains.
- Returns a list of strings wrapped between `+---+` border lines, with each content line formatted as `| <content> |`.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `nodes` | `list[str]` | Node name list, passed in registration order |
| `edges` | `dict[str, list[str]]` | Outgoing adjacency map `{node_name: [next_node_name, ...]}` |
| `source_nodes` | `list[str]` | List of source node names; when empty, it is auto-inferred from `edges` or taken from the first element of `nodes` |

### Return Value

`list[str]` — one string per line, with `+---+` border lines at the start and end, and content lines padded with `| ` on the left and right.

## Usage Examples

The following examples show direct calls to `render_structure_list`, as well as indirect calls via `TaskGraph.get_structure_list()`.

### Direct Call

```python
from celestialflow.graph.util_render import render_structure_list

# Node name list
nodes = ["Fetch", "Parse", "Save"]

# Outgoing adjacency map
edges = {
    "Fetch": ["Parse"],
    "Parse": ["Save"],
}

# Source nodes
source_nodes = ["Fetch"]

lines = render_structure_list(nodes, edges, source_nodes)
for line in lines:
    print(line)

# Example output:
# +--------------------------+
# | Fetch                    |
# | ╘-->Parse                |
# |     ╘-->Save             |
# +--------------------------+
```

### Handling Empty Graph

```python
from celestialflow.graph.util_render import render_structure_list

print(render_structure_list([], {}, []))
# ['+ No stages defined +']
```

### Via TaskGraph Built-in Method

`TaskGraph.get_structure_list()` automatically collects `get_nodes()`, `order_graph.out_edges`, and `get_source_nodes()`, then calls `render_structure_list`:

```python
from celestialflow import TaskGraph, TaskExecutor

s1 = TaskExecutor("Step1", func=lambda x: x.upper())
s2 = TaskExecutor("Step2", func=lambda x: len(x))
s3 = TaskExecutor("Step3", func=lambda x: x * 10)

graph = TaskGraph(name="RenderDemo", graph_mode="thread")
graph.set_nodes([s1, s2, s3])
graph.connect([s1], [s2])
graph.connect([s2], [s3])

graph.run({s1.get_name(): ["hello"]})

# Get the formatted tree-shaped text
tree_lines = graph.get_structure_list()
for line in tree_lines:
    print(line)
```

## Output Characteristics

- Supports marking cyclic / reference nodes (`[Ref]`): when a node has already been expanded, subsequent occurrences append ` [Ref]`.
- Supports multi-source node (forest) structure output: roots are separated by blank lines.
- Unconnected nodes (no parent and not in the source node list) are also rendered as independent tree roots.
- DFS uses an explicit stack frame `(node_name, prefix, is_last, is_root)`, producing the same result as the recursive version while handling deep chain graphs.

## Relationship with Other Modules

- `TaskGraph.get_structure_list()` is the main caller of this function, used to visualize the topology in logs and monitoring panels.
- This function only depends on the node name list and the adjacency map; it does not directly read attributes from node objects. Any graph structure providing an equivalent adjacency map can serve as input.
