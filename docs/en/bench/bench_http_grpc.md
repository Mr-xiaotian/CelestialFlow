# bench_http_grpc.py Benchmark Notes

> 📅 Last Updated: 2026/05/09

## Objective

Quantify the performance overhead of the CelestialTree event-tracking system under different transport modes (disabled / HTTP / gRPC), helping users balance high-fidelity tracing against minimal latency.

## Test Cases

| Scenario | Description |
|----------|-------------|
| `bench_no_ctree` | CelestialTree fully disabled, used as the baseline |
| `bench_http_ctree` | Report events to CelestialTree via HTTP |
| `bench_grpc_ctree` | Report events to CelestialTree via gRPC |

- **Graph topology**: a simple `TaskSplitter -> TaskStage` chain.
- **Task**: `no_op`, processing `range(1e4)`.
- **Configuration**: `stage_mode="thread"`, `execution_mode="thread"`, `max_workers=50`.

## Key Configuration

- `ctree_host`, `ctree_http_port`, and `ctree_grpc_port` are loaded from `.env`.

## Potential Issues

1. **CelestialTree service not running**: if the HTTP or gRPC server is unavailable, the benchmark fails immediately with a connection error.
2. **Network RTT dominates**: because the task is `no_op` with almost zero compute cost, most of the measured difference comes from event-reporting round trips rather than task execution itself.
3. **HTTP connections not reused**: the current implementation may create a new HTTP connection for each event. If connection pooling such as `requests.Session` is used, HTTP performance can improve substantially.
4. **gRPC cold start**: the first gRPC request needs handshake setup, which can look expensive in short-running jobs.

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10, `TaskSplitter -> TaskStage`, processing `range(1e4)`
> External service: local CelestialTree (HTTP + gRPC)

| Scenario | Time | Overhead vs Baseline |
|----------|------|----------------------|
| **no ctree** (baseline) | 4.14s | — |
| **http ctree** | 9.46s | +129% |
| **grpc ctree** | 9.25s | +124% |

**Key takeaways**:
- HTTP and gRPC are almost identical in this scenario, with less than 2% difference.
- Event tracing increases total runtime by about **2.3x** (`4.14s -> 9.3s`).
- Because the task is a near-zero-cost `no_op`, the overhead ratio is amplified; for CPU-intensive jobs, the relative overhead should be much lower.
- gRPC shows no obvious advantage here, likely because local-network RTT is already very small and HTTP could narrow the gap further once connection reuse is enabled.

## How to Run

```bash
python bench/bench_http_grpc.py
```

## Parameter Tuning

### Test Only Specific Transport Modes

Comment out unneeded cases in `main()`:

```python
def main():
    bench_no_ctree()       # Only test the baseline
    # bench_http_ctree()   # Skip HTTP
    # bench_grpc_ctree()   # Skip gRPC
```

### Adjust Task Scale

`TaskSplitter` expands `range(1e4)`, which you can shrink or enlarge:

```python
# Quick verification
range(100)

# High-load test
range(100_000)
```

### Adjust the Number of Workers

```python
# Change inside the function
max_workers=20   # Lower concurrency
# max_workers=100  # Higher concurrency
```

Run again after modification:

```bash
python bench/bench_http_grpc.py
```

## Dependencies

- `celestialflow` (`TaskChain`, `TaskSplitter`, `TaskStage`)
- `python-dotenv`
- External service: CelestialTree (HTTP port + gRPC port)
