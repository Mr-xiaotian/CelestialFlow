# Graph Serialization Utility Tests (test_serialize.py)

> 📅 Last Updated: 2026/06/11

## Purpose
Verifies graph structure serialization and visualization formatting functionality, ensuring that graph topologies can be correctly converted into JSON structures or readable text lists.

## Core Test Objects
- `build_structure_graph`: Converts an adjacency-list-style graph into a nested dictionary structure.
- `format_structure_list_from_graph`: Converts a nested structure into a formatted, indented string list.
- `make_stage`: Test helper function that constructs a `TaskStage` from a `stage_mode` × `execution_mode` combination.

## Key Test Scenarios
1. **DAG Serialization**: Verifies that a typical layered structure (e.g., s1→{s2,s3}→s4) is correctly parsed, with attributes such as func_name, stage_mode, execution_mode, and max_workers being accurate for each node.
2. **Cyclic Graph Serialization**: Verifies that a cyclic graph (e.g., cs1→cs2→cs3→cs1) does not cause an infinite loop during serialization.
3. **Text Formatting**: Verifies that the generated string list contains expected mode markers (e.g., `(S:serial, E:serial, W:2)`) and reference markers (`[Ref]`).

## Test Focus
- **Reference Markers**: Ensures that in non-tree DAGs or cyclic graphs, nodes that appear more than once display details only on first appearance, with subsequent appearances marked as references.
- **Recursion Termination**: Ensures the serialization algorithm correctly identifies already-visited nodes when handling circular references and terminates recursion promptly.

## How to Run

```bash
# Run all
pytest tests/graph/test_serialize.py -v

# Match specific test names
pytest tests/graph/test_serialize.py -k "dag" -v
pytest tests/graph/test_serialize.py -k "cyclic" -v
pytest tests/graph/test_serialize.py -k "format" -v
```

## Performance Reference

| Test | Duration |
|------|----------|
| `TestUtilSerialize` (DAG/Cyclic/Formatting) | ~0.1s total |

## Important Details
- Uses the `make_stage` helper function to construct test nodes with different `stage_mode` × `execution_mode` combinations.
- Tests cover both the JSON data layer and the final presentation text layer.

## Notes
- The test code is located at `tests/graph/test_serialize.py`, and the corresponding implementation is at `src/celestialflow/graph/util_serialize.py`.
