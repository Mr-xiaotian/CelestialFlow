# graph Test Package

> 📅 Last Updated: 2026/06/22

## Purpose
`tests/graph/` covers task graph construction, topology analysis, structure export, graph-level scheduling behavior, and dedicated tests for cyclic graph structures such as `TaskLoop` and `TaskWheel`, primarily corresponding to the `celestialflow.graph` module.

## Included Test Files
- `test_graph.py`: Covers `TaskGraph` construction, scheduling, error collection, and lifecycle.
- `test_serialize.py`: Covers structure graph JSON/text export logic.
- `test_structure.py`: Covers dedicated analysis of `TaskLoop` and `TaskWheel` cyclic graph structures.
- `test_utilgraph.py`: Covers `OrderGraph` construction, source node identification, and level computation helpers.

## How to Run

```bash
pytest tests/graph -v
pytest tests/graph -k "graph or utilgraph or structure" -v
```
