# bench_utils.py Benchmark Documentation

> 📅 Last Updated: 2026/04/22

## Objective

Provide a unified statistical output tool `summarize()` for the benchmarks under the `bench/` directory, standardizing the presentation format for duration data.

## Functionality

```python
def summarize(name: str, durations: list[float], count: int) -> None
```

Output includes:
- Per-round duration (raw values)
- Average duration (mean)
- Standard deviation (pstdev)
- Throughput (`count / mean_s`, items/s)

## Key Implementation

- Uses `statistics.pstdev` (population standard deviation), suitable for small samples (`REPEAT = 3`)
- Throughput is calculated based on the mean; if rounds vary significantly, this value is for reference only

## Potential Issues

1. **Small sample size**: Most benchmarks use `REPEAT = 3`; `pstdev` is sensitive to outliers. If one round spikes due to system jitter (e.g., background processes, garbage collection), the standard deviation will inflate significantly.
2. **Zero-value protection**: `throughput = count / mean_s if mean_s > 0 else 0.0`; in extremely fast scenarios (where `mean_s` approaches floating-point precision limits), this may produce very large values.

## How to Run

This file cannot be run directly; it is imported as a shared module:
```python
from bench_utils import summarize
```

## Related Files

- `bench/bench_ipc_queue.py`
- `bench/bench_mpqueue_vs_shared_memory.py`
