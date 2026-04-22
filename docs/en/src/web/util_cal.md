# util_cal

Calculation utility functions for the Web module.

## cal_interval

```python
def cal_interval(refresh_interval: int) -> float:
    """Converts a millisecond refresh interval to seconds, clamped to the [1, 60] range."""
```

Converts the millisecond-level refresh interval passed from the frontend to seconds and clamps it to a reasonable range, preventing overly frequent or overly sparse polling.
