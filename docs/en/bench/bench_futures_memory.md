# bench_futures_memory.py Benchmark Notes

> 📅 Last Updated: 2026/05/08

## Objective

Compare the memory usage difference between two thread-pool strategies: keeping all futures forever versus periodically cleaning up completed futures. This benchmark does not depend on CelestialFlow and isolates the memory cost of futures themselves.

## Background

`ThreadPoolExecutor` returns a `Future` for each submitted task. If all futures are appended to a list and only reclaimed at the very end, the list grows without bound as the task count increases. Periodically filtering out completed futures keeps the list size around `max_workers * 2`.

## Test Cases

### `dispatch_no_cleanup`
- Append every future to the list and never clean it up.
- Call `future.result()` for all futures at the end.

### `dispatch_with_cleanup`
- After each append, check the list length; when it reaches `max_workers * 2`, filter out completed futures.
- Call `result()` only on the remaining futures at the end.

## Key Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `task_count` | 10K / 100K / 500K | Number of tasks |
| `max_workers` | 20 | Thread pool size |
| Task function | `noop(x)` | Returns directly, no computation cost |

## How to Run

```bash
python bench/bench_futures_memory.py
```

## Parameter Tuning

### Change Task Scale and Worker Count

Adjust these values in `main()` inside `bench/bench_futures_memory.py`:

```python
def main():
    scales = [10_000, 100_000, 500_000]  # Change task counts here
    max_workers = 20  # Adjust thread pool size
```

### Test Only One Scale

```python
def main():
    scales = [100_000]  # Only test 100K tasks
    max_workers = 20
```

### Change Worker Count to Observe the Effect

```python
def main():
    scales = [100_000]
    max_workers = 4   # Fewer workers, observe cleanup behavior at lower concurrency
    # max_workers = 50  # High-concurrency scenario
```

Run again after modification:

```bash
python bench/bench_futures_memory.py
```

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10, `max_workers=20`

| Task Count | Mode | Time | Peak Memory | Memory After Completion |
|------------|------|------|-------------|-------------------------|
| 10,000 | no_cleanup | 0.351s | 17.94 MB | 0.20 MB |
| 10,000 | with_cleanup | 1.589s | 0.45 MB | 0.10 MB |
| 100,000 | no_cleanup | 5.507s | 177.01 MB | 0.18 MB |
| 100,000 | with_cleanup | 15.807s | 0.48 MB | 0.09 MB |
| 500,000 | no_cleanup | 30.232s | 883.51 MB | 0.16 MB |
| 500,000 | with_cleanup | 79.774s | 0.46 MB | 0.09 MB |

**Key takeaways**:
- Without cleanup, peak memory grows linearly with task count: `10K -> 18 MB`, `100K -> 177 MB`, `500K -> 884 MB`.
- With periodic cleanup, peak memory stays around `0.5 MB`, independent of task count.
- At 500K tasks, memory savings reach about **1800x**.
- Cleanup introduces extra runtime overhead because of list filtering, but in the real framework tasks usually have actual compute cost, so this overhead is often negligible.

## Dependencies

- `tracemalloc` (standard library)
- `concurrent.futures` (standard library)
