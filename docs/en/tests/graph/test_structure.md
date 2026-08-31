# Specific Graph Structure Tests (test_structure.py)

> 📅 Last Updated: 2026/08/26

## Purpose
Verifies the dedicated analysis capabilities of two predefined cyclic graph structures, `TaskLoop` and `TaskWheel`, as well as the input validation for various predefined graph structures (`TaskChain`, `TaskCross`, `TaskGrid`, `TaskLoop`, `TaskWheel`, `TaskComplete`), ensuring that empty/illegal inputs do not cause silent construction or crashes.

## Core Test Objects
- `TaskLoop`: A simple closed-loop task chain.
- `TaskWheel`: A center-diffusing wheel structure with a ring.
- `TaskChain`, `TaskCross`, `TaskGrid`, `TaskComplete`: Input validation for predefined graph structures with empty/illegal inputs.

## Test Coverage Matrix

| Test Class | Case Count | Coverage Target |
|--------|--------|---------|
| `TestTaskLoop` | 2 | isDAG identified as False, cycle nodes share the same level, source node derivation returns a representative |
| `TestTaskWheel` | 2 | Center at level 0, Ring at level 1, source node returns only Center |
| `TestStructureValidation` | 10 | Empty stages / empty layers / empty grid / empty first row / mismatched row length / single-node Complete / empty input validation for each structure |
| **Total** | **14** | |

## Key Test Flows

### TaskLoop Analysis
- Verifies `isDAG` is correctly identified as `False`.
- Verifies that all nodes within the cycle are assigned to the same logical level.
- Verifies that source node derivation selects a representative from the cycle as the injection point.

### TaskWheel Analysis
- Verifies that the center node (Center) is at Level 0 while the ring node (Ring) is at Level 1.
- Verifies that `get_source_names()` only returns the Center node, ensuring tasks are injected from the center.

### Structure Input Validation (`TestStructureValidation`)
Covers empty/illegal input boundaries for all 6 predefined graph structures:

| Case | Verification Point |
|------|--------|
| `test_chain_empty_stages_raises` | `TaskChain` with empty stages raises `InvalidStructureError` |
| `test_cross_empty_layers_raises` | `TaskCross` with empty layers raises `InvalidStructureError` |
| `test_cross_empty_layer_raises` | `TaskCross` containing an empty layer raises `InvalidStructureError` |
| `test_grid_empty_raises` | `TaskGrid` with empty grid raises `InvalidStructureError` |
| `test_grid_empty_row_raises` | `TaskGrid` with empty first row raises `InvalidStructureError` |
| `test_grid_ragged_rows_raises` | `TaskGrid` with mismatched row length raises `InvalidStructureError` |
| `test_loop_empty_stages_raises` | `TaskLoop` with empty stages raises `InvalidStructureError` |
| `test_wheel_empty_ring_raises` | `TaskWheel` with empty ring raises `InvalidStructureError` |
| `test_complete_single_node_raises` | `TaskComplete` with a single node raises `InvalidStructureError` |
| `test_complete_empty_stages_raises` | `TaskComplete` with empty stages raises `InvalidStructureError` |

## Test Focus
- **Non-DAG Recognition**: Ensures cyclic structures are not incorrectly treated as DAGs.
- **Level Consistency**: Verifies that logical level assignments still match physical intuition in the presence of circular dependencies.
- **Source Node Specialization**: Source node lookup logic optimized for specific structures.
- **Boundary Validation**: Ensures that all predefined graph structures strictly reject empty/illegal inputs, rather than silently constructing an empty graph.

## How to Run

```bash
# Run all
pytest tests/graph/test_structure.py -v

# TaskLoop tests only
pytest tests/graph/test_structure.py::TestTaskLoop -v

# TaskWheel tests only
pytest tests/graph/test_structure.py::TestTaskWheel -v

# Input validation tests only
pytest tests/graph/test_structure.py::TestStructureValidation -v
```

## Performance Reference

| Test | Duration |
|------|------|
| `TestTaskLoop` | ~1s (includes graph start and termination) |
| `TestTaskWheel` | ~1s |
| `TestStructureValidation` | < 0.1s (pure construction validation) |

## Important Details
- `TaskLoop` is started via `run()` and injects tasks (`run` defaults to `if_put_signal=True`, automatically emitting a termination signal for the source node to ensure test exit).
- `TaskWheel` does not execute tasks: after configuring via `set_graph_mode()` and `set_stage_execution_mode()`, it directly calls `get_graph_analysis()` / `get_source_names()` for static analysis.
- The test focus is on "analysis results" (analysis dict) rather than "execution results."
- The input validation tests are pure construction operations and do not involve graph startup.

## Notes
- This test focuses on the specialized behavior of `TaskGraph` subclasses.
- The related implementation is located at `src/celestialflow/graph/core_structure.py`.
