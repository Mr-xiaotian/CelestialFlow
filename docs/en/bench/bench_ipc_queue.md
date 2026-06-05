# bench_ipc_queue.py Benchmark Notes

> 📅 Last Updated: 2026/04/22

## Objective

Compare the performance of several Python IPC mechanisms in a real cross-process scenario: `MPQueue`, `SimpleQueue`, `Pipe`, and `Manager().Queue`. The goal is to support queue selection for CelestialFlow's former multiprocessing mode.

## Test Cases

| Mechanism | Description | Supported Topology |
|-----------|-------------|--------------------|
| `MPQueue` | Standard multiprocessing queue | SPSC |
| `SimpleQueue` | Lock-free simplified queue | SPSC |
| `Pipe` | Bidirectional or unidirectional pipe | SPSC |
| `Manager().Queue` | Queue backed by a Manager server process | SPSC |

- **Scale**: `COUNT = 100_000`, `REPEAT = 3`
- **Payload modes**: `int` (8 bytes), `small` (~16 bytes), `medium` (~144 bytes), `large` (~4104 bytes)
- **Validation**: data integrity is checked via a checksum to detect loss or corruption

## Key Implementation

- `producer_queue` / `consumer_queue`: use the sentinel object `_SENTINEL = None` to mark end of stream.
- `producer_pipe` / `consumer_pipe`: explicitly call `conn.close()` to prevent handle leaks.
- `expected_checksum`: parse the payload mode and compute the expected checksum.

## Potential Issues

1. **Pipe handle leaks**: if the producer or consumer does not close its end correctly, child processes on Windows may fail to exit or leak handles.
2. **Manager server bottleneck**: with `Manager().Queue`, all traffic must be forwarded through the Manager server process, which becomes a single bottleneck under load.
3. **Large-payload copy cost**: in `large` mode, each payload is about 4 KB, so 100k transfers imply roughly 400 MB of copying; this measures memory bandwidth more than queue mechanics.
4. **Windows `spawn` serialization overhead**: every payload is transferred via pickle between parent and child processes, so serialization and deserialization can dominate for large objects.

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10, spawn mode, `COUNT=100,000`, `REPEAT=3`, payload=`int` (8 bytes)

| Mechanism | Average Time | Throughput | Relative to MPQueue |
|-----------|--------------|------------|---------------------|
| **MPQueue** | 1.328s | 75,277 items/s | 1.00x |
| **SimpleQueue** | 1.099s | 90,962 items/s | 1.21x |
| **Pipe** | 1.006s | 99,358 items/s | 1.32x |
| **Manager().Queue** | 7.884s | 12,684 items/s | 0.17x |

**Key takeaways**:
- **Pipe is fastest**: 32% faster than MPQueue and does not require a queue abstraction layer.
- **SimpleQueue is second**: its lock-free implementation is 21% faster than MPQueue, but it only supports single-producer single-consumer.
- **Manager().Queue is slowest**: only 17% of MPQueue throughput because the Manager server becomes the hard bottleneck.
- In multiprocessing-style queue selection, Pipe and SimpleQueue are the best choices when the topology allows them.

## How to Run

```bash
python bench/bench_ipc_queue.py
```

## Parameter Tuning

### Change the Test Scale and Payload Mode

Adjust the global settings near the top of `bench/bench_ipc_queue.py`:

```python
COUNT = 10_000       # Fewer iterations for quick verification
# COUNT = 1_000_000  # Large-scale stress test

REPEAT = 1           # Run only one round for quick validation
# REPEAT = 5         # More rounds for more stable statistics

PAYLOAD_MODE = "small"  # Options: int / small / medium / large
```

### Test Only Specific IPC Mechanisms

Select cases in `main()`:

```python
def main() -> None:
    # run_queue_case(name="MPQueue", ...)   # Skip MPQueue
    # run_queue_case(name="SimpleQueue", ...)
    run_queue_case(name="Pipe", ...)          # Only test Pipe
    # run_queue_case(name="Manager().Queue", ...)
```

Run again after modification:

```bash
python bench/bench_ipc_queue.py
```

## Dependencies

- `bench_utils.summarize`
