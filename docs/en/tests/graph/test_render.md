# Graph Structure Rendering Tests (test_render.py)

> 📅 Last Updated: 2026/08/31

## Purpose
Verifies that `celestialflow.graph.util_render.render_structure_list` can render a graph structure (node metadata, adjacency list, source nodes) as a tree-shaped text list with borders, covering scenarios such as normal DAGs, cyclic graphs, empty graphs, and ultra-deep chains, while ensuring that deep-graph rendering does not trigger Python's default recursion limit.

## Core Test Objects
- `render_structure_list(nodes, edges, source_nodes)`: The rendering function, returning a list of bordered strings.
- `DEEP = 5000`: A deep-chain size exceeding Python's default recursion limit (approximately 1000), used to regression-test the iterative rendering logic.
- `make_node(name, mode, workers)`: Helper function that constructs a node metadata dictionary containing `func_name` / `execution_mode` / `max_workers`.

## Test Coverage Matrix

| Test Class | Case Count | Coverage Target | Key Assertions |
|--------|--------|---------|---------|
| `TestUtilRender` | 4 | Normal DAG rendering, empty structure, cyclic graph reference marker, ultra-deep chain rendering | Node label format `(E:<mode>, W:<workers>)`; empty structure returns `"+ No stages defined +"`; cyclic graph repeating nodes are expanded only once and marked `[Ref]`; deep chain length = `DEEP + 2` without raising `RecursionError` |

## Key Test Scenarios

1. **Normal DAG rendering** (`test_render_structure_list`): A 4-node diamond structure (s1→{s2,s3}→s4) verifies the node label format is correct and the list contains the `[Ref]` marker.
2. **Empty structure** (`test_render_structure_list_no_nodes`): Empty `nodes` should return the placeholder `"+ No stages defined +"`.
3. **Cyclic graph reference marker** (`test_render_structure_list_cycle`): A three-node closed loop (c1→c2→c3→c1) verifies that `c1` appears 2 times (first expansion + `[Ref]` back reference), and the entire output contains `[Ref]`.
4. **Ultra-deep chain does not trigger recursion limit** (`test_render_deep_chain_no_recursion_error`): A 5000-node linear chain verifies the rendered row count is exactly `DEEP + 2` (top border + node rows + bottom border), and the first and last node labels are both correct.

## Test Focus
- **Node Label Format**: `name::func_name (E:execution_mode, W:max_workers)`, with ` [Ref]` appended to referenced nodes.
- **Recursion Safety**: The implementation uses an explicit stack-based iterative DFS, so deep-chain rendering should not trigger `RecursionError`.
- **Empty Input and Boundaries**: Empty `nodes` returns a fixed placeholder text, avoiding empty list rendering.
- **Cyclic Graph Convergence**: Shared subgraph nodes are expanded only once, preventing infinite loops or redundant output.

## How to Run

```bash
# Run all
pytest tests/graph/test_render.py -v

# Run cyclic graph reference marker tests only
pytest tests/graph/test_render.py -k "cycle" -v

# Run deep-chain regression tests only
pytest tests/graph/test_render.py -k "deep" -v
```

## Performance Reference

| Test | Duration |
|------|------|
| `TestUtilRender` | < 0.2s (5000-node pure string construction) |

## Important Details
- `make_node` defaults to `execution_mode="serial"`, `max_workers=2`; callers can override as needed.
- `test_render_structure_list` asserts that `rendered_list[1]` contains the root node label, because the implementation first outputs the top border.
- The expected row count `DEEP + 2` for the deep-chain test consists of: top border + 5000 node rows + bottom border.

## Notes
- This module is the rendering-specific test split/renamed from the early `test_serialize.py`; serialization-related JSON behavior is no longer covered here.
- The related implementation is located at `src/celestialflow/graph/util_render.py`.
