# TaskEnvelope

A wrapper class for task data that is passed between stages. It encapsulates the raw task data, task hash, task ID, and source information.

## Attributes

```python
class TaskEnvelope:
    __slots__ = ("task", "hash", "id", "source")

    def __init__(self, task, hash: str, id: int, source: str = "input"):
        self.task = task      # Raw task data
        self.hash = hash      # Hash of the task content
        self.id = id          # Unique task ID
        self.source = source  # Task source (default "input")
```

## Class Methods

```python
@classmethod
def wrap(cls, task, task_id: int, source: str = "input"):
    """
    Wrap a raw task into a TaskEnvelope.

    :param task: Raw task
    :param task_id: Task ID
    :param source: Task source
    :return: TaskEnvelope instance
    """
```

## Instance Methods

```python
def unwrap(self) -> tuple:
    """
    Unwrap a TaskEnvelope.

    :return: (task, hash, id, source)
    """

def change_id(self, new_id: int):
    """
    Change the task ID (used in retry scenarios).

    :param new_id: New task ID
    """
```

## Usage Example

```python
from celestialflow.runtime import TaskEnvelope

# Wrap a task
envelope = TaskEnvelope.wrap(task_data, task_id=123, source="input")

# Unwrap
task, hash, id, source = envelope.unwrap()

# Change ID (on retry)
envelope.change_id(456)
```
