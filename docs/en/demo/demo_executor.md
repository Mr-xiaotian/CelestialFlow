# demo_executor.py Demo Documentation

> 📅 Last updated: 2026/04/22

## Purpose

Demonstrates the standalone execution capability of `TaskExecutor` in three execution modes (`serial`, `thread`, `async`). Showcases the complete lifecycle of exception retry, progress display, and task statistics, making it ideal as a first hands-on experience with the framework.

## Demo Contents

| Function | Mode | Task | Feature |
|----------|------|------|---------|
| `demo_fibonacci_serial` | serial | Fibonacci calculation | Single-threaded sequential execution |
| `demo_fibonacci_thread` | thread | Fibonacci calculation | 6-thread concurrency |
| `demo_fibonacci_async` | async | Async Fibonacci | Coroutine concurrency |

- **Input**: `range(25, 32) + [0, 27, None, 0, ""]`
- **Exception design**: `0`, `None`, `""` trigger `ValueError`; the framework automatically retries once

## Key Configuration

- `max_workers = 6`
- `max_retries = 1`
- `show_progress = False` (disables tqdm to avoid cluttered output during demos)

## Potential Issues

1. **Recursion depth and execution time**: `fibonacci(31)` involves a massive number of recursive calls and may take over 10 seconds in serial mode.
2. **`asyncio` environment**: `demo_fibonacci_async` uses `asyncio.run()`, which will fail when run directly in Jupyter Notebook (Notebook already has an event loop).
3. **No assertions**: This is a **demo script** and contains no `assert` statements. A successful run only means no uncaught exceptions were raised; it does not verify result correctness.

## How to Run

```bash
python demo/demo_executor.py
```

## Dependencies

- `celestialflow` (`TaskExecutor`)
- `demo_utils` (`fibonacci`, `fibonacci_async`)
