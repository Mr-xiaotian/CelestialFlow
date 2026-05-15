# bench_mpqueue_vs_shared_memory.py Benchmark Documentation

> 📅 Last Updated: 2026/04/22

## Objective

Compare performance of `multiprocessing.Queue` vs. a custom shared memory-based ring buffer under more complex producer-consumer topologies (SPSC, MPSC, SPMC). Providing in-depth data for IPC optimization in CelestialFlow's high-throughput scenarios.

## Test Cases

| Topology | Producers | Consumers | Description |
|----------|-----------|-----------|-------------|
| SPSC | 1 | 1 | Single-producer single-consumer |
| MPSC | 4 | 1 | Multi-producer single-consumer |
| SPMC | 1 | 4 | Single-producer multi-consumer |

- **Scale**: `COUNT = 100_000`, `REPEAT = 3`
- **SharedMemory configuration**: `SLOT_COUNT = 1024`, each slot size = 4B length prefix + payload
- **Synchronization primitives**: `Lock` (protecting read/write indices), `Semaphore` (empty/full slot counting)

## Key Implementation

### SharedMemory Ring Protocol
1. **Producer**: `empty_slots.acquire()` -> write payload under `write_lock` -> `full_slots.release()`
2. **Consumer**: `full_slots.acquire()` -> read payload under `read_lock` -> `empty_slots.release()`
3. **Key design**: `full_slots.release()` is executed outside the lock to maximize concurrency

## Potential Issues

1. **SharedMemory lifecycle management**: `shm.unlink()` must be executed only after all processes have closed. If a child process exits abnormally without calling `shm.close()`, `unlink` may fail or cause memory leaks.
2. **Insufficient slot_size**: If `payload_max_bytes(mode)` calculates incorrectly or actual payload exceeds `slot_size - 4`, `producer_shm_ring` will raise a `RuntimeError`.
3. **MPSC write contention**: Although `write_lock` protects index and write operations, multiple producers still serialize writes, so SharedMemory's advantage may be less than expected under MPSC.
4. **Windows shared memory naming**: `SharedMemory(name=shm_name)` on Windows relies on a global namespace; name conflicts (e.g., running multiple benchmark instances simultaneously) can cause unpredictable behavior.

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10, spawn mode, COUNT=100,000, REPEAT=3, payload=int (8 bytes), SLOT_COUNT=1024

### SPSC (Single-producer Single-consumer)

| Mechanism | Average Duration | Throughput | Winner |
|-----------|-----------------|------------|--------|
| MPQueue | 1.281s | 78,066 items/s | -- |
| SharedMemory ring | **0.878s** | **113,853 items/s** | ✅ **SharedMemory** (1.46x faster) |

### MPSC (4 Producers 1 Consumer)

| Mechanism | Average Duration | Throughput | Winner |
|-----------|-----------------|------------|--------|
| MPQueue | **1.618s** | **61,787 items/s** | ✅ **MPQueue** (1.18x faster) |
| SharedMemory ring | 1.905s | 52,487 items/s | -- |

### SPMC (1 Producer 4 Consumers)

| Mechanism | Average Duration | Throughput | Winner |
|-----------|-----------------|------------|--------|
| MPQueue | 2.851s | 35,070 items/s | -- |
| SharedMemory ring | **1.989s** | **50,277 items/s** | ✅ **SharedMemory** (1.43x faster) |

**Key Conclusions**:
- **SPSC**: SharedMemory has a clear advantage, avoiding pickle serialization and kernel-mode queue management
- **MPSC**: SharedMemory's write_lock becomes a bottleneck (4 producers serialize writes), so MPQueue is actually faster
- **SPMC**: SharedMemory leads again; multiple consumers can read different slots in parallel
- Strategy recommendation: Prefer SharedMemory for single-producer scenarios; prefer MPQueue for multi-producer scenarios

## How to Run

```bash
python bench/bench_mpqueue_vs_shared_memory.py
```

## Dependencies

- `bench_utils.summarize`
