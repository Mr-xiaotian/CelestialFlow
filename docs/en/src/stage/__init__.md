# Stage Module

> 📅 Last Updated: 2026/05/28

The Stage module defines the task execution units in CelestialFlow. It provides a complete hierarchy from basic task executors to complex task nodes, serving as the fundamental building blocks for constructing task graphs.

## Module Overview

The Stage module contains three levels of task execution units:
1. **TaskExecutor**: Basic task executor, handles single task execution logic
2. **TaskStage**: Enhanced task node, adds graph connection capabilities
3. **Predefined Nodes**: Implementations of common task patterns, such as splitters, routers, etc.

These components together form the core of task execution, each usable independently or combined into complex task flows.

## File Description

### Core Files

1. **core_executor.py** (`TaskExecutor`)
   - **Purpose**: Basic task executor handling single task execution, concurrency control, error handling, and retry mechanisms
   - **Key Features**:
     - Synchronous/asynchronous task execution
     - Error handling and retry strategies
     - Timeout control
     - Progress reporting and logging
     - Resource management and cleanup

2. **core_stage.py** (`TaskStage`)
   - **Purpose**: Enhanced task node inheriting from `TaskExecutor`, with added graph structure connection capabilities
   - **Key Features**:
     - Input/output queue connections
     - Automatic dependency management
     - Graph-structure-aware execution
     - Parallel and serial connections
     - State management and lifecycle control

3. **core_stages.py** (Predefined Nodes: `TaskSplitter`, `TaskRouter`, `TaskRedisTransport`, `TaskRedisSource`, `TaskRedisAck`)
   - **Purpose**: Pre-implemented common task patterns and Redis integration nodes to simplify complex workflow construction
   - **Included Nodes**:
     - `TaskSplitter`: Splits input into multiple sub-tasks
     - `TaskRouter`: Routes tasks to different downstream nodes based on conditions
     - `TaskRedisTransport`: Sends tasks to Redis queues for cross-language or distributed execution
     - `TaskRedisSource`: Consumes tasks from Redis queues as input source for the task graph
     - `TaskRedisAck`: Receives execution results from Redis Workers and acknowledges task completion

## Module Relationships

### Internal Relationships
- `TaskStage` inherits from `TaskExecutor`, extending graph connection functionality
- Predefined nodes are specialized implementations of `TaskStage`
- All nodes can be combined within a `TaskGraph`

### External Relationships
- **With Graph Module**: `TaskStage` is the basic building unit of `TaskGraph`
- **With Runtime Module**: Uses `TaskInQueue`/`TaskOutQueue` for inter-node communication, depends on `TaskDispatch` for execution
- **With Utils Module**: Uses utility functions for data processing and transformation
- **With Persistence Module**: Supports persistent saving of task state

## Usage Patterns

### Basic Usage
1. **Create Executor**: Inherit from `TaskExecutor` to implement custom business logic
2. **Wrap as Node**: Use `TaskStage` to wrap an executor for graph connection support
3. **Build Graph Structure**: Add nodes to `TaskGraph` and establish dependencies

### Advanced Usage
1. **Use Predefined Nodes**: Directly use `TaskSplitter`, `TaskRouter`, etc. to simplify development
2. **Combine Nodes**: Compose multiple nodes into complex data processing pipelines
3. **Custom Nodes**: Inherit from `TaskStage` to create domain-specific node types

## Design Principles

### Single Responsibility
- Each `TaskExecutor` handles only a single type of task
- `TaskStage` focuses on graph connections and state management
- Predefined nodes implement specific data processing patterns

### Composability
- All nodes use a unified interface and can be freely combined
- Supports chaining and parallel processing
- Input/output type compatibility checking

### Extensibility
- Easily create custom nodes through inheritance
- Plugin-based architecture support
- Configuration-driven, adjustable behavior without code changes

## Usage Examples

The following examples demonstrate typical usage of core classes in the stage module.

### Standalone TaskExecutor Usage

```python
from celestialflow import TaskExecutor

# Define processing function
def process_item(x: int) -> dict:
    return {"input": x, "output": x * 10}

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

# Statistics
print(f"Success: {executor.get_counts()['tasks_succeeded']}")
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

# Stage snapshots
for name, stage in graph.stage_dict.items():
    summary = stage.get_summary()
    print(f"{name}: {summary}")

# Graph summary
print(graph.get_graph_summary())
```

### TaskSplitter Usage

```python
from celestialflow import TaskGraph, TaskStage, TaskSplitter

# Custom splitter: splits a string by commas
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
print(graph.get_graph_summary())
```

### TaskRouter Usage

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
graph.connect([router], [pos, neg])  # Route to two downstreams

graph.start_graph({source.get_name(): [5, -3, 10, -8]})
print(graph.get_graph_summary())
```

## Best Practices

1. **Simple Tasks**: Use `TaskExecutor` directly or inherit from it
2. **Graph Nodes**: Always use `TaskStage` or subclasses as graph nodes
3. **Data Processing**: Prefer predefined nodes to reduce duplicate code
4. **Error Handling**: Implement robust error handling at the `TaskExecutor` level
5. **Resource Management**: Properly implement the `cleanup()` method to release resources
