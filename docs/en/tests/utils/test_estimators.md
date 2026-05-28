# Time Estimation Utility Tests (test_estimators.py)

> 📅 Last Updated: 2026/05/28

## Purpose

Validates the global task remaining time estimation functions in `celestialflow.utils.util_estimators`: `calc_remaining`, `calc_elapsed`, and `calc_global_remain_equal_pred`.

## Core Test Targets

- `calc_remaining`: Estimates the remaining time for a single Stage based on `(pending, processed, elapsed)`.
- `calc_elapsed`: Computes the actual elapsed time based on `time_start`, `time_end`, and `status`.
- `calc_global_remain_equal_pred`: Traverses all nodes in the graph and estimates each node's remaining time using an **equal-proportion distribution** based on upstream processed and downstream pending amounts.

## Key Test Scenarios

### `TestCalcRemaining`
- Normal estimation: `(pending=5, processed=5, elapsed=10)` → remaining 10s
- Edge cases: pending=0, processed=0, all three zero → all return 0
- Float input support

### `TestCalcElapsed`
- RUNNING status with pending → returns `current_time - time_start`
- RUNNING status without pending → returns `time_end - time_start`
- STOPPED status → returns `time_end - time_start`
- NOT_STARTED → returns 0
- Sequential calls simulate time progression

### `TestCalcGlobalRemainEqualPred`
- Single node with no predecessors / all-zero pending
- Linear chain (three nodes A→B→C): `total_processed` is reasonably distributed
- Fan-out (one-to-many), fan-in (many-to-one), diamond structure (A→[B,C]→D)
- Bottleneck node (large pending value)
- Result type is `dict[str, float]`, no negative values
- Upstream has no data but downstream has pending (uses diff value)
- Empty graph handling

### `TestPropertyBased` — Property-Based Tests
- Symmetric linear chains produce identical estimates
- Monotonicity: larger pending → larger estimate
- Monotonicity: larger processed → smaller estimate

## How to Run

```bash
# Run all
pytest tests/utils/test_estimators.py -v

# calc_remaining tests only
pytest tests/utils/test_estimators.py -k "Remaining" -v

# calc_elapsed tests only
pytest tests/utils/test_estimators.py -k "Elapsed" -v

# Global estimation tests only
pytest tests/utils/test_estimators.py -k "Global" -v

# Property-based tests only
pytest tests/utils/test_estimators.py -k "Property" -v
```

## Performance Reference

| Test Class | Duration |
|------------|----------|
| `TestCalcRemaining` | ~0.01s |
| `TestCalcElapsed` | ~0.02s |
| `TestCalcGlobalRemainEqualPred` | ~0.1s |
| `TestPropertyBased` | ~0.1s |

## Key Details

- Global estimation uses an **equal-proportion distribution assumption**: the remaining time for downstream nodes is allocated proportionally based on the processed amounts of upstream nodes.
- The helper function `_make_linear_chain(n)` constructs an n-node linear DAG for quickly building test topologies.
- Property-based tests validate the mathematical monotonicity of the estimation functions without relying on specific values.

## Notes

- These estimation functions are used for progress estimation and ETA display in the Dashboard; their accuracy affects the user experience.
- Related implementation is in `src/celestialflow/utils/util_estimators.py`.
