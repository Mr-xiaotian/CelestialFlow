# bench_tqdm.py Benchmark Documentation

> 📅 Last Updated: 2026/04/22

## Objective

Quantify the performance overhead of `tqdm` progress bar in loops, helping determine whether progress display should be enabled in ultra-large-scale iterations (millions).

## Test Cases

- **With tqdm**: Each iteration calls `pbar.update(1)`
- **Without tqdm**: Bare loop
- **Data scale**: Default `data_size = 1_000_000`
- **Simulated processing**: `item * 2` (extremely lightweight operation)

## Key Parameters

- `dynamic_ncols=True`: Auto-adapt to terminal width
- `total=0` then dynamically set `pbar.total = len(data)`: Demonstrates deferred total setting usage

## Potential Issues

1. **TTY detection overhead**: If output is redirected to a file or pipe, `tqdm` may auto-disable display but still execute partial refresh logic, causing results to differ from direct terminal execution.
2. **`dynamic_ncols` terminal query**: Each refresh queries terminal width, which may trigger slow system calls in certain CI environments or Windows PowerShell.
3. **Memory growth in large loops**: The test code fully expands `range(data_size)` into a `list` stored in `data`; when `data_size` is increased to 10 million, the list alone occupies ~80MB of memory.

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10, data_size=1,000,000, processing logic: `item * 2`

| Mode | Preparation Time | Processing Time | Total Time | Relative to no tqdm |
|------|-------------------|-----------------|------------|---------------------|
| **Without tqdm** | 0.0859s | 0.0334s | **0.1194s** | -- |
| **With tqdm** | 0.1067s | 0.3259s | **0.4325s** | **3.6x** |

**Key Conclusions**:
- tqdm increases total duration by approximately **3.6x** in this test (0.12s -> 0.43s)
- Processing time increases from 0.033s to 0.326s, nearly 10x, showing that in **extremely lightweight loop bodies**, tqdm's refresh overhead far exceeds actual computation
- When per-iteration computation is substantial (e.g., > 1ms), tqdm's relative overhead drops rapidly to negligible levels (< 5%)
- Strategy recommendation: Disable tqdm or increase `miniters` for million-scale lightweight loops; feel free to enable it for long-duration/low-count tasks

## How to Run

```bash
python bench/bench_tqdm.py
```

## Dependencies

- `tqdm`
