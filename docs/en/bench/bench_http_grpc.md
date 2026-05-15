# bench_http_grpc.py Benchmark Documentation

> 📅 Last Updated: 2026/05/09

## Objective

Quantitatively compare performance overhead of the CelestialTree event tracking system under different transport protocols (disabled / HTTP / gRPC), helping users make trade-offs between high-precision tracking and minimum latency.

## Test Cases

| Scenario | Description |
|----------|-------------|
| `bench_no_ctree` | CelestialTree completely disabled, used as baseline |
| `bench_http_ctree` | Events reported to CelestialTree via HTTP |
| `bench_grpc_ctree` | Events reported to CelestialTree via gRPC |

- **Graph structure**: Simple `TaskSplitter -> TaskStage` chain
- **Task**: `no_op` identity function (processing `range(1e4)`)
- **Configuration**: `stage_mode="thread"`, `execution_mode="thread"`, `max_workers=50`

## Key Configuration

- `ctree_host`, `ctree_http_port`, `ctree_grpc_port` loaded from `.env`

## Potential Issues

1. **CelestialTree service not running**: In HTTP/gRPC scenarios, if the server is unavailable, tests will throw a connection exception directly.
2. **Network latency dominates results**: Since the task is `no_op` (near-zero computation), measured time differences come almost entirely from event reporting network RTT, and do not reflect the true proportion in CPU-intensive scenarios.
3. **HTTP connections not reused**: The current implementation may create a new HTTP connection for each event report; using a connection pool (e.g., `requests.Session`) would significantly improve HTTP performance.
4. **gRPC cold start**: The first gRPC call requires TLS/handshake negotiation, which may manifest as higher latency in short tasks.

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10, TaskSplitter -> TaskStage chain, processing `range(1e4)`
> External service: Local CelestialTree (HTTP + gRPC)

| Scenario | Duration | Overhead vs Baseline |
|----------|----------|---------------------|
| **no ctree** (baseline) | 4.14s | -- |
| **http ctree** | 9.46s | +129% |
| **grpc ctree** | 9.25s | +124% |

**Key Conclusions**:
- HTTP and gRPC performance are nearly identical in this scenario (difference < 2%)
- Event tracking introduces approximately **2.3x** total duration increase (4.14s -> 9.3s)
- Since the task is `no_op` (zero computation), the overhead ratio is amplified; in CPU-intensive tasks, this ratio would decrease significantly
- gRPC did not show a clear advantage, likely because local network RTT is very low and HTTP connection reuse narrows the gap

## How to Run

```bash
python bench/bench_http_grpc.py
```

## Dependencies

- `celestialflow` (`TaskChain`, `TaskSplitter`, `TaskStage`)
- `python-dotenv`
- External services: CelestialTree (HTTP port + gRPC port)
