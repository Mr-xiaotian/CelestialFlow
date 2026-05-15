# SuccessSpout

> 📅 Last Updated: 2026/04/24

`SuccessSpout` inherits from `BaseSpout` and continuously listens to the success result queue, caching task-result pairs.

## Initialization

```python
class SuccessSpout(BaseSpout):
    def __init__(self):
        super().__init__()
        self.success_pairs: list[tuple[Any, Any]] = []
```

## Core Methods

### get_success_pairs

```python
def get_success_pairs(self) -> list[tuple[Any, Any]]:
    """
    Get the list of successful task-result pairs.

    :return: [(task, result), ...]
    """
```

## Internal Implementation

### _handle_record

Receives a `TaskEnvelope` from the queue, extracts the original task (`record.prev`) and the result (`record.task`), and appends them to `success_pairs`.

### _before_start

Clears `success_pairs` before starting.

## Use Cases

Success results are sent to the `SuccessSpout` queue. After execution completes, you can retrieve all successful (task, result) pairs via `get_success_pairs()`.

```python
executor = TaskExecutor("Processor", process)
executor.start(tasks)
pairs = executor.get_success_pairs()
```
