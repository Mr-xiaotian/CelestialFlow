# RuntimeEstimators

> 📅 Last Updated: 2026/08/19

`runtime/util_estimators.py` provides runtime time-consumption estimation functions.

## Main Functions

- `calc_remaining(processed, pending, elapsed)`: Estimates the remaining time for a node based on averages.
- `calc_elapsed(status, last_elapsed, last_pending, interval)`: Accumulates elapsed time by status.
- `format_avg_time(elapsed, processed)`: Formats the average processing speed (seconds/task or tasks/second).

## Usage Examples

The following examples demonstrate the usage of estimation functions such as `calc_remaining`, `calc_elapsed`, and `format_avg_time`.

### calc_remaining: Estimate Node Remaining Time

```python
from celestialflow.runtime.util_estimators import calc_remaining

# 80 processed, 20 remaining, 40 seconds elapsed
remaining = calc_remaining(
    processed=80,
    pending=20,
    elapsed=40.0,
)
print(f"Estimated remaining time: {remaining:.2f} seconds")  # 10.0 seconds (20/80 * 40)

# Returns 0 when no processed data
remaining_zero = calc_remaining(processed=0, pending=100, elapsed=10.0)
print(f"No historical data: {remaining_zero} seconds")  # 0
```

### calc_elapsed: Accumulate Elapsed Time by Status

```python
from celestialflow.runtime.util_types import StageStatus
from celestialflow.runtime.util_estimators import calc_elapsed

# Node is running, 30 seconds elapsed previously, 5 pending, 2-second collection interval
elapsed = calc_elapsed(
    status=StageStatus.RUNNING,
    last_elapsed=30.0,
    last_pending=5,
    interval=2.0,
)
print(f"Updated elapsed time: {elapsed:.1f} seconds")  # 32.0 (30 + 2)

# Node has stopped, elapsed time no longer increases
elapsed_stopped = calc_elapsed(
    status=StageStatus.STOPPED,
    last_elapsed=50.0,
    last_pending=0,
    interval=2.0,
)
print(f"Stopped node: {elapsed_stopped:.1f} seconds")  # 50.0 (no longer increasing)
```

### format_avg_time: Format Average Processing Speed

```python
from celestialflow.runtime.util_estimators import format_avg_time

# When avg time per task >= 1s, displays as s/it
print(format_avg_time(200.0, 100))  # 2.00s/it

# When avg time per task < 1s, displays as it/s (reciprocal)
print(format_avg_time(12.5, 100))  # 8.00it/s

# No data
print(format_avg_time(0.0, 0))  # N/A
```

## Use Cases

- Driving monitoring dashboard ETA display.
