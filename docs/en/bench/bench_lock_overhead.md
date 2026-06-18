# bench_lock_overhead.py Benchmark Guide

> 📅 Last Updated: 2026/06/16

## Objective

Compare the time overhead of two common synchronization scenarios with and without locks:

- Shared `int` increment
- `multiprocessing.Queue` read/write

Each scenario is tested under:

- Serial
- Parallel
- With lock
- Without lock

Used to quickly assess the cost of "adding an extra explicit lock layer" on the current machine, and how lock contention amplifies overhead under concurrent access.

## Test Content

| Test Item | Mode | Lock Strategy | Description |
|--------|------|--------|------|
| `shared int` | `serial` | `no_lock` | Single process directly increments shared integer |
| `shared int` | `serial` | `lock` | Single process enters `Value` lock on every increment |
| `shared int` | `parallel` | `no_lock` | 4 processes concurrently increment `Value(lock=False)` |
| `shared int` | `parallel` | `lock` | 4 processes concurrently increment `Value(lock=True)` |
| `MPQueue` | `serial` | `no_lock` | Single process sequential `put` / `get` |
| `MPQueue` | `serial` | `lock` | Single process wraps each `put` / `get` with an extra explicit lock |
| `MPQueue` | `parallel` | `no_lock` | 4 producers + 4 consumers concurrently access the same queue |
| `MPQueue` | `parallel` | `lock` | 4 producers + 4 consumers concurrently access the queue, with an extra explicit lock on every operation |

## Key Configuration

- `INT_OPS = 100_000`
- `MPQUEUE_ITEMS = 20_000`
- `PARALLEL_WORKERS = 4`
- `REPEAT = 2`
- Start method fixed to `spawn`, consistent with Windows default behavior

## Potential Issues

1. **Parallel `int` no-lock results are not guaranteed correct**: `Value(lock=False)`'s `value += 1` is not a cross-process atomic operation. Even if the result happens to be correct this round, it does not guarantee stable correctness at larger scale or on other machines.
2. **`spawn` overhead is significant under Windows**: Parallel mode total time includes child process creation cost, which especially amplifies `MPQueue` absolute time.
3. **`MPQueue` parallel results are not pure queue throughput**: The test values also include process scheduling, queue synchronization, pickle serialization, and teardown tail time.
4. **The explicit lock is an "extra layer of lock"**: `multiprocessing.Queue` already has its own internal synchronization; the `lock` results here measure the additional cost of "wrapping one more explicit lock outside".

## Benchmark Results (Measured)

### 2026/06/16 - Windows local retest

> Environment: Windows, `spawn`, `INT_OPS=100000`, `MPQUEUE_ITEMS=20000`, `PARALLEL_WORKERS=4`, `REPEAT=2`

#### Shared Int

| Mode | Lock Strategy | Mean Time | Std Dev | Final Value (Last Round) | Expected Value | Correct Rounds |
|------|--------|----------|--------|--------------------|--------|----------|
| `serial` | `no_lock` | 0.0078s | 0.0000s | 100000 | 100000 | 2/2 |
| `serial` | `lock` | 0.1044s | 0.0015s | 100000 | 100000 | 2/2 |
| `parallel` | `no_lock` | 0.1928s | 0.0096s | 100000 | 100000 | 2/2 |
| `parallel` | `lock` | 0.6163s | 0.0125s | 100000 | 100000 | 2/2 |

#### MPQueue

| Mode | Lock Strategy | put Phase | get Tail | Total Time | Std Dev | Correct Rounds |
|------|--------|----------|----------|--------|--------|----------|
| `serial` | `no_lock` | 0.0148s | 0.2954s | 0.3102s | 0.0011s | 2/2 |
| `serial` | `lock` | 0.0284s | 0.3657s | 0.3941s | 0.0054s | 2/2 |
| `parallel` | `no_lock` | 1.1135s | 0.1226s | 1.2361s | 0.0071s | 2/2 |
| `parallel` | `lock` | 1.0568s | 0.6139s | 1.6706s | 0.0807s | 2/2 |

**Conclusions for this round**:

- For shared `int`, the cost of explicit locking is very significant: about **13x** slower in serial, about **3.2x** slower in parallel
- For `MPQueue`, extra locking in serial mode increases total time by about **27%**; in parallel mode it notably amplifies the consumer tail phase, making it about **35%** slower overall
- `MPQueue` parallel total time is much higher than serial not because the queue itself degrades, but because `spawn`, process scheduling, and cross-process serialization already dominate queue operations at this scale
- This round's `parallel + no_lock` for shared `int` happened to be 2/2 correct, but this must not be taken as evidence that "lock-free cross-process increment is safe" — it only means the current scale happened not to encounter errors

## How to Run

```bash
python bench/bench_lock_overhead.py
```

## Parameter Tuning

### Increase shared `int` pressure

```python
INT_OPS = 500_000
```

### Increase queue pressure

```python
MPQUEUE_ITEMS = 100_000
```

### Increase concurrent process count

```python
PARALLEL_WORKERS = 8
```

### Increase repetition rounds

```python
REPEAT = 5
```

## Dependencies

- Python standard library
