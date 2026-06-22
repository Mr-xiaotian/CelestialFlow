# PendingCounter

> 📅 Last Updated: 2026/06/22

`funnel/util_count.py` provides a thread-safe pending counter, `PendingCounter`, used to count the number of records corresponding to a `BaseSpout` that have not yet finished processing.

## Core Object

### PendingCounter

```python
class PendingCounter:
    def __init__(self) -> None: ...
    def increment(self) -> int: ...
    def decrement(self) -> int: ...
    def get_count(self) -> int: ...
```

`PendingCounter` internally uses `threading.Lock` to protect the count variable, so it can be safely used in multi-threaded environments.

## Method Reference

| Method | Return Value | Description |
|--------|--------------|-------------|
| `increment()` | `int` | Increase the pending count by one and return the new value |
| `decrement()` | `int` | Decrease the pending count by one and return the new value |
| `get_count()` | `int` | Read the current pending count |

## Usage

`PendingCounter` is usually created automatically when `BaseSpout` is initialized; users generally do not need to interact with it directly. `BaseSpout.get_counter()` and `BaseSpout.get_pending_count()` provide external access:

```python
from celestialflow.funnel import BaseSpout

class PrintSpout(BaseSpout):
    def _handle_record(self, record):
        print(record)

spout = PrintSpout()
spout.start()

spout.get_queue().put("task_1")
spout.get_queue().put("task_2")

print(f"Pending: {spout.get_pending_count()}")

spout.stop()
print(f"Pending after stop: {spout.get_pending_count()}")
```

## Notes

1. **Counting Scope**: `BaseSpout._spout()` dequeues a record, calls `_handle_record()`, and only calls `decrement()` after processing completes (including on exception). Therefore, `get_pending_count()` includes records that have been dequeued but are still being processed.
2. **Rollback Mechanism**: `BaseInlet._funnel()` calls `increment()` before enqueueing; if enqueueing fails, it immediately calls `decrement()` to roll back the count.
3. **Thread Safety**: All operations are protected by `Lock`, making them safe in multi-producer / single-consumer scenarios.
