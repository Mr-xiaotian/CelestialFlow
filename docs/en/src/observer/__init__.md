# src/celestialflow/observer/__init__.py

> 📅 Last Updated: 2026/10/09

The `observer` module is CelestialFlow's **observability module**, responsible for the observer protocol, task / node / task graph event types, the event dispatch hub, and the built-in metrics and progress output observers.

## Exported Symbols

The module-level `__all__` exports are as follows:

```python
__all__ = [
    "GraphEndEvent",
    "GraphStartEvent",
    "MetricsObserver",
    "NodeEndEvent",
    "NodeStartEvent",
    "Observer",
    "ObserverHub",
    "PrintObserver",
    "TaskFailEvent",
    "TaskInputEvent",
    "TaskRetryEvent",
    "TaskSkipEvent",
    "TaskSuccessEvent",
    "TerminationInputEvent",
    "TerminationMergeEvent",
    "WorkerCrashEvent",
]
```

The exported symbols can be categorized as follows:

| Exported Symbol | Source Module | Description |
|---------|---------|------|
| `Observer` | `core_observer` | Observer base class, declaring the task / node / graph full-lifecycle callback interface; all callbacks default to no-op implementations |
| `ObserverHub` | `core_hub` | Observer dispatch hub, itself also an `Observer`, forwarding events in registration order |
| `MetricsObserver` | `core_metrics` | Graph-level metrics observer (write model + read-only view), maintaining node counts and status based on events |
| `PrintObserver` | `core_observer_print` | `print`-based console observer, convenient for local debugging and example demonstrations |
| `NodeStartEvent` / `NodeEndEvent` | `core_event` | Node start / end events |
| `TaskInputEvent` / `TaskSuccessEvent` / `TaskFailEvent` / `TaskSkipEvent` / `TaskRetryEvent` | `core_event` | Task input / success / fail / skip / retry events |
| `TerminationInputEvent` / `TerminationMergeEvent` | `core_event` | Termination-signal input / merge events |
| `WorkerCrashEvent` | `core_event` | Worker crash event |
| `GraphStartEvent` / `GraphEndEvent` | `core_event` | Task graph start / end events |

## File Descriptions

1. **core_observer.py** (`Observer`)
   - **Purpose**: Executor lifecycle observer base class, declaring 12 event callbacks and `handle_exception`.
   - **Features**: All callbacks provide default no-op implementations; it is not an ABC, and subclasses override as needed.

2. **core_event.py** (12 event `dataclass`es)
   - **Purpose**: Defines all event types of the task / node / task graph lifecycle.
   - **Features**: All are read-only data classes with `frozen=True, slots=True`, used as observer callback arguments.

3. **core_hub.py** (`ObserverHub`)
   - **Purpose**: Observer dispatch hub, forwarding each received event to registered observers in registration order.
   - **Features**: It is itself also an `Observer`; the observer list uses copy-on-write.

4. **core_metrics.py** (`MetricsObserver`)
   - **Purpose**: Graph-level metrics observer, maintaining each node's counts, status, and run start time based on events.
   - **Features**: It both writes as an observer and exposes a read-only `NodeMetrics` snapshot via the `MetricsView` protocol.

5. **core_observer_print.py** (`PrintObserver`)
   - **Purpose**: An out-of-the-box console observer.
   - **Features**: Uses thread-safe `ValueWrapper`s to count `total` / `succeeded` / `failed` / `skipped`, and prints with the `[name] ...` prefix.

## Module Relationships

### Internal Relationships
- `Observer` is the observer-pattern base class; `ObserverHub`, `MetricsObserver`, and `PrintObserver` are all `Observer` subclasses.
- The event types defined in `core_event.py` are jointly referenced by `core_observer` / `core_hub` / `core_metrics` / `core_observer_print`.

### External Relationships
- **With Node Module**: `BaseTaskNode` holds `ObserverHub observers` and calls `hub.on_*()` to broadcast when an event occurs.
- **With Persist Module**: `run_node_resources` / `run_graph_resources` register `LifecycleInlet` / `LogInlet` as observers into the hub, consuming events and writing them to disk.
- **With Assembly Module**: `assembly/core_run.py` assembles the `ObserverHub` and registers `MetricsObserver`, `LifecycleInlet`, `LogInlet`, etc.

## Architecture Features

### Event-Driven Dispatch
- **Event objects as callback parameters**: All callbacks receive read-only `dataclass`es defined in `core_event.py`, carrying rich fields.
- **Multicast dispatch**: `ObserverHub` broadcasts the same event to all registered observers at once.
- **Exception isolation**: An exception raised by a single observer callback is caught by the hub and handed to that observer's own `handle_exception`, **without interrupting** the dispatch to other observers, nor escaping into the framework execution path.

## Usage Example

```python
from celestialflow.observer import (
    Observer,
    ObserverHub,
    TaskSuccessEvent,
    MetricsObserver,
)


class MyObserver(Observer):
    def on_task_success(self, event: TaskSuccessEvent) -> None:
        print(f"{event.node} succeeded: {event.result_repr}")


hub = ObserverHub()
hub.add_observer(MyObserver())
hub.add_observer(MetricsObserver())
```

## Notes

1. **Import path**: Import the above symbols from `celestialflow.observer`, not from the legacy `celestialflow.observability`.
2. **Metrics and progress are separate**: use `MetricsObserver` for structured node metrics; use `PrintObserver` when only console progress output is needed.