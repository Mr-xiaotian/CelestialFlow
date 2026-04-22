# bench_queue.py Benchmark Documentation

> 📅 Last updated: 2026/04/22

## Objective

Compare the put/get/qsize/empty operation performance of various queue implementations in a single-process environment, including thread queues, multi-process queues, Manager queues, and Redis queues.

## Test Cases

| Queue Type | Description | Test Operations |
|------------|-------------|-----------------|
| `ThreadQueue` | `queue.Queue` | put, get, qsize, empty |
| `MPQueue` | `multiprocessing.Queue` | put, get, qsize, empty |
| `Manager().Queue` | `Manager().Queue` | put, get, qsize, empty |
| `Redis List` | Redis `lpush`/`rpop` | lpush, rpop, llen, empty-check |
| `Redis Stream` | Redis `xadd`/`xread` | xadd, xread, xlen, empty-check |

- **Scale**: `COUNT = 100_000`
- **Redis configuration**: Loaded from `.env` (`REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`)

## Potential Issues

1. **`MPQueue` misleading in single-process**: `MPQueue` is designed for cross-process use. Testing within a single process amplifies the underlying pipe/socket overhead, and results do not represent real cross-process performance.
2. **Redis Stream block behavior**: `xread` uses `block=0` (infinite blocking). If the message count does not match expectations, the test will hang forever.
3. **`qsize()` unreliability**: `MPQueue.qsize()` is imprecise in multi-process environments; even in single-process testing, its value may lag due to internal buffering.
4. **Redis `flushdb`**: The test executes `flushdb` before starting. If connected to a production Redis instance, this will cause data loss.

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10, COUNT=100,000
> Note: Redis tests did not complete within the 120s timeout due to slow local Redis service response. Below are local queue measured results only.

### Local Queue Comparison

| Queue Type | put/lpush | get/rpop | Notes |
|------------|-----------|----------|-------|
| **ThreadQueue** | 0.0777s | 0.0723s | Pure memory, no serialization, fastest |
| **MPQueue** | 0.1198s | **3.0071s** | put is acceptable, get extremely slow due to cross-process deserialization |
| **Manager().Queue** | 8.0674s | 8.5525s | Manager server forwarding, 100x+ slower |

### Redis Queues (Historical Reference, Not Fully Completed This Run)

| Operation | Estimated Duration (100k) | Bottleneck |
|-----------|--------------------------|------------|
| Redis List lpush/rpop | ~2-3s | Network RTT |
| Redis Stream xadd/xread | ~3-5s | Stream parsing overhead |

**Key Conclusions**:
- ThreadQueue get is **40x** faster than MPQueue, **100x+** faster than Manager().Queue
- MPQueue's get is the biggest weakness (3s vs 0.07s); if the framework's internal queue can fall back to thread mode, the benefit is enormous
- Redis queues are suitable for cross-device/cross-network scenarios and should not be considered for local IPC at all

## How to Run

```bash
python bench/bench_queue.py
```

## Dependencies

- `redis`
- `python-dotenv`
