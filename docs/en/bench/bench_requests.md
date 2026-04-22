# bench_requests.py Benchmark Documentation

## Objective

Quantitatively compare HTTP request performance of the `requests` library under different usage patterns: whether to use Session, whether to use concurrency, and Session sharing granularity. Provides optimization guidance for HTTP-communicating modules in CelestialFlow (Reporter, CelestialTree HTTP client).

## Test Cases

| Scenario | Session Usage | Concurrency |
|----------|--------------|-------------|
| Sequential - no session | New `requests.get()` each time | None |
| Sequential - with session | Reuse a single `Session` | None |
| Concurrent - no session | New `requests.get()` each time | 10 threads |
| Concurrent - per-thread session | Independent `Session` per thread | 10 threads |

- **Target URL**: `https://httpbin.org/get`
- **Number of requests**: `NUM_REQUESTS = 50`
- **Timeout**: `TIMEOUT = 30`

## Key Metrics

Outputs mean, median, stdev, min, and max (in milliseconds) for each group.

## Potential Issues

1. **Network fluctuation**: The target `httpbin.org` is on the public internet. Latency is affected by local network quality and international link conditions, so single-run results are not reproducible.
2. **Connection pool not warmed up**: The `requests.Session` connection pool establishes TCP/TLS connections on the first request. The first few requests may take significantly longer than subsequent ones.
3. **GIL limitation**: Threads in `ThreadPoolExecutor` are constrained by the Python GIL. CPU-intensive parts of `requests` (such as TLS handshake, JSON parsing) cannot truly run in parallel.
4. **httpbin rate limiting**: Frequent testing may trigger httpbin's rate limiter, resulting in 429 responses or connection resets.

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10, target https://httpbin.org/get, 50 requests, 10 concurrent threads

| Scenario | Average | Median | Stdev | Min | Max |
|----------|---------|--------|-------|-----|-----|
| **Sequential - no session** | 1144.1 ms | 1059.7 ms | 169.0 ms | 991.9 ms | 1680.1 ms |
| **Sequential - with session** | **274.7 ms** | **166.8 ms** | 204.5 ms | 162.1 ms | 1047.7 ms |
| **Concurrent - no session** | 1795.4 ms | 1738.8 ms | 417.9 ms | 1180.0 ms | 2837.8 ms |
| **Concurrent - per-thread session** | 1734.6 ms | 1738.8 ms | 215.9 ms | 1154.4 ms | 2407.4 ms |

**Key Conclusions**:
- **Session reuse is the biggest performance gain**: In sequential requests, using Session is **4.2x** faster than without (1144ms -> 275ms), by avoiding repeated TCP/TLS handshakes
- **Concurrency did not provide additional benefit**: In this test, the concurrent scenario (10 threads) actually had a higher average than sequential, because httpbin's public network latency and server-side processing became the bottleneck — client-side concurrency cannot break through
- **Per-thread Session is meaningless**: Under concurrency, per-thread Session performs nearly identically to no Session, as the connection reuse advantage is offset by connection pool contention under high concurrency
- Implications for CelestialFlow: Reporter and CelestialTree HTTP clients should globally reuse `requests.Session`

## How to Run

```bash
python bench/bench_requests.py
```

## Dependencies

- `requests`
