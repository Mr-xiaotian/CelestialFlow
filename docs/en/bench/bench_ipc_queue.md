# bench/bench_ipc_queue.py

> 📅 Last Updated: 2026/10/30

## Objective

Compare the performance of various Python IPC (Inter-Process Communication) mechanisms in real cross-process scenarios: MPQueue, SimpleQueue, Pipe, Manager().Queue. Provide data to support queue selection for CelestialFlow's multiprocessing mode.

> **Note**: The framework has removed `process` graph mode and its internal multiprocessing dependency (see change log), so the results of this script no longer reflect the framework's current internal behavior; they serve only as a historical reference for cross-process IPC performance.

## Test Content

| Mechanism | Description | Topology Support |
|------|------|----------|
| `MPQueue` | `multiprocessing.Queue`, with a feeder thread and locks | SPSC |
| `SimpleQueue` | `multiprocessing.SimpleQueue`, a simplified queue that writes directly to a pipe (no feeder thread, does not support `qsize`) | SPSC |
| `Pipe` | `Pipe(duplex=False)` unidirectional pipe | SPSC |
| `Manager().Queue` | Queue based on a Manager server process | SPSC |

- **Scale**: `COUNT = 100_000`, `REPEAT = 3`
- **Payload modes**: `int` (Python integer objects), `small` (`f"item-{i}"`), `medium` (`f"{i}-"` + 128 `x`s), `large` (`f"{i}-"` + 4096 `x`s)
- **Verification**: The consumer sends `(consumed, checksum)` back through a result queue; `consumed` must equal `COUNT` and `checksum` must equal `expected_checksum()` (an arithmetic series sum for `int` mode, the sum of payload lengths for the other modes), otherwise a `RuntimeError` is raised
- **Start method**: `__main__` attempts `set_start_method("spawn")` and ignores `RuntimeError` if it has already been set

## Key Implementation

- `producer_queue` / `consumer_queue`: Use sentinel object `_SENTINEL = None` to signal end of stream
- `producer_pipe` / `consumer_pipe`: Explicit `conn.close()` inside `try/finally` to prevent handle leaks; the parent process immediately closes its own handles at both ends after starting the two child processes
- `expected_checksum`: Parse payload mode to compute expected checksum
- `run_queue_case` / `run_pipe_case` / `run_manager_queue_case`: Run `REPEAT` rounds per mechanism, verify each round, then hand off to `summarize()` to output mean / standard deviation / throughput

## Potential Issues

1. **Pipe handle leaks**: If consumer/producer do not properly close connections, child processes may fail to exit or handle exhaustion may occur on Windows.
2. **`Manager().Queue` server bottleneck**: All data must be forwarded through the Manager server process; when producer/consumer concurrency is high, the server process becomes a single-point bottleneck.
3. **Large payload memory copy**: In `large` mode, each payload is approximately 4KB; 100k transfers mean approximately 400MB of data copying, primarily testing memory bandwidth rather than the queue itself.
4. **Windows `spawn` serialization overhead**: All payloads must be transferred between parent and child processes via pickle; serialization/deserialization time for large objects will dominate.

## Benchmark Results (Measured)

> 🟢 The timing/throughput in the tables of this section are all historical measured data and cannot be verified from source code; manual confirmation is required.

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
- **SimpleQueue is second**: Simplified implementation without a feeder thread, 21% faster than MPQueue, but only supports single producer single consumer
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

- `bench_utils.summarize` (same-directory module; importing works when running `python bench/bench_ipc_queue.py` directly)
- Python standard library: `multiprocessing` (`Queue`, `SimpleQueue`, `Pipe`, `Manager`, `Process`, `set_start_method`)
