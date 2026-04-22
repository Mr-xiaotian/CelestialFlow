# bench_datastructures.py Benchmark Documentation

> 📅 Last updated: 2026/04/22

## Objective

Compare read/write performance of various Python data structures and external storage backends under single-threaded and multi-process environments, providing quantitative evidence for selecting internal queues, shared state, and persistence backends in CelestialFlow.

## Test Cases

| Test Case | Description | Scale |
|-----------|-------------|-------|
| `test_builtin_dict` | Native dictionary put/get | N=10,000 |
| `test_queue_thread` | `queue.Queue` single-threaded read/write | N=10,000 |
| `test_mpqueue` | `multiprocessing.Queue` cross-process read/write | N=10,000 |
| `test_manager_dict` | `Manager().dict` cross-process read/write | N=10,000 |
| `test_value_number` | `multiprocessing.Value` atomic increment | N=10,000 |
| `test_redis_plain` | Redis sequential set/get | N=10,000 |
| `test_redis_pipeline` | Redis Pipeline batch set/get | N=10,000 |
| `test_redis_multithread_plain` | Redis multi-threaded concurrent writes | N=10,000 / 10 threads |
| `test_redis_hash` | Redis Hash sequential hset/hget | N=10,000 |
| `test_redis_list` | Redis List sequential rpush/lindex | N=10,000 |
| `test_redis_set` | Redis Set sequential sadd/sismember | N=10,000 |
| `test_redis_zset` | Redis Sorted Set sequential zadd/zscore | N=10,000 |

## Key Configuration

- `N = 10000`: Number of iterations per test
- Redis connection parameters loaded from `.env` (`REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`)

## Potential Issues

1. **Redis connection failure**: If Redis configuration is missing from `.env` or the service is not running, Redis-related tests will be skipped with a warning.
2. **Windows multi-process startup overhead**: `MPQueue` and `Manager().dict` tests under Windows `spawn` mode may spend significant time on subprocess startup alone, leading to inaccurate put/get timing.
3. **MPQueue buffer limits**: In `mpqueue_worker`, all N elements are put before get, which may hit OS pipe buffer limits when N is large (especially on Linux).

## How to Run

```bash
python bench/bench_datastructures.py
```

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10, local Redis, N=10,000

| Test Case | put/set | get | Notes |
|-----------|---------|-----|-------|
| Built-in dict | 0.0008s | 0.0003s | Single-threaded baseline, fastest |
| Queue (thread) | 0.0101s | 0.0108s | Thread-safe queue |
| MPQueue | 0.0149s | 0.3072s | Cross-process queue, get significantly slower due to serialization |
| Manager.dict | 0.5156s | 0.5369s | Manager server forwarding, 50-100x slower |
| Value (number) | 0.0174s | — | 10,000 atomic increments |
| Redis plain | 2.8352s | 2.9026s | Per-item RTT, dominated by network latency |
| Redis pipeline | 0.1474s | 0.1202s | Batched, ~20x faster than plain |
| Redis multi-thread | 1.1749s | 1.0765s | 10 threads concurrent, no pipeline |
| Redis hash | 2.8391s | 2.7675s | hset/hget, on par with plain |
| Redis list | 2.6853s | 2.8370s | rpush/lindex |
| Redis set | 2.7932s | 3.2969s | sadd/sismember |
| Redis zset | 3.1955s | 3.1854s | zadd/zscore |

**Key Conclusions**:
- Pure in-memory structures (dict, thread Queue) are 2-3 orders of magnitude faster than any IPC/network solution
- Redis Pipeline is essential for network scenarios, reducing latency from ~2.8s to ~0.15s
- MPQueue get is ~20x slower than put, primarily due to pickle deserialization overhead

## Dependencies

- `redis`
- `python-dotenv`
