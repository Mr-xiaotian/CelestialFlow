# bench_datastructures.py Benchmark Notes

> 📅 Last Updated: 2026/05/09

## Objective

Compare the read/write performance of several Python data structures and external storage backends in a single-threaded environment, providing quantitative evidence for CelestialFlow's internal queue and persistence backend choices.

## Test Cases

| Case | Description | Scale |
|------|-------------|-------|
| `test_builtin_dict` | Native dictionary put/get | N=10,000 |
| `test_queue_thread` | Single-threaded `queue.Queue` put/get | N=10,000 |
| `test_mpqueue` | Cross-process `multiprocessing.Queue` put/get (deprecated, kept for reference) | N=10,000 |
| `test_manager_dict` | Cross-process `Manager().dict` put/get | N=10,000 |
| `test_value_number` | Atomic increment with `multiprocessing.Value` (deprecated, kept for reference) | N=10,000 |
| `test_redis_plain` | Redis per-item set/get | N=10,000 |
| `test_redis_pipeline` | Redis Pipeline batch set/get | N=10,000 |
| `test_redis_multithread_plain` | Multi-threaded concurrent Redis writes | N=10,000 / 10 threads |
| `test_redis_hash` | Redis Hash per-item hset/hget | N=10,000 |
| `test_redis_list` | Redis List per-item rpush/lindex | N=10,000 |
| `test_redis_set` | Redis Set per-item sadd/sismember | N=10,000 |
| `test_redis_zset` | Redis Sorted Set per-item zadd/zscore | N=10,000 |

## Key Configuration

- `N = 10000`: number of iterations for each test.
- Redis connection settings are loaded from `.env` (`REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`).

## Potential Issues

1. **Redis connection failure**: if Redis configuration is missing in `.env` or the service is not running, Redis-related benchmarks are skipped with a warning.
2. **MPQueue buffer limit**: `mpqueue_worker` puts all `N` items before getting them back; when `N` is large, this can hit the OS pipe buffer limit, especially on Linux.

> **Note**: `test_mpqueue` and `test_value_number` rely on `multiprocessing.Queue` and `multiprocessing.Value`, which are no longer used internally by the framework because `stage_mode="process"` has been removed. These benchmarks remain only as historical reference.

## How to Run

```bash
python bench/bench_datastructures.py
```

## Parameter Tuning

### Change the Test Scale

Modify `N = 10000` in `bench/bench_datastructures.py`:

```python
# Small-scale quick verification
N = 1000

# Large-scale stress test
N = 100_000
```

### Run Only a Specific Test

The script runs all benchmarks by default. To focus on one structure, comment out the others in `main()`:

```python
if __name__ == "__main__":
    print(f"\nRunning benchmarks with N={N}\n")

    test_builtin_dict()          # Only test built-in dict
    # test_queue_thread()
    # test_mpqueue()
    # test_manager_dict()
    # ...
    # test_redis_plain(r)
    # test_redis_pipeline(r)
```

### Adjust the Redis Thread Count

`test_redis_multithread_plain` accepts a custom thread count:

```python
# Pass num_threads when calling the function
test_redis_multithread_plain(r, num_threads=5)   # 5 threads
# test_redis_multithread_plain(r, num_threads=20)  # 20 threads
```

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10, local Redis, N=10,000

| Case | put/set | get | Notes |
|------|---------|-----|-------|
| Built-in dict | 0.0008s | 0.0003s | Single-thread baseline, fastest |
| Queue (thread) | 0.0101s | 0.0108s | Thread-safe queue |
| MPQueue | 0.0149s | 0.3072s | Cross-process queue; `get` is much slower due to serialization |
| Manager.dict | 0.5156s | 0.5369s | Forwarded through a Manager server, 50-100x slower |
| Value (number) | 0.0174s | — | 10,000 atomic increments |
| Redis plain | 2.8352s | 2.9026s | Per-item RTT dominates |
| Redis pipeline | 0.1474s | 0.1202s | Batched requests, about 20x faster than plain |
| Redis multi-thread | 1.1749s | 1.0765s | 10 concurrent threads, no pipeline |
| Redis hash | 2.8391s | 2.7675s | hset/hget, roughly on par with plain |
| Redis list | 2.6853s | 2.8370s | rpush/lindex |
| Redis set | 2.7932s | 3.2969s | sadd/sismember |
| Redis zset | 3.1955s | 3.1854s | zadd/zscore |

**Key takeaways**:
- Pure in-memory structures (`dict`, thread `Queue`) are 2-3 orders of magnitude faster than IPC or network-based solutions.
- Redis Pipeline is essential in networked scenarios, reducing latency from about `2.8s` to about `0.15s`.
- `MPQueue.get` is about 20x slower than `put`, mainly because of pickle deserialization.

## Dependencies

- `redis`
- `python-dotenv`
