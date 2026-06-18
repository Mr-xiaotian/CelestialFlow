# bench_http_grpc.py Benchmark Guide

> 📅 Last Updated: 2026/06/18

## Objective

Quantitatively compare the performance overhead of the CelestialTree event tracking system under different transport protocols (disabled / HTTP / gRPC), helping users make trade-offs between high-precision tracing and minimal latency.

## Test Content

| Scenario | Description |
|------|------|
| `bench_no_ctree` | CelestialTree completely disabled, as baseline |
| `bench_http_ctree` | Report events to CelestialTree via HTTP |
| `bench_grpc_ctree` | Report events to CelestialTree via gRPC |

- **Graph structure**: Simple chain of `TaskSplitter → TaskStage`
- **Tasks**: `no_op` identity function (processing `range(1e4)`)
- **Config**: `stage_mode="thread"`, `execution_mode="thread"`, `max_workers=50`

## Key Configuration

- `ctree_host`, `ctree_http_port`, `ctree_grpc_port` read from `.env`

## Potential Issues

1. **CelestialTree service not running**: Under HTTP/gRPC scenarios, if the server is unavailable, the test will directly throw a connection exception.
2. **Network latency dominates results**: Since tasks are `no_op` (near-zero computation), measured time differences are almost entirely from network RTT of event reporting and cannot reflect real proportions in CPU-intensive scenarios.
3. **HTTP connections not reused**: The current implementation may create a new HTTP connection for each event report; using a connection pool (e.g., `requests.Session`) would significantly improve HTTP performance.
4. **gRPC cold start**: gRPC's first call requires TLS/handshake negotiation, which may manifest as higher latency in short tasks.

## Benchmark Results (Measured)

### Historical Results - Local CelestialTree (date not recorded)

> Environment: Windows, Python 3.10, TaskSplitter → TaskStage chain, processing `range(1e4)`
> External Service: local CelestialTree (HTTP + gRPC)

| Scenario | Time | Overhead vs Baseline |
|------|------|------------------|
| **no ctree** (baseline) | 4.14s | — |
| **http ctree** | 9.46s | +129% |
| **grpc ctree** | 9.25s | +124% |

**Key Takeaways**:
- HTTP and gRPC perform nearly identically in this scenario (difference < 2%)
- Event tracking introduces approximately **2.3x** total time increase (4.14s → 9.3s)
- Since tasks are `no_op` (zero computation), the overhead ratio is amplified; in CPU-intensive tasks, this ratio would be significantly lower
- gRPC did not show a clear advantage, likely because local network RTT is extremely low and HTTP connection reuse narrows the gap

### 2026/06/16 - Not rerun this round (external service unavailable)

> Note: When checking `127.0.0.1:7777` and `127.0.0.1:7778`, CelestialTree's HTTP / gRPC ports were both unavailable

- `bench_http_grpc.py` depends on a local CelestialTree service, so no new timing data is recorded this round
- Historical results can still be used as a reference for protocol overhead magnitude, but to obtain comparable data for the current version, the corresponding HTTP and gRPC server instances must be started first

## How to Run

```bash
python bench/bench_http_grpc.py
```

## Parameter Tuning

### Testing Specific Transport Modes Only

In `main()`, comment out unneeded modes:

```python
def main():
    bench_no_ctree()       # Test baseline only
    # bench_http_ctree()   # Skip HTTP
    # bench_grpc_ctree()   # Skip gRPC
```

### Adjusting Task Scale

Expanded from `range(1e4)` by `TaskSplitter`; can be modified larger or smaller:

```python
# Quick validation (few tasks)
range(100)

# High-load test
range(100_000)
```

### Adjusting Concurrent Worker Count

```python
# Modify inside the function
max_workers=20   # Reduce concurrency
# max_workers=100  # Increase concurrency
```

Run after modification:

```bash
python bench/bench_http_grpc.py
```

## Dependencies

- `celestialflow` (`TaskChain`, `TaskSplitter`, `TaskStage`)
- `celestialtree` (requires additional installation; available via `uv sync --group dev` in the source repository)
- `python-dotenv`
- External Service: CelestialTree (HTTP port + gRPC port)
