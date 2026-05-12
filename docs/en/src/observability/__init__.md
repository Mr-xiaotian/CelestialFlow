# Observability Module

> 📅 Last updated: 2026/05/08

The Observability module provides monitoring, metrics collection, error tracking, and remote control capabilities for CelestialFlow, making task execution transparent and controllable.

## Module Overview

The Observability module collects, aggregates, and reports system runtime status, providing real-time monitoring and remote control. Users can monitor task execution status, performance metrics, and error information in real time.

## File Description

### Core Components

1. **core_observer.py** (`BaseObserver`, `CallbackObserver`)
   - **Purpose**: Executor lifecycle observer base class and callback-based observer
   - **Key Features**:
     - **BaseObserver**: Defines lifecycle event interface (`on_start`, `on_task_success`, `on_task_fail`, `on_task_duplicate`, `on_tasks_added`, `on_finish`); subclasses override as needed
     - **CallbackObserver**: Accepts callback functions via keyword arguments, no subclassing required

2. **core_report.py** (`TaskReporter`)
   - **Purpose**: Task status reporter that collects and reports runtime status to a remote Web server
   - **Key Features**:
     - **Status Reporting**: Periodically pushes task graph structure, topology, runtime status, and error information
     - **Task Injection**: Receives user-injected tasks from Web UI and dynamically inserts them into the running task graph
     - **Parameter Adjustment**: Pulls configuration from the server to dynamically adjust reporting intervals
     - **Error Sync**: Supports two error push modes (metadata mode and content mode)
   - **Protocol**: HTTP
   - **Data Format**: JSON

3. **core_progress.py** (`TaskProgress`)
   - **Purpose**: tqdm-based task progress visualization, inherits `BaseObserver`
   - **Key Features**:
     - Creates progress bar via `on_start`
     - Updates progress via `on_task_success/fail/duplicate`
     - Dynamically increases total via `on_tasks_added`
     - Closes progress bar via `on_finish`

## Module Relations

### Internal
- `BaseObserver` is the observer pattern base class; `TaskProgress` and `CallbackObserver` are both built on it
- `TaskReporter` is an independent pluggable reporting component

### External
- **Stage Module**: `TaskExecutor` holds `list[BaseObserver]`, managed via `add_observer()` / `remove_observer()`
- **Graph Module**: Collects task graph structure and topology
- **Runtime Module**: Collects execution status, metrics, and error information
- **Persistence Module**: Retrieves persisted logs and error data
- **Web Module**: Bidirectional communication with Web UI

## Architecture

### Observer Pattern
- **Multicast**: `TaskExecutor` maintains `list[BaseObserver]`, broadcasting events at lifecycle points
- **Synchronous dispatch**: Events dispatched via `_notify(method_name, *args, **kwargs)`
- **Empty list = no-op**: No overhead when observer list is empty

### Bidirectional Communication (TaskReporter)
- **Upstream**: Status data reported to Web server
- **Downstream**: Control commands from Web server to running instance

## Usage

### Observer Usage
```python
from celestialflow import TaskExecutor, TaskProgress, CallbackObserver

# Use TaskProgress for progress bar
executor = TaskExecutor("Test", my_func)
executor.add_observer(TaskProgress())
executor.start(tasks)

# Use CallbackObserver for custom behavior
observer = CallbackObserver(
    on_task_success=lambda count=1: print(f"Success: {count}"),
    on_finish=lambda: print("Done"),
)
executor.add_observer(observer)
```

### TaskReporter Usage
```python
from celestialflow.observability import TaskReporter

reporter = TaskReporter(
    host="127.0.0.1",
    port=5000,
    task_graph=my_task_graph,
    log_inlet=log_inlet,
)
reporter.start()
```
