# bench_graph_mode.py Benchmark Guide

> 📅 Last Updated: 2026/08/31

## Objective

Compare the task graph execution performance of complex DAGs under different combinations of `graph_mode` (`serial` / `thread` / `async`) and `execution_mode` (`serial` / `thread` / `async`). Uses the framework's built-in `benchmark_graph` tool for a 3×3 matrix comparison.

## Test Content

### `bench_graph_0`
- **Structure**: 4-node DAG, `stage1 → stage2 → stage4`, `stage1 → stage3` (stage3 is an independent branch that does not merge into stage4)
- **Task Mix**: CPU-intensive (Fibonacci), I/O-intensive (sleep), pure computation (divide by two, square)
- **Input**: `range(25, 32)` (7 purely successful tasks; earlier versions included error inputs, which have been removed)
- **Retry Settings**: `stage1`, `stage2` enable `max_retries=1` for `ValueError` (not triggered under the current input)
- **Reporter**: Disabled by default (commented out in code; can be enabled by uncommenting)

### `bench_graph_1`
- **Structure**: 6-node multi-layer DAG (A → [B, C]; B → [D, E]; C → E; D → F)
- **Tasks**: Random 0-2 second sleep (simulating uneven load)
- **Input**: `range(10)`
- **Reporter**: Disabled by default (commented out in code; can be enabled by uncommenting)

### `bench_graph_2`
- **Structure**: 4-node DAG (Splitter → A → [B, C]), using `TaskSplitter` to expand inputs
- **Tasks**: Pure computation (add one, multiply by two), testing framework scheduling throughput upper limit
- **Input**: `range(10_000)` (expanded by Splitter into 10,000 individual tasks)

## Key Configuration

- `benchmark_graph` internally iterates over combinations of `graph_mode` (`serial` / `thread` / `async`) and `execution_mode` (`serial` / `thread` / `async`), for a total of **9 combinations**
- Synchronous node templates are passed in via `graph`, and asynchronous node templates via `async_graph`; `benchmark_graph` selects the appropriate template by column
- When the combination is `serial/thread + async`, the benchmark function calls the synchronous graph entry in a background thread to avoid conflicting with its own event loop

## Potential Issues

1. **Reporter disabled by default**: There is no `set_reporter(...)` or `add_observer(...)` call in the current script, so regardless of whether `REPORT_HOST`/`REPORT_PORT` is configured in `.env`, the reporter will not auto-connect; to enable the reporter, you must explicitly call `graph.set_reporter(...)` inside `bench_graph_*` and ensure the service is reachable.
2. **Long total runtime**: `benchmark_graph` runs `len(graph_modes) × len(execution_modes)` full graph executions; total time can reach several minutes when I/O delays are included.

## How to Run

```bash
python bench/bench_graph_mode.py
```

## Parameter Tuning

### Running a Specific Test Scenario

> `benchmark_graph` has been changed to an `async` function, and `bench_graph_*` are all `async def`; they must be called via `main_async()` or `asyncio.run()`.

In `bench/bench_graph_mode.py`'s `main_async()`, you can choose to run only a specific scenario:

```python
async def main_async() -> None:
    # await bench_graph_0()
    # await bench_graph_1()
    await bench_graph_2()

if __name__ == "__main__":
    asyncio.run(main_async())
```

### Adjusting Input Scale

```python
# bench_graph_2 default input is range(10_000); can be reduced for quick validation
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

> 🟢 All timing data in the tables of this section is historical measured data and cannot be verified from source code; manual confirmation is required. The `process` rows in earlier tables correspond to the deprecated `stage_mode="process"` and are retained only for historical reference.

### Historical Results - Windows graph mode comparison (date not recorded)

> Environment: Windows, Python 3.10

#### `bench_graph_0` — 4-node DAG, CPU+I/O mixed, 12 tasks (including boundary errors)

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 7.74s | 2.76s | 2.74s |
| **thread** | 7.19s | 2.28s | 2.14s |
| **process** | 9.88s | 4.99s | - |

Note: `process` mode has been deprecated; bench data retained only.

- `thread` and `serial` stage_mode show little difference in CPU-intensive (Fibonacci) scenarios (GIL constraint)
- Both `execution_mode=thread` and `async` provide 2-3x speedup (GIL-releasing portions of Fibonacci computation + I/O concurrency in sleep stages)
- `async` and `thread` performance is close; async has a slight edge in I/O-intensive scenarios

#### `bench_graph_1` — 6-node DAG, I/O-intensive (random sleep), 10 tasks

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 54.25s | 17.12s | 14.14s |
| **thread** | 17.10s | 7.07s | 6.05s |
| **process** | 20.47s | 10.98s | - |

Note: `process` mode has been deprecated; bench data retained only.

- Optimal combination: `thread` + `async` (6.05s), **9.0x** faster than worst combination `serial`+`serial` (54.25s)
- `async` outperforms `thread` in I/O-intensive scenarios (coroutine switching overhead < thread switching)
- `thread` (threaded layout) significantly outperforms `serial` (single-threaded serial layout) in I/O-intensive scenarios; stages can launch in parallel

#### `bench_graph_2` — 4-node DAG (Splitter→A→[B,C]), pure computation, 10,000 tasks

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 1.09s | 3.89s | 10.73s |
| **thread** | 2.79s | 5.30s | 11.40s |

- **`serial` + `serial` is fastest** (1.09s): pure computation with no I/O waiting, direct function calls with zero overhead
- `thread` is 3.5x slower than `serial`: thread pool submission + Future synchronization overhead is amplified on microsecond-level tasks
- `async` is 10x slower than `serial`: each task creates a coroutine object + event loop scheduling, but there are no I/O wait points to leverage concurrency
- `stage_mode=thread` also adds overhead: inter-stage thread scheduling is pure burden in pure computation scenarios
- **Conclusion: pure computation-intensive tasks should use `serial` + `serial` to avoid concurrency scheduling overhead**

#### Summary

- `stage_mode=thread` is the optimal choice in I/O-intensive scenarios
- `execution_mode=async` performs best in I/O-intensive scenarios, followed by `thread`, with `serial` being the slowest
- **`serial` is fastest in pure computation scenarios** — `thread` and `async` scheduling overhead cannot be amortized without I/O waiting, and instead become bottlenecks
- `async` requires stage functions to be async functions, hence both sync_graph and async_graph must be provided separately
- Total time includes: thread startup + task execution + queue transfer + termination signal propagation

### 2026/08/05 — Re-run after `start_graph_async` refactor

> Environment: Windows, Python 3.14, Reporter **disabled** (to avoid HTTP timeouts interfering with timing)
> Change: `benchmark_graph` is now an `async` function; the `async` execution mode uses `start_graph_async` instead of `start_graph`

#### `bench_graph_0` — 4-node DAG, CPU+I/O mixed, 12 tasks (including boundary errors)

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 8.36s | 1.38s | 1.39s |
| **thread** | 8.11s | 1.39s | 1.38s |

- When the I/O portion (`sleep_1`) accounts for a small share, `thread` and `async` still deliver about **6x** speedup
- `stage_mode` has little impact in this scenario (thread-layout overhead is masked by task execution time)

#### `bench_graph_1` — 6-node DAG, I/O-intensive (random sleep), 10 tasks

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 69.04s | 12.03s | 6.05s |
| **thread** | 19.02s | 6.02s | 8.06s |

- Optimal combination: `serial`+`async` (6.05s), **11.4x** faster than worst `serial`+`serial` (69.04s)
- `stage_mode=thread` + `execution_mode=async` (8.06s) is slower than `serial`+`async` (6.05s), because the combination of thread switching between stages + async coroutine scheduling produces double overhead
- `execution_mode=async` correctly takes effect for the first time in I/O-intensive scenarios (previously it mistakenly took the synchronous path), with a clear advantage

#### `bench_graph_2` — 4-node DAG (Splitter→A→[B,C]), pure computation, 10,000 tasks

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 2.65s | 3.18s | 6.05s |
| **thread** | 2.55s | 4.64s | 5.50s |

- `serial`+`serial` (2.65s) is fastest; the pure computation scenario conclusion is unchanged
- `async` slows down by about **2.3x** due to no I/O waiting and coroutine scheduling overhead
- Overall about 3x faster than the old version (with Reporter), confirming that the Reporter's HTTP timeout contributed a large amount of extra time in previous data

> **Reporter impact note**: In previous data, the Reporter service was not running; a background thread made HTTP requests every 5 seconds waiting for a timeout, significantly extending the overall time. With the Reporter fully disabled this round, the data more accurately reflects the framework's own scheduling performance.
>
> The old version (before 2026/07/16) with `execution_mode="async"` actually took the `start_graph` synchronous path (`start_stage` internally calls `asyncio.run`); the new version correctly takes the coroutine path via `start_graph_async`, so historical data is no longer directly comparable.

### 2026/08/17 — Re-run after the 9-combination matrix was completed

> Environment: macOS, Python 3.14.3, Reporter **not enabled**
> Change: `benchmark_graph` now provides the full 3×3 matrix of `graph_mode × execution_mode`; this round's data corresponds to the complete 9 combinations of `serial/thread/async × serial/thread/async`

#### `bench_graph_0` — 4-node DAG, CPU+I/O mixed, 12 tasks (including boundary errors)

| graph_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 8.17s | 1.17s | 1.16s |
| **thread** | 8.06s | 1.17s | 1.17s |
| **async**  | 8.05s | 1.17s | 1.15s |

- The three rows differ very little, indicating that the dominant factor in this scenario is still the concurrency mode inside nodes, not the graph-level launch mode
- Both `execution_mode=thread` and `async` compress total time to about 1.15s–1.17s, a **~7x** improvement over the `serial` column
- `graph_mode="async"` does not bring additional noticeable benefit, indicating that in this 4-node mixed DAG, the graph scheduling cost is already masked by task execution time

#### `bench_graph_1` — 6-node DAG, I/O-intensive (random sleep), 10 tasks

| graph_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 71.19s | 12.03s | 13.03s |
| **thread** | 21.05s | 7.03s  | 6.02s  |
| **async**  | 30.07s | 7.02s  | 6.01s  |

- The optimal combinations are `async + async` (6.01s) and `thread + async` (6.02s), nearly tied
- The benefit of upgrading from `serial` to `thread/async` at the graph level is very clear: even with `execution_mode=serial`, the time drops from 71.19s to 21.05s or 30.07s
- `execution_mode=thread` and `async` under `thread/async graph_mode` are both significantly better than pure serial, indicating that this scenario mainly benefits from I/O overlap and concurrent node launching

#### `bench_graph_2` — 4-node DAG (Splitter→A→[B,C]), pure computation, 10,000 tasks

| graph_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 1.10s | 1.63s | 2.10s |
| **thread** | 1.10s | 1.56s | 2.41s |
| **async**  | 1.11s | 1.56s | 1.92s |

- `serial + serial` remains the optimal solution, indicating that for small pure-computation tasks, direct function call overhead is the lowest
- `execution_mode=thread` introduces thread pool submission and synchronization overhead, so it is overall slower than `serial`
- `execution_mode=async` is the slowest, again because coroutine creation and scheduling cost cannot be amortized by I/O waiting
- This scenario contains `TaskSplitter`, which is always fixed to `execution_mode="serial"`; therefore, this set of data is a "mixed mode with Splitter as the serial entry" benchmark, not a strict uniform execution mode for all nodes

#### Round summary

- `benchmark_graph` can now directly output the complete `3 × 3` combination matrix
- For I/O-intensive DAGs, `graph_mode=thread/async` paired with `execution_mode=thread/async` yields the most clear benefit
- For mixed DAGs, the concurrency mode inside nodes is more dominant than the graph-level launch mode
- For pure computation microtasks, `serial + serial` remains the safest choice; extra concurrency layers usually only amplify scheduling overhead

> This round's data is not directly comparable column-by-column to the 2026/08/05 results: on one hand, the runtime environment switched from Windows to macOS; on the other hand, the matrix has been expanded from incomplete combinations to the full 3×3 grid, and the semantics of the `async` column have also been corrected.

### 2026/08/31 — Re-run after removing error inputs from bench_graph_0 (Windows)

> Environment: Windows, Python 3.14.3, Reporter **not enabled**
> Change: `bench_graph_0`'s input was changed from `range(25, 32) + [0, 27, None, 0, ""]` (with boundary errors) to pure `range(25, 32)`, excluding the impact of failure-task retry paths on timing

#### `bench_graph_0` — 4-node DAG, CPU+I/O mixed, 7 tasks (pure success path)

| graph_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 7.34s | 1.37s | 1.37s |
| **thread** | 7.06s | 1.38s | 1.39s |
| **async**  | 7.08s | 1.37s | 1.41s |

- Compared with the old version that included error inputs (serial column about 8.1–8.4s), after removing failure inputs the serial column drops to about 7.06–7.34s, saving the retry and error-handling overhead of failure tasks (about 1s)
- The `thread` / `async` columns barely change (about 1.37–1.41s): failure tasks themselves execute very quickly (fibonacci(0) immediately throws), so the impact on concurrent modes is negligible
- Conclusion unchanged: `graph_mode` differs very little across the three rows, and the node-internal `execution_mode` is still the dominant factor

#### `bench_graph_1` — 6-node DAG, I/O-intensive (random sleep), 10 tasks

| graph_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 79.05s | 12.03s | 12.10s |
| **thread** | 20.02s | 7.02s  | 6.06s  |
| **async**  | 21.03s | 8.02s  | 6.06s  |

- Optimal combinations: `thread + async` (6.06s) and `async + async` (6.06s), consistent with the 08/17 conclusion
- Random sleep (0–2s × about 60 tasks across the graph) causes high variance in single-round data (e.g., `serial+serial` fluctuates between 74–79s); compare multi-round trends rather than single-round absolute values

#### `bench_graph_2` — 4-node DAG (Splitter→A→[B,C]), pure computation, 10,000 tasks

| graph_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 4.59s | 3.67s | 6.42s |
| **thread** | 2.96s | 3.79s | 6.82s |
| **async**  | 3.05s | 5.48s | 5.69s |

- This round, `thread + serial` (2.96s) is the fastest combination, while `serial + serial` (4.59s) is slower; this is inconsistent with the historical trend of `serial+serial` dominating (1.10s / 2.65s), presumably due to system load or CPU frequency fluctuations, requiring a rerun for confirmation
- `execution_mode=async` is still the slowest (5.69–6.82s); the coroutine-scheduling-overhead conclusion for pure computation scenarios remains stable
- This scenario contains `TaskSplitter`, always fixed to `execution_mode="serial"`, so the `thread`/`async` columns only apply to the downstream A/B/C

#### Round summary

- After `bench_graph_0` was cleaned up: the conclusion that `execution_mode` dominates while `graph_mode` is irrelevant becomes clearer, and the ~1s overhead of failure paths is quantified
- I/O-intensive (bench_graph_1): `graph_mode=thread/async` + `execution_mode=async` remains optimal
- Pure computation (bench_graph_2): `async` remains the slowest, but the order of `serial+serial` and `thread+serial` flipped this round, with high single-round variance; multi-round data should be the basis for conclusions

> This round's runtime environment (Windows) is not directly comparable column-by-column to the 2026/08/17 macOS data.

## Dependencies

- `celestialflow` (`TaskGraph`, `TaskStage`, `benchmark_graph`)
- `python-dotenv`
- External Service: Reporter service (optional)
