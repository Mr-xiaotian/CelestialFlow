# Observability Module

> 📅 Last Updated: 2026/05/24

The Observability module provides observability features for CelestialFlow, including runtime status monitoring, performance metrics collection, error tracking, and remote control. It makes the task execution process transparent, monitorable, and controllable.

## Module Overview

The Observability module is responsible for collecting, aggregating, and reporting system runtime status, providing real-time monitoring views and remote control capabilities. Through this module, users can monitor task execution status, performance metrics, and error information in real-time, and dynamically adjust system behavior.

## Exports

| Exported Symbol | Source Module | Description |
|----------------|---------------|-------------|
| `BaseObserver` | `core_observer` | Executor lifecycle observer base class, defining event interfaces for `on_start`, `on_task_success`, `on_task_fail`, `on_task_duplicate`, `on_tasks_added`, `on_finish` |
| `CallbackObserver` | `core_observer` | Observer implementation that passes callback functions via keyword arguments, no need to define subclasses |
| `TaskReporter` | `core_report` | Task status reporter; a background thread periodically pushes runtime status to a Web server and pulls control commands |
| `NullTaskReporter` | `core_report` | Null implementation of the task reporter, serving as a placeholder when reporting is disabled; `start()` / `stop()` are no-ops |
| `TaskProgress` | `core_progress` | Task progress visualization tool based on `tqdm`, inheriting `BaseObserver`, automatically displays a progress bar in the terminal |

## File Description

### Core Components

1. **core_observer.py** (`BaseObserver`, `CallbackObserver`)
   - **Purpose**: Executor lifecycle observer base class and callback-style observer
   - **Key Features**:
     - `BaseObserver`: Defines lifecycle event interfaces (`on_start`, `on_task_success`, `on_task_fail`, `on_task_duplicate`, `on_tasks_added`, `on_finish`); subclasses override as needed
     - `CallbackObserver`: Passes callback functions via keyword arguments, no need to define subclasses

2. **core_report.py** (`TaskReporter`, `NullTaskReporter`)
   - **Purpose**: Task status reporter and its null implementation
   - **Key Features**:
     - **Status Reporting**: Periodically pushes task graph structure, topology, runtime status, and error information
     - **Task Injection**: Receives user-injected new tasks from the Web UI and dynamically inserts them into the running task graph
     - **Parameter Adjustment**: Pulls configuration from the server to dynamically adjust reporting interval and other parameters
     - **Error Synchronization**: Supports two error push modes (metadata mode and content mode)
     - **NullTaskReporter**: Placeholder when reporting is disabled, makes no network requests
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
- `NullTaskReporter` provides a safe placeholder when reporting is disabled

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
- Graceful degradation on network interruption without affecting the main execution flow
- `NullTaskReporter` serves as a zero-overhead placeholder when reporting is disabled

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

## Usage Examples

### Custom Observer + TaskReporter Used Together

The following example shows how to customize a statistics observer, and combine it with `TaskReporter` and `TaskGraph` to build an observable complete workflow:

```python
import asyncio
from celestialflow import TaskGraph, TaskExecutor, TaskStage, BaseObserver
from celestialflow.observability import TaskReporter
from celestialflow.persistence import LogInlet

# 1. Custom observer: collect task execution result statistics
class StatsObserver(BaseObserver):
    def __init__(self):
        self.success_count = 0
        self.fail_count = 0

    def on_task_success(self, count: int = 1):
        self.success_count += count

    def on_task_fail(self, count: int = 1):
        self.fail_count += count

    def on_finish(self):
        print(f"Execution finished: success {self.success_count}, fail {self.fail_count}")


# 2. Define task processing function
def process_item(item: int) -> int:
    if item % 5 == 0:
        raise ValueError(f"Skipping number {item}")
    return item * 2


async def main():
    # Create task graph
    graph = TaskGraph(schedule_mode="eager")
    stage = TaskStage("Processor", process_item, execution_mode="thread", max_workers=4)
    graph.set_stages([stage])

    # Register custom observer to the stage's executor
    stats_observer = StatsObserver()
    stage.add_observer(stats_observer)

    # Optional: enable TaskReporter to report to Web UI
    log_inlet = LogInlet()
    reporter = TaskReporter(
        host="127.0.0.1",
        port=5000,
        task_graph=graph,
        log_inlet=log_inlet,
    )
    reporter.start()

    # Start task graph
    await graph.start_graph({stage.get_tag(): list(range(20))})

    # Stop reporter
    reporter.stop()

    # View statistics
    print(f"Final stats - Success: {stats_observer.success_count}, Fail: {stats_observer.fail_count}")


asyncio.run(main())
```

This example demonstrates the collaboration of three types of observable components:
- **Custom Observer**: Inherits `BaseObserver` and overrides event methods to collect statistics
- **TaskGraph Integration**: Registers custom observers via `TaskStage`'s built-in observer list
- **TaskReporter**: Pushes runtime status to the Web server for external monitoring
