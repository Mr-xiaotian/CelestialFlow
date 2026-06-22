# bench_requests.py Benchmark Guide

> 📅 Last Updated: 2026/06/22

## Objective

Quantitatively compare the HTTP request performance of the `requests` library under different usage patterns: whether to use Session, whether to use concurrency, and Session sharing granularity. Provide optimization insights for CelestialFlow modules involving HTTP communication (Reporter, CelestialTree HTTP client).

## Test Content

| Scenario | Session Usage | Concurrency |
|------|-----------------|------|
| Sequential - no session | New `requests.get()` each time | None |
| Sequential - with session | Reuse single `Session` | None |
| Concurrent - no session | New `requests.get()` each time | 10 threads |
| Concurrent - per-thread session | Each thread has its own `Session` | 10 threads |

- **Default target URL**: `http://127.0.0.1:5005/api/pull_server_state`
- **Overridable via**: `--url` argument or `CELESTIALFLOW_BENCH_URL` environment variable
- **Request Count**: `NUM_REQUESTS = 50`
- **Timeout**: `TIMEOUT = 30`

## Key Metrics

Outputs mean, median, stdev, min, max (in milliseconds) for each group of requests.

## Potential Issues

1. **Default target is a local service**: The default URL is `http://127.0.0.1:5005/api/pull_server_state`. If you switch to a public target such as `httpbin.org`, latency is affected by network quality, making single-run results non-reproducible.
2. **Connection pool not warmed up**: `requests.Session`'s connection pool establishes TCP/TLS connections on the first request; the first few requests may have significantly higher latency than subsequent ones.
3. **GIL constraint**: Threads in `ThreadPoolExecutor` are constrained by Python's GIL; CPU-intensive parts of `requests` (e.g., TLS handshake, JSON parsing) cannot truly parallelize.
4. **Public target rate limiting**: If pointing at `httpbin.org` or similar public services, frequent testing may trigger rate limiting, returning 429 or connection resets.

## Benchmark Results (Measured)

### Historical Results - Public internet httpbin (date not recorded)

> Environment: Windows, Python 3.10, target https://httpbin.org/get, 50 requests, 10 concurrent threads

| Scenario | Mean | Median | Stdev | Min | Max |
|------|----------|--------|--------|--------|--------|
| **Sequential - no session** | 1144.1 ms | 1059.7 ms | 169.0 ms | 991.9 ms | 1680.1 ms |
| **Sequential - with session** | **274.7 ms** | **166.8 ms** | 204.5 ms | 162.1 ms | 1047.7 ms |
| **Concurrent - no session** | 1795.4 ms | 1738.8 ms | 417.9 ms | 1180.0 ms | 2837.8 ms |
| **Concurrent - per-thread session** | 1734.6 ms | 1738.8 ms | 215.9 ms | 1154.4 ms | 2407.4 ms |

**Key Takeaways**:
- **Session reuse provides the greatest benefit**: For sequential requests, using Session is **4.2x** faster than no Session (1144ms → 275ms), because repeated TCP/TLS handshakes are avoided
- **Concurrency did not bring additional benefits**: In this test, the mean for concurrent scenarios (10 threads) was actually higher than serial, because httpbin's public network latency and server-side processing became the bottleneck, and client-side concurrency could not break through
- **Per-thread independent Session is pointless**: In concurrent scenarios, each thread having its own Session performed nearly identically to no Session, because connection reuse benefits are offset by connection pool contention under high concurrency
- Implication for CelestialFlow: Reporter and CelestialTree HTTP client should reuse `requests.Session` globally

### 2026/06/16 - Local TaskWebServer

> Environment: Windows, target `http://127.0.0.1:5005/api/pull_server_state`, 50 requests, 10 concurrent threads
> Note: This round's test is based on a corrected `bench_concurrent_with_session()` that now truly uses "one Session per thread"

| Scenario | Mean | Median | Stdev | Min | Max |
|------|----------|--------|--------|--------|--------|
| **Sequential - no session** | 20.7 ms | 20.6 ms | 11.6 ms | 5.5 ms | 64.7 ms |
| **Sequential - with session** | **5.8 ms** | **5.3 ms** | 3.1 ms | 4.5 ms | 26.6 ms |
| **Concurrent - no session** | 36.6 ms | 33.8 ms | 11.9 ms | 10.5 ms | 65.9 ms |
| **Concurrent - per-thread session** | 32.6 ms | 34.8 ms | 6.3 ms | 9.6 ms | 46.4 ms |

**Supplementary conclusions for this round**:
- On a stable local target, **sequential Session reuse yields a very clear benefit**, with average time dropping about **72%** (20.7ms → 5.8ms)
- In concurrent scenarios, **per-thread Session reuse** still beats concurrent no-Session, but the advantage is noticeably smaller than in the serial scenario, indicating that local interface processing and thread scheduling overhead have become the main components
- Compared with the old public-internet `httpbin` results, local results show less variance and are more suitable for code-level connection reuse comparisons
- The current script is better suited for validating HTTP client strategies against CelestialFlow's own web interfaces, rather than measuring public internet network quality

### 2026/06/16 - Local TaskWebServer (2nd retest)

> Environment: Windows, target `http://127.0.0.1:5005/api/pull_server_state`, 50 requests, 10 concurrent threads

| Scenario | Mean | Median | Stdev | Min | Max |
|------|----------|--------|--------|--------|--------|
| **Sequential - no session** | 16.0 ms | 13.1 ms | 10.1 ms | 5.7 ms | 33.0 ms |
| **Sequential - with session** | **6.0 ms** | **5.8 ms** | 1.8 ms | 4.0 ms | 17.3 ms |
| **Concurrent - no session** | 37.3 ms | 37.1 ms | 10.5 ms | 8.2 ms | 55.5 ms |
| **Concurrent - per-thread session** | 33.2 ms | 35.6 ms | 6.9 ms | 10.4 ms | 39.8 ms |

**Supplementary conclusions for this round**:
- In the serial scenario, `Session` reuse remains the most significant gain, with average time dropping about **62%** (16.0ms → 6.0ms)
- In the concurrent scenario, per-thread `Session` reuse still beats no-Session, but the gain is noticeably smaller than in the serial scenario, indicating that local interface processing and thread scheduling already account for the majority
- Compared with the same day's previous local results, overall means have slightly declined, showing that this benchmark remains sensitive to the server's load and local machine state at the time

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

```bash
python bench/bench_requests.py --url http://127.0.0.1:5005/api/pull_server_state
```

Or using an environment variable:

```bash
set CELESTIALFLOW_BENCH_URL=http://127.0.0.1:5005/api/pull_server_state
python bench/bench_requests.py
```

### Testing Specific Scenarios Only

Comment out unneeded calls in `if __name__ == "__main__":`:

```python
print("\n[1/4] Sequential - no session")
# print_stats("no session", bench_without_session(args.url, NUM_REQUESTS))

print("\n[2/4] Sequential - with session")
print_stats("with session", bench_with_session(args.url, NUM_REQUESTS))
```

## Dependencies

- `requests`
