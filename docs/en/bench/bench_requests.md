# bench_requests.py Benchmark Notes

> 📅 Last Updated: 2026/04/22

## Objective

Quantify HTTP request performance with the `requests` library under different usage patterns: with or without Session reuse, with or without concurrency, and with different Session-sharing strategies. The results help optimize CelestialFlow modules that perform HTTP communication, such as Reporter and the CelestialTree HTTP client.

## Test Cases

| Scenario | Session Strategy | Concurrency |
|----------|------------------|-------------|
| Sequential - no session | New `requests.get()` each time | No |
| Sequential - with session | Reuse one `Session` | No |
| Concurrent - no session | New `requests.get()` each time | 10 threads |
| Concurrent - per-thread session | One `Session` per thread | 10 threads |

- **Target URL**: `https://httpbin.org/get`
- **Request count**: `NUM_REQUESTS = 50`
- **Timeout**: `TIMEOUT = 30`

## Key Metrics

The benchmark prints mean, median, stdev, min, and max in milliseconds for each scenario.

## Potential Issues

1. **Network fluctuation**: `httpbin.org` is a public endpoint, so latency depends heavily on the local network and international routing. A single run is not strictly reproducible.
2. **Connection pool warm-up**: `requests.Session` creates its TCP/TLS connection on the first request, so the first few calls can be significantly slower than later ones.
3. **GIL limitations**: threads in `ThreadPoolExecutor` are still subject to the Python GIL, so CPU-heavy parts of `requests` such as TLS handling and JSON parsing do not run fully in parallel.
4. **httpbin rate limiting**: frequent benchmarking may trigger rate limits, returning 429 or resetting connections.

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10, target `https://httpbin.org/get`, 50 requests, 10 worker threads

| Scenario | Mean | Median | Std Dev | Min | Max |
|----------|------|--------|---------|-----|-----|
| **Sequential - no session** | 1144.1 ms | 1059.7 ms | 169.0 ms | 991.9 ms | 1680.1 ms |
| **Sequential - with session** | **274.7 ms** | **166.8 ms** | 204.5 ms | 162.1 ms | 1047.7 ms |
| **Concurrent - no session** | 1795.4 ms | 1738.8 ms | 417.9 ms | 1180.0 ms | 2837.8 ms |
| **Concurrent - per-thread session** | 1734.6 ms | 1738.8 ms | 215.9 ms | 1154.4 ms | 2407.4 ms |

**Key takeaways**:
- **Session reuse is the biggest win**: for sequential requests, using a Session is about **4.2x** faster (`1144ms -> 275ms`) because it avoids repeated TCP/TLS handshakes.
- **Concurrency did not help here**: the 10-thread scenarios are actually slower on average because public-network latency and server-side processing dominate.
- **Per-thread Session brings no real benefit**: under concurrency, one Session per thread performs nearly the same as no Session because connection reuse is offset by connection-pool competition.
- For CelestialFlow, Reporter and the CelestialTree HTTP client should reuse a global `requests.Session`.

## How to Run

```bash
python bench/bench_requests.py
```

## Parameter Tuning

### Change Request Count and Concurrency

Modify the configuration near the top of `bench/bench_requests.py`:

```python
NUM_REQUESTS = 10          # Fewer requests for quick verification
# NUM_REQUESTS = 200       # More requests to observe steady-state performance after pool warm-up

CONCURRENT_WORKERS = 4     # Fewer worker threads
# CONCURRENT_WORKERS = 50  # High-concurrency scenario
```

### Change the Target Service

```python
TEST_URL = "https://httpbin.org/get"             # Default public endpoint
# TEST_URL = "http://localhost:8000/api/health"  # Local test service
```

### Test Only Specific Scenarios

```python
if __name__ == "__main__":
    print("\n[1/4] Sequential - no session")
    # test_without_session(...)             # Skip the no-session case

    print("\n[2/4] Sequential - with session")  # Only test Session reuse
    test_with_session(TEST_URL, NUM_REQUESTS)
    # ...
```

Run again after modification:

```bash
python bench/bench_requests.py
```

## Dependencies

- `requests`
