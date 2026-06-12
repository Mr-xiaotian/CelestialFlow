# bench_mpqueue_vs_shared_memory.py Benchmark Notes

> 📅 Last Updated: 2026/04/22

## Objective

Under more complex producer-consumer topologies (SPSC, MPSC, SPMC), compare the performance of `multiprocessing.Queue` against a custom ring buffer based on `shared_memory`. Provide in-depth data for CelestialFlow's IPC optimization in high-throughput scenarios.

## Test Contents

| Topology | Producers | Consumers | Description |
|----------|-----------|-----------|-------------|
| SPSC | 1 | 1 | Single producer single consumer |
| MPSC | 4 | 1 | Multi-producer single consumer |
| SPMC | 1 | 4 | Single producer multi-consumer |

- **Scale**: `COUNT = 100_000`, `REPEAT = 3`
- **SharedMemory config**: `SLOT_COUNT = 1024`, each slot size = 4B length prefix + payload
- **Synchronization primitives**: `Lock` (protects read/write indices), `Semaphore` (empty/full slot counting)

## Key Implementation

### SharedMemory Ring Protocol
1. **Producer**: `empty_slots.acquire()` → write payload under `write_lock` → `full_slots.release()`
2. **Consumer**: `full_slots.acquire()` → read payload under `read_lock` → `empty_slots.release()`
3. **Key design**: `full_slots.release()` is executed outside the lock to maximize concurrency

## Potential Issues

1. **SharedMemory lifecycle management**: `shm.unlink()` must be executed only after all processes have closed. If a child process exits abnormally without `shm.close()`, it may cause `unlink` to fail or result in memory leaks.
2. **Insufficient slot_size**: If `payload_max_bytes(mode)` is miscalculated or the actual payload exceeds `slot_size - 4`, `producer_shm_ring` will raise `RuntimeError`.
3. **MPSC write contention**: Although `write_lock` protects index and write operations, multiple producers are still serialized for writes; SharedMemory's advantage under MPSC may be less than expected.
4. **Windows shared memory naming**: `SharedMemory(name=shm_name)` relies on the global namespace on Windows; name collisions (e.g., running multiple benchmark instances simultaneously) can cause unpredictable behavior.

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10, spawn mode, COUNT=100,000, REPEAT=3, payload=int (8 bytes), SLOT_COUNT=1024

### SPSC (Single Producer Single Consumer)

| Mechanism | Average Time | Throughput | Winner |
|-----------|-------------|------------|--------|
| MPQueue | 1.281s | 78,066 items/s | — |
| SharedMemory ring | **0.878s** | **113,853 items/s** | ✅ **SharedMemory** (1.46x faster) |

### MPSC (4 Producers 1 Consumer)

| Mechanism | Average Time | Throughput | Winner |
|-----------|-------------|------------|--------|
| MPQueue | **1.618s** | **61,787 items/s** | ✅ **MPQueue** (1.18x faster) |
| SharedMemory ring | 1.905s | 52,487 items/s | — |

### SPMC (1 Producer 4 Consumers)

| Mechanism | Average Time | Throughput | Winner |
|-----------|-------------|------------|--------|
| MPQueue | 2.851s | 35,070 items/s | — |
| SharedMemory ring | **1.989s** | **50,277 items/s** | ✅ **SharedMemory** (1.43x faster) |

**Key Takeaways**:
- **SPSC**: SharedMemory has a clear advantage, avoiding pickle serialization and kernel-mode queue management
- **MPSC**: SharedMemory's write_lock becomes a bottleneck (4 producers serialized writes), making MPQueue faster instead
- **SPMC**: SharedMemory leads again, with multiple consumers able to read different slots in parallel
- Strategy recommendation: prefer SharedMemory for single-producer scenarios; prefer MPQueue for multi-producer scenarios

## How to Run

```bash
python bench/bench_mpqueue_vs_shared_memory.py
```

## Parameter Tuning

### Adjusting Test Scale and Configuration

Adjust at the top of `bench/bench_mpqueue_vs_shared_memory.py`:

```python
COUNT = 10_000       # Reduce iterations for quick validation
# COUNT = 1_000_000  # Large scale stress test

REPEAT = 1           # Run only 1 round
# REPEAT = 5         # Increase rounds

PAYLOAD_MODE = "int"  # Payload type: int / small / medium / large
SLOT_COUNT = 256     # Reduce ring buffer slot count
# SLOT_COUNT = 4096  # Increase slot count, observe buffer size impact on throughput
```

### Testing Specific Topologies Only

```python
TOPOLOGIES = [
    ("SPSC", 1, 1),     # Test single producer single consumer only
    # ("MPSC", 4, 1),   # Skip multi-producer scenario
    # ("SPMC", 1, 4),   # Skip single producer multi-consumer scenario
]
```

Run after modification:

```bash
python bench/bench_mpqueue_vs_shared_memory.py
```

## Dependencies

- `bench_utils.summarize`
