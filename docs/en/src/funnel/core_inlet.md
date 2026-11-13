# src/celestialflow/funnel/core_inlet.py

> 📅 Last Updated: 2026/11/13

`BaseInlet` is the base class for all inlet classes, responsible for sending records to the corresponding `BaseSpout` through a queue.

## Class Definition

```python
class BaseInlet:
    _queue: Queue[Any]
    _counter: PendingCounter

    def bind_spout(self, spout: BaseSpout) -> Self:
        """
        Bind the current inlet to the given spout.

        :param spout: Target listener
        :return: The current inlet instance, now bound
        """
        self._queue = spout.get_queue()
        self._counter = spout.get_counter()
        return self

    def send(self, record: Any) -> None:
        """
        Put a record into the queue of the bound spout.

        :param record: Record to send
        :return: ``None``
        """
        if not hasattr(self, "_queue") or not hasattr(self, "_counter"):
            raise InitializationError("inlet is not bound to spout")

        # Increment the pending count first, then enqueue; roll back the count immediately if enqueueing fails.
        self._counter.increment()
        try:
            self._queue.put(record)
        except Exception:
            self._counter.decrement()
            raise
```

## Core Methods

### bind_spout

```python
def bind_spout(self, spout: BaseSpout) -> Self:
```

- Binds the current inlet to the specified `BaseSpout` instance.
- Internally reuses the spout's input queue (`_queue`) and pending counter (`_counter`).
- Returns itself to support chaining: `BaseInlet().bind_spout(spout)`.
- Calling `send()` before binding raises `InitializationError`.

### send (public)

```python
def send(self, record: Any) -> None:
```

- Puts `record` into the queue shared with the spout; it is the Inlet's only write exit.
- Calls `increment()` before enqueueing; if enqueueing fails, immediately calls `decrement()` to roll back and re-raises the exception as-is.
- When no spout is bound (missing `_queue` / `_counter`), raises `InitializationError("inlet is not bound to spout")`.
- Subclasses can add semantic methods (e.g., `emit()`) that delegate internally to `self.send(...)`; **do not** override `send()` and then call back into `self.send(...)`, as that causes infinite recursion.

## Inheritance Relationships

```mermaid
classDiagram
    class BaseInlet {
        +bind_spout(spout: BaseSpout) Self
        +send(record: Any) None
    }
    class LogInlet {
        +send(record: LogRecord) None
    }
    class LifecycleInlet {
        +send(record: LifecycleRecord) None
    }
    BaseInlet <|-- LogInlet
    BaseInlet <|-- LifecycleInlet
```

### Inheritance Description

| Subclass | Source File | Responsibility |
|----------|-------------|----------------|
| `LogInlet` | `persist/core_log.py` | Log record inlet; `send(LogRecord)` forwards to `LogSpout`; the actual event translation is performed by `LogObserver` |
| `LifecycleInlet` | `persist/core_lifecycle.py` | Lifecycle record inlet; `send(LifecycleRecord)` forwards to `LifecycleSpout` for writing to SQLite; the actual event translation is performed by `LifecycleObserver` |

## Usage Example

```python
from celestialflow.funnel import BaseSpout, BaseInlet


class MySpout(BaseSpout):
    def __init__(self):
        super().__init__()
        self.received = []

    def _handle_record(self, record):
        self.received.append(record)


class MyInlet(BaseInlet):
    # Add a semantic method that delegates internally to the public send()
    def emit(self, data):
        self.send(data)


# Usage
spout = MySpout()
inlet = MyInlet().bind_spout(spout)

spout.start()
inlet.emit("hello")
inlet.emit({"key": "value"})
spout.stop()

print(spout.received)
```

## Notes

1. **One-Way Communication**: Inlet only writes to the queue, Spout is responsible for consumption; both are decoupled via the queue.
2. **Binding Style**: The queue and counter are created by `BaseSpout` and shared with the Inlet via `bind_spout()`; the Inlet does not manage the queue lifecycle directly.
3. **Thread Safety**: Uses `queue.Queue` and `PendingCounter` (internally locked) for safe inter-thread communication.
4. **Unbound Exception**: If `send()` is called without first calling `bind_spout()`, `InitializationError` is raised.
5. **Usage Pattern**: Typically one `BaseSpout` corresponds to one `BaseInlet`, forming a producer-consumer pair.
6. **Do not override `send()` to delegate to itself**: `send()` is the Inlet's final write exit; subclasses should add semantic methods and call `self.send(...)`.
