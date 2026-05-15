# Observability Module

> 📅 Last Updated: 2026/05/08

The Observability module provides observability features for CelestialFlow, including runtime status monitoring, performance metrics collection, error tracking, and remote control. It makes the task execution process transparent, monitorable, and controllable.

## Module Overview

The Observability module is responsible for collecting, aggregating, and reporting system runtime status, providing real-time monitoring views and remote control capabilities. Through this module, users can monitor task execution status, performance metrics, and error information in real-time, and dynamically adjust system behavior.

## File Description

### Core Components

1. **core_observer.py** (`BaseObserver`, `CallbackObserver`)
   - **Purpose**: Base class and callback-style observer for executor lifecycle
   - **Key Features**:
     - **BaseObserver**: Defines lifecycle event interfaces (`on_start`, `on_task_success`, `on_task_fail`, `on_task_duplicate`, `on_tasks_added`, `on_finish`); subclasses override as needed
     - **CallbackObserver**: Passes callback functions via keyword arguments, no need to define subclasses

2. **core_report.py** (`TaskReporter`)
   - **Purpose**: Task status reporter that collects runtime status and reports to a remote Web server
   - **Key Features**:
     - **Status Reporting**: Periodically pushes task graph structure, topology, runtime status, and error information
     - **Task Injection**: Receives user-injected new tasks from the Web UI and dynamically inserts them into the running task graph
     - **Parameter Adjustment**: Pulls configuration from the server to dynamically adjust reporting interval and other parameters
     - **Error Synchronization**: Supports two error push modes (metadata mode and content mode)
   - **Communication Protocol**: HTTP
   - **Data Format**: JSON

3. **core_progress.py** (`TaskProgress`)
   - **Purpose**: Task progress visualization based on `tqdm`, inheriting `BaseObserver`
   - **Key Features**:
     - Creates a progress bar on `on_start`
     - Updates progress on `on_task_success/fail/duplicate`
     - Dynamically increases total task count on `on_tasks_added`
     - Closes the progress bar on `on_finish`

## Module Dependencies

### Internal Dependencies
- `BaseObserver` is the base class of the observer pattern; `TaskProgress` and `CallbackObserver` are both based on it
- `TaskReporter` is an independent reporting component, designed to be pluggable

### External Dependencies
- **Stage Module**: `TaskExecutor` holds `list[BaseObserver]` and manages observers via `add_observer()` / `remove_observer()`
- **Graph Module**: Collects task graph structure and topology information
- **Runtime Module**: Collects execution status, performance metrics, and error information
- **Persistence Module**: Retrieves persisted log and error data
- **Web Module**: Bidirectional communication with the Web UI for status display and remote control

## Architecture Characteristics

### Observer Pattern
- **Multicast**: `TaskExecutor` internally maintains `list[BaseObserver]` and broadcasts events at lifecycle points
- **Synchronous Dispatch**: Events are synchronously dispatched to all observers via `_notify(method_name, *args, **kwargs)`
- **Empty List Equivalent to Null**: When the observer list is empty, there is no overhead

### Bidirectional Communication (TaskReporter)
- **Uplink Channel**: Status data reported to the Web server
- **Downlink Channel**: Control commands sent from the Web server to the running instance
- **Real-time**: Supports real-time status updates and instant control

### Fault Tolerance Design
- Local caching and retry on network interruption
- Graceful degradation without affecting the main execution flow

## Usage Patterns

### Observer Usage
```python
from celestialflow import TaskExecutor, TaskProgress, CallbackObserver

# Use TaskProgress to display a progress bar
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
