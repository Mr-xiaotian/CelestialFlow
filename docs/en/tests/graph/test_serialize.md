# Graph Serialization Utility Tests (test_serialize.py)

> Last Updated: 2026/05/23

## Purpose
Validates graph serialization and visualization formatting, ensuring graph topologies can be converted into tree-like JSON structures or readable text lists.

## Key Test Objects
- `build_structure_graph`: Converts an adjacency-list graph into a nested tree dictionary.
- `format_structure_list_from_graph`: Converts the nested structure into an indented list of formatted strings.

## Key Test Flow
1. **DAG serialization**: Verifies that a typical layered structure such as A -> {B, C} -> D is parsed correctly, and checks that the `is_ref` flag is set when a node is referenced more than once.
2. **Cyclic graph serialization**: Verifies that a cyclic graph such as A -> B -> C -> A does not recurse forever and that the cycle entry is marked as `is_ref: True`.
3. **Text formatting**: Verifies that the generated string list contains the expected indentation, function names, mode markers such as `(S:serial, E:serial)`, and reference markers such as `[Ref]`.

## Test Focus
- **Reference markers (`is_ref`)**: Ensures that repeated nodes in non-tree DAGs or cyclic graphs only show details on first appearance and are marked as references on later appearances.
- **Recursion termination**: Ensures that the serializer recognizes visited nodes and stops recursion correctly when handling cycles.

## How to Run

```bash
# Run all tests
pytest tests/graph/test_serialize.py -v

# Match specific test names
pytest tests/graph/test_serialize.py -k "dag" -v
pytest tests/graph/test_serialize.py -k "cycle" -v
pytest tests/graph/test_serialize.py -k "format" -v
```

## Performance Reference

| Test | Duration |
|------|----------|
| `TestUtilSerialize` (DAG / cycle / formatting) | ~0.1s overall |

## Important Details
- The tests use the helper `create_mock_stage_runtime` to construct a runtime environment with mock queues and logging components.
- Coverage includes both the JSON data layer and the final display-text layer.

## Notes
- The test code lives in `tests/graph/test_serialize.py`, and the implementation lives in `src/celestialflow/graph/util_serialize.py`.

