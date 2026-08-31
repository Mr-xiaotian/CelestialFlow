# Stage Module

> 📅 Last Updated: 2026/08/26

The Stage module defines the task execution units in CelestialFlow. It provides a complete system from basic task executors to complex task nodes, serving as the fundamental building blocks for constructing task graphs.

## Exported Symbols

| Exported Symbol | Source Module | Description |
|---------|---------|------|
| `TaskExecutor` | `core_executor` | Basic task executor, supporting serial/thread/async execution modes |
| `TaskStage` | `core_stage` | Enhanced task node, inheriting TaskExecutor with graph connection capabilities |
| `TaskSplitter` | `core_stages` | Predefined node: splits a single task into multiple sub-tasks |
| `TaskRouter` | `core_stages` | Predefined node: routes tasks to different downstream nodes based on conditions |

> The `AnyTaskStage` type alias is defined in `util_types.py` and is not included in `__all__`.

## Module Overview

The Stage module contains three levels of task execution units:
1. **TaskExecutor**: Basic task executor, handling single-task execution logic
2. **TaskStage**: Enhanced task node, adding graph connection capabilities
3. **Predefined Nodes**: Implementations of common task patterns, such as splitters and routers

These components together form the core of task execution; each component can be used independently or combined into complex task flows.

## File Descriptions

### Core Files

1. **core_executor.py** (`TaskExecutor`)
   - **Purpose**: Basic task executor, handling single-task execution, concurrency control, error handling, and retry mechanisms
   - **Key Features**:
     - Synchronous/async task execution
     - Error handling and retry strategies
     - Observer pattern lifecycle broadcasting
     - Result collection and error recording

2. **core_stage.py** (`TaskStage`)
   - **Purpose**: Enhanced task node, inheriting from `TaskExecutor`, with added graph structure connection capabilities
   - **Key Features**:
     - `prev_binding()` / `get_binding_counter()` implement predecessor/successor node counter binding
     - State snapshot (`snapshot()`) supports progress estimation
     - Queue draining (`drain_task_queue()`) marks unconsumed tasks as failed

3. **core_stages.py** (Predefined nodes: `TaskSplitter`, `TaskRouter`)
   - **Purpose**: Pre-implementations of common structural task patterns
   - **Contained Nodes**:
     - `TaskSplitter`: Distributes a single input to multiple sub-tasks
     - `TaskRouter`: Routes tasks to different downstream nodes based on conditions

4. **core_dispatch.py** (`TaskDispatch`)
   - **Purpose**: Task dispatcher, fetching tasks from `TaskInQueue` based on execution mode (serial/thread/async) and calling the user function

5. **util_types.py** (`AnyTaskStage`)
   - **Purpose**: Provides the `TaskStage[Any, Any]` type alias for wildcard annotation of Stages with arbitrary generic parameters

## Module Relationships

### Internal Relationships
- `TaskStage` inherits from `TaskExecutor`, extending it with graph connection functionality
- Predefined nodes are all specialized implementations of `TaskStage`
- All nodes can be combined and used within `TaskGraph`

### External Relationships
- **With Graph Module**: `TaskStage` is the basic building block of `TaskGraph`
- **With Runtime Module**: Uses `TaskInQueue` / `TaskOutQueue` for inter-node communication, depends on `TaskDispatch` for execution
- **With Persistence Module**: Persists task state via `LifecycleInlet` / `LogInlet`
- **With Observability Module**: Registers `BaseObserver` subclasses via `add_observer()`

## Usage Examples

The following examples demonstrate typical usage of the core classes in the stage module.

### TaskExecutor Standalone Usage

```python
from celestialflow import TaskExecutor


# Define a processing function
def process_item(x: int) -> int:
    return x * 10


# Create and execute
executor = TaskExecutor(
    name="Calculator",
    func=process_item,
    execution_mode="serial",
)
executor.run([1, 2, 3])

# Get results
success = executor.get_success_pairs()
for task, result in success:
    print(f"{task} -> {result}")
```

### TaskStage as a Graph Node

```python
from celestialflow import TaskGraph, TaskStage

# Create stage nodes
stage_a = TaskStage("StageA", func=lambda x: x + 1, execution_mode="thread")
stage_b = TaskStage("StageB", func=lambda x: x * 2, execution_mode="serial")

# Build graph
graph = TaskGraph()
graph.set_stages([stage_a, stage_b])
graph.connect([stage_a], [stage_b])

# Execute (synchronous entry)
graph.run({stage_a.get_name(): [5, 10, 15]})

# Stage snapshots
for name, stage in graph.stage_dict.items():
    summary = stage.get_summary()
    print(f"{name}: {summary}")
```

### TaskSplitter Usage Example

```python
from celestialflow import TaskGraph, TaskStage, TaskSplitter


# Custom splitter: split a string by commas
class CommaSplitter(TaskSplitter):
    def _split(self, task):
        return tuple(task.split(","))


# Build graph
raw = TaskStage("Source", func=lambda x: x, execution_mode="serial")
splitter = CommaSplitter("Splitter")
processor = TaskStage(
    "Process", func=lambda x: x.strip().upper(), execution_mode="thread"
)

graph = TaskGraph("SplitDemo")
graph.set_stages([raw, splitter, processor])
graph.connect([raw], [splitter])
graph.connect([splitter], [processor])

graph.run({raw.get_name(): ["a,b,c", "x,y,z"]})
```

### TaskRouter Usage Example

```python
from celestialflow import TaskGraph, TaskStage, TaskRouter


# Define a routing function: return target node name based on task content
def classify(x: int) -> str:
    if x > 0:
        return "positive"
    else:
        return "negative"


# Upstream only produces raw tasks
source = TaskStage("Source", func=lambda x: x, execution_mode="serial")

# Router internally decides which downstream to send the task to
router = TaskRouter("Router", classify)
pos = TaskStage("Positive", func=lambda x: f"POS: {x}", execution_mode="serial")
neg = TaskStage("Negative", func=lambda x: f"NEG: {x}", execution_mode="serial")

graph = TaskGraph("RouterDemo")
graph.set_stages([source, router, pos, neg])
graph.connect([source], [router])
graph.connect([router], [pos, neg])

graph.run({source.get_name(): [5, -3, 10, -8]})
```

## Design Principles

- **Single-use objects**: Both `TaskExecutor` and `TaskStage` are designed for single use and should not be reused after one run completes
- **Single responsibility**: Each `TaskExecutor` only handles a single type of task
- **Composability**: All nodes use a unified interface and can be freely combined into `TaskGraph`
