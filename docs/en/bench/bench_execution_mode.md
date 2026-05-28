# bench_execution_mode.py Benchmark Documentation

> 📅 Last Updated: 2026/05/28

## Objective

Compare performance differences of `TaskExecutor` across three execution modes (`serial`, `thread`, `async`) when handling CPU-intensive tasks (Fibonacci) and I/O-intensive tasks (sleep). Uses the framework's built-in `benchmark_executor` tool for unified comparison reports.

## Test Cases

### `bench_executor_fibonacci`
- **Task**: Compute Fibonacci sequence (`n=25..31`), including edge cases (`0, None, ""`)
- **Configuration**: `max_workers=6`, `max_retries=1`, retry on `ValueError`
- **Compared modes**: `serial`, `thread`, `async`

Both Fibonacci implementations use the **same iterative O(n) algorithm** to ensure a fair comparison:

```python
# Sync version — iterative, O(n)
def fibonacci(n):
    ...
    prev, curr = 1, 1
    for _ in range(3, n + 1):
        prev, curr = curr, prev + curr
    return curr

# Async version — iterative + coroutine yield every 8 rounds, O(n)
async def fibonacci_async(n):
    ...
    prev, curr = 1, 1
    for i in range(3, n + 1):
        prev, curr = curr, prev + curr
        if i % 8 == 0:
            await asyncio.sleep(0)  # yield the event loop
    return curr
```

The only difference is that `fibonacci_async` has an `await` yield point every 8 iterations — an inherent characteristic of the cooperative scheduling model in async execution mode.

### `bench_executor_sleep`
- **Task**: Pure 1-second sleep (simulating I/O wait); sync and async versions behave identically
- **Configuration**: `max_workers=6`, `max_retries=0`
- **Compared modes**: `serial`, `thread`, `async`

## Key Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `max_workers` | 6 (CPU) / 6 (I/O) | Number of concurrent workers |
| `max_retries` | 1 (CPU) / 0 (I/O) | Number of retries |

## Potential Issues

1. **CPU-intensive tasks limited by GIL**: Python's GIL restricts execution of Python bytecode to a single thread at a time. In `thread` mode, even with 6 workers, pure computation is largely serialized by the GIL.
2. **`asyncio` event loop conflict**: `main()` uses `asyncio.run()`, which will raise an error in Jupyter or environments with an existing event loop.
3. **`benchmark_executor` output format**: This tool changes the `TaskExecutor`'s `execution_mode` multiple times and reruns, so total time = number of modes × number of tasks × per-task time.

## How to Run

```bash
python bench/bench_execution_mode.py
```

## Parameter Adjustment

### Running a Specific Test Scenario

In `bench/bench_execution_mode.py`'s `main()`, you can selectively run tests:

```python
async def main():
    # Run only the Fibonacci test
    await bench_executor_fibonacci()
    # await bench_executor_sleep()  # comment out the sleep test
```

```bash
# Run after modification
python bench/bench_execution_mode.py
```

### Customizing Input Range

The Fibonacci test inputs are defined inside the function; you can modify the `numbers` list:

```python
# Test only small values (quick verification)
numbers = [10, 15, 20]

# Expand the range
numbers = list(range(20, 35))
```

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10

### Scenario 1: Fibonacci (CPU-intensive)
12 tasks (including 5 edge cases), max_workers=6, max_retries=1. All three modes use the **same iterative O(n) algorithm**.

| Mode | Duration | Notes |
|------|----------|-------|
| serial | 0.0065s | Single-thread sequential execution, pure computation with no scheduling overhead |
| thread | 0.0048s | 6 threads concurrent, limited by GIL, modest improvement |
| async | 0.0062s | Coroutine concurrency; await yield points in iteration allow concurrency, but still limited by pure computation nature |

> 🟢 All three modes are within the same order of magnitude (~5–6ms). Thread is slightly faster because the GIL still has small concurrency windows between high-frequency iteration yield points; async's `await` yield points introduce minuscule coroutine scheduling overhead. Overall differences are in microseconds — none of the three modes provide significant acceleration for CPU-intensive tasks.

### Scenario 2: sleep_1 (I/O-intensive)
6 tasks, each sleeping 1 second, max_workers=6. Sync and async sleep behavior is identical; the comparison results directly reflect execution mode differences.

| Mode | Duration | Notes |
|------|----------|-------|
| serial | 6.010s | Sequential sleep, total time ≈ 6 × 1s |
| thread | 1.006s | 6 threads in parallel, total time ≈ 1s + scheduling overhead |
| async | 1.009s | Coroutine parallelism, roughly on par with thread |

**Key Conclusions**:
- **I/O-intensive tasks**: Both thread and async achieve near-theoretical-optimal parallelism (~6× speedup), with negligible difference between them
- **CPU-intensive tasks**: All three modes are within the same order of magnitude. Pure computation tasks are limited by Python's GIL, giving thread mode no significant advantage; async can achieve concurrency at coroutine yield points but overall improvement is limited
- The core criterion for choosing an execution mode is **task nature**: use thread/async for I/O waits, consider GIL impact (or multiprocessing) for pure computation

## Dependencies

- `celestialflow` (`TaskExecutor`, `TaskProgress`, `benchmark_executor`)
