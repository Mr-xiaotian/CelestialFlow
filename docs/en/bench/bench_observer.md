# bench/bench_observer.py

> 📅 Last Updated: 2026/11/13

## Objective

Compare the execution time of `TaskExecutor` for the same batch of tasks across three scenarios—**no observer**, **print logging** (the framework's built-in `PrintObserver`, which requires a `name` prefix at construction), and **tqdm progress bar** (`TqdmObserver`, defined inside `bench_observer.py`)—to quantify the performance overhead introduced by observer callbacks.

Help users choose an appropriate observation strategy based on task scale and real-time feedback needs.

## Test Content

### Observer Strategy Comparison

| Scenario | Observer | Description |
|------|--------|------|
| **No observer** | `None` | Bare executor with no callback output, used as the baseline |
| **print logging** | `PrintObserver` | In the unified `on_event`, prints a `name`-prefixed statistics line for each event type (node start/end, task input / success / fail / skip), simulating simple log output |
| **tqdm progress bar** | `TqdmObserver` | In the unified `on_event`, updates the `tqdm` progress bar for the same set of event types, providing visual feedback |

### Task Workload

Two Fibonacci task sets with different computation amounts:

```python
# Light tasks: fib(20~29), 10 tasks in total
light_tasks = list(range(20, 30))

# "Heavier" tasks: fib(50, 55, 60, 65, 70, 75, 80), 7 tasks in total
# Note that fibonacci is an iterative O(n) implementation; even fib(80) only takes about 80 loops, so a single task is still at the microsecond level
heavy_tasks = [50, 55, 60, 65, 70, 75, 80]
```

## Key Parameters

| Parameter | Value | Description |
|------|-----|------|
| `execution_mode` | `serial` | All scenarios use serial mode to control variables and isolate observer impact |
| `max_workers` | 1 | Single worker to avoid parallel scheduling interference |
| `max_retries` | 0 | No retries, eliminating extra time from retry logic |

## Key Functions

### `run_benchmark`

```python
def run_benchmark(
    name: str,
    task_data: list[Any],
    func: Any,
    *,
    observer: Observer | None = None,
) -> float
```

Creates a `TaskExecutor(name, func, execution_mode="serial", max_workers=1, max_retries=0)`;
if an `observer` is passed, it calls `executor.add_observer(observer)`, then wraps
`executor.run(task_data)` with `time.perf_counter()` and returns the elapsed time (seconds). Every call creates a new executor to avoid leftover state.

### `TqdmObserver`

`TqdmObserver` inherits from the framework's `Observer` base class and overrides only the unified entry point `on_event(event: Event)`, dispatching by event type with `match event` (`handle_exception` keeps the base class default implementation):

| Event | Behavior |
|------|------|
| `NodeStartEvent` | Creates `tqdm(total=...)` using the currently accumulated `_total` |
| `TaskInputEvent` | `_total += 1`; if the progress bar has already been created, expands `total` accordingly and calls `refresh()` |
| `TaskSuccessEvent` / `TaskFailEvent` / `TaskSkipEvent` | Advances progress via the shared `_advance(1)` |
| `NodeEndEvent` | Closes the progress bar |

The unlisted `TaskRetryEvent`, termination-signal events, and graph events match no branch and are naturally ignored by `match`.
The `Observer` base class currently provides only `on_event` and `handle_exception`; there are no longer
per-event callbacks such as `on_node_start` / `on_task_success`.

### Worker Functions

- `fibonacci(n)`: **Iterative** implementation (`O(n)`), not recursive; `n <= 0` raises `ValueError`, a non-`int` raises `TypeError`
- `cpu_intensive(x)`: Pure CPU loop, used to amplify observer overhead; **the current script does not call it in any scenario**

## Potential Issues

1. **TTY buffering of print**: `print()` defaults to line-buffered; when output goes to a real terminal, screen refresh may be triggered, which is slower than redirecting to a file. The overhead of `print` may differ across terminal environments.
2. **`tqdm`'s deferred `total` creation**: `TqdmObserver` creates the progress bar upon receiving `NodeStartEvent` and accumulates the total upon receiving `TaskInputEvent` (that event may arrive before `NodeStartEvent`, so when the progress bar has not been created, only `_total` is accumulated). Since `run()` injects all tasks before starting the node, `total` at the time `NodeStartEvent` arrives already includes the tasks injected before startup; if further `TaskInputEvent` events arrive afterward, the progress bar expands dynamically, but this does not affect the correctness of the benchmark results.
3. **Warm-up effect**: The first run may be affected by bytecode cache warm-up, import initialization, or system cache, making subsequent rounds faster. `bench_observer_multirun()` mitigates this by averaging across multiple rounds.
4. **The Fibonacci workload itself is too light**: `fibonacci` is an iterative `O(n)` implementation, so the per-task time of both `light_fib` and `heavy_fib` is at the microsecond level, and the measured total time mainly consists of framework scheduling, event dispatch, and observer I/O rather than computation. The difference between the two data sets comes mostly from the task count (10 vs 7), and `heavy_fib` cannot be interpreted as "computation dominates". To observe how observer overhead decays as per-task time grows, you need a genuinely millisecond-level workload (e.g. recursive fib or adding `time.sleep`).

## Benchmark Results (Measured)

> 🟢 All timing data in the tables of this section is historical measured data and cannot be verified from source code; manual confirmation is required.
>
> These data were collected from an older version in which observers still used per-event callbacks; the current implementation has been unified to `on_event` + `match`,
> so event dispatch overhead and relative ratios may have changed. It is recommended to re-run locally before citing them.

### 2026/07/30 - Local Measurement

> Environment: macOS, Python 3.14, `execution_mode=serial`

#### Single-Round Comparison

| Task | Mode | Time | Relative to No Observer |
|------|------|------|----------------|
| light_fib (10 tasks) | **No observer** | 0.0037s | — |
| light_fib (10 tasks) | **print** | 0.0019s | -48.1% |
| light_fib (10 tasks) | **tqdm** | 0.0056s | +51.1% |
| heavy_fib (7 tasks) | **No observer** | 0.0014s | — |
| heavy_fib (7 tasks) | **print** | 0.0014s | +2.6% |
| heavy_fib (7 tasks) | **tqdm** | 0.0014s | +0.9% |

> ⚠️ For light tasks (fib 20~29), since each computation is extremely fast (microsecond-level), time variance is large; the negative value in the print scenario is measurement noise. Conclusions should refer to the averages.

#### Multi-Round Average (5 rounds, light_fib)

| Mode | Average | Min | Max |
|------|------|--------|--------|
| **No observer** | 0.0015s | 0.0014s | 0.0017s |
| **print** | 0.0017s | 0.0016s | 0.0018s |
| **tqdm** | 0.0017s | 0.0017s | 0.0018s |

**Key Conclusions**:

- In serial mode, the measured values are mainly composed of the framework's own scheduling and event dispatch overhead; `fibonacci` is an iterative `O(n)` implementation and `fib(50~80)` also takes only a few dozen loops, so the per-task computation difference between the "light" and "heavier" groups is at the microsecond level.
- In **light tasks**, the **relative difference** introduced by observers is more noticeable (up to ~50% in the historical single-round data), but the direction is not stable (print even showed a negative value); the absolute time is only at the millisecond level, and single-round values are dominated by measurement noise, so multi-round averages should be used.
- The total time of the 7 tasks in **heavier tasks** (fib 50~80) is instead lower, mainly because there are fewer tasks, not because "computation time dominates"; both workloads in this script are too light, so no conclusion such as "observer overhead becomes negligible once a single task exceeds 1ms" can be drawn from them.
- To evaluate observer overhead under realistic business workloads, switch to a per-task time of at least the millisecond level and then compare the three scenarios.

## How to Run

```bash
python bench/bench_observer.py
```

## Parameter Tuning

### Running a Single Test Scenario in Isolation

In `main()` of `bench_observer.py`, you can choose to run either the single-round comparison or the multi-round average test:

```python
def main():
    # Run single-round comparison only
    bench_observer_overhead()

    # Run multi-round average only
    # bench_observer_multirun()
```

After modification, run:

```bash
python bench/bench_observer.py
```

### Customizing Task Scale

Modify the task list in `bench_observer_overhead()` or `bench_observer_multirun()`:

```python
# Use larger computation to observe the overhead ratio of observers
heavy_tasks: list[Any] = list(range(80, 90))  # fib(80)~fib(89)

# Use more light tasks
light_tasks: list[Any] = list(range(10, 50))  # 40 light tasks
```

### Adjusting Data Volume and Number of Rounds

```python
# Modify rounds in bench_observer_multirun()
runs = 10  # Change from 5 to 10 for more stable averages
```

## Dependencies

- `celestialflow` (`Observer`, `PrintObserver`, `TaskExecutor`, plus the various event types under `celestialflow.observer`)
- `tqdm` (used by `TqdmObserver`)
