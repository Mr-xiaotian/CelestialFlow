# src/celestialflow/observer/core_observer.py

> 📅 Last Updated: 2026/11/13

`core_observer.py` defines the **base class** `Observer` for executor lifecycle observers. Unlike the legacy "one callback per event" design, all events now enter through the single `on_event` method; an implementer inherits this base class, overrides only that method, and dispatches by concrete event type with `match`, while events it does not care about are naturally ignored.

## Observer

```python
class Observer:
    def on_event(self, event: Event) -> None: ...

    def handle_exception(self, exception: Exception) -> None: ...
```

- `on_event`: the **only** event entry point; the default implementation ignores all events (the method body is `...`).
- `handle_exception`: the handler called when an observer's own callback raises an exception; by default it prints the traceback to standard error.

`Observer` is not an `ABC`; subclasses override as needed. Event objects are defined in `core_event.py` and all inherit from the base class `Event`.

### Event Dispatching

Subclasses usually dispatch by type in `on_event` using structural pattern matching:

```python
from celestialflow.observer import Event, Observer, TaskFailEvent, TaskSuccessEvent


class MyObserver(Observer):
    def on_event(self, event: Event) -> None:
        match event:
            case TaskSuccessEvent():
                print(f"{event.node} succeeded: {event.result_repr}")
            case TaskFailEvent():
                print(f"{event.node} failed: {event.exception}")
            case _:
                pass
```

| Event | Trigger Timing |
|------|----------|
| `NodeStartEvent` | Node starts (`BaseTaskNode._prepare_start`) |
| `NodeEndEvent` | Node ends (`BaseTaskNode._finish_start`) |
| `TaskInputEvent` | A task enters the node's input queue |
| `TaskSuccessEvent` | A task is processed successfully |
| `TaskFailEvent` | A task finally fails |
| `TaskSkipEvent` | A task is skipped |
| `TaskRetryEvent` | A task fails but triggers a retry |
| `TerminationInputEvent` | A termination signal enters the input queue |
| `TerminationMergeEvent` | Multiple termination signals are merged |
| `GraphStartEvent` | Task graph starts |
| `GraphEndEvent` | Task graph ends |

### handle_exception

```python
def handle_exception(self, exception: Exception) -> None:
    traceback.print_exception(exception)
```

When an observer's `on_event` itself raises an exception, `ObserverHub` catches it and calls **that observer's own** `handle_exception` to process it. The default implementation prints the exception traceback to standard error; subclasses can override it to implement custom strategies (collect, report, or ignore). If `handle_exception` itself raises again, the hub's `handle_exception` serves as the final fallback.

## Event Dispatch Mechanism

`Observer` events are **not invoked directly on each observer node by node**, but are broadcast through `ObserverHub`:

- The node holds an `ObserverHub` (`BaseTaskNode.observers`), registering observers via `add_observer()`;
- When an event occurs, the node constructs the corresponding event and calls `hub.on_event(event)`, and the hub forwards it to each observer in registration order;
- An exception raised by a single observer callback is caught by the hub and handed to that observer's `handle_exception`, **without interrupting the dispatch to other observers, nor escaping into the framework path**.

Built-in observers (also `Observer` subclasses):

| Class | File | Description |
|---|---------|------|
| `PrintObserver` | `core_print.py` | `print`-based console observer |
| `MetricsObserver` | `core_metrics.py` | Metrics observer that maintains node counts and status based on events |
| `ObserverHub` | `core_hub.py` | Observer dispatch hub, itself also an `Observer` |
| `LifecycleObserver` / `LogObserver` | `persist` | Lifecycle and log observers, assembled by `run_node_resources` / `run_graph_resources` |

## Usage Example

```python
from celestialflow.node import TaskExecutor
from celestialflow.observer import Event, Observer, TaskFailEvent, TaskSuccessEvent


class MyObserver(Observer):
    def on_event(self, event: Event) -> None:
        match event:
            case TaskSuccessEvent():
                print(f"{event.node} succeeded: {event.result_repr}")
            case TaskFailEvent():
                print(f"{event.node} failed: {event.exception}")


executor = TaskExecutor("Test", lambda x: x * 2)
executor.add_observer(MyObserver())
executor.run([1, 2, 3])
```

## Notes

1. **Single callback**: all events enter through `on_event`; the legacy per-event callbacks such as `on_node_start` / `on_task_success` have all been removed.
2. **`handle_exception` is not automatically wrapped**: a callback cannot guarantee it will not raise — the exception is caught by the hub and handed to this observer's `handle_exception`; it is not re-wrapped by the hub itself, but is caught by the hub's `handle_exception` as a fallback.
3. **Inherit rather than instantiate**: the `Observer` base class exposes `on_event`; in practice it is usually inherited and only the branches of interest are overridden.
