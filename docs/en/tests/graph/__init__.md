# graph Test Package

> 📅 Last Updated: 2026/08/31

## Purpose
`tests/graph/` covers task graph construction, topology analysis, structure rendering, graph-level scheduling behavior, and dedicated tests for cyclic graph structures such as `TaskLoop` and `TaskWheel`, primarily corresponding to the `celestialflow.graph` module.

## Included Test Files
- `test_estimators.py`: Remaining-time estimation and DAG load propagation algorithms.
- `test_graph.py`: Covers `TaskGraph` construction, scheduling, error collection, and lifecycle.
- `test_order_graph.py`: Covers `OrderGraph` construction, source node identification, level computation, SCC partitioning, and deep-graph regression for graph analysis basics.
- `test_render.py`: Covers rendering the structure graph as a tree-shaped text list with borders (replacing the old serialization tests).
- `test_structure.py`: Covers dedicated analysis and input validation for `TaskLoop` and `TaskWheel` cyclic graph structures.

## How to Run

```bash
pytest tests/graph -v
pytest tests/graph -k "graph or order_graph or structure or render" -v
```
