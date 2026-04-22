# Stage Module

The Stage module defines the task execution units in CelestialFlow. It provides a complete hierarchy from basic task executors to complex task nodes, serving as the fundamental building blocks for constructing task graphs.

## Module Overview

The Stage module contains three levels of task execution units:
1. **TaskExecutor**: Basic task executor that handles the execution logic of a single task
2. **TaskStage**: Enhanced task node with graph connection capabilities
3. **Predefined Nodes**: Implementations of common task patterns, such as splitters, routers, etc.

These components together form the core of task execution, and each can be used independently or combined into complex task flows.

## File Descriptions

### Core Files

1. **core_executor.py** (`TaskExecutor`)
   - **Purpose**: Basic task executor that handles single task execution, concurrency control, error handling, and retry mechanisms
   - **Key Features**:
     - Synchronous/asynchronous task execution
     - Error handling and retry strategies
     - Timeout control
     - Progress reporting and logging
     - Resource management and cleanup

2. **core_stage.py** (`TaskStage`)
   - **Purpose**: Enhanced task node that inherits from `TaskExecutor` and adds graph structure connection capabilities
   - **Key Features**:
     - Support for input/output queue connections
     - Automatic dependency management
     - Graph-aware execution
     - Support for parallel and serial connections
     - State management and lifecycle control

3. **core_stages.py** (Predefined Nodes: `TaskSplitter`, `TaskRouter`, `TaskRedisTransport`, `TaskRedisSource`, `TaskRedisAck`)
   - **Purpose**: Pre-built implementations of common task patterns and Redis integration nodes to simplify complex workflow construction
   - **Included Nodes**:
     - `TaskSplitter`: Distributes input to multiple subtasks
     - `TaskRouter`: Routes tasks to different downstream nodes based on conditions
     - `TaskRedisTransport`: Sends tasks to a Redis queue for cross-language or distributed execution
     - `TaskRedisSource`: Consumes tasks from a Redis queue as an input source for the task graph
     - `TaskRedisAck`: Receives execution results from Redis Workers and acknowledges task completion

## Module Relationships

### Internal Relationships
- `TaskStage` inherits from `TaskExecutor`, extending it with graph connection functionality
- All predefined nodes are specialized implementations of `TaskStage`
- All nodes can be combined within a `TaskGraph`

### External Relationships
- **With Graph Module**: `TaskStage` is the basic building unit of `TaskGraph`
- **With Runtime Module**: Uses `TaskQueue` for inter-node communication and relies on `TaskDispatch` for execution
- **With Utils Module**: Uses utility functions for data processing and transformation
- **With Persistence Module**: Supports persistent saving of task states

## Usage Patterns

### Basic Usage
1. **Create an Executor**: Inherit from `TaskExecutor` to implement custom business logic
2. **Wrap as a Node**: Use `TaskStage` to wrap the executor, enabling graph connections
3. **Build a Graph**: Add nodes to a `TaskGraph` and establish dependency relationships

### Advanced Usage
1. **Use Predefined Nodes**: Directly use `TaskSplitter`, `TaskRouter`, etc. to simplify development
2. **Compose Nodes**: Combine multiple nodes into complex data processing pipelines
3. **Custom Nodes**: Inherit from `TaskStage` to create domain-specific node types

## Design Principles

### Single Responsibility
- Each `TaskExecutor` handles only a single type of task
- `TaskStage` focuses on graph connections and state management
- Predefined nodes implement specific data processing patterns

### Composability
- All nodes use a unified interface and can be freely composed
- Supports chained calls and parallel processing
- Input/output type compatibility checks

### Extensibility
- Easily create custom nodes through inheritance
- Supports plugin-based architecture
- Configuration-driven, allowing behavior adjustments without code changes

## Best Practices

1. **Simple Tasks**: Directly use or inherit from `TaskExecutor`
2. **Graph Nodes**: Always use `TaskStage` or its subclasses as graph nodes
3. **Data Processing**: Prefer predefined nodes to reduce duplicate code
4. **Error Handling**: Implement robust error handling at the `TaskExecutor` level
5. **Resource Management**: Properly implement the `cleanup()` method to release resources
