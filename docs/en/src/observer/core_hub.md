# src/celestialflow/observer/core_hub.py

> 📅 Last Updated: 2026/11/13

`core_hub.py` defines the observer **dispatch hub** `ObserverHub`. It is itself an `Observer`, forwarding each received event to registered observers in registration order, and provides `find()` for locating observers by type. It is the broadcast hub between a node and its various downstream observers.

## ObserverHub

```python
class ObserverHub(Observer):
    def __init__(self) -> None: ...

    def add_observer(self, observer: Observer) -> None: ...

    def find[O: Observer](self, observer_type: type[O]) -> O | None: ...

    def on_event(self, event: Event) -> None: ...
```

## Event Dispatch

`on_event` iterates over the current observer snapshot and calls `observer.on_event(event)` on each observer. If some observer's callback raises an exception, it is handed to that observer's own `handle_exception`; if `handle_exception` itself raises again, the hub's own `handle_exception` serves as the final fallback. Neither case interrupts the dispatch to the other observers, nor escapes into the framework execution path.

```python
def on_event(self, event: Event) -> None:
    for observer in self._snapshot():
        try:
            observer.on_event(event)
        except Exception as exception:
            try:
                observer.handle_exception(exception)
            except Exception as fallback:
                self.handle_exception(fallback)
```

> Since there is only a single `on_event` entry point, adding a new event type requires no change to the hub: all observers receive every event and then handle it in their own `match` branches.

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

## Finding Observers by Type

```python
def find[O: Observer](self, observer_type: type[O]) -> O | None:
```

Lookup rules:

1. First scan the observers registered **directly at this level**, returning the first `isinstance` match (so subclass instances also match);
2. If not found at this level, recursively enter nested `ObserverHub`s in registration order;
3. Return `None` if nothing matches.

Therefore, **registrations closer to the caller take priority**.

A typical use is a node locating the lifecycle observer when reading results: when running independently, `LifecycleObserver` is registered directly on the node hub; under graph scheduling it lives in the graph-level hub, and `find` recursively hits both:

```python
from celestialflow.persist import LifecycleObserver

lifecycle = node.observers.find(LifecycleObserver)
db_path = lifecycle.db_path if lifecycle is not None else None
```

## Usage Example

### Registration and Broadcasting

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

### Nested Hubs and find

```python
from celestialflow.observer import ObserverHub
from celestialflow.persist import LifecycleObserver

graph_hub = ObserverHub()
graph_hub.add_observer(LifecycleObserver())

node_hub = ObserverHub()
node_hub.add_observer(graph_hub)  # The node shares the graph-level observers

found = node_hub.find(LifecycleObserver)
print(found is not None)  # True: find recurses into graph_hub
```

## Assembly Scenario

A node's observer hub is held by `BaseTaskNode` and usually nests the graph-level hub. During the assembly (`assembly/core_run.py`) phase:

- `MetricsObserver` is registered as the write model;
- `LifecycleObserver` / `LogObserver` (from the `persist` module) are registered, and they in turn drive `LifecycleInlet` / `LogInlet` and the spouts to complete persistence;
- When reporting is enabled, `PushSnapshotHandler` / `PushInlet` are also registered.

All of these are attached to the hub via `observers.add_observer(...)`; the node only broadcasts to `hub.on_event(...)` and is unaware of the specific observer details.

## Notes

1. **Thread safety**: `add_observer` can be called at runtime, and the read side can safely iterate the snapshot without locking.
2. **Exceptions do not escape**: an exception of a single observer is isolated inside the hub and will not interrupt the other observers in the same batch, nor be returned to the node execution path.
3. **It is itself an `Observer`**: `ObserverHub` inherits `Observer` and can be registered into another hub (which is precisely why cycle detection is needed).
4. **Priority of `find`**: this level first, then nested levels; among multiple instances of the same type, only the first match is returned.
