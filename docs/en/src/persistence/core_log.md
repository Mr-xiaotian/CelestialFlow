# Log Persistence

> 📅 Last updated: 2026/04/22

The `celestialflow.persistence` module provides a multi-process-safe logging system designed to solve the problems of unified log collection, formatting, and persistence in multi-process environments.

The core components are `LogSpout` and `LogInlet`.

## Architecture Design

Similar to error persistence, the logging system also uses a **Logger-Listener** pattern:

1.  **LogInlet (Producer)**:
    -   A wrapper class held by each Worker process.
    -   Provides rich semantic methods (such as `task_success`, `start_stage`, etc.).
    -   Packages log messages and levels and places them in a multi-process queue (`multiprocessing.Queue`).
    -   Supports log-level-based filtering to reduce unnecessary cross-process communication.

2.  **LogSpout (Consumer)**:
    -   Runs in an independent daemon thread in the main process.
    -   Retrieves log records from the queue and writes them to files.
    -   Manages log file rotation and formatting centrally.

## Log Levels

The system supports the following standard log levels (higher values indicate higher priority):

-   **TRACE** (0): Most detailed tracing information, such as queue `put`/`get` operations.
-   **DEBUG** (10): Debug information, such as process exit, task input, etc.
-   **SUCCESS** (20): Critical operation success, such as task completion, split success.
-   **INFO** (30): General information, such as stage start/end, graph structure output.
-   **WARNING** (40): Warning information, such as task retry, queue operation anomalies.
-   **ERROR** (50): Error information, such as task failure, loop exceptions.
-   **CRITICAL** (60): Critical errors.

## LogSpout

`LogSpout` manages log file configuration and the writing thread.

### Initialization

```python
listener = LogSpout()
listener.start()
```

Upon startup, logs are written to the `logs/task_logger({date}).log` file.

### File Path

```text
logs/
└── task_logger(2023-10-27).log
```

## LogInlet

`LogInlet` provides dedicated logging methods for different components, ensuring structured and consistent log content.

### Initialization

```python
sinker = LogInlet(log_queue, log_level="SUCCESS")
```

-   `log_queue`: The queue returned by `LogSpout.get_queue()`.
-   `log_level`: Sets the minimum log level for this Inlet; logs below this level will not be sent to the queue.

### Common Methods

#### Task Execution (Executor)
-   `start_executor(...)`: Records executor startup.
-   `end_executor(...)`: Records executor completion, including duration and statistics.

#### Stage & Layer
-   `start_stage` / `end_stage`: Records stage lifecycle.
-   `start_layer` / `end_layer`: Records execution details for each layer in layered scheduling.

#### Task Lifecycle
-   `task_input`: Task enters the input queue.
-   `task_success`: Task completed successfully, records result summary and duration.
-   `task_retry`: Task failed but triggers retry.
-   `task_error`: Task failed and cannot be retried (final failure).
-   `task_duplicate`: Duplicate task detected.

#### Task Flow
-   `split_trace` / `split_success`: Records task splitting process.
-   `route_success`: Records task routing results.
-   `put_item` / `get_item`: Records low-level queue operations (TRACE level).

#### Reporter
-   `push_*_failed`: Records warnings for failed data pushes to the Web server.
-   `pull_*_failed`: Records warnings for failed configuration pulls from the Web server.

By using these dedicated methods instead of generic `info()` or `debug()`, the generated logs are easier to read and machine-parse.
