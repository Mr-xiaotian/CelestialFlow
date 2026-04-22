# Graph Module

The Graph module is CelestialFlow's core scheduling system, responsible for managing dependency relationships, execution flow, and lifecycle of task nodes. It provides flexible task graph construction, analysis, and serialization capabilities.

## Module Overview

The Graph module defines the basic units of task execution and their relationships, forming a Directed Acyclic Graph (DAG). Each node represents a `TaskStage`, and edges represent dependency relationships. This module ensures tasks are executed in the correct order and handles concurrency, error handling, and resource management.

## File Description

### Core Files

1. **core_graph.py** (`TaskGraph`)
   - **Purpose**: Core scheduler that manages dependency relationships, execution flow, resource allocation, and lifecycle of `TaskStage` nodes
   - **Key Features**:
     - Establish dependency relationships between nodes
     - Execute task graphs (synchronous/asynchronous)
     - Error handling and retry mechanisms
     - Resource management and concurrency control

2. **core_structure.py** (`TaskChain`, `TaskLoop`, `TaskCross`, `TaskComplete`, `TaskWheel`, `TaskGrid`)
   - **Purpose**: Provides predefined task graph structures to simplify building common patterns
   - **Included Structures**:
     - `TaskChain`: Linear task chain where nodes execute sequentially
     - `TaskLoop`: Loop structure with conditional loop support
     - `TaskCross`: Cross-connection structure with interconnected nodes between layers
     - `TaskComplete`: Fully connected structure where all nodes are interconnected
     - `TaskWheel`: Wheel structure where a center node connects to all other nodes
     - `TaskGrid`: Grid structure where nodes are arranged in rows and columns

### Utility Files

3. **util_analysis.py**
   - **Purpose**: Task graph analysis tools providing graph-theoretic analysis and diagnostic capabilities
   - **Key Functions**:
     - `format_networkx_graph()`: Converts a structure graph to a networkx directed graph
     - `compute_node_levels()`: Computes node levels in the graph (topological sort)
   - **Key Features**:
     - Graph structure conversion and visualization support
     - Node level computation and topological analysis
     - Dependency analysis and validation

4. **util_serialize.py**
   - **Purpose**: Task graph serialization and structure building tools
   - **Key Functions**:
     - `build_structure_graph()`: Builds a JSON graph structure from root nodes
     - `_build_structure_subgraph()`: Builds a single subgraph structure (internal function)
     - `format_structure_list_from_graph()`: Formats a string list from the graph structure
   - **Key Features**:
     - Task graph structure serialization to JSON format
     - Recursive graph structure construction
     - Structure formatting and text output

## Module Relationships

### Internal Relationships
- `TaskGraph` is the base class; all other structures inherit from or use it
- `TaskChain`, `TaskLoop`, etc. are specialized implementations of `TaskGraph`
- Analysis tools depend on graph structures for diagnostics
- Serialization tools can persist any `TaskGraph` instance

### External Relationships
- **With Stage Module**: Manages `TaskStage` nodes, each being an executable unit
- **With Runtime Module**: Uses `TaskDispatch` for task execution, depends on `TaskQueue` for communication
- **With Persistence Module**: Interacts with persistent storage through serialization tools
- **With Observability Module**: Provides execution status and performance metrics

## Usage Patterns

1. **Build Task Graph**: Create `TaskStage` nodes and establish dependencies via `graph.connect()`
2. **Choose Structure**: Use predefined structures based on requirements (e.g., `TaskChain` for linear flows)
3. **Execute**: Call `start_graph()` or use subclass methods like `start_chain()` to execute the task graph
4. **Monitor**: Use analysis tools to inspect graph structure and monitor execution status
5. **Persist**: Use serialization tools to save/load task graphs when needed

## Best Practices

- For simple linear flows, prefer `TaskChain`
- Use `TaskSplitter` and `TaskRouter` for complex branching logic
- Use `TaskLoop` for cyclic tasks
- Regularly use analysis tools to check the health of graph structures
- Serialize and save important workflows for debugging and recovery
