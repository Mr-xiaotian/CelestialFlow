# Specific Graph Structure Tests (test_structure.py)

> 📅 Last Updated: 2026/05/23

## Purpose
Verifies the dedicated analysis capabilities of two predefined cyclic graph structures, `TaskLoop` and `TaskWheel`, ensuring they behave as expected in non-DAG scenarios.

## Core Test Objects
- `TaskLoop`: A simple closed-loop task chain.
- `TaskWheel`: A center-diffusing wheel structure with a ring.

## Key Test Flow
1. **TaskLoop Analysis**:
   - Verifies `isDAG` is correctly identified as `False`.
   - Verifies that all nodes within the cycle are assigned to the same logical level.
   - Verifies that source node derivation selects a representative from the cycle as the injection point.
2. **TaskWheel Analysis**:
   - Verifies that the center node (Center) is at Level 0 while the ring node (Ring) is at Level 1.
   - Verifies that `get_source_stages` returns only the Center node, ensuring tasks are injected from the center.

## Test Focus
- **Non-DAG Recognition**: Ensures cyclic structures are not incorrectly treated as DAGs.
- **Level Consistency**: Verifies that logical level assignments still match physical intuition in the presence of circular dependencies.
- **Source Node Specialization**: Source node lookup logic optimized for specific structures.

## How to Run

```bash
# Run all
pytest tests/graph/test_structure.py -v

# TaskLoop tests only
pytest tests/graph/test_structure.py::TestTaskLoop -v

# TaskWheel tests only
pytest tests/graph/test_structure.py::TestTaskWheel -v
```

## Performance Reference

| Test | Duration |
|------|----------|
| `TestTaskLoop` | ~1s (includes graph start and termination) |
| `TestTaskWheel` | ~1s |

## Important Details
- Uses specialized methods such as `start_loop` and `start_wheel` to start tests, with `put_termination_signal=True`.
- The test focus is on "analysis results" (analysis dict) rather than "execution results."

## Notes
- This test focuses on the specialized behavior of `TaskGraph` subclasses.
- The related implementation is located at `src/celestialflow/graph/core_structure.py`.
