# demo_executor.py Demo Documentation

> 📅 Last Updated: 2026/05/08

## Purpose

Demonstrates the standalone execution capabilities of `TaskExecutor` in three execution modes (`serial`, `thread`, `async`). Showcases the complete lifecycle of exception retries, progress display, and task statistics, serving as a first-hand introductory experience to the framework.

## Demo Contents

| Function | Mode | Task | Features |
|----------|------|------|----------|
| `demo_fibonacci_serial` | serial | Fibonacci computation | Single-threaded sequential execution |
| `demo_fibonacci_thread` | thread | Fibonacci computation | 6-thread concurrent execution |
| `demo_fibonacci_async` | async | Async Fibonacci | Coroutine-based concurrency |

- **Input**: `range(25, 32) + [0, 27, None, 0, ""]`
- **Exception design**: `0`, `None`, `""` trigger `ValueError`; the framework auto-retries once

## Key Configuration

- `max_workers = 6`
- `max_retries = 1`
- Progress bar added via `executor.add_observer(TaskProgress())`

## Potential Issues

1. **Recursion depth and duration**: `fibonacci(31)` involves a massive number of recursive calls and may take over 10 seconds in serial mode.
2. **`asyncio` environment**: `demo_fibonacci_async` uses `asyncio.run()`, which will fail when run directly in Jupyter Notebook (Notebook already has an event loop).
3. **No assertions**: This file is a **demo script** and contains no `assert` statements. Successful execution only means no uncaught exceptions were thrown; it does not verify result correctness.

## How to Run

```bash
python demo/demo_executor.py
```

## Dependencies

- `celestialflow` (`TaskExecutor`, `TaskProgress`)
- `demo_utils` (`fibonacci`, `fibonacci_async`)
