# Remaining-Time Estimator Tests (test_estimators.py)

> Last Updated: 2026/06/05

## Purpose
Validates the three estimator functions `calc_remaining`, `calc_elapsed`, and `calc_global_remain_equal_pred`, ensuring CelestialFlow can produce stable remaining-time predictions at both stage level and graph level.

## Coverage
- `calc_remaining`: Basic estimation from `processed / pending / elapsed`.
- `calc_elapsed`: Decides whether elapsed time should keep accumulating based on `StageStatus` and the previous snapshot.
- `calc_global_remain_equal_pred`: Propagates load from upstream to downstream on a DAG, covering linear chains, fan-in, fan-out, diamonds, and empty graphs.

## Key Scenarios
- Zero-value edges: `processed=0`, `pending=0`, empty graph.
- State transitions: accumulation strategies for `NOT_STARTED`, `RUNNING`, and `STOPPED`.
- Graph propagation: linear chains, fan-out, fan-in, diamonds, bottleneck nodes, and missing map data.
- Property checks: symmetry, monotonicity, and "must never become negative".

## How to Run

```bash
pytest tests/runtime/test_estimators.py -v
pytest tests/runtime/test_estimators.py -k "calc_remaining or calc_elapsed" -v
pytest tests/runtime/test_estimators.py -k "global_remain" -v
```

