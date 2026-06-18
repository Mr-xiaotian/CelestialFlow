# bench_gil_vs_nogil.py Benchmark Guide

> 📅 Last Updated: 2026/06/18

## Objective

Compare the behavior of `CelestialFlow` when running under Python 3.14 standard edition (GIL enabled) versus the free-threading edition (GIL disabled), with focus on two capabilities:

- Throughput changes when `TaskExecutor` runs CPU tasks in thread mode
- Overall speedup of `TaskGraph` in a threaded pipeline

This benchmark does not automatically launch two Python environments within a single process — it only tests the **current interpreter**. Therefore, you must run it once each in the GIL and No-GIL environments, then manually compare results.

## Test Content

Script file: `bench/bench_gil_vs_nogil.py`

| Workload | Description |
|------|------|
| `executor_cpu_serial` | `TaskExecutor` serial execution of CPU-intensive tasks |
| `executor_cpu_thread` | `TaskExecutor` threaded execution of CPU-intensive tasks |
| `graph_cpu_pipeline_serial` | 3-stage `TaskGraph` serial CPU pipeline |
| `graph_cpu_pipeline_thread` | 3-stage `TaskGraph` threaded CPU pipeline |
| `graph_io_pipeline_thread` | 3-stage `TaskGraph` threaded I/O pipeline |

### Workload Design

- **CPU tasks**: Execute pure Python integer loops and hash-based mixed operations, aiming to stress Python bytecode execution overhead
- **I/O tasks**: `time.sleep()` to simulate blocking waits
- **Graph structure**: Fixed as a simple 3-stage series pipeline to avoid topology differences confounding results
- **Log level**: Unified to `CRITICAL` to minimize log overhead contaminating the benchmark
- **Repetitions**: Each workload runs 3 times by default, with average / min / max statistics

## Key Configuration

Default parameters:

| Parameter | Default | Description |
|------|--------|------|
| `repeats` | `3` | Number of repetitions per workload |
| `workers` | `0` | Automatically set to `min(os.cpu_count(), 16)` |
| `cpu_tasks` | `128` | Number of CPU tasks for `TaskExecutor` |
| `cpu_loops` | `120000` | Loop intensity per CPU task |
| `pipeline_tasks` | `96` | Number of pipeline tasks for `TaskGraph` |
| `pipeline_loops` | `60000` | Loop intensity for pipeline CPU tasks |
| `io_tasks` | `96` | Number of I/O pipeline tasks |
| `io_sleep_ms` | `10.0` | Sleep duration per I/O task (milliseconds) |

## How to Run

Since the script only tests the current interpreter, please run it in two separate Python 3.14 environments.

### Running in GIL Environment

```bash
python bench/bench_gil_vs_nogil.py --json-out bench_gil_result.json
```

### Running in No-GIL Environment

```bash
python bench/bench_gil_vs_nogil.py --json-out bench_nogil_result.json
```

If you maintain two `uv` virtual environments locally as in the example, you can also invoke them explicitly:

```powershell
.\gil\.venv\Scripts\python.exe .\bench\bench_gil_vs_nogil.py --json-out .\bench_gil_result.json
.\no-gil\.venv\Scripts\python.exe .\bench\bench_gil_vs_nogil.py --json-out .\bench_nogil_result.json
```

## Parameter Tuning

### Adjust worker count

```bash
python bench/bench_gil_vs_nogil.py --workers 8
```

### Reduce task scale for quick validation

```bash
python bench/bench_gil_vs_nogil.py \
  --repeats 1 \
  --workers 4 \
  --cpu-tasks 16 \
  --cpu-loops 20000 \
  --pipeline-tasks 12 \
  --pipeline-loops 10000 \
  --io-tasks 12 \
  --io-sleep-ms 2
```

### Increase CPU pressure

```bash
python bench/bench_gil_vs_nogil.py --cpu-loops 200000 --pipeline-loops 100000
```

## Potential Issues

1. **Must run twice separately**: The script does not automatically switch Python environments. You need to collect both outputs yourself when comparing results.
2. **First run writes to fallback sqlite**: `TaskExecutor` / `TaskGraph` create a `fallback/` directory at runtime, so the script first changes the working directory to the repository root to avoid temporary path or permission issues.
3. **Do not mix results from different parameters**: If the GIL and No-GIL runs use different parameters, the results are not comparable.
4. **CPU frequency fluctuations may affect results**: Under Windows, background load, thermal management, and power policies can cause jitter in individual runs, hence the default of 3 repetitions with averaging.

## Benchmark Results (Measured)

### 2026/06/18 - Windows 11 / Python 3.14.3 / 8 workers

> Parameters used:
> `repeats=3, workers=8, cpu_tasks=96, cpu_loops=100000, pipeline_tasks=72, pipeline_loops=50000, io_tasks=72, io_sleep_ms=10`

| Workload | GIL Mean | No-GIL Mean | No-GIL Relative Performance |
|------|-----------|--------------|------------------|
| `executor_cpu_serial` | 1.1148s | 1.0836s | **1.03x** |
| `executor_cpu_thread` | 1.1191s | 0.2131s | **5.25x** |
| `graph_cpu_pipeline_serial` | 1.3526s | 1.2443s | **1.09x** |
| `graph_cpu_pipeline_thread` | 1.4777s | 0.1957s | **7.55x** |
| `graph_io_pipeline_thread` | 0.1514s | 0.1322s | **1.15x** |

Where:

```text
No-GIL Relative Performance = GIL mean time / No-GIL mean time
```

Values greater than `1.00x` indicate No-GIL is faster.

### Result Interpretation

- **Serial CPU mode shows little difference**: `executor_cpu_serial` and `graph_cpu_pipeline_serial` only improved by about `3% ~ 9%`, indicating that No-GIL does not magically accelerate single-threaded pure Python execution.
- **Threaded CPU mode shows significant improvement**: `executor_cpu_thread` achieved about **5.25x**, and `graph_cpu_pipeline_thread` reached about **7.55x**.
- **Graph-level threaded pipeline shows greater improvement**: Compared to single-executor thread mode, `TaskGraph`'s threaded pipeline more fully leverages the parallelism offered by free-threading.
- **I/O mode shows improvement but is not the main story**: `graph_io_pipeline_thread` only leads by about **15%**, consistent with the intuition that I/O waits already achieve reasonable concurrency under the GIL.

## Applicable Scenarios

This benchmark is suitable for answering the following questions:

- If `CelestialFlow` is deployed to a Python 3.14 No-GIL environment, how much improvement can threaded mode provide?
- Which layer — `TaskExecutor` or `TaskGraph` — benefits more noticeably from No-GIL?
- Is the current workload closer to CPU-threaded type or I/O type?

If your goal is:

- **Compare async / thread / serial execution modes**: Prefer `bench_execution_mode.py`
- **Compare different graph modes / DAG topology combinations**: Prefer `bench_graph_mode.py`
- **Specifically compare GIL vs. No-GIL differences in the Python interpreter**: Use this file

## Dependencies

- `celestialflow`
- Python 3.14 standard edition (GIL)
- Python 3.14 free-threading edition (No-GIL)
