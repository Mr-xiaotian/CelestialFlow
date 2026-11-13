# src/celestialflow/observer/__init__.py

> 📅 Last Updated: 2026/11/13

The `observer` module is CelestialFlow's **observability module**, responsible for the observer protocol, unified event types, the event dispatch hub, and the built-in metrics and progress output observers.

## Exported Symbols

The module-level `__all__` exports are as follows:

```python
__all__ = [
    "Event",
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
]
```

The exported symbols can be categorized as follows:

| Exported Symbol | Source Module | Description |
|---------|---------|------|
| `Event` | `core_event` | Base class of all observed events; serves only as a type marker and carries no state |
| `Observer` | `core_observer` | Observer base class, declaring only the unified `on_event(event)` and `handle_exception(exception)` |
| `ObserverHub` | `core_hub` | Observer dispatch hub, itself also an `Observer`, forwarding events in registration order and providing `find()` |
| `MetricsObserver` | `core_metrics` | Graph-level metrics observer (write model + read-only view), maintaining node counts and status based on events |
| `PrintObserver` | `core_print` | `print`-based console observer, convenient for local debugging and example demonstrations |
| `NodeStartEvent` / `NodeEndEvent` | `core_event` | Node start / end events |
| `TaskInputEvent` / `TaskSuccessEvent` / `TaskFailEvent` / `TaskSkipEvent` / `TaskRetryEvent` | `core_event` | Task input / success / fail / skip / retry events |
| `TerminationInputEvent` / `TerminationMergeEvent` | `core_event` | Termination-signal input / merge events |
| `GraphStartEvent` / `GraphEndEvent` | `core_event` | Task graph start / end events |

## File Descriptions

1. **core_observer.py** (`Observer`)
   - **Purpose**: Executor lifecycle observer base class, declaring only `on_event` and `handle_exception`.
   - **Features**: All events enter through a single entry point, and subclasses dispatch by type using `match`; the base class is not an `ABC`.

2. **core_event.py** (`Event` + 11 event `dataclass`es)
   - **Purpose**: Defines the unified event base class and all event types of the task / node / task graph lifecycle.
   - **Features**: Concrete events are read-only data classes with `frozen=True, slots=True`; `Event` uses `__slots__ = ()` and carries no state.

3. **core_hub.py** (`ObserverHub`)
   - **Purpose**: Observer dispatch hub, forwarding each received event to registered observers in registration order; `find()` searches observers recursively by type.
   - **Features**: It is itself also an `Observer`; the observer list uses copy-on-write.

4. **core_metrics.py** (`MetricsObserver`)
   - **Purpose**: Graph-level metrics observer, maintaining each node's counts, status, and run start time based on events.
   - **Features**: It both writes as an observer and exposes a read-only `NodeMetrics` snapshot via the `MetricsView` protocol.

5. **core_print.py** (`PrintObserver`)
   - **Purpose**: An out-of-the-box console observer.
   - **Features**: Uses thread-safe `ValueWrapper`s to count `total` / `succeeded` / `failed` / `skipped`, and prints with the `[name] ...` prefix.

## Module Relationships

### Internal Relationships
- `Observer` is the observer-pattern base class; `ObserverHub`, `MetricsObserver`, and `PrintObserver` are all `Observer` subclasses.
- The event types defined in `core_event.py` are jointly referenced by `core_observer` / `core_hub` / `core_metrics` / `core_print`.

### External Relationships
- **With Node Module**: `BaseTaskNode` holds `ObserverHub observers`, constructs an event when it occurs, and calls `hub.on_event(...)` to broadcast it; when reading results it uses `observers.find(LifecycleObserver)` to locate the lifecycle observer and obtain its `db_path`.
- **With Persist Module**: `LifecycleObserver` / `LogObserver` are `Observer` subclasses, registered into the hub by `run_node_resources` / `run_graph_resources`, consuming events and writing them to disk.
- **With Assembly Module**: `assembly/core_run.py` assembles the `ObserverHub` and registers `MetricsObserver`, `LifecycleObserver`, `LogObserver`, etc.

## Architecture Features

### Event-Driven Dispatch
- **Single entry**: All observers only implement `on_event(event)`; event objects are read-only `dataclass`es defined in `core_event.py`, carrying rich fields.
- **Explicit lifecycle timestamps**: The start/end times of nodes and task graphs are carried by event fields (`start_time` / `end_time`), so observers do not need to sample `time.time()` themselves.
- **Multicast dispatch**: `ObserverHub` broadcasts the same event to all registered observers at once.
- **Exception isolation**: An exception raised by a single observer callback is caught by the hub and handed to that observer's own `handle_exception`, **without interrupting** the dispatch to other observers, nor escaping into the framework execution path.

## Usage Example

```python
from celestialflow.observer import (
    Event,
    MetricsObserver,
    Observer,
    ObserverHub,
    TaskSuccessEvent,
)


class MyObserver(Observer):
    def on_event(self, event: Event) -> None:
        match event:
            case TaskSuccessEvent():
                print(f"{event.node} succeeded: {event.result_repr}")
            case _:
                pass


hub = ObserverHub()
hub.add_observer(MyObserver())
hub.add_observer(MetricsObserver())
```

Find a registered observer:

```python
from celestialflow.observer import ObserverHub, PrintObserver

hub = ObserverHub()
hub.add_observer(PrintObserver("StageA"))

printer = hub.find(PrintObserver)
print(printer.name if printer is not None else None)  # StageA
```

## Notes

1. **Import path**: Import the above symbols from `celestialflow.observer`, not from the legacy `celestialflow.observability`.
2. **Metrics and progress are separate**: use `MetricsObserver` for structured node metrics; use `PrintObserver` when only console progress output is needed.
3. **Observers only implement `on_event`**: The legacy per-callback methods such as `on_node_start` / `on_task_success` have all been removed.
