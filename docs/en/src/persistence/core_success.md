# SuccessSpout

> 📅 Last updated: 2026/04/24

`SuccessSpout` inherits from `BaseSpout` and is used to continuously listen to the success result queue and cache task-result pairs.

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

## Usage Scenario

Success results are sent to the `SuccessSpout` queue. After execution completes, all successful (task, result) pairs can be retrieved via `get_success_pairs()`.

```python
executor = TaskExecutor("Processor", process)
executor.start(tasks)
pairs = executor.get_success_pairs()
```
