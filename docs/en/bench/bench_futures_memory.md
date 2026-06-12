# bench_futures_memory.py Benchmark Notes

> 📅 Last Updated: 2026/05/08

## Objective

Purely compare the memory usage difference between "no cleanup" and "periodic cleanup" strategies for a futures list in a thread pool scenario. Does not depend on the CelestialFlow framework, measuring the memory overhead of futures themselves in isolation.

## Background

`ThreadPoolExecutor` returns `Future` objects after submitting tasks. If all futures are appended to a list and awaited for final collection, the list grows unboundedly with the task count. Periodically filtering out completed futures can limit the list size to `max_workers * 2`.

## Test Contents

### `dispatch_no_cleanup`
- All futures appended to list, no cleanup performed
- Unified `future.result()` call at the end

### `dispatch_with_cleanup`
- After each append, check list length; when it reaches `max_workers * 2`, filter out completed futures
- Call `result()` on remaining futures at the end

## Key Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `task_count` | 10K / 100K / 500K | Task count |
| `max_workers` | 20 | Thread pool size |
| Task function | `noop(x)` | Returns immediately, no computation overhead |

## How to Run

```bash
python bench/bench_futures_memory.py
```

## Parameter Tuning

### Adjusting Task Scale and Worker Count

Adjust in the `main()` function of `bench/bench_futures_memory.py`:

```python
def main():
    scales = [10_000, 100_000, 500_000]  # Modify task count here
    max_workers = 20  # Adjust thread pool size
```

### Testing a Single Scale Only

```python
def main():
    scales = [100_000]  # Test 100K tasks only
    max_workers = 20
```

### Adjusting Worker Count to Observe Impact

```python
def main():
    scales = [100_000]
    max_workers = 4   # Fewer workers, observe cleanup strategy behavior at different concurrency levels
    # max_workers = 50  # High concurrency scenario
```

Run after modification:

```bash
python bench/bench_futures_memory.py
```

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10, max_workers=20

| Task Count | Mode | Time | Peak Memory | Memory After Completion |
|------------|------|------|-------------|------------------------|
| 10,000 | no_cleanup | 0.351s | 17.94 MB | 0.20 MB |
| 10,000 | with_cleanup | 1.589s | 0.45 MB | 0.10 MB |
| 100,000 | no_cleanup | 5.507s | 177.01 MB | 0.18 MB |
| 100,000 | with_cleanup | 15.807s | 0.48 MB | 0.09 MB |
| 500,000 | no_cleanup | 30.232s | 883.51 MB | 0.16 MB |
| 500,000 | with_cleanup | 79.774s | 0.46 MB | 0.09 MB |

**Key Takeaways**:
- Without cleanup, peak memory grows linearly with task count: 10K → 18 MB, 100K → 177 MB, 500K → 884 MB
- With periodic cleanup, peak memory stays constant at ~0.5 MB regardless of task count
- At 500K tasks, memory savings are approximately **1800x**
- The cleanup operation has additional time overhead (list filtering), but in a real framework where tasks have computation overhead, this overhead is negligible

## Dependencies

- `tracemalloc` (stdlib)
- `concurrent.futures` (stdlib)
