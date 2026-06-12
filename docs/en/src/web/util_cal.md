# util_cal

> 📅 Last Updated: 2026/05/23

Web module calculation utility function.

## cal_interval

```python
def cal_interval(refresh_interval: int) -> float:
    """Converts a millisecond refresh interval to seconds and clamps it within [1.0, 60.0]."""
```

Converts the frontend's millisecond-level refresh interval to seconds, and clamps it within a reasonable range to prevent excessive polling frequency from overloading the server, or overly low polling frequency from causing data delays.

## Usage Examples

### Usage Examples for Calendar/Time Calculation Functions

```python
from celestialflow.web.util_cal import cal_interval

# 5000ms -> 5.0s (standard 5-second refresh)
print(f"5000ms -> {cal_interval(5000)}s")    # 5.0

# 1000ms -> 1.0s (lower bound: 1 second)
print(f"1000ms -> {cal_interval(1000)}s")    # 1.0

# 500ms -> 1.0s (below lower bound, clamped to 1.0)
print(f"500ms  -> {cal_interval(500)}s")     # 1.0

# 120000ms -> 60.0s (exceeds upper bound, clamped to 60.0)
print(f"120000ms -> {cal_interval(120000)}s") # 60.0

# Edge case: exactly at the upper bound
print(f"60000ms -> {cal_interval(60000)}s")   # 60.0

# Typical Web UI refresh interval configurations
refresh_options_ms = [1000, 2000, 5000, 10000, 30000]
print("\nCommon refresh interval conversions:")
for ms in refresh_options_ms:
    seconds = cal_interval(ms)
    print(f"  {ms:>6}ms -> {seconds:.1f}s")
# Output:
#    1000ms -> 1.0s
#    2000ms -> 2.0s
#    5000ms -> 5.0s
#   10000ms -> 10.0s
#   30000ms -> 30.0s
```
