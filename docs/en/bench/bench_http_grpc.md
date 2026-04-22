# bench_http_grpc.py Benchmark Documentation

> 📅 Last updated: 2026/04/22

## Objective

Quantitatively compare the performance overhead of the CelestialTree event tracing system under different transport protocols (disabled / HTTP / gRPC), helping users make trade-offs between high-precision tracing and minimum latency.

## Test Cases

| Scenario | Description |
|----------|-------------|
| `bench_no_ctree` | CelestialTree completely disabled, serves as baseline |
| `bench_http_ctree` | Events reported to CelestialTree via HTTP |
| `bench_grpc_ctree` | Events reported to CelestialTree via gRPC |

- **Graph structure**: Simple `TaskSplitter -> TaskStage` chain
- **Task**: `no_op` identity function (processing `range(1e4)`)
- **Configuration**: `stage_mode="process"`, `execution_mode="thread"`, `max_workers=50`

## Key Configuration

- `ctree_host`, `ctree_http_port`, `ctree_grpc_port` loaded from `.env`

## Potential Issues

1. **CelestialTree service not running**: In HTTP/gRPC scenarios, if the server is unavailable, the test will throw a connection exception directly.
2. **Network latency dominates results**: Since the task is `no_op` (virtually zero computation), the measured time difference is almost entirely from network RTT of event reporting, and does not reflect the true proportion in CPU-intensive scenarios.
3. **HTTP connections not reused**: The current implementation may create a new HTTP connection for each event report. Using a connection pool (e.g., `requests.Session`) would significantly improve HTTP performance.
4. **gRPC cold start**: The first gRPC call requires TLS/handshake negotiation, which may manifest as higher latency in short tasks.

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10, TaskSplitter -> TaskStage chain, processing `range(1e4)`
> External services: Local CelestialTree (HTTP + gRPC)

| Scenario | Duration | Overhead vs Baseline |
|----------|----------|---------------------|
| **no ctree** (baseline) | 4.14s | — |
| **http ctree** | 9.46s | +129% |
| **grpc ctree** | 9.25s | +124% |

**Key Conclusions**:
- HTTP and gRPC perform nearly identically in this scenario (difference < 2%)
- Event tracing introduces approximately **2.3x** total time increase (4.14s -> 9.3s)
- Since the task is `no_op` (zero computation), the overhead ratio is amplified; in CPU-intensive tasks, this ratio would decrease significantly
- gRPC did not show a clear advantage, likely because local network RTT is extremely low and HTTP connection reuse narrows the gap

## How to Run

```bash
python bench/bench_http_grpc.py
```

## Dependencies

- `celestialflow` (`TaskChain`, `TaskSplitter`, `TaskStage`)
- `python-dotenv`
- External services: CelestialTree (HTTP port + gRPC port)
