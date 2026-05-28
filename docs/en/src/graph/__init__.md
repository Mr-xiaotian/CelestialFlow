# Graph Module

> 📅 Last Updated: 2026/05/28

The Graph module is the core scheduling system of CelestialFlow, responsible for managing dependency relationships, execution flow, and lifecycle of task nodes. It provides flexible task graph construction, analysis, and serialization capabilities.

## Module Overview

The Graph module defines the basic units of task execution and their relationships, forming a directed graph. Each node represents a `TaskStage`, and edges represent data flow dependencies. This module ensures tasks are executed in the correct topological order and handles concurrency, error handling, and resource management.

## File Description

### Core Files

1. **core_graph.py** (`TaskGraph`)
   - **Purpose**: Core scheduler that manages dependency relationships, execution flow, resource allocation, and lifecycle of `TaskStage` nodes
   - **Key Features**:
     - Establishing dependency relationships between nodes (`set_stages` / `connect`)
     - Executing the task graph (`eager` all-at-once / `staged` layer-by-layer)
     - Runtime monitoring snapshots and global remaining time estimation
     - Dynamic task injection (`put_stage_queue`)
     - Error persistence and unconsumed task handling

2. **core_structure.py** (Predefined Graph Structures)
   - **Purpose**: Provides six predefined task graph structures to simplify common patterns
   - **Included Structures**:
     - `TaskChain`: Linear task chain, nodes connected sequentially
     - `TaskLoop`: Ring structure, nodes connected end-to-end
     - `TaskCross`: Multi-layer cross structure, intra-layer parallel with inter-layer full connections
     - `TaskComplete`: Complete graph, every node connects to all other nodes
     - `TaskWheel`: Wheel-spoke structure, center node connects to all ring nodes
     - `TaskGrid`: 2D grid, nodes connect to right and below neighbors

### Utility Files

3. **util_analysis.py**
   - **Purpose**: Graph analysis tools based on `networkx`
   - **Key Functions**:
     - `build_networkx_graph()`: Builds a `DiGraph` from adjacency list and runtime info
     - `find_source_nodes()`: Finds source nodes with in-degree 0
     - `compute_node_levels()`: Computes node levels (supports DAGs and cyclic graphs)

4. **util_serialize.py**
   - **Purpose**: Task graph structure serialization to JSON and text formatting
   - **Key Functions**:
     - `build_structure_graph()`: Recursively builds structure JSON from source nodes
     - `_build_structure_subgraph()`: Recursively builds a subgraph (internal function)
     - `format_structure_list_from_graph()`: Formats into printable tree-style text

## Module Dependencies

### Internal Dependencies
- `TaskGraph` is the base class; all other structures inherit from it
- `TaskChain`, `TaskLoop`, etc. are specialized implementations of `TaskGraph` (encapsulating `set_stages` / `connect` logic)
- Analysis tools depend on `networkx` for graph-theoretic computations
- Serialization tools output runtime structures as JSON/text

### External Dependencies
- **With Stage Module**: `TaskGraph` manages `TaskStage` nodes; each node starts via `start_stage`
- **With Runtime Module**: Uses `TaskInQueue`/`TaskOutQueue` as inter-node communication pipes
- **With Persistence Module**: Persists via `LogSpout`/`FailSpout`
- **With Observability Module**: Pushes status to Web UI via `TaskReporter`

## Usage Patterns

1. **Build Task Graph**: Create `TaskStage` nodes → `set_stages()` register → `connect()` establish dependencies
2. **Choose Structure**: For common patterns, use predefined structures like `TaskChain`/`TaskCross`
3. **Configure**: Integrate external services via `set_reporter()` / `set_ctree()`
4. **Execute**: Call `start_graph()` or subclass methods like `start_chain()`/`start_cross()`
5. **Monitor**: Use `collect_runtime_snapshot()` and `get_graph_summary()` to check status

## Usage Examples

The following examples demonstrate building and executing various graph structures.

### Basic TaskGraph Construction

```python
from celestialflow import TaskGraph, TaskStage

# Define stage functions
def stage_a_func(x: int) -> int:
    return x + 1

def stage_b_func(x: int) -> int:
    return x * 2

def stage_c_func(x: int) -> int:
    return x - 3

# Create nodes
s1 = TaskStage("S1", func=stage_a_func, execution_mode="serial")
s2 = TaskStage("S2", func=stage_b_func, execution_mode="serial")
s3 = TaskStage("S3", func=stage_c_func, execution_mode="serial")

# Build DAG: S1 -> S2 -> S3
graph = TaskGraph(schedule_mode="eager")
graph.set_stages([s1, s2, s3])
graph.connect([s1], [s2])
graph.connect([s2], [s3])

# Execute
graph.start_graph({s1.get_name(): [1, 2, 3]})

# View summary
summary = graph.get_graph_summary()
print(f"Graph summary: {summary}")

# Graph analysis
analysis = graph.get_graph_analysis()
print(f"Is DAG: {analysis['isDAG']}")
print(f"Layers: {analysis['layersDict']}")
```

### TaskChain Linear Chain

```python
from celestialflow import TaskChain, TaskStage

stages = [
    TaskStage("Clean", func=lambda x: x.strip().lower()),
    TaskStage("Parse", func=lambda x: int(x)),
    TaskStage("Compute", func=lambda x: x ** 2),
]

chain = TaskChain(stages, stage_mode="serial")
chain.start_chain({stages[0].get_name(): [" 10 ", " 20 ", " 30 "]})

print(f"Chain summary: {chain.get_graph_summary()}")
```

### TaskCross Cross-Layer

```python
from celestialflow import TaskCross, TaskStage

# Define two layers
layer1 = [TaskStage("F1", func=lambda x: x * 2), TaskStage("F2", func=lambda x: x + 3)]
layer2 = [TaskStage("G1", func=lambda x: x ** 2), TaskStage("G2", func=lambda x: -x)]

cross = TaskCross(layers=[layer1, layer2], schedule_mode="eager")
cross.start_cross({layer1[0].get_name(): [1, 2], layer1[1].get_name(): [10, 20]})
print(cross.get_graph_summary())
```

### TaskGrid Grid

```python
from celestialflow import TaskGrid, TaskStage

s00 = TaskStage("A", func=lambda x: x)
s01 = TaskStage("B", func=lambda x: x + 1)
s10 = TaskStage("C", func=lambda x: x * 2)
s11 = TaskStage("D", func=lambda x: x * x)

grid = TaskGrid(grid=[[s00, s01], [s10, s11]])
grid.start_grid({s00.get_name(): [1, 2]})
print(grid.get_graph_summary())
```

### TaskLoop Ring Graph

```python
from celestialflow import TaskLoop, TaskStage

stages = [
    TaskStage("L1", func=lambda x: x + 1),
    TaskStage("L2", func=lambda x: x * 2),
    TaskStage("L3", func=lambda x: x - 1),  # L3 -> L1 forms a ring
]

loop = TaskLoop(stages)
# Ring structures should use put_termination_signal=False to avoid premature termination
loop.start_loop({stages[0].get_name(): [10]}, put_termination_signal=False)
```

### TaskWheel Wheel Graph

```python
from celestialflow import TaskWheel, TaskStage

center = TaskStage("Center", func=lambda x: f"processed: {x}")
ring = [TaskStage(f"R{i}", func=lambda x: f"ring-{i}: {x}") for i in range(3)]

wheel = TaskWheel(center=center, ring=ring)
wheel.start_wheel({center.get_name(): ["data"]})
```

## Best Practices

- Use `TaskChain` for linear flows — no need for manual `connect`
- Use `TaskCross` or manual composition for multi-branch parallel pipelines
- For cyclic graphs (`TaskLoop`/`TaskWheel`), use `put_termination_signal=False` and inject termination externally
- Enable `set_reporter(True)` in production for Web monitoring
- Use `staged` mode for complex DAGs to facilitate layer-by-layer debugging
