# bench_observer.py Benchmark Guide

> 📅 Last Updated: 2026/08/26

## Objective

Compare the execution time of `TaskExecutor` under three scenarios for the same batch of tasks—**no observer**, **print logging** (`PrintObserver`), and **tqdm progress bar** (`TqdmObserver`)—to quantify the performance overhead introduced by observer callbacks.

Help users choose an appropriate observation strategy based on task scale and real-time feedback needs.

## Test Content

### Observer Strategy Comparison

| Scenario | Observer | Description |
|------|--------|------|
| **No observer** | `None` | Bare executor with no callback output, used as the baseline |
| **print logging** | `PrintObserver` | Executes `print()` on every lifecycle event, simulating simple log output |
| **tqdm progress bar** | `TqdmObserver` | Updates a `tqdm` progress bar on every lifecycle event, providing visual feedback |

### Task Workload

Two Fibonacci task sets with different computation amounts:

```python
# Light tasks: fib(20~29), 10 tasks in total, small per-task computation
light_tasks = list(range(20, 30))

# Heavy tasks: fib(50, 55, 60, 65, 70, 75, 80), 7 tasks in total, larger per-task computation
heavy_tasks = [50, 55, 60, 65, 70, 75, 80]
```

## Key Parameters

| Parameter | Value | Description |
|------|-----|------|
| `execution_mode` | `serial` | All scenarios use serial mode to control variables and isolate observer impact |
| `max_workers` | 1 | Single worker to avoid parallel scheduling interference |
| `max_retries` | 0 | No retries, eliminating extra time from retry logic |

## Potential Issues

1. **TTY buffering of print**: `print()` defaults to line-buffered; when output goes to a real terminal, screen refresh may be triggered, which is slower than redirecting to a file. The overhead of `print` may differ across terminal environments.
2. **`tqdm`'s `total=0` initial value**: `TaskExecutor` has not resolved the total task count when `add_observer` is called, so `total` is 0 in `on_start` and is not updated until `on_tasks_added`. `TqdmObserver` handles this scenario (initially setting `total=0` and dynamically expanding in `on_tasks_added`), but this does not affect the correctness of the benchmark results.
3. **Warm-up effect**: The first run may be affected by bytecode cache warm-up, import initialization, or system cache, making subsequent rounds faster. `bench_observer_multirun()` mitigates this by averaging across multiple rounds.
4. **Fibonacci computation itself is already small enough**: For light tasks, the I/O overhead of observer callbacks may dominate; the absolute numbers from benchmarks will vary by machine, but the **relative ratios** should remain consistent across platforms.

## Benchmark Results (Measured)

> 🟢 All timing data in the tables of this section is historical measured data and cannot be verified from source code; manual confirmation is required.

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

- In serial mode, the additional overhead of observers is closely related to the computation amount of the task itself.
- In **light tasks**, the I/O overhead of tqdm and print is relatively noticeable, and the gap among the three schemes can reach ~50%.
- In **heavy tasks** (fib 50~80), computation time dominates; the absolute time of the three schemes is nearly identical, and observer overhead is negligible.
- When a single task takes more than **1ms**, choosing print or tqdm has minimal impact on overall performance; pick based on needs.

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

- `celestialflow` (`TaskExecutor`, `BaseObserver`)
- `tqdm` (used by `TqdmObserver`)
