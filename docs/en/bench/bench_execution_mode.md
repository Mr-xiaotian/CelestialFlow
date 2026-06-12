# bench_execution_mode.py Benchmark Notes

> 📅 Last Updated: 2026/06/11

## Objective

Compare the performance differences of `TaskExecutor` across three execution modes (`serial`, `thread`, `async`) when handling CPU-intensive tasks (Fibonacci) and I/O-intensive tasks (sleep). Uses the framework's built-in `benchmark_executor` tool for unified comparison output.

## Test Contents

### `bench_executor_fibonacci`
- **Tasks**: Compute Fibonacci sequence (`n=25..31`), including invalid inputs (`0, None, ""`)
- **Config**: `max_workers=6`, `max_retries=1`, retry on `ValueError`
- **Compared Modes**: `serial`, `thread`, `async`

Both Fibonacci implementations use the **same iterative O(n) algorithm** for fair comparison:

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
            await asyncio.sleep(0)  # Yield to event loop
    return curr
```

The only difference is that `fibonacci_async` has an `await` yield point every 8 iterations, which is an inherent cooperative scheduling characteristic of the async execution mode.

### `bench_executor_sleep`
- **Tasks**: Pure sleep of 1 second (simulating I/O wait); sync and async versions behave identically
- **Config**: `max_workers=6`, `max_retries=0`
- **Compared Modes**: `serial`, `thread`, `async`

## Key Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `max_workers` | 6 (CPU) / 6 (I/O) | Concurrent worker count |
| `max_retries` | 1 (CPU) / 0 (I/O) | Retry count |

## Potential Issues

1. **CPU-intensive tasks constrained by GIL**: Python's GIL restricts only one thread to execute Python bytecode at a time. In `thread` mode, even with 6 workers, most of the pure computation time is still serialized by the GIL.
2. **`asyncio` event loop conflict**: `main()` uses `asyncio.run()`, which will error in Jupyter or environments with an existing event loop.
3. **`benchmark_executor` output format**: This tool changes `TaskExecutor`'s `execution_mode` multiple times and reruns, total time = number of modes × number of tasks × single task time.

## How to Run

```bash
python bench/bench_execution_mode.py
```

## Parameter Tuning

### Running a Specific Test Scenario

In `bench/bench_execution_mode.py`'s `main()`, you can selectively run:

```python
async def main():
    # Run Fibonacci test only
    await bench_executor_fibonacci()
    # await bench_executor_sleep()  # Comment out sleep test
```

```bash
# Run after modification
python bench/bench_execution_mode.py
```



### Customizing Input Range

Fibonacci test inputs are defined in the `bench_task_1` list inside the function; you can modify the task list:

```python
# Test small values only (quick validation)
bench_task_1: list[Any] = [10, 15, 20]

# Expand range
bench_task_1: list[Any] = list(range(20, 35))
```

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10

### Scenario 1: Fibonacci (CPU-intensive)
Input of 12 tasks (including 5 boundary error cases), max_workers=6, max_retries=1. All three modes use the **same iterative O(n) algorithm**.

| Mode | Time | Description |
|------|------|-------------|
| serial | 0.0065s | Single-thread sequential execution, pure computation with no scheduling overhead |
| thread | 0.0048s | 6 threads concurrent, constrained by GIL, limited improvement |
| async | 0.0062s | Coroutine concurrency, await yield points in iterations allow concurrency but still limited by pure computation nature |

> 🟢 All three modes are in the same order of magnitude (~5-6ms). Thread is slightly faster because GIL still offers small concurrency windows between high-frequency iteration yield points; async's `await` yield points introduce minimal coroutine scheduling overhead. Overall differences are in microseconds — CPU-intensive tasks see no significant speedup in any mode.

### Scenario 2: sleep_1 (I/O-intensive)
Input of 6 tasks, each sleeping 1 second, max_workers=6. Sync and async sleep behavior is consistent, so comparison results directly reflect execution mode differences.

| Mode | Time | Description |
|------|------|-------------|
| serial | 6.010s | Sequential sleep, total ≈ 6 × 1s |
| thread | 1.006s | 6 threads parallel, total ≈ 1s + scheduling overhead |
| async | 1.009s | Coroutine parallel, essentially on par with thread |

**Key Takeaways**:
- **I/O-intensive tasks**: Both thread and async achieve near-theoretical optimal parallelism (~12x speedup), with negligible difference between them
- **CPU-intensive tasks**: All three modes are in the same order of magnitude. Pure computation tasks are constrained by Python's GIL — thread offers no significant advantage; async can be concurrent at coroutine yield points but the overall improvement is limited
- The core criterion for choosing an execution mode is **task nature**: thread/async for I/O waiting, consider GIL impact for pure computation (or consider multiprocessing)

## Dependencies

- `celestialflow` (`TaskExecutor`, `TaskProgress`, `benchmark_executor`)
