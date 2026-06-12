# bench_datastructures.py Benchmark Notes

> 📅 Last Updated: 2026/06/11

## Objective

Compare the read/write performance of various Python data structures and external storage in a single-threaded environment, providing quantitative data for CelestialFlow's internal queue and persistence backend selection.

## Test Contents

| Test Item | Description | Scale |
|-----------|-------------|-------|
| `test_builtin_dict` | Native dict put/get | N=10,000 |
| `test_queue_thread` | `queue.Queue` single-thread read/write | N=10,000 |
| `test_mpqueue` | `multiprocessing.Queue` cross-process read/write (deprecated, retained for reference only) | N=10,000 |
| `test_manager_dict` | `Manager().dict` cross-process read/write | N=10,000 |
| `test_value_number` | `multiprocessing.Value` atomic increment (deprecated, retained for reference only) | N=10,000 |
| `test_redis_plain` | Redis individual set/get | N=10,000 |
| `test_redis_pipeline` | Redis Pipeline batch set/get | N=10,000 |
| `test_redis_multithread_plain` | Redis multi-thread concurrent writes | N=10,000 / 10 threads |
| `test_redis_hash` | Redis Hash individual hset/hget | N=10,000 |
| `test_redis_list` | Redis List individual rpush/lindex | N=10,000 |
| `test_redis_set` | Redis Set individual sadd/sismember | N=10,000 |
| `test_redis_zset` | Redis Sorted Set individual zadd/zscore | N=10,000 |

## Key Configuration

- `N = 10000`: iteration count per test
- Redis connection parameters loaded from `.env` (`REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`)

## Potential Issues

1. **Redis connection failure**: If Redis config is missing in `.env` or the service is not running, Redis-related tests will be skipped with a warning only.
2. **MPQueue buffer limit**: The `mpqueue_worker` puts all N elements first before getting, which may hit the OS pipe buffer limit when N is large (especially on Linux).

> **Note**: `test_mpqueue` and `test_value_number` use `multiprocessing.Queue` and `multiprocessing.Value`, which are no longer used internally by the framework (`stage_mode="process"` has been removed). These benchmarks still run by default in the script, primarily serving as a cross-process performance baseline comparison against pure in-memory solutions, retained for reference.

## How to Run

```bash
python bench/bench_datastructures.py
```

## Parameter Tuning

### Adjusting Test Scale

Modify `N = 10000` in `bench/bench_datastructures.py` to change the test scale:

```python
# Small scale quick validation
N = 1000

# Large scale stress test
N = 100_000
```

### Running Specific Tests in Isolation

The script runs all tests by default. To validate a single data structure, comment out other calls in `main()`:

```python
if __name__ == "__main__":
    print(f"\nRunning benchmarks with N={N}\n")

    test_builtin_dict()          # Test built-in dict only
    # test_queue_thread()
    # test_mpqueue()
    # test_manager_dict()
    # ...
    # test_redis_plain(r)
    # test_redis_pipeline(r)
```

### Adjusting Redis Thread Count

`test_redis_multithread_plain` supports a custom concurrency thread count:

```python
# Pass num_threads parameter when calling the function
test_redis_multithread_plain(r, num_threads=5)   # 5 threads
# test_redis_multithread_plain(r, num_threads=20)  # 20 threads
```

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10, local Redis, N=10,000

| Test Item | put/set | get | Notes |
|-----------|---------|-----|-------|
| Built-in dict | 0.0008s | 0.0003s | Single-thread baseline, fastest |
| Queue (thread) | 0.0101s | 0.0108s | Thread-safe queue |
| MPQueue | 0.0149s | 0.3072s | Cross-process queue, get significantly slower due to serialization |
| Manager.dict | 0.5156s | 0.5369s | Manager server forwarding, 50-100x slower |
| Value (number) | 0.0174s | — | 10,000 atomic increments |
| Redis plain | 2.8352s | 2.9026s | Per-item RTT, network latency dominates |
| Redis pipeline | 0.1474s | 0.1202s | Batch packing, ~20x faster than plain |
| Redis multi-thread | 1.1749s | 1.0765s | 10 threads concurrent, no pipeline |
| Redis hash | 2.8391s | 2.7675s | hset/hget, comparable to plain |
| Redis list | 2.6853s | 2.8370s | rpush/lindex |
| Redis set | 2.7932s | 3.2969s | sadd/sismember |
| Redis zset | 3.1955s | 3.1854s | zadd/zscore |

**Key Takeaways**:
- Pure in-memory structures (dict, thread Queue) are 2-3 orders of magnitude faster than any IPC/network solution
- Redis Pipeline is essential in networked scenarios, reducing latency from ~2.8s to ~0.15s
- MPQueue's get is ~20x slower than put, primarily due to pickle deserialization overhead

## Dependencies

- `redis`
- `python-dotenv`
