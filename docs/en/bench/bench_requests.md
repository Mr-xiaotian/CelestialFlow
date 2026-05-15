# bench_requests.py Benchmark Documentation

> 📅 Last Updated: 2026/04/22

## Objective

Quantitatively compare HTTP request performance of the `requests` library under different usage patterns: with or without Session, with or without concurrency, and Session sharing granularity. Providing optimization guidance for HTTP communication modules in CelestialFlow (Reporter, CelestialTree HTTP client).

## Test Cases

| Scenario | Session Usage | Concurrency |
|----------|--------------|-------------|
| Sequential - no session | New `requests.get()` each time | None |
| Sequential - with session | Reuse a single `Session` | None |
| Concurrent - no session | New `requests.get()` each time | 10 threads |
| Concurrent - per-thread session | Independent `Session` per thread | 10 threads |

- **Target URL**: `https://httpbin.org/get`
- **Request count**: `NUM_REQUESTS = 50`
- **Timeout**: `TIMEOUT = 30`

## Key Metrics

Outputs mean, median, stdev, min, max (in milliseconds) for each group of requests.

## Potential Issues

1. **Network fluctuation**: Target `httpbin.org` is on the public internet; latency is affected by local network and international link quality, making single-run results non-reproducible.
2. **Connection pool not warmed up**: `requests.Session`'s connection pool establishes TCP/TLS connections on the first request; the first few requests may have significantly higher latency than subsequent ones.
3. **GIL limitation**: Threads in `ThreadPoolExecutor` are constrained by Python's GIL; CPU-intensive parts of `requests` (e.g., TLS handshake, JSON parsing) cannot truly parallelize.
4. **httpbin rate limiting**: Frequent testing may trigger httpbin's rate limit, returning 429 or connection reset.

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10, target https://httpbin.org/get, 50 requests, 10 concurrent threads

| Scenario | Mean | Median | Stdev | Min | Max |
|----------|------|--------|-------|-----|-----|
| **Sequential - no session** | 1144.1 ms | 1059.7 ms | 169.0 ms | 991.9 ms | 1680.1 ms |
| **Sequential - with session** | **274.7 ms** | **166.8 ms** | 204.5 ms | 162.1 ms | 1047.7 ms |
| **Concurrent - no session** | 1795.4 ms | 1738.8 ms | 417.9 ms | 1180.0 ms | 2837.8 ms |
| **Concurrent - per-thread session** | 1734.6 ms | 1738.8 ms | 215.9 ms | 1154.4 ms | 2407.4 ms |

**Key Conclusions**:
- **Session reuse is the biggest performance gain**: In sequential requests, using Session is **4.2x** faster than without (1144ms -> 275ms), by avoiding repeated TCP/TLS handshakes
- **Concurrency did not provide additional benefit**: In this test, the concurrent scenario (10 threads) actually had a higher mean than sequential, because httpbin's public network latency and server-side processing became the bottleneck, and client-side concurrency could not break through
- **Per-thread independent Session is meaningless**: In concurrent scenarios, per-thread Session performed nearly identical to no Session, as the connection reuse advantage is offset by connection pool contention under high concurrency
- Implications for CelestialFlow: Reporter and CelestialTree HTTP clients should globally reuse `requests.Session`

## How to Run

```bash
python bench/bench_requests.py
```

## Dependencies

- `requests`
