# util_cal

> 📅 Last Updated: 2026/04/22

Calculation utility functions for the Web module.

## cal_interval

```python
def cal_interval(refresh_interval: int) -> float:
    """Convert a millisecond refresh interval to seconds, clamped to the [1, 60] range."""
```

Converts the millisecond-level refresh interval from the frontend to seconds and clamps it to a reasonable range, preventing overly frequent or overly sparse polling.
