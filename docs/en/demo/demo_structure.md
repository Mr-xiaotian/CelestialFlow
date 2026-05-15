# demo_structure.py Demo Documentation

> 📅 Last Updated: 2026/05/15

## Purpose

Demonstrates various predefined graph structures (DAG and cyclic graphs) from `core_structure.py`, showcasing how CelestialFlow builds and runs under chain, cross, grid, loop, wheel, complete graph, and other topologies.

## Demo Structures

### DAG (Directed Acyclic Graph)

| Function | Structure | Description |
|----------|-----------|-------------|
| `demo_chain` | TaskChain | 5-node linear chain, thread mode |
| `demo_forest` | TaskGraph | Two independent tree-shaped DAGs coexisting |
| `demo_cross` | TaskCross | 3-layer cross structure (3->1->3) |
| `demo_network` | TaskCross | Multi-layer multi-branch network (2->3->1) |
| `demo_star` | TaskCross | Central node pointing to multiple edge nodes |
| `demo_fanin` | TaskCross | Multiple source nodes converging into one merge node |
| `demo_grid` | TaskGrid | 4x4 thread grid, staged scheduling |

### Cyclic Graphs

| Function | Structure | Description |
|----------|-----------|-------------|
| `demo_loop` | TaskLoop | 3-node closed loop, self-locking structure |
| `demo_wheel` | TaskWheel | Central node + 4 ring nodes |
| `demo_complete` | TaskComplete | 3-node complete graph, fully connected |
| `demo_multi_cycle` | TaskGraph | Multi-cycle interconnected graph: 3 groups of 2-node cycles (A/B/C), A2 branches out to B1 and C1 |

## Key Configuration

- DAG structures: `stage_mode="thread"`, `execution_mode="thread"`
- `demo_grid`: Uses `staged` scheduling mode (layer-by-layer execution)
- Cyclic graphs: `put_termination_signal=False` (external stop control recommended)
- All demos enable `Reporter` and `CelestialTree`

## Potential Issues

1. **Cyclic graphs do not stop automatically**: `demo_loop`, `demo_complete`, etc. use `put_termination_signal=False` and will loop continuously until the process is manually terminated.
2. **Sleep delay accumulation**: `add_one_sleep` contains a 1-second sleep; 20 tasks x multiple nodes = long total duration.
3. **No assertions**: Only verifies that the framework can start and run, does not check result values.

## How to Run

```bash
python demo/demo_structure.py
```

## Dependencies

- `celestialflow` (`TaskGraph`, `TaskChain`, `TaskCross`, `TaskGrid`, `TaskLoop`, `TaskWheel`, `TaskComplete`, `TaskStage`)
- `demo_utils`
- `python-dotenv`
- External services: CelestialTree (optional), Reporter (optional)
