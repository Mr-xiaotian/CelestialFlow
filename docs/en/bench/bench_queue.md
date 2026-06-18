# bench_queue.py Benchmark Guide

> 📅 Last Updated: 2026/06/16

## Objective

In a single-process environment, compare the put/get/qsize/empty operation performance of various queue implementations, including thread queues, multiprocessing queues, Manager queues, and Redis queues.

## Test Content

| Queue Type | Description | Test Operations |
|----------|------|----------|
| `ThreadQueue` | `queue.Queue` | put, get, qsize, empty |
| `MPQueue` | `multiprocessing.Queue` | put, get, qsize, empty |
| `Manager().Queue` | `Manager().Queue` | put, get, qsize, empty |
| `Redis List` | Redis `lpush`/`rpop` | lpush, rpop, llen, empty-check |
| `Redis Stream` | Redis `xadd`/`xread` | xadd, xread, xlen, empty-check |

- **Scale**: `COUNT = 100_000`
- **Redis config**: Read from `.env` (`REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`)

## Potential Issues

1. **Misleading `MPQueue` in single process**: `MPQueue` is designed for cross-process use; when tested in a single process, the underlying pipe/socket overhead is amplified and the results do not represent real cross-process performance.
2. **Redis Stream blocking behavior**: `xread` uses `block=0` (infinite blocking); if the message count does not match expectations, the test will hang indefinitely.
3. **`qsize()` unreliability**: `MPQueue.qsize()` is inexact in multi-process environments; even in single-process testing, its value may lag due to internal buffering.
4. **Redis `flushdb`**: `flushdb` is executed before the test starts; if connected to a production Redis instance, this will cause data loss.

## Benchmark Results (Measured)

### Historical Results - Windows local queues and Redis (date not recorded)

> Environment: Windows, Python 3.10, COUNT=100,000
> Note: Redis tests did not complete within the 120s timeout due to slow local Redis service response; below are local queue measured results.

#### Local Queue Comparison

| Queue Type | put/lpush | get/rpop | Notes |
|----------|-----------|----------|------|
| **ThreadQueue** | 0.0777s | 0.0723s | Pure memory, no serialization, fastest |
| **MPQueue** | 0.1198s | **3.0071s** | put is acceptable, get is extremely slow due to cross-process deserialization |
| **Manager().Queue** | 8.0674s | 8.5525s | Manager server forwarding, 100x+ slower |

#### Redis Queues (historical reference values, not fully completed this run)

| Operation | Estimated Time (100k) | Bottleneck |
|------|-----------------|------|
| Redis List lpush/rpop | ~2-3s | Network RTT |
| Redis Stream xadd/xread | ~3-5s | Stream parsing overhead |

**Key Takeaways**:
- ThreadQueue is **40x** faster than MPQueue get, and **100x+** faster than Manager().Queue
- MPQueue's get is the biggest bottleneck (3s vs 0.07s); if the framework's internal queue can degrade to thread mode, the gains are enormous
- Redis queues are suitable for cross-device/cross-network scenarios; they should never be considered for local IPC

### 2026/06/16 - Local queues and Redis retest

> Environment: Windows, COUNT=100,000, Redis service available for this round, List / Stream tests completed

#### Local Queue Comparison

| Queue Type | put/lpush | get/rpop | qsize/xlen/llen | empty |
|----------|-----------|----------|-----------------|-------|
| **ThreadQueue** | 0.0401s | 0.0427s | 0.0159s | 0.0202s |
| **MPQueue** | 0.0857s | 1.7550s | 0.0650s | 0.9309s |
| **Manager().Queue** | 3.4102s | 3.2287s | 3.1512s | 3.0891s |

#### Redis Queues (measured this round)

| Type | Write | Read | Length Query | empty |
|------|------|------|----------|-------|
| Redis List | 24.7174s | 24.8115s | 24.7813s | 24.5446s |
| Redis Stream | 26.5111s | 0.5551s | 25.8857s | 27.2085s |

**Supplementary conclusions for this round**:
- Local queues remain far faster than Redis; `ThreadQueue` is still the lightest choice for purely local scenarios
- `MPQueue`'s `get` and `empty` costs remain very high; cross-process synchronization state checks are especially expensive
- With Redis available this round, we can see: `xread` is fast, but `xadd` / `xlen` / flush phases are all very heavy; overall not suitable for local high-frequency queuing

## How to Run

```bash
python bench/bench_queue.py
```

## Parameter Tuning

### Adjusting Test Scale

The script defaults to `COUNT = 100_000`; modify in `if __name__ == "__main__"`:

```python
if __name__ == "__main__":
    COUNT = 10_000       # Small scale quick validation (takes a few seconds)
    # COUNT = 1_000_000  # Large scale stress test (note Manager().Queue will be extremely slow)
```

### Testing Specific Queue Types Only

```python
if __name__ == "__main__":
    COUNT = 10_000

    # test_threadqueue_perf(COUNT)        # Comment out thread queue
    test_mpqueue_perf(COUNT)              # Test MPQueue only
    # test_manager_queue_perf(COUNT)      # Skip Manager queue
    # test_redis_list_perf(COUNT)         # Skip Redis
    # test_redis_stream_perf(COUNT)
```

Run after modification:

```bash
python bench/bench_queue.py
```

## Dependencies

- `redis`
- `python-dotenv`
