# RuntimeEstimators

> 📅 Last Updated: 2026/04/22

`runtime/util_estimators.py` provides runtime duration estimation functions.

## Main Functions

- `calc_remaining(processed, pending, elapsed)`: Estimates the remaining time for a node.
- `calc_elapsed(status, last_elapsed, last_pending, interval)`: Accumulates elapsed time based on status.
- `calc_global_remain_equal_pred(...)`: Estimates global remaining time based on DAG and observed metrics.

## Use Cases

- Drives ETA display on the monitoring dashboard.
- Helps identify potential congestion nodes.
