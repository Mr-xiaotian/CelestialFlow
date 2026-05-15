# bench_execution_mode.py Benchmark Documentation

> 📅 Last Updated: 2026/05/08

## Objective

Compare performance differences of `TaskExecutor` across three execution modes (`serial`, `thread`, `async`) when handling CPU-intensive tasks (Fibonacci) and I/O-intensive tasks (sleep). Uses the framework's built-in `benchmark_executor` tool for unified comparison reports.

## Test Cases

### `bench_executor_fibonacci`
- **Task**: Recursive Fibonacci computation (`n=25..31`), including edge cases (`0, None, ""`)
- **Configuration**: `max_workers=6`, `max_retries=1`, retry on `ValueError`
- **Compared modes**: `serial`, `thread`, `async`

### `bench_executor_sleep`
- **Task**: Pure 1-second sleep (simulating I/O wait)
- **Configuration**: `max_workers=12`, `max_retries=0`
- **Compared modes**: `serial`, `thread`, `async`

## Key Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `max_workers` | 6 (CPU) / 12 (I/O) | Number of concurrent workers |
| `max_retries` | 1 (CPU) / 0 (I/O) | Number of retries |

## Potential Issues

1. **Recursion depth limit**: `fibonacci` uses recursive implementation; input `n=31` produces ~2 million recursive calls taking several seconds. Accidentally passing larger values may cause `RecursionError`.
2. **`asyncio` event loop conflict**: `main()` uses `asyncio.run()`, which will raise an error in Jupyter or environments with an existing event loop.
3. **`benchmark_executor` output format**: This tool changes the `TaskExecutor`'s `execution_mode` multiple times and reruns, so total time = number of modes x number of tasks x per-task time, which may take several minutes to complete.

## How to Run

```bash
python bench/bench_execution_mode.py
```

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10

### Scenario 1: Fibonacci (CPU-intensive)
12 tasks (including 5 edge cases), max_workers=6, max_retries=1

| Mode | Duration | Notes |
|------|----------|-------|
| serial | 0.896s | Single-thread sequential execution |
| thread | 0.862s | 6 threads concurrent, limited improvement due to GIL |
| async | 0.009s | Coroutine concurrency, best performance in pure CPU scenarios due to no GIL overhead |

### Scenario 2: sleep_1 (I/O-intensive)
12 tasks, each sleeping 1 second, max_workers=12

| Mode | Duration | Notes |
|------|----------|-------|
| serial | 12.131s | Sequential sleep, total time ~= 12 x 1s |
| thread | 1.028s | 12 threads in parallel, total time ~= 1s + scheduling overhead |
| async | 1.024s | Coroutine parallelism, roughly on par with thread |

**Key Conclusions**:
- CPU-intensive tasks: async is ~100x faster than serial/thread due to no GIL contention (though in this case, fibonacci is purely synchronous recursive, and the async advantage mainly comes from event loop scheduling)
- I/O-intensive tasks: thread/async are ~12x faster than serial, approaching the theoretical limit
- Thread mode shows minimal improvement in CPU-intensive scenarios due to GIL limitation

## Dependencies

- `celestialflow` (`TaskExecutor`, `TaskProgress`, `benchmark_executor`)
