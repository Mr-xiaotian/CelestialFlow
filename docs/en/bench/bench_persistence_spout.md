# bench_persistence_spout.py Benchmark Guide

> 📅 Last Updated: 2026/06/17

## Objective

Evaluate the throughput ceiling of persistence-related `spout` instances in the "queue pre-populated with many records, only measuring background consumption and writes" scenario.

This script currently covers two targets:

- `LogSpout`
- `FallbackSpout`

Where:

- `LogSpout` measures single-threaded log file write queue drain speed
- `FallbackSpout` measures transaction throughput of SQLite fallback in "direct `commit()` after each valid change" mode

## Test Content

| Test Item | Description | Timing Scope |
|--------|------|----------|
| `LogSpout` | Pre-build log records and push them into the queue, then start `spout` to drain the queue | `start()` to `stop()` |
| `FallbackSpout` | Pre-build `insert` records and push them into the queue, then start `spout` to drain the queue | `start()` to `stop()` |

The script uses the following model:

```text
preload queue -> start spout -> drain all queued records
```

Thus the test results are closer to "peak processing speed of the background writer", excluding the cost of real-time data production by the caller.

## Key Configuration

- `--log-count`: default `200_000`
- `--fallback-count`: default `20_000`
- `LogSpout` writes to `bench_task_logger.log` in a temporary directory
- `FallbackSpout` writes to `bench_fallback.sqlite3` in a temporary directory
- `FallbackSpout` uses the current project implementation, i.e., "direct `commit()` after each valid change"

## Potential Issues

1. **`LogSpout` results do not equal real disk forced flush frequency**: The current test does not perform explicit `flush()` or `fsync()` for each record; what is measured is closer to file buffer and page cache write speed.
2. **`FallbackSpout`'s bottleneck is primarily transaction commits**: The results largely reflect SQLite `commit()` throughput under the current disk and transaction mode, not just Python loop overhead.
3. **Start/stop costs can amplify small-sample results**: When the record count is too low, the fixed costs of thread startup, stop signal, and final `commit()` become magnified.
4. **Instability may occur with large samples**: Locally, larger samples `--log-count 500000 --fallback-count 50000` were attempted; `LogSpout` completed normally, but the `FallbackSpout` phase experienced one interpreter crash, so it is recommended to treat that scale as a stress exploration value, not a stable baseline.

## Benchmark Results (Measured)

### 2026/06/17 - Windows local first measurement

> Environment: Windows, local `.venv`, model "pre-populate queue then start spout to drain", `log-count=200000`, `fallback-count=20000`

| Test Item | Record Count | Total Time | Throughput | Avg Time per Record |
|--------|--------|--------|------|--------------|
| `LogSpout` | 200,000 | 0.2036s | 982,287.88 records/s | 1.02 us |
| `FallbackSpout` | 20,000 | 3.2515s | 6,151.08 records/s | 162.57 us |

**Conclusions for this round**:

- `LogSpout` is already close to one million records per second, indicating that under the current implementation the log write bottleneck is not primarily on the Python side
- `FallbackSpout` is approximately 6.1k records per second, clearly limited by SQLite single-transaction commit
- The throughput gap between the two is approximately **160x**

### 2026/06/17 - Windows local retest (moderately enlarged samples)

> Environment: Windows, local `.venv`, same model, `log-count=300000`, `fallback-count=30000`

| Test Item | Record Count | Total Time | Throughput | Avg Time per Record |
|--------|--------|--------|------|--------------|
| `LogSpout` | 300,000 | 0.2960s | 1,013,446.75 records/s | 0.99 us |
| `FallbackSpout` | 30,000 | 4.6633s | 6,433.23 records/s | 155.44 us |

**Supplementary conclusions for this round**:

- `LogSpout` remains stable at about **1 million records/s** after sample enlargement
- `FallbackSpout` remains stable at about **6.4k records/s** after sample enlargement
- Under the current machine and implementation, `log` is not the bottleneck; `fallback/sqlite` is the primary limiting factor

## How to Run

```bash
python bench/bench_persistence_spout.py
```

If the project is not installed as an importable package, you can also directly use the local virtual environment interpreter:

```bash
.\.venv\Scripts\python.exe bench/bench_persistence_spout.py
```

## Parameter Tuning

### Adjust log sample count

```bash
python bench/bench_persistence_spout.py --log-count 500000
```

### Adjust fallback sample count

```bash
python bench/bench_persistence_spout.py --fallback-count 50000
```

### Adjust both sample types simultaneously

```bash
python bench/bench_persistence_spout.py --log-count 300000 --fallback-count 30000
```

## Dependencies

- Python standard library
- `celestialflow.persistence` from project source
