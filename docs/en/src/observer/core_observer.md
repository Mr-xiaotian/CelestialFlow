# src/celestialflow/observer/core_observer.py

> 📅 Last Updated: 2026/10/09

`core_observer.py` defines the **base class** `Observer` for executor lifecycle observers. It declares the event callback interfaces of the task / node / task graph full lifecycle; all callbacks provide default no-op implementations, and an implementer only needs to inherit this base class and override the methods of interest.

## Observer

```python
class Observer:
    def on_node_start(self, event: NodeStartEvent) -> None: ...
    def on_task_input(self, event: TaskInputEvent) -> None: ...
    def on_task_success(self, event: TaskSuccessEvent) -> None: ...
    def on_task_fail(self, event: TaskFailEvent) -> None: ...
    def on_task_skip(self, event: TaskSkipEvent) -> None: ...
    def on_task_retry(self, event: TaskRetryEvent) -> None: ...
    def on_termination_input(self, event: TerminationInputEvent) -> None: ...
    def on_termination_merge(self, event: TerminationMergeEvent) -> None: ...
    def on_worker_crash(self, event: WorkerCrashEvent) -> None: ...
    def on_node_end(self, event: NodeEndEvent) -> None: ...
    def on_graph_start(self, event: GraphStartEvent) -> None: ...
    def on_graph_end(self, event: GraphEndEvent) -> None: ...

    def handle_exception(self, exception: Exception) -> None: ...
```

All event callbacks default to no-op implementations (not an ABC); subclasses override as needed. Callback parameters are the event `dataclass`es defined in `core_event.py`.

### Event Descriptions

| Callback | Event | Trigger Timing |
|------|------|----------|
| `on_node_start` | `NodeStartEvent` | Node starts (`BaseTaskNode._prepare_start`) |
| `on_node_end` | `NodeEndEvent` | Node ends (`BaseTaskNode._finish_start`) |
| `on_task_input` | `TaskInputEvent` | A task enters the node's input queue |
| `on_task_success` | `TaskSuccessEvent` | A task is processed successfully |
| `on_task_fail` | `TaskFailEvent` | A task finally fails |
| `on_task_skip` | `TaskSkipEvent` | A task is skipped |
| `on_task_retry` | `TaskRetryEvent` | A task fails but triggers a retry |
| `on_termination_input` | `TerminationInputEvent` | A termination signal enters the input queue |
| `on_termination_merge` | `TerminationMergeEvent` | Multiple termination signals are merged |
| `on_worker_crash` | `WorkerCrashEvent` | A worker thread/coroutine catches an unhandled exception in the fallback layer |
| `on_graph_start` | `GraphStartEvent` | Task graph starts |
| `on_graph_end` | `GraphEndEvent` | Task graph ends |

### handle_exception

```python
def handle_exception(self, exception: Exception) -> None:
    traceback.print_exception(exception)
```

When a callback of an observer itself raises an exception, `ObserverHub` catches it and calls that observer's **own** `handle_exception` to process it. The default implementation prints the exception traceback to standard error; subclasses can override it to implement custom strategies (collect, report, or ignore). If `handle_exception` itself raises again, the hub's own `handle_exception` serves as the final fallback.

## Event Dispatch Mechanism

`Observer` events are **not invoked directly on each observer node by node**, but are broadcast through `ObserverHub`:

- The node holds an `ObserverHub` (`BaseTaskNode.observers`), registering observers via `add_observer()`;
- When an event occurs, the node calls `hub.on_*()`, and the hub forwards it to each observer in registration order;
- An exception raised by a single observer callback is caught by the hub and handed to that observer's `handle_exception`, **without interrupting the dispatch to other observers, nor escaping into the framework path**.

Built-in observers (also `Observer` subclasses):

| Class | File | Description |
|---|---------|------|
| `PrintObserver` | `core_observer_print.py` | `print`-based console observer |
| `MetricsObserver` | `core_metrics.py` | Metrics observer that maintains node counts and status based on events |
| `ObserverHub` | `core_hub.py` | Observer dispatch hub, itself also an `Observer` |
| `LifecycleInlet` / `LogInlet` | `persist` | Assembled by `run_node_resources` / `run_graph_resources`, consuming events and writing to disk |

## Usage Example

```python
from celestialflow.node import TaskExecutor
from celestialflow.observer import Observer, TaskFailEvent, TaskSuccessEvent


class MyObserver(Observer):
    def on_task_success(self, event: TaskSuccessEvent) -> None:
        print(f"{event.node} succeeded: {event.result_repr}")

    def on_task_fail(self, event: TaskFailEvent) -> None:
        print(f"{event.node} failed: {event.exception}")


executor = TaskExecutor("Test", lambda x: x * 2)
executor.add_observer(MyObserver())
executor.run([1, 2, 3])
```

## Notes

1. **Callback parameters are event objects**: Unlike the legacy `BaseObserver` (whose callbacks received basic parameters such as `count`), all callbacks receive the corresponding event `dataclass`, with richer available fields.
2. **`handle_exception` is not automatically wrapped**: a callback cannot guarantee it will not raise — the exception is caught by the hub and handed to this observer's `handle_exception`; it is not re-wrapped by the hub itself, but is caught by the hub's `handle_exception` as a fallback.
3. **Inherit rather than instantiate**: the `Observer` base class exposes all callbacks; in practice it is usually inherited and only the needed methods are overridden.