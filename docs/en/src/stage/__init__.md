# Stage Module

> 📅 Last Updated: 2026/06/11

The Stage module defines the task execution units in CelestialFlow. It provides a complete system from basic task executors to complex task nodes, serving as the fundamental building blocks for constructing task graphs.

## Exported Symbols

| Exported Symbol | Source Module | Description |
|---------|---------|------|
| `TaskExecutor` | `core_executor` | Basic task executor, supporting serial/thread/async execution modes |
| `TaskStage` | `core_stage` | Enhanced task node, inherits `TaskExecutor`, adds graph connection capability and `stage_mode` control |
| `TaskSplitter` | `core_stages` | Predefined node: splits a single task into multiple sub-tasks |
| `TaskRouter` | `core_stages` | Predefined node: routes tasks to different downstream nodes based on conditions |
| `TaskRedisTransport` | `core_stages` | Predefined node: pushes tasks to a Redis queue |
| `TaskRedisSource` | `core_stages` | Predefined node: pulls tasks from a Redis queue as an input source |
| `TaskRedisAck` | `core_stages` | Predefined node: waits for execution results from remote Workers |

> The `AnyTaskStage` type alias is defined in `util_types.py` and is not included in `__all__`.

## Module Overview

The Stage module consists of three levels of task execution units:
1. **TaskExecutor**: Basic task executor, handling single-task execution logic
2. **TaskStage**: Enhanced task node, adding graph connection capabilities
3. **Predefined Nodes**: Implementations of common task patterns, such as splitters, routers, Redis integration, etc.

These components together form the core of task execution, where each component can be used independently or combined into complex task flows.

## File Descriptions

### Core Files

1. **core_executor.py** (`TaskExecutor`)
   - **Purpose**: Basic task executor, handling single-task execution, concurrency control, error handling, and retry mechanisms
   - **Key Features**:
     - Synchronous/asynchronous task execution
     - Error handling and retry strategies
     - Observer pattern lifecycle broadcasting
     - Result collection and error recording

2. **core_stage.py** (`TaskStage`)
   - **Purpose**: Enhanced task node, inheriting from `TaskExecutor`, adding graph structure connection capabilities
   - **Key Features**:
     - Supports `stage_mode` (serial/thread) to control node scheduling within the Graph
     - Inlet binding (`set_inlet`) to connect fail/log queues to the persistence layer
     - Upstream node counter binding (`prev_bindings`)
     - State management and lifecycle control (`NOT_STARTED → RUNNING → STOPPED`)

3. **core_stages.py** (Predefined nodes: `TaskSplitter`, `TaskRouter`, `TaskRedisTransport`, `TaskRedisSource`, `TaskRedisAck`)
   - **Purpose**: Pre-implementations of common task patterns and Redis integration nodes
   - **Included Nodes**:
     - `TaskSplitter`: Distributes input to multiple sub-tasks
     - `TaskRouter`: Routes tasks to different downstream nodes based on conditions
     - `TaskRedisTransport`: Sends tasks to a Redis queue for cross-language or distributed execution
     - `TaskRedisSource`: Consumes tasks from a Redis queue as the input source of a task graph
     - `TaskRedisAck`: Receives execution results from Redis Workers and acknowledges task completion

4. **util_types.py** (`AnyTaskStage`)
   - **Purpose**: Provides a type alias `TaskStage[Any, Any]` for wildcard annotation of Stages with arbitrary generic parameters

## Module Relationships

### Internal Relationships
- `TaskStage` inherits from `TaskExecutor`, extending it with graph connection functionality
- Predefined nodes are all specialized implementations of `TaskStage`
- All nodes can be composed together within a `TaskGraph`

### External Relationships
- **With Graph Module**: `TaskStage` is the fundamental building block of `TaskGraph`
- **With Runtime Module**: Uses `TaskInQueue` / `TaskOutQueue` for inter-node communication, depends on `TaskDispatch` for execution
- **With Persistence Module**: Persists task state via `FailInlet` / `LogInlet`
- **With Observability Module**: Registers `BaseObserver` subclasses via `add_observer()`

## Usage Examples

The following examples demonstrate typical usage of the core classes in the stage module.

### TaskExecutor Standalone Usage

```python
from celestialflow import TaskExecutor

# Define processing function
def process_item(x: int) -> int:
    return x * 10

# Create and execute
executor = TaskExecutor(
    name="Calculator",
    func=process_item,
    execution_mode="serial",
)
executor.start([1, 2, 3])

# Get results
success = executor.get_success_pairs()
for task, result in success:
    print(f"{task} -> {result}")
```

### TaskStage as Graph Node

```python
from celestialflow import TaskGraph, TaskStage

# Create stage nodes
stage_a = TaskStage("StageA", func=lambda x: x + 1, stage_mode="thread")
stage_b = TaskStage("StageB", func=lambda x: x * 2, stage_mode="serial")

# Build graph
graph = TaskGraph()
graph.set_stages([stage_a, stage_b])
graph.connect([stage_a], [stage_b])

# Execute
graph.start_graph({stage_a.get_name(): [5, 10, 15]})

# Stage snapshot
for name, runtime in graph.stage_runtime_dict.items():
    summary = runtime.stage.get_summary()
    print(f"{name}: {summary}")
```

### TaskSplitter Usage Example

```python
from celestialflow import TaskGraph, TaskStage, TaskSplitter

# Custom splitter: split strings by comma
class CommaSplitter(TaskSplitter):
    def _split(self, *task):
        return tuple(task[0].split(","))

# Build graph
raw = TaskStage("Source", func=lambda x: x, stage_mode="serial")
splitter = CommaSplitter("Splitter")
processor = TaskStage("Process", func=lambda x: x.strip().upper(), stage_mode="thread")

graph = TaskGraph()
graph.set_stages([raw, splitter, processor])
graph.connect([raw], [splitter])
graph.connect([splitter], [processor])

graph.start_graph({raw.get_name(): ["a,b,c", "x,y,z"]})
```

### TaskRouter Usage Example

```python
from celestialflow import TaskGraph, TaskStage, TaskRouter

# Define a processing function that generates routing info
def classify(x: int) -> tuple:
    if x > 0:
        return ("positive", x)
    else:
        return ("negative", x)

source = TaskStage("Source", func=classify, stage_mode="serial")
router = TaskRouter("Router")
pos = TaskStage("Positive", func=lambda x: f"POS: {x}", stage_mode="serial")
neg = TaskStage("Negative", func=lambda x: f"NEG: {x}", stage_mode="serial")

graph = TaskGraph()
graph.set_stages([source, router, pos, neg])
graph.connect([source], [router])
graph.connect([router], [pos, neg])  # Route to both downstream nodes

graph.start_graph({source.get_name(): [5, -3, 10, -8]})
```

## Design Principles

- **Single-Use Objects**: Both `TaskExecutor` and `TaskStage` are designed for single use and should not be reused after completing one run
- **Single Responsibility**: Each `TaskExecutor` handles only a single type of task
- **Composability**: All nodes use a unified interface and can be freely composed into a `TaskGraph`
