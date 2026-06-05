# bench_tqdm.py Benchmark Notes

> 📅 Last Updated: 2026/04/22

## Objective

Quantify the runtime overhead of a `tqdm` progress bar inside a loop, helping decide whether progress display should be enabled for very large iteration counts.

## Test Cases

- **With tqdm**: call `pbar.update(1)` on every iteration.
- **Without tqdm**: plain loop.
- **Data size**: default `data_size = 1_000_000`.
- **Simulated work**: `item * 2`, an extremely lightweight computation.

## Key Parameters

- `dynamic_ncols=True`: adapt automatically to terminal width.
- `total=0` followed by `pbar.total = len(data)`: demonstrates delayed total assignment.

## Potential Issues

1. **TTY detection overhead**: if output is redirected to a file or pipe, `tqdm` may disable rendering but still run part of its refresh logic, producing results that differ from a real terminal.
2. **Terminal-width polling**: with `dynamic_ncols`, each refresh queries terminal width, which can be slow in some CI environments or Windows PowerShell.
3. **Memory growth for huge loops**: the benchmark expands `range(data_size)` into a full `list`. At `10,000,000`, the list alone costs roughly 80 MB.

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10, `data_size=1,000,000`, work=`item * 2`

| Mode | Preparation Time | Processing Time | Total Time | Relative to No tqdm |
|------|------------------|-----------------|------------|---------------------|
| **Without tqdm** | 0.0859s | 0.0334s | **0.1194s** | — |
| **With tqdm** | 0.1067s | 0.3259s | **0.4325s** | **3.6x** |

**Key takeaways**:
- In this benchmark, `tqdm` increases total runtime by about **3.6x** (`0.12s -> 0.43s`).
- Processing time jumps from `0.033s` to `0.326s`, almost 10x, which shows that refresh overhead dominates when the loop body is extremely cheap.
- Once each iteration becomes more expensive, such as more than 1 ms of compute, the relative cost of `tqdm` usually drops quickly to a negligible level.
- Strategy suggestion: disable `tqdm` for million-scale lightweight loops or increase `miniters`; keep it enabled for long-running or low-iteration tasks.

## How to Run

```bash
python bench/bench_tqdm.py
```

## Parameter Tuning

### Change the Data Scale

`test_tqdm_performance(data_size)` accepts a `data_size` parameter:

```bash
# Compare different scales
python -c "
from bench.bench_tqdm import test_tqdm_performance
test_tqdm_performance(use_tqdm=False, data_size=100_000)
test_tqdm_performance(use_tqdm=True, data_size=100_000)
"
```

You can also edit `if __name__ == "__main__"` directly:

```python
if __name__ == "__main__":
    # Small-scale quick verification
    test_tqdm_performance(use_tqdm=False, data_size=10_000)
    test_tqdm_performance(use_tqdm=True, data_size=10_000)

    # Large-scale test to observe how tqdm overhead changes
    # test_tqdm_performance(use_tqdm=False, data_size=10_000_000)
    # test_tqdm_performance(use_tqdm=True, data_size=10_000_000)
```

Run again after modification:

```bash
python bench/bench_tqdm.py
```

## Dependencies

- `tqdm`
