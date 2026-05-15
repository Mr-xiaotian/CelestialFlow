# bench_graph_mode.py Benchmark Documentation

> 📅 Last Updated: 2026/05/15

## Objective

Compare task graph execution performance across different combinations of `stage_mode` (`serial` / `thread`) and `execution_mode` (`serial` / `thread` / `async`) for complex DAGs. Uses the framework's built-in `benchmark_graph` tool for matrix-style comparison.

## Test Cases

### `bench_graph_0`
- **Structure**: 4-node DAG (`stage1 -> [stage2, stage3] -> stage4`)
- **Task mix**: CPU-intensive (Fibonacci), I/O-intensive (sleep), pure computation (halve, square)
- **Input**: `range(25, 32) + [0, 27, None, 0, ""]` (including edge cases)
- **Services enabled**: Reporter

### `bench_graph_1`
- **Structure**: 6-node multi-layer DAG (A -> [B, C] -> [D, E] -> F)
- **Task**: Random 0-2 second sleep (simulating uneven workload)
- **Input**: `range(10)`
- **Services enabled**: Reporter

### `bench_graph_2`
- **Structure**: 4-node DAG (Splitter -> A -> [B, C]), using `TaskSplitter` to expand input
- **Task**: Pure computation (add one, multiply by two), testing framework scheduling throughput ceiling
- **Input**: `range(10_000)` (expanded to 10,000 independent tasks via Splitter)

## Key Configuration

- `benchmark_graph` internally iterates over combinations of `stage_mode` (`serial` / `thread`) and `execution_mode` (`serial` / `thread` / `async`), totaling **6 combinations**, each running the full graph
- This file does not directly configure these modes; it only provides `sync_graph` (sync function) and `async_graph` (async function) to pass into `benchmark_graph`

## Potential Issues

1. **Environment variable dependency**: `REPORT_HOST` and others must be loaded from `.env`; if not configured, the reporter connection will fail.
2. **Long total runtime**: `benchmark_graph` runs `len(stage_modes) x len(execution_modes)` full graph executions, which may take several minutes including I/O delays.

## How to Run

```bash
python bench/bench_graph_mode.py
```

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10

### `bench_graph_0` -- 4-node DAG, CPU+I/O mixed, 11 tasks (including edge cases)

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 7.74s | 2.76s | 2.74s |
| **thread** | 7.19s | 2.28s | 2.14s |

- `thread` vs `serial` stage_mode shows little difference in CPU-intensive (Fibonacci) scenarios (GIL limitation)
- `execution_mode=thread` and `async` both provide 2-3x speedup (partial GIL release during Fibonacci + I/O concurrency during sleep stages)
- `async` and `thread` performance are close; async has a slight edge in I/O-intensive scenarios

### `bench_graph_1` -- 6-node DAG, I/O-intensive (random sleep), 10 tasks

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 54.25s | 17.12s | 14.14s |
| **thread** | 17.10s | 7.07s | 6.05s |

- Best combination: `thread` + `async` (6.05s), **9.0x** faster than worst combination `serial`+`serial` (54.25s)
- `async` outperforms `thread` in I/O-intensive scenarios (coroutine switching overhead is lower than thread switching)
- `thread` (threaded layout) significantly outperforms `serial` (single-thread serial layout) in I/O-intensive scenarios, as stages can start in parallel

### `bench_graph_2` -- 4-node DAG (Splitter->A->[B,C]), pure computation, 10,000 tasks

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 1.09s | 3.89s | 10.73s |
| **thread** | 2.79s | 5.30s | 11.40s |

- **`serial` + `serial` is fastest** (1.09s): pure computation with no I/O wait, direct function calls with zero overhead
- `thread` is 3.5x slower than `serial`: thread pool submission + Future synchronization overhead is amplified for microsecond-level tasks
- `async` is 10x slower than `serial`: each task creates a coroutine object + event loop scheduling, but there are no I/O wait points to exploit concurrency
- `stage_mode=thread` also adds overhead: inter-stage thread scheduling is pure burden in computation-only scenarios
- **Conclusion: pure computation-intensive tasks should use `serial` + `serial` to avoid concurrency scheduling overhead**

### Summary

- `stage_mode=thread` is the optimal choice for I/O-intensive scenarios
- `execution_mode=async` performs best in I/O-intensive scenarios, followed by `thread`, with `serial` being slowest
- **In pure computation scenarios, `serial` is fastest** -- `thread` and `async` scheduling overhead cannot be amortized without I/O waits, becoming a bottleneck instead
- `async` requires stage functions to be async functions, hence separate sync_graph and async_graph must be provided
- Total duration includes: thread startup + task execution + queue transfer + termination signal propagation

## Dependencies

- `celestialflow` (`TaskGraph`, `TaskStage`, `benchmark_graph`)
- `python-dotenv`
- External services: Reporter service (optional)
