# demo_structure.py Demo Documentation

> 📅 Last updated: 2026/04/22

## Purpose

Demonstrates the various predefined graph structures (DAG and cyclic graphs) in `core_structure.py`, showcasing how CelestialFlow builds and runs under multiple topologies including chain, cross, grid, loop, wheel, and complete graphs.

## Demo Structures

### DAG (Directed Acyclic Graph)

| Function | Structure | Description |
|----------|-----------|-------------|
| `demo_chain` | TaskChain | 5-node linear chain, process mode |
| `demo_forest` | TaskGraph | Two independent tree-shaped DAGs coexisting |
| `demo_cross` | TaskCross | 3-layer cross structure (3->1->3) |
| `demo_network` | TaskCross | Multi-layer multi-branch network (2->3->1) |
| `demo_star` | TaskCross | Central node pointing to multiple edge nodes |
| `demo_fanin` | TaskCross | Multiple source nodes converging into one merge node |
| `demo_grid` | TaskGrid | 4x4 process grid, staged scheduling |

### Cyclic Graphs

| Function | Structure | Description |
|----------|-----------|-------------|
| `demo_loop` | TaskLoop | 3-node closed loop, self-locking structure |
| `demo_wheel` | TaskWheel | Central node + 4 ring nodes |
| `demo_complete` | TaskComplete | 3-node complete graph, pairwise connected |

## Key Configuration

- DAG structures: `stage_mode="process"`, `execution_mode="thread"`
- `demo_grid`: Uses `staged` scheduling mode (layer-by-layer execution)
- Cyclic graphs: `put_termination_signal=False` (external stop control recommended)
- All demos enable `Reporter` and `CelestialTree`

## Potential Issues

1. **Cyclic graphs do not stop automatically**: `demo_loop`, `demo_complete`, etc. use `put_termination_signal=False` and will loop continuously until the process is manually terminated.
2. **Process startup overhead**: A large number of `stage_mode="process"` nodes start slowly on Windows; `demo_grid` (16 processes) may require tens of seconds to initialize.
3. **Sleep delay accumulation**: `add_one_sleep` contains a 1-second sleep; 20 tasks x multiple nodes = long total execution time.
4. **No assertions**: Only verifies that the framework can start and run; does not check result values.

## How to Run

```bash
python demo/demo_structure.py
```

## Dependencies

- `celestialflow` (`TaskGraph`, `TaskChain`, `TaskCross`, `TaskGrid`, `TaskLoop`, `TaskWheel`, `TaskComplete`, `TaskStage`)
- `demo_utils`
- `python-dotenv`
- External services: CelestialTree (optional), Reporter (optional)
