# bench_queue.py Benchmark Notes

> 📅 Last Updated: 2026/04/22

## Objective

Compare the performance of `put` / `get` / `qsize` / `empty` across several queue implementations in a single-process environment, including thread queues, multiprocessing queues, Manager queues, and Redis queues.

## Test Cases

| Queue Type | Description | Measured Operations |
|------------|-------------|---------------------|
| `ThreadQueue` | `queue.Queue` | put, get, qsize, empty |
| `MPQueue` | `multiprocessing.Queue` | put, get, qsize, empty |
| `Manager().Queue` | `Manager().Queue` | put, get, qsize, empty |
| `Redis List` | Redis `lpush` / `rpop` | lpush, rpop, llen, empty-check |
| `Redis Stream` | Redis `xadd` / `xread` | xadd, xread, xlen, empty-check |

- **Scale**: `COUNT = 100_000`
- **Redis config**: loaded from `.env` (`REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`)

## Potential Issues

1. **Misleading MPQueue result in a single process**: `MPQueue` is designed for cross-process use, so its pipe/socket overhead is exaggerated in single-process measurements.
2. **Blocking behavior of Redis Stream**: `xread` uses `block=0` (infinite blocking). If the message count does not match expectations, the benchmark can hang forever.
3. **`qsize()` is not precise**: `MPQueue.qsize()` is inherently approximate in multi-process contexts, and even in a single-process test it can lag behind because of internal buffering.
4. **Redis `flushdb`**: the benchmark calls `flushdb` before running. Pointing it at a production Redis instance would delete real data.

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10, `COUNT=100,000`
> Note: Redis benchmarks did not finish within the 120s timeout because the local Redis service was slow to respond. The table below therefore contains only local queue results.

### Local Queue Comparison

| Queue Type | put/lpush | get/rpop | Notes |
|------------|-----------|----------|-------|
| **ThreadQueue** | 0.0777s | 0.0723s | Pure in-memory, no serialization, fastest |
| **MPQueue** | 0.1198s | **3.0071s** | `put` is acceptable, but `get` is extremely slow because of cross-process deserialization |
| **Manager().Queue** | 8.0674s | 8.5525s | Forwarded through a Manager server, more than 100x slower |

### Redis Queue (Historical Reference, Not Fully Re-run This Time)

| Operation | Estimated Time (100k) | Bottleneck |
|-----------|-----------------------|------------|
| Redis List `lpush` / `rpop` | ~2-3s | Network RTT |
| Redis Stream `xadd` / `xread` | ~3-5s | Stream parsing overhead |

**Key takeaways**:
- `ThreadQueue` is about **40x** faster than `MPQueue.get` and more than **100x** faster than `Manager().Queue`.
- The biggest weakness of `MPQueue` is `get` (`3s` vs `0.07s`), so any opportunity to downgrade an internal queue to thread mode brings major gains.
- Redis queues are for cross-device or cross-network scenarios; they are not a sensible choice for local IPC.

## How to Run

```bash
python bench/bench_queue.py
```

## Parameter Tuning

### Change the Test Scale

The default is `COUNT = 100_000`. You can modify it in `if __name__ == "__main__"`:

```python
if __name__ == "__main__":
    COUNT = 10_000       # Small-scale quick verification (a few seconds)
    # COUNT = 1_000_000  # Large-scale stress test (Manager().Queue becomes very slow)
```

### Test Only Specific Queue Types

```python
if __name__ == "__main__":
    COUNT = 10_000

    # test_threadqueue_perf(COUNT)        # Skip thread queue
    test_mpqueue_perf(COUNT)              # Only test MPQueue
    # test_manager_queue_perf(COUNT)      # Skip Manager queue
    # test_redis_list_perf(COUNT)         # Skip Redis
    # test_redis_stream_perf(COUNT)
```

Run again after modification:

```bash
python bench/bench_queue.py
```

## Dependencies

- `redis`
- `python-dotenv`
