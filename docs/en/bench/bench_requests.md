# bench_requests.py Benchmark Notes

> 📅 Last Updated: 2026/04/22

## Objective

Quantitatively compare the HTTP request performance of the `requests` library under different usage patterns: whether to use Session, whether to use concurrency, and Session sharing granularity. Provide optimization insights for CelestialFlow modules involving HTTP communication (Reporter, CelestialTree HTTP client).

## Test Contents

| Scenario | Session Usage | Concurrency |
|----------|---------------|-------------|
| Sequential - no session | New `requests.get()` each time | None |
| Sequential - with session | Reuse single `Session` | None |
| Concurrent - no session | New `requests.get()` each time | 10 threads |
| Concurrent - per-thread session | Each thread has its own `Session` | 10 threads |

- **Target URL**: `https://httpbin.org/get`
- **Request Count**: `NUM_REQUESTS = 50`
- **Timeout**: `TIMEOUT = 30`

## Key Metrics

Outputs mean, median, stdev, min, max (in milliseconds) for each group of requests.

## Potential Issues

1. **Network fluctuation**: The target `httpbin.org` is on the public internet; latency is affected by local network and international link quality, making single-run results non-reproducible.
2. **Connection pool not warmed up**: `requests.Session`'s connection pool establishes TCP/TLS connections on first request; the first few requests may have significantly higher latency than subsequent ones.
3. **GIL constraint**: Threads in `ThreadPoolExecutor` are constrained by Python's GIL; CPU-intensive parts of `requests` (e.g., TLS handshake, JSON parsing) cannot truly parallelize.
4. **httpbin rate limiting**: Frequent testing may trigger httpbin rate limiting, returning 429 or connection resets.

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10, target https://httpbin.org/get, 50 requests, 10 concurrent threads

| Scenario | Mean | Median | Stdev | Min | Max |
|----------|------|--------|-------|-----|-----|
| **Sequential - no session** | 1144.1 ms | 1059.7 ms | 169.0 ms | 991.9 ms | 1680.1 ms |
| **Sequential - with session** | **274.7 ms** | **166.8 ms** | 204.5 ms | 162.1 ms | 1047.7 ms |
| **Concurrent - no session** | 1795.4 ms | 1738.8 ms | 417.9 ms | 1180.0 ms | 2837.8 ms |
| **Concurrent - per-thread session** | 1734.6 ms | 1738.8 ms | 215.9 ms | 1154.4 ms | 2407.4 ms |

**Key Takeaways**:
- **Session reuse provides the greatest benefit**: For sequential requests, using Session is **4.2x** faster than no Session (1144ms → 275ms), because repeated TCP/TLS handshakes are avoided
- **Concurrency did not bring additional benefits**: In this test, the mean for concurrent scenarios (10 threads) was actually higher than serial, because httpbin's public network latency and server-side processing became the bottleneck, and client-side concurrency could not break through
- **Per-thread independent Session is pointless**: In concurrent scenarios, each thread having its own Session performed nearly identically to no Session, because connection reuse benefits are offset by connection pool contention under high concurrency
- Implication for CelestialFlow: Reporter and CelestialTree HTTP client should reuse `requests.Session` globally

## How to Run

```bash
python bench/bench_requests.py
```

## Parameter Tuning

### Adjusting Request Count and Concurrency

Modify configuration at the top of `bench/bench_requests.py`:

```python
NUM_REQUESTS = 10          # Reduce request count for quick validation
# NUM_REQUESTS = 200       # Increase request count, observe steady-state performance after connection pool warm-up

CONCURRENT_WORKERS = 4     # Reduce concurrent threads
# CONCURRENT_WORKERS = 50  # High concurrency scenario
```

### Changing Test Target

```python
TEST_URL = "https://httpbin.org/get"             # Default public internet target
# TEST_URL = "http://localhost:8000/api/health"  # Local test service
```

### Testing Specific Scenarios Only

```python
if __name__ == "__main__":
    print("\n[1/4] Sequential - no session")
    # test_without_session(...)             # Skip no-Session test

    print("\n[2/4] Sequential - with session")  # Test Session reuse only
    test_with_session(TEST_URL, NUM_REQUESTS)
    # ...
```

Run after modification:

```bash
python bench/bench_requests.py
```

## Dependencies

- `requests`
