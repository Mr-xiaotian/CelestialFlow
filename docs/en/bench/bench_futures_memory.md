# bench_futures_memory.py Benchmark Documentation

> 📅 Last updated: 2026/05/08

## Objective

Purely compare the memory usage difference between "no cleanup" and "periodic cleanup" strategies for futures lists in a thread pool scenario. Independent of the CelestialFlow framework, isolating the memory overhead of futures themselves.

## Background

`ThreadPoolExecutor` returns a `Future` object after submitting a task. If all futures are appended to a list and only collected at the end, the list grows unboundedly with task count. Periodically filtering out completed futures limits the list size to `max_workers * 2`.

## Test Cases

### `dispatch_no_cleanup`
- All futures appended to list, no cleanup performed
- Final batch call to `future.result()`

### `dispatch_with_cleanup`
- After each append, check list length; when it reaches `max_workers * 2`, filter out completed futures
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

| Tasks | Mode | Elapsed | Peak Memory | Post-run Memory |
|-------|------|---------|-------------|-----------------|
| 10,000 | no_cleanup | 0.351s | 17.94 MB | 0.20 MB |
| 10,000 | with_cleanup | 1.589s | 0.45 MB | 0.10 MB |
| 100,000 | no_cleanup | 5.507s | 177.01 MB | 0.18 MB |
| 100,000 | with_cleanup | 15.807s | 0.48 MB | 0.09 MB |
| 500,000 | no_cleanup | 30.232s | 883.51 MB | 0.16 MB |
| 500,000 | with_cleanup | 79.774s | 0.46 MB | 0.09 MB |

**Key Conclusions**:
- Without cleanup, peak memory grows linearly with task count: 10K → 18 MB, 100K → 177 MB, 500K → 884 MB
- With periodic cleanup, peak memory stays constant at ~0.5 MB, independent of task count
- At 500K tasks, memory savings of approximately **1800x**
- Cleanup has additional time overhead (list filtering), but in real frameworks where tasks have computation overhead, this cost is negligible

## Dependencies

- `tracemalloc` (standard library)
- `concurrent.futures` (standard library)
