# Stage Module

> 📅 Last updated: 2026/04/24

The Stage module defines the task execution units in CelestialFlow. It provides a complete hierarchy from basic task executors to complex task nodes, serving as the fundamental building blocks for constructing task graphs.

## Module Overview

The Stage module contains three levels of task execution units:
1. **TaskExecutor**: Basic task executor, handles the execution logic of individual tasks
2. **TaskStage**: Enhanced task node, adds graph connection capabilities
3. **Predefined Nodes**: Implementations of common task patterns, such as splitters, routers, etc.

These components together form the core of task execution. Each component can be used independently or combined into complex task flows.

## File Descriptions

### Core Files

1. **core_executor.py** (`TaskExecutor`)
   - **Purpose**: Basic task executor that handles individual task execution, concurrency control, error handling, and retry mechanisms
   - **Key Features**:
     - Synchronous/asynchronous task execution
     - Error handling and retry strategies
     - Timeout control
     - Progress reporting and logging
     - Resource management and cleanup

2. **core_stage.py** (`TaskStage`)
   - **Purpose**: Enhanced task node that inherits from `TaskExecutor` and adds graph-structure connection capabilities
   - **Key Features**:
     - Input/output queue connections
     - Automatic dependency management
     - Graph-structure-aware execution
     - Parallel and serial connection support
     - Status management and lifecycle control

3. **core_stages.py** (Predefined Nodes: `TaskSplitter`, `TaskRouter`, `TaskRedisTransport`, `TaskRedisSource`, `TaskRedisAck`)
   - **Purpose**: Pre-built implementations of common task patterns and Redis integration nodes, simplifying the construction of complex workflows
   - **Included Nodes**:
     - `TaskSplitter`: Distributes input to multiple subtasks
     - `TaskRouter`: Routes tasks to different downstream nodes based on conditions
     - `TaskRedisTransport`: Sends tasks to a Redis queue for cross-language or distributed execution
     - `TaskRedisSource`: Consumes tasks from a Redis queue as a task graph input source
     - `TaskRedisAck`: Receives execution results from Redis Workers and acknowledges task completion

## Module Relationships

### Internal Relationships
- `TaskStage` inherits from `TaskExecutor`, extending it with graph connection functionality
- All predefined nodes are specialized implementations of `TaskStage`
- All nodes can be combined within a `TaskGraph`

### External Relationships
- **With Graph Module**: `TaskStage` is the basic building block of `TaskGraph`
- **With Runtime Module**: Uses `TaskQueue` for inter-node communication, relies on `TaskDispatch` for execution
- **With Utils Module**: Uses utility functions for data processing and transformation
- **With Persistence Module**: Supports persistent saving of task state

## Usage Patterns

### Basic Usage
1. **Create an executor**: Inherit from `TaskExecutor` to implement custom business logic
2. **Wrap as a node**: Use `TaskStage` to wrap the executor, enabling graph connections
3. **Build the graph structure**: Add nodes to `TaskGraph` and establish dependency relationships

### Advanced Usage
1. **Use predefined nodes**: Directly use `TaskSplitter`, `TaskRouter`, etc. to simplify development
2. **Compose nodes**: Combine multiple nodes into complex data processing pipelines
3. **Custom nodes**: Inherit from `TaskStage` to create domain-specific node types

## Design Principles

### Single Responsibility
- Each `TaskExecutor` handles only a single type of task
- `TaskStage` focuses on graph connections and state management
- Predefined nodes implement specific data processing patterns

### Composability
- All nodes use a unified interface and can be freely combined
- Supports chained invocation and parallel processing
- Input/output type compatibility checking

### Extensibility
- Easily create custom nodes through inheritance
- Supports a plugin-based architecture
- Configuration-driven, allowing behavior adjustments without code changes

## Best Practices

1. **Simple tasks**: Use `TaskExecutor` directly or inherit from it
2. **Graph nodes**: Always use `TaskStage` or its subclasses as graph nodes
3. **Data processing**: Prefer predefined nodes to reduce duplicate code
4. **Error handling**: Implement robust error handling at the `TaskExecutor` level
5. **Resource management**: Properly implement the `cleanup()` method to release resources
