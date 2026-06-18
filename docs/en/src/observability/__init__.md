# Observability Module

> 📅 Last Updated: 2026/06/18

The Observability module provides CelestialFlow's observability features, including runtime status monitoring, progress visualization, the Observer pattern, and remote status reporting. It makes the task execution process transparent and monitorable.

## Exported Symbols

| Exported Symbol | Source Module | Description |
|---------|---------|------|
| `BaseObserver` | `core_observer` | Base class for executor lifecycle observers, defining event interfaces such as `on_start`, `on_task_success`, `on_task_fail`, `on_task_duplicate`, `on_tasks_added`, `on_finish` |
| `TaskProgress` | `core_progress` | `tqdm`-based task progress visualization tool, inheriting from `BaseObserver` |
| `TaskReporter` | `core_report` | Task status reporter, a background thread that periodically pushes runtime status to a Web server and pulls control commands |
| `NullTaskReporter` | `core_report` | Null implementation of task reporter, used as a placeholder when reporting is disabled |

> ⚠️ **Deprecated**: Previous documentation listed `CallbackObserver`. The source implementation of this class has been removed from `core_observer.py` and is no longer available.

## File Descriptions

### Core Components

1. **core_observer.py** (`BaseObserver`)
   - **Purpose**: Base class for executor lifecycle observers
   - **Key Features**:
     - `BaseObserver`: Defines lifecycle event interfaces, subclasses override as needed

2. **core_progress.py** (`TaskProgress`)
   - **Purpose**: `tqdm`-based task progress visualization, inheriting `BaseObserver`
   - **Key Features**:
     - Creates a progress bar via `on_start`
     - Updates progress via `on_task_success/fail/duplicate`
     - Dynamically increases total task count via `on_tasks_added`
     - Closes progress bar via `on_finish`

3. **core_report.py** (`TaskReporter`, `NullTaskReporter`)
   - **Purpose**: Task status reporter and its null implementation
   - **Key Features**:
     - **Status Reporting**: Periodically pushes task graph structure, topology, runtime status, and error information
     - **Task Injection**: Receives user-injected new tasks from the Web UI and dynamically inserts them into the running task graph
     - **Parameter Adjustment**: Pulls configuration from the server to dynamically adjust parameters such as reporting interval
     - **Error Syncing**: Supports two error push modes (metadata mode and content mode)
   - **Communication Protocol**: HTTP
   - **Data Format**: JSON

## Module Relationships

### Internal Relationships
- `BaseObserver` is the base class of the observer pattern; `TaskProgress` is implemented on top of it
- `TaskReporter` is an independent reporting component, designed to be pluggable
- `NullTaskReporter` provides a safe placeholder when reporting is turned off

### External Relationships
- **With Stage Module**: `TaskExecutor` holds `list[BaseObserver]`, managing observers via `add_observer()` / `remove_observer()`
- **With Graph Module**: `TaskReporter` collects task graph structure and topology information
- **With Persistence Module**: Obtains persisted log and error data, depends on `LogInlet`

## Architecture Features

### Observer Pattern
- **Multicast**: `TaskExecutor` internally maintains `list[BaseObserver]`, broadcasting events at lifecycle nodes
- **Synchronous Dispatch**: Events are synchronously dispatched to all observers via `_notify(method_name, *args, **kwargs)`
- **Empty List Equals Null**: When the observer list is empty, there is zero overhead

### Bidirectional Communication (TaskReporter)
- **Uplink**: Status data reported to the Web server
- **Downlink**: Control commands sent from the Web server to the running instance

### Fault Tolerance Design
- Graceful degradation on network interruption without affecting main flow execution
- `NullTaskReporter` as a zero-overhead placeholder when reporting is disabled

## Usage Patterns

### Observer Usage
```python
from celestialflow import TaskExecutor, TaskProgress

# Use TaskProgress to show progress bar
executor = TaskExecutor("Test", my_func)
executor.add_observer(TaskProgress())
executor.start(tasks)
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

## Usage Example

### Custom Observer + TaskReporter Combined Usage

```python
from celestialflow import TaskGraph, TaskStage, BaseObserver
from celestialflow.observability import TaskReporter
from celestialflow.persistence import LogInlet

# 1. Custom observer: collect task execution statistics
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

# Create task graph
graph = TaskGraph(schedule_mode="eager")
stage = TaskStage("Processor", process_item, execution_mode="thread", max_workers=4)
graph.set_stages([stage])

# Register custom observer to stage's executor
stats_observer = StatsObserver()
stage.add_observer(stats_observer)

# Optional: Enable TaskReporter to push to Web UI
log_inlet = stage.log_inlet
reporter = TaskReporter(
    host="127.0.0.1",
    port=5000,
    task_graph=graph,
    log_inlet=log_inlet,
)
reporter.start()

# Start task graph
graph.start_graph({stage.get_name(): list(range(20))})

# Stop reporter
reporter.stop()

# View statistics
print(f"Final stats - success: {stats_observer.success_count}, fail: {stats_observer.fail_count}")
```

This example demonstrates the collaboration of three types of observable components:
- **Custom Observer**: Inherits `BaseObserver` and overrides event methods to collect statistics
- **TaskGraph Integration**: Registers custom observers via `TaskStage`'s built-in observer list
- **TaskReporter**: Pushes runtime status to the Web server for external monitoring
