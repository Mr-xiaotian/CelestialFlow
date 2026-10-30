# tests/persist/test_render.py

> 📅 Last Updated: 2026/10/09

## Purpose

Validates the structure rendering logic of `celestialflow.persist.util_render.render_structure_list`: whether it can render the nodes and adjacency list into a tree-shaped bordered text list, correctly handle empty structures and cyclic graphs, and not trigger Python's recursion limit on deep-chain graphs.

> After the refactor, `util_render` was migrated from `src/celestialflow/graph` to `src/celestialflow/persist`; the test mirror accordingly lives in the `tests/persist` directory.

## Core Test Objects

| Class / Object | Source | Description |
|-----------|------|------|
| `render_structure_list(nodes, edges, source_nodes)` | `celestialflow.persist.util_render` | Generates a bordered tree-shaped text list from the node list, adjacency list, and source nodes; returns a list of strings (with border rows at the beginning and end) |
| `DEEP` (=5000) | Constant in this file | Exceeds Python's default recursion limit (about 1000), used to regression-test the explicit stack-based iterative rendering logic |

## Test Coverage Matrix

### `TestUtilRender`

| Case | Coverage Target |
|------|---------|
| `test_render_structure_list` | A normal DAG (`s1→s2/s3→s4`) renders a tree-shaped list containing `s1`, and includes a cyclic-reference row marked with `[Ref]` |
| `test_render_structure_list_no_nodes` | Empty structure returns the placeholder `["+ No nodes defined +"]` |
| `test_render_structure_list_cycle` | A cyclic graph (`c1→c2→c3→c1`) expands only once, marking repeated nodes as `[Ref]`; `c1` appears exactly 2 times (first expansion + back reference) |
| `test_render_deep_chain_no_recursion_error` | A 5000-node deep-chain graph does not trigger the recursion limit; the rendered row count is `DEEP + 2` (border + node rows + border) |

## Key Test Scenarios

### `test_render_structure_list_cycle`

- Constructs the cycle `{"c1": ["c2"], "c2": ["c3"], "c3": ["c1"]}` and renders with `["c1"]` as the root.
- Asserts that in the merged text `c1` appears exactly 2 times (first expansion + `[Ref]` back reference), and that the output contains `[Ref]`.

### `test_render_deep_chain_no_recursion_error`

- Constructs a 5000-node linear chain (`n0 → n1 → ... → n4999`).
- Asserts that `render_structure_list` returns `DEEP + 2` rows (top and bottom borders + 5000 node rows), with the first row being `n0` and the last node `n4999`.
- This case verifies that the rendering uses an **explicit stack-based iterative DFS** rather than recursion, thus avoiding Python's default recursion limit.

## How to Run

```bash
# Run all
pytest tests/persist/test_render.py -v

# Match by keyword
pytest tests/persist/test_render.py -k "cycle" -v
pytest tests/persist/test_render.py -k "deep" -v
```

## Notes

- The deep-chain case (`DEEP=5000`) relies on `render_structure_list`'s internal implementation having been changed to explicit stack iteration; if it reverts to a recursive implementation, it triggers a `RecursionError`.
- The related implementation is in `src/celestialflow/persist/util_render.py`.