# bench_utils.py Benchmark Notes

> 📅 Last Updated: 2026/04/22

## Objective

Provides a unified statistical output utility `summarize()` for all benchmarks under the `bench/` directory, standardizing the presentation format of timing data.

## Function

```python
def summarize(name: str, durations: list[float], count: int) -> None
```

Output contents:
- Per-round time (raw values)
- Average time (mean)
- Standard deviation (pstdev)
- Throughput (`count / mean_s`, items/s)

## Key Implementation

- Uses `statistics.pstdev` (population standard deviation), suitable for small samples (`REPEAT = 3`)
- Throughput calculation is based on the mean; if individual rounds vary significantly, this value is for reference only

## Potential Issues

1. **Small sample size**: Most benchmarks use `REPEAT = 3`; `pstdev` is sensitive to outliers. If one round has a sudden time spike due to system jitter (e.g., background processes, garbage collection), the standard deviation will inflate significantly.
2. **Zero-value guard**: `throughput = count / mean_s if mean_s > 0 else 0.0`; in extremely fast scenarios (`mean_s` near floating-point precision limits) may produce extremely large values.

## How to Run

This file cannot be run directly; it is imported as a shared module:
```python
from bench_utils import summarize
```

## Related Files

- `bench/bench_ipc_queue.py`
- `bench/bench_mpqueue_vs_shared_memory.py`
