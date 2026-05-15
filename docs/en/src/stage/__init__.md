# Stage Module

> 📅 Last Updated: 2026/04/24

The Stage module defines the task execution units in CelestialFlow. It provides a complete hierarchy from basic task executors to complex task nodes, serving as the fundamental building blocks for constructing task graphs.

## Module Overview

The Stage module contains three levels of task execution units:
1. **TaskExecutor**: Basic task executor, handles single task execution logic
2. **TaskStage**: Enhanced task node, adds graph connection capabilities
3. **Predefined Nodes**: Implementations of common task patterns, such as splitters, routers, etc.

These components together form the core of task execution, each usable independently or combined into complex task flows.

## File Descriptions

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
- **With Runtime Module**: Uses `TaskQueue` for inter-node communication, relies on `TaskDispatch` for execution
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

## Best Practices

1. **Simple Tasks**: Use `TaskExecutor` directly or inherit from it
2. **Graph Nodes**: Always use `TaskStage` or subclasses as graph nodes
3. **Data Processing**: Prefer predefined nodes to reduce duplicate code
4. **Error Handling**: Implement robust error handling at the `TaskExecutor` level
5. **Resource Management**: Properly implement the `cleanup()` method to release resources
