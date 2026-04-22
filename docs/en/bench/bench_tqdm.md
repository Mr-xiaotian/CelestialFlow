# bench_tqdm.py Benchmark Documentation

> 📅 Last updated: 2026/04/22

## Objective

Quantify the performance overhead of `tqdm` progress bars in loops, helping determine whether progress display should be enabled in ultra-large-scale iterations (millions of iterations).

## Test Cases

- **With tqdm**: Each iteration calls `pbar.update(1)`
- **Without tqdm**: Bare loop
- **Data scale**: Default `data_size = 1_000_000`
- **Simulated processing**: `item * 2` (extremely lightweight computation)

## Key Parameters

- `dynamic_ncols=True`: Automatically adapts to terminal width
- `total=0` then dynamically set `pbar.total = len(data)`: Demonstrates deferred total setting

## Potential Issues

1. **TTY detection overhead**: If output is redirected to a file or pipe, `tqdm` may automatically disable display but still execute some refresh logic, causing inconsistency with direct terminal results.
2. **`dynamic_ncols` terminal query**: Each refresh queries the terminal width, which may trigger slow system calls in certain CI environments or Windows PowerShell.
3. **Memory growth in large loops**: The test code fully expands `range(data_size)` into a `list` stored in `data`. When `data_size` increases to 10 million, the list alone occupies approximately 80MB of memory.

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10, data_size=1,000,000, processing logic: `item * 2`

| Mode | Preparation Time | Processing Time | Total Time | Relative to No tqdm |
|------|-------------------|-----------------|------------|---------------------|
| **No tqdm** | 0.0859s | 0.0334s | **0.1194s** | — |
| **With tqdm** | 0.1067s | 0.3259s | **0.4325s** | **3.6x** |

**Key Conclusions**:
- tqdm increases total time by approximately **3.6x** in this test (0.12s -> 0.43s)
- Processing time increases from 0.033s to 0.326s, nearly 10x, indicating that in **extremely lightweight loop bodies**, tqdm's refresh overhead far exceeds actual computation
- When per-iteration computation is substantial (e.g., > 1ms), tqdm's relative overhead quickly drops to negligible levels (< 5%)
- Strategy recommendation: Disable tqdm or increase `miniters` for million-scale lightweight loops; feel free to enable it for long-duration/low-iteration tasks

## How to Run

```bash
python bench/bench_tqdm.py
```

## Dependencies

- `tqdm`
