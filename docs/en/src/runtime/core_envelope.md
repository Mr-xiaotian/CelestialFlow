# TaskEnvelope

> 📅 Last Updated: 2026/06/18

A wrapper class for task data that is passed between Stages. It encapsulates the original task data, task hash, and task ID.

> ⚠️ **Changed**: The `source` and `prev` fields described in previous documentation have been removed during refactoring. `TaskEnvelope` currently only contains three core fields: `hash`, `id`, `task`.

## Attributes

```python
class TaskEnvelope:
    __slots__ = ("hash", "id", "task")

    def __init__(self, task: T, id: int):
        self.task: T = task   # Original task data
        self.hash: bytes | None = None  # Hash value (lazy computation)
        self.id: int = id     # Unique task ID
```

## Getter Methods

```python
def get_task(self) -> T:
    """Get the original task data."""

def get_hash(self) -> bytes:
    """Get the task hash value. Lazily computed and cached on first call."""

def get_id(self) -> int:
    """Get the task ID."""
```

## Lazy Hashing

`hash` is `None` at construction time and is only computed on the first call to `get_hash()`. This avoids wasting computational resources when deduplication checks are not needed.

- For normally serializable tasks, `get_hash()` uses `object_to_hash()` to generate a stable SHA1 byte string.
- If a task object cannot be pickled / hashed, `get_hash()` no longer throws the exception directly to the caller; instead, it falls back to a fallback byte string that is unique to that `TaskEnvelope` only.
- This fallback value carries a dedicated prefix, semantically indicating "unique placeholder for an unhashable task", preventing interference with normal task deduplication and scheduling.

```python
envelope = TaskEnvelope(task="data", id=1)
assert envelope.hash is None         # Not yet computed
h = envelope.get_hash()              # First call — computed and cached
assert envelope.hash is not None     # Now cached
assert envelope.get_hash() == h      # Subsequent calls return cached value
```

## Usage Example

The following examples demonstrate core `TaskEnvelope` operations: creation, data access, lazy hash computation, and ID changes.

```python
from celestialflow.runtime import TaskEnvelope

# 1. Create a task envelope
envelope = TaskEnvelope(
    task={"user": "alice", "score": 95},
    id=1,
)

# 2. Get the original task data
task = envelope.get_task()
print(f"Task data: {task}")  # {"user": "alice", "score": 95}

# 3. Check initial state (hash not yet computed — lazy evaluation)
print(f"Initial hash: {envelope.hash}")  # None

# 4. Get the task ID
print(f"Task ID: {envelope.get_id()}")  # 1

# 5. First call to get_hash() computes and caches SHA1
h = envelope.get_hash()
print(f"SHA1 hash: {h.hex()[:16]}...")
print(f"Hash cached after call: {envelope.hash is not None}")  # True
print(f"Repeat call returns cached value: {envelope.get_hash() == h}")    # True
```

### Multiple Data Types

```python
from celestialflow.runtime import TaskEnvelope

# Different types of task data
env_str = TaskEnvelope(task="hello world", id=2)
env_list = TaskEnvelope(task=[1, 2, 3], id=3)
env_dict = TaskEnvelope(task={"key": "value"}, id=4)
env_none = TaskEnvelope(task=None, id=5)
```

### Fallback Behavior for Unhashable Tasks

```python
from celestialflow.runtime import TaskEnvelope

class UnpicklableTask:
    def __getstate__(self):
        raise TypeError("cannot pickle")

env1 = TaskEnvelope(task=UnpicklableTask(), id=101)
env2 = TaskEnvelope(task=UnpicklableTask(), id=102)

h1 = env1.get_hash()
h2 = env2.get_hash()

assert h1.startswith(b"__unhashable_task__:")
assert h2.startswith(b"__unhashable_task__:")
assert h1 != h2
```

The goal of this behavior is not to allow unhashable tasks to participate in "content-based deduplication", but to guarantee that:

- A single unhashable task does not interrupt the entire scheduling pipeline
- It does not mistakenly collide with normal task hashes
- Different unhashable task envelopes still have unique identifiers
