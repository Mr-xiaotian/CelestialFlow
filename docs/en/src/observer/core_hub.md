# src/celestialflow/observer/core_hub.py

> 📅 Last Updated: 2026/10/09

`core_hub.py` defines the observer **dispatch hub** `ObserverHub`. It is itself an `Observer`, forwarding each received event to registered observers in registration order. It is the broadcast hub between a node and its various downstream observers.

## ObserverHub

```python
class ObserverHub(Observer):
    def __init__(self) -> None: ...

    def add_observer(self, observer: Observer) -> None: ...

    # Inherits Observer's 12 event callbacks + handle_exception
    def on_node_start(self, event: NodeStartEvent) -> None: ...
    def on_node_end(self, event: NodeEndEvent) -> None: ...
    # ... forwards each event to all observers in turn ...
    def on_graph_start(self, event: GraphStartEvent) -> None: ...
    def on_graph_end(self, event: GraphEndEvent) -> None: ...
```

The forwarding semantics of each event callback (`on_*`) are the same: iterate over the current observer snapshot, call the corresponding callback on each observer; if a callback of some observer raises an exception, hand it to that observer's own `handle_exception`; if `handle_exception` itself raises again, the hub's own `handle_exception` serves as the final fallback. Neither case interrupts the dispatch to the other observers, nor escapes into the framework execution path.

## Registration and Copy-on-Write

The observer list uses **copy-on-write**:

- A writer replaces `_observers` as a whole with a new immutable tuple under the protection of `_write_lock` via `add_observer()`;
- The read path `_snapshot()` directly returns the current reference, without locking or copying;
- Because the tuple is immutable and CPython does not tear attribute reads and replacements, the read always obtains a complete version of the snapshot, and there is no need to worry about concurrent modification during iteration.

```python
def add_observer(self, observer: Observer) -> None:
    self._reject_cycle(observer)
    with self._write_lock:
        self._observers = (*self._observers, observer)
```

### Cycle Reference Rejection

`add_observer` first calls `_reject_cycle` to reject a registration that would create a hub cycle reference (to avoid infinite recursion during dispatch):

- If `observer is self`, raise `ConfigurationError`;
- If `observer` is an `ObserverHub`, DFS through its observer tree to check whether it (directly or indirectly) already holds the current hub; if so, raise `ConfigurationError`.

## Usage Example

```python
from celestialflow.observer import (
    Observer,
    ObserverHub,
    MetricsObserver,
    TaskSuccessEvent,
)


class MyObserver(Observer):
    def on_task_success(self, event: TaskSuccessEvent) -> None:
        print(f"{event.node} succeeded: {event.result_repr}")


hub = ObserverHub()
hub.add_observer(MyObserver())
hub.add_observer(MetricsObserver())
```

## Assembly Scenario

A node's observer hub is held by `BaseTaskNode`. During the assembly (`assembly/core_run.py`) phase:

- `MetricsObserver` is registered as the write model;
- `LifecycleInlet` / `LogInlet` (from the `persist` module) are registered, consuming events and writing to disk;
- When reporting is enabled, `PushSnapshotHandler` / `PushInlet` are also registered.

All of these are attached to the same hub via `observers.add_observer(...)`; the node only broadcasts to `hub.on_*()` and is unaware of the specific observer details.

## Notes

1. **Thread safety**: `add_observer` can be called at runtime, and the read side can safely iterate the snapshot without locking.
2. **Exceptions do not escape**: an exception of a single observer is isolated inside the hub and will not interrupt the other observers in the same batch, nor be returned to the node execution path.
3. **It is itself an `Observer`**: `ObserverHub` inherits `Observer` and can be registered into another hub (which is precisely why cycle detection is needed).