# bench_graph_mode.py Benchmark Documentation

> 📅 Last updated: 2026/05/11

## Objective

Compare the task graph execution performance of complex DAGs across different combinations of `stage_mode` (`serial` / `thread`) and `execution_mode` (`serial` / `thread` / `async`). Uses the built-in `benchmark_graph` tool for matrix-style comparison.

## Test Cases

### `bench_graph_0`
- **Structure**: 4-node DAG (`stage1 -> [stage2, stage3] -> stage4`)
- **Task mix**: CPU-intensive (Fibonacci), I/O-intensive (sleep), pure computation (halve, square)
- **Input**: `range(25, 32) + [0, 27, None, 0, ""]` (including exceptional edge cases)
- **Enabled services**: Reporter

### `bench_graph_1`
- **Structure**: 6-node multi-layer DAG (A -> [B, C] -> [D, E] -> F)
- **Tasks**: Random 0-2 second sleep (simulating uneven load)
- **Input**: `range(10)`
- **Enabled services**: Reporter

## Key Configuration

- `stage_modes = ["serial", "thread"]`
- `execution_sync_modes = ["serial", "thread"]`
- `execution_async_modes = ["async"]`
- A total of **6 combinations**, each running the full graph
- Requires separate `sync_graph` (sync functions) and `async_graph` (async functions)

## Potential Issues

1. **Environment variable dependency**: `REPORT_HOST`, etc. must be loaded from `.env`; missing configuration will cause reporter connection failures.
2. **Long total runtime**: `benchmark_graph` runs `len(stage_modes) x len(execution_modes)` full graph executions. With I/O delays, total time can reach several minutes.

## How to Run

```bash
python bench/bench_graph_mode.py
```

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10

### `bench_graph_0` — 4-node DAG, CPU+I/O mixed, 11 tasks (including exceptional edge cases)

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 7.74s | 2.76s | 2.74s |
| **thread** | 7.19s | 2.28s | 2.14s |

- In CPU-intensive (Fibonacci) scenarios, `thread` and `serial` stage_mode show minimal difference (GIL limitation)
- `execution_mode=thread` and `async` both provide 2-3x speedup (partial GIL release during Fibonacci computation + I/O concurrency during sleep stages)
- `async` performs similarly to `thread`, with a slight edge in I/O-intensive scenarios

### `bench_graph_1` — 6-node DAG, I/O-intensive (random sleep), 10 tasks

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 54.25s | 17.12s | 14.14s |
| **thread** | 17.10s | 7.07s | 6.05s |

- Best combination: `thread` + `async` (6.05s), **9.0x** faster than the worst combination `serial`+`serial` (54.25s)
- `async` outperforms `thread` in I/O-intensive scenarios (coroutine switching overhead is lower than thread switching)
- `thread` (threaded layout) significantly outperforms `serial` (single-thread serial layout), as stages can start in parallel

### Summary

- `stage_mode=thread` is the optimal choice for I/O-intensive scenarios
- `execution_mode=async` performs best in I/O-intensive scenarios, followed by `thread`, then `serial`
- `async` requires stage functions to be async functions, hence separate sync_graph and async_graph are needed
- Total time includes: thread startup + task execution + queue transmission + termination signal propagation

## Dependencies

- `celestialflow` (`TaskGraph`, `TaskStage`, `benchmark_graph`)
- `python-dotenv`
- External services: Reporter service (optional)
