# bench_ipc_queue.py Benchmark Documentation

> 📅 Last Updated: 2026/04/22

## Objective

Compare performance of multiple Python IPC (inter-process communication) mechanisms in real cross-process scenarios: MPQueue, SimpleQueue, Pipe, Manager().Queue. Providing data support for CelestialFlow's queue selection in multi-process mode.

## Test Cases

| Mechanism | Description | Topology Support |
|-----------|-------------|-----------------|
| `MPQueue` | Standard multiprocessing queue | SPSC |
| `SimpleQueue` | Lock-free simplified queue | SPSC |
| `Pipe` | Bidirectional/unidirectional pipe | SPSC |
| `Manager().Queue` | Manager server-based queue | SPSC |

- **Scale**: `COUNT = 100_000`, `REPEAT = 3`
- **Payload modes**: `int` (8 bytes), `small` (~16 bytes), `medium` (~144 bytes), `large` (~4104 bytes)
- **Verification**: Data integrity verified via checksum (no loss, no corruption)

## Key Implementation

- `producer_queue` / `consumer_queue`: Use sentinel object `_SENTINEL = None` to signal end of stream
- `producer_pipe` / `consumer_pipe`: Explicit `conn.close()` to prevent handle leaks
- `expected_checksum`: Computes expected checksum based on payload mode

## Potential Issues

1. **Pipe handle leak**: If consumer/producer does not properly close connections, it may cause child processes to fail to exit or handle exhaustion on Windows.
2. **`Manager().Queue` server bottleneck**: All data must be forwarded through the Manager server process; when producer/consumer concurrency is high, the server process becomes a single point of bottleneck.
3. **Large payload memory copying**: In `large` mode, each payload is ~4KB; 100k transfers means ~400MB of data copying, primarily testing memory bandwidth rather than the queue itself.
4. **Windows `spawn` serialization overhead**: All payloads must be transmitted between parent and child processes via pickle; serialization/deserialization time dominates for large objects.

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10, spawn mode, COUNT=100,000, REPEAT=3, payload=int (8 bytes)

| Mechanism | Average Duration | Throughput | Relative to MPQueue |
|-----------|-----------------|------------|---------------------|
| **MPQueue** | 1.328s | 75,277 items/s | 1.00x |
| **SimpleQueue** | 1.099s | 90,962 items/s | 1.21x |
| **Pipe** | 1.006s | 99,358 items/s | 1.32x |
| **Manager().Queue** | 7.884s | 12,684 items/s | 0.17x |

**Key Conclusions**:
- **Pipe is fastest**: 32% faster than MPQueue, with no queue abstraction layer needed
- **SimpleQueue is second**: Lock-free implementation, 21% faster than MPQueue, but only supports single-producer single-consumer
- **Manager().Queue is slowest**: Only 17% of MPQueue throughput; the Manager server process is the absolute bottleneck
- For CelestialFlow's multi-process queue selection, Pipe and SimpleQueue are optimal for high-throughput scenarios (if topology allows)

## How to Run

```bash
python bench/bench_ipc_queue.py
```

## Dependencies

- `bench_utils.summarize`
