# Graph Module

> 📅 Last Updated: 2026/04/22

The Graph module is the core scheduling system of CelestialFlow, responsible for managing dependency relationships, execution flow, and lifecycle of task nodes. It provides flexible task graph construction, analysis, and serialization capabilities.

## Module Overview

The Graph module defines the basic units of task execution and their relationships, forming a Directed Acyclic Graph (DAG). Each node represents a `TaskStage`, and edges represent dependency relationships. This module ensures tasks are executed in the correct order and handles concurrency, error handling, and resource management.

## File Description

### Core Files

1. **core_graph.py** (`TaskGraph`)
   - **Purpose**: Core scheduler that manages dependency relationships, execution flow, resource allocation, and lifecycle of `TaskStage` nodes
   - **Key Features**:
     - Establishing dependency relationships between nodes
     - Executing the task graph (synchronous/asynchronous)
     - Error handling and retry mechanisms
     - Resource management and concurrency control

2. **core_structure.py** (`TaskChain`, `TaskLoop`, `TaskCross`, `TaskComplete`, `TaskWheel`, `TaskGrid`)
   - **Purpose**: Provides predefined task graph structures to simplify building common patterns
   - **Included Structures**:
     - `TaskChain`: Linear task chain, nodes execute sequentially
     - `TaskLoop`: Loop structure, supports conditional loops
     - `TaskCross`: Cross-connection structure, nodes interconnect between layers
     - `TaskComplete`: Fully-connected structure, all nodes interconnect
     - `TaskWheel`: Wheel structure, center node connects to all other nodes
     - `TaskGrid`: Grid structure, nodes arranged in rows and columns

### Utility Files

3. **util_analysis.py**
   - **Purpose**: Task graph analysis tools providing graph theory analysis and diagnostics
   - **Key Functions**:
     - `format_networkx_graph()`: Converts a structure graph to a networkx directed graph
     - `compute_node_levels()`: Computes node levels in the graph (topological sort)
   - **Key Features**:
     - Graph structure conversion and visualization support
     - Node level computation and topological analysis
     - Dependency relationship analysis and validation

4. **util_serialize.py**
   - **Purpose**: Task graph serialization and structure building tools
   - **Key Functions**:
     - `build_structure_graph()`: Builds a JSON graph structure from root nodes
     - `_build_structure_subgraph()`: Builds a single subgraph structure (internal function)
     - `format_structure_list_from_graph()`: Formats a string list from the graph structure
   - **Key Features**:
     - Task graph structure serialization to JSON format
     - Recursive graph structure representation building
     - Structure formatting and text output

## Module Dependencies

### Internal Dependencies
- `TaskGraph` is the base class; all other structures inherit from or use it
- `TaskChain`, `TaskLoop`, etc. are specialized implementations of `TaskGraph`
- Analysis tools rely on graph structure for diagnostics
- Serialization tools can persist any `TaskGraph` instance

### External Dependencies
- **Stage Module**: Manages `TaskStage` nodes, each being an executable unit
- **Runtime Module**: Uses `TaskDispatch` to execute tasks, relies on `TaskQueue` for communication
- **Persistence Module**: Interacts with persistent storage through serialization tools
- **Observability Module**: Provides execution status and performance metrics

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
- Regularly use analysis tools to check graph structure health
- Serialize and save important workflows for debugging and recovery
