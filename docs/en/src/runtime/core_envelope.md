# TaskEnvelope

> 📅 Last Updated: 2026/06/11

A wrapper class for task data that is passed between Stages. It encapsulates the original task data, task hash, task ID, and source information.

## Attributes

```python
class TaskEnvelope:
    __slots__ = ("task", "hash", "id", "source", "prev")

    def __init__(self, task: Any, id: int, source: str, prev: Any = None):
        self.task = task      # Original task data
        self.hash = None      # Hash value (lazy evaluation)
        self.id = id          # Unique task ID
        self.source = source  # Task source identifier
        self.prev = prev      # Previous task (for result cache backtracking)
```

## Getter Methods

```python
def get_task(self) -> Any:
    """Get the original task data."""

def get_hash(self) -> bytes:
    """Get the task hash. Lazily computed and cached on first call."""

def get_id(self) -> int:
    """Get the task ID."""

def get_prev(self) -> Any | None:
    """Get the previous task (for result cache backtracking)."""
```

## Lazy Hashing

`hash` is `None` at construction time and is only computed on the first call to `get_hash()`. This avoids wasting computation resources in scenarios where dedup checking is not needed.

- For normally serializable tasks, `get_hash()` uses `object_to_hash()` to generate a stable SHA1 byte string.
- If the task object cannot be pickled / hashed, `get_hash()` no longer raises the exception directly to the caller, but instead falls back to a unique per-`TaskEnvelope` placeholder byte string.
- This fallback value carries a dedicated prefix, semantically representing "unique placeholder for unhashable tasks," to avoid interfering with normal task dedup and scheduling.

```python
envelope = TaskEnvelope("data", id=1, source="input")
assert envelope.hash is None         # Not yet computed
h = envelope.get_hash()              # First call, computes and caches
assert envelope.hash is not None     # Now cached
assert envelope.get_hash() == h      # Subsequent calls return cached value
```

## Usage Examples

The following examples demonstrate core operations of `TaskEnvelope`: creation, data access, lazy hash computation, and ID changes.

```python
from celestialflow.runtime import TaskEnvelope

# 1. Create task envelope
envelope = TaskEnvelope(
    task={"user": "alice", "score": 95},
    id=1,
    source="input",
)

# 2. Get original task data
task = envelope.get_task()
print(f"Task data: {task}")  # {"user": "alice", "score": 95}

# 3. Check initial state (hash not yet computed — lazy evaluation)
print(f"Initial hash: {envelope.hash}")  # None

# 4. Get task ID
print(f"Task ID: {envelope.get_id()}")  # 1

# 5. First call to get_hash() computes and caches SHA1
h = envelope.get_hash()
print(f"SHA1 hash: {h.hex()[:16]}...")
print(f"Hash cached after call: {envelope.hash is not None}")  # True
print(f"Repeat call returns cached value: {envelope.get_hash() == h}")    # True

# 6. Get predecessor task (for result cache backtracking)
print(f"Predecessor task: {envelope.get_prev()}")  # None (prev not set)
```

### Multiple Data Types

```python
from celestialflow.runtime import TaskEnvelope

# Different types of task data
env_str = TaskEnvelope(task="hello world", id=2, source="producer")
env_list = TaskEnvelope(task=[1, 2, 3], id=3, source="producer")
env_dict = TaskEnvelope(task={"key": "value"}, id=4, source="producer")
env_none = TaskEnvelope(task=None, id=5, source="producer")

# prev parameter: records predecessor task (for result cache backtracking)
env_with_prev = TaskEnvelope(task="data", id=6, source="producer", prev=env_str)
print(f"Predecessor task data: {env_with_prev.prev.get_task()}")
```

### Fallback Behavior for Unhashable Tasks

```python
from celestialflow.runtime import TaskEnvelope

class UnpicklableTask:
    def __getstate__(self):
        raise TypeError("cannot pickle")

env1 = TaskEnvelope(task=UnpicklableTask(), id=101, source="input")
env2 = TaskEnvelope(task=UnpicklableTask(), id=102, source="input")

h1 = env1.get_hash()
h2 = env2.get_hash()

assert h1.startswith(b"__unhashable_task__:")
assert h2.startswith(b"__unhashable_task__:")
assert h1 != h2
```

The goal of this behavior is not to allow unhashable tasks to participate in "content-based dedup," but to ensure:

- A single unhashable task does not interrupt the entire scheduling chain
- No false hash collisions with normal tasks
- Different unhashable task envelopes still have unique identifiers
