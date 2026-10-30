# src/celestialflow/graph/__init__.py

> 📅 Last Updated: 2026/10/30

The Graph module is CelestialFlow's core scheduling system, responsible for managing dependency relationships between task nodes, execution flow, and lifecycle. It provides flexible task graph construction and analysis capabilities.

## Module Overview

The Graph module defines the fundamental units of task execution and their relationships, forming a directed graph. Each node is a `BaseTaskNode` derivative object defined in `celestialflow.node` (the public API includes `TaskExecutor`, `TaskSplitter`, `TaskRouter`), and edges represent data flow dependencies. This module ensures that tasks execute in the correct topological order and handles concurrency, error handling, and resource management.

### Public Exports (`__all__`)

```python
from celestialflow.graph import (
    TaskChain,  # Linear task chain
    TaskComplete,  # Complete graph structure
    TaskCross,  # Multi-layer cross structure
    TaskGraph,  # Core task graph
    TaskGrid,  # 2D grid structure
    TaskLoop,  # Cyclic structure
    TaskWheel,  # Wheel structure
)
```

`__all__ = ["TaskChain", "TaskComplete", "TaskCross", "TaskGraph", "TaskGrid", "TaskLoop", "TaskWheel"]`

## File Descriptions

### Core Files

1. **core_graph.py** (`TaskGraph`)
   - **Purpose**: Core scheduler, manages dependency relationships, execution flow, and lifecycle of task nodes (`BaseTaskNode` derivatives)
   - **Key Features**:
     - Establish inter-node dependencies (`set_nodes` / `connect`)
     - Execute task graphs (`start` / `start_async`, runs in serial/thread/async according to `graph_mode`)
     - Batch-set node execution modes (`set_node_execution_mode`) and shared event client (`set_ctree`)
     - Graph-level observer registration (`add_observer`) and query (`get_observers`)
     - Graph analysis (`_build_analysis` lazy rebuild: source node identification, DAG detection, level computation; public entry points are `get_source_nodes()` / `is_dag()` / `get_layers()`)
     - Initial task and persisted task injection (`run` / `run_async` / `restore_db` / `inject_tasks` / `inject_terminations`); the run entry points accept `log_level` and `report` (`ReportConfig`) parameters

2. **core_structure.py** (Predefined graph structures)
   - **Purpose**: Provides six predefined task graph structures, simplifying common patterns
   - **Included Structures**:
     - `TaskChain`: Linear task chain, nodes connected sequentially
     - `TaskLoop`: Cyclic structure, head-to-tail connection
     - `TaskCross`: Multi-layer cross structure, parallel within layers, fully connected between layers
     - `TaskComplete`: Complete graph, each node connects to all other nodes
     - `TaskWheel`: Hub-and-spoke structure, center connects to all ring nodes
     - `TaskGrid`: 2D grid, nodes connect to right and below neighbors

### Utility Files

3. **util_order_graph.py**
   - **Purpose**: Lightweight ordered directed graph and foundational graph algorithms
   - **Key Contents**:
     - `OrderGraph`: Minimal ordered directed graph, maintaining stable node order, in-edge and out-edge adjacency lists
     - `is_dag()` / `topo_sort()`: DAG detection and topological sorting
     - `tarjan_scc()` / `get_condensation()`: Strongly connected component analysis and condensation graph construction
     - `source_sccs()` / `source_nodes()`: Locate source SCCs and extract representative source nodes
     - `compute_node_levels()`: Compute node levels based on SCC condensation graph

> Note: The tree-style text rendering of graph structures (`render_structure_list`) has been moved from this module to `persist/util_render.py`; the Graph module no longer holds rendering logic.

## Module Relationships

### Internal Relationships
- `TaskGraph` is the base class; all other structures inherit from it
- `TaskChain`, `TaskLoop`, etc. are specialized implementations of `TaskGraph` (encapsulating `set_nodes` / `connect` logic)
- `util_order_graph.py` provides the shared internal lightweight graph structure and foundational graph algorithms
- `TaskGraph` currently performs source node identification, DAG detection, and level analysis on top of `OrderGraph`; the analysis results are rebuilt lazily, driven by the `_analysis_dirty` flag, and the public read entry points are `get_source_nodes()` / `is_dag()` / `get_layers()`

### External Relationships
- **With Node Module**: Task graph nodes (`TaskExecutor` / `TaskSplitter` / `TaskRouter`) are provided by `celestialflow.node`; `TaskGraph` is only responsible for assembly, connection, and scheduling
- **With Runtime Module**: Uses `TaskInQueue`/`TaskOutQueue` as inter-node communication pipes
- **With Observer Module**: Registers graph-level observers via `add_observer()` to receive events from all nodes in the graph; runtime resources are managed uniformly through `run_graph_resources`
- **With Persistence Module**: Achieves task persistence and recovery (`restore_db`) through the persistence entry points (lifecycle / log)

## Usage Patterns

1. **Build Task Graph**: Create `TaskExecutor` nodes (use `TaskSplitter` / `TaskRouter` as needed) → `set_nodes()` register → `connect()` establish dependencies
2. **Choose Structure**: For common patterns, directly use predefined structures like `TaskChain`/`TaskCross`
3. **Configure**: Inject an event client via `set_ctree()`, register graph-level observers via `add_observer()`
4. **Execute**: Call `run()` or `run_async()`; you can set the log level via `log_level` (default `"INFO"`), and enable remote reporting via `report=ReportConfig(...)` (default `None` means no reporting)

## Usage Examples

The following examples demonstrate construction and execution of various graph structures in the Graph module.

### Basic TaskGraph Construction

```python
from celestialflow import TaskGraph, TaskExecutor


# Define stage functions
def stage_a_func(x: int) -> int:
    return x + 1


def stage_b_func(x: int) -> int:
    return x * 2


def stage_c_func(x: int) -> int:
    return x - 3


# Create nodes
s1 = TaskExecutor("S1", func=stage_a_func, execution_mode="serial")
s2 = TaskExecutor("S2", func=stage_b_func, execution_mode="serial")
s3 = TaskExecutor("S3", func=stage_c_func, execution_mode="serial")

# Build DAG: S1 -> S2 -> S3
graph = TaskGraph(name="MyGraph", graph_mode="thread")
graph.set_nodes([s1, s2, s3])
graph.connect([s1], [s2])
graph.connect([s2], [s3])

# Execute
graph.run({s1.get_name(): [1, 2, 3]})

# Graph analysis (computed on demand at first read)
print(f"Source nodes: {graph.get_source_nodes()}")
print(f"Is DAG: {graph.is_dag()}")  # note that is_dag is a method
print(f"Layers: {graph.get_layers()}")
print(f"Node list: {graph.get_nodes()}")
print(f"Edge adjacency list: {graph.get_edges()}")
```

### Enable Log Level and Remote Reporting

```python
from celestialflow import TaskExecutor, TaskGraph
from celestialflow.runtime import ReportConfig

node = TaskExecutor("Only", func=lambda x: x + 1)
graph = TaskGraph(name="Reported", graph_mode="thread")
graph.set_nodes([node])

graph.run(
    {node.get_name(): [1, 2, 3]},
    log_level="DEBUG",
    report=ReportConfig(url="http://127.0.0.1:5005"),
)
```

> Before using `report`, make sure a receiving service is running at that address; passing `report=None` (the default) disables reporting entirely.

### TaskChain Linear Chain

```python
from celestialflow import TaskChain, TaskExecutor

nodes = [
    TaskExecutor("Clean", func=lambda x: x.strip().lower()),
    TaskExecutor("Parse", func=lambda x: int(x)),
    TaskExecutor("Compute", func=lambda x: x**2),
]

chain = TaskChain(name="DataPipeline", nodes=nodes, graph_mode="thread")
chain.run({nodes[0].get_name(): [" 10 ", " 20 ", " 30 "]})

# View nodes and sources
print(chain.get_nodes())
```

### TaskCross Cross Layers

```python
from celestialflow import TaskCross, TaskExecutor

# Define two layers
layer1 = [
    TaskExecutor("F1", func=lambda x: x * 2),
    TaskExecutor("F2", func=lambda x: x + 3),
]
layer2 = [
    TaskExecutor("G1", func=lambda x: x**2),
    TaskExecutor("G2", func=lambda x: -x),
]

cross = TaskCross(name="CrossPipeline", layers=[layer1, layer2], graph_mode="thread")
cross.run({layer1[0].get_name(): [1, 2], layer1[1].get_name(): [10, 20]})
```

### TaskGrid Grid

```python
from celestialflow import TaskGrid, TaskExecutor

s00 = TaskExecutor("A", func=lambda x: x)
s01 = TaskExecutor("B", func=lambda x: x + 1)
s10 = TaskExecutor("C", func=lambda x: x * 2)
s11 = TaskExecutor("D", func=lambda x: x * x)

grid = TaskGrid(name="GridPipeline", grid=[[s00, s01], [s10, s11]])
grid.run({s00.get_name(): [1, 2]})
```

### TaskLoop Cyclic Graph

```python
from celestialflow import TaskLoop, TaskExecutor

nodes = [
    TaskExecutor("L1", func=lambda x: x + 1),
    TaskExecutor("L2", func=lambda x: x * 2),
    TaskExecutor("L3", func=lambda x: x - 1),  # L3 -> L1 forms the cycle
]

loop = TaskLoop(name="FeedbackLoop", nodes=nodes)
# A cyclic graph cannot be run directly (it would block forever); termination signals
# must be injected after an external condition is met:
# loop.inject_terminations([n.get_name() for n in nodes])
# loop.run({nodes[0].get_name(): [10]}, if_put_signal=False)

print(loop.is_dag())  # False
print(loop.get_layers())  # nodes in the same cycle share a level
```

### TaskWheel Wheel Graph

```python
from celestialflow import TaskWheel, TaskExecutor

center = TaskExecutor("Center", func=lambda x: f"processed: {x}")


def make_ring_node(index: int) -> TaskExecutor:
    # Node callbacks must accept exactly one positional argument,
    # so a closure is used to capture the index
    def handle(x: str) -> str:
        return f"ring-{index}: {x}"

    return TaskExecutor(f"R{index}", func=handle)


ring = [make_ring_node(i) for i in range(3)]
wheel = TaskWheel(name="HubAndSpoke", center=center, ring=ring)

# This is also a cyclic graph: prepare external termination injection before running
print(wheel.get_nodes())  # ['Center', 'R0', 'R1', 'R2']
print(wheel.is_dag())  # False
```

## Best Practices

- Use `TaskChain` for linear flows; no need to manually `connect`
- Use `TaskCross` or manual composition for multi-path parallel pipelines
- Cyclic graphs (`TaskLoop` / `TaskWheel` / `TaskComplete`) cannot be used in `serial` mode, and `run()` blocks forever; call `inject_terminations()` to inject termination signals after an external condition is met
- When you need to monitor/receive events in the graph, register graph-level observers via `add_observer()`
- For async execution, use `TaskGraph` with `graph_mode="async"`, started via `start_async()` / `run_async()`
- Read graph analysis results via `get_source_nodes()` / `is_dag()` / `get_layers()` (all are method calls); do not access the now-privatized `_source_names` / `_is_dag` / `_layers_dict`
