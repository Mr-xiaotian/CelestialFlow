# bench_graph_mode.py Benchmark Notes

> 📅 Last Updated: 2026/06/11

## Objective

Compare the task graph execution performance of complex DAGs under different combinations of `stage_mode` (`serial` / `thread`) and `execution_mode` (`serial` / `thread` / `async`). Uses the framework's built-in `benchmark_graph` tool for matrix comparison.

## Test Contents

### `bench_graph_0`
- **Structure**: 4-node DAG (`stage1 → [stage2, stage3] → stage4`)
- **Task Mix**: CPU-intensive (Fibonacci), I/O-intensive (sleep), pure computation (divide by two, square)
- **Inputs**: `range(25, 32) + [0, 27, None, 0, ""]` (includes boundary error cases)
- **Enabled Services**: Reporter

### `bench_graph_1`
- **Structure**: 6-node multi-layer DAG (A → [B, C] → [D, E] → F)
- **Tasks**: Random 0-2 second sleep (simulating uneven load)
- **Inputs**: `range(10)`
- **Enabled Services**: Reporter

### `bench_graph_2`
- **Structure**: 4-node DAG (Splitter → A → [B, C]), using `TaskSplitter` to expand inputs
- **Tasks**: Pure computation (add one, multiply by two), testing framework scheduling throughput upper limit
- **Inputs**: `range(10_000)` (expanded by Splitter into 10,000 individual tasks)

## Key Configuration

- `benchmark_graph` internally iterates over combinations of `stage_mode` (`serial` / `thread`) and `execution_mode` (`serial` / `thread` / `async`), for a total of **6 combinations**, each running the full graph
- This file does not directly configure these modes; it only provides `sync_graph` (sync function) and `async_graph` (async function) to `benchmark_graph`

## Potential Issues

1. **Environment variable dependency**: `REPORT_HOST` etc. must be loaded from `.env`; if not configured, reporter connection will fail.
2. **Long total runtime**: `benchmark_graph` runs `len(stage_modes) × len(execution_modes)` full graph executions; total time can reach several minutes when I/O delays are included.

## How to Run

```bash
python bench/bench_graph_mode.py
```

## Parameter Tuning

### Running a Specific Test Scenario

In `bench/bench_graph_mode.py`'s `main()`, you can choose to run only a specific scenario:

```python
if __name__ == "__main__":
    bench_graph_0()     # Run 4-node DAG mixed scenario (commented out by default)
    bench_graph_1()     # Currently enabled: 6-node multi-layer DAG
    bench_graph_2()     # Currently enabled: Splitter throughput test
```

### Adjusting Input Scale

```python
# bench_graph_2 default input is range(10_000), can be reduced for quick validation
# Modify the input range inside the function
inputs = range(1_000)  # Change to 1000 tasks, quick validation
```

### Modifying Worker Count

The default worker count for each scenario can be directly adjusted in the code:

```python
# Inside bench_graph_0
max_workers = 4   # Reduce concurrent workers
```

Run after modification:

```bash
python bench/bench_graph_mode.py
```

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10

### `bench_graph_0` — 4-node DAG, CPU+I/O mixed, 11 tasks (including boundary errors)

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 7.74s | 2.76s | 2.74s |
| **thread** | 7.19s | 2.28s | 2.14s |
| **process** | 9.88s | 4.99s | - |

Note: `process` mode has been deprecated; bench data retained only.

- `thread` and `serial` stage_mode show little difference in CPU-intensive (Fibonacci) scenarios (GIL constraint)
- Both `execution_mode=thread` and `async` provide 2-3x speedup (GIL-releasing portions of Fibonacci computation + I/O concurrency in sleep stages)
- `async` and `thread` performance is close; async has a slight edge in I/O-intensive scenarios

### `bench_graph_1` — 6-node DAG, I/O-intensive (random sleep), 10 tasks

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 54.25s | 17.12s | 14.14s |
| **thread** | 17.10s | 7.07s | 6.05s |
| **process** | 20.47s | 10.98s | - |

Note: `process` mode has been deprecated; bench data retained only.

- Optimal combination: `thread` + `async` (6.05s), **9.0x** faster than worst combination `serial`+`serial` (54.25s)
- `async` outperforms `thread` in I/O-intensive scenarios (coroutine switching overhead < thread switching)
- `thread` (threaded layout) significantly outperforms `serial` (single-threaded serial layout) in I/O-intensive scenarios; stages can launch in parallel

### `bench_graph_2` — 4-node DAG (Splitter→A→[B,C]), pure computation, 10,000 tasks

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 1.09s | 3.89s | 10.73s |
| **thread** | 2.79s | 5.30s | 11.40s |

- **`serial` + `serial` is fastest** (1.09s): pure computation with no I/O waiting, direct function calls with zero overhead
- `thread` is 3.5x slower than `serial`: thread pool submission + Future synchronization overhead is amplified on microsecond-level tasks
- `async` is 10x slower than `serial`: each task creates a coroutine object + event loop scheduling, but there are no I/O wait points to leverage concurrency
- `stage_mode=thread` also adds overhead: inter-stage thread scheduling is pure burden in pure computation scenarios
- **Conclusion: pure computation-intensive tasks should use `serial` + `serial` to avoid concurrency scheduling overhead**

### Summary

- `stage_mode=thread` is the optimal choice in I/O-intensive scenarios
- `execution_mode=async` performs best in I/O-intensive scenarios, followed by `thread`, with `serial` being the slowest
- **`serial` is fastest in pure computation scenarios** — `thread` and `async` scheduling overhead cannot be amortized without I/O waiting, and instead become bottlenecks
- `async` requires stage functions to be async functions, hence both sync_graph and async_graph must be provided separately
- Total time includes: thread startup + task execution + queue transfer + termination signal propagation

## Dependencies

- `celestialflow` (`TaskGraph`, `TaskStage`, `benchmark_graph`)
- `python-dotenv`
- External Service: Reporter service (optional)
