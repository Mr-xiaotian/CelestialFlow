# bench_mpqueue_vs_shared_memory.py Benchmark Notes

> 📅 Last Updated: 2026/04/22

## Objective

Under more complex producer-consumer topologies (SPSC, MPSC, SPMC), compare `multiprocessing.Queue` against a custom ring buffer built on `shared_memory`. The goal is to gather deeper IPC data for high-throughput CelestialFlow scenarios.

## Test Cases

| Topology | Producers | Consumers | Description |
|----------|-----------|-----------|-------------|
| SPSC | 1 | 1 | Single producer, single consumer |
| MPSC | 4 | 1 | Multi-producer, single consumer |
| SPMC | 1 | 4 | Single producer, multi-consumer |

- **Scale**: `COUNT = 100_000`, `REPEAT = 3`
- **SharedMemory config**: `SLOT_COUNT = 1024`, each slot stores a 4-byte length prefix plus payload
- **Synchronization**: `Lock` for read/write index protection, `Semaphore` for empty/full slot counting

## Key Implementation

### SharedMemory Ring Protocol
1. **Producer**: `empty_slots.acquire()` -> write payload under `write_lock` -> `full_slots.release()`.
2. **Consumer**: `full_slots.acquire()` -> read payload under `read_lock` -> `empty_slots.release()`.
3. **Key design**: `full_slots.release()` happens outside the lock to maximize concurrency.

## Potential Issues

1. **SharedMemory lifecycle management**: `shm.unlink()` can only run after all processes have closed the segment. If a child exits abnormally without `shm.close()`, unlinking may fail or leak memory.
2. **Insufficient `slot_size`**: if `payload_max_bytes(mode)` is underestimated or the real payload exceeds `slot_size - 4`, `producer_shm_ring` raises `RuntimeError`.
3. **MPSC write contention**: although `write_lock` protects index updates and writes, multiple producers still serialize their writes, which can erase SharedMemory's advantage in MPSC mode.
4. **Windows shared-memory naming**: `SharedMemory(name=shm_name)` uses the global namespace on Windows, so name collisions between benchmark instances can cause unpredictable behavior.

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10, spawn mode, `COUNT=100,000`, `REPEAT=3`, payload=`int` (8 bytes), `SLOT_COUNT=1024`

### SPSC (Single Producer, Single Consumer)

| Mechanism | Average Time | Throughput | Winner |
|-----------|--------------|------------|--------|
| MPQueue | 1.281s | 78,066 items/s | — |
| SharedMemory ring | **0.878s** | **113,853 items/s** | ✅ **SharedMemory** (1.46x faster) |

### MPSC (4 Producers, 1 Consumer)

| Mechanism | Average Time | Throughput | Winner |
|-----------|--------------|------------|--------|
| MPQueue | **1.618s** | **61,787 items/s** | ✅ **MPQueue** (1.18x faster) |
| SharedMemory ring | 1.905s | 52,487 items/s | — |

### SPMC (1 Producer, 4 Consumers)

| Mechanism | Average Time | Throughput | Winner |
|-----------|--------------|------------|--------|
| MPQueue | 2.851s | 35,070 items/s | — |
| SharedMemory ring | **1.989s** | **50,277 items/s** | ✅ **SharedMemory** (1.43x faster) |

**Key takeaways**:
- **SPSC**: SharedMemory has a clear advantage because it avoids pickle serialization and kernel-level queue management.
- **MPSC**: SharedMemory loses because `write_lock` becomes the bottleneck when 4 producers serialize their writes.
- **SPMC**: SharedMemory pulls ahead again because multiple consumers can read different slots in parallel.
- Strategy suggestion: prefer SharedMemory for single-producer cases; prefer MPQueue for multi-producer cases.

## How to Run

```bash
python bench/bench_mpqueue_vs_shared_memory.py
```

## Parameter Tuning

### Change the Test Scale and Configuration

Adjust these values near the top of `bench/bench_mpqueue_vs_shared_memory.py`:

```python
COUNT = 10_000       # Fewer iterations for quick verification
# COUNT = 1_000_000  # Large-scale stress test

REPEAT = 1           # Run only one round
# REPEAT = 5         # More rounds

PAYLOAD_MODE = "int"  # Payload type: int / small / medium / large
SLOT_COUNT = 256     # Smaller ring buffer
# SLOT_COUNT = 4096  # Larger ring buffer, observe throughput changes
```

### Test Only Specific Topologies

```python
TOPOLOGIES = [
    ("SPSC", 1, 1),     # Only test single-producer single-consumer
    # ("MPSC", 4, 1),   # Skip multi-producer case
    # ("SPMC", 1, 4),   # Skip single-producer multi-consumer case
]
```

Run again after modification:

```bash
python bench/bench_mpqueue_vs_shared_memory.py
```

## Dependencies

- `bench_utils.summarize`
