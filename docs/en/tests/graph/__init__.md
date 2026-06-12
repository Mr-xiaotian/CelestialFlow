# graph Test Package

> 📅 Last Updated: 2026/06/11

## Purpose
`tests/graph/` covers task graph construction, topology analysis, structure export, graph-level scheduling behavior, and dedicated tests for cyclic graph structures such as `TaskLoop` and `TaskWheel`, primarily corresponding to the `celestialflow.graph` module.

## Included Test Files
- `test_analysis.py`: Covers source node identification, level computation, and NetworkX graph analysis helper functions.
- `test_graph.py`: Covers `TaskGraph` construction, scheduling, error collection, and lifecycle.
- `test_serialize.py`: Covers structure graph JSON/text export logic.
- `test_structure.py`: Covers dedicated analysis of `TaskLoop` and `TaskWheel` cyclic graph structures.

## How to Run

```bash
pytest tests/graph -v
pytest tests/graph -k "graph or analysis or structure" -v
```
