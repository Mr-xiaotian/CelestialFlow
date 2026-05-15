# bench_futures_memory.py Benchmark Documentation

> 📅 Last Updated: 2026/05/08

## Objective

Purely compare memory usage between two strategies for futures lists in thread pool scenarios: "no cleanup" vs. "periodic cleanup". Independent of the CelestialFlow framework, isolating measurement of futures' own memory overhead.

## Background

`ThreadPoolExecutor` returns a `Future` object after submitting a task. If all futures are appended to a list and left for final collection, the list grows indefinitely with the number of tasks. Periodically filtering out completed futures can limit the list size to `max_workers * 2`.

## Test Cases

### `dispatch_no_cleanup`
- All futures appended to list without any cleanup
- Final batch call to `future.result()`

### `dispatch_with_cleanup`
- After each append, check list length; filter out completed futures when it reaches `max_workers * 2`
- Final call to `result()` on remaining futures

## Key Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `task_count` | 10K / 100K / 500K | Number of tasks |
| `max_workers` | 20 | Thread pool size |
| Task function | `noop(x)` | Returns directly, no computation overhead |

## How to Run

```bash
python bench/bench_futures_memory.py
```

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10, max_workers=20

| Task Count | Mode | Duration | Peak Memory | Post-completion Memory |
|------------|------|----------|-------------|----------------------|
| 10,000 | no_cleanup | 0.351s | 17.94 MB | 0.20 MB |
| 10,000 | with_cleanup | 1.589s | 0.45 MB | 0.10 MB |
| 100,000 | no_cleanup | 5.507s | 177.01 MB | 0.18 MB |
| 100,000 | with_cleanup | 15.807s | 0.48 MB | 0.09 MB |
| 500,000 | no_cleanup | 30.232s | 883.51 MB | 0.16 MB |
| 500,000 | with_cleanup | 79.774s | 0.46 MB | 0.09 MB |

**Key Conclusions**:
- Without cleanup, peak memory grows linearly with task count: 10K -> 18 MB, 100K -> 177 MB, 500K -> 884 MB
- With periodic cleanup, peak memory stays constant at ~0.5 MB regardless of task count
- At 500K tasks, memory savings are approximately **1800x**
- Cleanup operations incur additional time overhead (list filtering), but in real framework usage where tasks have computation overhead, this cost is negligible

## Dependencies

- `tracemalloc` (standard library)
- `concurrent.futures` (standard library)
