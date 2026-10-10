# src/celestialflow/persist/util_render.py

> 📅 Last Updated: 2026/10/09

`util_render.py` (formerly `graph/util_render.py`, migrated to `persist`) provides a **graph structure rendering utility**. It currently contains a single function `render_structure_list`, which renders a graph structure (nodes, adjacency list, source nodes) as a **framed, tree-shaped text list**, used by the log module to output a graph-structure overview when a task graph starts.

## render_structure_list

```python
def render_structure_list(
    nodes: list[str],
    edges: dict[str, list[str]],
    source_nodes: list[str],
) -> list[str]:
```

Generates a framed, tree-shaped text list from a graph structure (node metadata, adjacency list, source nodes).

### Rendering Rules

1. Taking `source_nodes` as roots, expand into a tree-shaped text following the `edges` adjacency list;
2. Cyclic or shared-subgraph nodes are expanded only once; re-occurrences are marked with `[Ref]`;
3. Nodes not reached from any root (isolated nodes) are appended at the end;
4. Root nodes do not draw connectors; child nodes use the `╞-->` / `╘-->` connectors.

### Edge Handling

- With no nodes (empty `nodes`), returns `["+ No nodes defined +"]`;
- When source nodes are not explicitly provided, they are inferred as all nodes that are not children of any edge; if still empty, the first node is taken as the source.

### Return Value Format

The returned string list has a border line at the start and end, with per-line content in between, for example:

```text
+----------------------+
| A                    |
| ╞--> B               |
|     ╘--> C [Ref]     |
| ╘--> D               |
+----------------------+
```

In-line content is padded with `ljust` to the same width to keep the border aligned.

## Internal Implementation Points

- **Explicit-stack iterative DFS with pre-order traversal**: avoids hitting Python's recursion limit (default ~1000 levels) on deep-chain graphs.
- Stack frames carry `(node_name, prefix, is_last, is_root)`: `is_root` indicates a root node — roots do not draw connectors and their children have an empty prefix; the prefixes of the remaining nodes are determined by whether the parent is the last item among its siblings.
- Each node is added to `expanded_nodes` the first time it is visited; subsequent encounters are marked `[Ref]` and expansion stops.
- A blank line is inserted between root nodes, and before the isolated nodes appended at the end.

## Usage Example

```python
from celestialflow.persist.util_render import render_structure_list

lines = render_structure_list(
    nodes=["A", "B", "C"],
    edges={"A": ["B", "C"]},
    source_nodes=["A"],
)
for line in lines:
    print(line)
```

## Callers

`LogInlet` (`persist/core_log.py`) calls this function in `on_graph_start`, rendering the graph metadata carried by the `GraphStartEvent` (`nodes` / `edges` / `source_nodes`) into structural text, which is then written to the log line by line.

## Notes

1. **Pure in-memory rendering**: the function does not write to disk or depend on runtime state; it only generates text based on the passed-in graph structure parameters.
2. **Migration note**: this utility was originally located in `util_render.py` in the `graph` module; it has now been migrated to `persist` for reuse by the log module.
3. **Returns a text list**: callers need to decide how to consume the returned string list themselves (e.g., printing line by line or writing it to a file).