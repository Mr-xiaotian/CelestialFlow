# Observability Module

> 📅 Last Updated: 2026/08/26

The Observability module provides CelestialFlow's observability features, including runtime status monitoring, the Observer pattern, and remote status reporting. It makes the task execution process transparent and monitorable.

## Exported Symbols

| Exported Symbol | Source Module | Description |
|-----------------|---------------|-------------|
| `BaseObserver` | `core_observer` | Base class for executor lifecycle observers, defining event interfaces such as `on_start`, `on_task_success`, `on_task_fail`, `on_task_duplicate`, `on_tasks_added`, `on_finish` |
| `NullTaskReporter` | `core_report` | Null implementation of task reporter, used as a placeholder when reporting is disabled |
| `ReporterProtocol` | `core_report` | Minimum interface protocol required by Reporter dependants |
| `TaskReporter` | `core_report` | Task status reporter; a background thread periodically pushes runtime status to the `celestialflow-web` service and pulls control commands |

## File Descriptions

### Core Components

1. **core_observer.py** (`BaseObserver`)
   - **Purpose**: Base class for executor lifecycle observers
   - **Key Features**:
     - `BaseObserver`: Defines lifecycle event interfaces, subclasses override as needed

2. **core_report.py** (`TaskReporter`, `NullTaskReporter`)
   - **Purpose**: Task status reporter and its null implementation
   - **Key Features**:
     - **Status Reporting**: Periodically pushes task graph structure, topology, runtime status, and error information
     - **Task Injection**: Pulls tasks to be injected from the `celestialflow-web` service and dynamically inserts them into the running task graph
     - **Parameter Adjustment**: Pulls configuration from the `celestialflow-web` service to dynamically adjust parameters such as reporting interval
     - **Error Syncing**: Incrementally pushes error records based on `event_id`
   - **Communication Protocol**: HTTP
   - **Data Format**: JSON

## Module Relationships

### Internal Relationships
- `BaseObserver` is the base class of the observer pattern
- `TaskReporter` is an independent reporting component, designed to be pluggable
- `NullTaskReporter` provides a safe placeholder when reporting is turned off

### External Relationships
- **With Stage Module**: `TaskExecutor`'s internal `TaskMetrics` holds `list[BaseObserver]`, managed via `add_observer()` / `remove_observer()`
- **With Graph Module**: `TaskReporter` collects task graph structure and topology information
- **With Persistence Module**: Obtains persisted log and error data, depends on `LogInlet`

## Architecture Features

### Observer Pattern
- **Multicast**: `TaskExecutor`'s internal `TaskMetrics` maintains `list[BaseObserver]`, broadcasting events on count changes and node start/stop
- **Synchronous Dispatch**: All registered observers' corresponding callbacks are synchronously invoked in methods such as `add_success_count` / `add_fail_count` / `add_task_count` / `on_start` / `on_finish`
- **Exception Isolation**: Subclass-overridden callbacks are automatically wrapped by `__init_subclass__`; exceptions are uniformly caught by `observer_error()` and do not escape into the framework

### Bidirectional Communication (TaskReporter)
- **Uplink**: Status data reported to the celestialflow-web service
- **Downlink**: Control commands sent from the celestialflow-web service to the running instance

### Fault Tolerance Design
- Graceful degradation on network interruption without affecting main flow execution
- `NullTaskReporter` as a zero-overhead placeholder when reporting is disabled

## Usage Patterns

### TaskReporter Usage
```python
from celestialflow.observability import TaskReporter

reporter = TaskReporter(
    host="127.0.0.1",
    port=5000,
    task_graph=my_task_graph,
)
reporter.start()
```

## Usage Examples

### Custom Observer + TaskReporter Combined Usage

```python
from celestialflow import TaskGraph, TaskStage, BaseObserver
from celestialflow.observability import TaskReporter


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
graph = TaskGraph("ObsDemo")
stage = TaskStage("Processor", process_item, execution_mode="thread", max_workers=4)
graph.set_stages([stage])

# Register custom observer to stage's executor
stats_observer = StatsObserver()
stage.add_observer(stats_observer)

# Optional: Enable TaskReporter to push to the celestialflow-web service
reporter = TaskReporter(
    host="127.0.0.1",
    port=5000,
    task_graph=graph,
)
reporter.start()

# Start task graph
graph.run({stage.get_name(): list(range(20))})

# Stop reporter
reporter.stop()

# View statistics
print(
    f"Final stats - success: {stats_observer.success_count}, fail: {stats_observer.fail_count}"
)
```

This example demonstrates the collaboration of observability components:
- **Custom Observer**: Inherits `BaseObserver` and overrides event methods to collect statistics
- **TaskGraph Integration**: Registers custom observers via `TaskStage`'s built-in observer list
- **TaskReporter**: Pushes runtime status to the `celestialflow-web` service for monitoring or control
