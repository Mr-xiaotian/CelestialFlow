# TaskEnvelope

> 📅 Last Updated: 2026/06/05

A wrapper class for task data, passed between Stages. It encapsulates the raw task data, task hash, task ID, and source information.

## Hash Behavior

- For normal tasks, `get_hash()` delegates to `object_to_hash()` and caches the SHA1 bytes result.
- If the task cannot be pickled / hashed, `get_hash()` falls back to a unique byte string with the `__unhashable_task__:` prefix instead of raising an exception.
- The fallback is envelope-unique and is intended to keep one bad task from breaking the rest of the dispatch flow.

## Attributes

```python
class TaskEnvelope:
    __slots__ = ("task", "hash", "id", "source", "prev")

    def __init__(self, task: Any, id: int, source: str, prev: Any = None):
        self.task = task      # Raw task data
        self.hash = None      # Hash value (lazily computed)
        self.id = id          # Unique task ID
        self.source = source  # Task source identifier
        self.prev = prev      # Previous task (for result cache backtracking)
```

## Getter Methods

```python
def get_task(self) -> Any:
    """Get the raw task data."""

def get_hash(self) -> bytes:
    """Get the task hash. Lazily computed and cached on first call."""

def get_id(self) -> int:
    """Get the task ID."""

def change_id(self, new_id: int) -> None:
    """Change the task ID (used in retry scenarios)."""
```

## Lazy Hashing

The `hash` is `None` at construction time and is only computed on the first call to `get_hash()`. This avoids wasting computational resources in scenarios where deduplication checks are not needed.

If hashing fails for an unpicklable task, the cached value becomes the fallback bytes described above.

```python
envelope = TaskEnvelope("data", id=1, source="input")
assert envelope.hash is None         # Not computed
h = envelope.get_hash()              # First call, computed and cached
assert envelope.hash is not None     # Cached
assert envelope.get_hash() == h      # Subsequent calls return cached value
```

## Usage Example

```python
from celestialflow.runtime import TaskEnvelope

# Create an envelope
envelope = TaskEnvelope(task_data, id=123, source="input")

# Get data
task = envelope.get_task()
task_hash = envelope.get_hash()
task_id = envelope.get_id()

# Change ID (on retry)
envelope.change_id(456)
```
