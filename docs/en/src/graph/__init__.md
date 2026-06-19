# Graph Module

> 📅 Last Updated: 2026/06/18

The Graph module is CelestialFlow's core scheduling system, responsible for managing dependency relationships between task nodes, execution flow, and lifecycle. It provides flexible task graph construction, analysis, and serialization capabilities.

## Module Overview

The Graph module defines the fundamental units of task execution and their relationships, forming a directed graph. Each node represents a `TaskStage`, and edges represent data flow dependencies. This module ensures that tasks execute in the correct topological order and handles concurrency, error handling, and resource management.

### Public Exports (`__all__`)

```python
from celestialflow.graph import (
    TaskChain,      # Linear task chain
    TaskComplete,   # Complete graph structure
    TaskCross,      # Multi-layer cross structure
    TaskGraph,      # Core task graph
    TaskGrid,       # 2D grid structure
    TaskLoop,       # Cyclic structure
    TaskWheel,      # Wheel structure
)
```

## File Descriptions

### Core Files

1. **core_graph.py** (`TaskGraph`)
   - **Purpose**: Core scheduler, manages `TaskStage` node dependencies, execution flow, resource allocation, and lifecycle
   - **Key Features**:
     - Establish inter-node dependencies (`set_stages` / `connect`)
     - Execute task graphs (`eager` all-at-once launch / `staged` layer-by-layer execution)
     - Runtime monitoring snapshots and global remaining time estimation
     - Dynamic task injection (`put_stage_queue`)
     - Error persistence and unconsumed task handling

2. **core_structure.py** (Predefined graph structures)
   - **Purpose**: Provides six predefined task graph structures, simplifying common patterns
   - **Included Structures**:
     - `TaskChain`: Linear task chain, nodes connected sequentially
     - `TaskLoop`: Cyclic structure, head-to-tail connection
     - `TaskCross`: Multi-layer cross structure, parallel within layers, fully connected between layers
     - `TaskComplete`: Complete graph, each node connects to all other nodes
     - `TaskWheel`: Hub-and-spoke structure, center connects to ring nodes
     - `TaskGrid`: 2D grid, nodes connect to right and below neighbors

### Utility Files

3. **util_graph.py**
   - **Purpose**: Lightweight ordered directed graph and foundational graph algorithms
   - **Key Functions**:
     - `OrderGraph`: Minimal ordered directed graph with stable node iteration order
     - `is_dag()` / `topo_sort()`: DAG detection and topological traversal
     - `tarjan_scc()` / `get_condensation()`: SCC analysis and condensation graph construction
     - `compute_node_levels()`: Node level computation based on SCC condensation

4. **util_serialize.py**
   - **Purpose**: Task graph structure serialization to JSON and text rendering
   - **Key Functions**:
     - `build_structure_graph()`: Build structure JSON from node dict, adjacency table, and source nodes
     - `format_structure_list_from_graph()`: Format as printable tree text

## Module Relationships

### Internal Relationships
- `TaskGraph` is the base class; all other structures inherit from it
- `TaskChain`, `TaskLoop`, etc. are specialized implementations of `TaskGraph` (encapsulating `set_stages` / `connect` logic)
- `util_graph.py` provides the shared internal graph structure and graph-theoretic helpers
- `TaskGraph` now performs source lookup, DAG detection, and level analysis on top of `OrderGraph`
- Serialization tools output runtime structures as JSON/text

### External Relationships
- **With Stage Module**: `TaskGraph` manages `TaskStage` nodes, each node started via `start_stage`
- **With Runtime Module**: Uses `TaskInQueue`/`TaskOutQueue` as inter-node communication pipes
- **With Persistence Module**: Achieves persistence via `LogSpout`/`FailSpout`
- **With Observability Module**: Pushes state to Web UI via `TaskReporter`

## Usage Patterns

1. **Build Task Graph**: Create `TaskStage` nodes → `set_stages()` register → `connect()` establish dependencies
2. **Choose Structure**: For common patterns, directly use predefined structures like `TaskChain`/`TaskCross`
3. **Configure**: Integrate external services via `set_reporter()` / `set_ctree()`
4. **Execute**: Call `start_graph()` or subclass methods like `start_chain()`/`start_cross()`
5. **Monitor**: Use `collect_runtime_snapshot()` and `get_status_snapshot()` to obtain state

## Usage Examples

The following examples demonstrate construction and execution of various graph structures in the Graph module.

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
graph = TaskGraph(name="MyGraph", schedule_mode="eager")
graph.set_stages([s1, s2, s3])
graph.connect([s1], [s2])
graph.connect([s2], [s3])

# Execute
graph.start_graph({s1.get_name(): [1, 2, 3]})

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

chain = TaskChain(name="DataPipeline", stages=stages, stage_mode="serial")
chain.start_chain({stages[0].get_name(): [" 10 ", " 20 ", " 30 "]})

print(f"Chain status: {chain.get_status_snapshot()}")
```

### TaskCross Cross Layers

```python
from celestialflow import TaskCross, TaskStage

# Define two layers
layer1 = [TaskStage("F1", func=lambda x: x * 2), TaskStage("F2", func=lambda x: x + 3)]
layer2 = [TaskStage("G1", func=lambda x: x ** 2), TaskStage("G2", func=lambda x: -x)]

cross = TaskCross(name="CrossPipeline", layers=[layer1, layer2], schedule_mode="eager")
cross.start_cross({layer1[0].get_name(): [1, 2], layer1[1].get_name(): [10, 20]})
print(cross.get_status_snapshot())
```

### TaskGrid Grid

```python
from celestialflow import TaskGrid, TaskStage

s00 = TaskStage("A", func=lambda x: x)
s01 = TaskStage("B", func=lambda x: x + 1)
s10 = TaskStage("C", func=lambda x: x * 2)
s11 = TaskStage("D", func=lambda x: x * x)

grid = TaskGrid(name="GridPipeline", grid=[[s00, s01], [s10, s11]])
grid.start_grid({s00.get_name(): [1, 2]})
print(grid.get_status_snapshot())
```

### TaskLoop Cyclic Graph

```python
from celestialflow import TaskLoop, TaskStage

stages = [
    TaskStage("L1", func=lambda x: x + 1),
    TaskStage("L2", func=lambda x: x * 2),
    TaskStage("L3", func=lambda x: x - 1),  # L3 -> L1 forms the cycle
]

loop = TaskLoop(name="FeedbackLoop", stages=stages)
# For cyclic structures, recommend put_termination_signal=False to avoid premature termination
loop.start_loop({stages[0].get_name(): [10]}, put_termination_signal=False)
```

### TaskWheel Wheel Graph

```python
from celestialflow import TaskWheel, TaskStage

center = TaskStage("Center", func=lambda x: f"processed: {x}")
ring = [TaskStage(f"R{i}", func=lambda x: f"ring-{i}: {x}") for i in range(3)]

wheel = TaskWheel(name="HubAndSpoke", center=center, ring=ring)
wheel.start_wheel({center.get_name(): ["data"]})
```

## Best Practices

- Use `TaskChain` for linear flows; no need to manually `connect`
- Use `TaskCross` or manual composition for multi-path parallel pipelines
- For cyclic graphs (`TaskLoop`/`TaskWheel`), recommend `put_termination_signal=False` and stop via external injection
- Enable `set_reporter(True)` in production for Web monitoring
- Use `staged` mode for complex DAGs to facilitate layer-by-layer debugging
