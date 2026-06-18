# bench_ipc_queue.py Benchmark Guide

> 📅 Last Updated: 2026/06/16

## Objective

Compare the performance of various Python IPC (Inter-Process Communication) mechanisms in real cross-process scenarios: MPQueue, SimpleQueue, Pipe, Manager().Queue. Provide data to support queue selection for CelestialFlow's multiprocessing mode.

## Test Content

| Mechanism | Description | Topology Support |
|------|------|----------|
| `MPQueue` | Standard multiprocessing queue | SPSC |
| `SimpleQueue` | Lock-free simplified queue | SPSC |
| `Pipe` | Bidirectional/unidirectional pipe | SPSC |
| `Manager().Queue` | Manager-server-based queue | SPSC |

- **Scale**: `COUNT = 100_000`, `REPEAT = 3`
- **Payload modes**: `int` (8 bytes), `small` (~16 bytes), `medium` (~144 bytes), `large` (~4104 bytes)
- **Verification**: Data integrity verified via checksum (no loss, no corruption)

## Key Implementation

- `producer_queue` / `consumer_queue`: Use sentinel object `_SENTINEL = None` to signal end of stream
- `producer_pipe` / `consumer_pipe`: Explicit `conn.close()` to prevent handle leaks
- `expected_checksum`: Parse payload mode to compute expected checksum

## Potential Issues

1. **Pipe handle leaks**: If consumer/producer do not properly close connections, child processes may fail to exit or handle exhaustion may occur on Windows.
2. **`Manager().Queue` server bottleneck**: All data must be forwarded through the Manager server process; when producer/consumer concurrency is high, the server process becomes a single-point bottleneck.
3. **Large payload memory copy**: In `large` mode, each payload is approximately 4KB; 100k transfers mean approximately 400MB of data copying, primarily testing memory bandwidth rather than the queue itself.
4. **Windows `spawn` serialization overhead**: All payloads must be transferred between parent and child processes via pickle; serialization/deserialization time for large objects will dominate.

## Benchmark Results (Measured)

### Historical Results - Windows spawn int payload (date not recorded)

> Environment: Windows, Python 3.10, spawn mode, COUNT=100,000, REPEAT=3, payload=int (8 bytes)

| Mechanism | Average Time | Throughput | Relative to MPQueue |
|------|----------|--------|-------------|
| **MPQueue** | 1.328s | 75,277 items/s | 1.00x |
| **SimpleQueue** | 1.099s | 90,962 items/s | 1.21x |
| **Pipe** | 1.006s | 99,358 items/s | 1.32x |
| **Manager().Queue** | 7.884s | 12,684 items/s | 0.17x |

**Key Takeaways**:
- **Pipe is fastest**: 32% faster than MPQueue, and requires no queue abstraction layer
- **SimpleQueue is second**: Lock-free implementation, 21% faster than MPQueue, but only supports single producer single consumer
- **Manager().Queue is slowest**: Only 17% of MPQueue throughput; the Manager server process is the absolute bottleneck
- In CelestialFlow's multiprocessing queue selection, Pipe and SimpleQueue are the optimal solutions for high-throughput scenarios (if topology allows)

### 2026/06/16 - Windows spawn int payload retest

> Environment: Windows, COUNT=100,000, REPEAT=3, `PAYLOAD_MODE=int`

| Mechanism | Average Time | Throughput | Relative to MPQueue |
|------|----------|--------|-------------|
| **MPQueue** | 0.8434s | 118,563 items/s | 1.00x |
| **SimpleQueue** | 0.8417s | 118,806 items/s | 1.00x |
| **Pipe** | 0.7699s | 129,881 items/s | 1.09x |
| **Manager().Queue** | 4.5027s | 22,209 items/s | 0.19x |

**Supplementary conclusions for this round**:
- `Pipe` remains the fastest option on the current machine, but the gap with `MPQueue` / `SimpleQueue` has narrowed to about **9%**
- `SimpleQueue` and `MPQueue` are nearly tied this round, indicating that both already have very low overhead for `int` payloads
- `Manager().Queue` remains significantly behind, with throughput only about one-sixth of the fastest option

## How to Run

```bash
python bench/bench_ipc_queue.py
```

## Parameter Tuning

### Adjusting Test Scale and Payload Mode

Adjust global configuration at the top of `bench/bench_ipc_queue.py`:

```python
COUNT = 10_000       # Reduce iterations for quick validation
# COUNT = 1_000_000  # Large scale stress test

REPEAT = 1           # Run only 1 round for quick validation
# REPEAT = 5         # Increase rounds for higher statistical confidence

PAYLOAD_MODE = "small"  # Options: int / small / medium / large
```

### Testing Specific IPC Mechanisms Only

In `main()`, selectively run:

```python
def main() -> None:
    # run_queue_case(name="MPQueue", ...)   # Comment out MPQueue
    # run_queue_case(name="SimpleQueue", ...)
    run_pipe_case(...)                        # Test Pipe only
    # run_manager_queue_case(...)
```

Run after modification:

```bash
python bench/bench_ipc_queue.py
```

## Dependencies

- `bench_utils.summarize`
