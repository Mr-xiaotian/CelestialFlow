# Log Persistence

> 📅 Last Updated: 2026/05/09

The `celestialflow.persistence` module provides a multi-process-safe logging system designed to solve the problems of unified log collection, formatting, and persistence in multi-process environments.

The core components include `LogSpout` and `LogInlet`.

## Architecture Design

Similar to error persistence, the logging system also uses the **Logger-Listener** pattern:

1.  **LogInlet (Producer)**:
    -   A wrapper class held by each Worker thread.
    -   Provides rich semantic methods (such as `task_success`, `start_stage`, etc.).
    -   Packages log messages and levels, then places them into a thread-safe queue (`queue.Queue`).
    -   Supports log-level-based filtering to reduce unnecessary communication.

2.  **LogSpout (Consumer)**:
    -   Runs in an independent daemon thread.
    -   Retrieves log records from the queue and writes them to files.
    -   Manages log file rotation and formatting uniformly.

## Log Levels

The system supports the following standard log levels (higher values indicate higher priority):

-   **TRACE** (0): Most detailed trace information, such as queue `put`/`get` operations.
-   **DEBUG** (10): Debug information, such as process exit, task input, etc.
-   **SUCCESS** (20): Key operation success, such as task completion, split success.
-   **INFO** (30): General information, such as stage start/end, graph structure printing.
-   **WARNING** (40): Warning information, such as task retry, queue operation exceptions.
-   **ERROR** (50): Error information, such as task failure, loop exceptions.
-   **CRITICAL** (60): Critical errors.

## LogSpout

`LogSpout` manages log file configuration and the writing thread.

### Initialization

```python
listener = LogSpout()
listener.start()
```

After startup, logs will be written to the `logs/task_logger({date}).log` file.

### File Path

```text
logs/
└── task_logger(2023-10-27).log
```

## LogInlet

`LogInlet` provides specialized log methods for different components, ensuring log content is structured and consistent.

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
-   `start_layer` / `end_layer`: Records execution of each layer in staged scheduling.

#### Task Lifecycle
-   `task_input`: Task enters the input queue.
-   `task_success`: Task completed successfully, records result summary and duration.
-   `task_retry`: Task failed but triggered retry.
-   `task_error`: Task failed and cannot be retried (final failure).
-   `task_duplicate`: Duplicate task detected.

#### Task Flow
-   `split_trace` / `split_success`: Records task splitting process.
-   `route_success`: Records task routing result.
-   `put_item` / `get_item`: Records low-level queue operations (TRACE level).

#### Reporter
-   `push_*_failed`: Records warnings about failed data pushes to the Web server.
-   `pull_*_failed`: Records warnings about failed configuration pulls from the Web server.

By using these specialized methods instead of generic `info()` or `debug()`, the generated logs are easier to read and parse by machines.
