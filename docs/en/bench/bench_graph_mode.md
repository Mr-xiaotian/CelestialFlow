# bench_graph_mode.py Benchmark Documentation

> 📅 Last updated: 2026/05/08

## Objective

Compare the task graph execution performance of complex DAGs across different combinations of `stage_mode` (`serial` / `thread` / `process`) and `execution_mode` (`serial` / `thread`). Uses the built-in `benchmark_graph` tool for matrix-style comparison.

## Test Cases

### `bench_graph_0`
- **Structure**: 4-node DAG (`stage1 -> [stage2, stage3] -> stage4`)
- **Task mix**: CPU-intensive (Fibonacci), I/O-intensive (sleep), pure computation (halve, square)
- **Input**: `range(25, 32) + [0, 27, None, 0, ""]` (including exceptional edge cases)
- **Enabled services**: Reporter, CelestialTree

### `bench_graph_1`
- **Structure**: 6-node multi-layer DAG (A -> [B, C] -> [D, E] -> F)
- **Tasks**: Random 0-2 second sleep (simulating uneven load)
- **Input**: `range(10)`
- **Enabled services**: Reporter, CelestialTree

## Key Configuration

- `stage_modes = ["serial", "thread", "process"]`
- `execution_modes = ["serial", "thread"]`
- A total of **6 combinations**, each running the full graph

## Potential Issues

1. **Environment variable dependency**: `REPORT_HOST`, `CTREE_HOST`, etc. must be loaded from `.env`; missing configuration will cause reporter/ctree connection failures.
2. **CelestialTree not running**: If `set_ctree(True)` is called but the service is not running, `start_graph()` will throw a connection exception.
3. **Windows multi-process overhead**: With `stage_mode="process"`, each stage starts an independent process. A 4-stage DAG on Windows may spend more time on process startup than actual task execution.
4. **Long total runtime**: `benchmark_graph` runs `len(stage_modes) x len(execution_modes)` full graph executions. With I/O delays, total time can reach several minutes.

## How to Run

```bash
python bench/bench_graph_mode.py
```

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10

### `bench_graph_0` — 4-node DAG, CPU+I/O mixed, 11 tasks (including exceptional edge cases)

| stage_mode \ execution_mode | serial | thread |
|----------------------------|--------|--------|
| **serial** | 7.70s | 2.82s |
| **thread** | 7.12s | 2.63s |
| **process** | 9.88s | 4.99s |

- In CPU-intensive (Fibonacci) scenarios, `thread` and `serial` stage_mode show minimal difference (GIL limitation)
- `process` is actually the slowest due to process startup overhead
- `execution_mode=thread` still provides 2-3x speedup (partial GIL release during Fibonacci computation + I/O concurrency during sleep stages)

### `bench_graph_1` — 6-node DAG, I/O-intensive (random sleep), 10 tasks

| stage_mode \ execution_mode | serial | thread |
|----------------------------|--------|--------|
| **serial** | 61.20s | 17.08s |
| **thread** | 17.07s | 7.07s |
| **process** | 20.47s | 10.98s |

- Best combination: `thread` + `thread` (7.07s), **8.7x** faster than the worst combination `serial`+`serial` (61.20s)
- `thread` (threaded layout) outperforms `process` (multi-process layout) in I/O-intensive scenarios, saving process startup and cross-process serialization overhead
- `process` (multi-process layout) still significantly outperforms `serial` (single-process serial layout), as stages can start in parallel

### Summary

- `stage_mode=thread` is the optimal choice for I/O-intensive scenarios and supports lambda functions and other non-picklable objects
- `stage_mode=process` is suitable for CPU-intensive scenarios that need to bypass the GIL, but has significant process startup overhead on Windows
- `execution_mode=thread` outperforms `serial` in all scenarios
- Total time includes: process/thread startup + task execution + queue transmission + termination signal propagation

## Dependencies

- `celestialflow` (`TaskGraph`, `TaskStage`, `benchmark_graph`)
- `python-dotenv`
- External services: CelestialTree (optional), Reporter service (optional)
