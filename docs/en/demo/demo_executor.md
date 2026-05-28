# demo_executor.py Demo Documentation

> 📅 Last Updated: 2026/05/28

## Purpose

Demonstrates the standalone execution capabilities of `TaskExecutor` in three execution modes (`serial`, `thread`, `async`). Showcases the complete lifecycle of exception retries, progress display, and task statistics, serving as a first-hand introductory experience to the framework.

## Demo Contents

Core strategy comparison of the three execution modes:

```mermaid
flowchart TB
    subgraph Serial["Serial Mode serial"]
        direction LR
        T1_1["Task 1<br/>fibonacci(25)"] --> T1_2["Task 2<br/>fibonacci(26)"]
        T1_2 --> T1_3["..."]
        T1_3 --> T1_4["Task 7<br/>fibonacci(31)"]
    end

    subgraph Thread["Thread Mode thread"]
        direction LR
        T2_1["Task 1<br/>fibonacci(25)"]
        T2_2["Task 2<br/>fibonacci(26)"]
        T2_3["Task 3<br/>fibonacci(27)"]
        T2_4["Task 4<br/>fibonacci(28)"]
        T2_5["Task 5<br/>fibonacci(29)"]
        T2_6["Task 6<br/>fibonacci(30)"]
        T2_7["Task 7<br/>fibonacci(31)"]
    end

    subgraph Async["Async Mode async"]
        direction LR
        T3_1["Task 1<br/>fibonacci_async(25)"]
        T3_2["Task 2<br/>fibonacci_async(26)"]
        T3_3["Task 3<br/>fibonacci_async(27)"]
        T3_4["Task 4<br/>fibonacci_async(28)"]
        T3_5["Task 5<br/>fibonacci_async(29)"]
        T3_6["Task 6<br/>fibonacci_async(30)"]
        T3_7["Task 7<br/>fibonacci_async(31)"]
    end

    Input["Input<br/>range(25,32) + [0,27,None,0,'']"] --> Serial
    Input --> Thread
    Input --> Async

    Serial --> Retry["Auto-retry once<br/>max_retries=1"]
    Thread --> Retry
    Async --> Retry
```

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

1. **Recursion depth and duration**: `fibonacci(31)` involves extremely heavy recursive calls and may take over 10 seconds in serial mode.
2. **`asyncio` environment**: `demo_fibonacci_async` uses `asyncio.run()`, which will fail when run directly in Jupyter Notebook (Notebook already has an event loop).
3. **No assertions**: This file is a **demo script** and contains no `assert` statements. Successful execution only means no uncaught exceptions were thrown; it does not verify result correctness.

## How to Run

```bash
python demo/demo_executor.py
```

## Expected Behavior

Running the script will execute the three modes sequentially, producing output similar to:

```
========================================
[serial] Fibonacci benchmark (N=12 tasks, max_workers=6)
========================================
 80%|████████████████░░░░| ...

--- Summary ---
  mode=serial  success=07  fail=05  dup=0  pending=0  elapsed=0.90s

========================================
[thread] Fibonacci benchmark (N=12 tasks, max_workers=6)
========================================
 80%|████████████████░░░░| ...

--- Summary ---
  mode=thread  success=07  fail=05  dup=0  pending=0  elapsed=0.86s

========================================
[async] Fibonacci benchmark (N=12 tasks, max_workers=6)
========================================
 80%|████████████████░░░░| ...

--- Summary ---
  mode=async  success=07  fail=05  dup=0  pending=0  elapsed=0.01s
```

> **Note**: Of the 12 tasks, 5 edge case inputs (`0`, `27`, `None`, `0`, `""`) trigger `ValueError` and are ultimately marked as failed after retries; `success=07` represents the 7 normal Fibonacci tasks.
> All three modes use the iterative Fibonacci implementation (O(n)) from `demo_utils`, making performance comparable.

## Dependencies

- `celestialflow` (`TaskExecutor`, `TaskProgress`)
- `demo_utils` (`fibonacci`, `fibonacci_async`)
