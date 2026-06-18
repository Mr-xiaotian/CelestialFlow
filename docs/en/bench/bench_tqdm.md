# bench_tqdm.py Benchmark Guide

> 📅 Last Updated: 2026/06/16

## Objective

Quantify the performance overhead of the `tqdm` progress bar in loops, helping determine whether to enable progress display for ultra-large-scale iterations (millions+).

## Test Content

- **With tqdm**: Each iteration calls `pbar.update(1)`
- **Without tqdm**: Bare loop
- **Data scale**: Function signature defaults to `data_size = 10_000_000`, but the actual call in `__main__` uses `1_000_000`
- **Simulated processing**: `item * 2` (extremely lightweight operation)

## Key Parameters

- `dynamic_ncols=True`: auto-adapt to terminal width
- After `total=0`, dynamically set `pbar.total = len(data)`: demonstrates deferred total setting

## Potential Issues

1. **TTY detection overhead**: If output is redirected to a file or pipe, `tqdm` may auto-disable display but still execute some refresh logic, leading to inconsistent results versus direct terminal execution.
2. **`dynamic_ncols` terminal query**: Each refresh queries terminal width, which may trigger slow system calls in certain CI environments or Windows PowerShell.
3. **Memory growth in large loops**: The test code fully expands `range(data_size)` into a `list` stored in `data`; when `data_size` is increased to 10 million, the list alone occupies approximately 80MB of memory.

## Benchmark Results (Measured)

### Historical Results - Windows lightweight loop (date not recorded)

> Environment: Windows, Python 3.10, data_size=1,000,000, processing logic is `item * 2`

| Mode | Prep Time | Processing Time | Total Time | Relative to Without tqdm |
|------|----------|----------|--------|-------------|
| **Without tqdm** | 0.0859s | 0.0334s | **0.1194s** | — |
| **With tqdm** | 0.1067s | 0.3259s | **0.4325s** | **3.6x** |

**Key Takeaways**:
- tqdm increased total time by approximately **3.6x** in this test (0.12s → 0.43s)
- Processing time increased from 0.033s to 0.326s, nearly 10x, indicating that in **extremely lightweight loop bodies**, tqdm's refresh overhead far exceeds actual computation
- When per-iteration computation is larger (e.g., > 1ms), tqdm's relative overhead quickly drops to negligible (< 5%)
- Strategy recommendation: disable tqdm or increase `miniters` for million-scale lightweight loops; safely enable for long-duration / low-count tasks

### 2026/06/16 - Local retest

> Environment: Windows, `data_size=1,000,000`, processing logic is `item * 2`

| Mode | Prep Time | Processing Time | Total Time | Relative to Without tqdm |
|------|----------|----------|--------|-------------|
| **Without tqdm** | 0.0436s | 0.0207s | **0.0644s** | — |
| **With tqdm** | 0.0679s | 0.1933s | **0.2611s** | **4.1x** |

**Supplementary conclusions for this round**:
- On the current machine, `tqdm` increases total time by approximately **4.1x**, still significantly higher than the no-progress-bar version
- The processing phase increases from `0.0207s` to `0.1933s`, confirming that in lightweight loops the main cost still comes from refresh and terminal output
- Compared with historical results, absolute times have decreased overall, but the conclusion that "tqdm noticeably amplifies overhead on light tasks" remains unchanged

## How to Run

```bash
python bench/bench_tqdm.py
```

## Parameter Tuning

### Adjusting Data Scale

`test_tqdm_performance(data_size)` accepts a `data_size` parameter:

```bash
# Run comparison at different scales
python -c "
from bench.bench_tqdm import test_tqdm_performance
test_tqdm_performance(use_tqdm=False, data_size=100_000)
test_tqdm_performance(use_tqdm=True, data_size=100_000)
"
```

Can also be modified directly in `if __name__ == "__main__"`:

```python
if __name__ == "__main__":
    # Small scale test (quick validation)
    test_tqdm_performance(use_tqdm=False, data_size=10_000)
    test_tqdm_performance(use_tqdm=True, data_size=10_000)

    # Large scale test (observe tqdm overhead ratio change)
    # test_tqdm_performance(use_tqdm=False, data_size=10_000_000)
    # test_tqdm_performance(use_tqdm=True, data_size=10_000_000)
```

Run after modification:

```bash
python bench/bench_tqdm.py
```

## Dependencies

- `tqdm`
