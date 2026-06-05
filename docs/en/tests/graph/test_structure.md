# Specific Graph Structure Tests (test_structure.py)

> Last Updated: 2026/05/23

## Purpose
Validates the dedicated analysis behavior of the two predefined cyclic graph structures `TaskLoop` and `TaskWheel`, ensuring they behave as expected in non-DAG scenarios.

## Key Test Objects
- `TaskLoop`: A simple closed-loop task chain.
- `TaskWheel`: A wheel structure with a center, outward fan-out, and an outer ring.

## Key Test Flow
1. **TaskLoop analysis**:
   - Verifies that `isDAG` is correctly identified as `False`.
   - Verifies that all nodes inside the loop are assigned to the same logical level.
   - Verifies that source-stage derivation chooses one representative point from the loop as the injection point.
2. **TaskWheel analysis**:
   - Verifies that the center node is at level 0 and the outer ring nodes are at level 1.
   - Verifies that `get_source_stages` returns only the center node so tasks are injected from the center.

## Test Focus
- **Non-DAG detection**: Ensures cyclic structures are not mistakenly treated as DAGs.
- **Level consistency**: Verifies that logical levels still match physical intuition even when cyclic dependencies exist.
- **Source-node specialization**: Validates the source-node lookup logic optimized for these specific structures.

## How to Run

```bash
# Run all tests
pytest tests/graph/test_structure.py -v

# Run TaskLoop tests only
pytest tests/graph/test_structure.py::TestTaskLoop -v

# Run TaskWheel tests only
pytest tests/graph/test_structure.py::TestTaskWheel -v
```

## Performance Reference

| Test | Duration |
|------|----------|
| `TestTaskLoop` | ~1s (includes graph startup and termination) |
| `TestTaskWheel` | ~1s |

## Important Details
- The tests use specialized startup helpers such as `start_loop` and `start_wheel`, together with `put_termination_signal=True`.
- The focus is on the analysis results, meaning the analysis dict, rather than execution results.

## Notes
- These tests focus on specialized behavior in `TaskGraph` subclasses.
- Related implementation: `src/celestialflow/graph/core_structure.py`.

