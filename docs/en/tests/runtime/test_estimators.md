# Remaining Time Estimation Tests (test_estimators.py)

> 📅 Last Updated: 2026/06/22

## Purpose
Verifies the three estimation functions `calc_remaining`, `calc_elapsed`, and `calc_global_pending`, ensuring CelestialFlow can produce stable remaining-time predictions at both the node level and the graph level.

## Coverage Points
- `calc_remaining`: Basic estimation based on `processed / pending / elapsed`.
- `calc_elapsed`: Determines whether to continue accumulating elapsed time based on `StageStatus` and the previous round's snapshot.
- `calc_global_pending`: Propagates load from upstream to downstream on a DAG, covering linear chains, fan-in, fan-out, diamond, empty graphs, and other topologies.

## Key Scenarios
- Zero-value boundaries: `processed=0`, `pending=0`, empty graph.
- State transitions: Accumulation strategy for `NOT_STARTED`, `RUNNING`, and `STOPPED`.
- Graph structure propagation: Linear chain, fan-out, fan-in, diamond, bottleneck node, missing map data.
- Property verification: Symmetry, monotonicity, and "should never produce negative values."

## Test Coverage Matrix

| Test Class | Case Count | Coverage Goals |
|------------|------------|----------------|
| `TestCalcRemaining` | 7 | Basic ratio calculation and zero-value boundaries |
| `TestCalcElapsed` | 7 | State-machine-based elapsed time accumulation strategy |
| `TestCalcGlobalPending` | 16 | DAG propagation estimation: linear chain, fan-out, fan-in, diamond, bottleneck, empty graph, missing map data, etc. |
| `TestPropertyBased` | 3 | Property verification: symmetry, monotonicity, etc. |

## How to Run

```bash
pytest tests/runtime/test_estimators.py -v
pytest tests/runtime/test_estimators.py -k "calc_remaining or calc_elapsed" -v
pytest tests/runtime/test_estimators.py -k "global_pending" -v
```
