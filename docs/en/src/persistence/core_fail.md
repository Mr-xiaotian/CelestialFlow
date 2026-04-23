# Fail Persistence

> 📅 Last updated: 2026/04/22

The `celestialflow.persistence` module provides a robust error collection and persistence mechanism, ensuring that all exception information can be safely and orderly recorded during multi-process concurrent task execution for subsequent analysis or retry.

The core components are `FailSpout` and `FailInlet`.

## Architecture Design

The system uses a **producer-consumer** pattern to handle error logs:

1.  **FailInlet (Producer)**:
    -   Held by each Worker process (or thread).
    -   Responsible for packaging error information and task metadata into dictionaries.
    -   Places the packaged data into a multi-process-safe queue (`multiprocessing.Queue`).

2.  **FailSpout (Consumer)**:
    -   Runs in an independent daemon thread in the main process.
    -   Continuously listens to the queue and immediately writes new error records to a local file.
    -   File format is JSONL (JSON Lines), facilitating streaming reading and processing.

This design avoids multi-process contention for file write locks, ensuring high performance and data integrity.

## FailSpout

`FailSpout` manages error log file creation and writing.

### Initialization and Startup

```python
listener = FailSpout(error_source="graph_errors")
listener.start()
```

-   `error_source`: Error source identifier, used as part of the file name.
-   Upon startup, creates a file named `{error_source}({time}).jsonl` in the `./fallback/{date}/` directory.

### File Path

Error logs are saved by default in the `./fallback/` directory, archived by date:

```text
./fallback/
└── 2023-10-27/
    └── graph_errors(14-30-05-123).jsonl
```

### Stopping the Listener

```python
listener.stop()
```

Sends a termination signal to the queue and waits for the background thread to finish processing remaining data before safely exiting.

## FailInlet

`FailInlet` is the interface for sending data to the error queue.

### Recording Task Errors

When a task fails and cannot be retried, `TaskExecutor` calls the `task_error` method to record the error:

```python
sinker.task_error(
    stage_tag="MyStage",
    error=ValueError("Invalid input"),
    err_id=12345,
    task=[1, 2, 3]
)
```

Each recorded JSONL line contains the following fields:
-   `timestamp`: Time of the error (ISO format)
-   `stage`: Stage tag where the error occurred
-   `error_repr`: String representation of the error message (truncated)
-   `task_repr`: String representation of the task data (truncated)
-   `error`: Full error type and message
-   `task`: Original task data
-   `error_id`: Unique identifier for the error
-   `ts`: Raw timestamp

### Recording Metadata

`FailInlet` also supports recording metadata to help reconstruct the execution environment at the time:

-   `start_graph(structure_json)`: Records the task graph structure information.
-   `start_executor(executor_tag)`: Records the executor startup information.

```python
sinker.start_graph({...})
```

## Data Recovery

Since error logs use the standard JSONL format, you can easily write scripts to read these files and extract failed task data for retry or analysis. The `celestialflow.persistence.util_jsonl.load_jsonl_logs` function provided by the framework can assist with reading.
