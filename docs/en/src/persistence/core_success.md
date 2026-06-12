# SuccessSpout

> 📅 Last Updated: 2026/06/11

`SuccessSpout` inherits from `BaseSpout` and is used to continuously listen to the success result queue and cache task-result pairs.

## Architecture Design

```mermaid
flowchart LR
    Queue[queue.Queue] -->|Daemon thread polling| Spout[SuccessSpout._handle_record]
    Spout --> IsEnvelope{record is<br/>TaskEnvelope?}
    IsEnvelope -->|No| Drop[Drop]
    IsEnvelope -->|Yes| Extract[Extract result = record.task<br/>task = record.prev]
    Extract --> Append[Append to<br/>success_pairs list]
    Append --> Get[get_success_pairs<br/>Returns list[(task, result)]]
```

## Initialization

```python
class SuccessSpout[T, R](BaseSpout):
    def __init__(self):
        super().__init__()
        self.success_pairs: list[tuple[T, R]] = []
```

## Core Methods

### get_success_pairs

```python
def get_success_pairs(self) -> list[tuple[T, R]]:
    """
    Get list of successful task and result pairs

    :return: [(task, result), ...]
    """
```

## Internal Implementation

### _handle_record

Receives `TaskEnvelope` from the queue, checks the type, extracts the original task (`record.prev`) and result (`record.task`), and appends to `success_pairs`. Non-`TaskEnvelope` records are directly dropped.

### _before_start

Clears `success_pairs` before starting to ensure clean results for each run.

## Usage Scenarios

Success results are sent to the `SuccessSpout`'s queue. After execution ends, all successful (task, result) pairs can be obtained via `get_success_pairs()`. `TaskExecutor`'s `get_success_pairs()` delegates to the internal `SuccessSpout`.

## Usage Examples

### SuccessSpout Used with TaskExecutor to Retrieve Success Results

```python
from celestialflow import TaskExecutor


def double(x: int) -> int:
    """Simple processing function: double the input value"""
    if x < 0:
        raise ValueError(f"Cannot process negative number: {x}")
    return x * 2


# 1. Create executor
executor = TaskExecutor(
    "Double",
    double,
    execution_mode="thread",
    max_workers=4,
)

# 2. Start executor to process numbers 0~9
#    SuccessSpout automatically listens to the success result queue in the background
executor.start(range(10))

# 3. Get all successful (task, result) pairs
pairs = executor.get_success_pairs()

print(f"Successfully processed {len(pairs)} tasks:")
for task, result in pairs:
    print(f"  Input: {task:>3}  ->  Output: {result}")
```

### Retrieve Success Results from All Nodes in a TaskGraph

When using `TaskGraph` with multi-stage task graphs, you can retrieve success results from each stage's executor:

```python
from celestialflow import TaskGraph, TaskStage


def stage_a(x: int) -> str:
    return f"processed-{x}"


def stage_b(s: str) -> dict:
    return {"key": s.upper()}


# Create multi-stage task graph
graph = TaskGraph(schedule_mode="staged")
sa = TaskStage("StageA", stage_a, execution_mode="thread")
sb = TaskStage("StageB", stage_b, execution_mode="thread")
graph.set_stages([sa, sb])
graph.connect([sa], [sb])

# Start task graph
graph.start_graph({sa.get_name(): ["apple", "banana", "cherry"]})

# Get success results from each stage's executor
for stage in [sa, sb]:
    pairs = stage.get_success_pairs()
    print(f"Node {stage.get_name()}: {len(pairs)} tasks succeeded")
    for task, result in pairs[:2]:
        print(f"  Input: {task} -> Output: {result}")
```

> **Changed**: Previous example used `stage.get_tag()` and `await graph.start_graph()`. In the current source code, Stage uses `get_name()` as the unique identifier, and `start_graph()` is a synchronous method.
