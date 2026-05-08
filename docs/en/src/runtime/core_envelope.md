# TaskEnvelope

> 📅 Last updated: 2026/05/08

A wrapper class for task data passed between Stages. It encapsulates the original task data, task hash, task ID, and source information.

## Attributes

```python
class TaskEnvelope:
    __slots__ = ("task", "hash", "id", "source", "prev")

    def __init__(self, task: Any, id: int, source: str, prev: Any = None):
        self.task = task      # Original task data
        self.hash = None      # Hash value (lazily computed)
        self.id = id          # Unique task ID
        self.source = source  # Task source identifier
        self.prev = prev      # Previous task (for result cache backtracking)
```

## Getter Methods

```python
def get_task(self) -> Any:
    """Get the original task data."""

def get_hash(self) -> str:
    """Get the task hash. Lazily computed and cached on first call."""

def get_id(self) -> int:
    """Get the task ID."""

def change_id(self, new_id: int) -> None:
    """Change the task ID (used in retry scenarios)."""
```

## Lazy Hash

`hash` is `None` at construction time and only computed on the first call to `get_hash()`. This avoids wasting computation when duplicate checking is not needed.

```python
envelope = TaskEnvelope("data", id=1, source="input")
assert envelope.hash is None         # Not yet computed
h = envelope.get_hash()              # First call computes and caches
assert envelope.hash is not None     # Cached
assert envelope.get_hash() == h      # Subsequent calls return cached value
```

## Usage Example

```python
from celestialflow.runtime import TaskEnvelope

# Create envelope
envelope = TaskEnvelope(task_data, id=123, source="input")

# Get data
task = envelope.get_task()
task_hash = envelope.get_hash()
task_id = envelope.get_id()

# Change ID (on retry)
envelope.change_id(456)
```
