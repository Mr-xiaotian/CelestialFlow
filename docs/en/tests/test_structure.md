# test_structure.py Test Documentation

> 📅 Last Updated: 2026/05/15

## Test Objective

Validates the graph analysis capabilities of two cyclic graph structures, `TaskLoop` and `TaskWheel`, including:
- DAG detection (cyclic graphs should return `isDAG=False`)
- Level computation (cycle nodes share the same level, center node has its own level)
- Source node inference (`get_source_stages`)

## Test Scope

| Test Class | Test Count | Coverage |
|------------|-----------|----------|
| `TestTaskLoop` | 2 | Loop structure analysis, loop structure source inference |
| `TestTaskWheel` | 2 | Wheel structure analysis (center + ring levels), wheel structure source inference |

### Key Test Case Details

#### `test_loop_analysis`
- **Objective**: Validate graph analysis results for `TaskLoop` (s1 -> s2 -> s3 -> s1).
- **Assertions**: `isDAG` is `False`; all nodes are at the same level.

#### `test_loop_source_stages`
- **Objective**: Validate that `get_source_stages()` returns a representative node from within the loop.
- **Assertions**: Returns 1 source; tag belongs to a loop node.

#### `test_wheel_analysis`
- **Objective**: Validate the level structure of `TaskWheel` (center -> {r1, r2, r3}, r1 -> r2 -> r3 -> r1).
- **Assertions**: `isDAG` is `False`; center is at level 0, ring nodes are at level 1.

#### `test_wheel_source_stages`
- **Objective**: Validate that `get_source_stages()` for a wheel structure returns only the center node.
- **Assertions**: Returns 1 source; tag equals the center's tag.

## Dependencies

| Dependency | Description |
|------------|-------------|
| `celestialflow` | `TaskLoop`, `TaskWheel`, `TaskStage` |

## How to Run

```bash
pytest tests/test_structure.py -v
```

## Performance Reference

| Test | Duration (Windows / i5) |
|------|------------------------|
| `TestTaskLoop` | ~2s |
| `TestTaskWheel` | ~2s |

## Related Files

- `src/celestialflow/graph/core_structure.py`: `TaskLoop`, `TaskWheel` implementation
- `src/celestialflow/graph/util_analysis.py`: Graph analysis utility functions
- `tests/test_graph.py`: `TaskGraph` and other structure subclass tests
