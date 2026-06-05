# SuccessSpout

> 📅 Last Updated: 2026/05/24

`SuccessSpout` inherits from `BaseSpout` and continuously listens to the success result queue, caching task-result pairs.

## Architecture Design

```mermaid
flowchart LR
    Queue[queue.Queue] -->|Daemon thread polling| Spout[SuccessSpout._handle_record]
    Spout --> IsEnvelope{Is record a
TaskEnvelope?}
    IsEnvelope -->|No| Drop[Discard]
    IsEnvelope -->|Yes| Extract[Extract result = record.task
task = record.prev]
    Extract --> Append[Append to
success_pairs list]
    Append --> Get[get_success_pairs
returns list[(task, result)]]

    style Queue fill:#fff3e0
    style Spout fill:#e8f5e9
    style IsEnvelope fill:#fff9c4
    style Extract fill:#e3f2fd
    style Append fill:#c8e6c9
    style Get fill:#f3e5f5
```

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
    Get the list of successful task-result pairs

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

## Usage Examples

### SuccessSpout with TaskExecutor to Retrieve Success Results

The following complete example shows how to use `SuccessSpout` to retrieve all successful `(task, result)` pairs:

```python
import asyncio
from celestialflow import TaskExecutor


def double(x: int) -> int:
    """Simple processing function: doubles the input value"""
    if x < 0:
        raise ValueError(f"Cannot process negative number: {x}")
    return x * 2


async def main():
    # 1. Create executor
    executor = TaskExecutor(
        "Double Processor",
        double,
        execution_mode="thread",
        max_workers=4,
    )

    # 2. Start executor to process numbers 0~9
    #    SuccessSpout automatically listens to the success result queue in the background
    await executor.start(range(10))

    # 3. Retrieve all successful (task, result) pairs
    #    executor.get_success_pairs() delegates to SuccessSpout
    pairs = executor.get_success_pairs()

    # 4. Output results
    print(f"Successfully processed {len(pairs)} tasks:")
    for task, result in pairs:
        print(f"  Input: {task:>3}  ->  Output: {result}")

    # Expected output:
    #   Input:   0  ->  Output: 0
    #   Input:   1  ->  Output: 2
    #   Input:   2  ->  Output: 4
    #   ...
    #   Input:   9  ->  Output: 18


asyncio.run(main())
```

### Retrieving Success Results from All Nodes in a TaskGraph

When using `TaskGraph` with multiple stages, you can retrieve success results from each stage's executor:

```python
import asyncio
from celestialflow import TaskGraph, TaskStage


def stage_a(x: int) -> str:
    return f"processed-{x}"


def stage_b(s: str) -> dict:
    return {"key": s.upper()}


async def main():
    # Create multi-stage task graph
    graph = TaskGraph(schedule_mode="staged")
    sa = TaskStage("StageA", stage_a, execution_mode="thread")
    sb = TaskStage("StageB", stage_b, execution_mode="thread")
    graph.set_stages([sa, sb])
    graph.connect([sa], [sb])

    # Start task graph
    await graph.start_graph({sa.get_tag(): ["apple", "banana", "cherry"]})

    # Retrieve success results from each stage's executor
    # Note: the actual property name may be _executor; please refer to the specific version
    for stage in [sa, sb]:
        pairs = stage.get_success_pairs()
        print(f"Node {stage.get_tag()}: {len(pairs)} tasks succeeded")
        for task, result in pairs[:2]:  # Only print first 2
            print(f"  Input: {task} -> Output: {result}")


asyncio.run(main())
```
